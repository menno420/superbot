# Integrations, Media, Voice, and Website — roadmap draft

> **Status:** `plan` — planning/routing draft; not implementation approval.
> **Horizon:** Later/Someday. **Media boundary:** ADR-007.
> **Owner decisions Q-0041 + Q-0042 — answered (2026-06-09, router):** **Q-0041:**
> YouTube-alerts pilot first (ADR-007 seams) → Twitch on the same contract →
> Spotify/Steam after an account-link consent decision; operator-owned keys, dual
> opt-in, metadata-only bounded caches, fail-quiet degradation; voice behind its own
> architecture review, speech recognition last (deferred, not dropped). **Q-0042:**
> website = yes as a destination, staged (read-only companion via Discord OAuth2 first;
> management later through the same audited services; no web-only authority; bot
> process never serves the site); timing stays **Someday**. Both decide posture/order
> only — implementation still needs the normal promotion path.

## Planning contract

- **Status:** roadmap draft; routing only, not approval and not an active implementation lane.
- Source code, merged PRs, binding contracts, subsystem folios, and `docs/current-state.md` outrank this draft.
- Preserve domain-service mutation ownership, direct-vs-draft lane rules, deterministic event flow, auditability, rollback safety, observability, cache invalidation, and testability.
- Before implementation, re-verify source, live PRs, the relevant folio, and every named gate.

## Context and objective

Group Twitch/YouTube alerts, Spotify/Last.fm, Steam/gaming APIs, music playback, sound effects, speech commands, and a full web dashboard around shared provider/privacy/credential/retention/moderation/degraded-service concerns. This avoids provider-specific pipelines and prevents the website from becoming a second control plane.

## Scope

Read-only provider adapters and status/alert concepts; opt-in delivery; shared credential/health/freshness/provenance behavior; voice/music concept review; and a future web projection of canonical Discord-native reads/actions.

## Out of scope

Implementation before Q-0041, public media surfaces without privacy/provenance/moderation review, a BTD6- or AI-owned YouTube pipeline, storing unnecessary content/transcripts, or a website with independent mutation authority.

## Current state and seams to reuse

ADR-007 makes media a shared platform subsystem. Existing YouTube fetch/context/cache/render seams are the first reuse target. Health/readiness, settings/bindings, audit/event delivery, command access, and canonical panels/services must remain authoritative. Voice has no approved owner and requires an architecture/product decision.

Likely roots: `disbot/services/youtube_context_service.py`, `disbot/services/youtube_fetch_service.py`, `disbot/services/video_reference_cache_service.py`, `disbot/utils/db/youtube_video_cache.py`, `disbot/views/youtube_*`, provider settings/bindings, health/diagnostics, and canonical domain services exposed through panels.

## Proposed phases

1. **Decision pack:** answer Q-0041/Q-0042; define provider allowlist, credential ownership, consent, retention/deletion, moderation, cost/rate limits, and degraded-provider UX.
2. **Shared provider contract:** health/freshness/provenance/cache/alert-delivery interfaces extending media ownership; no new public command yet.
3. **One read-only/opt-in alert pilot:** choose YouTube or Twitch only after review, with safe disable and rate limits.
4. **Additional read integrations:** Spotify/Last.fm and Steam only if the shared contract proves reusable.
5. **Voice concept:** separate architecture review for playback/SFX/speech privacy, permissions, moderation, and operational cost.
6. **Website concept:** read-only projection first; reuse canonical authentication/authority/audit and domain mutation services if later approved.

## Dependencies, risks, and mechanics

Q-0041/Q-0042, ADR-007, privacy/security/moderation review, secrets management, provider terms, rate limits/cost, retention/deletion, and abuse controls. Caches need provenance/freshness and bounded retention. Provider outages must degrade safely. Mutations/delivery require audit, permission re-checks, idempotency, and rollback/disable.

## Migration, cache, audit, rollback, and test implications

Provider/account/config schemas must be additive and deletion-aware. Cache only bounded, provenance/freshness-labelled data and invalidate on provider/config changes. Audit credential/config/delivery/control actions without logging secrets or private content. Rollback is provider/feature disable plus deletion/revocation support. Tests need consent, permissions, secret redaction, rate limits, outages, stale caches, duplicate alerts, moderation, and website authority parity.

## Open questions and next session

- Q-0041 + Q-0042 answered (2026-06-09) — see the router entries for the full marked-up
  answers (provider order, consent/retention/degradation detail, website staging).
- **Recommended next model/session:** Opus decision/revision (answers now exist); Codex
  mapping-only until gates clear.
