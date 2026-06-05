# SuperBot — Service Ownership Quick Reference

> **Status:** reference (not binding). This is a quick-lookup companion to
> `docs/ownership.md`. When this table and `docs/ownership.md` disagree,
> **`docs/ownership.md` is authoritative.** Update this table when
> `docs/ownership.md` changes, not the other way around.
>
> **Purpose:** Give an agent or contributor a single-glance answer to "how must
> I route this mutation?" without reading the full binding doc. Use this to
> pick the write path; use `docs/ownership.md` to understand the contract.

---

## How to use

1. Find the domain row for the state you want to change.
2. Confirm your caller is in the "Allowed callers" list.
3. Call the documented write path — nothing else.
4. Verify the required side effects happen automatically through that path.
5. If your caller is not listed, route through an allowed caller or propose a
   contract change in `docs/ownership.md` first.

---

## Mutation ownership matrix

| Domain | Owner module | Allowed callers | Write path | Audit / event / cache side effects | Documented exceptions |
|---|---|---|---|---|---|
| **Economy** | `services/economy_service.py` | cogs, views, setup pipeline | `credit()` / `debit()` / `transfer()` / `bet_and_settle()` / `refund()` | `economy_audit_log` row (same txn) + `economy.balance_changed` event | none — INV-F (AST test) enforces this |
| **XP** | `services/xp_service.py` | cogs, listeners, jobs | `award()` / `reset()` | `xp.awarded` / `xp.level_up` / `xp.reset` events; level recalculation included | none — INV-G (AST test) enforces this |
| **Governance** | `governance/writes.py:GovernanceMutationPipeline` | governance cog, admin views, setup pipeline | pipeline methods (`set_visibility`, `set_cleanup_policy_for_scope`) | `governance_audit_log` row + 3 `governance.*` events + `guild_config` cache invalidate | `governance/execution.py:_audit_internal_bypass` — append-only audit row for internal bypasses; documented in `docs/ownership.md` |
| **Moderation** | `services/moderation_service.py` | mod cog, modals, auto-mod stages | `warn()` / `timeout()` / `kick()` / `ban()` / `unban()` / `clear_warnings()` / `auto_delete()` | three signals per action: `mod_logs` row (authoritative history) + best-effort `audit.action_recorded` companion + `moderation.action_taken` event (companion + event share a `mutation_id`). Clear-warnings logs the token `clearwarnings`. | none — INV pinned by `test_no_direct_moderation_writes.py` |
| **Channel lifecycle** | `services/channel_lifecycle_service.py` | channel cog (typed commands) | `ChannelLifecycleService().apply(ChannelLifecycleRequest(...))` — `rename` / `move` / `delete` only | best-effort `audit.action_recorded` companion + `channel.lifecycle_changed` event (shared `mutation_id`); no dedicated audit table | create/clone/overwrites/reorder not yet routed — pinned (`.delete`/`.edit`) by `test_no_direct_channel_mutations.py` |
| **Role lifecycle** | `services/role_lifecycle_service.py` | role cog + `views/roles/*` | `RoleLifecycleService().apply(RoleLifecycleRequest(...))` — `create` / `edit` / `delete` | best-effort `audit.action_recorded` companion + `role.lifecycle_changed` event (shared `mutation_id`); manageability via `utils.role_feasibility` | member assign/remove not owned — pinned (create/`role.edit`/`role.delete`) by `test_no_direct_role_mutations.py` |
| **Settings** | `services/settings_mutation.py:SettingsMutationPipeline` | setup pipeline, settings cog/views | `set_value()` | `settings_audit` row + `audit.action_recorded` event + `guild_config` cache invalidate | none |
| **Bindings** | `services/binding_mutation.py:BindingMutationPipeline` | setup pipeline, binding cog/views | `set_binding()` / `clear_binding()` | `binding_audit_log` row + `audit.action_recorded` event + `guild_config` cache invalidate | none |
| **Resources** | `services/resource_provisioning.py:ResourceProvisioningPipeline` | setup pipeline, admin, `cogs/logging/provision_view.py` | `provision(confirmed=True)` | `resource_provisioning_audit` row + `EVT_RESOURCE_PROVISIONED` event | none — RC-9: production callers exist (logging channel provisioning previews + commits here). Manual channel-management creation is a separate server-management follow-up. |
| **Game state** | `services/game_state_service.py` | game cogs, game views | `save()` / `load()` / `clear()` / `list_active_for_subsystem()` | none — checkpoint frequency makes audit rows noisy; see ADR-002 | none |
| **Setup session** | `services/setup_session.py` | setup cog, launcher view | `start_session()` / `mark_complete()` / `dismiss()` | best-effort `audit.action_recorded` event after DB write; failure is logged and swallowed | none |
| **Flags / rollout** | `services/rollout_mutation.py:RolloutMutationPipeline` | operator scripts (Phase 3 only — no Discord-facing UI yet) | `set_flag_state()` / `advance_rollout()` / `set_environment_tier()` | `feature_flag_audit` row + `EVT_FEATURE_FLAGS_CHANGED` / `EVT_ROLLOUT_ADVANCED` / `EVT_ENVIRONMENT_TIER_CHANGED` events + flag cache invalidate | none |
| **Participation** | `services/participation_mutation.py:ParticipationMutationPipeline` | cogs, views (self-write only — actor must equal user) | `set_participation()` / `set_subscription()` / `set_preference()` / `set_visibility()` | per-table audit rows + `audit.action_recorded` + synchronous user-config cache invalidate (inline, before event) + domain events | none |
| **Automation rules** | `services/automation_mutation.py:AutomationMutationPipeline` | admin cog/views, setup pipeline | `create_rule()` / `set_enabled()` / `delete_rule()` | config validation + `EVT_AUTOMATION_RULE_CHANGED` event | none |
| **Inventory** | `utils/db/inventory.py` | `cogs/inventory_cog.py` only | direct `utils/db/inventory.*` calls | none — simple CRUD, no cross-subsystem impact | intentional — documented in `docs/ownership.md` subsystem table |
| **Counting / Chain / Mining / Deathmatch** | `utils/db/games/<sub>.py` per subsystem | the subsystem's own cog only | direct `utils/db/games/<sub>.*` calls | none — single-subsystem state, simple CRUD | intentional — documented in `docs/ownership.md` subsystem table |

