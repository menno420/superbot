# 2026-06-28 — Feature-completion unit assessments (Q-0209 framework)

> **Status:** `in-progress`

**Run type:** routine · dispatch

## What I'm about to do

Empty-fire dispatch (no work order). The completion-first certification framework just shipped
(#1513, owner decision Q-0209) with **only Blackjack assessed (1/36 units)**. The natural deepening
slice of that just-started arc: **assess more S1 game units** against the game rubric
(`▢ → ◐`), turning the framework from a one-unit pilot into a real ledger with concrete punch-lists.

**Self-initiated (Q-0172):** advancing the completion-first arc the owner greenlit live (Q-0209) — a
*deepening* of an already-started unit/system (the framework), not a brand-new feature, so it sits
squarely inside the completion-first soft default.

Scope (additive, docs + possibly offline tests):
- Assess **Fishing**, **Mining**, **Word Chain** game units → one certificate each under
  `docs/planning/feature-completion/units/`, filled from `rubric-game.md`, each with a real
  punch-list; flip ledger State to `assessed`; regenerate the scoreboard.
- If budget allows, clear a contained, offline punch-list item (Blackjack edge tests, punch-list #3)
  to demonstrate the assess→close loop and advance the pilot toward certification.

No runtime behaviour change from the assessments (docs only); any test additions are offline.
