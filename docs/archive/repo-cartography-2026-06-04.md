# SuperBot repo cartography / architectural inventory

> **Status:** `archive` — Dated architectural inventory snapshot; source wins.

_Date: 2026-06-04_

This document records the shared neutral repository map from the initial read-only architecture inventory. It is intended to seed later parallel Analysis chats and should be treated as a mapping artifact, not an implementation plan.

## 1. Current repo state

- **Repository inspected:** `/workspace/superbot`
- **Current branch observed:** `work`
- **Latest commit observed:** `d583dcb Merge pull request #506 from menno420/claude/serene-sagan-E4Llm`
- **Working tree during inventory:** clean
- **Default-branch verification:** not fully verifiable locally because this checkout did not expose a local `main` ref or a remote. Future audits should confirm that `work@d583dcb` matches the intended GitHub `main` audit base.
- **Recent commit pattern:** recent visible history was dominated by BTD6-related merges and docs/data stabilization work around PRs #494-#506.
- **Test execution:** the inventory did not require running the full suite. The environment had `pytest` available, but tests were intentionally not used as the primary evidence for cartography.

Primary verification commands used in the original mapping pass included:

```bash
git status --short
git branch --show-current
git log --oneline --decorate -n 30
git log --merges --oneline -n 20
git branch -vv
git remote -v
git ls-files | wc -l
git ls-files | sort
find . -maxdepth 4 -type f | sort
find . -maxdepth 4 -type d | sort
rg "^class |^def |^async def " disbot tests -n
rg "^from |^import " disbot tests -n
rg "commands\\.|app_commands|discord.ui|View|Button|Select|Modal" disbot -n
rg "governance|visibility|permission|capability|execution|resolver|policy" disbot -n
rg "asyncpg|aiosqlite|sqlite|jsonb|migration|pool|database|db" disbot tests -n
rg "BTD6|btd6|ai_tools|AI|paragon|bloons|tower|hero|round|bloon" disbot tests -n
rg "TODO|FIXME|HACK|temporary|legacy|deprecated|stale|PLAN ONLY|not implemented" . -n
python -m pytest --version
```

## 2. Top-level structure

| Top-level path | Apparent responsibility |
| --- | --- |
| `.claude/`, `.claude.json` | Agent configuration, automation skills, and repo-working guidance. Shared/support. |
| `.github/workflows/` | CI workflows for code quality and AI evals. Shared/support, with platform and D references. |
| `.gitattributes`, `.gitignore`, `.mcp.json`, `.pre-commit-config.yaml` | Repository metadata and tooling configuration. Shared/support. |
| `Procfile` | Deployment/runtime process declaration. Platform/support. |
| `architecture_rules/` | Static architecture policy inputs for checker scripts: layers, mutation owners, helper allowlists. Shared/support with A/B/C/D boundary relevance. |
| `data/btd6/` | CSV seed/input data for BTD6 towers/heroes. Compartment D. |
| `disbot/` | Main bot package: bootstrap, cogs, services, views, governance, utilities, migrations, static data. |
| `docs/` | Repo-wide and subsystem architecture, ownership, audit, BTD6, AI, setup, helper, and roadmap documentation. Shared/support plus subsystem-specific docs. |
| `pyproject.toml` | Ruff/Black/isort/mypy configuration. Shared/support. |
| `requirements.txt`, `requirements-dev.txt` | Runtime and development dependencies. Shared/support/platform. |
| `scripts/` | Architecture checks, quality checks, eval harness entry, BTD6 ingestion/parser/upload tooling, and Claude hooks. Shared/support and D for BTD6 scripts. |
| `tests/` | Unit tests, eval harness, and fixtures. Tests should be assigned by system under test. |

## 3. Complete compartment assignment table

The repo contains more than one thousand tracked files. This table expands source, migration, test, docs, and tooling areas enough that no architectural area is hidden, while grouping large homogeneous static data and fixture sets.

