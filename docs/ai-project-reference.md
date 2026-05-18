# SuperBot — AI Project Reference

> Status: continuity artifact for future AI sessions.  
> Audited from `main` at merge commit `25908e7e63e944386f612a853266db140dda6619` after PR #68.  
> Scope: repository map and implementation reality. This file is not a new architecture plan.

## 0. Current Baseline

SuperBot is currently structured as a Discord-native application platform, not a simple feature bot. The active baseline includes:

- one process running `discord.py` + `asyncpg`;
- centralized bot entrypoint in `disbot/bot1.py`;
- immutable subsystem metadata in `utils/subsystem_registry.py`;
- governance-aware command and interaction gates;
- a platform-level message pipeline in `core/runtime/message_pipeline.py`;
- persistent panel/view recovery through `core/runtime/persistent_views.py` and anchor tables;
- centralized interaction routing through `core/runtime/interaction_router.py`;
- reusable guild resource resolution through `core/runtime/guild_resources.py`;
- service-layer mutation paths for shared/audited state;
- invariant tests for key architectural contracts.

The immediate next phase is setup/configuration platform work. Implementation should continue inside-out: runtime primitives, shared infrastructure, governance/resource/config domains, diagnostics, reusable UI framework, then setup/dashboard surfaces.

---

## 1. Repository Structure

| Area | Location | Current role |
|---|---|---|
| Process entrypoint | `disbot/bot1.py` | Bot construction, startup, shutdown, global checks, command logging, governance guard, cog loading, identity validation. |
| Cogs | `disbot/cogs/` | Subsystem command entry points and per-subsystem lifecycle hooks. |
| Cog domain packages | `disbot/cogs/<name>/` | Extracted domain logic/stages for larger subsystems, e.g. counting, xp, rps tournament. |
| Runtime platform | `disbot/core/runtime/` | Sessions, anchors, router, message pipeline, guild resources, tasks, navigation, diagnostics hooks. |
| Events | `disbot/core/events.py`, `disbot/core/events_catalogue.py` | Process-local EventBus plus known-event registry. |
| Governance | `disbot/governance/` | Visibility/execution/cleanup policy engine and command/interaction authorization. |
| Services | `disbot/services/` | Audited cross-subsystem mutation and operational services. |
| Views | `disbot/views/` | Shared base views and subsystem UI panels/modals/selectors. |
| Database layer | `disbot/utils/db/` | Asyncpg pool, migration runner, CRUD helpers. |
| SQL migrations | `disbot/migrations/` | Forward-only additive schema migrations. |
| Tests | `tests/` | Unit, invariant, runtime, registry, cog, and service tests. |
| Docs | `docs/` | Binding architecture and continuity documentation. |
| Runtime config | `disbot/config.py` | Environment-derived token, prefix, initial extensions, channel allowlists. |

### Loaded cogs

`config.INITIAL_EXTENSIONS` currently loads 20 cogs:

`admin`, `help`, `role`, `moderation`, `xp`, `blackjack`, `rps_tournament`, `utility`, `cleanup`, `channel`, `inventory`, `economy`, `counting`, `deathmatch`, `proof_channel`, `mining`, `diagnostic`, `chain`, `general`, `leaderboard`.

### Registered subsystems

`utils/subsystem_registry.SUBSYSTEMS` currently defines 20 subsystem identities:

`admin`, `moderation`, `economy`, `inventory`, `mining`, `xp`, `role`, `channel`, `cleanup`, `blackjack`, `deathmatch`, `rps_tournament`, `counting`, `chain`, `leaderboard`, `proof_channel`, `utility`, `general`, `help`, `diagnostic`.

Do not rename these without a data migration: subsystem names are persisted in panel/session/anchor state.

---

## 2. Runtime Architecture

### Startup flow

