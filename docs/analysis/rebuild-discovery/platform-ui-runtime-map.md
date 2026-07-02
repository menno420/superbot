# Platform/UI/runtime rebuild discovery map (Part 1 of 4)

> **Status:** `historical` — source-grounded discovery report for a possible future rebuild; source and merged PRs win.

Date: 2026-07-02  
Scope: core platform, UI grammar, runtime, help/discoverability, settings/bindings/provisioning, diagnostics.  
Output type: discovery map only. This report does **not** approve a rebuild and does **not** propose source changes.

## 1. Executive summary

### What this bot already does best

- **It has real platform seams, not only feature cogs.** The strongest reusable pieces are `BaseView`/`HubView`, `PersistentView`, `views.navigation`, `core.runtime.interaction_helpers`, `core.runtime.lifecycle`, `core.runtime.tasks`, `core.events.EventBus`, `core.runtime.subsystem_schema`, `utils.subsystem_registry`, governance resolution/mutation services, help catalogue/projection/overlay, typed settings/bindings/resource provisioning, and health diagnostics.
- **It separates mutation ownership better than most Discord bots.** Scalar settings go through `SettingsMutationPipeline`; bindings through `BindingMutationPipeline`; resources through `ResourceProvisioningPipeline`; governance through `GovernanceMutationPipeline`; help presentation through `help_overlay_mutation`; lifecycle Discord resources through channel/role lifecycle services.
- **It treats UI as an operational contract.** `BaseView` locks panels to the invoker by default, disables on timeout, and auto-attaches standard Help/back-to-hub navigation when `SUBSYSTEM` is declared. `PersistentView` documents cross-restart requirements. `safe_defer`, `safe_followup`, and `safe_edit` encode the Discord interaction deadline and embed-size limits.
- **It has discoverability as a projection layer.** Help is no longer only command introspection: `help_catalogue` builds a registry-aware catalogue; `help_projection` applies governance/execution/overlay decisions; `help_overlay` stores guild presentation customizations; Help routes can open command, category, and subsystem panels.
- **It already contains the vocabulary of a future platform kernel.** Current source effectively proves the need for `SubsystemManifest`, `PanelSpec`, `ActionSpec`, `NavigationSpec`, `SelectorSpec`, `SettingSpec`, `BindingSpec`, `ResourceSpec`, `ConfirmationSpec`, `WorkflowResult`, `MutationPreview`, `AuditEventSpec`, and `DiagnosticProviderSpec`.

### What a future clean repo should preserve

- Preserve **service-owned mutations + audited fan-out**: mutation result objects, authority re-checks at callback execution time, explicit audit/event emission, and cache invalidation hooks.
- Preserve **Help as projection**, not as scattered command docs: reason-coded display decisions, overlay state, route openers, category/subsystem grouping, and command-to-panel mapping.
- Preserve **runtime contracts**: lifecycle phases, managed task registry, publish-accepted EventBus semantics, persistent view registration, interaction helper patterns, startup and health diagnostics.
- Preserve **settings/bindings/resources as distinct lanes**: scalar values, Discord object pointers, and provisionable resources must not collapse into a generic configuration table.
- Preserve **registry-driven subsystem metadata**: subsystem keys, capabilities, hubs, related subsystems, default channels, visibility tier/mode, and UI priority are architectural data.

### What should be redesigned into central primitives

- Turn today's `SUBSYSTEMS` dict + `SubsystemSchema` into a single typed **`SubsystemManifest`** that owns metadata, capabilities, commands, panels, settings, bindings, resources, diagnostics, audit events, and help entries.
- Turn ad-hoc embed/view builders into **`PanelSpec` + `EmbedFrame` + `Table/ListSpec`** so panels can be rendered consistently across Discord, control API, docs, and tests.
- Turn button/select/modal callback patterns into **`ActionSpec`**, **`SelectorSpec`**, and **`ConfirmationSpec`** with standard authority, defer, mutation preview, result rendering, audit, and error handling.
- Turn navigation into **`NavigationSpec`** with canonical Help/home/back behavior, stack/anchor semantics, persistent custom IDs, and public/ephemeral policy.
- Turn diagnostics providers into **`DiagnosticProviderSpec`** with audience, sync/async lane, timeout, redaction, status mapping, and ownership metadata.
- Turn mutation return shapes into **`WorkflowResult` / `MutationPreview`** so settings, bindings, provisioning, governance, setup operations, and lifecycle services all speak one result grammar.

### What should not be carried forward

- Do not carry forward duplicate back buttons and one-off navigation functions where `views.navigation`/`BaseView` can express the contract.
- Do not carry forward direct `discord.ui.View` subclasses unless their specialized state/lifecycle is documented and test-pinned.
- Do not carry forward command-only feature surfaces without Help route, hub panel, or settings/discoverability metadata.
- Do not carry forward scattered permission checks; panel entry and every callback need central governance/capability resolution.
- Do not carry forward direct DB writes from cogs/views or ad-hoc raw SQL outside db/service owners.
- Do not copy stale planning docs as truth. This repo has valuable docs, but source + merged PRs remain authoritative.

## 2. Source route and verification

### Binding/current-state docs read

Read or inspected directly:

- `.claude/CLAUDE.md`
- `docs/collaboration-model.md`
- `docs/current-state.md`
- `docs/current-state/S3-ai-memory.md`
- `docs/current-state/S4-docs.md`
- `docs/current-state/S5-ops.md`
- `docs/AGENT_ORIENTATION.md`
- `docs/architecture.md`
- `docs/ownership.md`
- `docs/runtime_contracts.md`
- `docs/repo-navigation-map.md`
- `docs/repo-review-map.md`
- `docs/ultracode/README.md`
- `docs/subsystems/settings-bindings-provisioning.md`
- `docs/subsystems/health-diagnostics.md`
- `docs/help-command-surface-map.md`
- `docs/building-roadmap/command-integration-standard.md`
- `docs/building-roadmap/mother-hub-map.md`
- `docs/setup-platform/` index/content by targeted search
- `docs/health/` index/content by targeted search

