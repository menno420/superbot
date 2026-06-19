# P0-2 follow-up — content-free media diagnostics plan (2026-06-14)

> **Status:** `historical` — **▶ SHIPPED in #1044** (verified present + wired + tested 2026-06-19:
> `get_cache_stats` in `utils/db/youtube_video_cache.py` · `MediaCacheHealth` / `cache_health` in
> `video_reference_cache_service` · the `youtube_diagnostics` provider counters · the `!platform media`
> → `build_media_embed` surface · tests `test_youtube_diagnostics` / `test_video_reference_cache_service`
> / `test_youtube_video_cache_stats` / `test_media_maintenance_cog`). Provider-execution hardening (the
> "out of scope" item) stays queued. Original plan retained below for provenance.
> Implementation plan for the P0-2 media/YouTube follow-up
> slice "content-free media diagnostics". Source code + merged PRs win over this
> doc once the slice lands.
> **Class:** correctness. **Lane:** shared-platform media (ADR-007), not AI/BTD6.

## Why this slice

P0-2 media retention (#829, Q-0099) closed the **storage** privacy gaps: bounded
projection at the cache write, a scheduled physical purge (`MediaMaintenanceCog`),
thumbnail-URL validation, and the `media` ownership-registry row. The
[media production-readiness map](production-readiness/media-youtube-production-readiness-map-2026-06-12.md)
still lists one operational gap as **Not Done**:

> **Media-specific diagnostics/metrics/operator status** — *"Operators can
> see/edit the generic flag, but cannot inspect provider/key health, quota, fetch
> outcomes, cache size/age, purge status, or transcript availability rates."*

and "Required before production-ready" item **#4**:

> **Make provider data safely observable, not exposed.** Add content-free media
> health and diagnostics for credential presence, provider outcomes, cache
> freshness/size, logical/physical expiry, purge outcome, and quota state. Never
> include descriptions, transcripts, AI summaries, or full provider responses in
> logs/audits/metrics.

This slice ships that observability surface. It is **observe-only**: it adds no
new fetch/cache write path and does not change provider error semantics
(provider-execution *hardening* — retry/backoff/timeout taxonomy — is a separate
queued follow-up).

## The content-free contract (the load-bearing invariant)

Diagnostics surface **counts, ages, statuses, and outcome categories only**.
They must never read back or expose:

- video descriptions, titles, channel names, transcript text, AI summaries;
- raw provider response bodies or the cached `metadata_json` / `transcript_text`
  *content* (a `COUNT(*) FILTER (WHERE transcript_text IS NOT NULL)` predicate is
  content-free — it reads the column for a null-check and returns only an integer);
- the `YOUTUBE_API_KEY` value (presence/absence only).

This is the same posture as `MediaMaintenanceCog` (logs only a row count) and the
existing health read models (reason-coded, content-free). It is pinned by tests.

## Scope — what ships

### 1. Cache health metrics (DB-backed aggregate, content-free)

- **`utils/db/youtube_video_cache.get_cache_stats()`** — one read-only aggregate
  query. Selects **no content columns**: `total_rows`, `expired_rows`,
  `ok_rows`/`error_rows` (by `fetch_status`), `with_transcript_rows` (null-check
  predicate only), `oldest_fetched_at`, `newest_fetched_at`, and `next_expiry_at`
  (min live `expires_at`). Raw SQL stays isolated in `utils/db/` per the DB rule.
- **`video_reference_cache_service.cache_health()`** — thin service wrapper
  returning a frozen `MediaCacheHealth` dataclass (derives `live_rows`, ages in
  seconds). No raw SQL in the service.

### 2. Provider-request outcome counters (process-local, content-free)

- **`services/youtube_diagnostics.py`** — a process-local runtime counter module
  (state class: process-local runtime, per `architecture.md`). Owns:
  - `record_provider_outcome(category)` + `provider_outcome_counters()` — outcome
    categories `success | key_missing | private_or_deleted | quota_limited |
    timeout | fetch_error` (the bounded `YouTubeFetchError.reason` taxonomy + the
    timeout/success cases the fetcher doesn't currently classify);
  - `record_purge(...)` + `last_purge_snapshot()` — last physical-purge outcome
    (`rows`, `at`, `ok`/`failed`), so the readiness-map "purge status" is visible;
  - `snapshot()` for the `diagnostics_service` provider; `_reset_for_tests()`.
- **`youtube_fetch_service.fetch_video_metadata`** records its outcome category
  then re-raises/returns unchanged (no behaviour change). Adds the Prometheus
  `youtube_provider_request_total{outcome}` counter in `services/metrics.py` for
  the scrape surface.
- **`MediaMaintenanceCog._purge_loop`** records purge success/failure into
  `youtube_diagnostics`.

### 3. Operator surface

- A **`media`** `diagnostics_service` provider (process-local counters + last
  purge), registered in `MediaMaintenanceCog.setup` — shows in `!platform runtime`.
- **`!platform media`** (admin-gated) + `build_media_embed()` async builder:
  credential presence (Y/N, never the value), provider outcome counters, cache
  size/live/expired/with-transcript counts, oldest/newest age, next expiry, last
  purge outcome. Added to the Platform hub "Runtime / status" group.

## Acceptance

1. Docs-only PR opened first (this doc) on the branch; PR born-red.
2. Diagnostics surface the bounded cache-health metrics + provider-request
   outcome counters described above, content-free.
3. `python3.10 scripts/check_quality.py --full` green ·
   `python3.10 scripts/check_architecture.py --mode strict` 0 errors ·
   tests covering **no-raw-payload exposure** pass (assert no content column is
   selected/returned by `get_cache_stats`; assert the `media` snapshot/embed carry
   only counts/ages/categories).

## Out of scope (stays queued)

- Provider-execution hardening (retry/backoff, timeout/error taxonomy, request
  coalescing, quota budget) — the next P0-2 follow-up.
- Maintainer live verification (needs the production credential/runtime).
- The shared URL-parser consolidation + fresh-vs-cached reason-code alignment
  (readiness-map simplification items 1–2).
