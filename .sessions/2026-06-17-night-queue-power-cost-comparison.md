# Session — night-queue slot 2: power (activated-ability) cost comparison floor

> **Status:** `in-progress`

## Origin

Scheduled dispatch, empty work order → the live ▶ NIGHT QUEUE
([`planning/night-queue-2026-06-16.md`](../docs/planning/night-queue-2026-06-16.md)).
Slot 1 (hero cost comparison) shipped #1000; the topmost `TODO` is **slot 2 —
power (activated-ability) cost comparison** (§7.5). One PR.

## What I'm about to do

Add the **power** member of the §7.5 multi-entity cost-comparison floor — the
power-store sibling of the shipped paragon (#962) / tower (#946) / difficulty
(#950) / hero (#1000) builders. "Which power is cheaper, Cash Drop or Monkey
Boost?" ranks the **monkey-money** store price of two-or-more powers — the
BUG-0009 "grounded values, wrong assembly" class the value-only faithfulness
guard can't catch. Powers cost **monkey money** (fixed, not difficulty-scaled),
so this primitive has no difficulty axis (the one shape difference from #1000).

- `btd6_data_service.compare_power_costs(names)` — resolve each via the shared
  `find_power` resolver, dedup on id, rank ascending by `monkey_money_cost`, fail
  closed (<2 distinct).
- `btd6_context_service.deterministic_power_cost_comparison_reply` — fires on a
  cost-compare cue + ≥2 resolved powers; defers on a paragon cue / strategy /
  single-power lookups. Registered in `_BTD6_LIST_BUILDERS` after the hero builder.
- Tests: `tests/unit/services/test_btd6_power_cost_comparison.py` + an exclusivity
  corpus should-fire phrase.

Ships under **Q-0048** (read-only deterministic floor, no prod-check, auto-deploys).