1. `bot1.py` configures logging, reporter, intents, and `commands.Bot`.
2. `main()` runs PID guard and validates/finalizes the subsystem registry.
3. `utils.db.init()` initializes the database and migrations.
4. `core.runtime.setup()` initializes runtime services.
5. `message_pipeline.setup(bot)` installs the single platform-level message listener.
6. Health server, session GC, and process-memory sampler start as supervised app tasks.
7. `_load_cogs()` loads `config.INITIAL_EXTENSIONS`.
8. Identity-contract validation runs after cog load.
9. Bot starts with `bot.start(config.DISCORD_BOT_TOKEN)`.

### Command flow

1. Discord message reaches `commands.Bot`.
2. `_channel_guard` rejects commands outside configured allowed channels unless `!force` is used.
3. `_governance_guard` resolves command policy and blocks disabled subsystems before cog execution.
4. Command handler runs.
5. `on_command_completion` records success metrics/latency.
6. `on_command_error` records denied/error metrics and sends user-facing feedback where allowed.

### Message pipeline flow

All raw `on_message` feature listeners have been consolidated into `core/runtime/message_pipeline.py`.

Current stage tiers:

| Stage | Order | Tier | Behavior |
|---|---:|---|---|
| `cleanup` | 10 | moderation | Deletes blocked commands/prohibited content and short-circuits. |
| `counting` | 10 | moderation/game validation | Deletes invalid counting messages and short-circuits. |
| `chain` | 10 | moderation/game validation | Deletes chain violations and short-circuits. |
| `xp` | 20 | reward | Awards XP to messages that survive moderation stages. |
| `rps_tournament` | 30 | game input | Captures RPS tournament/match-channel moves. |

The pipeline pre-filters bot-authored messages and DMs. Stage exceptions are isolated and logged; downstream stages continue unless a stage returns `short_circuit=True`.

### Interaction flow

1. `bot1.on_interaction` delegates to `core.runtime.interaction_router.dispatch`.
2. The router extracts the custom-id prefix.
3. Prefix handler must be registered with `interaction_router.register(prefix, handler)`.
4. Governance visibility is checked before session resolution and handler execution.
5. A runtime session is resolved or created for `(user, guild, channel, subsystem)`.
6. Handler runs with latency metrics and slow-path recording.

Unknown custom-id prefixes increment metrics and emit a one-shot warning per prefix.

### Persistent view restoration

Persistent panels subclass `core.runtime.persistent_views.PersistentView`, set `SUBSYSTEM`, and register their class. Persistent views are stateless sentinels; user/session state is resolved from DB and interactions. Anchor restoration happens during `on_ready` through `message_anchor_manager.restore_anchors(bot)`.

Two placement patterns exist:

- Pattern A: `PersistentView` in the cog file; supporting views in `views/<name>/`.
- Pattern B: `PersistentView` in `views/<name>/main_panel.py` and imported by the cog.

Do not mix both patterns inside one subsystem.

---

## 3. Core Infrastructure Map

| System | Canonical module | Notes for reuse |
|---|---|---|
| Message pipeline | `core/runtime/message_pipeline.py` | Register `MessageStage` objects. Do not add raw feature `on_message` listeners. |
| Guild resources | `core/runtime/guild_resources.py` | Use `resolve_channel`, `ensure_channel`, `resolve_role`, `resolve_member`, `resolve_member_by_name`, `member_display`, `resolve_settings_channel`. |
| Interaction router | `core/runtime/interaction_router.py` | Central prefix router for runtime-managed UI. |
| Persistent views | `core/runtime/persistent_views.py` | Restart-safe panel class registry and base ownership checks. |
| Sessions/state | `core/runtime/session_manager.py`, `state_store.py`, `session_gc.py` | Use for ephemeral UI/session state. |
| Anchors | `core/runtime/message_anchor_manager.py` | Persists/restores active panel message anchors. |
| Runtime tasks | `core/runtime/tasks.py` | Use for app-owned background task tracking outside entrypoint helpers. |
| Live updates | `core/runtime/live_update_scheduler.py` | Panel refresh scheduling. |
| Navigation | `core/runtime/navigation_stack.py` | Existing navigation/session primitive; potential setup wizard dependency. |
| Slow-path logging | `core/runtime/slow_path_log.py` | Used by command and interaction latency observability. |
| Governance | `governance/`, `services/governance_service.py` | Visibility/execution/cleanup policy surface. |
| Diagnostics | `services/diagnostics_service.py`, `cogs/diagnostic_cog.py` | Health snapshots and operator-facing diagnostics. |
| Moderation audit | `services/moderation_service.py` | Single audited moderation mutation path; includes `auto_delete`. |
| Economy audit | `services/economy_service.py` | Required path for balance mutation. |
| XP audit | `services/xp_service.py` | Required path for XP mutation. |
| DB migrations | `utils/db/migrations.py` | Forward-only `.sql` files under advisory lock. |
| Registry | `utils/subsystem_registry.py` | Immutable subsystem/capability/source-of-truth manifest. |
| Help menu | `cogs/help_cog.py` | Governance-aware direct-navigation help surface. |
| Base views | `views/base.py` | Shared view lifecycle/error/permission helpers. |