| File/path | Assigned compartment | Role | Apparent responsibility | Cross-compartment dependencies | Confidence |
| --- | --- | --- | --- | --- | --- |
| `.claude.json`, `.claude/CLAUDE.md`, `.claude/settings.json`, `.claude/agents/*`, `.claude/skills/*/SKILL.md` | Shared/support | config/tooling docs | Agent automation and repo-working guidance. | May encode audit expectations for all compartments. | Medium |
| `.github/workflows/ai-evals.yml` | Shared/support, D reference | config/CI | AI eval workflow. | Eval harness and AI/BTD6 behavior. | Medium |
| `.github/workflows/code-quality.yml` | Shared/support, A reference | config/CI | Code quality checks. | pyproject/tooling/scripts. | Medium |
| `.gitattributes`, `.gitignore`, `.mcp.json`, `.pre-commit-config.yaml` | Shared/support | config | Repo metadata, MCP, pre-commit. | All compartments. | High |
| `Procfile` | A / Shared | config/deployment | Process entrypoint for deployment. | Bot startup/runtime. | High |
| `pyproject.toml` | Shared/support | config/tooling | Formatting, linting, import, and typing policy. | All Python code. | High |
| `requirements.txt`, `requirements-dev.txt` | Shared/support | config/dependencies | Runtime and dev dependency pins. | All code/tests. | High |
| `architecture_rules/*.yaml` | Shared/support | config/architecture | Layering, mutation ownership, helper allowlists, duplicate allowlist. | A/B/C/D architecture boundaries. | High |
| `disbot/bot1.py` | A | runtime/core | Main Discord bot bootstrap, logging, task supervision, cog loading, command lifecycle, cleanup. | B governance cleanup/access; C/D cogs; A health/runtime/metrics. | High |
| `disbot/config.py` | A / Shared | config/runtime | Environment config, extension loading list, command-access notes, AI/BTD6 backend config. | A startup, B access, C command surface, D AI/BTD6. | High |
| `disbot/guild_lifecycle.py` | A/B | runtime/core | Guild join/leave lifecycle and likely governance/resource setup/teardown. | Governance, resources, setup. | Medium |
| `disbot/healthserver.py` | A | runtime/core | HTTP health/readiness/lifecycle/metrics endpoints. | Runtime lifecycle, metrics. | High |
| `disbot/core/events.py`, `disbot/core/events_catalogue.py` | A | runtime/core | Event bus and known event catalogue. | Services and governance emit events. | High |
| `disbot/core/resources/**` | A | runtime/core/service-like | Resource discovery, mutation, channel/role service, status and types. | B setup/governance, C role/channel/logging, tests/resources. | High |
| `disbot/core/runtime/bindings.py` | A/B | runtime/core | Subsystem binding runtime primitives. | B governance/settings, C setup/logging/channels. | Medium |
| `disbot/core/runtime/command_access.py` | B | runtime/governance | Central command-access resolver. | A bot guard, C/D cogs, settings views. | High |
| `disbot/core/runtime/command_descriptions.py`, `command_surface_ledger.py` | A/B/C | runtime/core | Command surface metadata and ledger. | C/D cogs and help/settings. | Medium |
| `disbot/core/runtime/component_registry.py`, `settings_registry.py`, `subsystem_schema.py`, `subsystem_capabilities.py`, `participation_schema.py`, `participation_capabilities.py` | A/B | runtime/core/registry | Schema, capability, settings, component, and participation registries. | B governance, C/D cogs/services. | High |
| `disbot/core/runtime/config_arbitration.py`, `guild_config.py`, `user_config.py`, `feature_flags.py` | A/B | runtime/config | Runtime config resolution, feature flags, typed guild/user config. | B governance/settings, C/D services. | High |
| `disbot/core/runtime/ephemeral_surface_manager.py`, `interaction_helpers.py`, `interaction_router.py`, `message_pipeline.py`, `navigation_stack.py`, `ui_permissions.py` | B | runtime/interactions | Shared interaction helpers, router, pipeline, UI permissions/navigation. | C/D views/cogs, A tasks/events. | High |
| `disbot/core/runtime/lifecycle.py`, `startup_outcome.py`, `tasks.py`, `scope_locks.py`, `slow_path_log.py`, `live_update_scheduler.py` | A | runtime/core | Lifecycle state, startup result, supervised tasks, locks, slow-path observability, live updates. | Bot startup, views/panels, metrics. | High |
| `disbot/core/runtime/message_anchor_manager.py`, `panel_manager.py`, `panel_recovery.py`, `persistent_views.py`, `session_gc.py`, `session_manager.py`, `state_store.py` | B/A | runtime/interactions | Panel/session/anchor/persistent-view infrastructure. | C/D feature views, DB utils, setup/settings. | High |
| `disbot/core/runtime/resource_specs.py`, `guild_resources.py` | A/B | runtime/resources | Guild resource spec/state plumbing. | Setup, resources, governance, logging/channels/roles. | Medium |
| `disbot/core/runtime/ai/**` | D/A | runtime/core AI | Provider-neutral AI contracts, gateway, feature flags, routing, safety, diagnostics, redaction, renderer registry, providers. | D AI services/cog/views, A runtime. | High |
| `disbot/governance/**` | B | governance | Public governance API, cache, cleanup, dependency, events, execution, health, models, permission tiers, resolver, scopes, snapshot, templates, writes. | A DB/events/runtime, C/D command gating, setup/settings. | High |
| `disbot/services/governance_service.py`, `governance_exceptions.py` | B | service/governance | Legacy/thin wrapper and governance exceptions. | B governance package, C/D callers. | High |
| `disbot/services/command_access_service.py`, `command_routing.py`, `binding_mutation.py`, `binding_backfill.py`, `settings_mutation.py`, `settings_resolution.py`, `rollout_mutation.py` | B/A | service | Command access/routing, binding and settings mutation/resolution, rollout mutation. | A DB/runtime, B governance/settings, C setup/settings UI. | High |
| `disbot/services/cleanup_levels.py`, `cleanup_profiles.py`, `history_cleanup.py` | B/C | service | Cleanup policy/profile/history cleanup behavior. | B governance cleanup; C cleanup cog. | Medium |
| `disbot/services/resource_health.py`, `resource_provisioning.py`, `resource_provisioning_catalogue.py`, `readiness_repair.py`, `platform_consistency.py` | A/B | service | Platform resource validation/provisioning/readiness/consistency. | A resources/runtime, B setup/governance. | High |
| `disbot/services/runtime.py`, `metrics.py`, `webhook_reporter.py`, `audit_events.py` | A | service/runtime | Boot identity/runtime lock, metrics, webhook reporting, audit event helpers. | Bot startup, events, observability, DB. | High |
| `disbot/services/guild_introspection_service.py`, `guild_snapshot.py`, `channel_recommender.py`, `customization_catalogue.py`, `bot_knowledge_service.py` | A/B/C | service | Guild scan/snapshot, recommendations, customization catalogue, bot self-knowledge. | Setup, docs/help/settings, AI. | Medium |
| `disbot/services/setup_*`, `wizard_finalization.py`, `setup_advisor_review.py`, `setup_ai_advisor.py` | B | workflow/service | Setup wizard sessions, plans, readiness, operations, AI advisor, finalization. | A runtime/resources, B governance/settings, C/D setup views. | High |
| `disbot/services/automation_*` | B/C | service/workflow | Automation registry/templates/scheduler/executor/mutation. | A events/DB, B policy, C diagnostic/admin. | Medium |
| `disbot/services/participation_mutation.py`, `rank_providers.py` | A/C | service | Participation write pipeline and rank provider abstractions. | XP/games, user config, DB. | Medium |
| `disbot/services/economy_service.py`, `xp_service.py`, `moderation_service.py`, `role_automation.py`, `role_exemption_service.py`, `server_logging.py`, `game_state_service.py`, `tournament_state_service.py`, `blackjack_engine.py` | C | service | General feature business logic. | A DB/events/runtime; B governance/settings; C cogs/views. | High |
| `disbot/services/paragon_service.py` | D | service | BTD6 paragon calculator integration/fallback. | D paragon cog/views/utils; external API optional. | High |
| `disbot/services/ai_*` | D | service | AI behavior profile/config/context/conversation/audit/diagnostics/instructions/memory/NL policy/permissions/policy mutation/readiness/task router/tools. | A core runtime AI, B policy/governance, D BTD6 AI. | High |
| `disbot/services/btd6_*` | D | service | BTD6 deterministic data, sources, ingestion, knowledge, grounding, resolver, stats, strategies, source health, view models, live queries, AI context/knowledge. | A DB/cache/runtime; B capability/policy; D cogs/views/data/scripts. | High |
| `disbot/services/parsers/**` | D | parser/tooling service | Steam/NinjaKiwi/BTD6 source parsers and envelopes. | BTD6 ingestion/tests/scripts. | High |
| `disbot/services/video_reference_cache_service.py`, `youtube_context_service.py`, `youtube_fetch_service.py` | D/C? | service | YouTube/video reference support. | D AI/BTD6 context and possibly C general. | Low |
| `disbot/cogs/bootstrap_access_cog.py` | B | cog/adapter | Central command access guard installed first. | A bot/runtime, B command access. | High |
| `disbot/cogs/admin_cog.py`, `disbot/cogs/admin/**` | C/A | cog/adapter/helper | Admin commands and cog management/reload. | A bot/runtime, B command access/governance. | High |
| `disbot/cogs/help_cog.py`, `disbot/cogs/help/**` | C/B | cog/adapter/workflow | Help command, routing, hub navigation. | A command ledger, B visibility/access, C/D cogs. | Medium |
| `disbot/cogs/role_cog.py`, `role/**`, `moderation_cog.py`, `moderation/**`, `xp_cog.py`, `xp/**`, `blackjack_cog.py`, `blackjack/**`, `rps_tournament_cog.py`, `rps_tournament/**`, `utility_cog.py`, `general_cog.py`, `four_twenty_cog.py`, `community_cog.py`, `cleanup_cog.py`, `cleanup/**`, `channel_cog.py`, `inventory_cog.py`, `economy_cog.py`, `economy/**`, `counting_cog.py`, `counting/**`, `deathmatch_cog.py`, `deathmatch/**`, `proof_channel_cog.py`, `leaderboard_cog.py`, `games_cog.py`, `chain_cog.py`, `mining_cog.py`, `mining/**`, `diagnostic_cog.py`, `diagnostic/**`, `logging_cog.py`, `logging/**` | C with A/B overlaps | cog/schema/helper/workflow/panel | General user-facing systems: roles, moderation, XP, games, cleanup, channel, economy, inventory, counting, deathmatch, proof, leaderboard, mining, diagnostics, logging. | C services/views/utils; A runtime/resources/metrics; B command access/settings/governance. | Medium-High |
| `disbot/cogs/settings_cog.py`, `settings/**`, `setup_cog.py`, `setup/**` | B/C | cog/adapter/workflow | Settings and setup wizard command surfaces. | B settings/governance/access/setup, C feature schemas, D AI/BTD6 setup sections. | High |
| `disbot/cogs/ai_cog.py`, `ai/**` | D/B | cog/schema | AI command adapter and schemas. | D AI services/views/runtime, B policy/permissions. | High |
| `disbot/cogs/btd6_cog.py`, `btd6_reference_cog.py`, `btd6_events_cog.py`, `btd6_strategy_cog.py`, `btd6_ops_cog.py`, `btd6/**`, `paragon_cog.py` | D | cog/adapter/schema/helper/workflow | BTD6 command adapters, embed/reply/builders, stage, freshness rendering, event helpers, paragon calculator. | D services/views/data; A runtime tasks/message pipeline; B gating. | High |
| `disbot/views/base.py`, `navigation.py` | B | view/runtime helper | BaseView, send_panel, standard error handling/navigation. | All feature views. | High |
| `disbot/views/selectors/**`, `access/**`, `settings/**`, `setup/**` | B with C/D references | view/workflow UI | Shared selectors, access explorer, settings hub/editors, setup wizard UI. | B services/governance/resources; C schemas; D AI/BTD6 sections. | High |
| `disbot/views/ai/**`, `btd6/**` | D/B | view | AI behavior/policy/routing/support UI; BTD6 panels/browsers/stats/paragon/strategy/live events/admin UI. | D services/utils; B BaseView/runtime/policy. | High |
| `disbot/views/blackjack/**`, `games/**`, `rps/**`, `counting/**`, `mining/**`, `economy/**`, `xp/**`, `moderation/**`, `roles/**`, `channels/**`, `community/**`, `diagnostic/**` | C with A/B overlaps | view | General feature panels/modals/hubs/game views. | C services; B BaseView/governance/runtime; A metrics/resources for diagnostics. | Medium-High |
| `disbot/views/youtube_embeds.py`, `youtube_renderers.py` | D/C? | view/render helper | YouTube embed/render support. | AI/BTD6 or general media surfaces. | Low |
| `disbot/utils/db/pool.py`, `migrations.py`, `codec.py`, `runtime_lock.py`, `platform_migration_checkpoints.py` | A | database helper | DB pool, codec, migration runner, runtime lock/checkpoints. | All DB users. | High |
| `disbot/utils/db/governance.py`, `command_access.py`, `command_routing.py`, `bindings.py`, `settings.py`, `settings_audit.py`, `feature_flag_state.py`, `environment_tiers.py`, `automation.py`, `resource_cache.py`, `resource_provisioning_audit.py`, `setup_draft.py`, `setup_session.py`, `sessions.py`, `anchors.py`, `user_participation.py` | B/A | database helper | Governance/settings/bindings/setup/session/panel/resource DB access. | A runtime, B governance/setup/settings. | High |
| `disbot/utils/db/economy.py`, `inventory.py`, `moderation.py`, `roles.py`, `xp.py`, `games/**`, `youtube_video_cache.py` | C/D | database helper | Feature DB helpers and YouTube cache. | C services/cogs/views; D if YouTube is AI/BTD6 context. | Medium |
| `disbot/utils/db/ai.py`, `btd6_data.py`, `btd6_sources.py`, `btd6_strategies.py` | D | database helper | AI policy/instruction/memory and BTD6 persistence. | D services/views/scripts/tests; B policy. | High |
| `disbot/utils/btd6/**` | D | helper/utility | BTD6 formatting, IDs, damage/cost/tier logic, CT render/geometry, paragon math, stats embeds, restrictions, name guards. | D cogs/services/views/tests. | High |
| `disbot/utils/settings_keys/**` | B/C/D | helper/config constants | Settings key namespaces for AI, BTD6, economy, games, governance, logging, moderation, role, XP. | All settings readers/writers. | Medium |
| `disbot/utils/channel_classify.py`, `channels.py`, `command_resolution.py`, `cooldowns.py`, `discord_permissions.py`, `embeds.py`, `guild_config_accessors.py`, `helpers.py`, `hub_registry.py`, `mining_render.py`, `subsystem_registry.py`, `synonyms.py`, `tournaments.py`, `ui_constants.py`, `user_config_accessors.py`, `visibility_rules.py` | Shared/A/B/C/D | helper/utility | Cross-cutting helpers, with some domain-specific helpers mixed in. | All compartments. | Medium |
| `disbot/migrations/001_initial_schema.sql`-`055_btd6_steam_patch_source.sql` | A/B/C/D by domain | migration | Database schema evolution for platform, governance, runtime sessions, resources, games, setup, automation, AI, BTD6, YouTube. | A migration runner plus domain owners. | Medium-High |
| `disbot/data/btd6/**`, `data/btd6/**` | D | data/static asset | Committed deterministic BTD6 fixtures and CSV source/input data. | D data service/tests/scripts. | High |
| `disbot/data/json/general_content.json`, `four_twenty_content.json`, `recipes.json` | C | data/static asset | General/four-twenty/mining recipe content. | C general/mining cogs. | High |
| `scripts/check_architecture.py`, `check_quality.py`, `run_evals.py`, `setup_dev_env.sh` | Shared/A | script/tooling | Architecture/quality/eval/dev setup tooling. | All compartments. | High |
| `scripts/claude_*` | Shared/support | script/tooling | Claude session hooks/reminders/summaries. | Agent workflow, not runtime. | Medium |
| `scripts/btd6_*`, `fetch_bloonswiki.py`, `fetch_btd6_wiki_data.py`, `import_btd6_data_from_csv.py`, `parse_bloonswiki.py`, `parse_gamedata.py`, `seed_btd6_data.py`, `upload_btd6_data.py` | D | script/tooling | BTD6 data extraction, parsing, seeding, upload, diff/inventory. | D data/services/tests. | High |
| `docs/architecture.md`, `docs/ownership.md`, `docs/architecture/service_ownership.md`, `docs/runtime_contracts.md`, `docs/health/platform-consistency-ledger.md`, `docs/setup-platform/resource-provisioning-overview.md`, `docs/server-logging.md`, `docs/setup-platform/roadmap_setup_platform.md` | A/B shared | documentation | Architecture/runtime/ownership/platform resource docs. | A/B/C/D boundary contracts. | High |
| `docs/audits/helper-debt-inventory.md`, `helper-policy.md`, `repo-navigation-map.md`, `loose-ends-audit-roadmap.md`, `AGENT_ORIENTATION.md`, `codegraph-usage.md` | Shared/support | documentation | Repo navigation, helper policy/debt, audit roadmap. | All compartments. | High |
| `docs/ai-*` | D/B | documentation | AI config, provider/grounding, readiness, integration. | D AI; B policy/governance. | High |
| `docs/btd6/btd6-*` | D | documentation | BTD6 data pipeline/backends/decode/source/groundedness/smoke plans. | D BTD6 services/scripts/data. | High |
| `docs/building-roadmap/*`, `docs/settings-*`, `docs/setup-platform/setup_wizard_finalization_plan.md`, `docs/setup-platform/operator-settings-presets.md`, `docs/archive/phase_2b_bindings_plan.md` | B/C | documentation | Settings/setup/bindings/UI platform roadmap. | B setup/settings/governance, C features. | Medium |
| `docs/audits/cog-hub-coverage-audit.md`, `help-command-surface-map.md`, `games-actionability-roadmap.md`, `mining_exploration_brainstorm.md`, `ui-view-adoption-audit.md`, `smoke-test-checklist.md` | C/shared | documentation | Feature UX/cog/help/game/mining/view coverage docs. | C features with A/B references. | Medium |
| `docs/decisions/**` | Shared/A/C | documentation/ADR | Architecture decisions such as game state restart safety and deferred followups. | A runtime, C games/views. | High |
| `docs/audits/**` | Shared/support | documentation/audit | Prior repo-wide/mutation-boundary audits. | All compartments; may be stale. | Medium |
| `tests/conftest.py`, `tests/__init__.py` | Shared/test | test support | Shared fixtures/import setup. | All tests. | High |
| `tests/unit/test_bot_boot.py`, `test_bot1_lifecycle_close_driver.py`, `test_config_env_cleanup.py`, `tests/unit/runtime/**`, `resources/**`, `db/**`, `registry/**`, `config_arbitration/**`, `feature_flags/**` | A/B | test | Bot bootstrap, lifecycle, runtime, DB, resources, registries, feature flags, config arbitration. | A runtime/data; B access/settings. | High |
| `tests/unit/governance/**`, `schema/**`, `bindings/**`, `binding_backfill/**`, `participation/**`, `slash/**`, B-side views/services tests | B | test | Governance/cache/snapshot/scope/startup, schemas/capabilities/bindings/participation/slash access. | B governance/interactions; A DB/runtime. | High |
| AI/BTD6 tests under `tests/unit/cogs`, `runtime/ai`, `services`, `views/ai`, `views/btd6`, `utils`, `scripts`, plus `tests/evals/**`, `tests/fixtures/ninjakiwi/**`, `tests/fixtures/steam/**` | D | test/eval/fixture | AI and BTD6 cogs/services/views/utils/scripts/source fixtures/evals. | D AI/BTD6; B policy; A runtime. | High |
| Non-AI/BTD6 tests under `tests/unit/cogs`, `services`, `views`, `help`, games/economy/xp/moderation/role/channel tests | C | test | General feature cogs/services/views/helpers/help/games. | C features; B gating; A runtime. | Medium |
| `tests/unit/docs/**`, `tests/unit/invariants/**` | Shared/support | test | Documentation and cross-cutting architecture invariants. | All compartments; assign findings by violated owner. | Medium |

