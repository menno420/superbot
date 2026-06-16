# 2026-06-16 — BTD6 hero cost-comparison floor (night-queue slot 1)

> **Status:** `in-progress`

## What I'm about to do
Scheduled dispatch, empty work order → the live ▶ Next action points at the
**night queue** (`planning/night-queue-2026-06-16.md`). Building the topmost
`TODO` slice: **Slot 1 — Hero cost comparison (§7.5)**.

A deterministic floor builder that ranks the base cost of two-or-more heroes
("is Quincy or Benjamin cheaper?") — the BUG-0009 "grounded values, wrong
assembly" class, on the hero entity. Mirrors #962 (paragon cost comparison)
almost exactly.

- `btd6_data_service.compare_hero_costs(names, *, difficulty)` — resolve each
  hero, dedup on id, rank ascending by difficulty-scaled base cost, fail closed
  on <2 distinct.
- `btd6_context_service.deterministic_hero_cost_comparison_reply` — fires on a
  cost-compare cue + ≥2 resolved heroes (defers on a paragon cue + strategy);
  registered in `_BTD6_LIST_BUILDERS`.
- Tests: `tests/unit/services/test_btd6_hero_cost_comparison.py` + one
  `_SHOULD_FIRE` corpus phrase in the exclusivity invariant.

Ships under Q-0048 (read-only deterministic floor, no prod-check).
