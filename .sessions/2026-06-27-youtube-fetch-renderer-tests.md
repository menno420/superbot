# 2026-06-27 — Media/YouTube focused test coverage (fetch service + renderers/embeds)

> **Status:** `in-progress`

**Run type:** routine · dispatch

## What this run is about to do

Empty-fire dispatch. The advisory phase gate reads **FIX** (correctness-first); the two open bugs are
gated (BUG-0009 data-gated, BUG-0019 #1 owner-gated) and the BTD6/fishing offline product lanes are
exhausted or owner-design-gated. The cleanest offline, zero-runtime-risk, correctness-priority lane is
the **Media/YouTube** subsystem's two still-open readiness **Not-Done** rows
([map](../planning/production-readiness/media-youtube-production-readiness-map-2026-06-12.md)):

1. **Fetch/cache/DB focused tests** — `youtube_fetch_service.py` has *no* dedicated test (the cache
   service + the cache-stats DB primitive already gained tests since the 2026-06-12 map).
2. **Embed/renderer focused tests** — `views/youtube_embeds.py` + `views/youtube_renderers.py` have no
   direct tests.

Plan: add focused unit tests (no runtime change) for `youtube_fetch_service.parse_video_id`,
`fetch_video_metadata` (every error/diagnostics-outcome branch, all I/O mocked), `fetch_transcript`
(degrade-to-`[]`); plus the two embed builders and the two response renderers. Then de-stale the two
readiness rows → Done.

(Close-out — idea / previous-run review / doc audit / run-report footer — appended at flip-to-complete.)