## 4. Compartment A candidate scope

**Platform foundation / runtime / data layer** should include:

- Startup/config/deployment: `disbot/bot1.py`, `disbot/config.py`, `disbot/guild_lifecycle.py`, `disbot/healthserver.py`, `Procfile`, requirements, pyproject, code-quality CI.
- Runtime/core: `disbot/core/events*`, `disbot/core/resources/**`, A-owned `disbot/core/runtime/**` files for lifecycle, startup outcomes, tasks, locks, slow-path logging, live updates, resources, config arbitration, guild/user config, feature flags, registries, and schemas.
- Data layer: `disbot/utils/db/pool.py`, `codec.py`, `migrations.py`, `runtime_lock.py`, `platform_migration_checkpoints.py`, resource/session/anchor DB plumbing.
- Platform services: `runtime.py`, `metrics.py`, `webhook_reporter.py`, `audit_events.py`, resource health/provisioning/readiness/consistency services, guild snapshot/introspection/recommendation/catalogue knowledge services.
- Migrations: A owns the migration runner and should review global order/safety; domain migration semantics should be handed to B/C/D.
- Tests: bot boot/lifecycle/config tests, runtime/resource/DB/registry/feature flag/config arbitration tests, and A-side architecture invariants.

Likely downstream dependents are all cogs, services, governance, setup/resource provisioning, BTD6 ingestion/data services, AI gateway, and tests requiring DB/runtime fixtures.

