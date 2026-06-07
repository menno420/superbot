# SuperBot — Repo Navigation Map

> **Status:** `binding` — (reference material). Describes the current
> layout of the bot tree, who owns which directory, and where to put
> new code. Companion to `docs/architecture.md` (conceptual layering)
> and `docs/ownership.md` (per-table / per-service ownership). This
> file is **path-level** orientation; the other two are
> **contract-level**.
>
> **How to use:** when you do not know which folder a piece of code
> belongs in, find the row here that matches the responsibility and
> follow the link. When a row says "see X for rules", do not put new
> code there before reading X.

---

## Top-level tree

```
superbot/
├── disbot/                  # Python source — everything that runs in production
│   ├── bot1.py              # entry point; commands.Bot construction; cog loading
│   ├── config.py            # env-loaded config + INITIAL_EXTENSIONS list
│   ├── guild_lifecycle.py   # join/leave teardown, forget_guild fan-out
│   ├── healthserver.py      # /health, /ready, /metrics HTTP probes
│   ├── cogs/                # discord.py extensions — subsystem entry points
│   ├── core/                # platform primitives (runtime, resources)
│   ├── data/                # static JSON data (general_content.json, …)
│   ├── governance/          # per-guild visibility/cleanup/capability engine
│   ├── migrations/          # numbered .sql files; idempotent; advisory-locked
│   ├── services/            # audited mutation paths + cross-subsystem logic
│   ├── utils/               # leaf helpers + DB access + settings keys
│   └── views/               # Discord UI: panels, modals, selectors, hubs
├── docs/                    # reference docs — see AGENT_ORIENTATION.md
├── tests/                   # pytest tree, mirrors disbot/ layout
├── .claude/                 # Claude Code config (CLAUDE.md, settings.json)
├── .codegraph/              # CodeGraph index (built artifact; not in git)
├── .github/workflows/       # CI (code-quality.yml + ai-evals.yml)
├── pyproject.toml           # black, isort, ruff, mypy, pytest config
├── requirements.txt         # runtime deps
└── Procfile                 # process declaration (deployment)
```

There is intentionally **no top-level README** — `docs/` is the
documentation surface. There is intentionally **no `__init__.py`
content in `disbot/` itself** — `core/`, `services/`, and `views/`
have empty package inits; `cogs/__init__.py` carries the canonical
subsystem-decomposition pointer; `governance/__init__.py` re-exports
the public governance API; `utils/db/__init__.py` re-exports the DB
layer.

---

## Where major systems live

