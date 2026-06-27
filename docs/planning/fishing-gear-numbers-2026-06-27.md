# Fishing gear numbers — the sim-pin record (2026-06-27)

> **Status:** `historical` design-numbers record (mirrors
> `gear-set-numbers-2026-06-11.md`). The authoritative copy of these numbers is the
> code (`utils/equipment.py`, `utils/fishing/gear.py`, `utils/mining/market.py`) +
> the guard test (`tests/unit/utils/test_fishing_gear.py`). This doc explains *why*
> the numbers are what they are.

## What shipped

The Q-0175 / V-14 *"matching gear → better fishing"* half (the offline successor to
the gear loadout presets, #1499). A fishing loadout now *biases the cast*, not just
swaps which mining/combat gear is equipped — by reusing the cross-game
`EffectiveStats` seam, no parallel fishing-stat store.

## The two stats

`EffectiveStats` gained two additive, default-0 fields:

| stat | feeds | cast effect |
|---|---|---|
| `fishing_power` | `utils.fishing.gear.fishing_pull_mult` | rarity pull (≥ 1, big-end of the *same* band) |
| `bite_luck` | `utils.fishing.gear.fishing_bite_speed_mult` | bite-speed (≤ 1, faster bites) |

Both default to 0 ⇒ both multipliers are exactly `1.0` ⇒ a cast with no fishing
gear is **byte-identical** to the pre-gear behaviour (the additive safety
property, the same one the skill tree relied on).

## The charm ladder (CHARM slot)

Deliberately in the **CHARM slot**, *off* the combat `SET_SLOTS`, so the duel-balance
sim (`tests/unit/utils/test_gear_set_numbers.py`) is untouched. A fishing loadout
equips one of these *instead of* the lucky charm — an optimisation, never a gate (the
starter still fishes fine).

| item | `fishing_power` | `bite_luck` | shop price | durability |
|---|---|---|---|---|
| fishing charm | 2 | 1 | 90 | 80 |
| anglers charm | 4 | 2 | 220 | 140 |
| master angler charm | 6 | 3 | 420 | 220 |

Coins-only (no recipe) — buyable satisfies `test_every_wearing_gear_is_reacquirable`;
no `recipes.json` change, so the curated-recipe-set lint is untouched. Prices are
monotonic and above the lucky charm.

## The conversion knobs

`utils/fishing/gear.py`:

- `PULL_PER_FISHING_POWER = 0.04` → master angler (`fishing_power=6`) gives **×1.24**
  rarity pull, a touch under a **Silver Rod** (1.25). So a fully-kitted fishing charm
  is roughly *one rod tier* of pull on top of the rod you hold — meaningful, not
  dominant.
- `BITE_SPEED_PER_BITE_LUCK = 0.03` → master angler (`bite_luck=3`) gives **×0.91**
  bite speed (~9% quicker bites). Gentle, like a low rod tier's `bite_speed`.
- Caps (`MAX_GEAR_PULL = 1.40`, `MIN_GEAR_BITE_SPEED = 0.75`) ensure gear can never
  dominate the rod × bait × weather stack even if a future item or stacking path
  pushes the stats far past this ladder.

## Where it folds in

`services.fishing_workflow.begin_cast` reads `character.character_stats(equipped,
skills)` and multiplies the gear knobs into `effective_pull` / `effective_bite_speed`
as the **4th** how-well knob (rod × bait × weather × **gear**). The cast panel shows a
`🎣 fishing gear` footer note when a bonus is active.
