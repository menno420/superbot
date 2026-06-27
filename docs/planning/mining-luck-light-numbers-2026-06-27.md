# Mining `luck` + `light_radius` wiring — pinned numbers (BUG-0026)

> **Status:** `reference` — the sim-pinned tuning for the two formerly-dead
> `EffectiveStats` wired in BUG-0026 (owner decision **Q-0208**, 2026-06-27).
> Source code wins; figures here are re-derivable from the cited code.

The owner chose to **wire** `light_radius` and `luck` (not remove them). Both are
**additive-safe** — byte-identical to prior behaviour when the stat is 0 — so they
change nothing for a player without the relevant gear and only ever *improve* play
for one who equips it.

## `light_radius` → fog-of-war reveal window

`utils/mining/grid.reveal_radius(light_radius)`:
`radius = min(2 + max(0, light_radius - 1), 4)`.

| light source (summed `light_radius`) | reveal radius | window |
|---|---|---|
| none / single torch (0–1) | **2** (unchanged) | 5×5 |
| lantern (2) | 3 | 7×7 |
| diamond lantern (3) | 4 | 9×9 |
| any future brighter light (4+) | 4 (capped) | 9×9 |

Non-regressive by design: a torch player sees exactly the pre-wiring window; only a
*better* light widens it. The same radius feeds the discovered-cell DB query and the
render in `views/mining/grid_mine_view.build_grid_embed`, so they never drift.

## `luck` → rare-find weighting

`utils/mining/exploration._luck_weighted` multiplies each outcome's selection weight
by `(1 + luck × boost)`, boost by rarity. Common stays flat, so luck never makes
junk/hazards *more* likely — and because the rarer finds rise, hazards fall in
*relative* terms.

| rarity | boost per luck point | weight ×, luck 1 / 2 / 3 |
|---|---|---|
| Common | 0.00 | 1.00 / 1.00 / 1.00 |
| Uncommon | 0.15 | 1.15 / 1.30 / 1.45 |
| Rare | 0.40 | 1.40 / 1.80 / 2.20 |
| Legendary | 0.60 | 1.60 / 2.20 / 2.80 |

**End-to-end effect** (re-derived from `eligible_outcomes(CAVERN, torch+pickaxe)` —
6 outcomes, base weight 13):

| luck (gear) | P(rare diamond vein) | P(hazard ambush) |
|---|---|---|
| 0 (none) | 7.69% | 15.38% |
| 1 (lucky charm *or* diamond pickaxe) | 10.00% | 14.29% |
| 2 (both) | 12.00% | 13.33% |
| 3 | 13.75% | 12.50% |

Small and steady: one luck source lifts the rare find by ~⅓ and trims the hazard
rate. Tunable via `_LUCK_RARITY_BOOST` — re-run the figures above
(`PYTHONPATH=disbot python3.10 -c "..."`) if the table changes.

## Guards

- `tests/unit/invariants/test_effective_stats_consumed.py` — `_UNWIRED_STATS` is now
  **empty**; the invariant fails if either stat loses its consumer.
- `tests/unit/utils/test_mining_grid.py::test_reveal_radius_*` — the curve + cap.
- `tests/unit/cogs/test_mining_exploration.py::test_luck_*` — identity at 0, rarity
  ordering, end-to-end rare-rate increase.
- `tests/unit/views/test_mining_grid_view.py::test_build_grid_embed_widens_window_with_a_brighter_light`.
