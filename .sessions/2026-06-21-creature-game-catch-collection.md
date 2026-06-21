# 2026-06-21 — Creature game runtime v1: catch + collection (dex)

> **Status:** `complete` — runtime feature (new `disbot/cogs/` + `services/` + migration), but
> **read-only/additive** (a brand-new opt-in subsystem; empty tables = byte-identical to the
> pre-creature bot) → self-merge on green (Q-0113). PvP, the substantial half, is deferred to its
> own `needs-hermes-review` session.

> **Run type:** routine · dispatch

## What I did

Scheduled dispatch, no work order → advanced the headline ungated buildable lane (current-state ▶
Next action): **the creature-game v1 runtime cog — catch + collection/dex first** (PvP is a separate
`needs-hermes-review` session). The design + Monte-Carlo sim + 36-creature catalog all shipped this
band (#1183/#1185/#1193/#1194, verdict PLAYABLE); this is the first `disbot/` runtime slice per the
[plan](../docs/planning/creature-game-design-and-sim-2026-06-20.md) §4 — the **catch** half — built
by mirroring the fishing subsystem precisely (pure domain → audited workflow → CRUD → hub-less cog),
reusing the **fishing-style catch log + `game_xp`** (the plan's explicit directive) and graduating
the sim's `creatures.json` to `disbot/data/` (Q-0186).

### What shipped (new files)
- `disbot/data/creatures/creatures.json` — the 36-creature original launch catalog (no Pokémon IP,
  Q-0187), graduated from `tools/game_sim/creatures.json` with per-element display emoji.
- `disbot/utils/creatures/` (`creature.py` + `encounters.py` + `__init__.py`) — pure, stdlib-only
  domain: the catalog loader (rarity-tiered, fail-safe → empty), the **rarity-weighted wild
  encounter** (Common common, Epic rare), and the **catch roll** (`rarity base + small capped
  level bonus`, never a sure thing — no level gate; rarer = harder, not locked).
- `disbot/services/creature_workflow.py` — the audited write boundary: on a *successful* catch the
  collection-log write + the `GAME_CREATURE` xp award commit in ONE `db.transaction()`, EventBus
  emit **after** commit (Q-0071); a fled creature writes nothing and awards no xp. `is_new`
  ("New dex entry!") read before the write.
- `disbot/utils/db/games/creatures.py` + migration `077_creature_collection_log.sql` — the
  collection-log CRUD (per-(user,guild,creature) tally; empty table = additive no-op), with a
  known-catalog allow-list on the leaderboard (the fishing reconciliation lesson).
- `disbot/cogs/creature_cog.py` — `!catch`/`!hunt`, `!dex`/`!collection`/`!creatures` (grouped by
  element), `!dextop`/`!topcatchers`, + the Help hook (hub-less v1, exactly like fishing).
- `services/game_xp_service` — new `GAME_CREATURE` track (🐾 Creatures label) + the `catch` award
  (4 xp); the world card surfaces creature standings automatically (it reads `game_xp` rows).
- Wiring: `config.py` (cog registered), `utils/db/__init__` (exports), `utils/subsystem_registry`
  (the `creature` subsystem entry, mirroring fishing).

### Generated-artifact + doc parity (the parity guards caught the new cog/subsystem — regenerated)
Adding a cog+subsystem+commands legitimately drifted six committed artifacts; all regenerated via
their own `--write`/regen commands (the system working as designed):
- `docs/operations/env-vars.md` (line-shift from the new config.py line) — `scan_env_usage --write-doc`.
- `architecture_rules/extension_roles.yaml` + `docs/architecture/extension-taxonomy-crosswalk.md`
  (classified `creature` as `product_subsystem`) — `extension_crosswalk --write`.
- `dashboard/data/dashboard.json` + `botsite/data/site.json` + `botsite/site/data.js` —
  `export_dashboard_data` (44 cogs, 311 commands now).
- `docs/setup-platform/settings-customization-command-map.md` — added the `### creature` section.
- `docs/planning/creature-game-design-and-sim-2026-06-20.md` §4 — marked the catch slice SHIPPED.

### Tests
- `tests/unit/utils/test_creature_catalog.py` (11), `test_creature_encounters.py` (8),
  `tests/unit/db/test_creature_db.py` (4), `tests/unit/services/test_creature_workflow.py` (6) —
  catalog shape, rarity-weighted rolls, SQL-shape pins, and the Q-0071 transaction-membership +
  flee-writes-nothing contract.

## Verification
- `python3.10 scripts/check_architecture.py --mode strict` → 0 errors (no new warnings).
- `python3.10 scripts/check_quality.py --full` → green (black/isort/ruff/mypy + full pytest, 11000+).
  mypy: `Success: no issues found in 745 source files`.
- The six parity guards that initially reddened (settings-doc, env-usage, generated-artifacts-fresh,
  atlas, export_dashboard_data, extension_crosswalk) + botsite all green after regeneration.

## Handoff
The catch half is live and self-merging on green. **The next creature slice is the level-normalized
PvP battle** — `services/creature_battle_engine.py` (the sim's math at `tools/game_sim/
creature_battle_sim.py` graduates here, pure), `cogs/creature_battle/` + `views/creature_battle/`
panels mirroring the `rps`/`deathmatch` challenge pattern. It is **runtime-verified
`needs-hermes-review`**, not an autonomous self-merge (plan §4 + the §3 finding that raw levels make
1v1s deterministic → PvP must normalize to a flat level). Other ungated lanes (current-state ▶):
botsite React-SPA migration, the `public-data-contract-field-snapshot` guard, or a
`needs-hermes-review` lane (consistency-linter AI-nav PR 1 · procedures→skills Batch 2).

## ⚑ Self-initiated
None — this was the dispatched/plan lane (current-state ▶ Next action option (a), an executable
`docs/planning/` plan). No invented feature; PvP correctly deferred to its gated session.

## 💡 Session idea
**A `creatures.json` ↔ sim parity guard** (stdlib test): assert the runtime catalog
`disbot/data/creatures/creatures.json` and the design-artifact `tools/game_sim/creatures.json` carry
the **same creature set** (name/element/rarity/archetype) so the balance the sim validated stays the
balance that ships. Right now the runtime catalog was *graduated by hand* from the sim; nothing fails
if a future creature is added to one but not the other, silently shipping an unvalidated roster (the
plan's whole "balance-before-build gate" depends on the two staying in lockstep). Cheap, closes a
real drift class, and generalizes when the PvP engine lands (it'll read the same catalog). Captured
for grooming.

## ⟲ Previous-session review
The previous run (CI-reliability batch, BUG-0020/0021/0022) was strong: it caught BUG-0022 — that
`check_quality.py --full` + `git add -A` could silently commit a corrupted `data.js` — a latent trap
live since the botsite data layer landed, and root-fixed it. That fix paid off **this** session: I
regenerated `data.js` via `export_dashboard_data` and the botsite sync tests stayed green precisely
because `main()` no longer clobbers the tracked file off a stale path. One thing it (and the band's
planning) could improve, now acted on as my session idea: the **generated-artifact parity net is
strong for web/docs artifacts but had no guard tying the new game's runtime catalog to the
sim-validated one** — a catch+battle game's correctness hinges on that pair staying in sync, and
nothing enforces it yet. Surfacing it here keeps the self-auditing loop honest: each new subsystem
should ship (or at least name) the parity guard for its own source-of-truth pair.

## 📤 Run report
- **Run type:** routine · dispatch
- **What shipped:** creature-game v1 runtime **catch + collection** slice (PR #1208) — new
  `creature` subsystem (cog + pure domain + audited workflow + migration 077 + 36-creature catalog +
  `GAME_CREATURE` xp track), `!catch`/`!dex`/`!dextop`, full test suite, and the six regenerated
  parity artifacts. PvP deferred to a `needs-hermes-review` session.
- **⚑ Owner-decisions:** none
- **⚑ Owner-manual-steps:** none (merge auto-deploys; migration 077 runs on boot)
- **⚑ Self-initiated:** none