Potentially misplaced or ambiguous A files include `services/runtime.py`, `services/metrics.py`, `core/runtime/ai/**`, and `core/runtime/command_access.py`.

## 5. Compartment B candidate scope

**Governance / permissions / visibility / interactions** should include:

- `disbot/governance/**`.
- Governance/settings/access services: governance wrappers, command access/routing, binding mutation/backfill, settings mutation/resolution, rollout mutation, cleanup policy, setup, wizard finalization, automation, and B-side participation mutation.
- Runtime interaction/session/panel/access files: command access, interaction helpers/router, message pipeline, ephemeral surface manager, message anchor manager, panel manager/recovery, persistent views, session GC/manager, state store, navigation stack, UI permissions.
- Views: `views/base.py`, `views/navigation.py`, selectors, access, settings, setup.
- Cogs: bootstrap access, setup, settings, and B-overlap portions of cleanup/channel/help/logging/role visibility surfaces.
- DB helpers: governance, command access/routing, bindings, settings/audit, feature flag state, environment tiers, automation, setup draft/session, user participation, sessions/anchors where policy state is involved.
- Migrations: governance, capabilities/templates/indexes, bindings, feature flags, environment tiers, setup, automation, command routing/access, and role automation exemption overlap.
- Tests: governance/schema/bindings/participation/slash/setup/settings/access/panel tests.

