# 2026-06-20 — Creature roster as a data-driven catalog (sim-validate ~36 at launch scale)

> **Status:** `in-progress`

## Arc

Product progress on the creature game (the CI/branch-hygiene thread is complete: #1187/#1188/#1191/
#1192 all merged). This executes the §2a "natural next design step" named last session: make
"creature = a data row" real and **prove ~30–40 balances** before any runtime build — the
balance-before-build gate. Design tooling only — no `disbot/` runtime, no owner gate (reversible
data + sim; Q-0172 idea→build).

## What this PR adds

- **`tools/game_sim/creatures.json`** — the v1 launch catalog: **36 original creatures** (6 per
  element; 12 Common / 12 Uncommon / 6 Rare / 6 Epic). Each is just `{name, element, rarity,
  archetype}` — **stats are derived at load** (`budget = RARITY_BUDGET[rarity]` split by archetype
  weights), so there are no stored stats to drift.
- **`creature_battle_sim.py`** — `_roster()` now **loads from the catalog** instead of a hardcoded
  list of 12. Adding a creature is now a data row, not a code edit (Q-0187d).
- **`test_creature_battle_sim.py`** — `test_roster_well_formed` now asserts the launch band
  (30–40) + an even per-element spread, not the old fixed 12.
- **Design doc §2a** — marked the catalog **BUILT** with the sim result.

## Verification

- Sim on the full 36 → **PLAYABLE (no flags)**, both seed 42 and seed 7. Type balance *tighter* than
  the 12-roster: per-element 49.6–50.6%, **spread 1.0pt** (uniform Common/balanced per-element
  starter makes the type check apples-to-apples); catch grind ~7 at L1.
- `pytest tests/unit/tools/` → 6/6. `check_quality --check-only`, `check_docs --strict`,
  `check_plan_homing` → all green.

## Shipped

_(filled at close)_
