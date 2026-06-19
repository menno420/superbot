# 2026-06-19 — Fleet A4: move diagnostic embeds into services/

> **Status:** `complete`

## Arc

Fleet unit A4 (`docs/planning/ultracode-fleet-plan-2026-06-19.md`, Lane A —
architecture boundary-debt burndown). Moved the big diagnostic embed module and
its helpers out of `cogs/` into `services/`, where the `views/diagnostic/` panels
can import them without reaching across the `views → cogs` layer boundary.

Before moving anything I mapped every caller (`context_map.py` + a full-tree grep
that searched function bodies too) — 9 importers of `_platform_embeds` and 4 of
`_helpers`, several of them lazy/function-body imports, plus 13 test files that
import these modules including several `unittest.mock.patch(
"cogs.diagnostic._platform_embeds....")` patch sites. To keep those patch sites
and every importer outside my touch set resolving, the old cog paths stay as thin
re-export shims pointing at the new `services/` modules.

## Shipped

- `cogs/diagnostic/_platform_embeds.py` (2,280 lines) → `services/diagnostic_embeds.py`
  (via `git mv`; internal `_fmt_snapshot_value` cross-ref repointed to
  `services.diagnostic_helpers`).
- `cogs/diagnostic/_helpers.py` → `services/diagnostic_helpers.py` (via `git mv`;
  the lazy `cogs.diagnostic._log_buffer` import stays lazy — function-body, so no
  module-level `services → cogs` violation; the checker only flags module-level).
- New thin re-export shims at both old cog paths (`_platform_embeds.py`,
  `_helpers.py`) re-exporting the full public + private surface (incl.
  `_EMBED_SOFT_CAP`, `_FIELD_HARD_CAP`, `_INFORMATIONAL_PREFIX`, `_fmt_snapshot_value`,
  `__all__`) so all existing importers and `mock.patch` sites resolve unchanged.
- Repointed the three `views/diagnostic/` importers to `services/`:
  `hub_panel.py` + `platform_panel.py` (module-level) and `paginator.py` (lazy) —
  clearing the two `[known] views → cogs` warnings on `hub_panel.py` and
  `platform_panel.py`.

Behaviour identical. No files outside the A4 touch set changed. No test files edited.

## Verification (all green)

- `check_architecture.py --mode strict` → 0 errors, 46 warnings, **no diagnostic
  `views → cogs` warning remains** (the two A4 targets cleared); no new violations.
- `check_quality.py --check-only` → All checks passed.
- `pytest --collect-only -q` → 10749 tests collected, 0 import errors.
- `pytest tests/unit -k "diagnostic or platform_embed or platform_panel"` → 278 passed.
- Extra patch-site sanity (`test_automation_executor`, `test_setup_readiness`,
  `test_wizard_hub`, `test_operator_explainers`) → 77 passed — shim preserves
  `mock.patch("cogs.diagnostic._platform_embeds....")` resolution.

## 📤 Run report

- **⚑ Self-initiated:** A4 — docs/planning/ultracode-fleet-plan-2026-06-19.md
- **PR:** #1097 (auto-merge armed, MERGE).
- **Touched (A4 set only):** `services/diagnostic_embeds.py` (new, moved),
  `services/diagnostic_helpers.py` (new, moved), `cogs/diagnostic/_platform_embeds.py`
  (now shim), `cogs/diagnostic/_helpers.py` (now shim), `views/diagnostic/hub_panel.py`,
  `views/diagnostic/platform_panel.py`, `views/diagnostic/paginator.py`,
  this session card.

### 💡 Session idea

A tiny `check_shim_reexports.py` AST guard: when a module is a declared
back-compat re-export shim (one `from <new> import (...)` block + a shim docstring),
assert every name the *rest of the tree* still imports from the old path is present
in the shim's import list. The A4 risk was exactly a missing private name
(`_EMBED_SOFT_CAP`, `_fmt_snapshot_value`) silently breaking a far-away importer that
`--collect-only` only catches at module import, not per-symbol. Worth having because
the fleet is doing many cogs→services moves this run and each one leaves a shim.

### ⟲ Previous-session review

The A8 baseview session (last merge before mine, #1084) did the right thing keeping
its change purely additive (justification comments, no behaviour change) — easy to
verify, zero blast radius. One workflow improvement it surfaces, relevant to this
whole fleet: the brief tells A4/A5 agents to "map every caller including lazy imports"
but doesn't warn that **the agent's git/file operations must target the assigned
worktree path, not the shared checkout** — I initially ran `git mv` against
`/home/user/superbot` (shared, on `main`) before noticing the Edit tool's
worktree-isolation error, and had to reset. A one-line "all file + git ops use your
worktree path `$WT`, never the shared checkout" note in the fleet brief's Rules of
engagement would save the next fleet run that round-trip.

## 📊 Telemetry

- Files moved: 2 (2,280 + 448 = 2,728 lines relocated via `git mv`, history preserved).
- Shims created: 2 (re-export only).
- Importers repointed: 3 (`views/diagnostic/`); 9 + 4 callers mapped, the rest left on
  the shims intentionally (preserves patch-site resolution).
- Layer warnings cleared: 2 (`views/diagnostic/hub_panel.py`, `platform_panel.py`).
- Tests: 278 targeted + 77 patch-site + 10749 collect-only — all green. 0 arch errors.
