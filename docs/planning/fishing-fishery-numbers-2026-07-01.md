# Fishing Fishery — pinned numbers (2026-07-01)

> **Status:** `living-ledger` — the tunable constants behind the **Fishery**, the fourth fishing
> structure (yield/abundance payoff). Change a number here **and** in
> `tests/unit/utils/test_mining_structures.py` (the build ladder + double-catch bonus are pinned
> there) in the same commit, like the tide-pool / dock / boathouse / coral / pearl number docs before it.

## What this is

The Fishery is the **fourth** coral structure (after the Tide Pool, the Dock, and the Boathouse). It
gives coral a genuinely distinct **fourth** payoff so a lucky deep-sea fisher chooses what their
coral buys across four axes:

| Structure | Payoff | Cost shape | Axis |
|---|---|---|---|
| **Tide Pool** | rarity-pull (rarer fish) | coral + coins | *quality* |
| **Dock** | bite-speed (faster bites) | coral + wood | *throughput per cast* |
| **Boathouse** | energy regen (shorter "line rest" wait) | coral + wood | *endurance / less waiting* |
| **Fishery** | double-catch chance (a second copy of the fish) | coral + **wood** | *yield / abundance* |

Coral now has **five** meaningfully-different sinks — cosmetic **curios**, the rarity **Tide Pool**,
the speed **Dock**, the endurance **Boathouse**, and the yield **Fishery**.

It reuses the generic `mining_structures` table (no migration), the audited
`services.mining_workflow.build_structure` seam, and the **additive-safety property**: unbuilt
(level 0) ⇒ the double-catch bonus is exactly `+0.0` ⇒ the chance is exactly
`utils.fishing.rewards.BONUS_CATCH_CHANCE` (`0.10`) ⇒ every existing player's catch economics is
byte-identical.

## Build ladder (`utils/mining/structures.py` — `_FISHERY_BUILD_LADDER`)

| Level | Name | Coral | Wood | Coins | Bonus | Double-catch chance |
|---|---|---|---|---|---|---|
| 1 | Fishery | 4 | 25 | 2,500 | +0.05 | 0.15 (from 0.10) |
| 2 | Grand Fishery | 8 | 45 | 6,000 | +0.10 | 0.20 (from 0.10) |

- **`fishery_bonus_chance(level) = 0.05·level`** (`_FISHERY_BONUS_STEP = 0.05`), clamped to the ladder.
  Level 0 ⇒ exactly `+0.0`. `services.fishing_workflow.begin_cast` adds it to
  `rewards.BONUS_CATCH_CHANCE` and threads the result onto `Cast.double_catch_chance`;
  `commit_catch` rolls it via `utils.fishing.rewards.roll_bonus_catch(rng, chance=...)`, which clamps
  the effective chance to `[0, 1]`.
- **Coral cost** is the dearest of the three coral+wood structures (Dock 7 < Boathouse 9 < **Fishery
  12**); the coral-only Tide Pool (19) is dearer on coral alone but carries no wood leg. A yield bonus
  compounds over *every* future catch, so it earns the higher price.

## Why yield is a genuinely fresh lever

The three prior coral structures each improve a *single cast*: the Tide Pool reweights **which** fish
you get, the Dock makes the bite **arrive sooner**, the Boathouse lets you cast **more often**. The
Fishery is the first structure that changes **how much a landed catch yields** — a well-stocked
fishery keeps the waters plentiful, so a successful reel is likelier to hook a *second* copy of the
same fish (straight into the bait/charm/rod/curio craft loops, or the market). Distinct axis, same
additive-safety and audited-seam guarantees as its siblings.

## Where the code lives

- Pure math + registry entry: `disbot/utils/mining/structures.py` (`FISHERY`, `_FISHERY_BUILD_LADDER`,
  `fishery_bonus_chance`).
- The roll knob: `disbot/utils/fishing/rewards.py` (`roll_bonus_catch(rng, *, chance=None)`).
- The cast wiring: `disbot/services/fishing_workflow.py` (`begin_cast` computes + threads
  `Cast.double_catch_chance`; `commit_catch` rolls it).
- The build seam (audited): `disbot/services/mining_workflow.py` (`build_structure`, generic
  `market.structure_build_reason`).
- UI: `disbot/views/fishing/fishery.py` (`🐟 Fishery` panel) + the 🏗 Structures sub-hub button +
  the `!fishery` command.
