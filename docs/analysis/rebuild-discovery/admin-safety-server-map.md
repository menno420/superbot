# Rebuild discovery map — admin, safety, server management, setup, logging

> **Status:** `historical` — rebuild discovery audit report; source-grounded snapshot for future planning.
>
> Scope: PART 2 of 4 for a possible future clean SuperBot rebuild. This report is discovery only: it does **not** approve a rebuild, implement changes, or change production state.

## 1. Executive summary

### Best server-owner/admin ideas to preserve

- **Discord-first server-management hub.** `disbot/cogs/server_management_cog.py` routes `!server` / `!servermanage` / `!serverpanel` into `views.server_management.hub.ServerManagementHubView`, which centralizes setup, settings, roles, channels, moderation, logging, diagnostics, help preview, and access-map routes instead of leaving server owners to memorize commands.
- **Setup as a draft/apply workflow, not direct mutation.** `services.setup_session`, `services.setup_draft`, `services.setup_operations`, and `views.setup.final_review` separate session state, draft operations, review, and apply. This is one of the strongest rebuild patterns.
- **Settings / bindings / provisioning separation.** Scalar settings go through `SettingsMutationPipeline`; bindings go through `BindingMutationPipeline`; create-or-bind resource work goes through `ResourceProvisioningPipeline`. A fresh repo should keep these as separate primitives rather than one broad “configure server” service.
- **Lifecycle services with preview/result objects.** `ChannelLifecycleService` and `RoleLifecycleService` already model preview/confirmation/result for Discord resource changes. This is the right foundation for destructive or hierarchy-sensitive operations.
- **Unified moderation audit seam.** Manual moderation, cleanup auto-delete, automod, counting/chain/image-mod stages, and the message pipeline converge on `services.moderation_service` / `services.server_logging.EVT_MOD_ACTION` so admin-visible history can be consistent.
- **Read-only diagnostic/platform hubs.** `diagnostic_cog`, `views.diagnostic.hub_panel`, and `views.diagnostic.platform_panel` make runtime facts discoverable without mutating state; the flag manager is the explicit exception and routes through the rollout pipeline.
- **Passive server event logging with per-category opt-in.** The logging subsystem keeps fresh guild behavior unchanged and lets owners opt into message/member/role/moderation/channel/server/voice categories.

### Best safety/audit/governance ideas

- **Capability-native authority at mutation seams.** `docs/capability-authority.md` and `governance.capability.actor_holds_capability` define the intended central check for settings/bindings/provisioning.
- **Callbacks must re-check authority.** `BaseView` invoker locking is not authority; mutating panels need a callback-level capability/admin check if reachable from help or hubs.
- **No silent auto-create.** Provisioning requires explicit confirmation or an operator standing setting, then audits success and failure.
- **Typed lifecycle outcomes.** `LifecyclePreview`, `LifecycleResult`, `StepResult`, `outcome`, and reversibility vocabulary provide a reusable safety grammar.
- **Fail-safe diagnostics/logging.** Event emitters and log senders are best-effort; failures should be counted/logged without breaking user commands.

### Highest-risk patterns to avoid in a fresh repo

- Scattered `has_permissions(administrator=True)`, `guild_permissions.*`, owner checks, and raw callback assumptions instead of one `AdminActionSpec`/`CapabilitySpec` resolver.
- Direct Discord mutations from cogs/views (`guild.create_*`, `channel.delete`, `member.add_roles`, etc.) instead of domain services.
- Direct legacy KV writes for settings and direct `subsystem_bindings` writes, bypassing audit/event/cache invalidation.
- Duplicate setup paths (`quicksetup`, setup wizard, hub panels, per-cog commands) that can drift.
- Inconsistent destructive confirmations: some lifecycle paths preview and confirm; older panels still do command-style one-shot deletes.
- One-off selectors/modals rather than shared resource picker, settings editor, confirmation, and create-or-bind primitives.

### Future admin UX should centralize around

A single **Server Management / Setup Control Center** with shared primitives: `SettingsPanelSpec`, `BindingSpec`, `ResourceMutationSpec`, `ConfirmationSpec`, `LifecycleResult`, `AuditEventSpec`, and `ServerEventRouteSpec`. Every admin panel should be a projection over these specs, not a bespoke command implementation.

## 2. Source route and verification

