# Health / diagnostics — planning & reference cluster

> **Status:** `reference` — index for the bot-awareness / health-diagnostics programme
> docs and the cross-subsystem consistency ledger. Area entry point lives in the folio:
> [`../subsystems/health-diagnostics.md`](../subsystems/health-diagnostics.md).
> Source code and merged PRs win over any plan here.

Consolidated out of the top-level `docs/` pile (owner decision Q-0010) so the
health/diagnostics material sits together behind the folio. Read the folio first; reach
for these on demand.

| Doc | What it is |
|---|---|
| [`bot-awareness-implementation-plan.md`](bot-awareness-implementation-plan.md) | The bot-awareness / health-diagnostics programme: execution authority + live delivery status (`living-ledger`; all 6 PRs shipped). |
| [`bot-awareness-diagnostics-plan.md`](bot-awareness-diagnostics-plan.md) | The Codex diagnostics map — context only (`reference`). |
| [`platform-consistency-ledger.md`](platform-consistency-ledger.md) | Cross-subsystem consistency / readiness ledger; verify each cell against source before treating it as work (`living-ledger`). |

The binding health surfaces live in code (`services/health_snapshot_service.py`,
`services/health_contracts.py`); the smoke expectations are pinned in
[`../smoke-test-checklist.md`](../smoke-test-checklist.md) (top-level).
