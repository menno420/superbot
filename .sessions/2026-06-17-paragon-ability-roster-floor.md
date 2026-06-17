# Session — 2026-06-17 · paragon-ability roster deterministic floor (BUG-0009 §7.6)

> **Status:** `in-progress`

## What I'm about to do
Scheduled dispatch, **empty work order** → the buildable `ready` decade-queue is thin
and the night-queue BTD6 floor lane is fully consumed, but `current-state.md` ▶ Next
action explicitly names **paragon-ability lookup** as a still-valid empty-fire
deterministic-floor slice. Building it:

- a new `deterministic_paragon_ability_roster_reply` floor builder in
  `btd6_context_service.py` — the paragon sibling of the shipped
  `deterministic_hero_ability_roster_reply`. Answers "what abilities does the
  Ascended Shadow paragon have" / "list the dart monkey paragon's abilities" off the
  curated `paragon_abilities.json` (served via `btd6_stats_service`), so the floor
  OWNS the labelled activated/passive list (BUG-0009 wrong-assembly class — every
  ability name is grounded, so a mislabel/invention slips past the value-only guard).
- registered in `_BTD6_LIST_BUILDERS`, with a `_SHOULD_FIRE` exclusivity-corpus entry;
  mutually exclusive with the hero-ability roster (requires the literal `paragon`
  token) and the paragon-cost comparison (defers on a cost cue).
- a `tests/unit/services/test_btd6_paragon_ability_roster.py` test file.

Read-only & deterministic → ships under Q-0048 (no prod-check gate). Data-complete
today (`paragon_abilities.json` is committed).
