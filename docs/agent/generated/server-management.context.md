# Agent Context Pack — Server Management

> **Status:** `reference` — generated orientation aid (NOT source of truth).
> Generated: 2026-06-08 · Subsystem key: `server-management`

> **NOT SOURCE OF TRUTH.** This file is generated from `docs/agent/index.yml`.
> Canonical docs listed under *Binding docs* always win over this pack.
> Edit the index, then re-run `python3.10 tools/agent_context/build_pack.py`.

## Folio (start here)

[`docs/subsystems/server-management.md`](../../../docs/subsystems/server-management.md) — canonical area index, debug router, current state, next candidates.

## Binding docs (read before editing)

- docs/architecture.md
- docs/ownership.md
- docs/runtime_contracts.md
- docs/capability-authority.md

## Reference docs (consult on demand)

- docs/planning/server-management-status-2026-06-05.md
- docs/setup-platform/resource-provisioning-overview.md

## Likely source areas

- disbot/cogs/channel_cog.py
- disbot/cogs/role_cog.py
- disbot/cogs/role/
- disbot/cogs/moderation_cog.py
- disbot/cogs/moderation/
- disbot/cogs/cleanup_cog.py
- disbot/cogs/cleanup/
- disbot/cogs/setup_cog.py
- disbot/cogs/setup/
- disbot/cogs/server_management_cog.py
- disbot/services/channel_lifecycle_service.py
- disbot/services/role_lifecycle_service.py
- disbot/services/moderation_service.py
- disbot/services/cleanup_profiles.py
- disbot/services/setup_diagnostics.py
- disbot/services/setup_operations.py
- disbot/services/setup_role_templates.py
- disbot/views/channels/
- disbot/views/roles/
- disbot/views/moderation/
- disbot/views/setup/
- disbot/views/server_management/

## Related subsystems

- `docs/agent/generated/health-diagnostics.context.md`
- `docs/agent/generated/settings-bindings-provisioning.context.md`

## Do NOT create

These systems already exist — duplicating them is the main source of
architectural drift in this repo.

- A new setup op-kind without updating all three places: disbot/services/setup_operations.py _KNOWN_KINDS + disbot/utils/db/setup_draft.py _KNOWN_OP_KINDS + a migration widening the setup_draft_operations.op_kind CHECK constraint
- A second mutation path for role thresholds — route through disbot/services/role_automation.py set_{time,xp}_threshold
- A direct DB write from a cog or view — route through the domain mutation service
- A second diagnostics composer — reuse disbot/services/setup_diagnostics.py (PR12 canonical composer)

## Active gates

- New setup op-kind is a three-place contract (dispatcher + DB gate + migration CHECK). See server-management folio debug router.
- PR13 AI generation layer remains gated by the AI-expansion gate in docs/current-state.md.

## Verification commands

Run these before pushing any change to this subsystem:

```
python3.10 scripts/check_quality.py --full
python3.10 scripts/check_architecture.py --mode strict
python3.10 -m pytest tests/unit/ -x -q -k server_management or setup
```

---

*This pack is orientation only.  When this file and a canonical doc
disagree, the canonical doc wins.  When this file and source code
disagree, source code wins.*
