# A repo-wide checker for un-recoverable one-shot deferred actions

> **Status:** `reference` — ✅ **BUILT advisory 2026-07-06** (PR #1748) as
> `scripts/check_deferred_recovery.py` (wired `continue-on-error` in `code-quality.yml`;
> `architecture_rules/deferred_recovery_exceptions.yml` allowlist; 10 unit tests). Captured 2026-07-05
> (rebuild Stage-2 subsystem walk session, PR #1725). This doc is the spec + calibration; the shipped
> module's docstring is the current reference. Promotion to a hard gate is owner-gated (Q-0239 G4).
> **Subsystem:** none (cross-cutting, `scripts/` tooling)
>
> **Build note (2026-07-06):** the calibrated signal held — keying on the **spawn-target** (not raw
> `asyncio.sleep`) + requiring a **persistent Discord state mutation** narrowed 23 raw-sleep files to
> **1** finding (`security_service._hold_then_lift`), which triaged to the intentional ADR-002
> process-local case (allowlisted; a mild residual slowmode-restore gap noted for the owner). The state
> signal also matches **name-based lifecycle-routed verbs** (`_lift_lockdown`/`slowmode`/`unlock`) so a
> mutation through `ChannelLifecycleService` isn't missed. `proof_channel_cog` (the #1728 fix) is
> correctly clean (persist `upsert_lock` + `on_ready` reconcile).

## The problem this session hit — twice, independently

The Stage-2 walk found the **identical bug shape in two unrelated subsystems**, discovered
independently, days apart in the walk order:

- **Row 9 (security):** a raid-lockdown auto-restore timer (`asyncio.sleep` + `tasks.spawn`,
  `security_service.py:216-240,330-354`) has no persisted deadline — a restart mid-lockdown never
  restores the channel's slowmode.
- **Row 16 (proof_channel):** a timed prize-unlock timer (`asyncio.sleep` + `tasks.spawn`,
  `proof_channel_cog.py:201-216`) has the identical gap — `cog_unload` cancels the timer without
  unlocking the channel, and a restart leaves it locked to the winner indefinitely.

Both are confirmed consumers of the rebuild's own **G-9 `DeferredActionSpec`** amendment (a
one-shot delayed callback family, alongside `utility_cog.py:61`'s reminder sleep — 3 confirmed
consumers total, per `docs/analysis/rebuild-discovery/new-bot-capability-audit/findings/FINAL-REVIEW.md:353-355`).
The rebuild's own amendment registry already names the fix shape: `DeferredActionSpec` needs
`ONE_SHOT` + `DURABLE` due-queue semantics **and a boot-reconcile step**
(`docs/analysis/rebuild-discovery/foundations/gate-0/amendment-registry.md:162-165`) — but today's
shipped implementations have none of that, in either subsystem, and nobody had previously
connected these two findings across subsystems.

## The idea

A small, disposable, read-only checker (`scripts/check_deferred_action_recovery.py`) that:

1. Greps for the shape: a function that does `asyncio.sleep(...)` followed by a Discord-state
   mutation (`channel.edit`, permission overwrite, role grant/removal, etc.), scheduled via
   `tasks.spawn`/`asyncio.ensure_future` from a command/listener body (not a `@tasks.loop`).
2. For each match, checks whether the *same module* also has (a) a persisted-deadline write
   (a DB column/row keyed on the same identifier the sleep closes over) and (b) a boot-time sweep
   that reconciles against it (referenced from `on_ready` or a startup hook).
3. Flags any match with (1) but not (2)+(3) as a **restart-recovery gap**, warn-only, with the
   file:line and a one-line "who consumes this" note.

This is exactly the "friction → guard" class (Q-0194): the same bug shape cost two separate,
independent research passes to discover this session, and the rebuild corpus already tells us
there's a third confirmed consumer (`utility_cog.py`'s reminder) worth checking too. A cheap
checker converts "discover this by reading 2,000 lines of source per subsystem" into "grep once,
get a punch list" — and it directly produces the evidence a future G-9 `DeferredActionSpec`
migration would want anyway (a complete consumer list with recovery-gap status per consumer).

## Why now, why cheap

- Stdlib-only (`ast`/`re` over `disbot/`), no new dependency.
- Genuinely disposable per Q-0105's adopt-freely convention — if it proves noisy or wrong, delete it.
- Would have caught both this session's findings mechanically instead of via two separate deep-dive
  research passes, and is likely to surface the third named consumer's status too
  (`utility_cog.py:61`'s reminder — not checked this session, scope was L1a/L1b only).

## Suggested follow-up

Not built this session (Stage-2 walk stayed docs/planning-only, no `disbot/`-adjacent tooling
changes). A natural pickup for the next execution session — likely worth running once, by hand,
as a `python3.10 -c` one-liner even before formalizing it as a committed script, just to see the
hit list across the rest of the bot (mining/fishing/casino all have timer-shaped mechanics per
earlier rebuild-discovery audits and are strong candidates for the same gap).

## Calibration (2026-07-05, CI-setup redesign PR #1737 — for the session that builds this)

Measured against source so the build starts calibrated (Q-0105):

- **Raw `asyncio.sleep` is far too broad:** 23 files in `disbot/` call it, most of them NOT deferred
  one-shot mutations — retry/backoff (`btd6_fetch_service`, `btd6_ingestion_supervisor`), infra loops
  (`runtime`, `session_gc`, `live_update_scheduler`), and **inline UX animations** (`poker_table`,
  `cast_view`, the channel panels do `sleep` + message edits *awaited inline* within an interaction,
  which are NOT fire-and-forget deferred locks).
- **The discriminating signal is the *spawn*, not the sleep.** The true bug shape is a callable
  **scheduled as a background task** (`tasks.spawn` / `asyncio.ensure_future` / `asyncio.create_task`)
  from a command/listener body — fire-and-forget, outliving the interaction — whose body contains
  `asyncio.sleep(...)` **then** a Discord state mutation (slowmode/permission/role edit). The confirmed
  true positives both match: `security_service._hold_then_lift` (via `tasks.spawn`) and
  `proof_channel_cog`'s prize-unlock timer (via `tasks.spawn`); `utility_cog:61`'s reminder is the
  milder third consumer (a missed send, not a stuck lock). So: **key the AST match on the spawned
  target, resolve the callee, and flag spawn-target = (sleep + state-mutation) that lacks a
  persisted-deadline write + a boot-time reconcile (`on_ready`/startup sweep).** Warn-only; the
  file:line punch list is the deliverable. Not shipped in #1737 (raw-sleep would be 20+ FPs); the
  precise signal is now recorded here + in the redesign doc §C.5.