### Source roots inspected

Inspected by direct reads and ripgrep across:

- Runtime/lifecycle: `disbot/bot1.py`, `disbot/config.py`, `disbot/guild_lifecycle.py`, `disbot/healthserver.py`, `disbot/core/runtime/`, `disbot/core/resources/`, `disbot/core/events.py`, `disbot/core/events_catalogue.py`.
- Governance/capability: `disbot/governance/`, `disbot/services/governance_service.py`, `disbot/services/*governance*`, `disbot/services/*capability*`, `disbot/utils/subsystem_registry.py`, `disbot/utils/hub_registry.py`, `disbot/utils/settings_keys/`.
- Shared UI/navigation: `disbot/views/base.py`, `disbot/views/navigation.py`, `disbot/views/selectors/`, `disbot/views/settings/`, hub view files found by `rg "class .*Hub|HubView|PersistentView|BaseView" disbot/views disbot/cogs`.
- Help/discoverability: `disbot/cogs/help_cog.py`, `disbot/cogs/help/`, `disbot/services/help_catalogue.py`, `disbot/services/help_projection.py`, `disbot/services/help_overlay.py`, `disbot/services/help_overlay_mutation.py`.
- Settings/bindings/provisioning: `disbot/services/settings*`, `disbot/services/binding*`, `disbot/services/resource_provisioning.py`, `disbot/services/lifecycle/`, `disbot/services/channel_lifecycle_service.py`, `disbot/services/role_lifecycle_service.py`, `disbot/views/settings/`.
- Diagnostics/observability: `disbot/services/diagnostics_service.py`, `disbot/services/health_snapshot_service.py`, `disbot/services/health_findings_service.py`, `disbot/services/health_contracts.py`, tests under `tests/unit/services/`, `tests/unit/runtime/`, `tests/unit/views/`, `tests/unit/help/`, `tests/unit/registry/`, `tests/unit/invariants/` by targeted search.

### Commands run and results

- `find /workspace -name AGENTS.md -print` — passed; no `AGENTS.md` files found under `/workspace`, so no repo-local agent instructions applied.
- `git status --short` — passed before editing; working tree initially clean.
- `gh pr list --state open --limit 20` — failed: `gh` is not installed in the container.
- `curl -s https://api.github.com/repos/menno420/superbot/pulls?state=open&per_page=20 ...` — attempted for open PR verification, but the inline parser failed because `python3.10` was initially not selected by pyenv. Verification limit recorded below.
- `PYENV_VERSION=3.10.20 python3.10 --version` — passed: `Python 3.10.20`.
- `PYENV_VERSION=3.10.20 python3.10 scripts/context_map.py disbot/views/base.py` — first failed before installing PyYAML; then passed after `python3.10 -m pip install PyYAML`. Result: `views.base`, review unit `A1 · platform: view-primitives`, 172 importers, 555 transitive dependents, high fan-in.
- `PYENV_VERSION=3.10.20 python3.10 scripts/context_map.py disbot/views/navigation.py` — first failed before installing PyYAML; then passed. Result: `views.navigation`, review unit `A1 · platform: view-primitives`, 49 importers, 555 transitive dependents, relevant test `tests/unit/views/test_navigation.py`.
- `PYENV_VERSION=3.10.20 python3.10 scripts/context_map.py disbot/utils/subsystem_registry.py` — first failed before installing PyYAML; then passed. Result: `utils.subsystem_registry`, review unit `A1 · platform: utils`, 31 importers, 555 transitive dependents, relevant test `tests/unit/utils/test_subsystem_registry.py`.
- `PYENV_VERSION=3.10.20 python3.10 scripts/context_map.py disbot/core/runtime/interaction_router.py` — first failed before installing PyYAML; then passed. Result: `core.runtime.interaction_router`, review unit `A1 · platform: runtime-core`, imported by `utils.subsystem_registry`, 555 transitive dependents.
- `PYENV_VERSION=3.10.20 python3.10 scripts/wiring_map.py --check` — passed. Advisory possible dead subscribers: `ticket.opened`, `governance.visibility.changed`, `governance.cache.invalidated`, `governance.cleanup.changed`. Final output: `EventBus wiring check passed ✓`.
- `PYENV_VERSION=3.10.20 python3.10 scripts/check_architecture.py --mode strict` — first failed before installing PyYAML; then passed with `0 error(s), 49 warning(s)`. Warnings include 13 direct-`discord.ui.View` inheritance warnings, 31 known layer-boundary warnings, and 5 raw-SQL warnings.

### Open PR / active gate status

- The GitHub CLI is absent, so open PR verification could not use `gh`.
- A GitHub REST check was attempted but the first parser invocation failed due to pyenv not exposing `python3.10` until `PYENV_VERSION=3.10.20` was set. Because this task is a repo-local discovery report and no source behavior was changed, I treated open PRs as a verification limit rather than a blocker.
- Current-state S3/S4/S5 show no active gate making this scope off-limits. They do identify the fresh-rebuild vision as planning/discovery context, not approval to rebuild.
- PR #1509, if open, was not used as merged truth. This report relies on checked-out source and binding docs.

### Verification limits