### Binding/current-state docs read

Read live repo docs requested by the prompt:

- `.claude/CLAUDE.md`
- `docs/collaboration-model.md`
- `docs/current-state.md`
- `docs/current-state/S1-bot.md`
- `docs/current-state/S5-ops.md`
- `docs/AGENT_ORIENTATION.md`
- `docs/architecture.md`
- `docs/ownership.md`
- `docs/runtime_contracts.md`
- `docs/repo-navigation-map.md`
- `docs/repo-review-map.md`
- `docs/ultracode/README.md`
- `docs/subsystems/server-management.md`
- `docs/subsystems/settings-bindings-provisioning.md`
- `docs/server-logging.md`
- `docs/setup-platform/resource-provisioning-overview.md`
- `docs/capability-authority.md`

### Source roots inspected

- Cogs: `admin_cog.py`, `diagnostic_cog.py`, `health_maintenance_cog.py`, `ux_lab_cog.py`, `server_management_cog.py`, `setup_cog.py`, `bootstrap_access_cog.py`, `moderation_cog.py`, `cleanup_cog.py`, `automod_cog.py`, `image_moderation_cog.py`, `security_cog.py`, `logging_cog.py`, `welcome_cog.py`, `counters_cog.py`, `channel_cog.py`, `role_cog.py`, `proof_channel_cog.py`, `ticket_cog.py`, plus `cogs/*/schemas.py` and listeners.
- Views: `views/diagnostic`, `views/server_management`, `views/setup`, `views/moderation`, `views/cleanup`, `views/channels`, `views/roles`, `views/tickets`, `views/ux_lab`, plus logging panel code under `cogs/logging/`.
- Services: diagnostics, health, setup, resource provisioning, moderation, automod, image moderation, security, server logging, welcome, counters, channel/role lifecycle, role automation, tickets.
- DB/migrations/utils: `utils/settings_keys/*`, `utils/db/moderation.py`, `utils/db/bindings.py`, `utils/db/resource_provisioning_audit.py`, setup tables, role tables, ticket tables, and migrations 022/029/030/031/035/052/069/078-081/089/098/099.
- Tests/invariants: moderation, role routing, cleanup schemas, setup delegate boundary, no-silent-auto-create, capability, settings/binding/provisioning tests, server logging tests where named by grep.

### Commands run and results

- `gh pr view 1509 --json number,state,title,url` — failed: `gh: command not found`. Open PR #1509 could not be verified from this container; treated as advisory only per instruction.
- `find docs/owner/claims -maxdepth 1 -type f -print` — found existing claim files, no file overlap with this report except repo-wide awareness.
- `rg -n "gate|owner|Hermes|setup|logging|live-bot|off-limits" ...` — active setup/server-management decisions exist; no stop-condition making this read-only mapping lane off-limits was found. Relevant active owner guidance: Discord panels remain the primary owner surface; AI/action gates remain separate; setup mutations require existing setup wizard/apply primitives; owner/Hermes review labels are retired in current binding docs.
- `python3.10 scripts/context_map.py <major cog>` — initial required command failed because `python3.10` was not active in pyenv. Retried with `PYENV_VERSION=3.10.20`; all context-map attempts then failed with `ModuleNotFoundError: No module named 'yaml'`.
- `PYENV_VERSION=3.10.20 python3.10 scripts/wiring_map.py --check` — passed with advisory possible dead subscribers for `ticket.opened` and governance events.
- `PYENV_VERSION=3.10.20 python3.10 scripts/check_architecture.py --mode strict` — failed with `ModuleNotFoundError: No module named 'yaml'`.
- `PYENV_VERSION=3.10.20 python3.10 scripts/check_docs.py` — run after adding this report; result recorded in final verification section below.

### Verification limits

- No live Discord credentials were used; Discord permission/hierarchy behavior is mapped from source and docs only.
- PR #1509 was not verifiable because GitHub CLI is unavailable.
- CodeGraph was not available as a callable local tool in this environment; fallback was docs + ripgrep + direct source reads.
- Context-map and strict architecture tooling were blocked by missing `yaml` in the selected Python environment.

## 3. Server control surface inventory

### 3.1 Admin and platform operator surfaces

