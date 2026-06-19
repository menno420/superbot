# 2026-06-19 — Fleet A2: move moderation _helpers from cogs into services/

> **Status:** `complete`

## Arc

Lane A unit **A2** of the [ultracode fleet brief](../docs/planning/ultracode-fleet-plan-2026-06-19.md) —
architecture boundary-debt burndown (ungated). move moderation _helpers from cogs into services/.

## Shipped (#1081)

- `cogs/moderation/_helpers.py` → **`services/moderation_helpers.py`** (old cog module deleted).
- Repointed importers: moderation_cog, views/moderation/modals; test patch-site updated in test_moderation_panel_embed.py.

Verified: `check_architecture --mode strict` exit 0 · `check_quality --check-only` clean ·
`pytest --collect-only` 10748 tests import-clean · targeted-domain tests pass.

> Completed by the fleet orchestrator after a mid-run container restart killed the per-unit
> agent before it flipped its card; the agent's implementation was intact in the worktree.

## 📤 Run report

- **Did:** move moderation _helpers from cogs into services/ (fleet A2). · **Outcome:** shipped
- **Shipped:** #1081
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** `none`
- **⚑ Owner manual steps:** `none`
- **⚑ Self-initiated:** A2 — docs/planning/ultracode-fleet-plan-2026-06-19.md (ungated arch boundary-debt)
- **↪ Next:** remaining fleet units.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 1 (#1081, on green) |
| CI-red rounds | 1 (born-red gate by design) |
| New ideas contributed | 0 (fleet completion run) |
| Ideas groomed | 0 |
