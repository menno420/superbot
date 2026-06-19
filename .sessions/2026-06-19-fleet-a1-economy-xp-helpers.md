# 2026-06-19 — Fleet A1: move economy/xp _helpers from cogs into services/

> **Status:** `complete`

## Arc

Lane A unit **A1** of the [ultracode fleet brief](../docs/planning/ultracode-fleet-plan-2026-06-19.md) —
architecture boundary-debt burndown (ungated). move economy/xp _helpers from cogs into services/.

## Shipped (#1080)

- `cogs/economy/_helpers.py` → **`services/economy_helpers.py`**, `cogs/xp/_helpers.py` → **`services/xp_helpers.py`** (git renames; old cog modules deleted).
- Repointed importers: economy_cog, xp_cog, views/economy/{main,shop,work}_panel, views/xp/{config,main}_panel, views/xp/rank_view.
- **rank_view.py A8 collision resolved here:** kept A1's `services.xp_helpers` import fix and folded in A8's `_RankView` justification comment (A8 drops the file).

Verified: `check_architecture --mode strict` exit 0 · `check_quality --check-only` clean ·
`pytest --collect-only` 10748 tests import-clean · targeted-domain tests pass.

> Completed by the fleet orchestrator after a mid-run container restart killed the per-unit
> agent before it flipped its card; the agent's implementation was intact in the worktree.

## 📤 Run report

- **Did:** move economy/xp _helpers from cogs into services/ (fleet A1). · **Outcome:** shipped
- **Shipped:** #1080
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** `none`
- **⚑ Owner manual steps:** `none`
- **⚑ Self-initiated:** A1 — docs/planning/ultracode-fleet-plan-2026-06-19.md (ungated arch boundary-debt)
- **↪ Next:** remaining fleet units.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 1 (#1080, on green) |
| CI-red rounds | 1 (born-red gate by design) |
| New ideas contributed | 0 (fleet completion run) |
| Ideas groomed | 0 |