Likely downstream dependents are every command, setup/settings/logging/channel/role panels, AI policy views/services, BTD6 capability/policy integration, and invariants.

Potentially misplaced or ambiguous B files include runtime-located command access, cleanup services, setup sections that are domain-aware for AI/BTD6, and settings views that perform policy mutations.

## 6. Compartment C candidate scope

**General Discord feature cogs and user-facing systems** should include:

- Non-BTD6/non-AI cogs: admin, help, roles, moderation, XP, blackjack, RPS tournament, utility, cleanup, channels, inventory, economy, counting, deathmatch, proof channel, mining, diagnostics, chain, general, four-twenty, leaderboard, logging, games, community.
- General feature services: economy, XP, moderation, role automation/exemptions, server logging, game state, tournament state, blackjack engine, C-side participation and rank providers.
- Feature views: blackjack, games, RPS, counting, mining, economy, XP, moderation, roles, channels, community, diagnostics, and C-side settings usage.
- Helpers/DB/static data: economy, inventory, moderation, roles, XP, games DB helpers; mining render; tournaments; generic channel/permission/embed/cooldown/helper/hub/synonym/UI helpers; general JSON content.
- Migrations: game, mining, RPS, game-state, economy audit, participation audit, role XP thresholds, role automation overlap, YouTube overlap if it is general media.
- Tests: non-AI/BTD6 cogs/services/views/help/utils/games/economy/XP/moderation/role/channel tests.

