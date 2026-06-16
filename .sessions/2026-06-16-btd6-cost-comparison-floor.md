# Session — AI §7.5 deterministic BTD6 cost-comparison floor

> **Status:** `in-progress`

## What this is

Same dispatch run as the permission-allowlist PR (#945). After shipping the owner-redirect, this is
the **routine's actual work order**: advance the plan with the next buildable slice. The `ready`
decade-queue is consumed; the live ▶ plan-first slice is **AI §7 next workflow family**. Building
**§7.5 — multi-entity comparison** at its highest-traffic, deterministic case: a **BTD6
cost-comparison floor builder**.

## Why this slice

Comparison questions ("is a 0-4-1 desperado cheaper than a 2-0-4 sniper", "compare the cost of a
5-0-0 ninja and a 0-5-0 wizard") are the **BUG-0003/0005 + BUG-0009 "wrong assembly" class**: the
model freelances/mis-ranks the arithmetic, and the value-only faithfulness guard can't catch a
mis-*ranking*. The proven fix shape (BUG-0009): the deterministic layer OWNS the labelled answer,
served as a pre-emptive floor before the model. Deterministic ⇒ ships under Q-0048 (no prod-check).

## Plan

- `btd6_data_service.compare_crosspath_costs(candidates, *, difficulty="medium")` — pure §7.5
  rank/diff primitive: price each `(tower, code)` via the existing `crosspath_cost`, rank ascending,
  return cheapest/most-expensive/spread.
- `btd6_context_service.deterministic_cost_comparison_reply(message_text)` — fires only on a
  high-precision cost-compare cue + ≥2 resolvable `(tower, code)` candidates (multi-tower scan,
  crosspath paired from the chars before each tower; base `000` if none); `None` otherwise. Appended
  to the `deterministic_btd6_list_reply` dispatcher (auto-wires the floor in `natural_language_stage`).
- Tests: crosspath compare · base-tower compare · difficulty cue · negatives (single tower /
  strategy / no cost cue / no comparison).
- **Substantial** (a new §7 family + new external-facing answer path) → label `needs-hermes-review`,
  do NOT self-merge (Q-0117).
