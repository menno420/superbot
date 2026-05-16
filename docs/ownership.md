# SuperBot — Ownership boundaries

> **Status:** binding. Every module/table/event listed here has a
> single owner that decides what is or isn't legal to do with it.
> Touching state owned by another subsystem requires going through
> that subsystem's service layer (or proposing a contract change).

---

## Owner taxonomy

- **Subsystem owner** — the cog that conceptually owns a feature
  (e.g. the `economy` subsystem owns the coin balance).
- **Service owner** — the `services/<name>_service.py` module that
  mediates writes to subsystem state crossed-by other subsystems.
- **Platform owner** — `core/runtime/*` or `governance/` modules that
  own infrastructure shared by every subsystem.

A piece of state with a service owner is **always** mutated through
that service.  No exceptions for cogs or other services.

---

## Service ownership

| Service | Owns | Writers must… |
|---|---|---|
| `services/economy_service.py` | every coin-balance mutation (`xp.coins` column, `economy_audit_log` rows) | call `credit`/`debit`/`transfer`/`bet_and_settle`/`refund`. No `db.add_coins`/`db.set_coins` outside the service.  INV-F (AST test). |
| `services/xp_service.py` | every XP mutation (`xp.xp` column, level transitions, XP row deletion) | call `award(...)` for grants and `reset(...)` for clears. No `db.add_xp`/`db.delete_xp` outside the service.  INV-G (AST test). |
| `services/moderation_service.py` | every moderation action (`warnings`, `mod_logs`, Discord ban/kick/timeout calls) | call `warn`/`timeout`/`kick`/`ban`/`unban`/`clear_warnings`. Emits `moderation.action_taken`. |
| `services/blackjack_engine.py` | pure card/hand/deck math (no I/O) | call `rank_value`/`hand_value`/`new_deck`/`hand_str`/`is_blackjack`. No copy-pasted card logic in cogs. |
| `services/game_state_service.py` | in-flight game state checkpoints (`game_state` table) | call `save`/`load`/`clear`/`list_active_for_subsystem`.  JSONB payload; cogs own their schemas. |
| `services/governance_service.py` (legacy shim) | the public surface re-exported from `governance/*` | re-exports only.  No business logic should live here. |
| `governance/writes.py:GovernanceMutationPipeline` | every governance write (subsystem_visibility, cleanup_policies, capability_overrides, audit log) | use the pipeline.  INV-E (`test_apply_template_uses_pipeline`). |

---

## Subsystem ownership

Each subsystem owns its data tables.  Other subsystems read freely;
writes must come from the owning cog or a shared service.

