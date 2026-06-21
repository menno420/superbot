# Idea — a parity guard tying the creature sim to the runtime battle engine

> **Status:** `ideas` · captured 2026-06-21 (creature PvP battle-engine session, PR #1213) ·
> **BUILT 2026-06-21 (PR #1227)** — same dispatch run, after #1213 merged.
> Not a plan, not approval. Source + binding contracts win.

> **▶ SHIPPED (PR #1227):** `tests/unit/tools/test_creature_sim_engine_parity.py` loads both modules
> and asserts they agree on every shared design constant (type chart · element cycle · rarity
> budgets · archetype weights · move powers · buff step/cap · signature move names · level-scaling
> rates · team size) **plus** a behavioral end-to-end check (the engine derives the same stat line
> the sim does for the whole catalog). The sim's archetype-weights dict was lifted from a local in
> `_roster()` to a module constant `ARCHETYPE_WEIGHTS` so it's comparable. This idea is now closed.
> **Lane:** decided/small — a stdlib parity test, no owner decision needed.
> **Subsystem:** games (creatures) · tooling.

## The problem this catches

The creature game now has the **same combat-design constants in two places**:

- `tools/game_sim/creature_battle_sim.py` — the Monte-Carlo **playability simulator** (the design /
  tuning tool the owner uses to validate balance before shipping), and
- `disbot/utils/creatures/battle.py` — the **runtime battle engine** that graduated that math
  (shipped this session).

Both independently define the *same* design numbers: `RARITY_BUDGET`, the archetype stat weights,
the type-chart multipliers (`STRONG`/`WEAK`/`NEUTRAL`), the element cycle, `NORMAL_POWER` /
`ELEMENT_POWER`, `BUFF_STEP` / `BUFF_CAP`, the per-element signature-move names, and the
`HP_PER_LVL` / `OFF_PER_LVL` level-scaling rates. That is a **two-sources-of-truth drift class**:
the owner tunes a number in the sim to fix balance, the runtime engine keeps the old value, and the
sim's "PLAYABLE" verdict no longer describes the bot players actually experience — silently. It's
exactly the drift the repo already guards elsewhere (the `panel_base_class` allowlist↔arch-frozenset
parity test #1166; the dashboard freshness umbrella #1027).

## The idea

A small stdlib **parity test** — `tests/unit/tools/test_creature_sim_engine_parity.py` — that loads
both modules (the sim via `importlib`, the repo convention for tool scripts) and asserts they agree
on every shared design constant. One assertion per constant family; a tuning change to either side
that isn't mirrored fails CI with a clear "sim and runtime engine disagree on X" message.

Open sub-decision (cheap, defer to build time): assert *equality* of the raw constants, **or** the
stronger "same `effectiveness(a, b)` for every element pair + same derived stats for a sample
roster". The latter survives a refactor that changes representation but not behavior; start with the
former (simplest) and add the behavioral check if the constants are ever restructured.

## Why it's worth having

- **Keeps the balance-before-build gate honest** — the sim's verdict only means something if the
  runtime engine *is* the thing the sim modelled. This is the whole premise of the "use a simulator
  to see how playable it is" discipline the owner asked for.
- Tiny, stdlib-only, fully verifiable, no runtime/Discord needed → a clean self-merge lane.
- Naturally extends as the game grows: when v2 adds moves/creatures-as-data (plan §5 future lanes),
  the parity surface grows with it and the guard keeps both copies honest.

## Provenance / disposability

Surfaced by the PR #1213 engine session (the duplication is a direct consequence of graduating the
sim's math into the bot rather than importing it — correct, since the sim is a *disposable design
tool* that must not be a runtime dependency). Disposable like any guard: delete it if the sim is
ever retired (plan §3 notes the sim is deletable once its numbers are pinned — at which point the
runtime engine becomes the sole source of truth and this guard has nothing left to compare).
