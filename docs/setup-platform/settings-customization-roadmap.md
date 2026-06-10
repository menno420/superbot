# Settings & Customization Manager — Roadmap

> **Status:** `reference` — architectural lane/reference roadmap. The
> S7–S12 planned/in-progress labels below are **not a verified current queue**; later
> source contains access, cleanup, setup, and provisioning surfaces that make the
> milestone sequence incomplete as status reporting. Start at
> `docs/subsystems/settings-bindings-provisioning.md` and verify source before work.
> **Sequencing superseded (2026-06-09):** the current settings *build order* is the
> source-verified Phase 0–6 roadmap in
> [`docs/planning/settings-cog-centralization-audit-2026-06-09.md`](../planning/settings-cog-centralization-audit-2026-06-09.md)
> §11 — Phases 0+1 **shipped 2026-06-09 (#640)**; **Phase 2 is next**, as Batch 4 of
> [`docs/planning/consolidated-implementation-plan-2026-06-10.md`](../planning/consolidated-implementation-plan-2026-06-10.md)
> *(pointer updated 2026-06-10; it previously said "queued as scoreboard Lane 7")*.
> This file stays the architecture reference for the three lanes + ownership invariants.

Architecture summary and 15-milestone implementation sequence for the **Global
Settings & Customization Manager**. Companion to
[`docs/setup-platform/settings-customization-command-map.md`](settings-customization-command-map.md)
(per-cog inventory) and
[`docs/setup-platform/resource-provisioning-overview.md`](resource-provisioning-overview.md)
(the RPM lane explainer).

## Three architectural lanes

1. **Settings lane** — scalar `guild_settings` rows declared by `SettingSpec`.
   Read path: `SettingsResolution`. Write path: `SettingsMutationPipeline`.
2. **Binding lane** — Discord resource pointers (channels, roles, categories,
   threads) declared by `BindingSpec` and stored in `subsystem_bindings`.
   Existing canonical writer: `BindingMutationPipeline`. Read path:
   per-subsystem services (e.g. `server_logging.resolve_log_channel`).
3. **Resource provisioning lane** — `ResourceProvisioningPipeline` owns the
   "select existing **or** create new" UX for any Discord resource. It calls
   `BindingMutationPipeline.set_binding(...)` at step 8 of its 11-step
   contract — it never writes `subsystem_bindings` itself.

## Ownership invariants

- Channel / role / category / thread values **must** be `BindingSpec`s, never
  scalar `SettingSpec`s. `SettingsResolution` is scalar-only.
- Each physical Discord resource is owned by **exactly one** subsystem's
  `BindingSpec`. Other subsystems that reference it (e.g. cleanup
  referencing the logging cleanup channel) must **deep-link**, not
  re-declare. Cleanup must not own a duplicate `cleanup_log_channel`
  binding — the logging subsystem owns `cleanup_channel`.
- CSV / list shapes (e.g. `cleanup.ignored_channels`) are **transitional
  only**. Long-term storage is typed list / policy tables.
- `CustomizationCatalogue` panel detection prefers authoritative sources
  (`command_surface_ledger`, explicit metadata, help hooks, known list,
  future `PanelRegistry`). Regex is fallback-only.
- **Discord resource creation is a separate concern from settings/bindings.**
  No cog or settings page may create channels/roles/categories directly — it
  must call `ResourceProvisioningPipeline`. Setup wizard (S12+) consumes
  provisioning packs, never creates resources directly.
- **Silent auto-create is forbidden** except where a setting explicitly opts
  in (e.g. `logging.auto_create_channels=true`) AND the operator has
  selected a provisioning policy ahead of time.

## Canonical mutation pipelines

| Pipeline | Owns writes to | Source-of-truth file |
|----------|----------------|----------------------|
| `BindingMutationPipeline` | `subsystem_bindings` | `disbot/services/binding_mutation.py` |
| `GovernanceMutationPipeline` | `subsystem_visibility`, `cleanup_policies` | `disbot/governance/writes.py` |
| `ParticipationMutationPipeline` | `user_*` tables | `disbot/services/participation_mutation.py` |
| `RolloutMutationPipeline` | `feature_flag_state`, `feature_flag_audit` | `disbot/services/rollout_mutation.py` |
| **`SettingsMutationPipeline`** (S4) | scalar `guild_settings` rows declared by `SettingSpec`; new `settings_mutation_audit` | **`disbot/services/settings_mutation.py`** |
| **`ResourceProvisioningPipeline`** (S4.5) | Discord resource creation (channels/roles/categories); new `resource_provisioning_audit`. **Always calls `BindingMutationPipeline.set_binding` to write the binding row** — never writes `subsystem_bindings` itself. | **`disbot/services/resource_provisioning.py`** |

UI **calls** these — never writes a row directly. Setup wizard **calls** them
via the Settings Manager cog and services — never directly.

## 15 roadmap milestones

12 numbered stages (S0–S12) plus two bridge milestones (S2.5, S4.5).

| Stage | Title | Status | Branch |
|-------|-------|--------|--------|
| S0    | Settings & Customization Command Map (docs-first) | landed | `claude/settings-customization-command-map` |
| S1    | Read-only SettingsRegistry | landed | `claude/settings-registry-readonly` |
| S2    | CustomizationCatalogue | landed | `claude/customization-catalogue` |
| S2.5  | ResourceProvisioningCatalogue | landed | `claude/resource-provisioning-catalogue` |
| S3    | SettingsResolution | landed | `claude/settings-resolution` |
| S4    | SettingsMutationPipeline | landed | `claude/settings-mutation-pipeline` |
| S4.5  | ResourceProvisioningPipeline | landed | `claude/resource-provisioning-pipeline` |
| S5    | Settings Manager Cog shell + read-only views + help hook | landed | `claude/settings-cog-readonly` |
| S6    | Scalar edit / reset flows | **landed** | `claude/settings-edit-flows` |
| S6.5  | Channel/role native selects + numeric presets (PR #7) | **landed** | `claude/settings-input-hints` |
| S7    | Logging customization with create/select channel flow | planned | `claude/settings-logging-customization` |
| S8    | Cleanup customization expansion | planned | `claude/settings-cleanup-customization` |
| S9    | Access policy manager | planned | `claude/settings-access-policy` |
| S10   | Subsystem setup packs / create-required-resources actions | planned | `claude/settings-subsystem-pages-*` and `claude/settings-setup-packs-*` |
| S11   | Help / Admin / Platform integration pass | planned | `claude/settings-discoverability-integration` |
| S12   | Setup wizard integration planning | in progress | `claude/setup-wizard-planning` |

**Feature-flag state.** The Settings Manager cog ships with the
``settings.manager_cog.enabled`` flag.  S5/S6/S7 landed with the flag
default OFF — operators opted in per guild.  PR #8 (after the
stabilization plan's S5-S7 close-out: XP/Economy pipeline migrations
+ channel/role/numeric-presets input modes) **flipped the default to
ON** so the hub is available by default once the cog loads.  The
kill-switch remains: operators flip it OFF either via the
``SUPERBOT_FF_SETTINGS__MANAGER_COG__ENABLED=off`` env override or
the (future) ``!platform flags`` command, and the cog returns the
disabled embed in that state.

## Execution workflow

- Every PR starts from a fresh `main`.
- One focused PR per milestone (S10 splits into per-subsystem and per-setup-pack
  sub-PRs).
- Each PR is default-OFF (feature flag) and single-`git revert` safe.
- Stop on failing tests, migration uncertainty, circular-import risk,
  architecture ambiguity, or unexpected behaviour changes.
- Never merge PRs without explicit operator approval.

## Dependency graph

```
  utils/subsystem_registry.SUBSYSTEMS
            │
            ▼
  core/runtime/subsystem_schema._REGISTRY ──┐──────────────────────┐
            │                                │                      │
            ▼                                ▼                      ▼
  core/runtime/settings_registry  ──→ services/customization     services/resource_provisioning
            │                          _catalogue (S2)             _catalogue (S2.5)
            ▼                                ▲                      │
  services/settings_resolution (S3)          │                      ▼
            │                                │                      services/resource_provisioning (S4.5)
            ▼                                │                      │  uses guild_resources.ensure_channel
  services/settings_mutation (S4)            │                      │  + new ensure_role / ensure_category
            │  (writes legacy KV; audits;    │                      │  writes binding via BindingMutationPipeline
            │   emits EVT_SETTING_CHANGED)   │                      │  audits; emits EVT_RESOURCE_PROVISIONED
            ▼                                                       ▼
  cogs/settings_cog + views/settings/  ←── consume all three pipelines via UI widgets

  binding_mutation ─── canonical writer for subsystem_bindings        (untouched; called by RPM step 8)
  governance/writes ── canonical writer for subsystem_visibility +
                         cleanup_policies                              (untouched)
  participation_mutation ─ canonical writer for user_*                 (untouched)
```

## Module map

```
disbot/
  core/runtime/
    settings_registry.py            ← S1
  services/
    customization_catalogue.py      ← S2
    resource_provisioning_catalogue.py  ← S2.5
    resource_provisioning.py        ← S4.5
    settings_resolution.py          ← S3
    settings_mutation.py            ← S4
  cogs/
    settings_cog.py                 ← S5
  views/settings/
    hub.py                          ← S5
    binding_select.py               ← S7 (reused across S10)
    channel_create_modal.py         ← S7
    logging_view.py                 ← S7
    cleanup_view.py                 ← S8
    access_view.py                  ← S9
    <subsystem>_view.py             ← S10 per-subsystem
  migrations/
    029_settings_mutation_audit.sql      ← S4
    030_resource_provisioning_audit.sql  ← S4.5
    031_cleanup_channel_policies.sql     ← S8 v2 (deferred)
    032_cleanup_prohibited_words.sql     ← S8 v3 (deferred)
    033_logging_routes.sql               ← future (NOT in v1 scope)
```

## See also

- [`docs/setup-platform/settings-customization-command-map.md`](settings-customization-command-map.md)
  — per-cog inventory (24-field template).
- [`docs/setup-platform/resource-provisioning-overview.md`](resource-provisioning-overview.md)
  — RPM lane (11-step contract, no-silent-auto-create rule,
  reserved `logging_routes` future model).
- [`docs/runtime_contracts.md`](../runtime_contracts.md) — existing mutation
  pipeline contracts.
- [`docs/archive/phase-2-completion-readiness.md`](../archive/phase-2-completion-readiness.md) —
  setup readiness blocker tracker.