Potentially misplaced or ambiguous C files include view-like files under `disbot/cogs/cleanup/` and `disbot/cogs/logging/`, direct DB exceptions for simple feature/game systems, diagnostics crossing A/B/C, and YouTube/video files.

## 7. Compartment D candidate scope

**BTD6 + AI subsystem** should include:

- BTD6 cogs: BTD6 mother/reference/events/strategy/ops cogs, `disbot/cogs/btd6/**`, and paragon cog.
- AI cogs: `ai_cog.py`, `disbot/cogs/ai/**`.
- AI runtime/service layer: `disbot/core/runtime/ai/**`, `services/ai_*`, and the AI gateway shim.
- BTD6 services: all `services/btd6_*`, `paragon_service.py`, and `services/parsers/**`.
- Views: `views/btd6/**`, `views/ai/**`, and likely YouTube render helpers pending ownership decision.
- Helpers/data/DB: `utils/btd6/**`, `utils/db/ai.py`, BTD6 DB helpers, AI/BTD6 settings keys, `disbot/data/btd6/**`, `data/btd6/**`.
- Migrations: AI policy/instruction migrations, BTD6 source/strategy/ingestion/blob/patch migrations, and YouTube cache if AI/BTD6-specific.
- Scripts: BTD6 decode/inventory/diff/fetch/parse/import/seed/upload scripts and D-side eval runner usage.
- Docs: `docs/ai-*`, `docs/btd6/btd6-*`, and D-side smoke/eval docs.
- Tests/fixtures: AI/BTD6 cogs/services/views/utils/scripts/runtime tests, `tests/evals/**`, NinjaKiwi and Steam fixtures.

Potentially misplaced or ambiguous D files include `core/runtime/ai/**`, paragon at top-level cog/service paths, and YouTube/video context/cache/render files.

## 8. Shared/support files

| File/path | Why shared/support | Later chat ownership |
| --- | --- | --- |
| `.claude/**`, `.claude.json` | Agent workflow config, not runtime architecture. | Consolidation pass. |
| `.github/workflows/code-quality.yml` | CI quality gate. | A primary; consolidation for repo-wide checks. |
| `.github/workflows/ai-evals.yml` | AI eval workflow. | D primary; A for CI environment. |
| `.gitattributes`, `.gitignore`, `.mcp.json`, `.pre-commit-config.yaml` | Repo metadata/tooling. | Consolidation/A. |
| `pyproject.toml` | Quality/type/lint config applies repo-wide. | A primary; all chats as reference. |
| `requirements*.txt` | Dependency map applies repo-wide. | A primary; D for AI/BTD6 dependencies. |
| `architecture_rules/**` | Architecture checker policy, mutation ownership, layer rules. | Consolidation with A/B/C/D input. |
| Repo-wide docs such as `AGENT_ORIENTATION.md`, `repo-navigation-map.md`, helper docs, audit-roadmap docs | Repo navigation and policy docs. | Consolidation, with A for helper policy. |
| `docs/audits/**` | Historical audit docs may be stale. | Consolidation; verify against code. |
| `docs/decisions/**` | ADRs affect runtime/game/view patterns. | A/C depending decision; consolidation validates conflicts. |
| Shared scripts | Repo-wide tooling. | A/consolidation; D for eval runner if AI-focused. |
| `scripts/claude_*` | Local Claude automation hooks. | Shared/support. |
| `tests/unit/docs/**` | Documentation consistency tests. | Consolidation; docs mapped to domains. |
| `tests/unit/invariants/**` | Cross-cutting architecture invariants. | Consolidation, with each chat owning failures in scope. |

## 9. Dependency map

### Cogs to services/workflows/views/helpers

- `bot1.py` loads configured cogs from `config.INITIAL_EXTENSIONS`; bootstrap access is expected to load first for central command gating.
- BTD6 cogs depend on BTD6 builders, embeds, reply/stage helpers, runtime message pipeline/tasks/interaction helpers, BTD6 services, and BTD6 panel views.
- AI cogs depend on AI services, AI policy/config, runtime AI through `services.ai_gateway`, and AI views.
- Setup/settings cogs depend on setup services, settings/bindings/governance services, runtime interaction/session/panel helpers, and setup/settings views.
- Economy/XP/moderation should depend on service layers.
- Games may use game-state/tournament/blackjack services plus documented narrow DB helper exceptions.
- Help/diagnostic/admin cogs cross command surface, runtime, governance, metrics, and feature registries.

### Services to database/governance/runtime/helpers

