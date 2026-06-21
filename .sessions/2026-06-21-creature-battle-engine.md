# 2026-06-21 — Creature game PvP: the pure battle engine (foundation slice)

> **Status:** `complete` — work is done + green, but this is a substantial runtime-game plan step →
> `needs-hermes-review` (Q-0117): auto-merge is **disabled**, so green CI does **not** self-merge;
> it waits for Hermes/owner review. (Born-red HOLD lifted as the deliberate final step, Q-0133.)

> **Run type:** routine · dispatch

## What I did

Scheduled dispatch, no work order → advanced the headline ungated buildable lane (current-state ▶
Next action option (a)): **the creature-game PvP battle**. The full PvP feature is engine + cog +
interactive challenge views, explicitly a **runtime-verified** session in the
[plan](../docs/planning/creature-game-design-and-sim-2026-06-20.md) §4 — and I cannot verify live
Discord interactions in this container. So I scoped this PR to the **foundation half I *can* verify
without Discord runtime**: the **pure, level-normalized battle engine**, graduated from the
validated Monte-Carlo sim (`tools/game_sim/creature_battle_sim.py`) into the bot, plus a test suite
that **re-validates the sim's fairness gates inside the runtime engine**. The interactive cog +
challenge views (which genuinely need a live-walk) build on this engine next.

### What shipped (PR #1213)
- `disbot/utils/creatures/battle.py` — pure, stdlib-only, deterministic combat engine:
  - rarity→budget + archetype→spread **stat derivation** (`derive_stats`, graduated from the sim);
  - the **symmetric 6-element type chart** (`effectiveness`), pinned to a canonical `ELEMENT_CYCLE`
    constant — **not** `creature.ELEMENTS` (catalog first-seen order), which would silently re-wire
    effectiveness if the catalog were reordered (a correctness trap I caught while graduating it);
  - the **4-move kit** (Normal hit · element hit · +DEF · +ATK), level scaling + capped buff stages;
  - the **move-selection policies** (best-damage / naive-element / random / setup — the skill lever);
  - **level-normalized team construction** (`standard_team`, one-of-each-element, anti-P2W §3) +
    `order_type_aware`, `build_team`, `fresh_team`;
  - `resolve_battle()` → a `BattleOutcome` with a **structured, replayable turn-by-turn event log**
    + winner (the log shape the cog/views slice will render).
- `tests/unit/utils/test_creature_battle.py` (24 tests) — chart symmetry (exact), equal-stat type
  balance ≈50% (spread <5pts), normalized PvP ≈50%, skill rewarded-not-absolute (~69%), status-move
  value (~60%), raw +2-level dominance ~100% (the finding that motivates normalization), plus stat /
  move / combatant / resolution unit coverage. **All deterministic by fixed seed** (no flakiness).
- `disbot/utils/creatures/__init__.py` — re-exports the engine surface.
- Plan §4 + current-state ▶ Next action de-staled (engine SHIPPED; cog/views is the sharpened NEXT).

### Architecture note (a deliberate, noted deviation)
Plan §4 names `services/creature_battle_engine.py`. The engine is **pure combat math** (no DB, no
audit, no IO), so per `docs/architecture.md` it belongs in `utils/creatures/` beside its pure-domain
siblings `creature.py`/`encounters.py`, **not** the `services/` audited-write layer. The `services/`
seam enters only when a battle *persists a result / awards xp / emits audit* (the cog-wiring slice);
even then the math stays pure here. Took the cleaner layering and recorded why (working agreement:
prefer the better implementation, note the deviation).

## Verification
- `python3.10 scripts/check_quality.py --full` → green (11114 passed, 44 skipped; black/isort/ruff/
  mypy clean). One trap on the way: the PostToolUse auto-fixer didn't fire on `Write` (only `Edit`),
  so `black`/`ruff` (COM812) had to be applied by hand before CI would have gone green — see Context
  delta. `python3.10 scripts/check_architecture.py --mode strict` → exit 0 (no new findings).
- `python3.10 scripts/check_current_state_ledger.py --strict` and `check_docs.py --strict` → green.

