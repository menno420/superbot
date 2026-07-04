# Health / Diagnostics production-readiness map — 2026-06-12

> **Status:** `historical` — source-verified production-readiness map; update after the next live verification session.
> **Superseded 2026-06-19 (was active):** Superseded — the P1-2 findings-lifecycle gaps closed #843. Live spine: hardening-roadmap. Do not act on this — current map: [planning/README](../README.md).
>
> **Mode:** docs-only source mapping and production-readiness review. No reported
> execution-subsystem bug is reclassified as a Health / Diagnostics bug unless the
> reporting path itself is wrong.
>
> **Verdict:** **Partial** (improving). The deterministic health contracts, isolated
> snapshot aggregator, provider registry, consistency report, persistent findings schema,
> and principal Discord/AI read surfaces are implemented and heavily unit-tested.
> **P1-2 closed the two code gaps (2026-06-14):** the persisted finding lifecycle now has a
> sole-writer operator transition path (`set_status` + `!platform finding`, Q-0097) and
> retention runs on a long-lived daily loop, not startup-only. The remaining gap to
> production-ready is the **maintainer live-verification debt** recorded by the canonical
> folio (the live Discord/AI walk — owner-led).

## Current verified state

- Source reviewed at repository HEAD on **2026-06-12**. Source and merged PRs win over
  roadmap wording.