| Concern | Path | Owner notes |
|---|---|---|
| Process entry point | `disbot/bot1.py` | Cog loading, global checks, governance gate, signal handling, identity-contract validation. **Do not add subsystem logic here.** |
| Static config | `disbot/config.py` | Env vars, `INITIAL_EXTENSIONS`, channel allow-lists. **Order of `INITIAL_EXTENSIONS` matters** (`bootstrap_access_cog` first — see comment). |
| HTTP probes | `disbot/healthserver.py` | `/health`, `/ready`, `/metrics`. |
| Guild lifecycle | `disbot/guild_lifecycle.py` | `teardown` fans `forget_guild` and `delete_for_guild` calls across every guild-keyed surface. **Every new guild-scoped cache or table must register here.** |
| Cogs | `disbot/cogs/<name>_cog.py` (+ `disbot/cogs/<name>/`) | One file per subsystem entry; private domain logic in the sibling package. See `docs/architecture.md` § "Subsystem decomposition". |
| Services (mutation) | `disbot/services/<name>_service.py` or `<name>_mutation.py` | Audited writers. See `docs/ownership.md` § "Service ownership". |
| Pure-domain services | `disbot/services/blackjack_engine.py`, `disbot/services/cog_routing_profiles.py`, … | Stateless math / catalogue logic. May be called from cogs and other services. |
| Lifecycle contract | `disbot/services/lifecycle/` (`contracts.py`) | Shared request/preview/result/reversibility/outcome types + `emit_lifecycle_audit` for *change* ops (rename/move/delete/create/edit) that `ResourceProvisioningPipeline` does not own. Consumers: `services/channel_lifecycle_service.py`, `services/role_lifecycle_service.py`. See `docs/resource-provisioning-overview.md` § "Sibling lane". |
| Platform runtime | `disbot/core/runtime/` | EventBus consumers, session_manager, panel_manager, interaction_router, navigation_stack, tasks supervisor, persistent_views, identity contract, etc. **Must not import cogs or services.** |
| Resources runtime | `disbot/core/resources/` | Typed Discord-resource discovery / mutation / status. |
| Governance | `disbot/governance/` | Visibility, cleanup, capability resolution + the `GovernanceMutationPipeline`. Strict internal layer order (see `governance/__init__.py` docstring). |
| Database (CRUD) | `disbot/utils/db/<feature>.py` | All asyncpg use. Submodules are leaves of the dep graph. See `docs/ownership.md` § "Dependency direction". |
| DB pool | `disbot/utils/db/pool.py` | The only place that opens an asyncpg pool. |
| Migrations | `disbot/migrations/NNN_*.sql` | Idempotent; advisory-locked; run by `utils/db/migrations.py`. **Next free number is the highest existing + 1.** |
| Settings keys | `disbot/utils/settings_keys/*.py` | Typed constants for `guild_settings` rows. |
| Subsystem registry | `disbot/utils/subsystem_registry.py` | Single source of truth for subsystem metadata. Frozen after `validate_registry()`. |
| Hub registry | `disbot/utils/hub_registry.py` | Mother-hub presentation metadata (Help category index). Display only — no business logic. |
| UI views | `disbot/views/<subsystem>/` | Per-subsystem panels, modals, selectors. **Must not import other cogs.** |
| Shared view primitives | `disbot/views/base.py` | `BaseView`, `HubView`, `send_panel`, `handle_view_error`. |
| Shared navigation | `disbot/views/navigation.py` | `attach_back_button`, `BackTarget`. Canonical back-button helper. **No second navigation helper module.** |
| Shared selectors | `disbot/views/selectors/` | Re-usable Discord selector primitives. |
| Tests | `tests/unit/<area>/` | Mirrors the source tree. Doc-pin tests live in `tests/unit/docs/`. |
| Architecture invariant tests | `tests/unit/invariants/` | INV-F, INV-G, INV-L AST checks. |
| ADRs | `docs/decisions/NNN-*.md` | Architecture Decision Records. Immutable once landed. |

---

## Helper locations at a glance

Helper rules live in `docs/helper-policy.md`. The map below is just
"where do existing helpers live today?" so you can find prior art.

### Currently in `disbot/utils/` (leaf helpers, no I/O except DB layer)

| File | Contains | Notes |
|---|---|---|
| `utils/helpers.py` | `_parse_member`, `safe_select_emoji`, `post_log_embed`, `normalize_name`, `CogMenuView` | **Grab-bag — do not add new helpers here.** See `docs/helper-policy.md` for routing rules. |
| `utils/embeds.py` | `success`, `error`, `info`, `warning`, `server_info_embed`, `user_info_embed` | Underused — most cogs build `discord.Embed` inline. Treat as legacy; do not promote into. |
| `utils/channels.py` | `safe_channel_name`, `get_or_create_category`, `create_private_channel`, `cleanup_category` | Direct Discord channel manipulation. Prefer `services/resource_provisioning.py` for any **new** channel creation. |
| `utils/cooldowns.py` | `check_cooldown`, `format_remaining` | Time-window math. Pure. |
| `utils/visibility_rules.py` | tier helpers | Read-only governance helpers. |
| `utils/role_feasibility.py` | `evaluate_role`, `manageable_roles`, `not_everyone`, `summarize_exclusions`, `RoleFeasibility` | Pure role manageability/exclusion model shared by selectors + services (stdlib + `discord` only). The single source of truth for "can I touch this role?". |
| `utils/synonyms.py` | `find_command` | Command-name fuzzy matching. |
| `utils/tournaments.py` | tournament math | Pure helpers shared between RPS / blackjack tournament cogs. |
| `utils/ui_constants.py` | color constants | UI palette. |
| `utils/hub_registry.py` | `HubEntry`, `HUBS` | Mother-hub presentation metadata. |
| `utils/subsystem_registry.py` | `SUBSYSTEMS`, validators | The canonical subsystem manifest. |
| `utils/guild_config_accessors.py` | typed read accessors | Guild config read surface (over `core.runtime.guild_config`). |
| `utils/user_config_accessors.py` | typed read accessors | Per-user / participation read surface. |
| `utils/db/<feature>.py` | per-table CRUD | The only place asyncpg lives. |
| `utils/settings_keys/*.py` | typed key constants | One file per subsystem. |

