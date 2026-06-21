# 2026-06-21 — BTD6: surface same-version data drift (sha-based seed reminder)

> **Status:** `in-progress`

## Arc (what I'm about to do)
Completes the data-freshness story from the auto-seed work (#1255). Strict Q-0077(b)
auto-seeds only on a **version bump**; `served_data_drift()` is **version-only** too. So a
**same-version** data edit (e.g. the #1249/#1251 buff windows — still 55.1) neither
auto-seeds NOR warns — it silently stays stale on the postgres store until someone
remembers `!btd6ops seed-data`. This closes that gap with a **reminder** (no auto-write —
honors the owner's strict-(b) choice).

## Plan
1. `btd6_data_service.content_drift()` — sha over canonical JSON (matches the seed digest)
   of every committed file vs what the active store serves; returns the changed names (or
   None for the file backend / in-sync). Sync, reuses `read_blob` (warmed in-memory store).
2. Surface it where version drift already shows — `btd6_cog.cog_load` (boot log) + `!btd6
   status` embed — in the **else** branch (same-version case), so no double-warning.
3. Tests + docs note.