---

## 4. Dependency Direction Rules

Current binding direction from `docs/architecture.md`:

- `cogs -> services`, `cogs -> core/runtime`, `cogs -> utils/db` reads.
- `views -> services`, `views -> discord`, shared view helpers. Views must not import other cogs.
- `services -> utils/db` and `services -> core/events`.
- `governance -> utils/db.governance` and runtime/session/event primitives.
- `core/runtime -> utils/db/*` is allowed for runtime persistence.
- `core/runtime -> cogs` is disallowed.
- `core/runtime -> services` is generally disallowed by architecture, but note that `message_pipeline._route_moderation_action` currently imports `services.moderation_service` as a deliberate integration hook. Treat this as existing implementation reality, not a general precedent.
- `utils/db -> anything outside utils` is disallowed.
- Production code must not mutate shared balances/XP outside the appropriate service layer.

Setup/dashboard work should preserve: UI surfaces consume runtime/services; they do not own persistence or policy.

---

## 5. Existing Reusable Primitives for Setup Platform Work

| Need | Reuse first |
|---|---|
| Channel selection/resolution | `core.runtime.resources.resolve_channel`, `ensure_channel`; `views/channels/*` selector flows. |
| Role selection/resolution | `core.runtime.resources.resolve_role`; `views/roles/*` helpers and selectors. |
| Member lookup/display | `resolve_member`, `resolve_member_by_name`, `member_display`. |
| Settings-bound channel lookup | `resolve_settings_channel`. |
| Governance visibility/execution | `governance.GovernanceContext`, `services.governance_service.resolve_visibility`, `resolve_command_policy`. |
| Command/subsystem discovery | `utils.subsystem_registry.SUBSYSTEMS`, `COMMAND_TO_SUBSYSTEM`, `all_subsystems_sorted()`. |
| Help navigation | `HelpPanelView`, `build_help_menu_view(interaction)` hook on cogs. |
| View lifecycle | `views.base.BaseView`, `HubView`, `send_panel`, interaction helpers. |
| Persistent dashboard panels | `PersistentView`, panel anchors, runtime sessions. |
| Diagnostics snapshots | `diagnostics_service.register(...)`; `DiagnosticCog` platform commands. |
| Audited moderation | `moderation_service.auto_delete`, `warn`, `timeout`, `kick`, `ban`, `clear_warnings`. |
| Background tasks | `_supervised_task` in entrypoint, `core.runtime.tasks.spawn` elsewhere. |
| Config/settings storage | `guild_settings` via `utils.db`; future setup work should centralize hot-path config rather than add cog-local caches. |
| Migration safety | `utils/db/migrations.py`; new schema as new `.sql`, never edit old migrations. |

---

## 6. Current Platform Constraints

- No scattered raw feature `on_message` listeners. Use `MessageStage` and the message pipeline.
- Use guild resource helpers instead of raw `guild.get_*` where applicable.
- Preserve persistent view registration and anchor restoration patterns.
- Avoid cog-local reinvention of runtime primitives.
- UI consumes runtime/services and should not own persistence.
- Cross-domain mutations go through services or orchestration services.
- Registry metadata is immutable after startup validation.
- Governance is platform-level: disabled subsystems block commands and routed interactions.
- Migrations are forward-only and idempotent.
- Process-local registries are single-process assumptions; do not silently design sharding/multiprocess features without ADR/migration.
- Feature/setup changes should be small, testable, and reviewable.