---

## Platform-owned surfaces

These are not domain mutations — they are infrastructure writes owned by
`core/runtime/` or `governance/`. Do not call them from cogs or views directly.

| Surface | Owner | Allowed writers | Write method |
|---|---|---|---|
| `panel_anchors` | `core.runtime.message_anchor_manager` | panel manager only | `upsert_panel_anchor` / `mark_panel_anchor_stale` |
| `runtime_sessions` | `core.runtime.session_manager` | session manager only | session lifecycle methods |
| `runtime_session_state` | `core.runtime.state_store` | state store only | `set` / `set_many` / `delete` / `invalidate_guild_state` |
| `game_state` | `services/game_state_service.py` | game cogs, game views | `save` / `load` / `clear` |
| `economy_audit_log` | `services/economy_service.py` | service only (append-only) | inside economy service methods |
| `governance_audit_log` | `GovernanceMutationPipeline` | pipeline only (append-only) | `_audit_internal_bypass` carve-out documented |

---

## What "correct" looks like end-to-end

```
cog / view / setup pipeline
  │
  └─▶  service / pipeline
          ├─ 1. validate inputs
          ├─ 2. open transaction (if multi-row)
          ├─ 3. apply DB write
          ├─ 4. append audit row (same transaction)
          └─ 5. after commit: invalidate cache → emit catalogued event
```

The side effects in step 5 are automatic when you use the service/pipeline.
Callers do not need to invalidate caches or emit events themselves.

---

## Adding a new mutation domain

1. Add a row to `docs/ownership.md`'s **Service ownership** and **Subsystem
   ownership** tables — that is the binding contract.
2. Add a row to this table as a convenience.
3. Add the new catalogued event to `core/events_catalogue.KNOWN_EVENTS` and to
   `docs/ownership.md`'s event table.
4. Add an AST-enforcement test in `tests/unit/invariants/` if the blocklist
   should be machine-checked (follow the INV-F / INV-G pattern).
