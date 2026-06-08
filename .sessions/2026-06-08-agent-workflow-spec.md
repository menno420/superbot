# 2026-06-08 — Agent stage spec (60-question batch → new doc)

## What happened

Ran a 60-question multiple-choice batch with the maintainer covering the full operational
spec for every stage of the multi-agent pipeline: **Analysis**, **Decisions**,
**Revision**, **Prompt Forge**, and the **Executor** agent.

All 60 answers confirmed the recommended direction, with one exception: **Q22** —
handoff sections in generated prompts → maintainer chose **Never** (C) over the
recommended "cross-stage only" (B). No handoff section in Prompt Forge output.

## Shipped

- **`docs/owner/agent-workflow-spec.md`** (new) — the canonical operational spec for all
  five stages. Covers: stage scopes, what each stage must not do, output structures
  (Analysis four-tier severity, Revision five-section output, Decisions structured
  direction, Prompt Forge standard prompt anatomy), cross-cutting rules (truth layers,
  one-fact-one-home, ideas routing, gate checks, act-vs-ask, docs maintenance as
  first-class work). Q-0013 in the router records the full batch.
- **`docs/AGENT_ORIENTATION.md`** — added "Working on the multi-agent pipeline /
  generating session prompts" task route pointing to agent-workflow-spec.md as the entry
  point.
- **`docs/owner/README.md`** — added agent-workflow-spec.md to the companion docs list.
- **`docs/owner/ai-project-workflow.md`** — added a link to the spec after the stage
  table in §2.
- **`docs/owner/maintainer-question-router.md`** — added Q-0013 recording the batch and
  routing result.

## Context delta

- **Needed but not pointed to:** nothing — the orientation and folios were sufficient to
  identify the correct output home (a new spec doc under `docs/owner/`) and the wiring
  targets (AGENT_ORIENTATION, README, ai-project-workflow).
- **Pointed to but didn't need:** none; docs-only session with no code exploration
  required.
- **Discovered by hand:** Q22 (handoff sections in prompts) deviated from the recommended
  answer. Worth noting: when the maintainer departs from a recommendation, record the
  actual answer faithfully in the spec and the router — don't silently correct it toward
  the recommendation.
