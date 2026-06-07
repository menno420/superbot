# BTD6 data / tools subsystem — folio

> **Status:** `living-ledger` (area index). Source + ADR-006 + current state win.
> **Last updated:** 2026-06-06.

## What & where

BTD6 spans reference/data ingestion, provenance/source registry, caches, live
queries/events, strategies, browsers, calculators, and grounded AI context. Start in
`disbot/cogs/btd6/`, `disbot/cogs/btd6_cog.py`, the other `disbot/cogs/btd6_*_cog.py`
files, `disbot/services/btd6_*`, `disbot/views/btd6/`, `disbot/utils/db/btd6_*`,
`disbot/utils/settings_keys/btd6.py`, and `disbot/data/btd6/`.

## Rules & approved structures (binding — link, don't restate)

- **ADR-006** (`docs/decisions/006-btd6-data-provenance-ownership.md`) binds the
  provenance object, owner-per-fact-type matrix, hybrid storage choice, and source
  registry linkage. Extraction remains paused until a follow-on docs/schema PR
  implements that contract.
- Provider/provenance checks, caching/source-health clarity, and AI behavior/config
  correctness are gates, not optional polish. `docs/current-state.md` owns the global
  gate wording.
- Preserve groundedness and absence-claim guards. Derived values must carry enough
  evidence/provenance to distinguish sourced facts from calculations; see
  `docs/btd6/btd6-derived-value-groundedness-finding.md` and
  `docs/btd6/btd6-absence-claim-guard-design.md`.
- BTD6 AI behavior is configuration/capability gated; shared media/YouTube is owned
  by `docs/subsystems/media-youtube.md`, not BTD6 (ADR-007).

## Current state

- BTD6 data extraction is **paused pending implementation of the ADR-006 provenance
  schema**. Do not resume extraction or add new mappings in a folio/mapping session.
- The repo already contains source registry, ingestion, fact-store, data-provider,
  cache, grounding, resolver, live-query, strategy, and ops-readiness services plus
  migrations/data. Their existence is not proof that provenance/source health is
  sufficient for new extraction.
- Existing UI direction is visible in live-event, tower, hero, leaderboard, strategy,
  CT-map, and paragon browser/calculator views. Paragon and other env-gated paths may
  run degraded in the sandbox; do not call them broken or production-verified.

## Plans / pending approval

The BTD6 docs describe decode/extraction, pipeline, backend, cloud-data, AI tool
calling, and smoke-test directions. They are indexed in
[`../btd6/README.md`](../btd6/README.md) and remain subordinate to ADR-006 and the global
AI/BTD6 gate. Do not duplicate their detailed sequences here.

## Ideas (not approved)

Further live-event/tower/hero/leaderboard browsing, richer paragon calculation, and
additional AI tools are candidates only after provenance, caching, source health, and
behavior/config gates are satisfied.

## Next candidates

1. Before restarting extraction, verify ADR-006's provenance schema is implemented,
   source-registry references and owner matrix are enforced, migrations are safe,
   and cache/source-health behavior is observable and tested.
2. Reconcile provider/provenance and freshness claims across the source registry,
   ingestion supervisor, fact store, cache, and rendered responses.
3. Only after the global gate clears, choose a bounded browser/calculator/AI change
   and prove derived-value groundedness plus degraded-source behavior.

## Related docs

`docs/decisions/006-btd6-data-provenance-ownership.md`, the BTD6 docs indexed in
[`../btd6/README.md`](../btd6/README.md),
`docs/audits/agent-d-btd6-ai-subsystem-audit-2026-06-05.md`,
`docs/current-state.md`, `docs/subsystems/ai.md`, `docs/subsystems/media-youtube.md`.
