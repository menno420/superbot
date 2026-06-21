# 2026-06-21 — Creature game PvP: the pure battle engine (foundation slice)

> **Status:** `in-progress` — born-red HOLD (Q-0133). Substantial runtime-game plan step →
> `needs-hermes-review`, **NOT** an autonomous self-merge (Q-0117).

> **Run type:** routine · dispatch

## What I'm about to do

Scheduled dispatch, no work order → advancing the headline ungated buildable lane (current-state ▶
Next action option (a)): **the creature-game PvP battle**. The full PvP feature is engine + cog +
interactive challenge views, explicitly a **runtime-verified** session in the
[plan](../docs/planning/creature-game-design-and-sim-2026-06-20.md) §4. This run ships the
**foundation half I can verify without Discord runtime**: the **pure, level-normalized battle
engine** graduated from the validated Monte-Carlo sim (`tools/game_sim/creature_battle_sim.py`)
into `disbot/utils/creatures/battle.py`, with a unit-test suite that **re-validates the sim's
fairness gates inside the bot** (type balance ~50%, normalized PvP ~50%, skill impact, status-move
value). The interactive cog + challenge views (which genuinely need live Discord verification) are
the next slice on top of this engine.

**Deviation from plan §4 wording (noted):** the plan names `services/creature_battle_engine.py`;
the engine is pure combat math (no DB, no audit, no IO) so it belongs in `utils/creatures/` next to
its pure-domain siblings `creature.py`/`encounters.py`, not in the `services/` audited-write layer.
The `services/` seam enters only when battles **persist results / award xp / emit audit** (the
later cog-wiring slice) — and even then the math stays pure in utils with a thin service over it.
