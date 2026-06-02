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

**Setup (no terminal needed — recommended):**

1. The `btd6_data_blobs` table is created by migration `054` automatically on
   boot — nothing to do.
2. In Discord, as a server **administrator**, run **`!btd6ops seed-data`**. The
   bot loads its bundled data files into the table and replies with the count +
   the next step. (Idempotent — safe to re-run, e.g. after a game-data update.)
3. In **Railway → your bot service → Variables**, add `BTD6_DATA_BACKEND` =
   `postgres`. Saving redeploys the service.
4. Run **`!btd6 status`** — it should read `Data source: postgres (<N> blobs)`.

⚠️ Order matters: **seed first** (step 2), *then* flip the variable (step 3). If
you switch to `postgres` while the table is empty, BTD6 lookups report
"unavailable" until you seed.

**Alternative (CLI):** from a checkout with the deployment `DATABASE_URL`:
```bash
python3.10 scripts/seed_btd6_data.py --dry-run   # preview, no DB
python3.10 scripts/seed_btd6_data.py             # seed
```

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
