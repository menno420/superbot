# Session — runtime lock: release early on shutdown (fix ~85s deploy downtime)

> **Status:** `complete`

## Origin — a production Railway log dump

The owner dropped a ~3.5h Railway log (3 container boots). Triaged it as "here's prod state, find +
fix what's wrong." The bot itself is healthy (43 cogs load, gateway connects, BTD6 ingestion runs on
schedule), but one signal was a real, user-visible bug.

## The bug — intermittent ~85s of deploy downtime

Two handoffs in the log:
- **1st (clean):** old replica `33277b9d` shut down gracefully — logged `BTD6 ingestion supervisor
  stopped` + `Runtime lock released`; new replica took over in ~10s.
- **2nd (broken):** old replica `e8eade73` got SIGTERM at `08:45:53` (`closing bot (timeout 20.0s)`),
  but Railway **force-killed the container ~10s later** at `08:46:03` (proven by `Connection reset by
  peer` at `08:46:05` and the **absence of any `Runtime lock released` log**). New replica `05ed9fef`
  then waited **95.6s (20 poll attempts)** for the stale lock to expire → **no live bot for ~89s**.

**Root cause:** the singleton runtime-lock is released only in `main()`'s `finally` — *after*
`bot.close()` (20s budget) + a 5s task drain. Railway's kill grace (~10s observed) is **shorter than
the bot's own close timeout (20s)**, so on a slow close the `finally` never runs and the lock leaks for
its full 90s TTL. Compounding it, the close-timeout force-exit (`os._exit(1)`) *also* bypasses the
`finally`, leaving the lock "wedged until its 90s TTL" — the exact thing its own comment claims to
avoid. It's intermittent because it only bites when `bot.close()` is slower than the platform grace.

## Decision (owner, AskUserQuestion)

Offered three approaches (early release / raise Railway grace / shorten close timeout). Owner chose
**release the lock early** — robust to any kill timing (crash/OOM included), downtime ~85s → ~6s.

## Fix

