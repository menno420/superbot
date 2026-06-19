# 2026-06-19 — Fleet A5: untangle deathmatch circular import

> **Status:** `complete`

Fleet unit **A5** from `docs/planning/ultracode-fleet-plan-2026-06-19.md` — Lane A
architecture boundary-debt burndown. Untangle the `cogs/deathmatch/actions.py` ↔
`cogs/deathmatch_cog.py` circular import and remove the module-level `views → cogs`
layer-boundary violations in `views/games/deathmatch_panel.py`.

## Arc

**The cycle (mapped before touching anything):**
- `cogs/deathmatch/actions.py` imported `Deathmatch` from `cogs/deathmatch_cog.py`
  at **module level** — but used it *only* as a type annotation (the `cog` param of
  `has_existing_duel`; at runtime it reads `cog.active_duels`, a dict).
- `cogs/deathmatch_cog.py` lazily imports `views.games.deathmatch_panel`
  (inside `build_help_menu_view`) and `cogs.deathmatch.schemas` (inside `cog_load`).
- `views/games/deathmatch_panel.py` imported from **both** `cogs.deathmatch.actions`
  and `cogs.deathmatch_cog` at module level — the two `views → cogs` warnings
  (ticket `arch-fix-13`, `architecture_rules/layers.yaml:301-308`).

**Caller/importer map (incl. lazy + test string-patches):** the symbols are pinned to
their modules by the test suite — `tests/unit/cogs/test_deathmatch_guild_scope.py:68`
monkeypatches `"cogs.deathmatch_cog._tick_duel_gear_wear"` *by string path*, and four
test files import `_Duel`/`_DuelView`/`_ChallengeView`/`_tick_duel_gear_wear`/`BASE_*`
from `cogs.deathmatch_cog` and `pick_bot_action`/`can_challenge_human` from
`cogs.deathmatch.actions`. Those test files are outside this unit's file set, so the UI
types **cannot be physically relocated** without breaking tests I may not edit. The
clean break that keeps every symbol in its existing home is the documented
cycle-breaking pattern in this repo: **TYPE_CHECKING-guard the type-only imports + lazy
function-body imports for the runtime uses** (only module-level imports are layer-checked,
per `layers.yaml` header).

**The break:**
- `actions.py`: `from cogs.deathmatch_cog import Deathmatch` → `TYPE_CHECKING`-guarded.
  Removes the module-level `actions → deathmatch_cog` runtime edge that closed the cycle.
- `deathmatch_panel.py`: the two module-level `cogs.*` imports → `TYPE_CHECKING`
  (type-only: `_Duel`/`Deathmatch` annotations) + lazy function-body imports for the four
  runtime sites (`_BotDuelView.__init__` → `_Duel`; `_bot_turn` → `pick_bot_action`;
  `_DeathmatchOpponentSelect.callback` → `can_challenge_human`/`has_existing_duel`/
  `make_duel_key`/`_ChallengeView`; `_resolve_deathmatch_cog` → `Deathmatch`). The panel
  no longer carries any module-level `views → cogs` edge.

Behaviour is identical (no logic changed). The stale `arch-fix-13` entries in
`architecture_rules/layers.yaml:301-308` are now harmless dead config (the checker only
emits a warning when the import is actually present) — left untouched as that file is
outside this unit's fixed set; the reconciliation pass can prune them.

## Shipped

- **#1096** — A5: untangle deathmatch circular import. Two files:
  `disbot/cogs/deathmatch/actions.py`, `disbot/views/games/deathmatch_panel.py`.
- Verification (all green): `check_architecture --mode strict` (0 errors, 46 warnings —
  down from 48, the two deathmatch `views → cogs` warnings removed);
  `check_quality --check-only` (exit 0); `pytest --collect-only` (10749 collected, no
  import errors); `pytest -k deathmatch` (47 passed); plus `mypy` on both files (clean)
  and a runtime import-chain probe confirming the cycle edge is gone and the
  `_tick_duel_gear_wear` patch target still resolves.

## ⟲ Previous-session review

A5 ran in the Lane A fleet alongside A1–A8/B1–B8. The fleet brief (A4/A5 flagged "run
last, map every caller incl. lazy imports first") did exactly the right thing here — the
explicit "map before moving" instruction is what surfaced the test-string-patch
constraint that *blocks* the brief's literal "lift the UI types into the view" wording.
**Concrete improvement to the system:** when a fleet/planning brief prescribes a code
*move* ("lift X out of module Y"), it should note that *test files which import or
string-patch the symbol are part of the constraint set even when they're outside the
unit's editable file set* — a move is only safe if the symbol's import path survives. A
one-line "check `grep -rn '<symbol>' tests/ | grep -E 'import|patch'` before relocating"
in the brief's Rules-of-engagement A4/A5 note would catch this class up front. (Filed as
the session idea below.)

## 💡 Session idea

**Arch-checker "stale known-violation" lint.** `architecture_rules/layers.yaml`
accumulates `known_violations` entries (like the two `arch-fix-13` deathmatch lines this
PR just made obsolete) that linger as dead config once the underlying import is removed,
because the checker only consults `_is_known` when a live violation is found — a removed
violation leaves its YAML entry orphaned and invisible. A small guard in
`check_architecture.py` (or a `scripts/check_stale_known_violations.py`) that flags any
`known_violations` / `known_lazy_violations` entry whose `(file, import)` pair no longer
exists in the source would turn boundary-debt burndown into a *measurable, self-cleaning*
ledger: every unit that removes a tracked edge gets a nudge to delete the now-dead YAML
row, instead of leaving it for the 30-PR reconciliation pass. Worth having because the
fleet run is about to retire ~48 such entries at once.

## 📤 Run report

- **Did:** untangled the deathmatch actions↔cog circular import and removed the panel's two module-level `views → cogs` edges via TYPE_CHECKING + lazy imports · **Outcome:** shipped
- **Shipped:** #1096 — A5 deathmatch cycle break (2 files; 0 arch errors, 47 deathmatch tests green)
- **Run type:** `manual` (fleet unit dispatch)
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none
- **⚑ Self-initiated:** A5 — docs/planning/ultracode-fleet-plan-2026-06-19.md
- **↪ Next:** remaining Lane A units (A1–A4, A6–A8) burn down the rest of the `views → cogs` / helper-in-cog debt; reconciliation pass can prune the now-dead `arch-fix-13` YAML rows.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 0 (PR #1096 open, auto-merge armed on green) |
| CI-red rounds | 0 (all local checks green on first run) |
| Repo-rule trips | 0 (arch check: 0 errors) |
| New ideas contributed | 1 (stale known-violation lint) |
| Ideas groomed | 0 (fixed-scope fleet unit) |
