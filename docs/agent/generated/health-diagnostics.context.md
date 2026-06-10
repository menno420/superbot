# Agent Context Pack — Health / Diagnostics

> **Status:** `reference` — generated orientation aid (NOT source of truth).
> Generated: 2026-06-10 · Subsystem key: `health-diagnostics`

> **NOT SOURCE OF TRUTH.** This file is generated from `docs/agent/index.yml`.
> Canonical docs listed under *Binding docs* always win over this pack.
> Edit the index, then re-run `python3.10 tools/agent_context/build_pack.py`.

## Folio (start here)

[`docs/subsystems/health-diagnostics.md`](../../../docs/subsystems/health-diagnostics.md) — canonical area index, debug router, current state, next candidates.

## Binding docs (read before editing)

- docs/architecture.md
- docs/ownership.md
- docs/runtime_contracts.md

## Reference docs (consult on demand)

- docs/health/bot-awareness-implementation-plan.md
- docs/health/platform-consistency-ledger.md
- docs/smoke-test-checklist.md

## Likely source areas

- disbot/services/health_contracts.py
- disbot/services/health_snapshot_service.py
- disbot/services/health_findings_service.py
- disbot/services/diagnostics_service.py
- disbot/services/platform_consistency.py
- disbot/cogs/diagnostic_cog.py
- disbot/cogs/diagnostic/
- disbot/views/diagnostic/
- disbot/utils/db/health_findings.py
- disbot/migrations/057_operational_health_findings.sql

## Related subsystems

- `docs/agent/generated/ai.context.md`
- `docs/agent/generated/server-management.context.md`

## Do NOT create

These systems already exist — duplicating them is the main source of
architectural drift in this repo.

- A second diagnostics aggregator — compose existing providers in disbot/services/diagnostics_service.py
- A second health-findings store — reuse disbot/services/health_findings_service.py + disbot/utils/db/health_findings.py
- A health 'fix' inside the reporting layer — health shows the problem; fix it in the execution subsystem it reports on

## Active gates

- Health/diagnostics is a reporting layer. Root cause lives in the reported subsystem — do not 'fix' the health system for a failure it merely displays.

## Verification commands

Run these before pushing any change to this subsystem:

```
python3.10 scripts/check_quality.py --full
python3.10 scripts/check_architecture.py --mode strict
python3.10 -m pytest tests/unit/ -x -q -k health
```

---

*This pack is orientation only.  When this file and a canonical doc
disagree, the canonical doc wins.  When this file and source code
disagree, source code wins.*