- Domain services generally depend on `utils/db/*` and `core/events`, and should not depend on cogs.
- BTD6 services depend on BTD6 DB helpers, static BTD6 data, parsers, AI context/tools, and governance/capability integration.
- AI services depend on runtime AI, AI DB helpers, and governance/settings/policy services.
- Setup/resource services depend on resource discovery/mutation/status, governance/settings/bindings DB helpers, setup session/draft DB helpers.
- Observability services are platform-wide.

### Views to runtime/governance/services

- `views/base.py` is the shared interaction lifecycle base.
- Feature views should depend on BaseView/navigation/safe interaction helpers, feature services, and settings/governance services only when editing policy/config.
- Setup views depend on setup session/draft/progress/readiness services, resource provisioning, governance/settings/bindings, and domain setup sections.
- BTD6 and AI views depend on D services/utilities plus B-owned BaseView/runtime/policy seams.

### Governance to database/cache/events/runtime dependencies

- Governance owns cache, cleanup, events, execution, health, models, resolver, snapshot, templates, and writes.
- Governance depends on governance/session/settings DB helpers, subsystem registry, visibility rules, settings keys, and event/cache invalidation.
- Governance must remain the central place for permissions, visibility, capability, execution gating, cleanup policy, and subsystem policy.

### BTD6/AI to service/data/tool dependencies

- BTD6 facts should be sourced from `btd6_data_service`, fact stores, data providers, and committed/configured data sources rather than cogs/views inventing facts.
- AI cogs/services should use `services.ai_gateway`, not direct runtime gateway imports.
- Paragon external API is configurable and has local fallback semantics that must be clearly labeled and tested.

### Tests to systems under test

- Runtime/resources/DB/registry/feature flags/config arbitration tests map to A/B.
- Governance/schema/bindings/participation/slash/setup/settings tests map to B.
- Non-AI/BTD6 cogs/services/views/help/utils tests map to C.
- AI/BTD6 cogs/services/views/utils/scripts/runtime/eval/fixture tests map to D.
- Invariants and docs tests are cross-cutting and should assign failures by owner.

## 10. Cross-compartment risk register

| Risk | Evidence/files | Affected compartments | Later chat responsible | Severity guess |
| --- | --- | --- | --- | --- |
| Audit base could diverge from GitHub `main`. | Branch observed as `work`; no local `main` or remote in original checkout. | All | Consolidation/A | Medium |
| Runtime AI is under core but functionally D-owned. | `disbot/core/runtime/ai/**`, `services/ai_gateway.py`. | A/D | A + D | Medium |
| Command access/governance spans runtime, services, governance, and bootstrap cog. | `core/runtime/command_access.py`, command access services, governance package, bootstrap cog, config load ordering. | A/B/C/D | B primary | High |
| Cleanup policy exists as governance and feature/admin UX. | `governance.cleanup`, `services/cleanup_*`, `cogs/cleanup_cog.py`, cleanup panel. | B/C/A | B + C | Medium |
| View/panel code exists both under `views/` and under some cog subpackages. | Cleanup/logging panel-like files under cogs; canonical `views/base.py`. | B/C | C with B reference | Medium |
| Direct DB usage exceptions need verification against mutation ownership. | Simple inventory/game DB helpers and ownership exceptions. | A/C | C + A | Medium |
| Migrations are numerous and domain-spanning. | `disbot/migrations/001`-`055`. | A/B/C/D | A with all chats | Medium |
| Historical docs may conflict with current code after recent BTD6 changes. | Recent BTD6-heavy commits and extensive docs under `docs/btd6/btd6-*` and `docs/audits/**`. | D/shared | D + consolidation | Medium |
| YouTube/video ownership is unclear. | YouTube services, views, and migration `049`. | C/D/A | D asks maintainer | Unknown |
| Help/settings/diagnostic surfaces cross multiple boundaries. | help, diagnostic, settings cogs/views/services. | B/C/A | B + C | Medium |
| BTD6/AI cross runtime/governance/policy boundaries and could hide circular dependencies. | BTD6 cogs/services, runtime AI, governance policy/capability integrations. | A/B/D | D primary | High |
| Prefix/slash parity risk remains. | Mixed command surfaces; BTD6 explicitly documents both, other cogs need verification. | B/C/D | C + D | Medium |
| TODO/legacy/stale markers exist in binding backfill, config arbitration, AI projection, anchors/panels, and BTD6 freshness/render areas. | TODO/FIXME/legacy marker search. | A/B/D | Each chat by owner | Medium |
| Governance package comments suggest fragile import boundaries. | Governance package local imports to avoid circular import pressure. | A/B | B + A | Medium |

## 11. Recommended final parallel-audit split

The four-chat split is appropriate if shared/support files receive a later consolidation pass.

### Analysis A: Platform foundation / runtime / data layer

- **Inspect:** bot startup/config/health, events, resources, A-owned runtime, DB pool/migrations/codec/locks/checkpoints, platform services, CI/tooling, A tests.
- **Exclude:** deep governance policy semantics, feature business logic, BTD6/AI factual correctness.
- **Reference only:** governance, feature cogs/views/services, BTD6/AI domain code.
- **Main questions:** Is startup/shutdown deterministic and observable? Are migrations safe and aligned? Are runtime/session/panel/task primitives stable? Are helpers centralized and leaf-like? Does tooling enforce the architecture?

### Analysis B: Governance / permissions / visibility / interactions

- **Inspect:** governance package, access/routing/bindings/settings/setup/automation/cleanup policy services, B-owned interaction/session/panel runtime files, bootstrap/setup/settings cogs, base/selectors/access/settings/setup views, B DB helpers, B migrations/tests.
- **Exclude:** feature service correctness, BTD6 data correctness, DB pool internals.
- **Reference only:** C feature code, D AI/BTD6 code, A runtime/DB primitives.
- **Main questions:** Is governance centralized and enforceable? Are permissions/visibility/capabilities/cleanup/command access one system? Are interactions/session/panels consistent? Do writes go through owners?