- No live Discord bot, production DB, credentials, or provider keys were used.
- Source was inspected in the current checkout only; unmerged PR source was not incorporated.
- `check_quality.py --full` was not run because this change is one markdown report and the full suite is expensive; targeted docs/architecture/wiring checks were used instead, with `check_docs.py` run after writing the report if available.

## 3. Platform architecture map

### Runtime lifecycle

- `disbot/bot1.py` is the process entry and wiring hub: it loads extensions, validates registries, registers persistent views, attaches command gating, starts health/control surfaces, and owns shutdown cleanup.
- `disbot/core/runtime/lifecycle.py` is the canonical process phase machine: `STARTING`, `RUNNING`, `DRAINING`, `SHUTTING_DOWN`, `RESTARTING`, `STOPPED`, `FAILED_STARTUP`. It exposes `can_accept_commands()`, `request_shutdown()`, `request_restart()`, pending intent state, a transition ring buffer, and metrics gauges/histograms.
- `disbot/core/runtime/tasks.py` centralizes managed background tasks. `spawn()` keeps strong refs, records outcomes, logs errors, supports `cancel_all()` and `cancel_by_prefix()`, and registers a diagnostics provider.
- `disbot/core/runtime/scope_locks.py`, `session_gc.py`, `message_anchor_manager.py`, `navigation_stack.py`, `live_update_scheduler.py`, and `message_pipeline.py` show a recurring platform need: scoped state, anchors, sessions, locks, and safe slow-path execution should be first-class runtime services in a rebuild.

### EventBus and event catalogue

- `disbot/core/events.py` defines a lightweight in-process async `EventBus` with `on`, `off`, `emit`, `registered_events`, and `delivery_stats`.
- The bus contract is **publish-accepted**: `emit()` returning means the bus accepted dispatch, not that every subscriber succeeded. Handler failures/timeouts are isolated and observable.
- `disbot/core/events_catalogue.py` is the known event-name catalogue. Unknown event names warn once and increment metrics instead of crashing runtime.
- `scripts/wiring_map.py --check` passed, with advisory possible dead subscribers. A future repo should make `AuditEventSpec/EventSpec` part of `SubsystemManifest`, including payload shape and subscriber ownership.

### Persistent views and anchor/session lifecycle

- `disbot/core/runtime/persistent_views.py` defines `PersistentView`, a registry, and the cross-restart contract: `timeout=None`, static `custom_id`s on all components, registration at startup, and no message-local closure state as the only authority.
- `views.navigation.BackTarget` explicitly warns that stack closures cannot be persisted across restarts; persistent re-registration must rebuild views without `_back_target` and rely on click-time governance rechecks.
- `message_anchor_manager`, `navigation_stack`, and `session_gc` indicate that the bot already has implicit session/anchor semantics. A clean repo should model anchors and session state centrally, instead of letting each view improvise.

### Interaction helper/defer/edit/followup pattern

- `core.runtime.interaction_helpers.safe_defer()` defers idempotently and returns `False` if the token expired or HTTP failed.
- `safe_followup()` chooses response vs followup based on whether a response has already happened.
- `safe_edit()` edits the original/anchor safely; `clamp_embed()` enforces Discord embed component, field-count, and total-size limits before sending.
- `help_ctx_shim()` demonstrates compatibility debt: many hub builders still expect command `ctx`; Help/interactions need an interaction-shaped opener. A rebuild should pass explicit `PanelContext` rather than shim command contexts.

### Managed task lifecycle

- `core.runtime.tasks.spawn()` is the canonical task creation API and should be preserved conceptually.
- `cancel_by_prefix()` encodes a useful naming convention (`<subsystem>:<purpose>[:<id>]`) that should become a `TaskSpec`/`ManagedTaskSpec` contract in a future repo.
- Diagnostics provider registration by the tasks module is a good model: runtime services self-report through `diagnostics_service`.

### Governance/capability resolver

- `disbot/governance/models.py` defines `GovernanceContext`, `VisibilityResult`, `ExecutionResult`, `CleanupPolicy`, `CommandPolicy`, `SubsystemEffectiveState`, snapshots and diffs.
- `governance.resolver` resolves visibility through scope chain, member tiers, overrides, dependencies, and subsystem state.
- `governance.execution` resolves command/capability execution and caches capability overrides.
- `governance.capability.actor_holds_capability()` is consumed by settings/bindings/provisioning mutation pipelines via `SettingSpec.capability_required` and `BindingSpec.capability_required`.
- `governance.writes.GovernanceMutationPipeline` owns visibility/cleanup/capability-style writes and audit fan-out.
- Rebuild lesson: never treat opening a panel as authorization. Every action callback must re-resolve capability at execution time.

### Registry/hub metadata

- `utils.subsystem_registry.SUBSYSTEMS` is a platform manifest in dict form. It contains display names, descriptions, emoji, color, visibility tier/mode, category, tags, entry points, default channels, dependencies, cleanup support, UI priority, parent hub, hub group, and capabilities.
- `validate_registry()` freezes and validates structure, including capability namespace and hub relationships.
- `utils.hub_registry.HubEntry` adds a more UI-specific hub catalogue with routes, labels, audience tiers, and presentation metadata.
- Rebuild lesson: merge these into typed manifests rather than split metadata between raw dicts, hub registry, help catalogue, command aliases, and panel code.

### Help projection/discoverability

- `help_catalogue.build_help_catalogue()` builds registry-backed rows for hubs/subsystems and findings.
- `help_projection.project_help()` and `project_help_with_execution()` apply governance, execution, overlay, and orphaned override decisions into a reason-coded `HelpProjection`.
- `help_overlay` provides cached guild presentation overlays and `home_embed_frame()` for home-message framing; `help_overlay_mutation` owns audited hide/rename/description/home-message changes.
- `cogs/help/route.py` provides `HelpRoute`, `HelpOpener`, route resolution, single-command embeds, not-found embeds, and `open_route()`.
- `cogs/help/panels.py.HelpCategoryView` is a persistent Help category selector.

