# Agent Context Pack — AI / Setup Advisor

> **Status:** `reference` — generated orientation aid (NOT source of truth).
> Generated: 2026-06-08 · Subsystem key: `ai`

> **NOT SOURCE OF TRUTH.** This file is generated from `docs/agent/index.yml`.
> Canonical docs listed under *Binding docs* always win over this pack.
> Edit the index, then re-run `python3.10 tools/agent_context/build_pack.py`.

## Folio (start here)

[`docs/subsystems/ai.md`](../../../docs/subsystems/ai.md) — canonical area index, debug router, current state, next candidates.

## Binding docs (read before editing)

- docs/architecture.md
- docs/ownership.md
- docs/runtime_contracts.md
- docs/ai-config-ownership.md

## Reference docs (consult on demand)

- docs/planning/ai-roadmap-2026-06-07.md
- docs/ai/ai-complex-request-tool-orchestration-plan.md
- docs/ai/ai-service-integration-map.md

## Likely source areas

- disbot/cogs/ai_cog.py
- disbot/cogs/ai/
- disbot/core/runtime/ai/
- disbot/services/ai_policy_mutation.py
- disbot/services/ai_config_projection_service.py
- disbot/services/ai_gateway.py
- disbot/services/ai_tools.py
- disbot/utils/settings_keys/ai.py

## Related subsystems

- `docs/agent/generated/health-diagnostics.context.md`
- `docs/agent/generated/settings-bindings-provisioning.context.md`

## Do NOT create

These systems already exist — duplicating them is the main source of
architectural drift in this repo.

- A second natural-language policy resolver
- A second AI tool registry — reuse disbot/services/ai_tools.py
- A second diagnostics aggregator — reuse disbot/services/diagnostics_service.py
- A direct DB scanner inside ai_cog.py
- An AI mutation path that bypasses disbot/services/ai_policy_mutation.py

## Active gates

- AI feature expansion gated on: bot-wide stability + provider/provenance checks + caching/source-health clarity + AI behavior/config correctness. See docs/current-state.md 'Gates / blocked work'.
- First Opus target = lock orchestration foundation (AR-10, owner decision). Approve docs/ai/ai-complex-request-tool-orchestration-plan.md before net-new tools.

## Verification commands

Run these before pushing any change to this subsystem:

```
python3.10 scripts/check_quality.py --full
python3.10 scripts/check_architecture.py --mode strict
python3.10 -m pytest tests/unit/ -x -q -k ai
```

---

*This pack is orientation only.  When this file and a canonical doc
disagree, the canonical doc wins.  When this file and source code
disagree, source code wins.*