### Subsystem-private helpers (`disbot/cogs/<name>/_helpers.py`)

Used today by: `admin`, `blackjack` (split into `_persistence.py`,
`_state.py`, `actions.py`, `schemas.py`), `counting`
(`_constants.py`, `_stage.py`, `game_logic.py`, `handler.py`,
`parsing.py`), `diagnostic`, `economy`, `moderation`,
`rps_tournament`, `setup`, `xp`. The leading underscore signals
"private to this subsystem" — do not import these from another
subsystem.

### View-private helpers (`disbot/views/<name>/_helpers.py`)

Used today by: `views/channels/`, `views/roles/`, `views/rps/`. Same
underscore convention.

### Shared view primitives

- `disbot/views/base.py` — `BaseView`, `HubView`, `send_panel`,
  `handle_view_error`. Imported by ~73 files.
- `disbot/views/navigation.py` — back-button helper +
  `BackTarget`. Canonical. **Do not create a parallel
  navigation module.**
- `disbot/views/selectors/` — shared modal selectors.

### Help / routing helpers

- `disbot/cogs/help/route.py` — `HelpRoute`, `HelpOpener`,
  `resolve_route`, `open_route`. The shared resolver behind typed
  `!help <category>` and the Help dropdown. **No second resolver.**

---

## Where to put new code

Match the row in the table; if no row matches, the request likely
crosses a layer boundary and needs a contract decision (open an ADR
or read `docs/architecture.md` § "Ownership boundary" again).

| You want to add… | Put it in… | Mandatory references |
|---|---|---|
| A new Discord command for an existing cog | The cog file (or its sibling package if the cog is decomposed) | `docs/architecture.md` § "Subsystem decomposition"; `docs/building-roadmap/command-integration-standard.md` |
| A new subsystem | `disbot/cogs/<name>_cog.py` + `disbot/cogs/<name>/` + (if UI) `disbot/views/<name>/` | `docs/architecture.md` § "Where to add a new subsystem"; `docs/building-roadmap/mother-hub-map.md` |
| A new persistent panel (re-attached on restart) | A `PersistentView` subclass in the cog file (Pattern A) or `views/<name>/main_panel.py` (Pattern B) | `docs/architecture.md` § "PersistentView placement"; `docs/runtime_contracts.md` § 3 |
| A new modal / selector / child panel | `disbot/views/<subsystem>/` | `disbot/views/base.py` for `BaseView`; `disbot/views/navigation.py` for back buttons |
| A pure-domain rule / scoring function | `disbot/cogs/<name>/<topic>.py` (subsystem-local) or `disbot/services/<name>_engine.py` (shared) | `docs/architecture.md` § "Subsystem decomposition" step 1–2 |
| A new audited mutation | New method on the existing `services/<name>_service.py` or `<name>_mutation.py`, or a new service if no owner exists | `docs/ownership.md` § "Service ownership"; `docs/runtime_contracts.md` § 9 |
| A new DB table | `disbot/migrations/NNN_<name>.sql` (next free number) + new file in `disbot/utils/db/<name>.py` + register a `delete_for_guild` hook in `disbot/guild_lifecycle.py` if guild-keyed | `docs/architecture.md` INV-I; `docs/platform-consistency-ledger.md` § 3 |
| A new EventBus event | Add literal to `disbot/core/events_catalogue.KNOWN_EVENTS`; document in `docs/ownership.md` § "Event ownership"; emit from a service (never a cog) | `docs/architecture.md` INV-A; `docs/runtime_contracts.md` § 2 |
| A new background task | `core.runtime.tasks.spawn(name, coro)` | `docs/architecture.md` INV-K; `docs/runtime_contracts.md` § 7 |
| A new platform diagnostic | Register a provider in `services/diagnostics_service.py`; surface via `!platform <subcommand>` | `docs/subsystems/health-diagnostics.md`; `docs/platform-consistency-ledger.md` § 1 "Diagnostics"; `docs/smoke-test-checklist.md` |
| A new setting key | `disbot/utils/settings_keys/<subsystem>.py`; declare a `SettingSpec` in the cog or its service; write via `SettingsMutationPipeline` | `docs/subsystems/settings-bindings-provisioning.md`; `docs/settings-customization-roadmap.md`; `docs/building-roadmap/config-input-standard.md` |
| A new binding (Discord resource pointer) | Declare a `BindingSpec`; write via `BindingMutationPipeline`; never store IDs in `SettingSpec` | `docs/subsystems/settings-bindings-provisioning.md`; `docs/settings-customization-roadmap.md` § "Ownership invariants" |
| A new resource creation flow | Use `services/resource_provisioning.py` (`ResourceProvisioningPipeline`) | `docs/resource-provisioning-overview.md` |
| A new governance write | Use `governance/writes.py:GovernanceMutationPipeline` | `docs/ownership.md` INV-E |
| A new helper (any kind) | Read `docs/helper-policy.md` **first**. The default answer is "inline it" or "put it in the cog's own package". | `docs/helper-policy.md` |

