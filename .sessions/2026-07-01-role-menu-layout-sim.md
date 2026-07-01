# 2026-07-01 — Role-menu builder button-layout simulation

> **Status:** `in-progress` — born-red card (Q-0133). Run type: manual · owner-directed.

**Branch:** `claude/reaction-roles-counter-bgxnyd` (restarted from `main` @ #1608 — prior PR merged).

## What I'm about to do (intentions)

Owner asked (after the builder preview-fix): "create a simulation to find out the most optimal button
placements and functions." Build a real optimizer (in the `tools/sim/` precedent — `help_menu_grouping_sim`,
`setup_wizard_sim`) that models the builder's buttons + weighted operator journeys + a transparent UX
cost model, and searches (seeded simulated annealing) for the layout — and function set — that minimises
interaction cost. Deliver the tool + its findings; adopting a layout is a separate, owner-gated follow-up
(it changes their tested UI).

## What shipped

_(filled in at close)_

## Context delta

_(filled in at close)_
