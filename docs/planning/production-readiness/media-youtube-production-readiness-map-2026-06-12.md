# Media / YouTube production-readiness map — 2026-06-12

> **Status:** `audit` — verified readiness review (point-in-time); findings are not implementation approval.
> **Mode:** docs-only mapping and production-readiness review; no fixes implemented.
> **Verdict:** **Not production-ready.** The feature is a coherent, default-off AI
> grounding slice with useful unit coverage, but production readiness is blocked by
> retention/privacy gaps, incomplete operational controls and diagnostics, untested
> fetch/cache/render paths, inconsistent error semantics, and no live provider or
> production-database verification.

## Current verified state

- Media/YouTube is an accepted **shared platform + external-API subsystem**, not an
  AI-owned or BTD6-owned pipeline. AI is the only current runtime consumer; BTD6 has
  routing precedence over YouTube links but does not consume video context.
- A URL-driven path exists end to end: AI task router → AI feature-fact gatherer →
  YouTube context service → cache/fetch services → AI provider → optional describe or
  compare renderer. There is no standalone YouTube cog or public media command.
- The path is default-off behind `youtube.context.enabled` and additionally refuses to
  run without `YOUTUBE_API_KEY`. It accepts at most two recognized YouTube URLs per
  message.
- Metadata is fetched from YouTube Data API v3; transcript retrieval uses
  `youtube-transcript-api`. Transcript failures are silently converted to “unavailable.”
- Migration `049` creates `youtube_video_cache`. Successful rows receive a 24-hour
  logical TTL and error rows a 10-minute logical TTL. Reads ignore expired rows, but
  expired rows are not physically removed because the purge helper has no caller.
- Cached `metadata_json` is the full raw provider item, not the bounded/sanitized
  metadata projection used in AI facts. Cached transcript text is sanitized and capped
  at 1,500 characters before storage.
- Provider-derived title, channel, description excerpt, and transcript excerpt have
  control characters and Discord mentions removed before use in facts. Discord sends
  use `AllowedMentions.none()`. Provider thumbnail URLs and raw metadata cache content
  are not validated/sanitized as a whole.
- Logs observed in the subsystem contain a missing-key configuration warning or a video
  ID plus traceback on unexpected metadata failures; no transcript/content logging or
  audit payload publishing exists in the mapped path.