---

## Where to look when something breaks

This duplicates `docs/runtime_contracts.md` § 11, but is reproduced
here as the navigation entry-point. The canonical table lives there.

| Symptom | First file | Most likely owner |
|---|---|---|
| "Interaction Failed" UX error | `core/runtime/interaction_router.py` | missing `safe_defer`, missing handler registration |
| Panel buttons unresponsive | `core/runtime/persistent_views.py` + `core/runtime/message_anchor_manager.py` | cog failed to load, view subsystem renamed |
| Help category shows commands that don't run | `utils/subsystem_registry.py:validate_identity_contract` + `!platform identity` | identity-contract drift |
| Balance "lost" coins | `services/economy_service.py` + `economy_audit_log` table | overdraft path; missing debit reason |
| Tournament didn't pay out | `services/economy_service.py` filtered on `tournament:*` reasons | service exception silenced |
| Bot eats CPU | `core/runtime/tasks.py` + `task_outcome_total` metric | runaway `tasks.spawn` loop |
| Migrations stuck | `utils/db/migrations.py` + `pg_stat_activity` | concurrent deploy holding the advisory lock |
| Boot aborts with `entry_point_missing_command` | `utils/subsystem_registry.py` + the cog that failed to load | identity-contract STRICT mode caught a real regression (see `docs/runtime_contracts.md` § 12) |

---

## Subsystem cheat sheet (cog → owning paths)

A condensed version of `docs/help-command-surface-map.md` and
`docs/ownership.md`. The full inventory lives in those files.

