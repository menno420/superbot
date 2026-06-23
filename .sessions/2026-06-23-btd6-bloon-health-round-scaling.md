# 2026-06-23 — BTD6 late-game/freeplay bloon health scaling (round-scaled HP)

> **Status:** `in-progress`

Owner-directed (Discord screenshot). The bot answered "how much health does a BAD
have on r100?" with a flat **20,000** and asserted "round 100 doesn't change the
BAD's base health." A community member (kthxbye) corrected it: **28k — 20k base ×
1.4 by r100.** This session adds the missing round-relative health scaling.

## What I'm about to do
- Research-verified (web, this session): BTD6 applies a **runtime** late-game /
  freeplay health ramp to **MOAB-class** bloons — +2% of base HP per round from
  round 81, piecewise-linear (`v(100)=1.40`), so a BAD first spawns on round 100
  already at **28,000 HP** (20,000 × 1.4), 67,200 RBE. **Not in the dump** (round
  files = composition/timing only; `BloonModel` stores base `maxHealth` only) —
  same shape as per-round XP/cash, which we already curate.
- Encode the curve as a curated `disbot/data/btd6/bloon_scaling.json` (mirrors the
  `round_xp.json` source-noted pattern), add `moab_class_health_multiplier()` /
  `bloon_health_at_round()` to `btd6_data_service`, surface it in
  `btd6_context_service` (a deterministic "bloon HP at round N" floor reply +
  MOAB-class grounding note), and pin the verified anchors (r100 = 1.4, BAD =
  28,000) in tests.

Sources: bloons.fandom.com *Late Game and Freeplay (BTD6)* + *Big Airship of Doom*
(28,000 / 67,200 RBE @ r100) + topper64.co.uk *BTD6 Rounds* ("+2% health/round
after round 80"). r≤100 bracket cross-verified; >100 brackets are the wiki's
documented continuation.
