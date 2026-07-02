# parity/ — the golden behavioral harness (Phase 0.5)

> **Status:** `shipped` (2026-07-02, linchpin-validation session) — the
> rebuild design spec's Phase-0.5 deliverable
> ([design spec §6](../docs/planning/rebuild-design-spec-2026-07-02.md)),
> built and coverage-measured BEFORE the Phase-3 owner gate. It doubles as a
> current-bot behavioral regression net today.

## What this is

Black-box goldens of the CURRENT bot: **command in → embeds/components/DB
delta/events out**, captured by driving the real `disbot/` bot in-process —
real `commands.Bot`, real cogs, real dispatch (converters, cooldowns, the
governance `before_invoke` gate, the error handler), real Postgres — with
one fake seam: the HTTP boundary where output would leave for Discord
(`parity/harness/fake_http.py`). Inputs are synthetic gateway payloads fed
to the real `ConnectionState` parser (`parity/harness/world.py`), so every
object the bot touches is a genuine discord.py model.

**The current bot is the oracle.** The harness observes it verbatim and
never changes its behavior; a rebuilt bot replays the same cases against the
same goldens and is **red until parity**.

## The integrity rule (design spec §6 — read before touching goldens)

The goldens are the acceptance oracle for the from-scratch rebuild. The
future new repo consumes them **read-only, as a pinned external dependency —
they live HERE, outside the new repo's write reach**, so neither bot can
silently rewrite its own oracle. A golden changes only via an explicit,
reviewed PR to this repo, with the diff explained (either "the current bot's
behavior changed deliberately in PR #N" or "the harness's normalization
changed, re-captured verbatim").

## Layout

| Path | What |
|---|---|
| `harness/fake_http.py` | the capture boundary (fake HTTPClient + webhook adapter; unknown calls fail LOUD) |
| `harness/world.py` | deterministic gateway-payload factories + the logical clock (snowflakes carry time) |
| `harness/boot.py` | boots the real bot gateway-free (the composition-root subset; deviations documented inline) |
| `harness/capture.py` | normalization: run-minted ids → symbolic refs; known-volatile scrubs, each documented |
| `harness/dbsnap.py` | per-case DB reset (TRUNCATE … RESTART IDENTITY) + full-table snapshot/delta |
| `harness/cases.py` / `runner.py` | the typed case model; capture + replay engines |
| `cases/curated.py` | hand-written multi-step flows (panels, games, config mutations) |
| `cases/sweep.py` | mechanical breadth: every enumerable prefix/slash command, synthesized args |
| `goldens/` | the captured fixtures (JSON, deterministic, reviewable) + `_sweep_skips.json` (excluded-with-reason) |
| `coverage.py` → `COVERAGE.md` | the measured coverage number + the named uncovered tail |

## Running it

Needs `python3.10` + `DATABASE_URL` pointing at a Postgres the harness may
TRUNCATE (it resets every table per case — **never point it at production**;
the sandbox recipe is `.session-journal.md` § Environment Runbook).

```bash
python3.10 -m parity.run capture            # curated + sweep → goldens/
python3.10 -m parity.run capture --curated  # the 11 deep flows only (fast)
python3.10 -m parity.run check              # replay + diff → red on drift
python3.10 -m parity.run check --only karma # substring filter
python3.10 -m parity.run coverage           # regenerate COVERAGE.md
```

CI note: `code-quality` runs no Postgres service, so capture/replay do not
run there (same posture as the existing real-Postgres integration tests);
the DB-free machinery tests (`tests/unit/parity/`) do. Wiring `check` into a
Postgres-serviced workflow is the natural next step once the corpus
stabilizes — in the NEW repo it is the required `golden-parity` gate from
day one (design spec §6).

## Determinism model (why replay is byte-stable)

- One **logical clock** starts at a fixed epoch and advances a fixed step
  per driven event; snowflake ids are minted from it (discord.py derives
  `created_at`/cooldown buckets from ids, so time IS the id).
- `time.time` is pinned to the logical clock inside the harness process
  (services stamp it into rows/branches — the XP throttle class).
- Per-case: global RNG seeded, module singletons reset via the suite's
  canonical `tests/_isolation.py` registry, database truncated with
  identity restart, fixtures re-applied.
- Run-minted ids/`custom_id`s normalize to first-appearance symbolic refs
  (`<msg:1>`, `<cid:1>`); world constants to names (`<#general>`,
  `<@member>`); known-volatile values (timestamps, uuids, nonces) scrub to
  markers. Everything else is captured **verbatim**.
- `delete_after` timers fire immediately (attributed to the scheduling
  step); `discord.ext.tasks` loops AND `discord.ui.View` wall-clock
  timeouts are neutralized (time-driven behavior is out of capture scope —
  documented deviations; a view's ~180s timeout-disable edit would
  otherwise land inside whatever case runs 3 minutes later).
- Every case's logical timeline starts at a base derived from a hash of
  its case id — POSITION-INDEPENDENT, so a full-corpus run and an
  `--only` run of one case produce identical goldens (absolute logical
  time leaks into epoch-int DB columns like `xp.last_xp`).
- Extension-management commands (`unloadall`/`loadall`) are excluded: they
  mutate the process's cog set mid-run, garbaging every later capture.

Every one of those rules exists because a replay diff caught the class; see
the session log for the discovery trail.

## Deliberate deviations from production (the honesty ledger)

1. No gateway/network; `bot.latency` is NaN (renders as a stable string).
2. Runtime instance lock, health server, memory sampler, close driver, and
   the automation scheduler are not started (ops, not behavior).
3. `discord.ext.tasks` loops don't tick and `discord.ui.View` timeouts
   never fire — scheduled/expiry behavior (retention sweeps, live-update
   refresh, panel timeout-disable) is uncaptured; named in COVERAGE.md.
4. The platform-owner identity is pinned to the admin persona
   (`BOT_OWNER_USER_ID`), so owner-gated surfaces are drivable.
5. Env-keyed integrations (AI providers, YouTube, webhooks) are absent →
   their *degraded* behavior is what gets captured (matches the sandbox
   posture; the AI answer surface has its own oracle in `tests/evals/`).
6. `delete_after` delays collapse to immediate (above).

A rebuilt bot replayed against these goldens inherits the same deviations —
they cancel out; what must match is everything else.