| Subsystem | Entry commands | Panels/views | Services/mutation owners | Settings/bindings/resources | DB/tables | Events/audit | Tests/invariants |
|---|---|---|---|---|---|---|---|
| Admin cog | `!admin`, owner/admin utility commands in `admin_cog.py` | Mostly command output; no `views/admin` directory present | Mixed command handlers; rebuild should isolate platform-owner operations | Bot/global operational flags where applicable | feature flag/state tables via rollout service if used | Should emit explicit operator audit; current admin surfaces are more command-shaped | Needs owner-only/admin-only invariant coverage in fresh repo |
| Diagnostics | `!diagnostics`, `!platform`, health/readiness commands in `diagnostic_cog.py` | `views.diagnostic.hub_panel._DiagnosticsHubView`, `_PaginatorView`, `_PlatformHubView`, `FlagManagerView`, `AutomationPanelView` | `services.diagnostics_service`, `diagnostic_embeds`, `diagnostic_helpers`; `FlagManagerView` writes through rollout mutation; `AutomationPanelView` through `AutomationMutationPipeline` | Read-only registry/platform facts; flag manager includes operator flags such as `settings.mutation.primary` and `resource_provisioning.primary` | feature flag state/audit, automation rules | Read-only panels; flag writes audited by rollout pipeline; automation writes emit `automation.rule_changed` | wiring map includes event subscribers; flag manager source comments explicitly forbid direct delete path |
| Health maintenance | health-maintenance cog | Command-driven maintenance/readiness | `health_contracts`, `health_findings_service`, `health_observations`, `health_snapshot_service` | Health facts, observations, findings | health storage if configured | Diagnostic/audit logs, not user mutation | Should remain read-only or owner-gated maintenance in rebuild |
| UX lab | `ux_lab_cog.py` | `views.ux_lab.*` mockups/probes/layout demos | None for production mutation | N/A | N/A | N/A | Treat as design lab, not production owner surface |

### 3.2 Server management and setup

| Subsystem | Entry commands | Panels/views | Services/mutation owners | Settings/bindings/resources | DB/tables/migrations | Events/audit | Tests/invariants |
|---|---|---|---|---|---|---|---|
| Server management hub | `!server`, aliases `servermanage`, `serverpanel` | `ServerManagementHubView`, access map panel | Hub routes to existing cogs/services; `server_management_hub` aggregates readiness/capability facts | No own settings; projects setup/settings/bindings/readiness | None | Read-only navigation except routed panels | Rebuild should pin hub route registry |
| Setup wizard | `!setup`, `!setup scan`, `!setup start`, `!setup resume`, `!setup apply`, `!setup-delegate`, bootstrap access | `views.setup.launcher`, `hub`, `wizard`, `depth_panel`, `scan_panel`, `section_card`, `final_review`, `recovery`, `template_picker`, `essential_setup` | `setup_session`, `setup_draft`, `setup_operations`, `setup_access`, `setup_readiness`, `setup_sections`, `setup_role_templates`, `resource_provisioning` | Draft operations include settings, bindings, role templates, provisioning packs | migrations `031_setup_session`, `035_setup_draft_operations`, `045_setup_draft_provenance`, `046/047/038/069/099` | Setup delegate actor type is audited through settings/binding/provisioning pipelines; provisioning emits `resource.provisioned`; settings/bindings emit own events | `test_setup_delegate_apply.py`, `test_setup_delegate_actor_boundary.py`, setup readiness/tests |
| Resource provisioning | setup/resource panels and settings missing-binding flows | channel/role pickers; logging provisioning views under `cogs/logging` | `ResourceProvisioningPipeline` is the owner for create-or-reuse + bind | `ResourceRequirement`, `ProvisioningOption`, `BindingSpec` catalogue | `resource_provisioning_audit` migration 030 | emits `resource.provisioned` plus binding changed; audits success/fail/decline | `test_no_silent_auto_create.py`, provisioning pipeline tests |

### 3.3 Moderation and cleanup

