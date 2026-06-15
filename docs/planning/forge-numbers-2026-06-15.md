# Forge structure — pinned numbers (mining Slice B)

> **Status:** `reference` — the tunable defaults for the §7.5 Forge (Slice B of
> [`mining-structures-skill-tree-plan-2026-06-14.md`](mining-structures-skill-tree-plan-2026-06-14.md)).
> Source of truth is `disbot/utils/mining/structures.py`; this doc is the
> rationale + the change log, mirrored by `tests/unit/utils/test_mining_structures.py`.
> Change a number → change it in `structures.py`, this doc, and the test in one commit.

## The gate (additive by design)

The Forge gates **only the top two gear tiers**, so the overwhelming majority of
play is untouched until a player reaches gold/diamond gear:

| Gear tier (index) | Forge level required | Free without a forge? |
|---|---|---|
| bronze (1) · iron (2) · silver (3) | 0 | ✅ yes |
| gold (4) | 1 (Forge I) | needs forge |
| diamond (5) | 2 (Forge II) | needs forge |
| tools · structures · starters | 0 | ✅ yes |

`forge_level_required(recipe) = max(0, equipment.tier_index(gear_tier) − FREE_TIER_CEILING)`
with `FREE_TIER_CEILING = 3`. Non-gear recipes (tools/structures/starters,
`gear_tier is None`) require 0 — so an **empty `mining_structures` table is
byte-identical to today's crafting** (the additive safety property).

## Build ladder (coin + material sink)

| Build | Cost | Unlocks |
|---|---|---|
| → Forge I | 3 000 🪙 + 25 iron + 15 stone | gold-tier gear |
| → Forge II | 8 000 🪙 + 20 gold + 10 iron | diamond-tier gear |

`MAX_FORGE_LEVEL = 2` (Forge II unlocks the top of the gear ladder, so no higher
level is needed). The forge is cheap relative to the gear it unlocks and buildable
immediately, so the gate is a progression beat, not a wall.

## Rationale

- **Why distinct tiers, not a flat unlock:** a two-step ladder gives the structure
  sink two meaningful purchases (gold, then diamond) instead of one.
- **Why only the top two tiers gate:** keeps Slice B additive — existing players
  who craft up through silver are unaffected; only the end-game gear becomes a
  built-progression reward. (The work order's "gates higher-tier gear crafting"
  read literally as the *higher* tiers.)
- **Why a generic `mining_structures` table:** Slice C (Home backdrop) reuses the
  same table + `mining_workflow.build_structure`; only its own ladder differs.
