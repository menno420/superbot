# Idea — Fishing-specific gear stats (make loadout presets a real optimisation)

> **Status:** `ideas` · captured 2026-06-27 (dispatch run, alongside the gear-loadout-presets ship #1499).
> **Lane:** S1 bot product · games/mining-fishing. **Size:** small–medium, offline-buildable.

## The gap

The unified-loadout vision (`fishing-open-world-expansion-plan-2026-06-18.md`, Q-0175 / V-14) has two
halves:
1. **Swap mechanism** — *"put on fishing gear"* swaps your equipped items to a saved loadout. **Shipped
   2026-06-27 (#1499)** as named loadout presets.
2. **Matching gear increases the activity's bonus** — *"fishing gear → better fishing"*. **Not built:**
   `utils/equipment.EffectiveStats` only models mining (`mining_power`/`light_radius`/`depth_access`/…)
   and combat (`damage`/`defense`/`max_health`) stats. There is no fishing stat for gear to bias, so a
   "fishing loadout" is currently just convenience — it changes *which* mining/combat gear is equipped,
   not how well you fish.

## The idea

Add a fishing stat to the shared stat model and read it as a 4th how-well knob in the cast:

- **`utils/equipment.py`** — add `fishing_power` (and maybe `bite_luck`) to `EffectiveStats`, plus a
  handful of fishing-flavoured gear items in `_GEAR` (e.g. a fishing rod-charm / tackle vest in the
  existing tier ladder). Additive — zero until those items exist, so every current stat read is
  byte-identical.
- **`utils/fishing/` + `services/fishing_workflow.begin_cast`** — read the player's `EffectiveStats`
  and fold `fishing_power`/`bite_luck` into the existing cast model as a 4th knob beside
  **rod × bait × weather** (faster bites and/or a rarity nudge). Pure, sim-pinnable like the rod knobs.

## Why it's worth having

It turns the just-shipped loadout presets from cosmetic convenience into a **real optimisation** (the
exact framing the owner used: "switching is an *optimization*, not a gate"), and it does so by reusing
the cross-game `EffectiveStats` seam rather than inventing a parallel fishing-stat system. It also lays
the groundwork for the same pattern in other activities (exploration gear, etc.).

## Connections / don't-duplicate

- Build on `utils/equipment.py` (`EffectiveStats`, `_GEAR`, the bronze…diamond tier ladder) and the
  fishing cast seam (`utils/fishing/`, `fishing_workflow.begin_cast`, the rod/bait/weather knobs) —
  do **not** add a parallel fishing-only stat store.
- Keep it offline + sim-pinned (mirror `docs/planning/gear-set-numbers-2026-06-11.md`'s approach).
