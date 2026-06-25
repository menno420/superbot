# 2026-06-25 — BTD6 eval anchors: #855 MOAB-class bonuses (S2 P1-1, follow-up to #1460)

> **Status:** `in-progress`

## Goal (dispatch run, slice 2 — follow-up PR)

Second slice of this dispatch run. #1460 (slice 1, merged) anchored the BTD6 projected-total
eval figures and corrected the starting-cash convention. While inventorying the remaining BTD6
knowledge/grounding eval cases for *other* cleanly-derivable-but-unanchored truths, found one:
`grounding.btd6_bomb_middle_path_moab_855` asserts the Bomb Shooter middle-path MOAB-class
bonuses (**+15 / +30 / +99** — MOAB Mauler / Assassin / Eliminator, the #855 Layer A data) in
its `llm_judge` rubric, with no anchor pinning them to the dataset. A re-seed that changed a
bonus would leave the case silently testing a stale truth.

## What I'm about to do

Add a `_moab_class_bonus(tower_id, code)` derive helper that reads the public
`btd6_stats_service.normal_stats(tower.tier(code)).specials` tuple (e.g. `('+15 vs MOAB-Class',)`
— the same structured source the grounding renders from) and extracts the integer bonus, plus
**three** `Anchor`s for the case (15.0 / 30.0 / 99.0). This closes the last uncovered
cleanly-derivable BTD6 grounding truth — the BTD6 knowledge/grounding eval cases are then
anchor-complete (only documented distractors + user-supplied inputs stay unanchored).

Offline test-only (no `disbot/` runtime). Self-mergeable.
