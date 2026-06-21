# 2026-06-21 — Creature PvP battle flow (cog + views + service)

> **Status:** `in-progress` — building the user-facing creature PvP battle flow
> (creature-game v1 next slice). Runtime code, **`needs-hermes-review`** (the
> named ▶ NEXT was explicitly "Not an autonomous self-merge").

> **Run type:** `routine · dispatch`

## What I'm about to do

Build the user-facing creature PvP flow that docks onto the already-shipped pure
battle engine (`disbot/utils/creatures/battle.py`, PR #1213), per the
[creature-game plan](../docs/planning/creature-game-design-and-sim-2026-06-20.md)
§4 and current-state ▶ NEXT:

- `services/creature_battle_service.py` — thin **read** boundary: load each
  player's owned-creature pool from the collection-log, build a **level-normalized**
  team (`NORMALIZED_LEVEL`, the §3 anti-P2W finding), resolve via the engine. v1 is
  read-only (no result persistence yet — "(later) record results").
- `views/creature_battle/` — `challenge.py` (Accept/Decline challenge view) +
  `render.py` (battle-outcome embed). Challenge view extends **BaseView** with
  `author=opponent` so only the challenged player can interact — cleaner than a
  direct `discord.ui.View` and keeps the arch `baseview_inheritance` ratchet green.
- `cogs/creature_battle_cog.py` — `!cbattle @opponent` (mirrors the rps/deathmatch
  PvP-challenge pattern). Flat cog file to match the sibling `creature_cog.py`
  (noted deviation from the plan's `cogs/creature_battle/` package wording —
  one command doesn't justify a package).
- Register in `config.py`; tests for the service + render.
