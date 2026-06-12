# Media / YouTube subsystem — folio

> **Status:** `living-ledger` (area index). Source + ADR-007 win.
> **Last updated:** 2026-06-06.

## What & where

Media/YouTube is shared platform infrastructure for fetching, caching, grounding,
and rendering video references. Start in `disbot/services/youtube_context_service.py`,
`disbot/services/youtube_fetch_service.py`,
`disbot/services/video_reference_cache_service.py`,
`disbot/utils/db/youtube_video_cache.py`, migration
`disbot/migrations/049_youtube_video_cache.sql`, and
`disbot/views/youtube_embeds.py` / `disbot/views/youtube_renderers.py`.

## Rules & approved structures (binding — link, don't restate)

- **ADR-007** declares media/YouTube a shared platform subsystem, not BTD6-owned.
  New media features register here and keep AI/BTD6 consumers downstream.
- `docs/server-logging.md` defines fail-safe operational/audit routing expectations;
  media expansion must not leak transcript/content data into logs or audit payloads.
- Provider content must be treated as untrusted external data. Before expansion,
  review privacy, retention/cache expiry, credentials, transcript/content safety,
  moderation exposure, provenance/grounding, and guild/channel authority.

## Current state

- Fetch, context, cache, DB, embed, and renderer seams exist. YouTube context is
  operator/config gated, and migration `049` stores bounded cached metadata,
  transcript/fetch status, errors, and expiry.
- YouTube is env-gated and runs degraded in the sandbox when required keys/network
  behavior are unavailable; degraded does not mean broken, and production behavior
  has not been live-verified in this mapping session.
- There is no standalone YouTube cog in the mapped source. Treat current media as
  shared support infrastructure, not an already-shipped public channel-summary UI.

## Plans / pending approval

Future YouTube/channel-summary or content-status direction must be promoted through
an approved plan. It should reuse the shared fetch/cache/context/render seams,
identify the public/operator surface, define provenance and freshness, and specify
logging, privacy, moderation, test, and rollback behavior.

## Ideas (not approved)

`docs/ideas/ai-extra-tool-capability-ideas.md` contains YouTube/Twitch/content-status
and connector ideas. They are not approval for a connector, summary tool, or public
media command.

## Next candidates

1. Document/verify cache retention, error taxonomy, source freshness, credential
   handling, and what data may enter logs before adding a new surface.
2. If a channel-summary/content-status feature is promoted, choose a bounded,
   read-only first slice and explicitly review privacy/security/moderation risks.
3. Verify degraded behavior and provider failures in tests; require maintainer live
   verification before claiming production fetch/transcript behavior.

## Related docs

`docs/decisions/007-media-youtube-ownership.md`, `docs/server-logging.md`,
`docs/current-state.md`, `docs/subsystems/ai.md`, `docs/subsystems/btd6.md`,
`docs/ideas/ai-extra-tool-capability-ideas.md`, and the verified
[2026-06-12 production-readiness map](../planning/production-readiness/media-youtube-production-readiness-map-2026-06-12.md).

## Broader integration routing (not approved)

The [integrations/media/voice/website roadmap draft](../planning/integrations-media-voice-website-roadmap-2026-06-08.md) routes provider-alert, activity, voice, and website concepts around ADR-007 and the required privacy/credential/moderation/retention decisions. It does not approve a new provider or public media surface.
