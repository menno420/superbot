# 2026-06-26 — Project Moon (Limbus) grounding path (PR 2)

> **Status:** `complete`

**Run type:** routine · dispatch

## What this run did
Empty-fire dispatch (no work order). Open bugs were all owner-gated/off-repo (BUG-0011 VPS repro ·
BUG-0019 #1 + BUG-0009 owner-design forks), so this run took the next on-plan, owner-directed
(Q-0192) slice: **Project Moon knowledge-domain PR 2 — the grounding path** (Slice A item 2 of
`planning/project-moon-knowledge-domain-plan-2026-06-21.md`, the explicit ▶ Next in S1-bot.md).

Wired the committed Limbus structural facts into the AI natural-language stage as grounding,
mirroring the BTD6 grounding seam, **default-preserving** (BTD6 path byte-identical):

- **`AITask.PROJMOON_ANSWER`** (`core/runtime/ai/contracts.py`).
- **Router** (`services/ai_task_router.py`): `has_limbus_context` → `PROJMOON_ANSWER`, checked
  **after** BTD6 (disjoint keyword sets; BTD6 keeps priority) and **before** video.
- **`services/projmoon_context_service.py`** (new): `build(text)` resolves the named Limbus entities
  + bounded roster phrases ("list every sinner", "the three damage types") into provenanced,
  cap-bounded grounding fact lines, read-only over `projmoon_data_service`. Enriches Sinners with
  their `literary_origin`, Sins with the colour affinity, E.G.O grades with the rank. Ambiguous bare
  tokens (`he`/`don`/`sang`) excluded so they ride along only via a distinctive alias. Never raises
  (best-effort grounding).
- **`natural_language_stage._gather_feature_facts`**: a `PROJMOON_ANSWER` branch injects those facts
  as `retrieved_facts` (the same seam BTD6/video use).
- **Eval-coverage partition**: `PROJMOON_ANSWER` acknowledged in `_ACK_UNCOVERED_TASKS` (model-eval
  case deferred to the runtime walk + faithfulness-guard follow-up).

**Tests (offline, 27 new):** `tests/unit/services/projmoon/test_projmoon_context_service.py` (10:
per-entity + roster grounding, ambiguous-token exclusion, provenance survival, fact cap,
determinism, degradation), `tests/unit/services/test_ai_task_router_projmoon.py` (router priority +
no over-route), `tests/unit/runtime/ai/test_natural_language_stage_projmoon.py` (the
`_gather_feature_facts` seam). Full CI mirror green (`check_quality.py --full`: 12591+ passed;
`check_architecture --mode strict`: 0 errors).

## Deliberately deferred (documented in-module + plan)
- The **prose-faithfulness validation guard** (plan §6 "hardest correctness risk") — this slice
  injects grounded facts but does not yet post-verify the model reply against them the way
  `btd6_grounding_service` does. Follow-up slice.
- The live **Q-0086 runtime walk** (owner) — the gated AI stage now grounds Limbus; confirm a real
  Limbus Q&A grounds + reads well on both providers.
- Slice A item 1 (StaticData exact-number ingest); then Slice B (extract the shared
  `KnowledgeDomain` seam from BTD6 + Limbus).

## ⟲ Previous-session review
The 2026-06-25 runs (`projmoon-limbus-domain`, `essential-setup-pr2-extras-health`) executed cleanly
and left a **sharp, turn-key ▶ Next** — PR 1's progress banner named exactly the next slice, its
files, and the deferral reason, which let this run start building within minutes with no
re-discovery. That is the handoff discipline working as intended. **One improvement it surfaces:**
the plan's "reuse the … faithfulness guard" phrasing under-specified that prose faithfulness is a
*separate, harder* deferral from the grounding-fact injection — a reader could mistake PR 2 for
"grounding + guard". This run split them explicitly in the module docstring + plan banner + eval
ack. **System improvement:** when a plan step bundles a cheap part and an expensive part under one
verb ("reuse X"), the executor should split them in the ▶ Next on landing — captured here as the
done thing; worth promoting into the dispatch-handoff convention so future bundled steps don't ship
half-done-looking.

## 💡 Session idea
**A `services/grounding_format.py` (or `utils/grounding_format.py`) domain-agnostic home for the
sanitise / cap / provenance helpers.** Right now both BTD6 and projmoon grounding services import
`utils.btd6.grounding_format` — a projmoon service reaching into a `btd6`-namespaced util is a smell,
and it's the first concrete evidence (rule-of-three: BTD6 + Limbus) that these helpers are
*domain-agnostic*. The Slice B `KnowledgeDomain` extraction is the natural moment to lift them out.
Small, mechanical, removes a cross-domain coupling. Not built this run (Slice B scope); flagged so
the seam extraction picks it up.

## ⚑ Self-initiated
none — this is the explicit owner-directed (Q-0192) ▶ Next plan slice, not an invented feature.

## 📤 Run report
- **Run type:** routine · dispatch
- **PR:** #1467 (born-red → complete; auto-merge armed, merges on green Code Quality).
- **What shipped:** Project Moon (Limbus) knowledge-domain PR 2 — the AI grounding path.
- **⚑ Self-initiated:** none.
- **⚑ Owner-decisions:** none (no new owner decision; executes existing Q-0192).
- **⚑ Owner-manual-steps:** the **Q-0086 runtime walk** — verify a live Limbus Q&A grounds + reads
  well on both providers (the gated AI stage now grounds Limbus). Not a deploy step (merge
  auto-deploys); a behavioural live-verification only.
- **Bug-book:** no change (open bugs remain owner-gated/off-repo as noted above).