## Why a foundation slice, not the whole feature
The plan flags the user-facing battle as runtime-verified. Shipping untested interactive Discord
views I can't live-walk would be low-confidence work stacked on a `needs-hermes-review` branch. The
engine is the correct, complete, fully-CI-verifiable foundation (the plan's "first PR = foundation;
later PRs build on top"), and it's the half whose *correctness is the whole game* — so it earns the
re-validation suite. The cog/views slice is sharply handed off below.

## Context delta
- **Needed but not pointed to:** nothing major — the fishing-mirrored creature spine
  (`utils/creatures/` + `services/creature_workflow.py`) and the sim were exactly where the plan +
  the prior session card said. The one reverse-engineered fact: the runtime `Creature` carries
  **no battle stats** (name/element/rarity/archetype/emoji only), so the engine must *derive* stats
  — the sim's `_spread`/`RARITY_BUDGET` is the canonical source for that.
- **Pointed to but didn't need:** the deep historical tail of `current-state.md` ▶ Next action (the
  ledger is enormous; the live sentence + Recently-shipped were enough — as the doc itself says).
- **Discovered by hand:** the type chart must key off a **fixed** element cycle, not the
  catalog-derived `ELEMENTS` order — a latent correctness trap if the two are conflated. Captured as
  a module comment + a dedicated test.
- **Decisions made alone:** (1) engine in `utils/` not `services/` (layering, noted above); (2)
  `NORMALIZED_LEVEL = 50` (cosmetic — the engine is symmetric in level); (3) `needs-hermes-review` +
  auto-merge disabled for this PR. None are product-intent — no router entry needed.
- **Flagged for maintainer:** the engine is **unit-validated but never run in a live battle** — the
  cog/views slice is where real Discord behaviour gets verified. Hermes review should sanity-check
  the combat *feel* (the sim's sample-battle log is the reference), not just the code.

## ⟲ Previous-session review (Q-0102)
The previous dispatch run (`2026-06-21-creature-game-catch-collection.md`, PR #1208) did the catch+
collection half cleanly by mirroring fishing precisely, and — crucially — its session card and the
plan §4 *explicitly pre-scoped* the battle as "a later `needs-hermes-review` slice," which made this
session's scoping decision trivial. That forward-pointering is the workflow working as intended.
One thing it could have done better: it left the **sim↔runtime constant duplication** implicit (it
graduated `creatures.json` and the catch constants but not the battle constants, and didn't note
that the battle slice would *re-duplicate* the sim's combat math). **System improvement it surfaces:**
when a runtime slice graduates numbers from a disposable design tool, the card should name the
resulting two-sources-of-truth surface so the *next* slice plans a parity guard up front — which is
exactly the Q-0089 idea I filed this run, closing that loop.

## 💡 Session idea (Q-0089)
[`creature-sim-engine-constant-parity-guard-2026-06-21.md`](../docs/ideas/creature-sim-engine-constant-parity-guard-2026-06-21.md)
— the combat-design constants now live in both the sim and the runtime engine; a small stdlib parity
test keeps the sim's "PLAYABLE" verdict honest about what players actually play. Indexed in the ideas
README. (Genuine, not filler — it's the direct structural consequence of graduating the sim's math.)

## 🧹 Grooming (Q-0015)
The session idea above *is* a freshly-routed decided/small-lane idea (idea → README index, with a
clear self-merge build path). The broader creature backlog (PvP cog/views, art, world-hub docking)
stays sequenced in the plan; nothing orphaned.

## 📋 Doc audit (Q-0104)
`check_current_state_ledger --strict` ✓ · `check_docs --strict` ✓ · plan §4 + current-state ▶ Next
action de-staled · idea filed + indexed · this card is the durable home for the run. No drift left
in chat.

## 📤 Run report

- **Did:** shipped the pure level-normalized creature **battle engine** + a 24-test fairness-gate
  suite, graduating the validated sim's combat math into `disbot/utils/creatures/battle.py` ·
  **Outcome:** shipped (awaiting Hermes review — not self-merged)
- **Shipped:** #1213 — creature PvP battle engine (foundation slice), `needs-hermes-review`,
  auto-merge disabled; CI green.
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** `none` (the open creature design calls — PvP balance/art — are
  already routed under Q-0187; nothing new this run)
- **⚑ Owner manual steps:** `none`
- **⚑ Self-initiated:** `none` (option (a) was the dispatched/current-state ▶ Next action lane; the
  Q-0089 idea was filed, not built)
- **↪ Next:** the user-facing PvP flow (runtime-verified `needs-hermes-review`, builds on the shipped
  engine) — `cogs/creature_battle/` + `views/creature_battle/` panels mirroring the `rps`/`deathmatch`
  challenge pattern, a thin `services/` boundary to read each player's team from the collection-log
  and (later) record results, level-normalized matchup. Engine API to build on:
  `utils.creatures.battle.{resolve_battle, standard_team, build_team, Combatant, BattleOutcome}`.
