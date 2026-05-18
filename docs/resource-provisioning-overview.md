# Resource Provisioning Manager (RPM) — Overview

Companion doc for the Global Settings & Customization Manager. Explains the
**Resource Provisioning Lane** that runs parallel to settings and bindings.

Sister docs:
- [`docs/settings-customization-roadmap.md`](settings-customization-roadmap.md)
- [`docs/settings-customization-command-map.md`](settings-customization-command-map.md)


## Why a separate lane

`SettingsResolution` reads scalar settings. `BindingMutationPipeline` writes
the binding row that records "this subsystem points at channel X". Neither
service knows how to **create** a Discord resource in the first place — and
neither should grow that responsibility.

`ResourceProvisioningPipeline` is the single canonical place that:
1. Decides whether to create a new Discord resource or reuse an existing one.
2. Asks the operator to confirm.
3. Performs the Discord API call with the right name, category, and
   permission template.
4. Validates the result.
5. Writes the binding through `BindingMutationPipeline` (it never writes
   `subsystem_bindings` directly).
6. Audits the action.
7. Emits both `resource.provisioned` and `binding.changed` events.


## The 11-step `provision(...)` contract

Every Discord resource creation in the platform runs through these eleven
steps. The setup wizard (S12 and beyond) consumes this pipeline. No cog or
view bypasses it.

1. **Resolve** `ResourceRequirement` + `BindingSpec` from the
   `ProvisioningCatalogue.find(...)` lookup. Raise `UndeclaredResourceError`
   if missing.
2. **Validate actor / capability** — admin-tier today; future Phase 4.5
   uses `BindingSpec.capability_required`.
3. **Validate bot Discord permissions** for the requested resource kind
   (`manage_channels` for CHANNEL / CATEGORY, `manage_roles` for ROLE) via
   `guild.me.guild_permissions`. Insufficient permissions →
   `UnauthorizedProvisioningError` (audited as `permission_blocked`).
4. **Preview creation / reuse result** — build a `ProvisioningPreview`
   (already-bound? name collision? category exists?). Records non-fatal
   `warnings`.
5. **Require explicit confirmation** — `mode="create"` requires
   `confirmed=True`, otherwise raise `ProvisioningConfirmationRequired`. UI
   calls `preview()` first, shows the operator the planned action, then
   calls `provision(..., confirmed=True)`. The only exemption is a
   standing operator setting (e.g. `logging.auto_create_channels=true`)
   that counts as the standing confirmation — never undeclared.
6. **Create or reuse the resource** — `mode="create"`: dispatch by `kind`
   (channels via `core.runtime.guild_resources.ensure_channel`; roles /
   categories via new helpers added in S4.5 — `ensure_role`,
   `ensure_category`; threads deferred). `mode="use_existing"`: validate
   `existing_id` resolves on the guild and matches `kind`. Discord failure
   → `DiscordProvisioningFailedError` (audited as `discord_failed`).
7. **Validate the created resource** — re-resolve by ID; confirm `kind`
   match; check permissions against the template, log warnings without
   failing.
8. **Bind the resource through `BindingMutationPipeline.set_binding(...)`** —
   never write `subsystem_bindings` directly. `BindingMutationPipeline`
   emits `EVT_BINDING_CHANGED` as part of its own contract.
9. **Audit provisioning** — single row in `resource_provisioning_audit`
   (introduced by migration `030_resource_provisioning_audit.sql`). Columns:
   `id`, `mutation_id`, `guild_id`, `subsystem`, `binding_name`, `kind`,
   `mode`, `created`, `resource_id`, `outcome`
   (`success | permission_blocked | discord_failed | declined`),
   `actor_id`, `committed_at`. Every failure path also audits — never silent.
10. **Emit `EVT_RESOURCE_PROVISIONED`** (and via step 8 already
    `EVT_BINDING_CHANGED`) — best-effort, swallow-and-count per the
    participation-mutation pattern.
11. **Return** a typed `ProvisioningResult`.


## Hard rules

- **No silent auto-create.** Every `provision(mode="create")` call requires
  either an explicit operator confirmation in the UI (`confirmed=True`) or
  a standing setting the operator has flipped after seeing a provisioning
  policy (e.g. `logging.auto_create_channels=true`). Silent auto-create is
  forbidden — the pipeline must never create a Discord resource as an
  undeclared side effect. Enforced by `test_no_silent_auto_create.py`
  (S4.5 invariant).
- The pipeline is the **only** legitimate creator of Discord resources for
  subsystem use. No cog calls `guild.create_text_channel`,
  `guild.create_role`, `guild.create_category`, `ensure_channel`,
  `ensure_role`, or `ensure_category` directly. Enforced by the same
  invariant test.
- The pipeline does **not** touch scalar settings — those still go through
  `SettingsMutationPipeline`.
- The pipeline does **not** touch access policies — those still go through
  `GovernanceMutationPipeline`.
- Setup wizard (S12 and onward) **consumes** provisioning packs; it never
  owns or replicates creation logic.


## Reserved future model: `logging_routes`

Per-severity log routing is **not in v1 scope** of this roadmap. The table
shape is reserved for a future PR after S7 lands:

```sql
CREATE TABLE logging_routes (
    guild_id BIGINT NOT NULL,
    route_name TEXT NOT NULL CHECK (route_name IN ('moderation','cleanup','runtime','audit')),
    level TEXT NOT NULL CHECK (level IN ('debug','info','warning','error','critical')),
    channel_binding TEXT NOT NULL,   -- "logging.mod_channel" / "logging.cleanup_channel"
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    PRIMARY KEY (guild_id, route_name, level)
);
```

Reserved as migration `033_logging_routes.sql`. Until that future PR, v1
recognises only `mod_channel` and `cleanup_channel` bindings.


## Standard channel-name presets (logging consumer)

The logging customization (S7) seeds the `ChannelCreateModal` with the
following presets so operators don't have to hand-type the names:

- `mod-logs`
- `cleanup-logs`
- `log-channel-debug`
- `log-channel-info`
- `log-channel-warning`
- `log-channel-error`
- `log-channel-critical`

Operators may pick any preset, supply a custom name, or accept the suggestion
seeded from `ProvisioningHint.suggested_name`.


## See also

- [`docs/settings-customization-command-map.md`](settings-customization-command-map.md)
  — per-cog inventory; the `provisionable_resources` row on each cog comes
  from this overview's data model.
- [`docs/settings-customization-roadmap.md`](settings-customization-roadmap.md)
  — 15-milestone roadmap.
- `disbot/core/runtime/resource_specs.py` — `ResourceKind`,
  `ProvisioningPriority`, `ProvisioningHint`, `ResourceRequirement` data
  classes (already present).
- `disbot/services/binding_mutation.py` — the 7-step binding writer the RPM
  delegates to at step 8.