| Subsystem | Entry commands | Panels/views | Services/mutation owners | Settings keys | DB/tables | Events/audit | Tests/invariants |
|---|---|---|---|---|---|---|---|
| Manual moderation | `!warn`, `!warnings`, `!clearwarnings`, `!mute/timeout`, `!kick`, `!ban`, `!unban`, moderation panel command | `views.moderation.main_panel`, `views.moderation.modals` | `services.moderation_service` should own warn/timeout/kick/ban/unban/clear/manual records | `warn_threshold`, `warn_timeout_minutes`, `moderation_dm_on_action`, `moderation_dm_actions`, `moderation_dm_template`, `moderation_require_reason`, `moderation_ban_delete_message_days`, `moderation_max_timeout_minutes`, `moderation_warn_escalation_action`, `moderation_post_action_cleanup`, `moderation_post_action_cleanup_limit`, `moderation_public_log_channel`, `moderation_public_log_actions` | `utils/db/moderation.py`, `mod_logs` / warnings tables | emits `moderation.action_taken`; server logging consumes for mod/private and public log | moderation tests; governance ADR-008 moderator-role tier grants |
| Cleanup | cleanup commands/panel | `views.cleanup.policy_panel` | `cleanup_cog` detects spam/cleanup policy; destructive delete/audit routes through `moderation_service.auto_delete` | cleanup settings registered with capability `cleanup.policy.configure`, including spam window | legacy KV settings; moderation logs for deletes | auto-delete emits same moderation event | `test_cleanup_schemas.py` pins capability/spec shape |
| Automod | `automod_cog.py`, listener stage | no `views/automod` directory present; settings panels via schemas/settings | `automod_service` and listener stage; final delete routes via message pipeline to `moderation_service.auto_delete` | `automod_enabled`, rule flags/counts/windows, exempt role/channel CSVs | legacy KV settings | message pipeline descriptor -> `EVT_MOD_ACTION`; automod-specific audit through moderation logs | automod schema/config tests |
| Image moderation | `image_moderation_cog.py`, listener stage | no dedicated image moderation views present | `image_moderation_service` external-call scanner; stage only when opted in; delete through moderation seam | `image_moderation_enabled`, per-category flags, threshold, exempt role/channel CSVs | legacy KV settings | emits `image_moderation.flagged`; moderation delete event if action taken | config/listener tests should preserve no-external-call-until-enabled |
| Security | `security_cog.py` | no `views/security` directory present | `security_service` owns raid/account-age detection and actions | `security_enabled`, raid count/window/slowmode/lockdown/channel, age min/action, alert channel | legacy KV settings | emits `security.raid_detected`, `security.account_flagged`; staff alert channel | security config/service tests |
| Message pipeline | global `on_message` platform listener | N/A | `core.runtime.message_pipeline` orchestrates staged message handling and routes moderation descriptors to `moderation_service.auto_delete` | N/A | moderation logs via service | ordered stage contract: automod/cleanup/counting/chain/image_mod before XP rewards | pipeline tests/invariants |

### 3.4 Server logging, welcome, counters, passive events

| Subsystem | Entry commands | Panels/views | Services/mutation owners | Settings/bindings/resources | DB/tables | Events/audit | Tests/invariants |
|---|---|---|---|---|---|---|---|
| Logging | `logging_cog.py`; panel code in `cogs/logging/*` | `panel.py`, `routes_panel.py`, `select_view.py`, `provision_view.py` | `server_logging` sends embeds; `server_logging_config` reads config; settings/bindings/provisioning pipelines mutate | `logging_enabled`, mod/cleanup channels, auto-create, passive category flags, routing, ignored channels/users; BindingSpecs for mod/cleanup/events/message/member/role channels | legacy KV; subsystem_bindings; provisioning audit | subscribes `moderation.action_taken`, `audit.action_recorded`; gateway/audit-log listeners emit embeds | server-logging docs/tests |
| Welcome | `welcome_cog.py` | no `views/welcome` directory present | `welcome_service` greets/DMs/entry-role; config service reads | welcome enable flags, channel, templates, entry role, DM/card/min-age/delete-after | legacy KV | emits `welcome.member_greeted`; logs failures | welcome config/service tests |
| Counters | `counters_cog.py` | no `views/counters` directory present | `counter_service` owns renaming loop; config reads | counters enabled, total/humans/bots channel ids/templates | legacy KV | emits `counters.updated` | counter tests |

### 3.5 Channel and role lifecycle

