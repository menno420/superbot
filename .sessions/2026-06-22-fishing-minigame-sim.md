# 2026-06-22 — Fishing minigame: design simulation + analysis

> **Status:** `in-progress` — born-red card. Owner-directed research/design session
> (no runtime `disbot/` code yet). Building a simulation to find the most fun + fair
> fishing-minigame mechanic before committing to an implementation direction.

## Arc (what I'm about to do)

Owner wants the fishing subsystem (today: prefix-only deterministic roll) to become an
**interactive minigame** — leaning toward a real "cast line → wait… → bite! → reel in" loop,
but he's **not sure that's the best option** and is "still finalizing the idea." He explicitly
asked me to **create and run a simulation** to find: the most fun way to play, the right
bite-timing, how long the reaction window should be, the best rod-upgrade system, and how the
**boat / deepwater fish** (Phase 2 of the plan) should differ from shoreline fishing. He
welcomes other ideas.

This session (research + tooling, fully reversible, no runtime code):
1. **Build `tools/sim/fishing_minigame_sim.py`** — a stdlib-only Monte-Carlo sim that models the
   *full Discord latency chain* (message-edit push → human reaction → button round-trip) so the
   reaction-window numbers are realistic, not twitch-game fantasy. Scores candidate mechanics on
   fun/fairness/reward proxies across a player population (varied reaction time + network latency).
2. **Run it**, sweep parameters (bite-time distribution, reaction-window length, rod tiers,
   shoreline vs deepwater), and capture the output.
3. **Write `docs/planning/fishing-minigame-design-2026-06-22.md`** — findings, recommended numbers,
   the rod-upgrade ladder, the boat/deepwater design, and alternative mechanic ideas. Route the
   genuinely owner-level direction choices to him.

Grounded in: `docs/planning/fishing-open-world-expansion-plan-2026-06-18.md` (Q-0175 vision),
current `fishing_workflow` / `utils/fishing/` (21 fish, 7 levels, fish now sellable+cookable per
#1289).

## Shipped

_(filled in at close)_
