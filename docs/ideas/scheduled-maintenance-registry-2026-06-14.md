# Idea: a central scheduled-maintenance registry (retire single-loop cogs)

> **Status:** `ideas` — captured 2026-06-14 (P0-2 media-retention session). Tooling/arch lane. Medium.
> **Provenance:** surfaced directly by minting a zero-command cog this session just to host one loop.

## The friction that surfaced it

P0-2 PR 1 (#829) needed a periodic job: physically purge expired
`youtube_video_cache` rows. The only idiomatic way to own a periodic job in this
codebase today is **a whole cog with a `tasks.loop`** — so the session minted
`MediaMaintenanceCog` purely to host one loop, no commands, no settings, no
subsystem row. That cog joins a growing set of single-loop cogs:
`counters_cog` (rename loop), `community_spotlight_cog` (refresh), `role_cog`
(threshold sweep), and now `media_maintenance_cog`.

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
  a silently-dead `tasks.loop` is invisible until something rots.
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
