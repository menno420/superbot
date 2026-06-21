# 2026-06-21 — BTD6 data: auto-seed the postgres blob store on boot

> **Status:** `in-progress`

## Arc (what I'm about to do)
Owner asked: "isn't the BTD6 data auto-seeded now? I used to run seed-data manually."
**Checked — it is NOT automated.** `seed_postgres_from_files` is called only by
`!btd6ops seed-data` + `scripts/seed_btd6_data.py`; no boot/deploy caller. Migration 054
just creates the empty table. `cog_load` already *detects* drift and warns "run seed-data"
but doesn't fix it — and that drift check is `game_version`-based, so a buff-only data change
(like #1249/#1251, still 55.1) wouldn't even trip it.

Consequence: on the **postgres** backend (what the owner's seed-data memory implies), every
data PR needs a manual seed — including the just-shipped buff windows. Correcting my earlier
"no manual step" claim, which only held for the `file` backend.

## Plan
1. `btd6_data_service.auto_seed_enabled()` — true iff `BTD6_DATA_BACKEND=postgres` and
   `BTD6_AUTO_SEED` not disabled (kill-switch, default on).
2. `BTD6Cog.cog_load` — before `warm_provider()`, if `auto_seed_enabled()`, call
   `seed_postgres_from_files()` (idempotent; defensive — failure logs + continues serving the
   existing store). Postgres-only (file reads bundled files directly; cloud seeds via its own
   upload script). Also fixes the doc's "seed before flipping the var" footgun.
3. Config flag + docs (btd6-data-backends, production-deployment: seed-data now automatic).
4. Tests: gating + cog_load auto-seeds when enabled.
