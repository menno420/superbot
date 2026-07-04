# Fishing Boathouse — pinned numbers (2026-07-01)

> **Status:** `living-ledger` — the tunable constants behind the **Boathouse**, the third fishing
> structure (energy-regen payoff). Change a number here **and** in
> `tests/unit/utils/test_mining_structures.py` (the build ladder + regen multiplier are pinned there)
> in the same commit, like the tide-pool / dock / coral / pearl number docs before it.

## What this is

The Boathouse is the **third** coral structure (after the Tide Pool,
`docs/planning/fishing-tide-pool-numbers-2026-07-01.md`, and the Dock,
`docs/planning/fishing-dock-numbers-2026-07-01.md`). It gives coral a distinct **third** payoff so a
lucky deep-sea fisher genuinely chooses what their coral buys:

| Structure | Payoff | Cost shape | Axis |
|---|---|---|---|
| **Tide Pool** | rarity-pull (rarer fish) | coral + coins | *quality* |
| **Dock** | bite-speed (faster bites) | coral + wood | *throughput per cast* |
| **Boathouse** | energy regen (shorter "line rest" wait) | coral + **wood** | *endurance / less waiting* |

Coral now has **four** meaningfully-different sinks — cosmetic **curios**, the rarity **Tide Pool**,
the speed **Dock**, and the endurance **Boathouse**.

It reuses the generic `mining_structures` table (no migration), the audited
`services.mining_workflow.build_structure` seam, and the **additive-safety property**: unbuilt
(level 0) ⇒ the regen multiplier is exactly `1.0` ⇒ the effective regen interval is exactly
`REGEN_SECONDS` ⇒ every existing player's energy behaviour is byte-identical.

## Build ladder (`utils/mining/structures.py` — `_BOATHOUSE_BUILD_LADDER`)

| Level | Name | Coral | Wood | Coins | Regen mult | Effective interval | Faster |
|---|---|---|---|---|---|---|---|
| 1 | Boathouse | 3 | 20 | 2,000 | ×0.88 | 26s (from 30s) | 12% |
| 2 | Grand Boathouse | 6 | 40 | 5,000 | ×0.76 | 23s (from 30s) | 24% |

- **`boathouse_regen_mult(level) = 1.0 − 0.12·level`** (`_BOATHOUSE_REGEN_STEP = 0.12`), clamped to the
  ladder. Level 0 ⇒ exactly `1.0`. `utils.fishing.energy.regen_seconds_for(mult)` turns it into the
  effective regen interval `max(1, round(REGEN_SECONDS · mult))` (30 → 26 → 23), passed to
  `settle` / `spend` / `seconds_until` in `begin_cast` and `get_energy`, where **lower seconds =
  faster refill**.
- **Coral cost** (3 + 6 = **9** for the full build) sits *between* the Dock (7) and the Tide Pool (19),
  and it also spends **wood** (a common mined material, like the Dock) so it isn't purely coral-gated.
- **Coins** (2k / 5k) likewise sit between the Dock (1.2k / 3.5k) and the Tide Pool (1.5k / 4k / 9k).

## Why energy regen (a distinct axis from Tide Pool and Dock)

Regen speed only matters when you are **energy-throttled** — it shortens the "🎣 you're out of energy —
ready to cast again in N" wait, letting you fish more per real-time hour. The Dock's bite-speed helps
*every* cast's bite wait; it does nothing for the energy throttle. The Tide Pool changes *what* you
catch, not *how much* you can fish. So the three levers don't overlap: quality (Tide Pool),
per-cast throughput (Dock), and session endurance (Boathouse). The bonus is bounded and modest
(max 24% faster refill) — pacing help, never removing the finite-energy brake the owner chose.

## Invariants the tests pin

- `boathouse_regen_mult(0) == 1.0` (byte-identical when unbuilt) and it falls `0.88 / 0.76` across the
  two levels, clamped below `MAX_BOATHOUSE_LEVEL` and never non-positive.
- `energy.regen_seconds_for(1.0) == REGEN_SECONDS` (byte-identical) and returns `26 / 23` for the two
  built levels; never below 1.
- `build_cost(BOATHOUSE, level)` returns the ladder rows above and `None` past the top.
- `begin_cast` / `get_energy` settle energy at the faster interval when a Boathouse is built (a built
  Boathouse regens strictly faster than an unbuilt one; an unbuilt Boathouse is byte-identical).
- Building routes through the audited `mining_workflow.build_structure` seam (coin debit + coral + wood
  consume + level raise in one transaction) — no new mutation path.
- The Boathouse is a fishing bonus, never a gear-craft forge gate (`forge_level_required("boathouse")
  == 0`).