---

## 7. Setup Platform Relevance Map

| Subsystem | Setup/governance relevance |
|---|---|
| `admin` | Cog lifecycle controls; useful model for delegated admin and operator gates. |
| `diagnostic` | Health checks, identity contract, runtime repair surface, setup validation pages. |
| `help` | Existing navigation framework and direct panel-opening pattern. |
| `channel` | Resource provisioning and channel/category permission workflows. |
| `role` | Role templates, governance scopes, selector UX. |
| `moderation` | Audited policy examples and permission/role hierarchy checks. |
| `cleanup` | Per-channel cleanup rules and command/content policy patterns. |
| `xp` | Participation/reward settings, notification examples, role threshold linkage. |
| `economy` | Audited service mutation and log-channel provisioning examples. |
| `inventory` | Dependent subsystem example; should inherit economy availability. |
| `mining` | Participation/reward loop and persistent view example. |
| `counting` | Participation-aware game channel setup, message-stage validation, per-channel state. |
| `chain` | Channel-scoped rules and message-stage validation. |
| `rps_tournament` | Tournament/channel provisioning, ephemeral game state, game-input pipeline stage. |
| `blackjack` | Game UI/state lifecycle; caution around cog-local state boundaries. |
| `deathmatch` | Challenge/match participation model. |
| `proof_channel` | Timed access and permission-bound resource management. |
| `leaderboard` | Cross-subsystem read-model and display aggregation. |
| `utility` | Low-risk general commands and visibility examples. |
| `general` | General onboarding/info panel candidate. |

---

## 8. Implementation Readiness

### Already reusable

- Subsystem registry and capability metadata.
- Governance visibility/execution checks for commands and interactions.
- Guild resource resolver for channels/roles/members/settings-bound channels.
- Message pipeline with invariant test.
- Persistent view base and panel-anchor restoration.
- Help menu direct-navigation hook.
- Diagnostic command surface and snapshot registration pattern.
- Service-layer audit/event mutation paths.

### Extract first for setup platform

1. Shared UI selectors: channel selector, role selector, subsystem selector, capability selector.
2. Central setup transaction model: draft -> validate -> preview -> apply -> rollback.
3. Guild resource provisioning service: channel/category/role creation as planned operations, not direct button-side effects.
4. Governance/config write orchestrator: one path for setup changes that touches visibility, permissions, cleanup policy, notification preferences, and resource bindings.
5. Diagnostics validators for setup drafts before applying changes.
6. Reusable panel/navigation framework for wizard/dashboard pages.

### Do not touch yet unless required

- Core game rules for blackjack/rps/deathmatch unless setup integration needs metadata extraction only.
- Old migrations; add new migration files only.
- Registry identity strings.
- Service mutation contracts for economy/xp/moderation.
- Existing working help direct-navigation behavior.

### Hidden coupling and drift candidates

- Some cogs still contain both command logic and substantial UI/modal code; setup should not copy these patterns into a giant setup cog.
- `chain_cog.py` uses `self.bot.get_channel(...)` in display/list rendering; future resource cleanup may want a bot/guild-aware resource-display abstraction.
- `message_pipeline._route_moderation_action` imports `services.moderation_service` from runtime despite the general layer rule. Treat as a targeted existing exception.
- `config.ALLOWED_CHANNELS` and cleanup whitelist are environment-driven static sets; setup platform work likely needs a migration path toward per-guild configurable command channels.
- `COMMAND_TO_SUBSYSTEM` is explicitly transitional; future command metadata should prefer command extras/decorators.
- Several features still rely on process-local state; setup work must classify new state as authoritative, cached config, process-local, or ephemeral session.

### High-risk files