- Source and merged PRs win over prior docs. Live GitHub review on **2026-06-12** found
  one open PR, [#704](https://github.com/menno420/superbot/pull/704), with no relevant
  files. Relevant merged history reviewed: [#338](https://github.com/menno420/superbot/pull/338)
  introduced the runtime slice, [#414](https://github.com/menno420/superbot/pull/414)
  clarified the operator flag, [#518](https://github.com/menno420/superbot/pull/518)
  accepted ADR-007, [#546](https://github.com/menno420/superbot/pull/546) added the
  subsystem folio, [#594](https://github.com/menno420/superbot/pull/594) added the
  generated context pack, and [#631](https://github.com/menno420/superbot/pull/631)
  updated the broader unapproved integrations roadmap. None closes the readiness gaps
  recorded below.

## Scope inventory table

| Item | Path | Type | State | Reason | Evidence |
|---|---|---|---|---|---|
| Shared media ownership decision | `docs/decisions/007-media-youtube-ownership.md` | Architecture/ownership | **Done** | ADR-007 accepts one shared platform media subsystem and explicitly forbids BTD6 ownership. | Decision and consequences name shared ownership and downstream AI/BTD6 consumers. |
| Canonical ownership registry entry | `docs/ownership.md` | Architecture inventory | **Done** | P0-2 (Q-0099): a `media` (YouTube) subsystem row was added to `docs/ownership.md` — owns `youtube_video_cache`, shared-platform (ADR-007), with the data-minimisation + retention owners named. | `docs/ownership.md` § Subsystem ownership `media (YouTube)` row. |
| Subsystem folio and generated context pack | `docs/subsystems/media-youtube.md`; `docs/agent/generated/media-youtube.context.md` | Orientation docs | **Done** | Both route agents to the shared seams and privacy/logging rules. | Folio and generated pack list the source route and active gates. |
| URL-to-context orchestration | `disbot/services/youtube_context_service.py` | Service | **Partial** | End-to-end resolution, sanitization, fact rendering, two-video cap, and negative-cache mapping exist; duplicated URL parsing, inconsistent cached/fresh error codes, and no concurrency controls remain. | `build`, `_resolve_video`, `_reason_to_status`, `_render_facts`. |
| Provider metadata fetch | `disbot/services/youtube_fetch_service.py` | External API service | **Partial** | API-key check, 10-second HTTP timeout, private/deleted and quota handling exist; there is no retry/backoff, shared session, rate/quota diagnostics, response-schema validation, or explicit network exception taxonomy. | `fetch_video_metadata`. |
| Provider transcript fetch | `disbot/services/youtube_fetch_service.py` | External API service | **Partial** | Blocking client is moved to an executor and absence degrades safely, but all exceptions are silently swallowed, there is no timeout/language/provenance/status detail, and failures cannot be distinguished from no transcript. | `fetch_transcript`. |
| Cache service | `disbot/services/video_reference_cache_service.py` | Service/cache policy | **Partial** | Centralized read/write seam and 24-hour/10-minute logical TTLs exist; transcript status is reduced to available/unavailable, error detail is not surfaced, and retention has no purge orchestration. | `get_cached`, `put_cached`, `_CACHE_TTL_*`. |
| Cache DB helper | `disbot/utils/db/youtube_video_cache.py` | DB helper | **Partial** | Raw SQL is isolated, reads exclude expired rows, upsert and purge primitives exist. **P0-2 (Q-0099): `purge_expired_video_cache` now has a caller** — `video_reference_cache_service.purge_expired`, scheduled by `cogs/media_maintenance_cog.py`. Focused DB-helper tests still TBD. | `get_video_cache`, `upsert_video_cache`, `purge_expired_video_cache`; caller in `media_maintenance_cog._purge_loop`. |
| Cache table/migration | `disbot/migrations/049_youtube_video_cache.sql` | Migration/table | **Partial** | Table, expiry index, status constraint, and error fields exist; retention is logical only, raw full metadata can persist indefinitely, and some declared statuses/fields are unused or incompletely projected. | `youtube_video_cache`; `transcript_unavailable` is never written; `transcript_status` is not exposed by `CachedVideoEntry`. |
| Sanitized bounded AI facts | `disbot/services/youtube_context_service.py` | Privacy/safety helper | **Partial** | Mentions/control characters are removed and text fact fields are capped. **P0-2 (Q-0099): the cache write now receives the bounded projection** (`_project_metadata`), so the raw provider payload is no longer stored. Provider text is still prompt-injection-capable untrusted content (delimiting/test suite remains TBD). | `_sanitise`, `_project_metadata`, `_build_video_context`, `_render_facts`; cache write receives `_project_metadata(metadata)`. |
| Video card embed | `disbot/views/youtube_embeds.py` | View helper | **Partial** | Title, AI summary, metadata fields, thumbnail, and transcript availability render; no focused tests validate limits, malicious provider strings, URLs, or embed behavior. | `build_video_card_embed`. |
| Compare embed | `disbot/views/youtube_embeds.py` | View helper | **Partial** | Two-video comparison renders bounded fields, but lacks focused tests and explicit provider-content escaping/validation. | `build_compare_embed`. |
| Describe/compare renderer registration | `disbot/views/youtube_renderers.py`; `disbot/cogs/ai_cog.py` | Render integration | **Partial** | Describe and compare renderers are explicitly and idempotently registered with mentions disabled; no dedicated renderer/embed tests exist and `VIDEO_QA` intentionally remains plain text. | `render_describe`, `render_compare`, `AICog.cog_load`. |
| AI task contract | `disbot/core/runtime/ai/contracts.py` | AI integration | **Done** | Typed tasks exist for describe, compare, and QA. | `AITask.VIDEO_DESCRIBE`, `VIDEO_COMPARE`, `VIDEO_QA`. |
| AI task routing | `disbot/services/ai_task_router.py` | AI integration | **Partial** | One/two-link routing and BTD6 precedence are tested; URL recognition is duplicated across modules and supports only a bounded set of URL forms. | `_YOUTUBE_URL_RE`, `_count_youtube_urls`, `classify`; `test_ai_task_router_youtube.py`. |
| AI feature-fact integration and failure short-circuit | `disbot/core/runtime/ai/natural_language_stage.py` | AI integration | **Partial** | Video facts and render context enter the central AI path; empty grounding blocks provider calls and writes reason-coded AI decision audits without content. Dedicated success/failure integration coverage is thin. | `_gather_feature_facts`; video-task no-facts branch. |
| Operator feature flag | `disbot/core/runtime/feature_flags.py` | Operator/config gate | **Partial** | Default-off operator flag, env override, and UI visibility exist, but its declared owner is `ai`, conflicting with ADR-007 shared platform ownership; no media-specific status/health surface exists. | `YOUTUBE_CONTEXT_ENABLED` has `owner="ai"`. |
| Credential gate | `YOUTUBE_API_KEY` read in `disbot/services/youtube_fetch_service.py` | Credential/config | **Partial** | Credential is env-only and is not logged; it is read once at import and the context service blocks even valid cache hits/transcript-only degradation when absent. No startup/health validation documents whether production has the key. | `_API_KEY`; early API-key return in `youtube_context_service.build`. |
| Dependency declarations | `requirements.txt` | Runtime dependency | **Done** | `aiohttp` and a bounded `youtube-transcript-api` version are declared. | `aiohttp>=3.9.0`; `youtube-transcript-api>=0.6.0,<1.0`. |
| YouTube-context unit tests | `tests/unit/services/test_youtube_context_service.py` | Tests | **Partial** | Covers default-off, missing key, cache hit/miss, private video, no transcript, repeated request, sanitization, and duration parsing with mocked I/O; does not test cache DB semantics, provider failures broadly, error-cache parity, malicious payloads, timeouts, or concurrency. | Nine focused tests, all external I/O mocked. |
| YouTube router unit tests | `tests/unit/services/test_ai_task_router_youtube.py` | Tests | **Done** | Covers describe/QA/compare, supported URL forms, no URL, and BTD6 routing precedence. | Nine router tests. |
| Fetch/cache/DB/migration focused tests | No dedicated files | Tests | **Not Done** | No focused tests directly exercise `youtube_fetch_service`, `video_reference_cache_service`, `youtube_video_cache`, or migration `049`. | Repository test-name/content search. |
| Embed/renderer focused tests | No dedicated YouTube view tests | Tests | **Not Done** | Generic renderer-registry tests exist, but YouTube embeds/renderers themselves are not directly tested. | Repository test-name/content search. |
| Live provider and production DB verification | No recorded current artifact | Verification | **Not Done** | Existing tests mock external I/O; the folio explicitly says production fetch/transcript behavior was not live-verified. | `tests/unit/services/test_youtube_context_service.py`; subsystem folio. |
| Media-specific diagnostics/metrics/operator status | No implementation found | Operations | **Not Done** | Operators can see/edit the generic flag, but cannot inspect provider/key health, quota, fetch outcomes, cache size/age, purge status, or transcript availability rates. | No media diagnostics/metrics registration found. |
| Standalone public media surface | No implementation found | Product surface | **Not Done** | There is no standalone YouTube cog/command/channel-summary UI. This is not required for the current AI slice, but must not be claimed as shipped. | Source inventory and subsystem folio. |

## Required before production-ready

1. **Define and enforce privacy/retention policy.** Decide exactly which provider
   metadata and transcript fields may be stored, store only the bounded projection or
   justify the raw payload, define deletion/purge ownership, schedule physical expiry,
   and verify deletion behavior against production-like PostgreSQL.
2. **Close ownership drift.** Add the accepted shared-media row/service registration to
   `docs/ownership.md` and change the feature flag's ownership classification away from
   `ai`; AI and BTD6 must remain downstream consumers.
3. **Harden provider execution.** Add explicit transcript timeout/error taxonomy,
   metadata network/schema handling, bounded retry/backoff policy, quota/rate controls,
   and stampede prevention for concurrent misses.
4. **Make provider data safely observable, not exposed.** Add content-free media health
   and diagnostics for credential presence, provider outcomes, cache freshness/size,
   logical/physical expiry, purge outcome, and quota state. Never include descriptions,
   transcripts, AI summaries, or full provider responses in logs/audits/metrics.
5. **Resolve cache/error inconsistencies.** Align fresh and cached reason codes; either
   use or remove declared status/error fields; decide whether missing API credentials
   should still permit valid cache hits or transcript-only degradation.
6. **Add direct tests.** Cover fetcher, cache service, DB helper, migration schema,
   embeds/renderers, untrusted content, timeout/network/quota failures, cache expiry and
   purge, concurrent misses, and AI-stage no-grounding/success behavior.
7. **Perform maintainer live verification.** In a controlled guild/channel with the
   production credential/config path, verify metadata, available/unavailable transcript,
   private/deleted video, quota failure, cache hit/expiry/purge, describe/QA/compare,
   BTD6 precedence, logging redaction, and rollback by disabling the flag.

## Bugs, inconsistencies, and risks

- ~~**Retention bug/risk:** `purge_expired_video_cache()` has no caller.~~ **FIXED (P0-2 /
  Q-0099):** `media_maintenance_cog` schedules a 6-hour physical purge via
  `video_reference_cache_service.purge_expired`, so expired transcript excerpts/metadata are
  removed from storage, not just hidden from reads.
- ~~**Raw-data mismatch:** `metadata_json` stores the full unsanitized YouTube API item.~~
  **FIXED (P0-2 / Q-0099):** the cache write now persists only `_project_metadata`'s bounded,
  sanitized projection (no full description, id, statistics, …) — matching the folio's
  “bounded cached metadata” characterization.
- **Fresh/cache error drift:** a fresh private-video failure returns
  `video_private_or_deleted`; the negative cache stores and later returns
  `private_or_deleted`. Similar status-vs-reason drift makes audits/operator behavior
  dependent on cache state.
- **Unused/incomplete schema semantics:** migration status `transcript_unavailable` is
  never written; `transcript_status`, `last_error_code`, and `last_error_at` are selected
  but not exposed through `CachedVideoEntry`; transcript fetch errors are cached as an
  `ok` metadata row with only `unavailable` status.
- **Missing-key ordering:** `build()` checks `_API_KEY` before URL extraction and cache
  lookup. An absent key disables valid cached responses and transcript-only operation,
  despite transcript retrieval not requiring the key.
- **Import-time credential snapshot:** `_API_KEY` is read once at import. Runtime secret
  rotation requires process restart and there is no explicit readiness signal.
- **Silent transcript failures:** all transcript exceptions are swallowed. Operators and
  tests cannot distinguish no transcript, provider/client breakage, blocking-call hang,
  or rate limiting.
- **Untrusted provider data:** descriptions and transcripts enter AI grounding and can
  contain prompt-injection text. Basic Discord sanitization is not a trust boundary;
  provider content must remain clearly delimited/untrusted in AI prompt assembly.
- ~~**Unvalidated provider URLs:** thumbnail URL is passed to Discord embeds without a
  scheme/host policy.~~ **FIXED (P0-2 / Q-0099):** `_safe_thumbnail_url` enforces HTTPS +
  `*.ytimg.com`/`*.youtube.com` host allowlist before the URL is stored or embedded.
  Canonical watch URLs are locally built.
- **Operational fragility:** each metadata fetch creates a new HTTP session; there is no
  retry/backoff, request coalescing, per-guild/global rate limit, quota budget, or media
  metrics/diagnostics.
- **Parser duplication:** supported-URL regexes exist independently in router, context,
  and fetch services, creating drift risk. Some valid YouTube URL variants are not
  recognized.
- **Ownership inconsistency:** ADR-007 says shared platform media; the feature flag still
  declares `owner="ai"`, and `docs/ownership.md` lacks the promised media row.
- **Broad exception traceback risk:** current unexpected metadata logging includes only
  video ID in the message, which is acceptable, but `exc_info=True` should be reviewed
  against future provider-client exceptions so response bodies, URLs with credentials,
  or content never leak through exception strings.

## Privacy, retention, credential, and logging checks

| Check | State | Finding |
|---|---|---|
| Transcript/content absent from normal logs | **Done** | No mapped log statement intentionally includes transcript, description, title, AI summary, or provider response body. |
| Transcript/content absent from audit payloads | **Done** | Media emits no generic audit event; AI decision audit records IDs/task/route/decision/reason/policy hash, not grounding content. |
| Discord mention safety | **Done** | Provider text mentions are replaced before facts and response sends/renderers use `AllowedMentions.none()`. |
| Provider content treated as untrusted | **Partial** | Text is bounded/sanitized for Discord and only the bounded projection is now stored (Q-0099); an explicit prompt-injection delimiting boundary/test suite is still TBD. |
| Bounded transcript storage | **Done** | Stored transcript text is sanitized and capped at 1,500 characters. |
| Bounded metadata storage | **Done** | P0-2 (Q-0099): `_project_metadata` runs before the cache write — only title/channel/published/duration/description-excerpt/validated-thumbnail are persisted; the raw provider item (full description, id, statistics, …) is never stored. Pinned by `test_cache_miss_stores_only_bounded_projection`. |
| Logical expiry | **Done** | Reads require `expires_at > now()`; success/error TTLs are 24 hours/10 minutes. |
| Physical deletion/retention enforcement | **Done** | P0-2 (Q-0099): `media_maintenance_cog` runs a scheduled (6h) `purge_expired_video_cache` so expired content is physically removed, not just hidden from reads. |
| Provider thumbnail URL validated | **Done** | P0-2 (Q-0099): `_safe_thumbnail_url` keeps only HTTPS `*.ytimg.com`/`*.youtube.com` URLs before storage/embed; anything else is dropped. Pinned by `test_safe_thumbnail_url_*`. |
| Credential secrecy | **Done** | API key comes from environment and is not included in logs or DB writes. |
| Credential readiness/rotation | **Partial** | Missing key fails closed, but there is no media readiness diagnostic and key value is captured at import. |
| Error logging redaction | **Partial** | Known errors are reason-coded without content; unexpected tracebacks need an explicit provider-exception redaction guarantee. |
| Public/moderation exposure review | **Partial** | Current surface is AI replies only and mentions are disabled; no explicit guild/channel authority or moderation policy exists for future public media surfaces. |

## Operator/config gate checks

- **Done:** `youtube.context.enabled` is declared, default-off, operator-audience, visible
  through the generic platform flag surfaces, and supports
  `SUPERBOT_FF_YOUTUBE_CONTEXT_ENABLED=on`.
- **Done:** the central AI stage fails closed and avoids calling the AI provider when
  video grounding facts are unavailable.
- **Partial:** `YOUTUBE_API_KEY` is a second effective gate, but is not represented in a
  media health/status surface and blocks cache hits before they are attempted.
- **Partial:** the flag is labeled as AI-owned even though accepted ownership is shared
  media/platform.
- **Not Done:** no media-specific status command/panel exposes effective flag source,
  credential presence, provider/quota health, cache/purge health, or recent reason-coded
  outcomes.
- **Not Done:** no documented production rollback/live-check runbook beyond turning the
  flag off; no verified production credential/config state was available in this review.

## AI and BTD6 dependency checks

- **AI — Partial:** AI consumes the shared `youtube_context_service` through the central
  feature-fact seam. The router defines typed video tasks, the stage prevents ungrounded
  provider calls, and describe/compare use registered renderers. However, provider text
  is untrusted prompt input, video success/failure integration coverage is limited, and
  media ownership is mislabeled on the feature flag.
- **BTD6 — Done for boundary, Partial for mixed-intent behavior:** BTD6 owns no YouTube
  fetch/cache/render path. Router precedence intentionally sends BTD6-looking text with a
  YouTube URL to `BTD6_ANSWER`, which is unit-tested. That means the video reference is
  ignored rather than combined with BTD6 grounding; this is a product limitation, not a
  reason to create a BTD6-owned media pipeline.
- **Shared-context rule — Done architecturally, incomplete in registry:** all current
  YouTube implementation files live in shared services/views/DB helper locations, but
  the ownership registry follow-on and flag-owner correction remain open.

## Simplification opportunities

1. Create one shared video-reference parser/canonicalizer used by router, context, and
   fetch layers instead of three regex implementations.
2. Define a single typed provider-result/error taxonomy so DB statuses, fresh failures,
   cached failures, AI reason codes, diagnostics, and tests cannot drift.
3. Cache only a typed bounded metadata projection rather than a raw provider response;
   this simplifies privacy review, schema validation, and future provider portability.
4. Either fully use `transcript_status`/error fields in the cache read model and
   diagnostics or remove redundant fields after a migration decision.
5. Separate “metadata credential available” from “context can be served” so cache-hit
   and potential transcript-only behavior follow an explicit policy rather than an early
   private-module-variable check.
6. Register media diagnostics and lifecycle/purge ownership once, in the shared platform
   subsystem; do not add parallel AI or BTD6 controls.

## Tests and live-verification gaps

### Existing useful coverage

- `tests/unit/services/test_youtube_context_service.py`: flag/key gates, cache hit/miss,
  successful fetch, private video, no transcript, repeated request, mention sanitization,
  and duration parsing; all external I/O mocked.
- `tests/unit/services/test_ai_task_router_youtube.py`: supported route forms and BTD6
  precedence.
- Generic AI renderer-registry, feature-flag declaration/UI, and natural-language-stage
  tests touch adjacent seams, but do not directly prove the full YouTube path.

### Missing automated coverage

- Metadata fetch status/network/timeout/schema/quota handling and transcript timeout/error
  taxonomy.
- Cache-service TTL/status mapping, DB helper serialization/read expiry/purge, migration
  `049` constraints/index/schema, and scheduled purge behavior.
- Fresh-vs-cached error-code parity, concurrent misses/request coalescing, and quota/rate
  behavior.
- Direct YouTube embed/renderer tests, including malicious provider content, thumbnail
  URL policy, Discord limits, missing fields, and QA plain-text behavior.
- AI-stage success/no-grounding branches with the shared YouTube context seam, plus proof
  that no transcript/content reaches decision audits or logs.
- Prompt-injection delimiting, raw metadata minimization, retention deletion, and
  traceback-redaction checks.

### Missing live verification

- Real YouTube metadata and transcript retrieval from the production network/runtime.
- Available, unavailable, disabled, private/deleted, quota-limited, timeout, and provider
  outage outcomes.
- Production PostgreSQL migration/cache hit/expiry/physical purge behavior.
- Effective operator flag source, credential presence, rollback, and content-free logs in
  a controlled Discord guild/channel.
- Describe, QA, compare, and mixed BTD6+YouTube messages end to end.

## Recommended next session

Run a **shared-media production-hardening planning session**, not an AI or BTD6 feature
session. Keep it docs/tests-first until policy choices are approved:

1. Ratify the data-minimization and retention contract: cached fields, transcript policy,
   TTLs, physical purge schedule/owner, and deletion verification.
2. Define the typed provider/error/status contract and content-free diagnostics/runbook,
   including credential readiness, quota, timeouts, and rollback.
3. Plan the ownership-registry/flag-owner correction and shared parser consolidation.
4. Specify the automated test matrix and a maintainer-controlled live-verification
   checklist.
5. Only after those decisions, implement a bounded hardening slice in the shared media
   subsystem. Do not create AI-owned or BTD6-owned YouTube services.
