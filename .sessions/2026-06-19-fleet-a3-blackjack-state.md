# 2026-06-19 — Fleet A3: move blackjack state/persistence into services/, break the actions↔_state cycle

> **Status:** `complete`

## Arc

Lane A unit **A3** of the [ultracode fleet brief](../docs/planning/ultracode-fleet-plan-2026-06-19.md) —
architecture boundary-debt burndown (ungated). move blackjack state/persistence into services/, break the actions↔_state cycle.

## Shipped (#1092)

- `cogs/blackjack/_state.py` → **`services/blackjack_state.py`**, `cogs/blackjack/_persistence.py` → **`services/blackjack_persistence.py`**.
- Repointed `views/blackjack/*` imports to the new `services.` locations (clears `views→cogs.blackjack._state/_persistence`); cog keeps back-compat re-exports so patch sites stay valid.
- Resolves the intra-package `cogs.blackjack ↔ views.blackjack` import cycle.

Verified: `check_architecture --mode strict` exit 0 · `check_quality --check-only` clean ·
`pytest --collect-only` 10748 tests import-clean · targeted-domain tests pass.

> Completed by the fleet orchestrator after a mid-run container restart killed the per-unit
> agent before it flipped its card; the agent's implementation was intact in the worktree.

## 📤 Run report

- **Did:** move blackjack state/persistence into services/, break the actions↔_state cycle (fleet A3). · **Outcome:** shipped
- **Shipped:** #1092
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** `none`
- **⚑ Owner manual steps:** `none`
- **⚑ Self-initiated:** A3 — docs/planning/ultracode-fleet-plan-2026-06-19.md (ungated arch boundary-debt)
- **↪ Next:** remaining fleet units.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 1 (#1092, on green) |
| CI-red rounds | 1 (born-red gate by design) |
| New ideas contributed | 0 (fleet completion run) |
| Ideas groomed | 0 |
