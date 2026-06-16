# 2026-06-16 — BTD6 paragon base-cost comparison floor (AI §7.5)

> **Status:** `in-progress`

**Branch:** `claude/magical-rubin-u3arq6` · **Date:** 2026-06-16 · scheduled dispatch (empty work
order → advance the next plan slice).

## What I'm about to do

The live ▶ NEXT buildable plan-first lane is **the AI §7 next workflow family**. §7.5 (multi-entity
comparison) has now shipped three of its four listed members — tower-vs-tower cost (#946),
by-difficulty cost (#950), round-range cash (#955). The one member still flagged *not yet built* in
the plan (`docs/ai/ai-complex-request-tool-orchestration-plan.md` §7.5) is **paragon
degree/resource scenarios**. I'm building the **paragon base-cost** comparison — the paragon entity's
headline resource number (its tier-6 build price), fully grounded in `utils/btd6/paragon_math`'s
committed `BASE_PRICES_MEDIUM` table and difficulty-aware via `base_price`, so it ships under Q-0048
with no prod-check exactly like the sibling cost builders.

Question shape: "is Glaive Dominus or Ascended Shadow cheaper?" / "which paragon costs the most?" —
rank the base build price of **two or more** paragons. This is the §7.5 comparison member of the
BUG-0009 "grounded values, wrong assembly" class: each paragon's base price is grounded, but a model
can mis-state *which is cheaper / by how much*, which the value-only faithfulness guard cannot catch.

Plan (mirrors #946/#950/#955 exactly, contained + test-covered):
- `btd6_data_service.compare_paragon_costs(names, *, difficulty="medium")` — resolve each name via
  `paragon_math.resolve_paragon`, price via `paragon_math.base_price`, dedup on paragon id, rank
  **ascending** (cheapest first), fail closed (<2 distinct priceable paragons).
- `btd6_context_service.deterministic_paragon_cost_comparison_reply` — high-precision floor: the
  existing cost-compare cue **+ an explicit `paragon` token** + two-or-more resolved paragons.
  Appended to `deterministic_btd6_list_reply` **before** the tower cost builders, and the two tower
  cost builders gain a `paragon`-present defer so the exclusivity invariant stays exactly-one-fires
  (a "dart/ninja paragon" question must not reach the base-tower cost builder).
- Tests: a new per-builder test module + the §7.5 exclusivity corpus entry (the invariant test
  iterates the live `_BTD6_LIST_BUILDERS` tuple, so the new builder needs a corpus phrase).

If capacity remains: a second clean slice (next plan member, a bug-book sweep, or a docs de-stale).
