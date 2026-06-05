# ADR-007: YouTube / media is a shared platform subsystem, not BTD6-owned

**Status:** Proposed — awaiting maintainer ratification (drafted 2026-06-05)
**Supersedes:** none
**Superseded by:** none

> **This ADR is a DRAFT.** It records the ownership question and recommended
> answer; it is **not** ratified.

## Context

YouTube/media services exist (e.g. `services/youtube_context_service.py` and a
`video_reference` concept) but their ownership is undocumented in
`docs/ownership.md`. RC-12 (audit consolidation, Agent D) flagged the ambiguity:
is media a BTD6 concern or a shared platform concern? Leaving it unowned makes any
new media feature an undeclared architectural change.

## Options

- **M1 (recommended):** Declare a shared `video_reference` / media subsystem
  (platform + external-API), explicitly **not** owned by BTD6. BTD6 consumes it
  like any other caller.
- **M2:** Fold media under BTD6 ownership. (Not recommended — it couples a general
  capability to one feature and contradicts the read-heavy BTD6 ownership split.)

## Decision

**DEFERRED — the maintainer ratifies M1/M2.** Recommended: **M1**. Once ratified,
`docs/ownership.md` gains a media-subsystem ownership row and the relevant
services register under it.

## Consequences (of M1)

- Media has one declared owner; new media features register there, not in BTD6.
- Clarifies AI grounding provenance for video references (pairs with ADR-006).

## Re-evaluation criteria

Ratify when the maintainer confirms the subsystem boundary; an ownership-doc PR
then records it.
