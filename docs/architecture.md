# SuperBot — Architecture

> **Status:** `binding` — This document defines the platform's layering
> and dependency rules.  CI invariants (`tests/unit/invariants/`) +
> ruff config enforce a subset; everything else is enforced by review.
>
> **Orientation:** new agent? Read `docs/AGENT_ORIENTATION.md` first
> — it indexes the binding docs and distinguishes them from the
> historical roadmap material. Looking for "where does this code
> live"? See `docs/repo-navigation-map.md`. Adding or moving a
> helper? See `docs/helper-policy.md`.

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
   │   cogs/           │    │  core/runtime/       │    │   governance/      │
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
                                          │ (migrations)       │
                                          └────────────────────┘
```

### Layers

| Layer | Purpose | What it knows |
|---|---|---|
| **bot1.py** | Process entrypoint. Sets up `commands.Bot`, the global checks, the governance gate, cog loading, identity-contract validation. | Discord, all of the above. |
| **cogs/** | Subsystem business logic — Discord command handlers, listeners, panel UX. | services/, views/, utils/db/, governance/ (read-side: `get_visible_subsystems`). |
| **views/** | Reusable UI components per subsystem (ephemeral `BaseView` hubs, modals, selectors, child panels).  See "PersistentView placement" below for the entry-point convention. | `discord.ui.View`, `BaseView`, `PersistentView`. May call services. May *not* import cogs. |
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

## State classification

Every piece of mutable state in SuperBot belongs to exactly one of
four classes.  The class answers, in one place: where it lives, what
it survives, how it is invalidated, and what its eventual
substitution boundary is.

| Class | Lives in | Survives restart? | Survives process | Substitution boundary |
|---|---|---|---|---|
| **Authoritative persistent** | PostgreSQL | yes | yes | none — this IS the endpoint |
| **Process-local runtime** | module / instance dicts | no (rebuilt from DB) | no | Redis (per ADR-001 deferral) |
| **Cached config (derived)** | process-local with version stamp + TTL | no (lazy rehydrate) | no | Redis with TTL |
| **Ephemeral session** | `runtime_sessions` + `runtime_session_state` (TTL 2 h) | within TTL | within TTL | Redis with TTL |

### Authoritative persistent

Lives only in PostgreSQL.  Mutated only via `services/*` (audited;
see INV-F / INV-G).  Read by anyone within the layer rules above.
Examples: `economy_balances`, `xp_user`, `panel_anchors`,
`runtime_sessions`, `game_state` last-checkpoint rows.

### Process-local runtime

In-process dicts / sets / instances.  MUST be rebuildable from
authoritative state — a cold start of the bot recreates them lazily.
MUST register a `forget_guild` hook with `guild_lifecycle.teardown`
if scoped to a guild, and a cleanup hook with `session_gc` if scoped
to a session.  Examples: `governance.cache._CACHE_VERSION`,
`navigation_stack._locks`, `interaction_router._handlers`,
`persistent_views._REGISTRY`, `tasks._TASKS`.

### Cached config (derived)

A specialisation of process-local runtime that caches mostly-static
authoritative state.  Reads use version-stamped lookups (see
`governance.cache` for the reference shape).  Writes to the underlying
authoritative state MUST trigger explicit invalidation.  TTL is the
safety net, not the primary invalidation mechanism.  Hot-path guild
configuration flows through the `core/runtime/guild_config` primitive
— no ad-hoc per-cog caches.

There is no `services/quantum_cache.py` cache layer.  Do not add or
revive a service-level cache with that name as a shortcut around this
taxonomy: pick the row above, then use the documented owner (`guild_config`
for hot-path guild settings, `governance.cache` for governance-derived
lookups, or a feature-owned process-local cache with explicit invalidation
and teardown hooks).

### Ephemeral session

Lives in `runtime_sessions` + `runtime_session_state` (TTL = 2 h by
default; see `session_gc.SESSION_TTL`).  Reads/writes through
`core/runtime/session_manager` and `core/runtime/state_store`.
Cleaned by `session_gc._run_gc_loop`.  Examples: navigation_stack
screen contents, view-specific session payloads.

### Why this classification matters

Every new feature decision becomes mechanical:

- "I need a fast lookup of guild X's setting Y" → it is **cached
  config**; use `guild_config`.
- "I need a transient registry of who is currently in the matchmaking
  queue" → it is **process-local runtime**; document the `forget_guild`
  hook.
- "I need to persist a user's bet across restarts" → it is
  **authoritative persistent**; write through `services/economy_service`.
- "I need to remember which screen the user was on" → it is
  **ephemeral session**; use `core/runtime/state_store`.

Without this taxonomy the decision tree is re-derived in every
PR review.

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
for **splitting supporting UI** out of a cog when the cog grows past
~400 LOC.  See "PersistentView placement" below for the persistent-
panel entry-point convention; see "Subsystem decomposition" below for
the full splitting checklist.

For **read-heavy subsystems** (the BTD6 cog is the reference pattern),
prefer the query → view-model → embed sandwich:

* `services/<name>_query_service.py` (or equivalent) returns typed
  dataclasses from stored data; no view/cog imports.
* `services/<name>_view_model_service.py` composes query output into
  display-ready models that carry `freshness` + `context_id`. Embed
  builders consume VMs, not raw rows.
* `cogs/<name>/_*.py` + `views/<name>/*.py` hold the rendering and
  Discord-interaction logic only.

The BTD6 cog wires this through `build_*_view_model` builders in
`services/btd6_view_model_service.py` and shared rendering helpers in
`utils/btd6/` (`freshness_render`, `response_embed`, `context_footer`).

---

## Subsystem decomposition

When `cogs/<name>_cog.py` passes ~400 LOC it MUST be decomposed
according to the convention below.  New subsystems use the convention
from day one.  This codifies what "Where to add a new subsystem"
above sketches and what `role_cog` + `views/roles/*` already
demonstrates.

### Allowed packages for a single subsystem

```
cogs/<name>_cog.py             # entry-point: commands, listeners, persistent panel
cogs/<name>/                   # domain logic (pure, testable without Discord)
    __init__.py
    state_machine.py | rules.py | parsing.py | handler.py | ...
views/<name>/                  # UI: ephemeral hubs, modals, selectors, child panels
    __init__.py
    main_panel.py              # ephemeral !<name> entry point
    *_panel.py | *_view.py | _helpers.py
services/<name>_service.py     # cross-subsystem audited mutation — only when needed
```

### Hard ownership rules

| From | May import | MUST NOT import |
|---|---|---|
| `cogs/<name>_cog.py` | `cogs/<name>/`, `views/<name>/`, `services/`, `utils/`, `utils/db/`, `core/runtime/` | other `cogs/<other>_cog.py` (use EventBus or a service) |
| `cogs/<name>/` (domain) | `utils/`, `services/`, `core/runtime/` | `discord`, `views/`, other cogs |
| `views/<name>/` | `cogs/<name>/` (read), `services/`, `utils/`, `discord` | other cogs, `utils/db/` (reads only via service) |
| `services/<name>_*` | `utils/db/`, `core/events`, other `services/` | `cogs/`, `views/`, `discord` |

These extend the cross-layer rules in "Ownership boundary" above;
they do not relax any of them.

### Splitting checklist

When the cog grows past 400 LOC, ask in this order:

1. Is there a state machine?  → extract to
   `cogs/<name>/state_machine.py` (pure, no Discord).
2. Are there reusable rules / scoring / parsing?  →
   `cogs/<name>/<topic>.py` (pure).
3. Is there an on-message or callback handler that mutates shared
   state?  → extract to `cogs/<name>/handler.py` per the realtime
   pattern in "Realtime / event-driven systems" below.
4. Are there view classes > 100 LOC each?  →
   `views/<name>/<topic>_panel.py`.
5. Is there mutation that another subsystem might also need
   (balances, XP, audit)?  → existing service or new
   `services/<name>_service.py`.
6. Anything left in the cog file?  Only: command decorators,
   listener decorators, the `PersistentView` class (Pattern A),
   `setup()` function, `cog_load` / `cog_unload`.

### Reference implementations

- `role_cog.py` + `views/roles/*` — the canonical reference cited
  above in "Where to add a new subsystem".
- `cogs/counting_cog.py` + `cogs/counting/` — partial decomposition
  (`parsing`, `game_logic`, `_constants` extracted; the `on_message`
  handler is the next step per the realtime concurrency rules below).

---

## PersistentView placement

A subsystem's persistent panel (`PersistentView` subclass with
`SUBSYSTEM = "<name>"`) is the **identity-bearing** UI surface — its
class must be importable at module-load time so the
`persistent_views._REGISTRY` is populated before `restore_anchors`
runs at `on_ready`.  Two placements satisfy this invariant and both
are in production use:

### Pattern A — PersistentView in the cog file

The cog hosts the `PersistentView` class directly, alongside the
commands that open it.  Supporting child views, modals, selectors,
and ephemeral hubs live in `disbot/views/<name>/*`.

```
disbot/cogs/<name>_cog.py
    class <Name>PanelView(PersistentView):
        SUBSYSTEM = "<name>"
        ...
disbot/views/<name>/
    _helpers.py     # shared constants
    main_panel.py   # ephemeral BaseView for !<name> command
    *.py            # modals, selectors, child panels
```

Used by `help`, `mining`, `moderation`, and `role` (4 of 5
PersistentView-bearing subsystems).  Trade-off: the cog file grows
with both lifecycle and UI; mitigated by extracting supporting views
to `views/<name>/`.

### Pattern B — PersistentView in views/

The `PersistentView` lives in `disbot/views/<name>/main_panel.py`
and is re-exported by the cog via `from views.<name>.main_panel
import …`.  The cog file stays focused on commands and lifecycle.

```
disbot/cogs/<name>_cog.py
    from views.<name>.main_panel import <Name>PanelView   # re-export
disbot/views/<name>/
    main_panel.py
        class <Name>PanelView(PersistentView):
            SUBSYSTEM = "<name>"
            ...
```

Used by `economy` (1 of 5).  Trade-off: requires the import
side-effect (which runs `@register`) to happen at cog-load time —
the cog must import the view class for the registry to be populated
before `on_ready`.

### Which to use

Both patterns satisfy the identity contract (the `SUBSYSTEM` string
matches a `SUBSYSTEMS` key in `utils/subsystem_registry`), so
`!platform identity` reports clean for both.  Prefer **Pattern A**
for new subsystems unless the cog file is already very large; in
that case Pattern B keeps the cog under the ~400 LOC guideline.  Do
not mix patterns within a single subsystem.

---

## Realtime / event-driven systems

Cogs whose `on_message` listener or button/select callback mutates
shared in-process state MUST follow the **Validate / Mutate / Apply
(V/M/A)** pattern.  This is the official concurrency pattern for
hot-path handlers and applies equally to future systems
(tournaments, matchmaking, reaction games, limited-quantity drops).

### The Validate / Mutate / Apply pattern

```python
@dataclass(frozen=True)
class Decision:
    """All side-effects the handler must perform, computed under the lock."""
    # Whatever fields the caller needs: replies, reactions, deletions,
    # state-persistence flags, downstream events to emit, etc.
    ...

async def on_event(self, event):
    decision = await self._compute(event)        # VALIDATE + MUTATE — under lock
    await self._apply(decision, event)           # APPLY — outside lock

async def _compute(self, event) -> Decision:
    async with scope_locks.lock_for(event.scope_id):
        state = await self._load_state(event)    # cheap (cached / in-memory)
        if not self._is_valid(state, event):
            return Decision.reject(...)
        new_state = self._transition(state, event)
        await self._persist_state(new_state)     # cheap DB write, still under lock
        return Decision.accept(new_state, ...)

async def _apply(self, decision: Decision, event) -> None:
    # No state mutation here.  Just Discord I/O, event emission, log calls.
    ...
```

### Why this pattern, not just "smaller locks"

1. **Functional core, imperative shell.**  `_compute` is pure-ish
   (state-in, decision-out) and is unit-testable without Discord
   mocks.
2. **Lock scope bounded by computation, not by I/O.**  Slow Discord
   API calls cannot stall concurrent users in the same or other
   scopes.
3. **Race-free decisions.**  The decision and the state it was
   computed from are atomic.  There is no window where `_apply` could
   observe a state change the decision didn't see.
4. **Composable.**  `Decision` types from independent subsystems
   compose via the EventBus.
5. **Reusable.**  Tournaments, matchmaking, reaction games all fit
   this shape.

### Rules

- Discord I/O calls (`message.edit`, `message.delete`,
  `message.channel.send`, `message.add_reaction`,
  `interaction.response.*`, `interaction.followup.*`) MUST NOT
  appear inside a `scope_locks.lock_for(...)` block.
- The `Decision` dataclass MUST be `frozen=True`.
- The scope ID is a caller-defined string with a subsystem prefix:
  `f"counting:channel:{channel_id}"`, `f"tournament:{tournament_id}"`,
  `f"matchmaking:{mode}:{guild_id}"`.  The prefix lets
  `!platform locks <prefix>` filter.
- When a scope ends (`end_match`, `tournament_complete`, channel
  deleted), the cog MUST call `scope_locks.forget(scope_id)`.
  `session_gc` provides an idle-eviction safety net but is not the
  primary cleanup path.

### Reference implementation

`disbot/cogs/counting_cog.py` + `disbot/cogs/counting/handler.py`
(post-Phase S2.1 — the existing pre-pattern listener is the
counterexample documented in the stabilization plan).
