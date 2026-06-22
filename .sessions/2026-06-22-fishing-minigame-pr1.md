# 2026-06-22 — Fishing minigame PR1: the interactive cast → wait → BITE → reel loop

> **Status:** `in-progress` — born-red card. Owner-directed implementation (Q-0175 fishing
> minigame). Building the first runtime slice off the sim-backed design
> (`docs/planning/fishing-minigame-design-2026-06-22.md`, PR #1296).

## Arc (what I'm about to do)

The owner greenlit building the fishing minigame. This is **PR1 of a 2–3 PR plan** — the core
interactive loop, kept focused (runtime `disbot/` code → small PRs):

1. **Split the reward seam** — `fishing_workflow` currently rolls *and* writes in one call. Split
   into `roll_cast()` (read-only roll, so we know what's on the line at bite time) + `commit_catch()`
   (the audited atomic write), with `fish()` composing them (keeps existing `!fish`/tests green).
2. **Pure minigame domain** — `utils/fishing/minigame.py`: the sim-recommended tuning (randomised
   3–6 s bite + 1.5 s floor, ~2.5 s reaction window, trophy threshold) + pure resolve helpers, unit-
   testable, no Discord.
3. **The interactive view** — `views/fishing/cast_view.py` (`discord.ui.View`, mirrors
   `views/blackjack/solo_view.py`): cast → a managed background task arms the BITE after the delay →
   the **Reel** button resolves it. Miss (too slow) or premature reel = **the fish gets away** (owner
   decision: missed reel = no catch). On success, `commit_catch` writes it. Fake-out shake before the
   real bite. Active-cast guard (no double-casting) for soft pacing.
4. **Wire `!fish`** to launch the view; keep `fishlog`/`fishtop`.
5. **Tests** — pure minigame domain + the workflow split.

**Deferred to PR2/PR3** (kept out to stay focused): the trophy **reel-fight** (hybrid), the **rod
ladder** (new persistence + tackle UI), **energy** integration + **sell-value** rebalance, and the
**boat/deepwater** venue. Owner decisions already recorded: hybrid mechanic, fish-gets-away, soft
energy/cooldown, bait-later, shore-first.

## Shipped

_(filled in at close)_
