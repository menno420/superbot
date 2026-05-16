# SuperBot — Architecture

> **Status:** binding. This document defines the platform's layering
> and dependency rules.  CI invariants (`tests/unit/invariants/`) +
> ruff config enforce a subset; everything else is enforced by review.

SuperBot is a Discord-native application platform built on a single
Python process running `discord.py` + `asyncpg`.  The codebase is
organised in concentric layers so that:

1. The **runtime platform** (sessions, anchors, interaction routing,
   governance, EventBus) is independent of any individual feature.
2. **Subsystems** (cogs) are isolated units of feature logic, each
   owning its own table set and visibility/cleanup policy.
3. **Cross-subsystem state** (balances, XP, governance writes) is
   only mutated through **services** that audit + emit events.

A new contributor should be able to add a subsystem without learning
how panels, sessions, governance, or restoration work — those are
platform concerns the cog simply *uses*.

---

## Layer diagram

```
                       ┌─────────────────────────────────┐
                       │           bot1.py               │
                       │  events · guards · _load_cogs   │
                       └────────────────┬────────────────┘
                                        │
         ┌──────────────────────────────┴────────────────────────────┐
         │                                                           │
   ┌─────▼─────────────┐    ┌──────────────────────┐    ┌────────────▼────────┐
   │   cogs/  (×20)    │    │  core/runtime/       │    │   governance/      │
   │  thin dispatchers │◀──▶│  platform primitives │◀──▶│   policy engine    │
   └─────┬─────────────┘    └──────────┬───────────┘    └──────────┬─────────┘
         │                             │                            │
         │ ▼ delegates to              │ ▼ uses                     │ ▼ writes via
   ┌─────▼─────────────┐    ┌──────────▼───────────┐    ┌──────────▼─────────┐
   │   views/<sub>/    │    │   services/         │    │  GovernanceMutation │
   │  (UI components)  │    │  (audited mutations) │    │   Pipeline          │
   └─────┬─────────────┘    └──────────┬───────────┘    └──────────┬─────────┘
         │                             │                            │
         └──────────────┬──────────────┴────────────┬───────────────┘
                        ▼                           ▼
              ┌──────────────────┐         ┌────────────────────┐
              │ utils/  (helpers)│         │ utils/db/   (CRUD) │
              └──────────────────┘         └────────┬───────────┘
                                                    │
                                                    ▼
                                          ┌────────────────────┐
                                          │ PostgreSQL         │
                                          │ (15 migrations)    │
                                          └────────────────────┘
```

### Layers

