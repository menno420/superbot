# Session — 2026-06-15 · mining Slices E + F — respec polish + skill/milestone titles

> **Status:** `in-progress`

## What I'm about to do

Dispatch routine. Work order pointed at the mining lane (▶ Next action = mining respec-polish /
skill-titles / home — Slices E/F/C). **Home (C) shipped #910**; the remaining ▶ startable slices are
**E (respec polish)** and **F (titles)** of
[`mining-structures-skill-tree-plan-2026-06-14.md`](../docs/planning/mining-structures-skill-tree-plan-2026-06-14.md),
both unblocked by the #891 skill tree.

One open PR (#911, owner's live mining-hub UX restructure) touches `main_panel.py` + `gear_panel.py`,
so I deliberately surface both slices **away from those files** — Slice E lives in
`skills_panel.py`/`skill_service.py`; Slice F's title display goes on the `character_panel.py`
aggregator (its docstring already anticipates titles) and a `🏆 Titles` button on the skills panel,
not the main hub.

**Slice E — respec polish:** add a confirm step (cost + point preview, "are you sure") before the
coin charge, and a **partial respec of one branch** (`skill_service.respec_branch`) for a reduced
cost. Today the Respec button charges instantly with no confirm.

**Slice F — titles from skill mastery + milestones:** a pure trigger table
(`utils/mining/titles.py`) → an `equipped_title` store on `mining_player_state` (migration 074) →
`services/title_service.py` (earn-check + equip/unequip) → a `🏆 Titles` panel + `!titles` + the
equipped title surfaced on the Character embed. Earned set is **derived** from existing progression
(skill allocation at cap, max depth, game level) — only the equipped *choice* is persisted, so it's
fully additive (no title equipped → byte-identical).

Verify each slice: `check_quality --full` green + `check_architecture --mode strict` 0.

## What shipped

_(filled in as each slice lands)_

## Handoff / next

_(filled at close)_