| File | Risk reason |
|---|---|
| `disbot/bot1.py` | Startup, guards, task lifecycle, identity validation. |
| `disbot/utils/subsystem_registry.py` | Identity/capability source of truth; startup validation. |
| `disbot/core/runtime/message_pipeline.py` | Single message listener and stage ordering. |
| `disbot/core/runtime/interaction_router.py` | Central routed interaction dispatch and governance gate. |
| `disbot/core/runtime/persistent_views.py` | Persistent panel restart contract. |
| `disbot/core/runtime/message_anchor_manager.py` | Anchor persistence/restoration. |
| `disbot/governance/*` | Visibility/execution/cleanup policy. |
| `disbot/utils/db/migrations.py` | Schema bootstrapping and migration sequencing. |
| `disbot/cogs/help_cog.py` | Help/direct-navigation UX and panel anchor handling. |
| `disbot/cogs/cleanup_cog.py` | Moderation-stage behavior and cleanup policy. |
| `disbot/cogs/counting_cog.py` | V/M/A state handling and pipeline stage registration. |
| `disbot/cogs/chain_cog.py` | Message-stage enforcement plus embedded UI. |

---

## 9. Quick Reference Tables

### Important modules

| Module | Purpose |
|---|---|
| `core/runtime/message_pipeline.py` | Ordered message-stage orchestrator. |
| `core/runtime/guild_resources.py` | Unified guild resource resolver. |
| `core/runtime/interaction_router.py` | Custom-id prefix router. |
| `core/runtime/persistent_views.py` | Persistent view registry/base. |
| `core/runtime/message_anchor_manager.py` | Panel anchor persistence. |
| `core/runtime/session_manager.py` | Runtime sessions. |
| `utils/subsystem_registry.py` | Subsystem/capability manifest. |
| `services/governance_service.py` | Runtime governance policy resolution. |
| `services/moderation_service.py` | Audited moderation mutation path. |
| `services/economy_service.py` | Audited economy mutation path. |
| `services/xp_service.py` | Audited XP mutation path. |
| `views/base.py` | Shared view lifecycle helpers. |

### Important tests/invariants

| Test area | Contract |
|---|---|
| `tests/unit/runtime/test_message_pipeline_invariant.py` | No raw feature `on_message` listeners outside pipeline. |
| `tests/unit/runtime/test_guild_resources_invariant.py` | No raw guild resource lookup outside allowlist. |
| `tests/unit/registry/test_identity_contract.py` | Subsystem identity surfaces stay aligned. |
| `tests/unit/invariants/test_inv_f_economy_service.py` | Economy mutations go through service. |
| `tests/unit/invariants/test_inv_g_xp_service.py` | XP mutations go through service. |
| `tests/unit/invariants/test_no_raw_defer.py` | Interaction defers go through helper. |
| `tests/unit/runtime/test_events_catalogue.py` | EventBus names are catalogued. |
| `tests/unit/runtime/test_tasks.py` | Task spawning/lifecycle contract. |

### Known extension points

| Extension point | Add through |
|---|---|
| New message behavior | `MessageStage` + registration in cog lifecycle. |
| New persistent panel | `PersistentView` subclass + registry + anchor handling. |
| New routed UI prefix | `interaction_router.register(prefix, handler)`. |
| New subsystem | `SUBSYSTEMS`, cog extension, commands, optional persistent view, tests. |
| New audited mutation | Service-layer function + DB helper + event catalogue entry. |
| New DB schema | New forward-only `.sql` migration. |
| New setup page | Reusable UI framework + orchestration service; avoid cog-local persistence. |
| New diagnostic | `diagnostics_service.register(name, snapshot_fn)`. |

---

## 10. Next Implementation Direction

Do not restart the architecture plan. Continue with the accepted setup/configuration roadmap by extracting reusable primitives before assembling the wizard:

1. Create a setup domain package, but keep it orchestration-only at first.
2. Add shared selector components for subsystem/channel/role/capability/resource selection.
3. Add a draft setup model and validation service.
4. Add preview/apply/rollback transaction boundaries.
5. Add diagnostics checks that can validate setup drafts and live guild state.
6. Add setup dashboard pages that consume those services.
7. Only then wire first-run onboarding and setup command surfaces.

The setup system should coordinate existing primitives; it should not become a giant cog or duplicate governance/resource/config logic.
