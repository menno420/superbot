# 2026-06-26 — Project Moon (Limbus) grounding path (PR 2)

> **Status:** `in-progress`

**Run type:** routine · dispatch

## What I'm about to do
Empty-fire dispatch. Open bugs are owner-gated/off-repo (BUG-0011 VPS repro · BUG-0019 #1 /
BUG-0009 owner-design). Next on-plan, owner-directed slice = **Project Moon knowledge-domain
PR 2** (Slice A item 2, the grounding path), the explicit ▶ Next in S1-bot.md /
`planning/project-moon-knowledge-domain-plan-2026-06-21.md` (Q-0192).

Wire Limbus structural facts into the AI natural-language stage as grounding, mirroring the BTD6
grounding seam and keeping the BTD6 path byte-identical:
- `AITask.PROJMOON_ANSWER` (contracts).
- Router: `has_limbus_context` → `PROJMOON_ANSWER` (after BTD6, before video).
- New `services/projmoon_context_service.build()` — resolves named Limbus entities + bounded
  roster expansion to provenanced grounding fact lines (read-only over `projmoon_data_service`).
- `natural_language_stage._gather_feature_facts` branch → inject those facts.
- Offline-unit-tested; **default-preserving** (only Limbus-detected messages change; no BTD6 change).

**Flagged:** touches the gated AI stage — the live model-loop check is the owner's Q-0086 runtime
walk (the established AI-feature pattern). The prose-faithfulness *validation* guard (§6 "hardest
risk") is deliberately **deferred** to a follow-up; this slice injects grounding facts only.
