# ADR-006: BTD6 data provenance + owner-per-fact-type matrix

**Status:** Accepted (2026-06-05)
**Supersedes:** none
**Superseded by:** none

> **Accepted.** The provenance object + owner matrix + Hybrid storage choice are
> ratified and binding. This ADR still does **not** hand-design the schema; a
> follow-on docs/schema PR does that. BTD6 data extraction stays **PAUSED** until
> that PR lands (the RC-10 gate).

## Context

BTD6 facts have many composition/read owners and two different freshness models
(static extracted data vs live-source lookups) that are not applied uniformly.
RC-10 (audit consolidation, Agent D) requires a single provenance model and a
clear owner *per fact-type* before any further extraction, so a given answer's
source is always attributable and AI grounding stays auditable.

## Options / open questions (maintainer to decide)

1. **Provenance object:** adopt a single `DataProvenance` / `SourceAttribution`
   value object that every BTD6 fact carries (source, fetched-at, freshness
   model). *Recommended:* yes — one composed object, not per-consumer ad-hoc
   fields.
2. **Owner-per-fact-type matrix:** name the owning service for each fact-type
   (stats, paragon, map metadata, cash/eco, obstacles, …) so reads/compositions
   route through one owner. *Recommended:* yes — the view-model service
   (`services/btd6_view_model_service.py`) composes; query services own reads.
3. **Storage of extracted statics (the main open call):** `btd6_data_blobs` vs a
   source-registry table vs both. This has migration + freshness implications and
   is the decision only the maintainer should make.

## Decision

**ACCEPTED** (maintainer-ratified 2026-06-05):

1. **Provenance object:** every BTD6 fact carries a single composed
   `DataProvenance` / `SourceAttribution` value object (source, fetched-at,
   freshness model) — binding.
2. **Owner-per-fact-type matrix:** the view-model service
   (`services/btd6_view_model_service.py`) composes; the query services own reads —
   binding.
3. **Storage = Hybrid:** extracted statics remain in `btd6_data_blobs` (the fact
   store); the provenance object **references** source-registry rows
   (`btd6_sources` / `btd6_source_registry`) for source health + freshness. No new
   storage system is introduced.

The provenance object + matrix are now binding, but **BTD6 extraction stays paused**
(RC-10 gate): a follow-on docs/schema PR implements the provenance contract before
any new extraction resumes.

## Consequences

- Once ratified, BTD6 extraction can resume against a defined provenance contract.
- Until then, no new BTD6 data extraction (Ideas Lab §6; roadmap gate).

## Re-evaluation criteria

Ratify when the maintainer fixes the storage model; the provenance object + matrix
then become binding and a docs/schema PR implements them.
