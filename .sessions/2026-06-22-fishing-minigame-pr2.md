# 2026-06-22 — Fishing minigame PR2: the trophy reel-fight (completing the hybrid)

> **Status:** `in-progress` — born-red card. Owner-directed implementation (Q-0175 fishing
> minigame, continuing after #1298). Adding the trophy reel-fight — the second half of the owner's
> "hybrid" mechanic decision.

## Arc (what I'm about to do)

PR1 (#1298) shipped the core `cast → wait → BITE → reel`: ordinary fish land on the first reel.
The owner's **hybrid** decision (2026-06-22) was: *single reel for ordinary fish, a reel-fight for
trophies*. This PR2 adds the **reel-fight**:

- Hooking a **trophy** (top third of your unlocked band — `minigame.is_trophy`) no longer commits
  immediately; it starts a short **reel-fight**: 2–4 more timed reel taps (scaling with fish size),
  each its own generous presence-check window, each able to let the fish **snap free** with a small
  escape chance. Land every tap → the trophy is committed; miss a window or get snapped → it gets
  away (owner: missed reel = no catch).
- Kept fair: fight windows stay the *full* generous window (NOT the sim's tighter `w*0.8` — over
  Discord a tighter window punishes latency, not skill; trophies are harder via more taps + escape).
- Concurrency: each armed window carries a `_round_id` staleness token so a previous round's
  background task (still sleeping out its window) exits on wake instead of false-failing the fish.
- `escape_resist` is already a parameter on the escape helpers (defaults 0) so the PR3 **rod ladder**
  can buy it down without touching this code.

Pure helpers (`reel_fight_taps`, `fight_escape_chance`, `roll_escape`) added to
`utils/fishing/minigame.py` (testable, no Discord). No workflow/DB change — the fight just gates
when `commit_catch` runs. **Deferred to PR3+:** rod ladder, energy pacing + sell-value rebalance,
boat/deepwater.

## Shipped

_(filled in at close)_