### Analysis C: General Discord feature cogs and user-facing systems

- **Inspect:** all non-AI/non-BTD6 cogs, general feature services/views/helpers/static data, C DB helpers, C migrations/tests, help/UX docs.
- **Exclude:** BTD6/paragon/AI, central governance internals, runtime internals.
- **Reference only:** governance, runtime, AI/BTD6.
- **Main questions:** Are cogs thin adapters? Do services own business logic? Are workflows/services/views split cleanly? Are direct DB exceptions justified? Are prefix/slash/help/settings integrations consistent?

### Analysis D: BTD6 + AI subsystem

- **Inspect:** all BTD6/AI cogs/services/views/utils/DB helpers/migrations/docs/scripts/tests/fixtures/data, paragon, runtime AI, likely YouTube/video files pending decision, evals.
- **Exclude:** generic runtime internals outside runtime AI, general feature games, central governance policy changes.
- **Reference only:** governance, B setup sections, A runtime/DB outside runtime AI, general feature code.
- **Main questions:** Are BTD6 facts grounded? Are AI calls provider-neutral, policy-gated, observable, and safe? Is BTD6 ready for data extraction/integration? Are D boundaries against governance/runtime clean?

## 12. Handoff questions for later Analysis chats

### Analysis A should verify

- Is `work@d583dcb` identical to the intended GitHub `main` audit base?
- Do migrations `001`-`055` apply cleanly in order and map to current code owners?
- Does the migration runner match fresh-DB bootstrap assumptions?
- Are runtime sessions, anchors, panels, persistent views, and state store one coherent system?
- Are task spawning and shutdown centralized through runtime task/lifecycle primitives?
- Are observability paths complete enough for production diagnosis?
- Do `architecture_rules/*` match the code and docs ownership contracts?
- Are shared helpers leaf dependencies?

### Analysis B should verify

- Is bootstrap access actually loaded before commands can run?
- Do prefix and slash commands share the same command-access resolver?
- Is governance execution the only place that decides capability/visibility/permission denials?
- Are cleanup policy decisions centralized?
- Do settings/bindings/setup/automation writes emit required audit/events/cache invalidation?
- Do BaseView, persistent views, panel manager, session manager, and message anchors form a single model?
- Are setup wizard views/services too domain-aware?
- Are governance cache/snapshot/dependency invalidations deterministic and observable?

### Analysis C should verify

- For every non-D cog, is the cog a thin Discord adapter?
- Which feature cogs still contain business logic that should move to services/workflows?
- Are direct DB exceptions for inventory/counting/chain/mining/deathmatch narrow and justified?
- Are feature views only UI/state composition?
- Are help/settings/diagnostic panels consistent with the actual command surface?
- Are prefix/slash commands consistent and tested?
- Are feature-specific helpers duplicated with shared helpers?
- Are game-state services restart-safe enough for current behavior and ADRs?

### Analysis D should verify

- Are BTD6 facts always sourced from data services/fact stores/data providers?
- Are BTD6 docs and smoke checklist consistent with current data files and services?
- Is BTD6 ingestion/source health/freshness observable and tied to migrations/tables?
- Are BTD6 AI answers grounded, quota/policy-gated, and audited?
- Does runtime AI remain provider-neutral and not domain-coupled to BTD6?
- Are AI tools read-only and safe?
- Are paragon fallbacks labeled and tested?
- Should YouTube/video context/cache/render files belong to D, C, or shared media infrastructure?

## 13. Unknowns / needs human decision

| Item | Why unknown |
| --- | --- |
| Branch `work` vs default `main` | No local `main` or remote was available during inventory. |
| YouTube/video services, views, and migration | Could be D-owned AI/BTD6 context, C-owned general media, or shared media infrastructure. |
| Cleanup services and cleanup cog/panel | Cleanup is both governance policy and feature/admin UX. |
| Logging panel/view files under cogs | View-like files live under cogs; may be historical or intentional colocation. |
| `core/runtime/ai/**` | Path says platform; subsystem behavior says D. |
| Historical docs under `docs/audits/**` and roadmap docs | May be stale after recent PRs. |
| Generic helper modules | Some helpers may hide domain behavior and need symbol-by-symbol classification. |
| BTD6 generated/static data | Hand-authored vs generated authority and refresh source are not fully classified. |
| `.claude/**` | Not runtime architecture, but may encode repo process assumptions. |

## 14. Suggested consolidation strategy

After A/B/C/D audits finish:

1. Merge findings by ownership surface, not path alone.
2. Build a conflict matrix for claimed owner, observed owner, conflict, and maintainer decision.
3. Normalize cross-cutting decisions for runtime AI, YouTube/video ownership, cleanup ownership, setup-domain sections, and direct DB exceptions.
4. Convert findings into implementation backlog only after ownership conflicts are resolved.
5. Use tests and invariants as the final arbitration layer for future architectural corrections.

## Verification checklist from inventory

- [x] No files modified during original inventory
- [x] Current branch verified
- [x] Top-level tree mapped
- [x] All cogs assigned
- [x] All services assigned
- [x] All views assigned
- [x] All migrations assigned
- [x] All tests assigned
- [x] BTD6/AI searched
- [x] Governance searched
- [x] Runtime/session/view systems searched
- [x] Cross-compartment risks listed
- [x] Recommended parallel-audit split produced
