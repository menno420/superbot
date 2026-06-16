# Session — BTD6 difficulty cost-comparison floor (AI §7.5)

> **Status:** `in-progress`

**Branch:** `claude/magical-rubin-swi7wp` · **Date:** 2026-06-16 · scheduled dispatch (no work order → advance the next plan slice)

## What I'm about to do

The live ▶ NEXT buildable plan-first lane is **the AI §7 next workflow family**. The §7.5
multi-entity comparison floor shipped its first member in #946 — *tower-vs-tower* cost comparison
(`compare_crosspath_costs` + `deterministic_cost_comparison_reply`). The §7.5 plan explicitly lists
**difficulty cost comparisons** as the next member, still unbuilt: "is a 0-4-1 desperado cheaper on
medium or impoppable?" ranks the **same** upgrade state across difficulties — a single tower, so the
#946 multi-tower builder returns `None` and the question falls through to the model, which can
mis-state which difficulty is cheaper (the BUG-0009 "grounded values, wrong assembly" class the
floor exists to own).

Plan (mirrors the #946 shape exactly, contained + test-covered):
- `btd6_data_service.compare_difficulty_costs(tower, code, difficulties)` — the §7.5 difficulty
  rank/diff primitive; prices the one upgrade state once (`crosspath_cost` already returns every
  difficulty), ranks the named difficulties ascending, fails closed (<2 distinct valid difficulties).
- `btd6_context_service.deterministic_difficulty_cost_comparison_reply` — high-precision floor:
  cost-compare cue + **exactly one** resolvable `(tower, crosspath)` (≥2 is the multi-tower builder)
  + **≥2** named difficulties; `None` otherwise. Appended to the `deterministic_btd6_list_reply`
  dispatcher (auto-wires the pre-emptive BTD6 floor).
- Tests covering the firing case, base/crosspath, 3-difficulty ranking + spread, and the negatives
  (single difficulty, two towers → multi-tower builder, no cost cue, strategy).