| Subsystem | Entry commands | Panels/views | Services/mutation owners | Settings/bindings/resources | DB/tables | Events/audit | Tests/invariants |
|---|---|---|---|---|---|---|---|
| Channels | `channel_cog.py` channel create/list/delete/restrict/move/visibility commands | `views.channels.main_panel`, create/delete/list/move/restrict/visibility subviews | `ChannelLifecycleService` owns rename/move/delete/reorder preview/apply; provisioning owns subsystem channel creation; some manual channel CRUD remains legacy/grandfathered | Bindings via `BindingMutationPipeline`; resources via provisioning | lifecycle audit via `services.lifecycle.contracts` if used | `channel.lifecycle_changed` or lifecycle audit (service-level) | no-silent-auto-create allowlist documents legacy exceptions |
| Roles | `role_cog.py` role creation/management/time/XP/reaction-role flows | `views.roles.*` creation, management, diagnostics, exemptions, reaction, role menus, time/xp panels | `RoleLifecycleService` owns operator-driven role create/edit/delete; `role_automation` owns member assignment/removal for progression; reaction roles own self-assign paths | role settings: stack flags, reaction roles enabled; bindings/role thresholds/templates | migrations 003,052,056,078-081,089; role tables | `role.lifecycle_changed`; `audit.action_recorded` for role automation | `test_role_cog_routing.py` pins no direct member role APIs for threshold paths |

### 3.6 Support/proof/access surfaces

| Subsystem | Entry commands | Panels/views | Services/mutation owners | Settings/bindings/resources | DB/tables | Events/audit | Tests/invariants |
|---|---|---|---|---|---|---|---|
| Proof channel | `proof_channel_cog.py` | no `views/proof_channel` directory present | Settings/bindings/provisioning pipelines | `proof_channel.settings.configure`, `proof_channel` BindingSpec, ResourceRequirement | subsystem_bindings/provisioning audit | binding/resource events | schema tests likely |
| Tickets | `ticket_cog.py` | `views.tickets.*` hub/config/control/confirm/launcher | `ticket_service`, `ticket_mutation` own ticket open/close/config operations | ticket config + channel/category resources | migration `098_tickets`, `utils/db/tickets.py` | subscriber for `ticket.opened`; wiring map says possible dead subscriber advisory | ticket tests |

## 4. Best ideas/functions/classes to preserve

| Source | Problem solved | Rebuild disposition | Hidden dependencies |
|---|---|---|---|
| `governance.capability.actor_holds_capability` | Central capability decision with target-guild membership, platform-owner override, admin floor, revoke overlay, setup delegate actor type | **Copy idea; redesign API as `CapabilityDecision` service in foundation** | `config.is_platform_owner`, visibility tiers, execution override cache, setup delegate minting |
| `SettingsMutationPipeline.set_value` | One owner for scalar setting writes: validation, authority, audit, event, cache invalidation | **Copy nearly as-is conceptually** | `SettingSpec`, legacy KV, `settings.mutation.primary`, audit rows, event bus |
| `BindingMutationPipeline.set_binding/clear_binding` | One owner for binding rows and binding-change events | **Copy nearly as-is conceptually** | `BindingSpec`, subsystem binding table, provisioning delegates to it |
| `ResourceProvisioningPipeline.preview/provision` | Safe create-or-bind resources with no silent auto-create | **Copy idea; make UI primitive first-class** | Discord permissions, `guild_resources.ensure_*`, binding pipeline, provisioning audit |
| `services.lifecycle.contracts` | Shared preview/result/outcome/reversibility vocabulary | **Copy nearly as-is** | Domain services must emit lifecycle audit consistently |
| `ChannelLifecycleService` | Keeps destructive/channel hierarchy mutations out of views | **Copy idea; expand to all channel ops** | Discord hierarchy constraints, old channel cog exceptions |
| `RoleLifecycleService` | Keeps role create/edit/delete and feasibility checks out of panels | **Copy idea; expand member assignment separations** | Role hierarchy, `role_feasibility`, role automation audit |
| `role_automation` | Owns progression role assignment/removal; avoids direct `member.add_roles` in cog threshold paths | **Copy nearly as-is idea** | XP/time thresholds, exemptions table, role audit event |
| `moderation_service.auto_delete` and manual action functions | Unifies deletes and moderator actions into mod log/event flow | **Copy idea; redesign as `ModerationActionSpec` executor** | `mod_logs`, DM policy, cleanup policy, public logging |
| `message_pipeline.StageResult` / `ModerationActionDescriptor` | Ordered staged message handling; deleted messages do not proceed to rewards; audit is unified | **Copy nearly as-is** | Stage ordering constants; moderation service idempotence around `NotFound` |
| `server_logging.start/stop` subscriptions | Decouples moderation/audit events from log embeds | **Copy idea; formalize `ServerEventRouteSpec`** | Event names, channel binding/settings, per-category opt-in, ignored IDs |
| `views.diagnostic.platform_panel._PlatformHubView` | Discoverable read-only operational map for owner/admins | **Copy idea** | Registry completeness, read-only category select grammar |
| `views.diagnostic.flag_manager.FlagManagerView` | Mutating exception inside platform hub routes through mutation pipeline, not raw DB | **Copy idea but strengthen capability checks** | rollout pipeline, operator flags, admin/platform owner audience |
| `setup_operations.apply_operations` | Draft apply re-verifies setup access and mints `setup_delegate` actor type for pipelines | **Copy idea** | setup access service, draft operation schemas, audit actor types |
| `views.setup.final_review` | Human-readable final review before applying setup changes | **Copy idea** | draft rendering, before-state/undo policy, operation risk |
| `server_management_hub` service | Aggregates bot permission readiness for hub cards | **Copy idea** | moderation/channel/role feasibility utilities |