### Settings/bindings/resource provisioning

- `core.runtime.subsystem_schema` defines `SettingSpec`, `BindingSpec`, `ResourceRequirement`, `DomainPanelSpec`, and `SubsystemSchema`.
- `settings_resolution` is the typed read path for scalar settings with default/coercion/provenance and diagnostics counters.
- `settings_mutation.SettingsMutationPipeline` is the central scalar write path: resolves spec, checks authority/capability, coerces/validates, writes, invalidates, audits.
- `binding_mutation.BindingMutationPipeline` is the central binding write path: validates kind, checks capability/admin floor, writes binding rows, invalidates/audits.
- `resource_provisioning.ResourceProvisioningPipeline` previews and applies resource creation/reuse through declared resource requirements and binding specs; confirmation is mandatory for mutation.
- `binding_backfill` maps legacy setting IDs into binding rows with dry-run/apply classification and advisory locks.
- `views/settings` provides the operator UI grammar for typed settings: hub, subsystem summary, invalid settings, missing bindings, audit, bool toggle, text/number modals, enum select, role/channel selects, numeric presets, reset button, and related domain panels.

### Shared UI primitives

- `BaseView` standardizes invoker restriction, public panels, timeout disabling, error handling, `message` tracking, and standard navigation attachment.
- `HubView` standardizes hub timeout.
- `PersistentView` standardizes restart-safe component registration.
- `views.navigation` centralizes back-button attachment, Help/home/back-to-hub nav IDs, Help navigation attachments, BackTarget composition, component-cap warnings, safe defer/edit, and fallback errors.
- `views/selectors` centralizes channel/role/subsystem/scope/multi-select helpers, but the architecture warning list still shows duplicate direct select views in settings/channel/list panels.

### Diagnostics/health/observability

- `diagnostics_service` is a synchronous registry: `register`, `unregister`, `snapshot`, `snapshot_all`, `registered_names`, `_reset_for_tests`.
- `health_contracts` defines `SnapshotStatus`, `FindingSeverity`, `HealthAudience`, `OperationalHealthFinding`, `SubsystemHealth`, `HealthSnapshot`, `HealthSnapshotRequest`, and status derivation.
- `health_snapshot_service` composes runtime, tasks, diagnostics, errors, consistency, startup, extensions, AI, gateway, database, resource, and health-finding facts. It has cached and async collection lanes, `_safe`/`_safe_async` provider isolation, audience projection, redaction, grouping, and payload serialization.
- `health_findings_service` owns persistent operational findings: record, list, count, status transitions, retention, and audit event fan-out on transition.

## 4. Best ideas/functions to preserve

