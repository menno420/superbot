# Fishing Tide Pool — pinned numbers (2026-07-01)

> **Status:** `living-ledger` — the tunable constants behind the **Tide Pool**, coral's
> first *functional* sink. Change a number here **and** in
> `tests/unit/utils/test_mining_structures.py` (the build ladder + pull multiplier are
> pinned there) in the same commit, like the coral / pearl / gear number docs before it.

## What this is

The fishing rare-material arc's **structure-target** successor (S1 "▶ next offline
successor"): coral now has two sinks to choose between —

- **curios** (`utils.fishing.curios`) — the *cosmetic* sink (a completionist shelf), and
- the **Tide Pool** (`utils.mining.structures.TIDE_POOL`) — the *functional* sink: a built
  structure whose rarity-pull bonus is folded into
  `services.fishing_workflow.begin_cast` as the cast's **5th "how-well" knob**
  (rod × bait × weather × gear × **tide pool**).

It reuses the generic `mining_structures` table (no migration), the audited
`services.mining_workflow.build_structure` seam, and the same additive-safety property the
fishing gear knob relies on: **unbuilt (level 0) ⇒ ×1.0 ⇒ every existing cast is
byte-identical.**

## Build ladder (`utils/mining/structures.py` — `_TIDE_POOL_BUILD_LADDER`)

| Level | Name | Coral | Coins | Rarity-pull bonus |
|---|---|---|---|---|
| 1 | Reef Pool | 3 | 1,500 | ×1.04 (+4%) |
| 2 | Tidal Basin | 6 | 4,000 | ×1.08 (+8%) |
| 3 | Grand Reef | 10 | 9,000 | ×1.12 (+12%) |

- **`tide_pool_pull_mult(level) = 1.0 + 0.04 · level`** (`_TIDE_POOL_PULL_STEP = 0.04`),
  clamped to the ladder. Level 0 ⇒ exactly `1.0`.
- **Coral cost** (3 + 6 + 10 = **19** for the full build) is comparable to carving the
  whole curio shelf (~14 coral), so the two sinks are a genuine choice rather than one
  dominating — a dedicated deep-sea fisher can eventually do both.
- **Coins** (1.5k / 4k / 9k) sit between the Campfire (500) and Forge (3k / 8k) ladders —
  a mid-weight coin sink, never a wall (fishing works fully without it).

## Why rarity-pull (not bite-speed / new fish)

The Tide Pool reweights the player's **already-unlocked** band toward the bigger, rarer
fish — it never unlocks new species (that stays the fishing-**level** axis) and never
changes the bite wait. So the bonus is meaningful (better trophies / dex fills) but small
and bounded (max +12%), and it composes cleanly with the four existing knobs as a plain
multiplier.

## Invariants the tests pin

- `tide_pool_pull_mult(0) == 1.0` (byte-identical cast when unbuilt) and it rises
  `1.04 / 1.08 / 1.12` across the three levels, clamped above `MAX_TIDE_POOL_LEVEL`.
- `build_cost(TIDE_POOL, level)` returns the ladder rows above and `None` past the top.
- `begin_cast` folds the tide-pool multiplier into `effective_pull` (a built pool raises
  the pull vs. an unbuilt one; an unbuilt pool leaves the pre-existing value unchanged).
- Building routes through the audited `mining_workflow.build_structure` seam (coin debit +
  coral consume + level raise in one transaction) — no new mutation path.
