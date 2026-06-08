# 2026-06-08 — P1A: Access Map projection service

**Task:** Continue the Adaptive Setup/Access platform onto the next lane after the
Q-0026 + P0B foundation merged (#588). Per the planning doc §15, that lane is **P1A —
the side-effect-free Access Map projection service** (§16 contract).

**Branch:** `claude/access-map-projection-p1a`, stacked on the merged #588 commit (so it
builds on the snake_case keys, not the drift). #588 merged mid-session → this branch's
diff against main is clean P1A-only.

## Shipped

- **`disbot/services/access_projection.py`** — a read-only composed Access Map read model.
  For a `(feature, context)` pair it answers "allowed here, and if not, why?" by
  **composing the existing policy owners** in a fixed precedence and short-circuiting on
  the first deny. It owns **no policy** (no second permission system — §16.7); every
  `allow`/`deny` traces to an existing owner via `source_chain`.
  - Axes: **command access** (`command_access.resolve_command_access` — lifecycle/DM/
    bootstrap/channel), **routing** (`command_routing.is_cog_enabled`, keyed on the
    subsystem key), **governance** (`governance.get_visible_subsystems` — the *same* read
    the existing `AccessExplorerView` uses), **availability** (future — `skipped`), **help
    visibility** (ledger `is_hidden_from_help` — *informational, never gates*), **preference**
    (future).
  - Reuses `command_access.DecisionReason` codes verbatim for the command-access axis;
    the small extra code set (`routing_disabled`, `subsystem_hidden`, `availability_window`)
    + user-safe `safe_text` live in a static `_SAFE_TEXT` table (no context interpolation →
    leak-free by construction).
  - Public surface: `AccessContext`, `AccessDecision`, `LockedReason`, `AxisOutcome`,
    `FeatureEntry`, `feature_inventory()`, `resolve_feature_access()`, `project_access_map()`.
  - `unknown` is honest: an unresolved gating axis yields `effective="unknown"`, never a
    false `allow`.
- **`tests/unit/services/test_access_projection.py`** — 19 tests: feature inventory,
  per-axis precedence/short-circuit, bootstrap-bypass, unknown handling, help-axis-
  non-gating, reason-safety (no id/role/tier leak), and the §16.7 negative-architecture
  guardrails (no mutation/UI/Discord imports; only read resolvers referenced).

## Verification

- `python3.10 -m pytest tests/unit/services/test_access_projection.py` → **19 passed**.
- `python3.10 scripts/check_quality.py --full` → green (black/isort/ruff + mypy + full
  pytest; **8085 passed, 3 skipped** — DB-backed tests ran because Postgres was up).
- `python3.10 -m mypy disbot/services/access_projection.py` → no issues.
- `python3.10 scripts/check_architecture.py --mode strict` → 0 errors, no findings on the
  new module (services-layer; all cross-package imports function-local).
- Import smoke: 6 axes, 28 features, no cycle.

## Design decisions

- **Compose, never reimplement.** The governance axis calls `get_visible_subsystems`
  (the existing owner). Discovering `views/access/explorer.py::AccessExplorerView` — a
  governance-axis-only diagnostic — confirmed the projection is the *composed superset* a
  future P1C panel renders, not a competitor; documented in planning §16 status.
- **`skipped` vs `unknown`.** Future axes (availability, preference) are `skipped`
  (deliberately inert, never gate). A resolver that errors or lacks inputs is `unknown`
  (blocks a confident `allow`). Distinct states so the chain is honest about *why*.
- **Help axis is recorded but non-gating** — it can never flip an execution `allow` to a
  denied result (pinned by `test_help_hidden_does_not_flip_allow_to_deny`).
- **No diagnostics provider / boot import yet.** The projection is per-request, and nothing
  imports it until P1C; wiring a boot import for an unused provider would be premature.

## Next (ordered)

1. **P1B** — drift providers (`identity_mismatch`, `help_advertises_locked`,
   `routing_access_conflict`, `configured_resource_missing`) + locked-reason denial
   integration, in `setup_diagnostics`, built on `resolve_feature_access`.
2. **P1C** — read-only Access Map + staff-only Help Preview panels using P1A; link from
   Server Management / Settings (no new command names — Q-0032 safe default).
3. **P0C** — normalize the role-threshold direct-write drift onto an audited
   `role_automation` seam (planning §16.5) before any profile/routine targets thresholds.

## Context delta

- **Needed but not pointed to:** the existing `views/access/explorer.py::AccessExplorerView`
  — a read-only *governance-axis* explorer that the orientation/folios don't mention. It's
  the closest prior art to the Access Map and would be easy to accidentally duplicate; the
  projection deliberately reuses the same `get_visible_subsystems` read. Also that the
  **routing axis keys on the subsystem key** (`cog_name="games"`), not the cog class name —
  only discoverable by reading `cog_routing_profiles.py`.
- **Pointed to but didn't need:** the runtime_contracts / capability-authority deep docs —
  P1A is a pure read composition that adds no lifecycle or authority *policy*, so those
  contracts informed but didn't gate the code (the existing resolvers already encode them).
- **Discovered by hand:** that `command_access.resolve_command_access` already folds axes
  1+2 (lifecycle + DM + bootstrap + channel) into one decision with a `DecisionSource` that
  distinguishes them — so the projection treats command-access as a single axis whose
  `AxisOutcome.detail` carries the source, rather than re-deriving bootstrap separately.
  Captured in the module docstring + planning §16.2.