| Layer | Purpose | What it knows |
|---|---|---|
| **bot1.py** | Process entrypoint. Sets up `commands.Bot`, the global checks, the governance gate, cog loading, identity-contract validation. | Discord, all of the above. |
| **cogs/** | Subsystem business logic — Discord command handlers, listeners, panel UX. | services/, views/, utils/db/, governance/ (read-side: `get_visible_subsystems`). |
| **views/** | Reusable UI components per subsystem.  Mirrors `views/roles/*` as the reference pattern. | `discord.ui.View`, `BaseView`, `PersistentView`. May call services. May *not* import cogs. |
| **services/** | Audited cross-subsystem mutation paths (economy, xp, governance). The **only** legitimate writers of shared state. | `utils/db/*`, `core/events.bus`, audit-log tables. |
| **governance/** | Per-guild visibility/execution/cleanup policy engine.  Strict internal layer order; see `governance/__init__.py` docstring. | `utils/db/governance`, `utils/db/sessions`, `core/events.bus`. |
| **core/runtime/** | Platform primitives: session manager, panel anchor manager, interaction router, EventBus, scheduler, persistent views, navigation stack, identity contract, managed tasks. | `utils/db/*`, `core/events.bus`. May *not* import cogs or services. |
| **utils/** | Pure helpers (cooldowns, embeds, settings keys, etc.) — no I/O. | Standard library, `discord`. |
| **utils/db/** | All Postgres access lives here.  Per-feature submodules host CRUD; `utils/db/pool` owns the asyncpg pool and primitives. | asyncpg. Nothing else. |

### Ownership boundary

The contract for every horizontal arrow in the diagram:

- **Allowed:** `cogs → services`, `cogs → core/runtime`, `cogs → utils/db` (reads).
- **Allowed:** `services → utils/db` (any direction).
- **Allowed:** `services → core/events` (emit events).
- **Allowed:** `governance → utils/db.governance`.
- **Allowed:** `core/runtime → utils/db/*`.
- **Disallowed:** `cogs → cogs` direct imports (use the EventBus or a service).
- **Disallowed:** `services → cogs`.
- **Disallowed:** `core/runtime → cogs`.
- **Disallowed:** `core/runtime → services` (services use core; not vice versa).
- **Disallowed:** `utils/db → anything outside utils`.
- **Disallowed:** any production code calling `db.add_coins` /
  `db.set_coins` outside the economy_service allowlist (INV-F).

A formal allowlist is documented in `docs/ownership.md`.

---

## Subsystem identity contract

Every subsystem name appears in **five** places, and **all five must
agree**:

1. `utils/subsystem_registry.SUBSYSTEMS` key
2. `cogs.*` `@commands.command(name="…")` declarations matching the
   registry's `entry_points`
3. `core.runtime.persistent_views._REGISTRY` (i.e. `PersistentView.SUBSYSTEM`)
4. `core.runtime.interaction_router._handlers` prefix
5. `panel_anchors.subsystem` and `runtime_sessions.subsystem` rows

`utils.subsystem_registry.validate_identity_contract` runs at startup
to surface drift; the regression test is at
`tests/unit/registry/test_identity_contract.py`.

### Subsystem identity strings are persisted

Renaming a subsystem requires a coordinated data migration because
existing rows in `panel_anchors` and `runtime_sessions` carry the old
string.  **Do not rename a subsystem in place.**

---

## Runtime invariants (CI-enforced)

| ID | Statement | Enforced by |
|---|---|---|
| INV-A | Every `bus.emit`/`bus.on` event name is in `core/events_catalogue.KNOWN_EVENTS`. | `core/events.py` warns + emits `unknown_event_total`; tests in `tests/unit/runtime/test_events_catalogue.py`. |
| INV-B | Subsystem identity strings agree across the five surfaces above. | `validate_identity_contract` at startup; regression tests `tests/unit/registry/test_identity_contract.py`. |
| INV-C | At most one `panel_anchors` row per `(user, channel, subsystem)`. | DB UNIQUE constraint (migration 008). |
| INV-D | At most one `runtime_sessions` row per `(user, channel, subsystem)`. | DB UNIQUE constraint (migration 007). |
| INV-E | Every governance write flows through `GovernanceMutationPipeline`. | Regression test in `tests/unit/help/test_help_navigation.py` (`test_apply_template_uses_pipeline`). |
| INV-F | Every balance mutation flows through `services.economy_service`. | AST scan `tests/unit/invariants/test_inv_f_economy_service.py`. |
| INV-G | Every XP mutation flows through `services.xp_service`. | AST scan `tests/unit/invariants/test_inv_g_xp_service.py`. |
| INV-H | `SUBSYSTEMS` registry is deep-frozen after `validate_registry()`. | `MappingProxyType` raises on mutation. |
| INV-I | Migrations are idempotent and run under `pg_advisory_lock`. | `utils/db/migrations.run_migrations`. |
| INV-J | Cog load failures register the subsystem as INTERNAL. | `bot1._load_cogs`. |
| INV-K | Every `asyncio.create_task` outside the entry-point layer uses `core.runtime.tasks.spawn`. | Regression tests `tests/unit/runtime/test_tasks.py`; new naked `create_task` calls trigger code review. |
| INV-L | Every interaction handler that performs I/O defers within 2 s, via `safe_defer`. | `core.runtime.interaction_helpers.safe_defer` + AST scan `tests/unit/invariants/test_no_raw_defer.py` (bans raw `interaction.response.defer(` outside the helper). |
| INV-M | No `print()` under `disbot/` (other than `tests/`). | Ruff rule `T20`. |
| INV-N | No bare `datetime.utcnow()` in production. | Ruff rule `DTZ003`. |

---

## Single-process assumption

Every in-process registry below is documented as **process-local**.
Replacing them with shared backends is `Phase Sc` work; until then
SuperBot runs as one shard, one process.

| Registry | File | Eventual substitution |
|---|---|---|
| `EventBus._handlers` | `core/events.py` | Redis pub/sub |
| `governance.cache._CACHE` / `_CACHE_VERSION` | `governance/cache.py` | Redis cache w/ version stamps |
| `governance.execution._OVERRIDES` | `governance/execution.py` | Redis |
| `persistent_views._REGISTRY` | `core/runtime/persistent_views.py` | stays process-local (class registry) |
| `interaction_router._handlers` | `core/runtime/interaction_router.py` | stays process-local |
| `live_update_scheduler._REGISTRATIONS` / `_last_edit` | `core/runtime/live_update_scheduler.py` | Redis for `_last_edit`; registrations stay local |
| `tasks._TASKS` | `core/runtime/tasks.py` | stays process-local |
| `navigation_stack._locks` | `core/runtime/navigation_stack.py` | stays process-local (acquired only when same-process serialisation matters) |

---

## Where to add a new subsystem

1. Register the subsystem in `utils/subsystem_registry.SUBSYSTEMS` (key,
   entry_points, capabilities, visibility_tier, …).
2. Add the cog file `disbot/cogs/<name>_cog.py`.
3. Make the cog import path `cogs.<name>_cog` part of
   `config.INITIAL_EXTENSIONS`.
4. If the subsystem has a panel UI, subclass
   `core.runtime.persistent_views.PersistentView`, set
   `SUBSYSTEM = "<name>"`, and `@register` the class.
5. Use the **service layer** for any mutation that another subsystem
   might also need (balances, XP, governance writes, future shared
   state).  Do NOT call `db.add_coins` or `db.set_coins` directly —
   route through `services.economy_service`.
6. Use catalogued event names if you `bus.emit`.  Add new names to
   `core/events_catalogue.KNOWN_EVENTS` before emitting them.
7. Hold task references via `core.runtime.tasks.spawn(name, coro)`.
8. Defer slow interaction handlers via
   `core.runtime.interaction_helpers.safe_defer`.
9. Write tests for the subsystem's math/logic; aim to land them in
   `tests/unit/<area>/` in the same PR as the feature.

The `role_cog` + `views/roles/*` directory is the reference pattern
when the cog grows past ~400 LOC.
