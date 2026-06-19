# 2026-06-19 — Fleet A6: move governance exception types into utils/governance_exceptions

> **Status:** `complete`

## Arc

Lane A unit **A6** of the [ultracode fleet brief](../docs/planning/ultracode-fleet-plan-2026-06-19.md) —
architecture boundary-debt burndown (ungated). move governance exception types into utils/governance_exceptions.

## Shipped (#1083)

- New **`utils/governance_exceptions.py`** holds the exception classes; `governance/__init__.py` + `governance/writes.py` import from utils so the governance layer no longer imports `services`.
- `services/governance_exceptions.py` keeps a back-compat re-export so external importers resolve unchanged.

Verified: `check_architecture --mode strict` exit 0 · `check_quality --check-only` clean ·
`pytest --collect-only` 10748 tests import-clean · targeted-domain tests pass.

> Completed by the fleet orchestrator after a mid-run container restart killed the per-unit
> agent before it flipped its card; the agent's implementation was intact in the worktree.

## 📤 Run report

- **Did:** move governance exception types into utils/governance_exceptions (fleet A6). · **Outcome:** shipped
- **Shipped:** #1083
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** `none`
- **⚑ Owner manual steps:** `none`
- **⚑ Self-initiated:** A6 — docs/planning/ultracode-fleet-plan-2026-06-19.md (ungated arch boundary-debt)
- **↪ Next:** remaining fleet units.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 1 (#1083, on green) |
| CI-red rounds | 1 (born-red gate by design) |
| New ideas contributed | 0 (fleet completion run) |
| Ideas groomed | 0 |
