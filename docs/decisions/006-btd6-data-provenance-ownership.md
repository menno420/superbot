# ADR-006: BTD6 data provenance + owner-per-fact-type matrix

**Status:** Proposed — awaiting maintainer ratification (drafted 2026-06-05)
**Supersedes:** none
**Superseded by:** none

> **This ADR is a DRAFT.** It records the decision to be made and the recommended
> shape; it is **not** ratified and it does **not** design a schema. BTD6 data
> extraction stays **PAUSED** until this is Accepted (the RC-10 gate).

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

**DEFERRED — the maintainer ratifies the provenance object + matrix + storage
choice.** This draft names owners and recommends the single-object approach; it
does **not** design the schema or pick storage. Extraction remains paused.

## Consequences

- Once ratified, BTD6 extraction can resume against a defined provenance contract.
- Until then, no new BTD6 data extraction (Ideas Lab §6; roadmap gate).

## Re-evaluation criteria

Ratify when the maintainer fixes the storage model; the provenance object + matrix
then become binding and a docs/schema PR implements them.