## 5. Safety and mutation model extraction

### One true mutation owner by action

| Action class | Current owner to preserve | Notes / hazards |
|---|---|---|
| Manual warn/timeout/kick/ban/unban/clear warnings | `services.moderation_service` | Commands/panels may initiate; service should own DM policy, reason requirement, ban-delete-days, post-action cleanup request, audit/event. |
| Automated message delete | `core.runtime.message_pipeline` routes descriptor to `moderation_service.auto_delete` | Stages can detect/delete, but audit should still be normalized by the moderation service. |
| Image moderation external call | `image_moderation_service` + listener/stage | Must be disabled by default; no external API call until guild opt-in; honor exempt roles/channels; threshold/category flags govern action. |
| Raid handling/account-age filter | `security_service` | Owns join-window state, slowmode/lockdown/action/alert; fresh repo should make Discord side effects explicit specs. |
| Cleanup policy delete | `cleanup_cog` stage/policy detection -> `moderation_service.auto_delete` | Cleanup settings are policy; deletion/audit owner is moderation service. |
| Server logging embeds | `server_logging` | It should never own primary mutations; it subscribes to events/gateway/audit logs and routes according to config. |
| Role lifecycle create/edit/delete | `RoleLifecycleService` | Must enforce role hierarchy and preview/confirm destructive changes. |
| Role member assignment/removal for progression | `role_automation` | Separate from role definition lifecycle; tests already enforce no direct cog member role APIs for threshold paths. |
| Channel lifecycle rename/move/delete/reorder | `ChannelLifecycleService` | Should absorb old channel cog direct mutations in future. |
| Subsystem create-or-bind resources | `ResourceProvisioningPipeline` | No silent auto-create; confirmation or standing setting required; binding through binding pipeline. |
| Scalar settings | `SettingsMutationPipeline` | Capability and kill-switch checked before write; emits settings changed. |
| Resource bindings | `BindingMutationPipeline` | Capability, audit/event/cache invalidation; never direct table writes from views/cogs. |
| Setup wizard apply | `setup_operations.apply_operations` | Owns draft operation execution and `setup_delegate` actor type; delegates actual mutation to pipelines. |
| Ticket open/close/config | `ticket_service` / `ticket_mutation` | Keep as domain owner; wiring check advisory says `ticket.opened` subscriber needs confirmation. |

## 6. Admin UX grammar

### Reusable patterns found