| Item | Problem solved | New-repo value | Disposition | Hidden dependencies / migration risks |
|---|---|---|---|---|
| `views.base.BaseView` | Standard invoker lock, timeout disable, error handling, nav attach | Essential UI lifecycle baseline | Copy idea; redesign as `PanelRuntimeView` around specs | Depends on `views.navigation`, `config.is_platform_owner`, Discord message edit behavior |
| `views.base.HubView` | Repeated hub timeout/defaults | Useful hub convention | Copy nearly as-is after spec integration | Hub vs child panels still inconsistent |
| `views.base.send_panel` | Binds sent message to view for timeout edit | Avoids lost message reference | Copy idea | Only command-context send; interactions need parallel path |
| `views.base.handle_view_error` | Logs rich context and sends generic ephemeral | Good global error UX | Copy idea | Some specialized views bypass for admin details |
| `views.navigation.attach_back_button` | Central back button with cap guard/defer/edit/fallback | High-value navigation primitive | Redesign into `NavigationSpec`/`ActionSpec` | Parent builders are closures, cannot persist; custom IDs must be stable |
| `views.navigation.attach_standard_nav` | Never-stranded Help/back-to-hub controls | Core discoverability contract | Preserve | Requires correct `SUBSYSTEM`, `parent_hub`, Help route availability |
| `views.navigation.BackTarget` / `chain_back` | Composable ad-hoc back stack without router | Valuable transitional pattern | Redesign into serializable nav stack | Closure state cannot survive restarts |
| `core.runtime.interaction_helpers.safe_defer` | Avoids Discord 3-second failure | Essential | Copy nearly as-is | Must be universally adopted; modal flows may need variants |
| `safe_followup` / `safe_edit` | Response/followup/edit routing and token failure handling | Essential | Copy idea | Attachment clearing and ephemeral behavior must be modeled |
| `clamp_embed` | Prevents Discord embed-limit hard failures | Essential embed frame primitive | Redesign as `EmbedFrame` validator | Discord limits are platform-specific and may change |
| `core.runtime.persistent_views.PersistentView` | Restart-safe UI component contract | Essential | Copy idea with typed registration metadata | Static `custom_id`s are persisted API; cannot rename casually |
| `core.runtime.lifecycle` | Process phase/admission/shutdown state | Essential | Copy nearly as-is | Metrics labels, command gating, shutdown semantics |
| `core.runtime.tasks.spawn` | Strong refs, outcomes, cancellation, diagnostics | Essential | Copy idea as managed task service | Naming convention is informal; make typed |
| `core.events.EventBus` | In-process fact fan-out with isolation | Valuable | Redesign around typed events | Event names/payload shapes currently stringly typed |
| `core.events_catalogue.KNOWN_EVENTS` | Event name inventory | Valuable | Redesign as `AuditEventSpec/EventSpec` | Wiring map warnings indicate catalogue/subscriber drift risk |
| `utils.subsystem_registry.SUBSYSTEMS` | Central subsystem metadata/capabilities | Essential | Redesign as typed `SubsystemManifest` | Keys are persisted across DB, help, routing, settings, governance |
| `core.runtime.subsystem_schema.SettingSpec` | Typed scalar settings declaration | Essential | Preserve and fold into manifest | `settings_key` constants and KV schema are hidden dependencies |
| `BindingSpec` | Typed Discord-resource pointer declaration | Essential | Preserve | Binding kind/table assumptions; legacy backfill |
| `ResourceRequirement` / provisioning specs | Declared resources for preview/apply | Essential | Preserve as `ResourceSpec` | Discord permission/order/idempotency, binding link |
| `DomainPanelSpec` | Makes non-scalar config discoverable in Settings | Important | Preserve | Discovery-only; mutation authority remains elsewhere |
| `settings_resolution.resolve_value` | Typed setting read with defaults/provenance | Essential | Copy idea | Consumers rely on declared defaults and coercion shape |
| `SettingsMutationPipeline` | Central scalar write with auth/audit/cache | Essential | Redesign as `ActionSpec` executor | Direct DB writes must be prohibited; actor type assumptions |
| `BindingMutationPipeline` | Central binding write with kind/auth/audit | Essential | Redesign as `BindingAction` executor | Discord object kind validation; binding table schema |
| `ResourceProvisioningPipeline.preview/apply` | Confirmation-first provisioning | Essential | Preserve idea | Needs permission checks, partial failure model, audit and retries |
| `help_catalogue.build_help_catalogue` | Registry-to-help read model | Essential | Preserve | Depends on subsystem registry, command discovery, aliases |
| `help_projection.HelpProjection` | Reason-coded help visibility/render model | Essential | Preserve | Overlay/gov/execution state and orphaned overrides |
| `help_overlay.home_embed_frame` | Central Help home presentation frame | Useful | Redesign as `EmbedFrame` | Default byte-identical tests may pin content |
| `help_overlay_mutation` | Audited presentation customization | Essential | Preserve lane | DB migration/table and audit event assumptions |
| `governance.capability.actor_holds_capability` | Capability gate for mutations | Essential | Preserve idea | Empty capability = admin floor in pipelines; do not reinterpret |
| `governance.writes.GovernanceMutationPipeline` | Sole governance mutation owner | Essential | Preserve | Scope/version/cache/audit semantics |
| `diagnostics_service.register/snapshot_all` | Lightweight provider registry | Useful | Redesign as typed providers | Sync-only registry; health has async lane separately |
| `health_snapshot_service.collect_snapshot` | Composed operator health snapshot | Essential | Preserve idea | Redaction, provider isolation, audience gates |
| `health_findings_service.set_status` | Operator-managed finding lifecycle | Useful | Preserve | Audit event names and DB migration 057 |
| `ChannelLifecycleService` / `RoleLifecycleService` | Discord resource lifecycle previews/results | Valuable | Preserve | Discord API permissions and idempotency assumptions |

## 5. UI grammar extraction

### Hub panels

Current patterns:

- Hub classes usually extend `HubView` and declare `SUBSYSTEM`, e.g. settings hub, diagnostic platform panel, economy/community/server-management hubs.
- Hubs typically render an embed plus a view with buttons/selects for child panels.
- Help can open many hubs through `build_help_menu_view` hooks or route openers.
- Hub metadata is split across `SUBSYSTEMS`, `hub_registry`, command docs, Help route code, and individual view classes.

Consistent:

- Hub timeout is usually 180 seconds through `HubView`.
- `BaseView` auto-navigation increasingly ensures Help/back-to-hub controls.
- Hubs are often invoker-locked unless intentionally public.

Fragmented:

- Some hubs still use direct `discord.ui.View` or bespoke command-context builders.
- Hub opener return shapes vary: some return `(embed, view)`, some send directly, some require `ctx`, some accept `interaction`.

### Child panels

Current patterns:

- Child panels are usually `BaseView`/`HubView` descendants with back buttons added externally or auto-attached by `SUBSYSTEM`.
- Settings child panels include `SubsystemSettingsView`, `InvalidSettingsView`, `MissingBindingsView`, `RecentChangesView`.
- Diagnostic subviews render sections of the health/diagnostics state.

Consistent:

- Increasing use of `safe_defer` + `safe_edit` for in-place transitions.
- Back buttons rebuild parents at click time, which is correct for governance/state freshness.

Fragmented:

- Parent/back builders are closures and not serializable.
- Some child panels have custom back buttons (`settings_missing_bindings.back`, `settings_invalid.back`, `settings_subsystem.back_to_hub`) while standard nav uses `nav:*` IDs.

### Persistent panels

Current patterns:

- `PersistentView` is used when controls must survive restarts; Help category selector is an example.
- Static `custom_id`s are required for every component.

Consistent:

- Contract is well documented in `persistent_views.py`.

Fragmented/hazard:

- Persistent `custom_id` strings are effectively API. They are spread across view code and not centrally inventoried.
- Closure-backed navigation cannot persist.

### Buttons

Current patterns:

- Buttons encode actions directly in callbacks.
- Back/help/home buttons use `views.navigation` or local button classes.
- Destructive/confirmation buttons use custom short-timeout views in several areas.

Consistent:

- `attach_back_button()` handles defer/build/edit/fallback consistently where adopted.
- `BaseView` handles invoker lock and timeout disable.

