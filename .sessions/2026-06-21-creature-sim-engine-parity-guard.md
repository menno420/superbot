# 2026-06-21 — Creature sim↔engine constant parity guard (PR 2)

> **Status:** `in-progress` — born-red HOLD (Q-0133). Small stdlib test + a contained refactor of a
> disposable design tool → **ungated self-merge on green** (Q-0113), not `needs-hermes-review`.

> **Run type:** routine · dispatch

## What I'm about to do

Same dispatch run, continuation after PR #1213 (the creature battle engine) **merged** to main.
Building the Q-0089 idea I filed this run —
[`creature-sim-engine-constant-parity-guard`](../docs/ideas/creature-sim-engine-constant-parity-guard-2026-06-21.md):
the combat design constants now live in **both** `tools/game_sim/creature_battle_sim.py` (the
balance simulator) and `disbot/utils/creatures/battle.py` (the runtime engine that graduated them).
That's a two-sources-of-truth drift class — tune one, the other silently diverges, and the sim's
"PLAYABLE" verdict stops describing what players actually play.

**Plan:** (1) lift the sim's archetype-weights dict from a local in `_roster()` to a module
constant `ARCHETYPE_WEIGHTS` (it's the only design constant the sim keeps local — every other one
is already module-level), so it's importable/comparable; (2) add
`tests/unit/tools/test_creature_sim_engine_parity.py` (importlib-loads the sim, the repo convention
for tool scripts) asserting the sim and engine agree on every shared design constant: type-chart
multipliers, element cycle, rarity budgets, archetype weights, move powers, buff step/cap, signature
move names, level-scaling rates, team size.

Disposable, stdlib-only, fully CI-verifiable — no Discord runtime.