- **Preview before mutation:** provisioning preview, setup final review, channel/role lifecycle previews.
- **Confirmation for irreversible actions:** lifecycle services and ticket confirm views model this; future repo should require `ConfirmationSpec` for ban/delete/role delete/channel delete/bulk cleanup/full setup apply.
- **Permission/capability re-check in callbacks:** documented in `docs/capability-authority.md`; must be made universal for mutating panels reachable from hubs/help.
- **Resource picker flows:** channel/role selectors exist in `views/selectors`, logging provision views, setup template/resource flows, role/channel panels.
- **Create or bind flows:** resource provisioning pipeline and logging provisioning views are the best concrete implementation.
- **Settings editor flows:** schemas (`SettingSpec`) plus settings views are the canonical future route; many cogs still expose command-specific config.
- **Diagnostic read-only panels:** diagnostic/platform hubs demonstrate safe read-only UX.
- **Staff/admin/owner separation:** moderation uses moderator tier grants; settings/provisioning use admin floor + platform owner override; setup-delegate is owner/capability significant; platform diagnostics should be owner/admin classified.
- **Ephemeral/public behavior:** diagnostic hubs are ephemeral/timeout-based; moderation public logging is opt-in and strips moderator identity; most owner panels should default ephemeral.

### Inconsistencies to eliminate

- Commands, hubs, and setup wizard expose overlapping setup/config paths.
- Some admin surfaces rely on command decorators while panels rely on invoker locks; callbacks need a single `AdminActionSpec` authority check.
- Logging settings use legacy channel-id settings and BindingSpecs in parallel; future repo should pick binding rows as route truth and migrate settings as compatibility aliases only.
- View directories are inconsistent: logging panels live under `cogs/logging/`, tickets use `views/tickets`, no dedicated views exist for automod/security/welcome/counters despite owner-facing settings.
- Lifecycle result vocabulary exists for channels/roles but not yet for moderation/security/tickets/logging route mutations.

## 7. Hidden dependencies and rebuild hazards

- **Permission semantics:** Discord administrator, bot owner override, target-guild membership, moderator/trusted role tier grants, setup delegate actor type, and raw Discord permissions (`manage_channels`, `manage_roles`, moderation perms) are distinct and must not be collapsed.
- **Capability strings:** `logging.settings.configure`, `moderation.settings.configure`, `cleanup.policy.configure`, `proof_channel.settings.configure`, XP/help/game capabilities, and empty-capability admin floor all exist.
- **Settings key names:** legacy KV keys listed in `utils/settings_keys/*` are externally observable migration data; a rebuild needs an import map.
- **Binding rows:** `subsystem_bindings` is the durable row owner for resource IDs; provisioning binds through the binding pipeline.
- **Audit payload shapes:** moderation logs/events, settings mutation audit, resource provisioning audit, lifecycle audit, feature flag audit, ticket audit should be formalized before rebuild.
- **Event names:** `moderation.action_taken`, `audit.action_recorded`, `settings.changed`, binding changed event, `resource.provisioned`, `role.lifecycle_changed`, `security.raid_detected`, `security.account_flagged`, `image_moderation.flagged`, `welcome.member_greeted`, `counters.updated`, `automation.rule_changed`, `ticket.opened`.
- **Log routing channels:** mod channel, cleanup channel, events/message/member/role channels, public moderation log channel, security alert channel, welcome channel, counter channels.
- **Discord hierarchy constraints:** bot role position must exceed managed roles; channel/category permissions and slowmode require bot permissions; delete/reorder operations can fail mid-flight.
- **External moderation API assumptions:** image moderation uses OpenAI moderation endpoint and must not send images unless enabled; endpoint failures should degrade safely and log diagnostic failures.
- **Per-guild teardown hooks:** setup sessions, bindings, tickets, role menus, counters, logging route state, and automation rules all have guild-scoped persistence; rebuild import/teardown must be explicit.
- **Persistent panel IDs:** diagnostic views are ephemeral, but tickets/role menus/logging/setup launchers may have persistent custom IDs; a clean repo needs a registry.
- **Live/owner-gated setup assumptions:** setup delegate and owner-only bootstrap are capability-significant; do not let normal users apply setup drafts.

## 8. Fragmentation and duplication inventory

### Critical rebuild lesson

- **Direct Discord mutations must not live in views/cogs.** Legacy channel/role paths are grandfathered; future repo should require lifecycle/provisioning services for every Discord resource mutation.
- **Authority cannot be decorator-only.** Hubs/help can make panels reachable without command decorators; mutating callbacks must re-check capability.
- **Setup apply must be one path.** `quicksetup`, setup wizard, per-cog config, and hub routes should all compile to setup draft operations or mutation specs.

### Important improvement