- **`bot1._drive_close_on_lifecycle_request`** — the instant shutdown begins (right after the "closing
  bot" log, before the close-beginning webhook and `bot.close()`): `_heartbeat_stop.set()` then
  `await _runtime.release_lock_best_effort()`. So a mid-drain SIGKILL can no longer wedge the lock. The
  release is idempotent + boot-scoped (`utils.db.runtime_lock.release` DELETEs only this boot's row), so
  `main()`'s finally re-runs it as the canonical no-op net.
- **`services.runtime.run_heartbeat_loop`** — a `not owned` result *while `stop_event` is set* is now an
  expected shutdown release (new `outcome="released"`, clean loop exit), not a false "peer reclaimed →
  split-brain → `os._exit(1)`". Ordering is guaranteed: the driver sets the stop-event *before* the row
  is deleted, and the loop reads `is_set()` only after observing the row gone.
- **`_heartbeat_stop` + `services.runtime`** promoted to module scope so the driver can reach them
  (removed the `main()`-local copies).
- **`services.metrics`** — documented the new `released` outcome on `runtime_lock_heartbeat_total`.

### Architectural decision (recorded in the invariant docstrings)

Two AST invariants (`test_lifecycle_observability_contract.py`, `test_bot_boot.py`) forbade the driver
from calling `release_lock_best_effort` (cleanup belongs to `main()`'s finally). Updated **deliberately,
with rationale**: the lock release is *not* local teardown like `db.close`/`reporter.close` — it is the
**next-replica handoff signal**, and leaking it costs ~90s of downtime, so the driver drops it early on
every shutdown path. `db.close` / `reporter.close` / `sys.exit` / `os.execv` stay finally-only, so
shutdown-vs-restart cleanup remains unified. Both invariants now *assert the driver does release the
lock, before `bot.close()`*.

### Tradeoff (accepted)

The lock frees while the old replica is still draining, so in rare unlucky timing the new replica could
briefly overlap. In practice the new replica's 5s acquire-poll + ~connect time lands after the old's
gateway has closed, so overlap is typically zero — strictly better than ~85s downtime.

## Verification

- `tests/unit/services/test_runtime.py` — new `test_heartbeat_released_when_lock_dropped_during_shutdown`
  (released outcome, no `os._exit`); the peer-reclaim `lost`→`os._exit` path unchanged.
- `tests/unit/test_bot1_lifecycle_close_driver.py` — new ordering test (release + heartbeat-stop happen
  *before* `bot.close()`) + an autouse isolation fixture stubbing the early release.
- Both invariant tests updated (forbidden-set minus the lock; positive assertions added).
- `python3.10 scripts/check_quality.py --full` → **green (9939 passed, 37 skipped)**.
- `python3.10 scripts/check_architecture.py --mode strict` → **exit 0** (only pre-existing `views`
  warnings).

**Merge ≠ deploy** — the downtime fix only takes effect after a Railway prod deploy.

## Out of scope (noted, not fixed)

- **"Config arbitration — degraded"** startup-health WARNING on every boot = the settings arbiter
  falling back to legacy reads for some keys (`services/platform_consistency.py:_collect_config_arbitration`).
  Designed-degradation; the known settings/bindings convergence lane — not a crash, separate concern.
- **"setup_cog.on_ready: launcher message … is gone"** = the stored setup message was deleted in
  Discord; logged + handled (`setup_cog.py:701`). Benign INFO.

## 💡 Session idea (Q-0089)

[`close-timeout-align-with-platform-grace-2026-06-16.md`](../docs/ideas/close-timeout-align-with-platform-grace-2026-06-16.md)
— make `LIFECYCLE_CLOSE_TIMEOUT_SECONDS` env-configurable (mirror the `RUNTIME_LOCK_BOOT_*` knobs) so
an operator can set it *below* the platform's real kill-grace. The force-exit fallback currently
(hardcoded 20s) never fires under Railway's ~10s grace; the early lock-release makes that mostly moot
for the lock, but aligning the timeout is real defense-in-depth for the rest of the finally cleanup.
Small/decided-lane follow-up to this PR. (Indexed in `docs/ideas/README.md`.)

## ⟲ Previous-session review (Q-0102)

Previous session: **BUG-0013 deathmatch challenge-timer fix** (`2026-06-16-fix-deathmatch-challenge-timer.md`).
- **Did well:** first end-to-end proof of the reported-bug → Hermes-`intake`-triage → Claude-fix loop;
  a tight, contained `_ChallengeView` fix with fail-against-old regression tests.
- **What it surfaced (and the genuine through-line to today):** that bug was *"a timed view kept doing
  work after it should have stopped, and clobbered its successor."* Today's bug is the **same class** at
  the runtime layer — the heartbeat loop would have `os._exit(1)`'d on our *intentional* lock release if
  I hadn't taught it that a stop-signalled release is benign. Both are "a loop/timer outlives its stop
  signal."
- **Concrete workflow improvement:** the deathmatch session *captured* its stays-fixed guard (an AST
  invariant for timed views that transition without `self.stop()`) but **deferred building it** — it's
  still open in that log. This session, by contrast, shipped its positive invariant alongside the fix.
  The norm worth making explicit: **a lifecycle/timer/loop fix ships its "stays-fixed" invariant in the
  same PR.** The deathmatch session's deferred guard is a ready grooming pick-up for a future session
  (left un-bundled here on purpose — runtime PR, focused risk profile).

## Documentation audit (Q-0104)

- `check_docs.py --strict` → **green**. `check_architecture --mode strict` → exit 0.
- `check_current_state_ledger.py --strict` flags **#944, #945** as not-yet-in-ledger — these are merges
  from *before* this session (the branch started at #945's merge commit), i.e. the standing
  living-ledger drift the **next reconciliation** handles (not due till #960; Q-0124: manual sessions
  don't run the reconciliation pass). PR #948 is intentionally **not** added (unmerged — the next
  session reconciles it). No chat-only durable info outstanding: the fix is in code + tests, the
  decision + rationale in the invariant docstrings, the idea is filed + indexed, the claim is cleared.
- Backlog grooming (Q-0015): deliberately *not* bundled — this is a focused, higher-risk runtime PR and
  mixing unrelated idea-execution in would violate the small-focused-runtime-PR norm. Named the ready
  grooming pick-up above (the deathmatch timed-view invariant).
