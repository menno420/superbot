# BTD6 Product Extensions — routing draft

> **Status:** `plan` — planning/routing draft; not implementation approval.
> **Horizon:** Later. **Gate:** ADR-006 provenance/source-health/groundedness requirements and current BTD6 expansion gates.

## Planning contract

- **Status:** roadmap draft; routing only, not approval and not an active implementation lane.
- Source code, merged PRs, binding contracts, subsystem folios, and `docs/current-state.md` outrank this draft.
- Preserve domain-service mutation ownership, direct-vs-draft lane rules, deterministic event flow, auditability, rollback safety, observability, cache invalidation, and testability.
- Before implementation, re-verify source, live PRs, the relevant folio, and every named gate.

## Context and objective

Route owner-selected BTD6 rules/trivia, challenge generation, score/run tracking, and leaderboards without using them to bypass provenance or extraction gates.

## Scope

- Rules/trivia as provenance-backed read surfaces over answerable facts.
- Challenge generation as deterministic constraints plus provenance-backed facts; AI may explain only after AI gates.
- Score/run tracking and leaderboards as a separate user-data/product decision with privacy, anti-cheat, and retention review.

## Out of scope

New extraction paths before gates clear; unsupported absence claims; derived values without evidence; AI-invented rules/challenges; BTD6-owned media pipeline; or unreviewed cross-server score profiles.

## Current state and seams to reuse

Reuse BTD6 source registry/provider/data/fact/grounding/cache/readiness/response/view-model services, provenance schema, freshness/source-health rendering, and shared leaderboard/economy patterns only after ownership review. ADR-007 owns media.

Likely roots: `disbot/services/btd6_*`, `disbot/cogs/btd6*`, `disbot/views/btd6/`, `disbot/utils/db/btd6_data.py`, and the BTD6 data/provenance docs.

## Proposed phases

1. Keep provenance/source-health/decode work authoritative; do not expand extraction for these ideas.
2. Define an answerability-backed rules/trivia read model and freshness UX.
3. Define deterministic challenge constraints and validation using only supported facts.
4. Decide score/run ownership, verification, privacy, retention, anti-cheat, and leaderboard scope before schema work.
5. Consider AI wording/explanation only after AI gates, with deterministic challenge authority retained in BTD6 services.

## Dependencies, risks, and mechanics

ADR-006, provenance schema, source registry/health/cache clarity, groundedness/absence guards, provider parity, and privacy/anti-cheat decisions for user runs. Additive migrations, provenance on every fact, cache invalidation, audit for submissions/moderation, rollback/disable, and source-health tests are required.

## Migration, cache, audit, rollback, and test implications

Any facts or run records require additive provenance-aware migrations and explicit retention. Cache invalidation follows the source registry/ingestion owners and must expose freshness/source health. Audit submissions/moderation and source changes without fabricating evidence. Rollback disables unsupported facts/features and reverts through source-owned pipelines. Tests require provenance, answerability/absence guards, provider parity, stale/degraded sources, deterministic challenge validation, anti-cheat, and privacy.

## Open questions and next session

Score verification and leaderboard scope require owner/product review during a future revision. **Recommended next model/session:** keep Codex mapping-only until BTD6 gates clear; then Opus revises rules/trivia and run-tracking ownership.
