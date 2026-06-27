# 2026-06-27 — YouTube cache DB-primitive test coverage (dispatch slice 2)

> **Status:** `in-progress`

**Run type:** routine · dispatch

## What this run is about to do

Second slice of the same empty-fire dispatch run (slice 1 = PR #1485, YouTube fetch/renderer tests,
merged). Advances the remaining Media/YouTube readiness row — **Fetch/cache/DB/migration focused
tests** (left `Partial` by slice 1). The `youtube_video_cache` DB primitives `get_video_cache`,
`upsert_video_cache`, and `purge_expired_video_cache` have **no** dedicated test (only `get_cache_stats`
does, via the content-free contract test). They are offline-testable by mocking `pool.get()` (the
pattern the existing cache-stats test uses).

Plan: add `tests/unit/utils/db/test_youtube_video_cache.py` covering the TTL `expires_at > now()` read
filter, the upsert param/JSON-serialization contract, and the `purge` "DELETE N" → int parse — all with
a mocked pool connection, no live DB. Migration 049 application itself stays a live-DB concern
(`[needs-live-bot]`); honest row update.

(Close-out enders appended at flip-to-complete.)
