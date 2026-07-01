# Fishing Dock — pinned numbers (2026-07-01)

> **Status:** `living-ledger` — the tunable constants behind the **Dock**, the Tide Pool's
> bite-speed sibling. Change a number here **and** in
> `tests/unit/utils/test_mining_structures.py` (the build ladder + bite-speed multiplier are
> pinned there) in the same commit, like the tide-pool / coral / pearl number docs before it.

## What this is

The Dock is the **second** coral structure (sibling to the Tide Pool,
`docs/planning/fishing-tide-pool-numbers-2026-07-01.md`). It exists to make a coral investment a
real **choice** rather than a single upgrade path:

| Structure | Payoff | Cost shape | Role |
|---|---|---|---|
| **Tide Pool** | rarity-pull (rarer fish) | coral + coins | premium |
| **Dock** | bite-speed (faster bites) | coral + **wood** | entry (cheaper) |

Coral now has three meaningfully-different sinks — cosmetic **curios**, the rarity **Tide Pool**,
and the speed **Dock** — so a lucky deep-sea fisher decides *what* their coral buys.

It reuses the generic `mining_structures` table (no migration), the audited
`services.mining_workflow.build_structure` seam, and the **additive-safety property**: unbuilt
(level 0) ⇒ the bite-speed multiplier is exactly `1.0` ⇒ every existing cast is byte-identical.

## Build ladder (`utils/mining/structures.py` — `_DOCK_BUILD_LADDER`)

| Level | Name | Coral | Wood | Coins | Bite-speed |
|---|---|---|---|---|---|
| 1 | Fishing Dock | 2 | 15 | 1,200 | ×0.94 (6% faster) |
| 2 | Deepwater Pier | 5 | 30 | 3,500 | ×0.88 (12% faster) |

- **`dock_bite_speed_mult(level) = 1.0 − 0.06·level`** (`_DOCK_BITE_STEP = 0.06`), clamped to the
  ladder. Level 0 ⇒ exactly `1.0`. The multiplier is folded into `begin_cast`'s
  `effective_bite_speed`, where **lower = a shorter bite wait** (the same convention rod/bait use).
- **Coral cost** (2 + 5 = **7** for the full build) is deliberately *cheaper* than the Tide Pool
  (19 coral) — the Dock is the entry structure — but it also spends **wood** (a common mined
  material, like the Campfire) so it isn't purely coral-gated.
- **Coins** (1.2k / 3.5k) sit just below the Tide Pool's ladder — the cheaper of the two coral
  structures, so an early fisher can afford *faster* fishing before *rarer* fishing.

## Why bite-speed (a distinct axis from the Tide Pool)

Bite-speed shortens the wait between casts — it makes fishing *faster*, compounding everything
(more catches, more coral, more XP per session) without changing *what* you catch. That is a
genuinely different lever from the Tide Pool's rarity-pull (which changes *what* you catch without
changing the rate), so the two structures don't overlap: one is throughput, the other is quality.
Both bounded and small (max 12%), both plain multipliers composing with the four base knobs.

## Invariants the tests pin

- `dock_bite_speed_mult(0) == 1.0` (byte-identical when unbuilt) and it falls `0.94 / 0.88` across
  the two levels, clamped below `MAX_DOCK_LEVEL` and never negative.
- `build_cost(DOCK, level)` returns the ladder rows above and `None` past the top.
- `begin_cast` folds the dock multiplier into `effective_bite_speed` (a built dock lowers it vs. an
  unbuilt one; an unbuilt dock leaves the pre-existing value unchanged) and sets `dock_bonus`.
- Building routes through the audited `mining_workflow.build_structure` seam (coin debit + coral +
  wood consume + level raise in one transaction) — no new mutation path.
