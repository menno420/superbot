# Agent Context Pack — Settings / Bindings / Provisioning

> **Status:** `reference` — generated orientation aid (NOT source of truth).
> Generated: 2026-06-10 · Subsystem key: `settings-bindings-provisioning`

> **NOT SOURCE OF TRUTH.** This file is generated from `docs/agent/index.yml`.
> Canonical docs listed under *Binding docs* always win over this pack.
> Edit the index, then re-run `python3.10 tools/agent_context/build_pack.py`.

## Folio (start here)

[`docs/subsystems/settings-bindings-provisioning.md`](../../../docs/subsystems/settings-bindings-provisioning.md) — canonical area index, debug router, current state, next candidates.

## Binding docs (read before editing)

- docs/architecture.md
- docs/ownership.md
- docs/runtime_contracts.md
- docs/capability-authority.md

## Reference docs (consult on demand)

- docs/setup-platform/settings-customization-roadmap.md
- docs/setup-platform/settings-customization-command-map.md
- docs/setup-platform/resource-provisioning-overview.md
- docs/health/platform-consistency-ledger.md
- docs/building-roadmap/config-input-standard.md

## Likely source areas

- disbot/core/runtime/settings_registry.py
- disbot/core/runtime/bindings.py
- disbot/core/runtime/subsystem_capabilities.py
- disbot/services/settings_mutation.py
- disbot/services/settings_resolution.py
- disbot/services/binding_mutation.py
- disbot/services/resource_provisioning.py
- disbot/core/resources/
- disbot/services/governance_service.py
- disbot/views/settings/
- disbot/views/setup/

## Related subsystems

- `docs/agent/generated/server-management.context.md`
- `docs/agent/generated/ai.context.md`
- `docs/agent/generated/health-diagnostics.context.md`

## Do NOT create

These systems already exist — duplicating them is the main source of
architectural drift in this repo.

- A setting for a Discord-resource pointer — that is a binding, not a setting
- A resource-provisioning write that bypasses preview + confirmation + audit
- A panel callback that does not re-check authority/capability at execution time
- A direct DB write to settings/bindings from a cog or view — route through the mutation service

## Active gates

- Direct vs. draft lane choice is canonical in docs/ownership.md 'Direct vs. draft mutation lanes'.
- Every panel callback must re-check authority/capability at execution time (opening a panel is not authorization).

## Verification commands

Run these before pushing any change to this subsystem:

```
python3.10 scripts/check_quality.py --full
python3.10 scripts/check_architecture.py --mode strict
python3.10 -m pytest tests/unit/ -x -q -k settings or binding
```

---

*This pack is orientation only.  When this file and a canonical doc
disagree, the canonical doc wins.  When this file and source code
disagree, source code wins.*
