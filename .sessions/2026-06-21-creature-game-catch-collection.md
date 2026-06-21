# 2026-06-21 — Creature game runtime v1: catch + collection (dex)

> **Status:** `in-progress` — born-red HOLD (Q-0133). Building the first runtime slice of the
> creature catch/battle game.

> **Run type:** routine · dispatch

## What I'm about to do

Scheduled dispatch, no work order → advancing the headline ungated buildable lane from
current-state ▶ Next action: **the creature-game v1 runtime cog (catch + collection/dex first;
PvP is a separate `needs-hermes-review` session)**. The design + Monte-Carlo sim + 36-creature
catalog all shipped this band (#1183/#1185/#1193/#1194, verdict PLAYABLE); the next step per the
[plan](../docs/planning/creature-game-design-and-sim-2026-06-20.md) §4 is the actual `disbot/`
build of the **catch** half — wild-encounter catch + a collection "dex" + a leaderboard, reusing
the **fishing-style catch log + `game_xp`** (the plan's explicit directive), graduating the sim's
`creatures.json` to `disbot/data/` (Q-0186). PvP battle (`services/creature_battle_engine.py` +
`cogs/creature_battle/`) is deliberately deferred to a runtime-verified `needs-hermes-review`
session per current-state.

Mirrors the fishing subsystem exactly (pure domain → audited workflow → CRUD → hub-less cog):

- `disbot/data/creatures/creatures.json` — the 36-creature launch catalog (graduated from the sim).
- `disbot/utils/creatures/` — pure domain: catalog + rarity-weighted wild encounter + catch roll.
- `disbot/services/creature_workflow.py` — the audited write boundary (catch-log + xp in one txn).
- `disbot/utils/db/games/creatures.py` + migration `077_creature_collection_log.sql` — the dex CRUD.
- `disbot/cogs/creature_cog.py` — `!catch` · `!dex` · `!dextop`, plus the Help hook (hub-less v1).
- `services/game_xp_service` — new `GAME_CREATURE` track + `catch` award; `config.py`,
  `utils/db/__init__`, `utils/subsystem_registry` wiring.
