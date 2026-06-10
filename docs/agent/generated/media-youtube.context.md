# Agent Context Pack — Media / YouTube

> **Status:** `reference` — generated orientation aid (NOT source of truth).
> Generated: 2026-06-10 · Subsystem key: `media-youtube`

> **NOT SOURCE OF TRUTH.** This file is generated from `docs/agent/index.yml`.
> Canonical docs listed under *Binding docs* always win over this pack.
> Edit the index, then re-run `python3.10 tools/agent_context/build_pack.py`.

## Folio (start here)

[`docs/subsystems/media-youtube.md`](../../../docs/subsystems/media-youtube.md) — canonical area index, debug router, current state, next candidates.

## Binding docs (read before editing)

- docs/architecture.md
- docs/ownership.md
- docs/runtime_contracts.md
- docs/decisions/007-media-youtube-ownership.md
- docs/server-logging.md

## Likely source areas

- disbot/services/youtube_context_service.py
- disbot/services/youtube_fetch_service.py
- disbot/services/video_reference_cache_service.py
- disbot/utils/db/youtube_video_cache.py
- disbot/views/youtube_embeds.py
- disbot/views/youtube_renderers.py
- disbot/migrations/049_youtube_video_cache.sql

## Related subsystems

- `docs/agent/generated/btd6.context.md`
- `docs/agent/generated/ai.context.md`

## Do NOT create

These systems already exist — duplicating them is the main source of
architectural drift in this repo.

- A BTD6-owned or AI-owned YouTube pipeline — ADR-007: media is shared platform only
- Logs or audit payloads that leak transcript/content data — docs/server-logging.md

## Active gates

- YouTube is operator/config gated.
- Provider content is untrusted external data — review privacy, retention, credentials, and guild/channel authority before any expansion.

## Verification commands

Run these before pushing any change to this subsystem:

```
python3.10 scripts/check_quality.py --full
python3.10 scripts/check_architecture.py --mode strict
```

---

*This pack is orientation only.  When this file and a canonical doc
disagree, the canonical doc wins.  When this file and source code
disagree, source code wins.*
