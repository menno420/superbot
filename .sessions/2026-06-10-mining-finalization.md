# 2026-06-10 — Mining & tool/gear finalization (4-PR stack)

**PRs (stacked, each based on its predecessor; verify merges live):**
[#661](https://github.com/menno420/superbot/pull/661) RS01 atomic shop purchase →
[#663](https://github.com/menno420/superbot/pull/663) RS02 stage 1 (relocate + workshop workflow) →
[#664](https://github.com/menno420/superbot/pull/664) RS02 stage 2 (full write boundary + recipes reconciliation) →
[#665](https://github.com/menno420/superbot/pull/665) progression platform (game-XP, deeper ladders, gear/recipe UX, duels wear, PIL cards).

**Authoritative docs:** `docs/ownership.md` (§ Cross-domain transactions + the
mining/game_xp rows), `docs/subsystems/games.md`, router §32 (Q-0075/Q-0076),
consolidated plan Batch 7 execution record. The plan itself was approved via
ExitPlanMode after an external ChatGPT review pass (all its claims
source-verified; the RS02 "staged, separate PRs" objection resolved by actually
splitting 2a/2b instead of recording a deviation).

## What shipped (one line each)

- Q-0071 plumbing: conn-aware `utils/db` primitives (+ metrics preserved),
  `db.transaction()`, `economy_service.{debit,credit}_in_txn` (no-event legs).
- The FIND-RS01 two-commit shop purchase → one transaction (live-proven:
  concurrent double-click = exactly one charge).
- Mining: pure domain → `utils/mining/`; ALL writes → `services/mining_workflow.py`
  (one transaction per op; AST ratchet `test_mining_write_boundary.py`);
  `cogs/mining/` deleted; characterization net kept every message byte-identical.
- recipes.json 47 → 13 curated (+5 new-tier recipes), alignment lint governs content.
- Shared game-XP track (migrations 065/066 — renumbered around #659's 064_help_overlay): central award policy, daily soft cap, derived
  shared level, awards atomic with their actions, `gamexp`/`crafting` boards,
  depth records; level-ups render inline.
- Deeper ladders incl. **diamond lantern → MAGMA finally reachable** (depth-3 was
  dead content — nothing granted `depth_access` 3).
- Gear panel (slot→item selects + Equip Best), Recipe browser (taxonomy categories +
  craft-on-select + >25 pagination), fuzzy names, `!fastmine`, duels wear (Q-0054
  closed), PIL inventory + character stat cards.

## Context delta (the six-question reflection)

- **Route miss:** none serious — CLAUDE.md → collaboration-model → current-state →
  journal → games folio + brainstorm §7 was exactly right for this task.
- **Route excess:** the consolidated plan is now very long; grepping section
  headers first (the journal rule) was essential — reading Batch 7 alone sufficed.
- **Discovered by hand:**
  (1) discord.py 2.7 select testing: a REAL `Select` instance's `values` reads
  `self._values` (via a ContextVar override) — `_selected_values` does not exist;
  the MagicMock idiom avoids this entirely.
  (2) asyncpg `AmbiguousParameterError` when one `$n` feeds two column types
  (BIGINT + INTEGER) — invisible to mock-pool tests, caught only by the live-DB
  pass; fix with explicit `::` casts. A live round-trip per new SQL shape is worth
  the 30 seconds.
  (3) The CI isort skip-glob does NOT actually exclude `tests/` (glob alternation
  `(a|b)` isn't glob syntax) — touched test files must be isorted even though
  black/ruff skip them.
  (4) `check_architecture` flags any `pool.*` use outside `utils/db/` — the
  `db.transaction()` context manager is the sanctioned way a workflow service
  holds a transaction.
- **Decisions made alone:** PR 2a/2b split instead of the plan-review's
  "record a deviation" (strictly more compliant with Batch 7); receiver-aware AST
  invariants (the `set_depth`/`add_item` name collisions with setup/discord.ui made
  name-only scans false-positive — the CodeGraph name-collision lesson applies to
  AST nets too); award-inside-transaction rolls the whole action back on XP
  failure (rare, simplest, consistent with Q-0071).
- **Weak point of what shipped:** duels wear is unit-tested but not live-clicked
  (needs two humans); the daily soft cap's read-compute-write has a documented
  benign race; `_tick_duel_gear_wear` re-reads equipment after the duel rather
  than using duel-start state (a mid-duel unequip dodges wear — accepted, noted).
- **One change that would have helped:** a journal rule that new SQL with mixed
  column types needs a live round-trip before the suite run — added as the
  candidate rule below.

## Candidate rule (not yet promoted)

- **Run one live-DB round-trip for every NEW SQL statement** (not just mock-pool
  pins) — two of this session's three real bugs (asyncpg type deduction, the
  isort skip-glob being a no-op is the third) were invisible to mocks.

## Next

- **Structures (§7.5 Forge/Vault/Home)** on the new write boundary, then the
  **§7.4 capped skill tree** (substrate ready: `game_xp` + `EffectiveStats`).
- Maintainer live-walk suggestions: `!minemenu` → Gear/Recipes panels,
  `!character` (stat card), craft a diamond lantern → descend ×3 → MAGMA,
  a PvP duel to see wear notes.
