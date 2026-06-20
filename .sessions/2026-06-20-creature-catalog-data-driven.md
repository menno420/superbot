# 2026-06-20 — Creature roster as a data-driven catalog (sim-validate ~36 at launch scale)

> **Status:** `complete`

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

## Shipped (PR #1193)

- `tools/game_sim/creatures.json` (36 creatures) + `creature_battle_sim.py` loads it +
  `test_creature_battle_sim.py` updated + design doc §2a marked BUILT.

## Decisions made alone (owner said "pick good defaults")

- **36 creatures** (6/element, 12C/12U/6R/6E) — middle of the recommended 30–40 band; enough dex
  depth, not an art/balance overreach. Reversible data.
- **Default flavor (names) mine to set, owner refines** — gear-paper-doll precedent (I build the
  system + a working default; owner swaps the creative skin). Kept the original 12's iconic names
  (Cindling, Magmaul, Rippling, Abysscale, Sproutle, Thornmaw, Voltkit, Stormfang, Pebblet,
  Boulderon, Zephyrl, Galeon) and added 24 in the same voice.
- **Uniform Common/balanced per-element starter** (slot 0) — makes the type-balance check
  apples-to-apples, which is why spread fell to 1.0pt.

## Flagged for maintainer

- **Roster flavor is a default, not a design lock** — names/themes are yours to rename anytime
  (it's one JSON file); the *engineering* (data-driven loading + sim-proven balance at launch
  scale) is what's locked in. Q-0187(a–d) confirmations still open (this builds on the
  recommended path, doesn't pre-empt the decision).

## 💡 Session idea (Q-0089)

**A `--roster <path>` flag on the sim so an owner/agent can A/B a *candidate* roster JSON without
editing the committed catalog.** Now that the roster is data, balance-testing a proposed change
(new creature, retuned rarity budget) should be a one-liner against a scratch file, not an edit +
revert. Tiny argparse addition; makes the balance-before-build gate frictionless for the next
roster change. Lane = tooling. (Captured, not built.)

## ⟲ Previous-session review (Q-0102)

The #1192 (branch-freshness) session closed the stale-branch class well — and this session is the
first to *benefit* from it: the SessionStart banner flagged this branch `1 behind / 2 ahead`, I
synced in one step, and opened #1193 on a clean base (no rebase foot-gun this time). That's the
proactive guard working end-to-end on its very next use. **System improvement:** the one remaining
manual step is the agent *remembering* to run the sync the banner prints — the captured `/sync-branch`
guarded command (from #1192) would close that last gap; worth promoting next.

## 📤 Run report

- **Did:** turned the creature roster into a sim-validated data-driven catalog (36, PLAYABLE) ·
  **Outcome:** shipped (design tooling + docs)
- **Shipped:** #1193 — `creatures.json` (36) + sim loads it + test/doc updates
- **Run type:** `manual · self-initiated product step (Q-0172; §2a next step)`
- **⚑ Owner decisions needed:** Q-0187(a–d) still open (this builds the recommended path)
- **⚑ Owner manual steps:** none (rename creature flavor anytime — it's one JSON file)
- **⚑ Self-initiated:** YES — promoted the §2a "build the catalog" step without waiting (Q-0172);
  flagged here. Flavor is a default, owner refines.
- **↪ Next:** the gated runtime build (Lane A catch engine, Q-0186) graduates this catalog to
  `disbot/data/`; or deepen the sim (real moves/abilities) before runtime.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs this session | 1 (#1193, design tooling + docs, auto-merge on green) |
| Runtime (`disbot/`) code changed | 0 |
| Roster | 12 (hardcoded) → 36 (data-driven JSON) |
| Sim verdict at launch scale | PLAYABLE (no flags), seeds 42 + 7; type-balance spread 1.0pt |
| Tests | 6/6 (`tests/unit/tools/`) |
| Branch-freshness guard | fired on this session's own stale branch → synced cleanly (first real use) |
| CI-red rounds | 1 (by-design born-red session gate only) |
| New ideas contributed | 1 (sim `--roster <path>` A/B flag) |
