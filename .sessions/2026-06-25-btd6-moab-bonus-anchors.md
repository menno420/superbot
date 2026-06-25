# 2026-06-25 — BTD6 eval anchors: #855 MOAB-class bonuses (S2 P1-1, follow-up to #1460)

> **Status:** `complete` — ready to merge (Q-0133). Run type: routine · dispatch.

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

## What shipped (PR #1461)

- `tests/evals/test_btd6_grounding_anchors.py`: `_moab_class_bonus(tower_id, code)` helper +
  3 `Anchor`s for `grounding.btd6_bomb_middle_path_moab_855` (15.0 / 30.0 / 99.0), both drift
  directions.
- `docs/current-state/S2-btd6.md`: de-staled — the BTD6 knowledge/grounding cases are now
  anchor-complete for every cleanly-derivable truth.

## Verification

- `tests/evals/test_btd6_grounding_anchors.py`: **48 passed** (42 after #1460; +6 = 3 anchors
  × 2 directions).
- `python3.10 scripts/check_quality.py --full`: green (12525 passed in the combined
  slice-1+slice-2 run before #1460 merged; this branch's content is identical — slice 1 from
  main + slice 2).
- `python3.10 scripts/check_architecture.py --mode strict`: **0 errors** (test-only).

## Session enders

This is the **second** PR of one dispatch run; the standing session enders (💡 Q-0089 new
idea — the distractor *negative-anchor* guard · ⟲ Q-0102 previous-session review · Q-0104 doc
audit · the full run report) are filed in the slice-1 card
[`2026-06-25-btd6-projected-total-anchors.md`](2026-06-25-btd6-projected-total-anchors.md) (#1460)
to avoid forced duplication.

## 📤 Run report

- **Did:** S2 P1-1 slice 2 — anchored the #855 Bomb-Shooter MOAB-class bonuses (+15/+30/+99) in
  the grounding eval, closing the last uncovered cleanly-derivable BTD6 grounding truth ·
  **Outcome:** shipped
- **Shipped:** #1461 — `_moab_class_bonus` helper + 3 anchors + S2 de-stale; offline test-only
- **Run type:** `routine · dispatch` (Q-0165)
- **⚑ Owner decisions needed:** `none`
- **⚑ Owner manual steps:** `none`
- **⚑ Self-initiated:** `none` (advanced the S2 P1-1 anchor-coverage plan slice; no
  self-invented feature)
- **↪ Next:** S2 P1-1 anchor-tooling follow-ons — #1458's **eval-anchor coverage report** (now
  the cleanest next slice; the manual inventory it would automate is complete as of this run) ·
  the **distractor negative-anchor guard**; live `llm_judge` battery + absence-guard Layer B
  stay creds-/review-gated.
