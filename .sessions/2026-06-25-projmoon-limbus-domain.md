# 2026-06-25 — Project Moon (Limbus) knowledge domain — runtime PR 1

> **Status:** `in-progress`
> **Run type:** routine · dispatch
> **Branch:** `claude/funny-franklin-adgv45`

## What I'm about to do

Scheduled dispatch fire, no work order → advance the next on-plan slice. Picked the
owner-directed **Project Moon knowledge domain** program (Q-0192, "full parity, all
games"; [plan](../docs/planning/project-moon-knowledge-domain-plan-2026-06-21.md)),
listed as a ▶ startable item in S1.

Decomposed Slice A for reliability in an unattended run:

- **PR 1 (this run — fully offline + safe, no AI hot-path):** a standalone **Limbus**
  knowledge domain — committed *structural/lore* data (the stable, verifiable facts
  with provenance, **not** fragile exact StaticData dumps), a typed data service, a
  resolver + `has_limbus_context()` keyword detector, and a browsable `!pm` / `/pm`
  lookup surface. Proves the domain shape end-to-end without touching BTD6 or the AI
  natural-language stage.
- **PR 2 (next run — flagged for a Q-0086 runtime walk):** wire
  `AITask.PROJMOON_ANSWER` + grounding into `core/runtime/ai/natural_language_stage.py`.

CI mirror green + arch strict 0 before flipping this card to `complete`.
