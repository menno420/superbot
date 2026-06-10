# 2026-06-10 — PR4 `/myprofile` foundation plan (planning session)

**PR:** #684 (docs-only). **Prompt:** "Continue from where you left off" —
the routed next pick after the consolidated plan completed (#683 merged).

## Shipped

`docs/planning/myprofile-foundation-plan-2026-06-10.md` — the Batch-10/DT09-
selected planning session, in the #674 turn-key shape: §6's backend
inventory **re-verified exact against today's source** (the 4 audited
`ParticipationMutationPipeline` entrypoints, typed accessors, TTL cache,
`ParticipationSchema` registry — XP the sole registrant; zero UI callers);
design envelope = Q-0080 stranger-grade (ephemeral, self-scoped, cooldown,
per-guild keys) + Q-0081 relationship note + the §6 hard rules (no table
collapse; visibility bridge strictly out of scope). Slicing: **PR A**
read-only profile card (zero writes, turn-key) · **PR B** the pipeline's
first UI consumer (one-call-per-action, the editor-stack idioms) · **PR C**
join-time onboarding **gated** on an owner decision (public-bot DM posture).
Routed: roadmap settings row · wizard-plan banner · current-state lane.

## Context delta

- **Needed but not pointed to:** the new router §35 posture decisions
  (Q-0080–Q-0083) — landed mid-day by another session; found via the
  roadmap's new posture block during re-sync. The re-sync-before-acting
  habit is what caught it; a planning session that skipped the sync would
  have produced a plan without the public-bot filter.
- **Decisions made alone:** §6's "draft→preview→commit as template" applied
  by *lane shape* instead (single self-service toggles = direct-lane via the
  audited pipeline; the template reserved for compound editors) — deviation
  reasoned in the plan §3. The hub is NOT gated by `participation.enabled`
  (members always see/set state; gated subsystems get labeled) — the
  honest-store argument, flagged for review in PR A.
- **Flagged for maintainer:** PR C (onboarding) deliberately needs your call
  on DM-vs-in-guild + public-bot DM posture before anyone builds it.

## Open after this session

Execute the plan (PR A turn-key, then PR B) · Help Phase 4 records (gated) ·
AI §7.5 (post-eval) · the eval walk.