| Subsystem | Tables owned | Service path |
|---|---|---|
| `admin`        | (none — uses governance/diagnostic surfaces) | n/a |
| `help`         | (none — read-only on registry + governance)  | n/a |
| `diagnostic`   | (uses `logs` for queries)                    | n/a |
| `general`      | (loads `data/json/general_content.json`)      | n/a |
| `role`         | `role_thresholds`, `reaction_roles`            | direct via `utils/db/roles.py` |
| `moderation`   | `warnings`, `mod_logs`                         | `services/moderation_service.py` (preferred); `utils/db/moderation.py` direct for read-only / legacy callers |
| `xp`           | `xp.xp`, `xp.level`, `xp.messages`, `xp.last_xp` | `services/xp_service.py` |
| `economy`      | `economy`, `job_progress`, `economy_audit_log`   | `services/economy_service.py` |
| `inventory`    | `inventory`                                    | direct via `utils/db/inventory.py` |
| `cleanup`      | `prohibited_words`                             | direct via `utils/db/moderation.py` |
| `chain`        | `chain_channels`                               | direct via `utils/db/games/chain.py` |
| `counting`     | `counting_state`                               | direct via `utils/db/games/counting.py` |
| `mining`       | `mining_inventory`                             | direct via `utils/db/games/mining.py` |
| `deathmatch`   | `deathmatch_stats`                             | direct via `utils/db/games/deathmatch.py` |
| `rps_tournament` | `rps_players`, `rps_matches`                 | direct via `utils/db/games/rps.py`; balance mutations via economy_service |
| `blackjack`    | (uses `xp.coins`; tournament state in `guild_settings`) | balance via economy_service |
| `channel`      | (uses Discord API; visibility via governance)  | governance pipeline |
| `proof_channel`| (uses Discord API; balance via economy)        | economy_service |
| `utility`      | (no DB tables of its own)                      | n/a |
| `leaderboard`  | (reads every owner's tables; no writes)        | n/a |

### Shared columns

- `xp.coins` — **owned by economy**, NOT xp.  This is a historical
  layout where coins were colocated with XP for one PK. Writers
  must route through `economy_service`.  Readers may use
  `db.get_coins` / `utils/db/economy.get_coins` directly.

---

## Platform ownership

| Surface | Owner | Allowed writers |
|---|---|---|
| `panel_anchors` | `core.runtime.message_anchor_manager` | only the panel manager (via `upsert_panel_anchor`, `mark_panel_anchor_stale`). |
| `runtime_sessions` | `core.runtime.session_manager` | only session_manager. |
| `runtime_session_state` | `core.runtime.state_store` | only state_store (`set`, `set_many`, `delete`, `invalidate_guild_state`). |
| `subsystem_visibility` | `GovernanceMutationPipeline` | only the pipeline. |
| `cleanup_policies` | `GovernanceMutationPipeline` | only the pipeline. |
| `capability_execution_overrides` | `GovernanceMutationPipeline` | only the pipeline. |
| `governance_audit_log` | `GovernanceMutationPipeline` | append-only via the pipeline; never updated or deleted. |
| `governance_templates` | `governance.templates` | only the template API. |
| `economy_audit_log` | `services/economy_service.py` | append-only inside the service. |
| `game_state` | `services/game_state_service.py` | only the service.  JSONB payload per (guild, user, channel, subsystem). |
| `schema_migrations` | `utils/db/migrations.py` | only the migration runner. |

---

## Event ownership

The catalogue (`core/events_catalogue.KNOWN_EVENTS`) lists every
allowed event name.  Owners of each event:

| Event | Emitter | Payload keys |
|---|---|---|
| `governance.visibility.changed` | `GovernanceMutationPipeline.set_visibility` | `guild_id`, `subsystem`, `scope_type`, `scope_id`, `mutation_id` |
| `governance.cleanup.changed` | `GovernanceMutationPipeline.set_cleanup_policy` | `guild_id`, `scope_type`, `scope_id`, `mutation_id` |
| `governance.cache.invalidated` | every mutation pipeline path | `guild_id` |
| `governance.execution.allowed` | `governance.execution.resolve_execution` (success) | `guild_id`, `user_id`, `capability`, … |
| `governance.execution.denied` | `governance.execution.resolve_execution` (deny) | `guild_id`, `user_id`, `capability`, `reason` |
| `economy.balance_changed` | `services/economy_service.py` | `guild_id`, `user_id`, `delta`, `new_balance`, `reason` |
| `xp.awarded` | `services/xp_service.py` | `guild_id`, `user_id`, `delta`, `new_xp`, `new_level`, `source` |
| `xp.level_up` | `services/xp_service.py` | `guild_id`, `user_id`, `new_level`, `source` |
| `xp.reset` | `services/xp_service.py` | `guild_id`, `user_id`, `actor_id`, `source` |
| `moderation.action_taken` | `services/moderation_service.py` | `guild_id`, `target_id`, `actor_id`, `action` (`warn`/`timeout`/`kick`/`ban`/`unban`/`clear_warnings`), `reason` |

Adding a new event:
1. Add the literal string to `core/events_catalogue.KNOWN_EVENTS`.
2. Add a row to the table above.
3. Document the payload contract in the emitting module's docstring.

Without step 1 the bus warns (`unknown_event_total{event, op}`).

---

## Dependency direction (allow / disallow)

### Allowed imports

```
cogs/             →  services/, core/runtime/, utils/db/, views/, governance/ (read)
views/            →  services/, core/runtime/, utils/db/ (read)
services/         →  utils/db/, core/events
governance/       →  utils/db/governance, utils/db/sessions, utils/subsystem_registry,
                     utils/visibility_rules, utils/settings_keys, services/governance_exceptions
core/runtime/     →  utils/db/*, core/events, services/metrics
utils/db/<sub>    →  utils/db/pool, utils/db/codec
utils/db/pool     →  asyncpg
utils/<helper>    →  standard library, discord (no I/O)
```

### Disallowed imports

| Direction | Why |
|---|---|
| `cogs → cogs` | Inter-subsystem coupling. Use the EventBus or a service. |
| `services → cogs` | Reverse-direction dependency. Services don't know about UI. |
| `core/runtime → cogs` | Runtime must be feature-agnostic. |
| `core/runtime → services` | Services use core, not the other way. (Metrics is the lone exception — observability is universal.) |
| `utils → cogs` / `utils → services` / `utils → core/runtime` | Helpers are leaves of the dep graph. |
| `utils/db → anything outside utils` | The DB layer must be reusable from any other layer; no cycles. |
| Lazy / inside-function imports that bypass the rules above | The contract is the file-level import graph, not the call graph. Lazy imports are allowed only to break a *transient* cycle and must be commented as such. |

### Direct DB writes — explicit blocklist

These calls are **forbidden** outside their owning module:

| Symbol | Owner | Forbidden in |
|---|---|---|
| `db.add_coins` / `utils.db.economy.add_coins` | `services/economy_service.py` | every cog, every other service. |
| `db.set_coins` / `utils.db.economy.set_coins` | `services/economy_service.py` | every cog, every other service. |
| Raw SQL `UPDATE xp ... coins` / `INSERT INTO xp (..., coins ...)` | `services/economy_service.py` + `utils/db/economy.py` | every other production file. |
| `db.set_subsystem_visibility` / raw writes to `subsystem_visibility` | `GovernanceMutationPipeline` | every cog, every other service. |
| `db.set_cleanup_policy` / raw writes to `cleanup_policies` | `GovernanceMutationPipeline` | every cog, every other service. |
| `db.write_governance_audit` | `GovernanceMutationPipeline` | direct write only inside the pipeline. |

The first row is enforced by INV-F (AST test).  Add to that test
when introducing future forbid-lists.

---

## Mutation semantics

Every audited mutation goes through this contract:

```
   ┌──────────────┐    ┌─────────────────────────┐    ┌─────────────────┐
   │ Caller       │    │ Service / Pipeline      │    │ EventBus        │
   │ (cog / view) │───▶│ - validate              │───▶│ subscribers     │
   └──────────────┘    │ - DB write (txn)        │    │ (panels, audit, │
                       │ - audit row (same txn)  │    │  analytics)     │
                       │ - cache invalidation    │    └─────────────────┘
                       │ - emit event            │
                       └─────────────────────────┘
```

**Required steps for any new service mutation:**

1. Validate inputs (positive amounts, non-self-transfer, etc.).
2. Open a transaction if more than one row is touched.
3. Apply the write(s).
4. Append an audit row inside the same transaction.
5. After commit: invalidate caches if needed, emit the catalogued event.
6. Never raise from inside an event emission — handler timeouts /
   failures are isolated by the bus.

**Required for any new event:**

- Catalogued name (`core/events_catalogue.KNOWN_EVENTS`).
- Payload documented in `docs/ownership.md` event table.
- At least one consumer or a `# reserved for future use` comment.

---

## Audit-log semantics

Three audit tables exist, all append-only:

- `governance_audit_log` (migration 006) — every governance write.
- `economy_audit_log` (migration 014) — every balance mutation.
- `mod_logs` (migration 001) — every moderator action.

These tables are **never** updated or deleted.  Compaction belongs to
DB-side retention policy, not application code.

---

## Concurrency expectations

- DB writes are atomic at the row level via `ON CONFLICT DO UPDATE`.
- Multi-row mutations (transfers, deathmatch dual-update, session_state
  batch) use an explicit `async with conn.transaction()`.
- Each handler/listener is run inside `asyncio` — no thread locks
  needed; use `asyncio.Lock` per ownership scope when read-modify-write
  cannot be expressed in SQL (see `navigation_stack._locks`).
- Migration runner holds a Postgres advisory lock for the duration of
  the apply, preventing concurrent bot instances from racing.

---

## What to do when the boundary is unclear

1. Check this document and `docs/architecture.md`.
2. If a piece of state belongs to *two* subsystems, the answer is
   almost always: extract a third (service) that mediates writes.
3. If you need cog A to react to cog B's state change, add a catalogued
   event and a listener — do not import cog B from cog A.
4. If a feature requires bypassing INV-F or INV-E, the change is an
   architecture change.  Open an issue or update this doc first.