Fragmented:

- Button labels, rows, custom IDs, authority checks, and result messages vary by feature.
- Some buttons still implement direct `interaction.response` calls instead of helper functions.

### Selects

Current patterns:

- Shared selector helpers: `views/selectors/channel.py`, `role.py`, `subsystem.py`, `multi.py`, `multi_channel.py`, `multi_role.py`, `scope.py`.
- Settings hub uses `_SubsystemSelect` and page buttons for >25 options.
- Settings editor dispatch uses enum select, role/channel selects, numeric presets, and reset selects.

Consistent:

- Discord 25-option/component limits are recognized.
- Settings hub paginates actionable groups.

Fragmented:

- There are duplicate direct select views (`LogChannelSelectView`, `ChannelSettingSelectView`, role/channel setting views) flagged by architecture checks.
- Select option building and empty-state behavior are not yet a single `SelectorSpec`.

### Modals

Current patterns:

- Settings text and number editors use `discord.ui.Modal` (`TextSettingModal`, `NumberSettingModal`).
- Modal callbacks write through `SettingsMutationPipeline` and refresh parent panels.

Consistent:

- Typed `SettingSpec` controls modal routing.

Fragmented:

- Modal result rendering and parent refresh are per-widget helper functions.
- Modal validation UX is not expressed as a shared `ActionSpec` result.

### Back/help/home navigation

Current patterns:

- `BaseView` auto-attaches standard Help and back-to-hub controls when `SUBSYSTEM` is set and `STANDARD_NAV` is true.
- `views.navigation` defines `NAV_HELP_ID`, `NAV_HUB_ID_PREFIX`, `BackTarget`, `attach_back_button`, `chain_back`, and Help attachment forwarding.
- Legacy local back buttons still exist in Help, settings, games, logging, and admin areas.

Consistent:

- The desired contract is clear: no panel should strand a user away from Help or mother hub.

Fragmented:

- There are several local custom IDs and local back button classes; not all panels express their parent through a central `NavigationSpec`.

### Pagination

Current patterns:

- Settings hub paginates groups past Discord's 25-option cap.
- Diagnostic and list panels have bespoke pagination or dense embeds.
- Architecture warnings include `_ChannelListPaginatorView` directly extending `discord.ui.View`.

Consistent:

- Discord limits are known and guarded in several places.

Fragmented:

- No single `PaginatedSelectorSpec` or `ListSpec/TableSpec` owns pagination, empty states, page labels, and bounds.

### Confirmation/destructive flows

Current patterns:

- Resource provisioning requires preview + confirmation before applying.
- Lifecycle services return preview/result shapes.
- Destructive admin/setup operations often use local short-timeout confirmation views.

Consistent:

- The provisioning lane has the best preview/confirm/apply/audit pattern.

Fragmented:

- Confirmation UX is not one reusable primitive; button labels, timeout, authority re-check, and audit result rendering differ.

### Error and timeout handling

Current patterns:

- `BaseView.on_error` uses `handle_view_error`.
- `PersistentView.on_error` also delegates to shared error handling.
- `safe_defer`/`safe_followup`/`safe_edit` handle token and HTTP failures.
- `BaseView.on_timeout` disables controls and edits the bound message.

Consistent:

- The platform has a clear error doctrine and logs rich interaction context.

Fragmented:

- Some specialized direct `discord.ui.View` classes bypass shared handling.
- Channel-management views intentionally expose error type to admins; this should become an explicit error policy, not a divergence.

### Public vs ephemeral behavior

Current patterns:

- `BaseView(public=False)` locks panels to author; `public=True` allows shared panels.
- Help/settings/admin callbacks often send ephemeral fallback messages.
- Slash/status parity surfaces are often ephemeral.

Consistent:

- Invoker lock is centralized.

Fragmented:

- Public/ephemeral policy is implicit per call. A future `PanelSpec` should declare visibility, audience, whether the anchor is public, and whether errors/results are ephemeral.

## 6. Future new-repo primitive proposal

