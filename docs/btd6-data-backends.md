# BTD6 data backends

> **Status:** `reference` — BTD6 data-backend reference.

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

**The committed files are kept on purpose.** Production reads from Postgres
(`BTD6_DATA_BACKEND=postgres`), but the JSON under `disbot/data/btd6/` stays in
the repo as: the seed source (`!btd6ops seed-data` reads it), the default
backend for local dev + CI, and a version-controlled backup. They're marked
`linguist-generated` in `.gitattributes`, so GitHub collapses them in diffs and
drops them from language stats — the repo stays tidy without losing the safety
net or the easy re-seed. (Deleting them would break `!btd6ops seed-data` and the
file backend for ~6 MB of cosmetic savings, so we don't.)

## Scope note (fixtures vs the stats tree)

`btd6_data_service` (the 9 fixtures) and `btd6_stats_service` (the per-entity
`stats/` tree, the 5.8 MB bulk) both read through the provider, so the whole
data set honours `BTD6_DATA_BACKEND`. `!btd6ops seed-data` loads all 64 blobs
into the table in one go.

## CI hermeticity

Unit tests never touch a real backend: they drive the loader via
`set_provider(FileRawProvider(<dir>))` or an injected `fetch_all` for the
Postgres provider (`tests/unit/services/test_btd6_postgres_provider.py`). Before
removing the committed fixtures, add a minimal subset under `tests/fixtures/btd6/`
and inject it via a conftest autouse fixture so CI stays offline.
