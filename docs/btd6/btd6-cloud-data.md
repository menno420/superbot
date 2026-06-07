# BTD6 cloud data (object-store fixtures)

> **Status:** `reference` — shipped mechanism (opt-in). The bot reads BTD6 deterministic
> fixtures from the local repo by default; setting `BTD6_DATA_BASE_URL` switches
> it to a cloud object store. The repo-data removal (the audit-cleanliness
> payoff) is the gated cutover step below.

## Why

`disbot/data/btd6/` is ~6 MB (5.8 MB of it the per-tower/hero/paragon `stats/`
tree). Serving it from a public-read object store keeps the bulk out of the
repo (cleaner audits / CodeGraph / grep) and lets data refresh without a code
deploy. The seam lives at one choke point — `btd6_data_service` reads every
fixture through a swappable `BTD6RawProvider` — so the backend swap needs **no**
change to the ~14 dataset consumers.

## How it works

- **Provider seam:** `services/btd6_data_provider.py` defines `BTD6RawProvider`
  (Protocol), `FileRawProvider` (local disk, the default), and
  `CloudRawProvider` (HTTPS fetch → local cache).
- **Selection (no I/O at import):** `btd6_data_service._select_provider()` picks
  `CloudRawProvider` when `BTD6_DATA_BASE_URL` is set, else `FileRawProvider`.
- **Warm + degrade (startup):** the BTD6 mother cog's `cog_load` calls
  `btd6_data_service.warm_provider()` **before** starting the ingestion
  supervisor. For the cloud provider this downloads the fixtures into
  `BTD6_DATA_CACHE_DIR`; the sync `get_dataset()` then reads from that cache, so
  the event loop never blocks on network I/O. If a required fixture is
  unreachable **and** absent from the cache, the cog logs a warning, **skips**
  the ingestion supervisor (so it doesn't error-loop), and leaves the panel
  working — the bot does not crash. `!btd6 status` / `!btd6 diagnostics` show
  the active data source + availability.
- **Resilience:** a fetch failure for a fixture already cached is tolerated
  (the cached copy is served). A `manifest.json` checksum mismatch flags the
  fixture as *stale* in the status line but still serves it.

## Environment variables (set on Railway)

| Var | Meaning |
|---|---|
| `BTD6_DATA_BASE_URL` | Public-read base URL of the bucket/CDN, e.g. `https://data.example.com/btd6`. Unset → local repo files. |
| `BTD6_DATA_CACHE_DIR` | Local cache dir for fetched fixtures. Empty → an ephemeral temp dir (re-warmed each boot). |

A **public-read** bucket needs **no** secret at runtime — the bot does a plain
HTTPS GET. Credentials are only needed for the one-time *upload* below.

## Bucket setup (recommended: Cloudflare R2)

1. Create an R2 bucket and enable public access (or front it with a CDN / a
   custom domain). Note the public base URL.
2. Upload the data tree from a checkout with your S3-compatible creds:
   ```bash
   AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... \
   python3.10 scripts/upload_btd6_data.py \
       --bucket <bucket> \
       --endpoint-url https://<accountid>.r2.cloudflarestorage.com \
       --prefix btd6
   ```
   This writes `manifest.json` (sha256 + size per file) and uploads every
   `*.json` under `disbot/data/btd6/` (fixtures **and** the `stats/` subtree),
   preserving relative paths.
3. Set `BTD6_DATA_BASE_URL=https://<public-host>/btd6` on Railway and redeploy.
4. Verify in Discord: `!btd6 status` should show
   `Data source: cloud:<url> (cached)`.

Offline sanity checks (no boto3 / network needed):
```bash
python3.10 scripts/upload_btd6_data.py --check          # print the manifest summary
python3.10 scripts/upload_btd6_data.py --write-manifest # write manifest.json locally
```

## Cutover — removing the data from the repo (gated)

The audit-cleanliness payoff lands only when the bulk data leaves the repo. Do
this **after** the bucket is populated and `BTD6_DATA_BASE_URL` is verified:

1. Confirm `!btd6 status` reads from the cloud and BTD6 lookups work.
2. `git rm -r disbot/data/btd6/stats` (and, once the data-service runtime path
   is confirmed in production, the top-level fixture JSON) and commit. Keep the
   generator scripts + `manifest.json` for reproducibility.

> **CI hermeticity:** unit tests must not depend on the bucket. Tests drive the
> loader through `set_provider(FileRawProvider(<dir>))` (see
> `tests/unit/services/test_btd6_data_service.py`). Before removing the
> committed fixtures, add a minimal fixture subset under `tests/fixtures/btd6/`
> and inject it via a conftest autouse fixture so CI stays offline.

## Follow-up

The runtime cloud read currently covers the `btd6_data_service` fixtures (the 7
core JSONs). The per-entity `stats/` tree (`btd6_stats_service`) reuses the same
pattern — applying the `BTD6RawProvider` seam there is the next increment; the
upload script already publishes the whole tree, so the bucket is ready.