- Live GitHub check on **2026-06-12** found one open PR, [#704](https://github.com/menno420/superbot/pull/704),
  “Screenshots from live testing the bot.” Its changed files do not touch Health /
  Diagnostics, so it does not change this review's claims.
- Relevant recent merged PRs checked: [#650](https://github.com/menno420/superbot/pull/650)
  (honest diagnostics registry/provider semantics), [#553](https://github.com/menno420/superbot/pull/553)
  (SKIPPED consistency presentation), [#548](https://github.com/menno420/superbot/pull/548)
  (real-Postgres migration/findings tests), [#547](https://github.com/menno420/superbot/pull/547)
  (integration-gap scope), [#541](https://github.com/menno420/superbot/pull/541)
  (grouped errors, AI tool, persistent findings), [#537](https://github.com/menno420/superbot/pull/537)
  (health model/aggregator/commands/startup snapshot), [#263](https://github.com/menno420/superbot/pull/263)
  (lifecycle/runtime-lock providers), [#248](https://github.com/menno420/superbot/pull/248)
  (readiness snapshot), and [#88](https://github.com/menno420/superbot/pull/88)
  (unified consistency report).
- Targeted Health / Diagnostics / platform / smoke / consistency unit selection completed locally: **451 passed, 9 skipped** (the skips are environment-gated integration cases).
- The canonical architecture is coherent: one synchronous provider registry
  (`diagnostics_service`), one typed health aggregator (`health_snapshot_service`),
  one persistent findings writer (`health_findings_service`), and one platform
  consistency collector (`platform_consistency`). No second aggregator or store is
  needed.
- The health snapshot is a reporting layer. Resource, role, setup, AI-provider,
  database, startup, extension, gateway, and consistency failures remain bugs or
  operational conditions in their owning subsystems unless the adapter misreports
  them.

### Readiness scale used here

| State | Meaning |
|---|---|
| **Done** | Implemented in source with a coherent owner/boundary and relevant automated coverage. |
| **Partial** | Implemented, but missing live proof, complete exposure, lifecycle, smoke coverage, or a promised observability/control seam. |
| **Not Done** | Required or claimed capability has no implementation path. |

## Scope inventory table

### Contracts, aggregation, and health snapshot paths

| Item | Path | Type | State | Reason | Evidence |
|---|---|---|---|---|---|
| Typed health contracts and deterministic status folding | `disbot/services/health_contracts.py` | contract | **Done** | Frozen audience/status/finding/subsystem/snapshot/request models and deterministic severity/status helpers exist. | `health_contracts.py:28-248`; `tests/unit/services/test_health_snapshot_service.py` |
| Cached process-local snapshot lane | `disbot/services/health_snapshot_service.py::collect_cached_snapshot` | snapshot path | **Done** | Sync lane composes only cached/process-local adapters and audience-projects the result. | `health_snapshot_service.py:952-985` |
| Async live snapshot lane | `disbot/services/health_snapshot_service.py::collect_snapshot` | snapshot path | **Done** | Adds isolated, timeout-bounded DB, optional fresh consistency, and optional guild-resource checks. | `health_snapshot_service.py:987-1046`; timeout/isolation tests |
| Runtime adapter | `health_snapshot_service.py::_runtime_subsystem` | snapshot provider | **Done** | Maps lifecycle phase and failed-startup finding. | `health_snapshot_service.py:170-203` |
| Tasks adapter | `health_snapshot_service.py::_tasks_subsystem` | snapshot provider | **Partial** | Reports active count as healthy but does not inspect terminal/recent task failures despite roadmap language describing recent task failure degradation. | `health_snapshot_service.py:205-218`; plan §3.3 |
| Diagnostics-registry adapter | `health_snapshot_service.py::_diagnostics_subsystem` | snapshot provider | **Done** | Aggregates all registered providers and turns isolated `_error` payloads into bounded findings. | `health_snapshot_service.py:220-258` |
| Grouped recent-errors adapter | `health_snapshot_service.py::_errors_subsystem` | snapshot provider | **Partial** | Implemented and opt-in via `HEALTH_GROUPED_FINDINGS`, but the canonical folio still records a maintainer live-test debt. | `health_snapshot_service.py:260-321`; `docs/subsystems/health-diagnostics.md:96-101` |
| Cached consistency adapter | `health_snapshot_service.py::_consistency_subsystem` | snapshot provider | **Done** | Reuses the one readiness cache and correctly separates actionable WARNING/FATAL from benign SKIPPED sections. | `health_snapshot_service.py:323-402`; PR #553 |
| Startup outcomes adapter | `health_snapshot_service.py::_startup_subsystem` | snapshot provider | **Done** | Maps recorded startup outcomes into bounded findings. | `health_snapshot_service.py:404-436` |
| Extension-load adapter | `health_snapshot_service.py::_extensions_subsystem` | snapshot provider | **Done** | Distinguishes required bootstrap-access failure from optional extension degradation. | `health_snapshot_service.py:438-485` |
| AI adapter | `health_snapshot_service.py::_ai_subsystem` | snapshot provider | **Partial** | Correctly treats AI as optional and reports degradation; production AI-path live verification remains owed. | `health_snapshot_service.py:487-532`; `docs/subsystems/health-diagnostics.md:94-101` |
| Gateway adapter | `health_snapshot_service.py::_gateway_subsystem` | snapshot provider | **Done** | Reports readiness, latency, guild count, and unavailable guilds without making gateway optional. | `health_snapshot_service.py:534-577` |
| Database adapter | `health_snapshot_service.py::_database_subsystem` | snapshot provider | **Done** | Bounded async ping drives a required critical status when unreachable. | `health_snapshot_service.py:579-592` |
| Fresh consistency adapter | `health_snapshot_service.py::_fresh_consistency_subsystem` | snapshot provider | **Done** | Reuses `platform_consistency.collect_report`; no second consistency aggregator. | `health_snapshot_service.py:594-605` |
| Guild resource-health adapter | `health_snapshot_service.py::_resources_subsystem` | snapshot provider | **Done** | Reuses `resource_health.inspect`; guild-local failures degrade but never make whole-bot health critical. | `health_snapshot_service.py:607-653` |
| Per-source failure isolation | `health_snapshot_service.py::_safe`, `_safe_async` | reliability boundary | **Done** | A source exception/timeout cannot blank the complete snapshot. | `health_snapshot_service.py:655-711`; isolation tests |
| Finding grouping, bounds, ordering, and final status | `health_snapshot_service.py::_group_findings`, `_finalize`, `_overall_summary` | aggregation | **Done** | Stable bounded output and deterministic folding exist. | `health_snapshot_service.py:713-777` |
| Audience projection/redaction | `health_snapshot_service.py::project_for_audience`, `_project_*` | security boundary | **Done** | Pure owner/admin/public downscope is implemented and omission-tested. | `health_snapshot_service.py:779-837`; `test_health_redaction.py` |
| Bounded AI payload | `health_snapshot_service.py::snapshot_to_payload` | integration path | **Done** | Serializes only projected, allowlisted, bounded content. | `health_snapshot_service.py:839-909` |
| Startup snapshot cache and boot recording | `health_snapshot_service.py::record_startup_snapshot`; `disbot/bot1.py::_report_startup_health` | snapshot path | **Partial** | One-shot, managed, best-effort path exists; canonical docs still require a maintainer reconnect/startup live walk. | `health_snapshot_service.py:936-950`; `bot1.py:190-239`; folio live-test debt |
| Health collection/source/redaction metrics promised by plan | `metrics.py::health_snapshot_collection_seconds`, `health_snapshot_source_failure_total`, `health_snapshot_redaction_total` | observability | **Done** (2026-06-30, PR #1584) | The §3.6 collection-duration / source-failure / redaction-outcome metrics are implemented and wired at the snapshot seams (`collect_snapshot`/`collect_cached_snapshot` duration, `_safe`/`_safe_async` source-failure, `project_for_audience` redaction). | `docs/health/bot-awareness-implementation-plan.md:216`; `metrics.py`; `test_health_snapshot_metrics.py` |

### Diagnostics provider registry — every registered provider found in source

All providers below share the same status: **Done** as registered sync providers, with
one production caveat: a provider exists only after its owning module loads. Registry
truth therefore means “currently loaded providers,” not a static promised catalogue.
That corrected contract shipped in PR #650.

| Item | Path | Type | State | Reason | Evidence |
|---|---|---|---|---|---|
| `automation_scheduler` | `disbot/services/automation_scheduler.py` | provider | **Done** | Registered with the canonical registry. | `automation_scheduler.py:374` |
| `bindings` | `disbot/core/runtime/bindings.py` | provider | **Done** | Registered with the canonical registry. | `bindings.py:270` |
| `capability_map` | `disbot/core/runtime/subsystem_capabilities.py` | provider | **Done** | Registered with the canonical registry. | `subsystem_capabilities.py:112` |
| `command_descriptions` | `disbot/core/runtime/command_descriptions.py` | provider | **Done** | Registered with the canonical registry. | `command_descriptions.py:292` |
| `command_surface_ledger` | `disbot/core/runtime/command_surface_ledger.py` | provider | **Done** | Registered with the canonical registry. | `command_surface_ledger.py:765` |
| `config_arbitration` | `disbot/core/runtime/config_arbitration.py` | provider | **Done** | Registered with the canonical registry. | `config_arbitration.py:627` |
| `customization_catalogue` | `disbot/services/customization_catalogue.py` | provider | **Done** | Registered with the canonical registry. | `customization_catalogue.py:713` |
| `event_bus` | `disbot/core/events.py` | provider | **Done** | Registered with the canonical registry. | `events.py:195` |
| `feature_flags` | `disbot/core/runtime/feature_flags.py` | provider | **Done** | Registered with the canonical registry. | `feature_flags.py:812` |
| `governance_cache` | `disbot/governance/cache.py` | provider | **Done** | Registered with the canonical registry. | `governance/cache.py:164` |
| `guild_config` | `disbot/core/runtime/guild_config.py` | provider | **Done** | Registered with the canonical registry. | `guild_config.py:265` |
| `lifecycle` | `disbot/core/runtime/lifecycle.py` | provider | **Done** | Registered with the canonical registry. | `lifecycle.py:447` |
| `navigation_stack` | `disbot/core/runtime/navigation_stack.py` | provider | **Done** | Registered with the canonical registry. | `navigation_stack.py:151` |
| `participation_schemas` | `disbot/core/runtime/participation_schema.py` | provider | **Done** | Registered with the canonical registry. | `participation_schema.py:324` |
| `persistent_views` | `disbot/core/runtime/persistent_views.py` | provider | **Done** | Registered with the canonical registry. | `persistent_views.py:120` |
| `platform_readiness` | `disbot/services/platform_consistency.py` | provider | **Done** | Exposes the cached readiness snapshot through the canonical registry. | `platform_consistency.py:1256-1270` |
| `recent_errors` | `disbot/cogs/diagnostic_cog.py` | provider | **Partial** | Ring-buffer provider is registered only when DiagnosticCog setup runs; grouped-health use remains opt-in/live-unverified. | `diagnostic_cog.py:726-740` |
| `resource_provisioning_catalogue` | `disbot/services/resource_provisioning_catalogue.py` | provider | **Done** | Registered with the canonical registry. | `resource_provisioning_catalogue.py:317` |
| `resource_requirements` | `disbot/core/runtime/subsystem_schema.py` | provider | **Done** | Registered with the canonical registry. | `subsystem_schema.py:372` |
| `resources` | `disbot/core/resources/__init__.py` | provider | **Done** | Registered with the canonical registry. | `core/resources/__init__.py:106` |
| `runtime_lock` | `disbot/services/runtime.py` | provider | **Done** | Registered with the canonical registry. | `runtime.py:360` |
| `schemas` | `disbot/core/runtime/subsystem_schema.py` | provider | **Done** | Registered with the canonical registry. | `subsystem_schema.py:371` |
| `scope_locks` | `disbot/core/runtime/scope_locks.py` | provider | **Done** | Registered with the canonical registry. | `scope_locks.py:283` |
| `server_logging` | `disbot/services/server_logging.py` | provider | **Done** | Registered with the canonical registry. | `server_logging.py:884` |
| `settings_registry` | `disbot/core/runtime/settings_registry.py` | provider | **Done** | Registered with the canonical registry. | `settings_registry.py:266` |
| `settings_resolution` | `disbot/services/settings_resolution.py` | provider | **Done** | Registered with the canonical registry. | `settings_resolution.py:405` |
| `slow_path` | `disbot/core/runtime/slow_path_log.py` | provider | **Done** | Registered with the canonical registry. | `slow_path_log.py:141` |
| `tasks` | `disbot/core/runtime/tasks.py` | provider | **Done** | Registered with the canonical registry. | `tasks.py:190` |
| `user_capability_map` | `disbot/core/runtime/participation_capabilities.py` | provider | **Done** | Registered with the canonical registry. | `participation_capabilities.py:107` |
| `user_config` | `disbot/core/runtime/user_config.py` | provider | **Done** | Registered with the canonical registry. | `user_config.py:241` |
| Registry API: `register`, `unregister`, `snapshot`, `snapshot_all`, `registered_names` | `disbot/services/diagnostics_service.py` | aggregator | **Done** | One sync, hot-reload-friendly registry; failures isolate to `_error`; no I/O or mutation. | `diagnostics_service.py:67-132`; `test_diagnostics_service.py` |

### Persistent finding store and lifecycle

| Item | Path | Type | State | Reason | Evidence |
|---|---|---|---|---|---|
| Sole-writer service | `disbot/services/health_findings_service.py` | finding store owner | **Done** | Best-effort recording/list/count/retention boundary is isolated and metrics-backed. | `health_findings_service.py:1-116`; sole-writer invariant test |
| `record_findings` boot persistence | `health_findings_service.py::record_findings`; `bot1.py::_report_startup_health` | write path | **Partial** | Correctly persists startup-snapshot findings across boots, but no periodic/live snapshot persistence path exists; recurrence visibility is therefore boot-sampled. | `health_findings_service.py:31-70`; `bot1.py:220-235` |
| `list_by_status` and `count_by_status` | `health_findings_service.py` | read path | **Done** | Powers the typed findings command without bypassing the owner. | `health_findings_service.py:73-89` |
| Retention sweep | `health_findings_service.py::run_retention` | retention path | **Done** | Correct 30-day roll-up/prune logic runs at startup **and** on a daily `HealthMaintenanceCog._retention_loop` (P1-2), so long-lived replicas re-sweep. | `health_findings_service.py`; `cogs/health_maintenance_cog.py`; `bot1.py:228-235` |
| Finding lifecycle transitions (`open` → `resolved` / `ignored`) | `health_findings_service.py::set_status`; `diagnostic_cog.py::platform_finding` (`!platform finding`) | lifecycle | **Done** | Q-0097 (operator-managed): `set_status` is the sole transition path (DB primitive `set_finding_status`, pinned by the sole-writer AST guard); a real transition emits `audit.action_recorded`. `!platform finding resolve/ignore/reopen <fingerprint>` is the admin command. | migration `057`; `health_findings_service.py`; `cogs/diagnostic_cog.py` |
| DB primitives: upsert/list/count/roll-up/prune | `disbot/utils/db/health_findings.py` | DB primitives | **Done** | Pool-only primitives sit behind the sole writer and are real-Postgres integration-tested. | `health_findings.py:22-171`; PR #548 |
| `operational_health_findings` | `disbot/migrations/057_operational_health_findings.sql` | table | **Done** | Idempotent per-fingerprint durable detail store with bounded statuses and occurrence count. | migration `057`:38-60 |
| `operational_health_finding_aggregates` | `disbot/migrations/057_operational_health_findings.sql` | table | **Done** | Retention roll-up preserves bounded long-run counters. | migration `057`:62-69 |
| Findings metrics | `disbot/services/metrics.py` | observability | **Done** | Record and prune counters exist; no new event stream was added. | `metrics.py:139-149` |

### Platform consistency and readiness surfaces

| Item | Path | Type | State | Reason | Evidence |
|---|---|---|---|---|---|
| Unified consistency orchestrator | `disbot/services/platform_consistency.py::collect_report` | consistency aggregator | **Done** | One fail-safe orchestrator stamps typed kinds and caches the latest report. | `platform_consistency.py:219-286` |
| `identity_contract` | `platform_consistency.py::_collect_identity_contract` | consistency section | **Done** | Canonical typed section exists. | `ReadinessKind`; collector tuple |
| `feature_flags` | `platform_consistency.py::_collect_feature_flags` | consistency section | **Done** | Canonical typed section exists. | `ReadinessKind`; collector tuple |
| `rollout_audit` | `platform_consistency.py::_collect_rollout_audit` | consistency section | **Done** | Canonical typed section exists. | `ReadinessKind`; collector tuple |
| `bindings` | `platform_consistency.py::_collect_bindings` | consistency section | **Done** | Canonical typed section exists and may correctly SKIP without guild context. | `ReadinessKind`; folio debug router |
| `binding_backfill` | `platform_consistency.py::_collect_binding_backfill` | consistency section | **Done** | Canonical typed section exists; no checkpoints may correctly SKIP. | `ReadinessKind`; folio debug router |
| `config_arbitration` | `platform_consistency.py::_collect_config_arbitration` | consistency section | **Done** | Canonical typed section exists and preserves real unfinished-migration warnings. | `ReadinessKind`; folio debug router |
| `participation` | `platform_consistency.py::_collect_participation` | consistency section | **Done** | Canonical typed section exists. | `ReadinessKind`; collector tuple |
| `migrations` | `platform_consistency.py::_collect_migrations` | consistency section | **Done** | Canonical typed section exists. | `ReadinessKind`; collector tuple |
| `runtime_providers` | `platform_consistency.py::_collect_runtime_providers` | consistency section | **Done** | Checks loaded registry providers without inventing a second provider catalogue. | `platform_consistency.py:895`; collector tuple |
| `lifecycle` | `platform_consistency.py::_collect_lifecycle` | consistency section | **Done** | Canonical typed section exists. | `ReadinessKind`; collector tuple |
| `setup_readiness` | `platform_consistency.py::_collect_setup_readiness` | informational consistency section | **Done** | Uses the dynamic setup-blocker registry. | `platform_consistency.py:185-199`; collector tuple |
| `wizard_finalization` | `platform_consistency.py::_collect_wizard_finalization` | consistency section | **Done** | Canonical typed section exists. | `ReadinessKind`; collector tuple |
| `ReadinessSnapshot` and `platform_readiness` provider | `platform_consistency.py::build_readiness_snapshot`, `_readiness_snapshot_dict` | readiness snapshot | **Done** | Pure sync cached snapshot includes consistency, startup outcomes, catalogue build state, and managed tasks. | `platform_consistency.py:1113-1270` |
| Readiness ↔ smoke doc-test relation | `docs/smoke-test-checklist.md`; `tests/unit/docs/test_smoke_test_checklist.py` | drift guard | **Partial** | Field correspondence is pinned, but the checklist says to inspect nonexistent `!platform diagnostics`; actual routes are `!platform runtime` and `!platform consistency`. | smoke checklist lines 5-14; command list in `diagnostic_cog.py` |

### Cog, embed, and view surfaces

| Item | Path | Type | State | Reason | Evidence |
|---|---|---|---|---|---|
| General diagnostics commands: `diagnostics/diag`, `lifecycle/lc`, `list_commands_detailed`, `find_command`, `validate_json_files`, `check_database`, `diagnostic_bot_status`, `latency`, `system_info`, `query_logs`, `recent_errors`, `test_notification` | `disbot/cogs/diagnostic_cog.py` | cog commands | **Done** | Admin-gated operator routes exist and reuse shared builders. | `diagnostic_cog.py:68-264` |
| Cog integration helpers: `build_help_menu_view`, `build_platform_help_menu_view`, `governance_context_for`, `setup` | `disbot/cogs/diagnostic_cog.py`; `disbot/cogs/diagnostic/_platform_embeds.py` | cog functions | **Done** | Help integration, governance context, extension setup, and recent-error provider registration are explicit. `governance_context_for` moved to `_platform_embeds` to keep the cog under the 800-LOC ceiling. | `diagnostic_cog.py:87-148`; `_platform_embeds.governance_context_for` |
| Platform health commands: `platform health`, `startup`, `findings`, `runtime`, `consistency`, `lifecycle` | `disbot/cogs/diagnostic_cog.py` | cog commands | **Partial** | Typed routes exist, but `startup` and `findings` are omitted from the interactive Platform hub despite the hub claiming every existing subcommand is grouped. | `diagnostic_cog.py:334-425`; `platform_panel.py:1-105` |
| Other typed Platform routes: `status`, `setup-readiness`, `anchors`, `identity`, `caches`, `locks`, `tasks`, `views`, `slow`, `automation`, `sessions`, `schemas`, `settings-registry`, `setting`, `customization`, `provisioning`, `participation-schemas`, `resource-requirements`, `bindings`, `resources`, `flags`, `flag`, `migrations`, `command-access`, `access`, `cleanup-preview`, `counting-health` | `disbot/cogs/diagnostic_cog.py` | cog commands | **Done** | Routes exist; reported failures belong to their owning subsystems unless rendering/collection is wrong. | `diagnostic_cog.py:286-696` |
| Health/startup/findings renderers | `disbot/cogs/diagnostic/_platform_embeds.py::build_health_embed`, `build_startup_health_embed`, `build_findings_embed` | cog/view functions | **Done** | Shared bounded rendering exists; source snapshot is already projected. | `_platform_embeds.py:858-1000` |
| Consistency/readiness renderers | `_platform_embeds.py::build_consistency_embed`, `build_setup_readiness_embed` | cog/view functions | **Done** | Shared typed report renderers exist. | `_platform_embeds.py:398-494`, `1689-1790` |
| Remaining Platform render/read functions: `build_access_explainer_embed`, `build_cleanup_preview_embed`, `read_counting_save_outcomes`, `build_counting_health_embed`, `build_resources_embed`, `build_bindings_embed`, `build_schemas_embed`, `build_settings_registry_embed`, `build_setting_detail_embed`, `build_customization_embed`, `build_provisioning_embed`, `build_status_embed`, `build_runtime_embed`, `build_lifecycle_embed`, `build_caches_embed`, `build_locks_embed`, `build_tasks_embed`, `build_views_embed`, `build_slow_embed`, `build_sessions_embed`, `build_anchors_embed`, `build_identity_embed`, `build_participation_schemas_embed`, `build_resource_requirements_embed`, `build_flags_embed`, `build_migrations_embed`, `build_command_access_diagnostic_embed` | `disbot/cogs/diagnostic/_platform_embeds.py` | cog/view functions | **Done** | Render/read helpers are centralized; PR #650/#RS08 removed misleading or inline-SQL behavior. | `_platform_embeds.py`; relevant cog/DB tests |
| Platform render utilities: `_capped`, `_format_field_value`, `_estimated_embed_size`, `_health_block`, `_render_health_embed`, `_fmt_lifecycle_event_metadata`, `_fmt_snapshot_value`, `_render_health_findings` | `disbot/cogs/diagnostic/_platform_embeds.py` | cog/view functions | **Done** | Private formatting/bounding helpers support the shared embeds without collecting or mutating state. | `_platform_embeds.py` |
| General diagnostics builders: `build_hub_overview_embed`, `build_bot_status_embed`, `build_latency_embed`, `build_system_info_embed`, `build_check_database_embed`, `build_validate_json_embed`, `build_command_list_pages`, `build_query_logs_embed`, `build_test_notification_embed` | `disbot/cogs/diagnostic/_helpers.py` | cog/view functions | **Done** | Shared builders back both typed commands and hub callbacks. | `_helpers.py:44-448` |
| General diagnostics private formatter: `_format_table_set` | `disbot/cogs/diagnostic/_helpers.py` | cog/view function | **Done** | Bounded formatting helper stays local to diagnostic rendering. | `_helpers.py:170-194` |
| In-memory recent-error ring | `disbot/cogs/diagnostic/_log_buffer.py::_RingBufferHandler` | diagnostic source | **Done** | Bounded process-local source powers `recent_errors`; not confused with durable findings. | `_log_buffer.py:1-73` |
| Diagnostics hub and paginator | `disbot/views/diagnostic/hub_panel.py::_DiagnosticsHubView`; `paginator.py::_PaginatorView` | views | **Done** | In-place safe-edit navigation exists for general diagnostic tools. | `hub_panel.py`; `paginator.py` |
| Platform hub | `disbot/views/diagnostic/platform_panel.py::build_platform_hub_embed`, `_dispatch`, `_PlatformCategorySelect`, `_PlatformHubView` | view | **Partial** | Health and consistency dispatch correctly, but startup/findings are absent and the “every existing subcommand” module claim is false. | `platform_panel.py:1-105`, `107-371` |
| Automation panel | `disbot/views/diagnostic/automation_panel.py` (`_truncate`, scheduler/rule fetch+format/build helpers, `_commit_set_enabled`, `_commit_delete`, `_RuleSelect`, `AutomationPanelView`, `open_panel`) | view | **Done** | Read surface and segregated canonical mutations exist; this is a platform manager, not the health aggregator. | `automation_panel.py:42-582` |
| Flag manager | `disbot/views/diagnostic/flag_manager.py` (flag sorting/resolution/build helpers, `_FlagSelect`, `FlagManagerView`) | view | **Done** | Segregated manager routes writes through the rollout pipeline. | `flag_manager.py:61-505` |
| Diagnostic package exports | `disbot/cogs/diagnostic/__init__.py`; `disbot/views/diagnostic/__init__.py` | package surface | **Done** | Existing package surfaces are small and explicit. | package files |

### Tests and smoke/readiness relations

| Item | Path | Type | State | Reason | Evidence |
|---|---|---|---|---|---|
| Health contracts/aggregation/isolation/redaction/import/read-only tests | `tests/unit/services/test_health_snapshot_service.py`, `test_health_redaction.py`, `test_health_import_safety.py`, `test_health_readonly_invariants.py`, `test_health_observations.py` | automated tests | **Done** | Core deterministic and security boundaries are pinned. | named tests |
| Findings service/store/migration/sole-writer tests | `tests/unit/services/test_health_findings_service.py`; `tests/unit/db/test_health_findings_integration.py`; `test_migration_057_operational_health_findings.py`; `tests/unit/invariants/test_inv_health_findings_service.py` | automated tests | **Done** | Includes real-Postgres integration when DB is available plus CI-safe schema pins. | PR #548; named tests |
| Consistency/readiness tests | `tests/unit/services/test_platform_consistency.py`; `tests/unit/invariants/test_platform_consistency_kinds.py`; `tests/unit/runtime/test_consistency_import_cycle.py`; `tests/unit/docs/test_smoke_test_checklist.py` | automated tests | **Done** | Typed ordering, isolation/import safety, and readiness/checklist field drift are pinned. | named tests |
| Cog/embed/panel tests | `tests/unit/cogs/test_diagnostic_consistency_embed.py`, `test_diagnostic_panels_data.py`, `test_platform_health_embed.py`, `test_platform_flags_embed.py`, `test_platform_setting_detail.py`; `tests/unit/runtime/test_platform_commands.py`, `test_platform_diagnostics_commands.py`; `tests/unit/views/diagnostic/test_automation_panel.py`; `tests/unit/views/test_platform_hub_view.py` | automated tests | **Partial** | Broad rendering/route coverage exists, but no test currently requires startup/findings to appear in the Platform hub or rejects the false “every subcommand” claim. | named tests; `platform_panel.py` options |
| Startup/reconnect tests | `tests/unit/runtime/test_startup_health_pr3.py`, `test_lifecycle_diagnostics.py` | automated tests | **Done** | One-shot startup collection and lifecycle provider behavior are pinned. | named tests |
| Diagnostic DB/read-model tests | `tests/unit/db/test_diagnostic_read_models.py`; `tests/unit/binding_backfill/test_platform_migration_checkpoints_db.py` | automated tests | **Done** | Platform diagnostic renderers use owning DB read seams rather than inline SQL. | PR #RS08; named tests |
| Adjacent reported-subsystem tests | `tests/unit/services/test_btd6_source_health.py`, `test_cleanup_diagnostics.py`, `test_resource_health.py`, `test_setup_diagnostics.py`, `test_setup_readiness.py`; `tests/unit/views/test_role_diagnostics_panel.py`, `test_settings_diagnostic_subviews.py`; `tests/unit/views/setup/sections/test_diagnostics_section.py` | automated tests | **Done** | These verify root-cause/reporting seams consumed by diagnostics; failures here are not automatically Health / Diagnostics bugs. | named tests |
| Diagnostic boundary/split tests | `tests/unit/invariants/test_setup_diagnostics_readonly.py`; `tests/unit/help/test_platform_diagnostics_split.py`; `tests/unit/runtime/test_platform_diagnostics_commands.py` | automated tests | **Done** | Read-only setup diagnostics and user-facing platform/help split are pinned. | named tests |
| HTTP health server tests | `tests/unit/runtime/test_healthserver.py` | adjacent smoke/readiness | **Done** | `/health`/`/ready` behavior is covered; this is adjacent runtime readiness, not the typed HealthSnapshot aggregator. | named test; `disbot/healthserver.py` |
| Canonical manual smoke checklist | `docs/smoke-test-checklist.md` | live verification | **Partial** | Covers HTTP probes, consistency, readiness fields, startup outcomes, and tasks, but has no explicit `!platform health`, `startup`, `findings`, grouped-error, or owner AI-tool walk. | checklist; folio live-test debt |
| Production AI/grouped/findings live walk | no completed evidence recorded | live verification | **Not Done** | Canonical folio explicitly says the maintainer walk is still owed. | `docs/subsystems/health-diagnostics.md:94-101` |

## Required before production-ready

1. **Complete and record the maintainer live walk** for `!platform health`,
   `!platform startup`, `!platform findings`, opt-in grouped errors, recurring count
   across a restart, owner/admin redaction difference, and the owner-gated
   `diagnostics_health_snapshot` AI tool. This is the highest-confidence remaining gate
   because the canonical folio already names it.
2. ✅ **DONE (P1-2).** Q-0097 = operator-managed: `health_findings_service.set_status`
   is the sole transition path (no second writer; DB primitive `set_finding_status`,
   pinned by the AST guard), surfaced by `!platform finding resolve/ignore/reopen
   <fingerprint>` and audited via `audit.action_recorded`.
3. ✅ **DONE (P1-2).** Retention is now operational on long-lived replicas:
   `health_findings_service.run_retention()` runs at startup **and** on the daily
   `HealthMaintenanceCog._retention_loop` (mirrors `MediaMaintenanceCog`).
4. **Reconcile Platform hub completeness.** Either add read-only `startup` and
   `findings` routes to the existing hub or correct the hub's “every existing
   subcommand” claim and document why those typed-only routes are intentionally absent.
5. **Repair smoke-route drift.** Replace the nonexistent `!platform diagnostics`
   instruction with actual routes and add explicit smoke bullets for the newer health
   surfaces. Preserve the existing `ReadinessSnapshot` 1:1 doc-test contract.
6. **Decide whether the plan's health collection/source/redaction metrics are still a
   production requirement.** If yes, add them to the existing metrics owner; if no,
   reconcile the plan so future reviewers do not treat them as shipped.
7. **Verify production cadence semantics.** Document that persistent findings are
   boot-sampled only, or persist findings from another bounded existing snapshot
   cadence. Do not make the read-only aggregator itself a writer.

## Bugs, inconsistencies, and risks

### Health / Diagnostics implementation bugs or inconsistencies

- **Platform hub completeness claim is false.** `platform_panel.py` says it groups every
  existing `!platform <subcommand>`, but `startup` and `findings` are typed-command-only.
- **Smoke checklist points to a nonexistent command.** It instructs operators to inspect
  `!platform diagnostics`; no such Platform subcommand exists. `!platform runtime`
  renders `snapshot_all()`, while `!platform consistency` populates/reads the unified
  report.
- ~~**Finding lifecycle is schema-only.**~~ **FIXED (P1-2):** `health_findings_service.set_status`
  + `!platform finding resolve/ignore/reopen <fingerprint>` is the operator transition path
  (Q-0097); aggregate roll-up is now reachable.
- ~~**Retention is startup-only.**~~ **FIXED (P1-2):** `HealthMaintenanceCog` reruns the
  30-day sweep daily on a long-lived process.
- **Tasks health is shallow.** The health adapter always marks the task subsystem healthy
  from active count alone; it cannot report the “recent task terminal failure” behavior
  described by the implementation plan.
- ~~**Promised general health metrics are absent.**~~ **RESOLVED 2026-06-30 (PR #1584):**
  collection-duration (`health_snapshot_collection_seconds`), source-failure count
  (`health_snapshot_source_failure_total`), and redaction-outcome
  (`health_snapshot_redaction_total`) metrics are now implemented and wired at the snapshot seams.

### Operational risks, not necessarily implementation bugs

- Provider count and “runtime providers” reflect loaded modules, not a static complete
  catalogue. This is now honest by design, but operators must not read an absent
  optional provider as proof of failure without checking module load state.
- Grouped errors are process-local and opt-in; persistent findings are boot-sampled.
  Neither is a complete replacement for unredacted runtime logs.
- Health snapshots intentionally scrub traces, raw SQL, tokens, and identifiers. This
  can make a finding insufficient to debug by itself; the correct next step is runtime
  logs and the reported subsystem.
- A fresh consistency request can produce context-dependent SKIPPED sections (for
  example, no guild in a DM). This is not a health bug.

## Reporting gaps vs root-cause subsystem gaps

| Observation | Classification | Reason / owner |
|---|---|---|
| Health card reports role automation, cleanup, resources, setup, or AI-provider degradation accurately | Root-cause subsystem gap | Fix the execution/provider subsystem; health is correctly reporting it. |
| Health card turns benign `SKIPPED` consistency into an actionable finding | Reporting gap | This was a health presentation bug and was fixed in PR #553. |
| Config arbitration WARNING with `missing=0` while `bindings.primary` is on | Root-cause migration/config state | It is a real unfinished-backfill signal, not noise to suppress in health. |
| Provider raises and `snapshot_all()` returns `_error` while the rest render | Correct reporting behavior | Failure isolation is the intended registry contract. |
| Tasks recently failed but health says tasks are healthy because active count is nonzero | Reporting gap | The task adapter lacks failure-state interpretation. |
| Persistent row never becomes resolved/ignored | Health finding-lifecycle gap | The store advertises states but has no transition path. |
| Resource adapter reports broken/missing configured binding | Root-cause resource/config gap | `resource_health` owns the diagnosis; health only projects it. |
| Database ping reports critical/unavailable | Usually root-cause DB/runtime gap | It becomes a health bug only if timeout/isolation/status mapping is wrong. |

## Simplification opportunities

- **Use one operator entry vocabulary.** Treat `!platform health` as the bounded summary,
  `!platform runtime` as raw provider roll-up, `!platform consistency` as fresh platform
  consistency, and `!platform findings` as durable history. Update docs and hub labels to
  make those four purposes explicit.
- **Derive hub completeness in tests from the typed subcommand set or maintain an
  explicit intentional-exclusion list.** Do not add another router or aggregator.
- **Keep lifecycle transitions in `health_findings_service`.** If Q-0097 approves them,
  add minimal `resolve`/`ignore` service methods and DB primitives rather than allowing
  views/cogs to write directly.
- **Reuse the existing managed task supervisor for retention cadence.** Do not create a
  second scheduler.
- **Reconcile the historical implementation plan.** Mark the unimplemented general
  health metrics as deferred/removed or make them a concrete next slice.
- **Keep root-cause drill-down out of the health store.** Continue pointing to runtime
  logs and owning subsystem diagnostics instead of persisting raw traces.

## Tests and live-verification gaps

### Automated gaps

- Add a Platform-hub completeness test that either includes `startup` and `findings` or
  pins them as intentional typed-only exclusions.
- Add a route/docs test rejecting nonexistent `!platform diagnostics` references.
- If Q-0097 approves lifecycle transitions, add service, sole-writer, DB integration,
  recurrence/reopen, ignored-preservation, and retention-reachability tests.
- Add a test for long-lived retention scheduling if the sweep becomes periodic.
- Add task-health tests for recent/terminal failures if that reporting behavior remains
  required.
- If general health metrics remain required, pin collection success/failure/timeout and
  redaction counters without high-cardinality labels.

### Required live verification

- Boot cleanly; confirm startup snapshot is collected once and reconnect does not
  duplicate it.
- Run `!platform health` as guild admin and platform owner; compare redaction.
- Run `!platform startup` and verify it renders the settled cached startup snapshot.
- Induce one safe, known provider error and verify the provider degrades without blanking
  the snapshot or unrelated providers.
- Enable `HEALTH_GROUPED_FINDINGS`; induce repeated safe errors and confirm stable
  grouping/counts, then disable the flag and confirm rollback.
- Restart after a known finding and confirm `!platform findings` recurrence count rises.
- Verify migration `057` and retention behavior against production-like Postgres.
- Ask the production-configured model an owner-scoped bot-health question and verify it
  calls `diagnostics_health_snapshot`; verify non-owner scope cannot call it.
- Run `!platform consistency` in guild and DM contexts; confirm real warnings remain
  actionable and benign SKIPPED sections do not become findings.
- Exercise `/health`, `/ready`, and `/metrics` alongside Discord surfaces.

## Recommended next session

Run a **live-verification and contract-reconciliation session**, not a new architecture
session:

1. Answer Q-0097 before touching lifecycle mutation.
2. Execute the live verification list above and attach bounded evidence/results.
3. Correct the Platform hub and smoke-checklist route drift in the smallest coherent
   slice.
4. Decide and document cadence for persistence/retention and the promised general health
   metrics.
5. Only then implement approved gaps through the existing owners:
   `health_snapshot_service`, `health_findings_service`, `diagnostics_service`, and
   `platform_consistency`.