- Move logging UI from `cogs/logging/*` into `views/logging/*` or a generated settings/bindings panel family.
- Add first-class `ModerationActionSpec` and `SecurityActionSpec` previews/results matching lifecycle services.
- Convert public/private log channel IDs from legacy settings into binding specs with compatibility read aliases.
- Give automod/security/welcome/counters dedicated generated panels instead of command-only/admin-only hidden features.

### Cleanup

- Normalize naming: `ticket` vs `tickets`, `proof_channel` view absence, logging panels under cogs.
- Replace one-off modals/selects with shared resource picker/settings editor/confirmation primitives.
- Confirm or remove wiring-map advisory dead subscribers.

### Acceptable specialization

- UX lab remains a non-production design surface.
- Public moderation logging intentionally differs from private moderator logs by omitting actor identity.
- Image moderation needs external-call-specific guardrails beyond text automod.

## 9. Future new-repo recommendations

### Foundation primitives

- **`AdminActionSpec`**: name, audience, capability, Discord permission fallback, callback re-check requirement, public/ephemeral policy, audit event. Evidence: command decorators + capability docs + hub-reachable panels.
- **`ModerationActionSpec`**: action kind (`warn`, `timeout`, `kick`, `ban`, `delete`, `auto_delete`), target, reason policy, DM policy, cleanup policy, hierarchy/permission check, audit payload, log route. Evidence: `moderation_service`, moderation settings keys, message pipeline descriptor.
- **`ResourceMutationSpec`**: resource kind, operation (`create`, `bind`, `rename`, `move`, `delete`, `reorder`), preview, confirmation, Discord permission requirements, rollback/compensation notes. Evidence: provisioning and lifecycle services.
- **`AuditEventSpec`**: event name, actor/subject/guild, payload schema, redaction/public projection, subscribers. Evidence: moderation/server_logging/settings/provisioning/lifecycle events.
- **`SettingsPanelSpec`**: generated editor over `SettingSpec`, widgets, validation, capability, default, help copy, setup-section membership. Evidence: subsystem schemas and settings mutation pipeline.
- **`BindingSpec`**: canonical resource binding declaration with required kind, fallback route, setup/provisioning hint, migration/import alias. Evidence: subsystem binding docs and provisioning catalogue.
- **`ConfirmationSpec`**: irreversible/compensatable/reversible classification, challenge text or preview hash, timeout, actor re-check, before-state snapshot requirement. Evidence: lifecycle contracts and setup final review.
- **`LifecycleResult`**: shared result object for all Discord/server mutations, not just channels/roles. Evidence: `services.lifecycle.contracts`.
- **`ServerEventRouteSpec`**: passive event category, source (gateway/audit-log/domain event), opt-in flag, route binding, public/private projection, ignore filters. Evidence: server logging v1/v2 keys and docs.

### Recommended shape

Build the fresh repo around a **spec registry + mutation executors + generated panels**:

1. Each subsystem declares settings, bindings, resources, admin actions, log routes, and setup sections.
2. Hubs render from registries.
3. Mutations execute only through service-layer owners.
4. Every mutating UI callback re-checks an `AdminActionSpec`.
5. Every result emits a typed audit event and returns a typed result object.
6. Setup wizard compiles drafts to the same specs; it never owns mutation logic.

## 10. Handoff to other mapping sessions

### Platform/UI primitives this session depends on

- Base view invoker locking vs authority re-check.
- Settings registry and generated settings panels.
- Binding/provisioning catalogue.
- Event bus and audit event contracts.
- Persistent view/custom-id registry.
- Setup section registry and draft operation rendering.
- Capability/governance tier resolver.

### Areas that use or should use these patterns

- Economy/community/game features with admin-tunable settings should use `SettingsPanelSpec` and capability checks, not bespoke commands.
- AI provider/admin controls must remain read-only or capability-gated and should reuse diagnostics/platform panels.
- Games/community role rewards should route member role assignment through role automation, not direct Discord APIs.
- Any subsystem that needs a channel should declare a BindingSpec/ResourceRequirement and use provisioning.
- Public-facing announcements/logs should define `ServerEventRouteSpec` with public/private redaction rules.

## 11. Final verification after report creation

- `PYENV_VERSION=3.10.20 python3.10 scripts/check_docs.py` was attempted after writing this file. If it fails, record exact output in the session/final response; source was not changed to satisfy the checker because the allowed edit is this report only.

