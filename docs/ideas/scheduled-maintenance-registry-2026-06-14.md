# Idea: a central scheduled-maintenance registry (retire single-loop cogs)

> **Status:** `ideas` — captured 2026-06-14 (P0-2 media-retention session); **case strengthened
> + observability half sharpened 2026-06-14 (P1-2 findings-retention session)**. Tooling/arch lane. Medium.
> **Provenance:** surfaced by minting a zero-command cog (`MediaMaintenanceCog`, #829) to host one
> loop — then **reinforced one week later when P1-2 (#843) minted another,
> `HealthMaintenanceCog`, with the identical shape** (same copy-paste tax + doc-sync reconciliation).

## The friction that surfaced it

P0-2 PR 1 (#829) needed a periodic job: physically purge expired
`youtube_video_cache` rows. The only idiomatic way to own a periodic job in this
codebase today is **a whole cog with a `tasks.loop`** — so the session minted
`MediaMaintenanceCog` purely to host one loop, no commands, no settings, no
subsystem row. That cog joins a growing set of single-loop cogs:
`counters_cog` (rename loop), `community_spotlight_cog` (refresh), `role_cog`
(threshold sweep), `media_maintenance_cog`, and now `health_maintenance_cog`
(the P1-2 findings-retention loop, #843 — minted the same way a week later).

This is cog sprawl for what is really "run this coroutine every N hours," and it
scatters the bot's periodic work across N files with no single place to see,
trigger, or diagnose it.

## The idea

A small **`core/runtime/scheduled_tasks.py`** registry where any subsystem
registers a maintenance job declaratively:

```python
register_maintenance(
    name="media.cache_purge",
    interval=timedelta(hours=6),
    coro=video_reference_cache_service.purge_expired,
    owner="media",
)
```

One lightweight runner cog (`MaintenanceCog`) starts every registered job after
`wait_until_ready`, wraps each in the same fail-safe try/except, and exposes:

- a **content-free diagnostics row** per job (last-run time, last result/count,
  next-run, last error) — which also feeds the P0-2 follow-up "media
  diagnostics" surface for free, and the broader health/diagnostics cog;
- one place to **manually trigger** a job (admin command) for live testing;
- a natural seam for a future "pause all maintenance" kill-switch.

## Why it's worth having (not forced)

- Removes the "mint a cog per loop" tax — new periodic work becomes one
  `register_maintenance(...)` call, not a new file + `config.py` entry +
  help/settings surface-count reconciliation (this session paid that doc-sync
  tax for a zero-command cog).
- Gives periodic work the **observability** it currently lacks entirely — today
  a silently-dead `tasks.loop` is invisible until something rots. **Concrete
  mechanism (sharpened by the P1-2 session):** each registered job records a
  `last_ran_at` heartbeat on success; the health snapshot's `_tasks_subsystem`
  adapter — which the [health readiness map](../planning/production-readiness/health-diagnostics-production-readiness-map-2026-06-12.md)
  rates **Partial** precisely because it "reports healthy from active count alone
  and cannot report recent task failure" — degrades the `tasks` subsystem when a
  job hasn't fired within ~2× its declared cadence. This makes "retention runs
  daily" a *verifiable* claim on a long-lived replica instead of an untested one
  (the #829 media purge and #843 findings retention are both currently
  unobservable if their loop stops). It closes the readiness-map's
  shallow-tasks-adapter gap as a side effect of the registry.
- Aligns with the repo's existing "register once in a shared layer, don't add
  parallel controls" rule (ADR-007 reasoning, the readiness-map's "register
  diagnostics/lifecycle ownership once" recommendation).

## Cost / risk

- Migrating the existing loop cogs is behavior-preserving but touches live cogs
  (counters/spotlight/role) — slice it: ship the registry + move
  `media.cache_purge` onto it first (lowest risk, brand-new), then migrate the
  others one PR at a time behind the conformance.
- `tasks.loop` already gives restart/backoff semantics; the registry must not
  lose `before_loop`/cancellation correctness — pin with tests.

## Next step

If groomed up: a small plan doc + a PR that adds the registry and moves the
media purge onto it (proves the seam), leaving the other loop cogs as
follow-ups. Pairs naturally with the P0-2 "content-free media diagnostics"
follow-up.