| Primitive | What it should mean | Current files proving need |
|---|---|---|
| `SubsystemManifest` | Typed manifest for subsystem key, display, category, capabilities, entry points, hubs, panels, settings, bindings, resources, events, diagnostics | `utils/subsystem_registry.py`, `core/runtime/subsystem_schema.py`, `utils/hub_registry.py`, `services/help_catalogue.py`, `governance/*` |
| `PanelSpec` | Declarative panel identity, owner subsystem, audience, anchor/public policy, renderer, actions, selectors, navigation | `views/base.py`, `views/settings/hub.py`, `views/settings/subsystem_view.py`, `views/diagnostic/platform_panel.py`, hub views |
| `EmbedFrame` | Safe embed renderer with title/description/fields/footer/image budgets and style tokens | `interaction_helpers.clamp_embed`, `help_overlay.home_embed_frame`, many embed builders |
| `TableSpec` / `ListSpec` | Bounded table/list rendering with pagination and truncation | diagnostic panels, settings audit/missing/invalid embeds, channel list paginator |
| `ActionSpec` | Button/modal action contract: label, custom_id, capability, defer mode, handler, result renderer, audit event | `attach_back_button`, settings edit/reset widgets, provisioning apply, governance writes |
| `NavigationSpec` | Help/home/back/parent/child routes, serializable stack behavior, persistent custom IDs | `views/navigation.py`, `BaseView.SUBSYSTEM`, `parent_hub`, Help routes |
| `SelectorSpec` | Select menu options, pagination, selected state, empty state, callback result | `views/selectors/*`, settings hub `_SubsystemSelect`, enum/select setting editors |
| `SettingSpec` | Typed scalar config declaration | `core/runtime/subsystem_schema.py`, `settings_resolution.py`, `settings_mutation.py`, `views/settings/*` |
| `BindingSpec` | Typed Discord resource pointer declaration | `subsystem_schema.py`, `binding_mutation.py`, `binding_backfill.py`, missing bindings UI |
| `ResourceSpec` | Provisionable Discord resource requirement with preview/apply/link semantics | `core/runtime/resource_specs.py`, `services/resource_provisioning.py`, lifecycle services |
| `ConfirmationSpec` | Preview/confirm/cancel/apply grammar for destructive/provisioning flows | `resource_provisioning.py`, `services/lifecycle/contracts.py`, setup/provisioning views |
| `WorkflowResult` | Common mutation result: status, before/after, audit/event/cache flags, warnings, user message | `SettingsMutationResult`, `BindingMutationResult`, `ProvisioningResult`, `LifecycleResult`, `TransitionResult` |
| `MutationPreview` | Dry-run/preview object for settings bundles, provisioning, lifecycle/setup operations | `ProvisioningPreview`, `LifecyclePreview`, binding backfill `DryRunSummary`, setup operations |
| `AuditEventSpec` | Event name, payload shape, owner, persistence/audit behavior | `core/events_catalogue.py`, `services/audit_events`, mutation pipelines, health findings transitions |
| `DiagnosticProviderSpec` | Provider name, sync/async lane, timeout, status mapping, audience/redaction | `diagnostics_service.py`, `health_contracts.py`, `health_snapshot_service.py` |
| `ManagedTaskSpec` | Task name, subsystem, cancellation prefix, error hook, metrics labels | `core/runtime/tasks.py`, lifecycle shutdown cleanup |
| `PanelContext` | Explicit context replacing command-ctx shims: bot, guild, actor, channel, interaction/message anchor, audience | `interaction_helpers.help_ctx_shim`, Help openers, hub builders |

## 7. Hidden dependencies and rebuild hazards

### Persisted subsystem keys

- Keys in `utils.subsystem_registry.SUBSYSTEMS` are used by governance, help projection, settings schemas, bindings, resource requirements, command ledgers, diagnostics, and tests.
- Examples: `admin`, `server_management`, `moderation`, `economy`, `inventory`, `treasury`, `ticket`, `mining`, `settings`, `diagnostic`, `help` and many more.
- Hazard: renaming keys breaks DB rows, overlay rows, settings groups, Help overrides, governance policies, and capability strings.

### Persistent `custom_id` strings

Known examples from inspected scope:

- Standard nav: `nav:help`, `nav:hub:<subsystem>`.
- Help: `help:back`, `help_categories:select`.
- Settings hub: `settings_hub.subsystem_select`, `settings_hub.page_prev`, `settings_hub.page_next`, `settings_hub.needs_setup`, `settings_hub.invalid`, `settings_hub.missing_bindings`, `settings_hub.audit`, `settings_hub.command_access`.
- Settings children: `settings_missing_bindings.back`, `settings_invalid.back`, `settings_subsystem.back_to_hub`, `settings:back`, `settings_subsystem.open_panel`, edit/reset selects.
- Hazard: persistent/restart-safe views and Discord interaction routing depend on stable IDs. A rebuild needs an inventory and compatibility policy.

### Event names and payload shapes

- `core.events_catalogue.KNOWN_EVENTS` and `scripts/wiring_map.py --check` are current safeguards.
- EventBus payloads are kwargs without a typed schema. Mutation result flags such as `event_emitted` mean publish-accepted only.
- Hazard: a fresh repo could silently drop subscribers or change payload names unless events are typed and tested.

### DB schema assumptions

- Settings rely on canonical `utils/settings_keys` constants and KV rows.
- Bindings rely on `subsystem_bindings` semantics and legacy backfill classification.
- Help overlay relies on its overlay table/migration and cached row model.
- Health findings rely on migration 057 and finding fingerprint/status retention semantics.
- Resource provisioning and audit checks rely on audit tables and CHECK constraints widened in later migrations.

### Runtime session/anchor assumptions

- `BaseView.message` must be set for timeout disabling.
- `safe_edit`/navigation assumes an interaction has an editable original/anchor.
- `BackTarget` closure stacks are intentionally non-persistent.
- Persistent views must be re-registered at startup with static custom IDs.

### Governance visibility/capability assumptions

- Visibility and execution are distinct. A subsystem can be shown/hidden separately from command/action capability.
- Empty `capability_required` in setting/binding specs is treated as administrator floor, not anonymous access.
- Callback authority must be rechecked at execution time.
- Platform owner bypass exists via `config.is_platform_owner` and admin helpers.

### Help overlay/customization state

- Overlay can hide/rename/re-describe Help entries and customize home messages.
- Projection handles orphaned overrides.
- Hazard: rebuilding Help from command introspection alone loses guild-specific presentation state and operator expectations.

### Test/invariant assumptions

- Architecture checker currently allows warnings but no errors; warning classes are living debt inventory.
- Wiring map requires event wiring consistency but flags advisory possible dead subscribers.
- Settings declared-vs-consumed parity and settings reachability guards are documented current-state invariants.
- BaseView inheritance warnings are an explicit conformance ratchet.

## 8. Fragmentation inventory

### Critical rebuild lesson

