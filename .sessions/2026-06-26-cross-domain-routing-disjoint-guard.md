# 2026-06-26 — Cross-domain AI-routing disjointness guard (S1 / Project Moon prep)

> **Status:** `in-progress`
> **Run type:** routine · dispatch
> **Branch:** `claude/funny-franklin-8s9r5j`

## Goal (dispatch run, empty scheduled fire → advance the next plan slice)

Empty scheduled fire. The Project Moon knowledge-domain arc (Q-0192) is the active S1
program; Slice A (grounding path + faithfulness guard) shipped through #1469. The plan's
remaining ▶ Next items are **owner-gated** (the live Q-0086 runtime walk), **fragile-unattended**
(Slice A item 1 — the StaticData exact-number ingest, which poisons grounding if sourced
wrong), or **Slice B** (the risky gated BTD6 seam refactor that wants a runtime-verified
session). The clean, safe, offline-buildable slice both of the last two runs' session ideas
flagged is the **cross-domain `has_*_context` over-route harness**.

It guards a **currently-unguarded invariant**: `ai_task_router.classify` routes BTD6 first,
then Limbus, on the bare comment *"BTD6 keywords never collide with the distinctive Limbus
tokens"* — asserted, never tested. The two detectors even use **different match semantics**
(`has_btd6_context` is a substring scan; `has_limbus_context` is word-boundary), so a future
keyword-set edit could silently make a Limbus question route to BTD6 (starving projmoon) or a
BTD6 phrase trip the Limbus detector. This run pins that invariant with a registry-driven
guard so the next domain (LoR / LobCorp) is a one-line registration, not a re-derivation.

## Plan
- `tests/unit/runtime/ai/test_domain_routing_disjoint.py` — a registry-driven harness:
  per-domain representative corpora route to exactly that domain's `AITask`; structural
  token-disjointness between the substring-keyword domain and the word-boundary domains.
- A short **domain-detector curation recipe** in the ai folio (the prev-review system
  improvement) so the invariant + the "distinctive vs generic token" discipline has a
  durable home instead of living in two code comments.

## Verification (to fill at close)
