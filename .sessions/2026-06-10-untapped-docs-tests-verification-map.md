# Session — Untapped docs/tests/verification map — 2026-06-10

## Goal

Create a mapping-only audit of documentation drift, test/characterization gaps, plan sequencing conflicts, verification debt, and implementation readiness after the merged platform-surface maps.

## Scope and boundary

- Created `docs/planning/untapped-docs-tests-verification-map-2026-06-10.md`.
- Did not edit runtime source, tests, shared ledgers, current-state, roadmap, folios, or owner router.
- Did not duplicate parallel Codex Agent 1's runtime/services/workflows lane or Agent A/B command/panel inventories.

## Live state

- Mapped HEAD: `ed6269767c5614894fb3cdce2985d6487dc981b4`.
- `gh` was unavailable; GitHub REST returned zero open PRs.
- Confirmed recent merges #645, #644, #643, #638, #642, #640, #641, and #639.

## Main outcomes

- Identified server-management PR14 queue truth as the highest-severity stale-doc risk because the tracker/current-state/roadmap still queue an already-shipped hub.
- Consolidated FIND-A01–A09 and FIND-B01–B10 into owners, gates, required tests/docs, and bounded implementation candidates.
- Identified the command-surface classification completeness invariant, Help effective-projection seam tests, and Settings Phase 2 declaration coverage as the highest-value characterization work.
- Preserved gates around governance setup, broad AI work, Help overlays, and production-only health verification.
- Proposed owner-question candidates without editing the router.

## Verification

Final doc, quality, and architecture checks are recorded in the mapping document and commit/PR summary.
