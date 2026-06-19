# 2026-06-19 — Fleet A7: wrap raw SQL in utils/db helpers

> **Status:** `complete`

## Arc

Lane A unit **A7** of the [ultracode fleet brief](../docs/planning/ultracode-fleet-plan-2026-06-19.md):
move the raw `pool.execute()` / `conn.execute()` / `fetch*` calls in
`services/game_state_service.py` and `services/platform_consistency.py` back behind the
`utils.db.*` seam, so the two services stop reaching past `utils/db/` for raw SQL
(13 of the 18 `raw_sql` architecture warnings).

## Shipped

- **New `utils/db` helpers** — `utils/db/games/game_state.py` and
  `utils/db/platform_consistency.py` — each wrapping the previously-inline SQL in named,
  typed functions. The two services now call those helpers instead of touching the pool
  directly. Behaviour-preserving (same queries, same results).
- **`raw_sql` architecture warnings 18 → 5** (the remaining 5 live in
  `automation_scheduler.py` / `binding_backfill.py`, out of this unit's scope).
- `check_architecture --mode strict` exit 0 · `check_quality --check-only` clean ·
  `pytest --collect-only` 10748 tests import-clean · 81 targeted game_state /
  platform_consistency tests pass.

## ⟲ Previous-session review (Q-0102)

This unit was completed by the fleet **orchestrator** after a mid-run container restart
killed the per-unit agent before it could flip its card. The agent had done the
implementation correctly but left it uncommitted and offloaded the full test suite to a
background process, then came to rest. **System improvement surfaced:** a fleet agent
should *commit its work before* kicking off a long background verification, so a restart
never strands finished work in an uncommitted worktree — and the orchestrator should tell
sub-agents to validate with `pytest --collect-only` + targeted tests rather than 14
concurrent full suites (the likely cause of the resource-exhaustion restart).

## 📤 Run report

- **Did:** wrapped the 13 raw-SQL calls in `game_state_service` + `platform_consistency`
  behind new `utils/db` helpers (fleet unit A7). · **Outcome:** shipped
- **Shipped:** #1087 — 2 new `utils/db` helper modules; 2 services rewired; `raw_sql` 18 → 5.
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** `none`
- **⚑ Owner manual steps:** `none`
- **⚑ Self-initiated:** A7 — docs/planning/ultracode-fleet-plan-2026-06-19.md (architecture
  boundary-debt burndown, ungated)
- **↪ Next:** remaining fleet units; the 5 residual `raw_sql` warns in
  `automation_scheduler` / `binding_backfill` are a future slice.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 1 (#1087, on green) |
| CI-red rounds | 1 (born-red session gate by design) |
| `raw_sql` arch warns | 18 → 5 |
| New ideas contributed | 0 (fleet completion run) |
| Ideas groomed | 0 |
