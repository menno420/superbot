# Session — BUG-0009 slice 2: deterministic Geraldo per-level item lists

> **Status:** `in-progress`

**Dispatch:** empty/generic work order → took the live ▶ Next action = **BUG-0009
slice 2: per-level item lists (Geraldo per-level groupings)**, the same proven
shape as slice 1 (#924, MK-related family).

## What I'm about to do
- Add a deterministic Geraldo per-level grouping to `btd6_data_service`
  (`geraldo_items_by_unlock_level()`) — the relation the model gets wrong.
- Add `deterministic_geraldo_per_level_reply()` to `btd6_context_service` — fires
  on the "what does Geraldo unlock at each level / per level / level N" shape;
  `None` for single-item lookups / strategy → those still reach the model.
- Unify the BUG-0009 floor in `natural_language_stage` behind one dispatcher
  `deterministic_btd6_list_reply()` (MK first, then Geraldo) so slice 3
  (newest-towers) drops in cleanly.
- Tests + bug-book + current-state ▶ handoff.

CI mirror green (`check_quality --full` + `check_architecture --mode strict`)
before flipping this card to `complete`.
