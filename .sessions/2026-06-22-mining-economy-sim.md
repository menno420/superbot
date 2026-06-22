# 2026-06-22 — Mining economy / balance simulation

> **Status:** `in-progress` — building a Monte-Carlo balance sim for the mining game.
> Born-red card (Q-0133); flipped to `complete` as the deliberate final step.

## Arc (what I'm about to do)

Owner-directed in-chat: the mining grid's first real grid Mine is now live (#1281/#1282), and
the owner feels **rewards may be too large and too frequent**. He recalled that a prior session
introduced the idea of *running a simulation to find a balanced configuration*. Task: create and
run a balance simulation for the mining game so it stays **fun and playable for everyone**, and
surface a recommended, balanced configuration of the tunables (reward size / frequency / grid
descent), following the existing `tools/game_sim/` design-sim precedent
(`creature_battle_sim.py` — stdlib, deterministic, PASS/WARN verdict, config-as-data).

Depth (currently capped at 3) is explicitly *not* the priority — the faucet (reward magnitude +
frequency) is.

## Plan

- Map the real mining reward + grid mechanics (rewards, drop rates, depth, costs, XP).
- Build `tools/game_sim/mining_economy_sim.py` — Monte-Carlo a player's session(s): coins/XP
  per dig, per session, over time; sweep candidate configs against fun/balance targets.
- Run it, find the most balanced config, write the numbers into a `docs/planning/` record.
- Light smoke/invariant test mirroring `test_creature_battle_sim.py`.