- **Metadata split across registries and code.** `SUBSYSTEMS`, `SubsystemSchema`, `hub_registry`, Help route/openers, command decorators, settings views, and docs all contain pieces of one subsystem manifest. Rebuild with `SubsystemManifest` first.
- **Navigation is partly central, partly local.** `views.navigation` is correct direction, but local back buttons remain in Help/settings/games/logging/admin patterns. Rebuild with serializable `NavigationSpec` and generated standard controls.
- **Action callbacks are not centrally specified.** Settings widgets, provisioning confirmations, governance buttons, and hub buttons repeat defer/auth/mutate/audit/render code. Rebuild with `ActionSpec` and `WorkflowResult`.
- **Persistent IDs are not centrally inventoried.** Stable `custom_id`s are spread through source. Rebuild with a custom-id registry and compatibility tests.

### Important improvement

- **Direct `discord.ui.View` inheritance remains.** `check_architecture.py --mode strict` warns on `_DuelView`, `_ChallengeView`, `LogChannelProvisionView`, `LogChannelSelectView`, `_DisabledHelpHookView`, `BTD6AdminView`, `StrategyReviewView`, `_ChannelListPaginatorView`, `ChannelSettingSelectView`, `NumericPresetsView`, `RoleSettingSelectView`, `SetupLauncherView`, `_RankView`. Some are acceptable specialization; some are platform debt.
- **Layer-boundary warnings remain known debt.** Core imports services in runtime modules; governance imports services; utils imports core/services in DB helpers. A clean repo can avoid much of this by making runtime ports explicit.
- **Raw SQL warnings remain in service files.** `automation_scheduler.py` and `binding_backfill.py` still contain known raw SQL/pool primitive warnings. A future repo should enforce db-access owners from day one.
- **Help opener context shims indicate old command-first surfaces.** `help_ctx_shim()` is practical but proves the need for `PanelContext`.

### Cleanup

- Consolidate selector option builders into `SelectorSpec`.
- Consolidate settings edit parent-refresh helpers.
- Replace per-panel back button classes with generated navigation controls.
- Inventory all custom IDs and event names into generated docs/tests.
- Replace one-off embed/list truncation with `EmbedFrame`/`ListSpec`.

### Acceptable specialization

- Game-state views may extend `discord.ui.View` directly when tightly coupled to gameplay lifecycle, timeout cleanup, or transient challenge state. The current `BaseView` doctrine already allows this if documented.
- Channel-management views may expose richer admin error details, but that should be an explicit `ErrorPolicy.ADMIN_DIAGNOSTIC` rather than a hidden custom `on_error`.
- Dense domain panels can keep custom renderers if they still declare `PanelSpec`, `NavigationSpec`, and action metadata.

## 9. Minimum foundation a fresh repo should start with

Before recreating any feature cogs, a clean SuperBot repo should have this platform kernel:

1. **Typed `SubsystemManifest` registry** with stable keys, display metadata, capabilities, command surfaces, panel surfaces, settings, bindings, resources, events, diagnostics, and help entries.
2. **Governance/capability service** with visibility vs execution separation, member/role tiers, scope chain, callback-time capability checks, cache invalidation, and audited mutation pipeline.
3. **Runtime lifecycle service** with phases, command admission gate, graceful shutdown/restart intents, managed task registry, metrics, and diagnostics provider.
4. **Typed EventBus/audit catalogue** with event names, payload schemas, owner, subscriber wiring checks, publish-accepted semantics, delivery stats, and audit fan-out.
5. **UI platform grammar**: `PanelSpec`, `ActionSpec`, `NavigationSpec`, `SelectorSpec`, `ConfirmationSpec`, `EmbedFrame`, `ListSpec/TableSpec`, `PanelContext`, `WorkflowResult`.
6. **Discord interaction helpers** for defer/followup/edit, embed/file limits, ephemeral/public policy, timeout/error behavior, and persistent-view registration.
7. **Help/discoverability projection** from manifests + governance + overlay state, including routes to panels and commands.
8. **Settings/bindings/resources lanes** with typed read models, mutation pipelines, preview/confirm provisioning, cache invalidation, audit, and tests.
9. **Diagnostics/health layer** with typed provider specs, cached/async lanes, redaction/audience projection, persistent findings, and startup snapshot.
10. **Invariants/checkers from day one**: architecture/layering, direct-view conformance, settings declared⇔consumed, event wiring, custom-id uniqueness, command/help reachability, and docs/report path checks.

## 10. Handoff to other mapping sessions

### Admin/safety session should verify

- Whether moderation, automod, cleanup, logging, channel, role, ticket, setup, and server-management panels re-check governance/capability at callback execution time.
- Which admin/safety views still directly extend `discord.ui.View` for acceptable specialization vs avoidable BaseView debt.
- Whether destructive admin actions follow preview/confirmation/audit semantics comparable to resource provisioning.
- Governance event payloads, audit event names, and permission tiers used outside this platform scope.

### Community/games session should verify

- Which game/community hubs can be expressed as `PanelSpec`/`ActionSpec` and which game-state views require direct specialized `discord.ui.View`.
- Whether economy/inventory/mining/treasury/community panels use service-owned mutations and standard navigation.
- Any duplicate pagination/select/list patterns in game leaderboards, inventories, shops, matchmaking, and BTD6 browsers that should become `ListSpec`/`SelectorSpec`.
- Persistent custom IDs and session state in game flows.

### AI/data/tooling session should verify

- AI runtime/tool orchestration manifests that resemble `SubsystemManifest`, `ActionSpec`, or `DiagnosticProviderSpec`.
- AI-memory substrate assumptions that should plug into EventBus, diagnostics, settings, Help projection, or control-plane manifests.
- Whether tool catalogues, answerability projections, and data-source freshness metadata can share the same discovery grammar as Help/diagnostics.
- Static checks that should become mandatory in a fresh repo: architecture, wiring map, settings parity, custom IDs, docs consistency, and CodeGraph coverage.
