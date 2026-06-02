# BTD6 data backends

The BTD6 deterministic data (fixtures: towers/heroes/maps/modes/rounds/bloons/
ct_relics, plus the per-entity `stats/` tree + paragon descriptions/abilities)
is read through one swappable seam — `services/btd6_data_provider.py`
(`BTD6RawProvider`). Every read funnels through `btd6_data_service._load_file`,
so the backend is a one-line config switch with **zero** changes to the ~14
dataset consumers.

Pick the backend with `BTD6_DATA_BACKEND`:

| Value | Backend | When |
|---|---|---|
| `""` / `file` | Committed files under `disbot/data/btd6/` (`FileRawProvider`) | Default; local dev. |
| `postgres` | The `btd6_data_blobs` table (`PostgresRawProvider`) | **Recommended in production** — you already run Postgres. |
| `cloud` | A public-read object store / CDN (`CloudRawProvider`) | If you want the data on a bucket/CDN. See `docs/btd6-cloud-data.md`. |

All backends share the same startup contract: the BTD6 mother cog's `cog_load`
calls `btd6_data_service.warm_provider()` (a no-op for `file`) **before**
starting ingestion; if required data is unavailable it logs, skips the
supervisor, and leaves the panel working rather than crashing. `!btd6 status` /
`!btd6 diagnostics` show the active source + availability.

## Postgres backend (recommended)

**Why:** it reuses the database the bot already hard-depends on — no new
external service, failure mode, public URL, or credential. The fixtures are
static, read-once-into-memory reference data, so they live as JSONB blobs keyed
by repo-relative path (`towers.json`, `stats/dart_monkey.json`, …). At startup
`PostgresRawProvider` loads the whole set with one query into memory; the
synchronous loaders then read from that dict (the async DB is never on a hot
path).

**Setup:**

1. The `btd6_data_blobs` table is created by migration `054` (runs
   automatically on boot).
2. Seed it from a checkout pointed at your deployment DB:
   ```bash
   # dry run (no DB):
   python3.10 scripts/seed_btd6_data.py --dry-run
   # seed (uses the bot's DSN env vars):
   python3.10 scripts/seed_btd6_data.py
   ```
3. Set `BTD6_DATA_BACKEND=postgres` on Railway and redeploy.
4. Verify: `!btd6 status` shows `Data source: postgres (<N> blobs)`.
5. Refresh after a game patch: regenerate the fixtures, re-run the seed script
   (it upserts).

**Cutover — removing the data from the repo (gated):** once `!btd6 status`
reads from Postgres and BTD6 lookups work, `git rm -r disbot/data/btd6/`
(keeping the generator scripts) and commit. Do this only after the table is
seeded **and** every consumer reads from PG (see the stats note below).

## Scope note (fixtures vs the stats tree)

`btd6_data_service` (the 7 fixtures) reads through the provider today, so it
honours `BTD6_DATA_BACKEND` immediately. The per-entity `stats/` tree
(`btd6_stats_service`, the 5.8 MB bulk) is migrated to the same provider/seam in
the same series — the seed script already loads `stats/**` into the table, so
the data is present; the repo-removal cutover waits until the stats loaders read
from PG too.

## CI hermeticity

Unit tests never touch a real backend: they drive the loader via
`set_provider(FileRawProvider(<dir>))` or an injected `fetch_all` for the
Postgres provider (`tests/unit/services/test_btd6_postgres_provider.py`). Before
removing the committed fixtures, add a minimal subset under `tests/fixtures/btd6/`
and inject it via a conftest autouse fixture so CI stays offline.