| Subsystem | Cog file | View package | Service / mutation path | DB module |
|---|---|---|---|---|
| admin | `cogs/admin_cog.py` (+ `cogs/admin/`) | — | n/a (uses governance) | n/a |
| ai | `cogs/ai_cog.py` (+ `cogs/ai/`) | `views/ai/` | `services/ai_gateway.py` (read-only); `services/ai_diagnostics_service.py`; `services/ai_policy_mutation.py` (audited writes); `services/ai_config_projection_service.py` (operator-facing read model); `services/ai_readiness_service.py` (chain-check scan) — see `docs/ai-config-ownership.md` (binding) | `utils/db/ai.py` — typed `ai_guild_policy` / `ai_channel_policy` / `ai_category_policy` / `ai_role_policy` / `ai_instruction_profile` / `ai_decision_audit` |
| blackjack | `cogs/blackjack_cog.py` (+ `cogs/blackjack/`) | `views/blackjack/` | `services/economy_service.py` (coins); `services/blackjack_engine.py` (math) | n/a |
| btd6 | `cogs/btd6_cog.py` (+ `cogs/btd6/`) | `views/btd6/` | `services/btd6_ai_service.py` (AI augmentation) | n/a in M1 (typed `btd6_*` source/strategy tables land in M3A/M4) |
| channel | `cogs/channel_cog.py` | `views/channels/` | `services/channel_lifecycle_service.py` (rename/move/delete) + `governance/writes.py` (visibility) + `services/resource_provisioning.py` (creation) | n/a |
| chain | `cogs/chain_cog.py` | — | direct CRUD | `utils/db/games/chain.py` |
| cleanup | `cogs/cleanup_cog.py` (+ `cogs/cleanup/`) | — | direct CRUD | `utils/db/moderation.py` |
| community | `cogs/community_cog.py` | `views/community/` | n/a (hub) | n/a |
| counting | `cogs/counting_cog.py` (+ `cogs/counting/`) | `views/counting/` | direct CRUD | `utils/db/games/counting.py` |
| deathmatch | `cogs/deathmatch_cog.py` (+ `cogs/deathmatch/`) | — | direct CRUD | `utils/db/games/deathmatch.py` |
| diagnostic | `cogs/diagnostic_cog.py` (+ `cogs/diagnostic/`) | `views/diagnostic/` | `services/diagnostics_service.py` (read-only providers) | n/a |
| economy | `cogs/economy_cog.py` (+ `cogs/economy/`) | `views/economy/` | `services/economy_service.py` | `utils/db/economy.py` |
| general | `cogs/general_cog.py` | — | reads `data/json/general_content.json` | n/a |
| help | `cogs/help_cog.py` (+ `cogs/help/`) | — | `cogs/help/route.py` (resolver) | n/a |
| inventory | `cogs/inventory_cog.py` | — | direct CRUD | `utils/db/inventory.py` |
| leaderboard | `cogs/leaderboard_cog.py` | — | read-only | reads multiple |
| logging | `cogs/logging_cog.py` (+ `cogs/logging/`) | — | `services/server_logging.py` | `utils/db/settings.py` |
| mining | `cogs/mining_cog.py` (+ `cogs/mining/`) | `views/mining/` | direct CRUD | `utils/db/games/mining.py` |
| moderation | `cogs/moderation_cog.py` (+ `cogs/moderation/`) | `views/moderation/` | `services/moderation_service.py` | `utils/db/moderation.py` |
| proof_channel | `cogs/proof_channel_cog.py` | — | `services/economy_service.py` (coins) | n/a |
| role | `cogs/role_cog.py` | `views/roles/` | role create/edit/delete via `services/role_lifecycle_service.py`; thresholds/reaction-roles direct CRUD | `utils/db/roles.py` |
| rps_tournament | `cogs/rps_tournament_cog.py` (+ `cogs/rps_tournament/`) | `views/rps/` | direct CRUD + `economy_service` | `utils/db/games/rps.py` |
| settings | `cogs/settings_cog.py` (+ `cogs/settings/`) | `views/settings/` | `services/settings_mutation.py` | `utils/db/settings.py` |
| setup | `cogs/setup_cog.py` (+ `cogs/setup/`) | `views/setup/` | `services/setup_operations.py` (+ companion services) | `utils/db/setup_session.py`, `utils/db/setup_draft.py` |
| utility | `cogs/utility_cog.py` | — | n/a | n/a |
| xp | `cogs/xp_cog.py` (+ `cogs/xp/`) | `views/xp/` | `services/xp_service.py` | `utils/db/xp.py` |

When this table and `docs/help-command-surface-map.md` disagree, the
latter is authoritative (it is pinned to the registry by
`tests/unit/docs/test_help_surface_map_doc.py`).

---

## Updating this file

Update this map when:

- A new top-level directory appears under `disbot/`.
- A subsystem is added, removed, or split.
- A helper category that did not exist is created (e.g. a new
  `services/` companion package).
- A "where to put new code" row becomes wrong because the canonical
  pipeline / location moved.

Do **not** update it for:

- New individual files inside an existing package.
- New subsystem-private helpers (those follow the helper policy and
  do not need a path-level callout).
- New commands within an existing cog.

If you find this file disagrees with reality, fix it in the same PR
that changes reality. There is no doc-pin test for this map; staleness
is the main risk.
