# 2026-06-21 — Creature sim↔engine constant parity guard (PR 2)

> **Status:** `complete` — small stdlib test + a contained refactor of a disposable design tool →
> **ungated self-merge on green** (Q-0113); auto-merge armed, born-red HOLD lifted as the final step.

> **Run type:** routine · dispatch

## What I did

Same dispatch run, continuation after PR #1213 (the creature battle engine) **merged** to main.
Built the Q-0089 idea I filed earlier this run —
[`creature-sim-engine-constant-parity-guard`](../docs/ideas/creature-sim-engine-constant-parity-guard-2026-06-21.md).
With #1213's engine now on main, the dependency that blocked a clean second slice was resolved, and
the parity guard is exactly the kind of small, fully-CI-verifiable, ungated self-merge follow-on the
dispatch prompt asks for (2–3 slices, not one) — and it directly hardens what #1213 shipped.

### The drift it closes
#1213 **graduated** the combat math from the disposable sim (`tools/game_sim/creature_battle_sim.py`)
into the runtime engine (`disbot/utils/creatures/battle.py`). Graduation *copies* the math (correct —
the sim must never be a runtime dependency), so the design constants now live in two places: tune one,
the other silently diverges, and the sim's "PLAYABLE" verdict stops describing what players play. Same
two-sources-of-truth class the repo already guards with the `#1166` allowlist↔arch-frozenset test.

### What shipped (PR #1227)
- `tools/game_sim/creature_battle_sim.py` — lifted the archetype-weights dict from a local in
  `_roster()` to a module constant `ARCHETYPE_WEIGHTS` (it was the *only* design constant the sim
  kept local; every other is module-level), so the guard can compare it. Pure refactor — `_roster`
  now reads the constant; no behavior change (the existing `test_creature_battle_sim.py` still green).
- `tests/unit/tools/test_creature_sim_engine_parity.py` — importlib-loads the sim (repo convention for
  tool scripts) and asserts sim↔engine agreement on: type-chart multipliers, element cycle, rarity
  budgets, archetype weights, move powers, buff step/cap, signature move names, level-scaling rates,
  team size — **plus** two behavioral checks: `effectiveness()` agrees for every (attacker, defender)
  pair, and `derive_stats()` produces the same stat line the sim does for the whole live catalog
  (the strongest form — survives a representation refactor, fails a real re-wire). An inert-guard
  assertion (`checked > 0`) fails loudly if the catalog and roster ever stop overlapping.

## Verification
- `python3.10 scripts/check_quality.py --check-only` → exit 0 (true CI mirror; sim file ruff-clean in
  CI scope; the test file's `S101`/`PT018` are in `tests/`, which CI excludes from ruff).
- `python3.10 scripts/check_quality.py --full` → green (see run).
- Targeted: 45 creature tests pass (10 new parity + 11 existing sim + 24 engine).

## 📤 Run report

- **Did:** built the Q-0089 sim↔engine constant **parity guard** (filed earlier this run), hardening
  #1213's graduated combat math against silent drift · **Outcome:** shipped (self-merge on green)
- **Shipped:** #1227 — parity guard + sim `ARCHETYPE_WEIGHTS` module-constant lift; ungated self-merge.
  (This run also shipped #1213 — the battle engine — which MERGED; see its card.)
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** `none`
- **⚑ Owner manual steps:** `none`
- **⚑ Self-initiated:** the parity guard (#1227) — promoted my own Q-0089 idea → build with no
  dispatched order or owner ask (Q-0172). Contained, reversible, test-only + a disposable-tool
  refactor; flagged here for review. (The idea was filed openly in #1213; the build is the
  self-initiated step.)
- **↪ Next:** unchanged from #1213's handoff — the user-facing creature **PvP flow**
  (runtime-verified `needs-hermes-review`): `cogs/creature_battle/` + `views/creature_battle/` panels
  mirroring `rps`/`deathmatch`, a thin `services/` boundary to read each player's team from the
  collection-log and (later) record results. Build on `utils.creatures.battle.{resolve_battle,
  standard_team, build_team, Combatant, BattleOutcome}`; the parity guard now keeps the sim honest
  as the engine evolves.
