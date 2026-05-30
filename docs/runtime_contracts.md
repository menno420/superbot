# SuperBot — Runtime contracts

> **Status:** binding. Describes the lifecycle every platform primitive
> guarantees, and what subsystems must do to participate.  Failure
> modes and recovery semantics live here so a new contributor can
> answer "what happens when X breaks?" without reading source.

---

## 1. Subsystem identity contract

A subsystem identity string lives in **five** places.  All five must
agree, all the time:

1. `utils/subsystem_registry.SUBSYSTEMS` key
2. `cogs.*` `@commands.command(name=…)` matching `entry_points`
3. `core.runtime.persistent_views._REGISTRY` (via `PersistentView.SUBSYSTEM`)
4. `core.runtime.interaction_router._handlers` prefix
5. `panel_anchors.subsystem` and `runtime_sessions.subsystem` rows

**Enforcement:** `utils.subsystem_registry.validate_identity_contract(bot)`
runs at startup after `_load_cogs`.  Findings are logged at WARNING;
the regression test
`tests/unit/registry/test_identity_contract.py` validates the four
surfaces.

**Failure mode:** drift produces silent UX bugs — help categories
without commands, panels with unresponsive buttons, orphaned anchor
rows pointing at removed cogs.  Operators can run `!platform identity`
to print the current findings without restart.

**Recovery:** rename the cog/view/string to match the registry, or
remove the orphan row.  Subsystem name strings are persisted in
`panel_anchors`/`runtime_sessions` — never rename in place; phase via
add → backfill → drop.

---

## 2. EventBus contract

`core/events.py` exposes a single global `bus` with two methods:

```python
bus.on(event_name: str, handler: Coroutine) -> None
await bus.emit(event_name: str, **payload) -> None
```

### Guarantees

- **Sequential dispatch.**  Handlers for one emit run one after the
  other; failures are isolated (`try/except` per handler).
- **Per-handler timeout.**  Each handler runs under
  `asyncio.wait_for(..., timeout=5.0)`; a hung handler is cancelled and
  logged but cannot stall the bus.
- **Cataloged names.**  Every `event_name` is checked against
  `core/events_catalogue.KNOWN_EVENTS`.  Unknown names log a one-shot
  WARNING and emit `unknown_event_total{event, op}`; no exception is
  raised so an uncatalogued emit cannot break runtime.
- **Single-process.**  The bus is in-process only.  Cross-shard event
  routing is a Phase Sc addition.

### Subsystem requirements

1. **Cataloged emit.**  Add the event name to
   `core/events_catalogue.KNOWN_EVENTS` before emitting it.
2. **Documented payload.**  Document the event in `docs/ownership.md`
   "Event ownership" table.
3. **Idempotent handlers.**  Handlers must tolerate being invoked
   twice for the same event (e.g. after a future Redis replay).
4. **No external side-effects without retry safety.**  HTTP calls,
   Discord API writes — these must be safe if the handler is timed
   out and re-fired by a future replay layer.

### Failure modes

| Failure | Detection | Recovery |
|---|---|---|
| Handler raises | logged at ERROR, isolated; other handlers continue | re-emission required to re-trigger |
| Handler times out | logged at ERROR, cancelled; other handlers continue | handler must complete < 5 s; refactor or `tasks.spawn` for long work |
| Uncatalogued name | one-shot WARNING + `unknown_event_total` increment | add to catalogue or fix the caller |

---

## 3. PersistentView contract

Subclasses of `core.runtime.persistent_views.PersistentView` are
re-attached to their Discord messages on bot restart.

### Required class invariants

- `SUBSYSTEM: ClassVar[str]` matches the subsystem identity string.
- `timeout=None` (set automatically by the base class).
- Every UI component declares a static `custom_id` of the form
  `"<SUBSYSTEM>:<action>[:<opaque-data>]"`.
- The class is decorated with `@register` so
  `persistent_views._REGISTRY[SUBSYSTEM]` resolves to it at startup.
- The class is **stateless across users** — instance attributes must
  not encode per-user state, since one instance is bound to many
  messages on restart.  Per-user/per-message context is recovered
  from `interaction.user` + `interaction.message` + DB state.

### Lifecycle

```
import-time:    @register adds the class to _REGISTRY
on_ready:       message_anchor_manager.restore_anchors(bot) iterates
                panel_anchors WHERE NOT is_stale and calls
                bot.add_view(SUBCLASS(), message_id=row.message_id)
interaction:    discord.py dispatches to the instance bound to the
                message; ownership-check runs (`interaction_check`)
restart:        the cycle restarts from on_ready
```

### Failure modes

| Failure | Detection | Recovery |
|---|---|---|
| Cog fails to load → view class not in `_REGISTRY` | `anchor_restore_total{result="view_missing"}` + WARNING log | `!cog reload <name>` then `!platform anchors` (operator); the next interaction on the unattached button will be silently dropped until restored |
| Anchor row points at a deleted Discord message | first interaction fetch fails NotFound; anchor marked stale | `session_gc` GC sweep prunes stale anchors every 5 min |
| `restore_anchors` invoked twice (e.g. reconnect) | guarded by `_RESTORED_ONCE` flag (R6) | use `reset_restoration_state()` to force a re-run if needed |

---

## 4. Session lifecycle

A runtime **session** is one row per `(user_id, channel_id, subsystem)`
in `runtime_sessions`, with associated `runtime_session_state` rows
holding K/V state.

### Guarantees

- **Unique invariant.**  DB UNIQUE `(user_id, channel_id, subsystem)`
  ensures at most one active session per triple.
- **TTL.**  Sessions older than `SESSION_TTL = 7200` s (2 h) are pruned
  by `session_gc` every 5 minutes.
- **Cascade delete.**  Removing a session drops every state row
  belonging to it.
- **Atomic batch update.**  Writing more than one key uses
  `state_store.set_many(...)` which wraps the per-key upserts in a
  single transaction (R3).

### Failure modes

| Failure | Detection | Recovery |
|---|---|---|
| Session GC deletes a session mid-interaction | session lookup returns None; state reads return None; handler degrades gracefully | UX absorbs as "session expired" — caller may recreate via `get_or_create` |
| Concurrent state writes to the same key | last-write-wins (no optimistic locking) | navigation_stack uses a per-session asyncio.Lock (R4) to avoid this for stack push/pop |
| Multi-key write fails partway | `set_many` runs inside an asyncpg transaction, so partial state cannot persist | retry the write |

---

## 5. Anchor lifecycle

A **panel anchor** is one row in `panel_anchors` recording the
Discord `message_id` of a `(user, channel, subsystem)` panel.

### Guarantees

- **Unique invariant.**  DB UNIQUE `(user_id, channel_id, subsystem)`.
- **Restoration.**  `on_ready` calls `restore_anchors(bot)` once per
  process — guarded by `_RESTORED_ONCE` so reconnect-triggered
  `on_ready` does not duplicate view bindings.
- **GC.**  Stale anchors (Discord message deleted) are marked
  `is_stale=TRUE` on first failure; `session_gc` deletes stale rows
  every 5 minutes.
- **Diagnostics.**  `anchor_restore_total{subsystem, result}` metric
  records every per-anchor outcome at restore time:
  `ok | view_missing | restore_failed`.

### Recovery hooks

- `message_anchor_manager.last_restore_stats()` — snapshot of the
  last restore outcome (counts).
- `!platform anchors` — operator-facing readout of the above plus a
  per-subsystem count of active anchors.

---

## 6. Interaction lifecycle

```
Discord  →  bot.on_interaction(interaction)
            │
            ▼
core.runtime.interaction_router.dispatch(interaction)
            │
            ├─ parse custom_id → "<prefix>:<action>"
            │
            ├─ if prefix has no handler →
            │     interaction_unhandled_total{prefix} += 1
            │     one-shot WARNING; return
            │
            ├─ governance gate:
            │     get_visible_subsystems(ctx)
            │     prefix not in visible → ephemeral "feature disabled" + return
            │     gate raises → fail open + governance_fail_open_total{prefix} += 1
            │
            ├─ session_manager.get_or_create(uid, gid, cid, prefix)
            │     failure → session=None, handler called anyway
            │
            └─ handler(interaction, action, session, request_id)
                 │
                 ▼
            cog code:
              await safe_defer(interaction)  ← within 3 s
              ... DB / governance / rendering ...
              await safe_edit / safe_followup
              tasks.spawn(...) for background work
              bus.emit(catalogued_event, ...)
```

### Guarantees

- **3-second token window.**  Use `safe_defer` to extend to 15 minutes
  if the handler needs any I/O.
- **Idempotent helpers.**  `safe_defer`, `safe_followup`, `safe_edit`
  all swallow `discord.NotFound` and `discord.HTTPException`, log a
  WARNING, and return success/failure rather than raise.  Callers do
  not need `try/except` for those specific failure modes.
- **Exception isolation.**  The router wraps every handler in
  `try/except Exception`; uncaught exceptions are logged at ERROR and
  an ephemeral error reply is sent to the user.
- **Permission errors.**  `core.runtime.ui_permissions.require_execution`
  raises `PermissionError`; the router catches and treats it as
  "already replied" (the helper sent an ephemeral message).

---

## 7. Managed task lifecycle

Every background coroutine spawned by application code goes through
`core.runtime.tasks.spawn(name, coro)`.

### Guarantees

- **Strong reference held.**  No PEP 8.5 GC trap; the task survives
  until done.
- **Exception logging.**  Unhandled exceptions are logged with full
  traceback at ERROR.
- **Outcome metric.**  `task_outcome_total{name, outcome}` increments
  on every completion (`ok` / `error` / `cancelled`).
- **Cooperative shutdown.**  `tasks.cancel_all()` cancels every
  still-running spawned task during graceful drain.

### Naming convention

`<subsystem>:<short-purpose>[:<id>]`.  Examples:
`counting:save:1234`, `panel_refresh:economy:99999`,
`rps:countdown:5678`.

### Forbidden patterns

- Bare `asyncio.create_task(coro)` outside `bot1.py` and
  `core/runtime/session_gc.py` (entry-point lifecycle tasks
  already tracked via `_APP_TASKS`).

---

## 8. Restoration guarantees

When the bot restarts:

1. `db.init()` opens the pool + runs migrations under
   `pg_advisory_lock`.
2. `core.runtime.setup()` subscribes EventBus handlers (idempotent).
3. `_load_cogs()` imports every extension in order;
   `PersistentView.@register` decorators populate
   `persistent_views._REGISTRY`.
4. `bot.start()` connects to Discord; `on_ready` fires.
5. `on_ready` calls `message_anchor_manager.restore_anchors(bot)`:
   - Query `panel_anchors WHERE NOT is_stale`.
   - For each row, look up `_REGISTRY[subsystem]`; instantiate the
     view class; `bot.add_view(view, message_id=row.message_id)`.
   - Emit `anchor_restore_total` per row.
   - Set `_LAST_RESTORE_STATS` for `!platform anchors`.
6. `on_ready` calls `live_update_scheduler.setup(bot)` (idempotent).
7. Health server task starts; session_gc task starts.

### What survives a restart

- Every `panel_anchors` row → re-bound views.
- Every `runtime_sessions` row → recreated lazily on next interaction.
- Every `runtime_session_state` row → readable until session expires.
- Every governance override → loaded on-demand.
- Every `economy_audit_log` / `governance_audit_log` row → never deleted.

### What does NOT survive a restart

- In-process governance cache (`_CACHE`, `_CACHE_VERSION`) — rebuilt
  on first access.
- In-process EventBus handler list — re-registered by `core.runtime.setup`.
- `live_update_scheduler._last_edit` rate-limit dict — drops to empty.
- Per-session `navigation_stack._locks` — replaced lazily on next push.
- In-progress tournaments not persisted to DB.
- In-process counting/blackjack/rps game state held in cog instance
  attributes — but cogs can now checkpoint via
  :mod:`services.game_state_service` (migration 015) and restore at
  cog_load. Adoption is per-cog; cogs not yet wired in retain the
  pre-existing "restart cancels" behaviour. For money flow, use
  :func:`services.economy_service.refund` to return staked coins
  with audit-trail attribution so the user is never out money.

---

## 9. Mutation contract checklist

For any new service-layer mutation:

- [ ] Validate inputs (raise `ValueError` for malformed amounts /
      same-source-and-target / etc.).
- [ ] Wrap multi-row writes in `async with conn.transaction()`.
- [ ] Append an audit row inside the transaction.
- [ ] Bump or invalidate any in-process cache that derives from the
      affected state.
- [ ] After commit, emit the catalogued event via `bus.emit(...)`.
- [ ] Document the event in `docs/ownership.md`.
- [ ] Add a regression test that asserts the audit row appears and
      the event fires.

### Settings & platform-flag read/write contract

SuperBot has three operator-config systems; new code must use the
canonical seam for each rather than reading or writing storage directly:

- **Scalar guild settings** (`guild_settings` KV). Write through
  `services.settings_mutation.SettingsMutationPipeline.set_value` (typed
  coercion + validation + audit + cache invalidation + event). Read
  through `services.settings_resolution.resolve_setting` (the full
  `SettingResolution` with provenance + validity) or the
  `resolve_value(guild_id, subsystem, name, fallback)` convenience.
  Never `int(await db.get_setting(...))` at a call-site — a malformed
  stored row must degrade to the `SettingSpec` default, not raise.
- **Feature / platform flags** (`feature_flag_*` tables). Read through
  `core.runtime.feature_flags.is_enabled` / `resolve_with_provenance`;
  write through `services.rollout_mutation.RolloutMutationPipeline`.
- **AI env flags** (`core.runtime.ai.feature_flags`) are env-only and
  boot-safe; `docs/ai-config-ownership.md` covers how a per-guild AI
  policy overlays them.

---

## 10. Observability contract

Every long-lived async loop or fire-and-forget mutation must:

1. Run inside `core.runtime.tasks.spawn(...)` so failures are visible
   in `task_outcome_total{outcome="error"}`.
2. Log a one-shot WARNING (not ERROR) for recoverable platform
   anomalies (token expired, message gone, view missing).
3. Emit a metric for any silent failure path that operators would
   otherwise discover via user reports.

Current metric inventory: `services/metrics.py`.  Adding a new metric
requires updating that file *and* the runbook (`docs/runbook.md` —
future work in Phase T).

---

## 11. Where to look when something breaks

| Symptom | First diagnostic | Likely cause |
|---|---|---|
| "Interaction Failed" UX error | `governance_fail_open_total`, `interaction_unhandled_total` | missing `safe_defer`, missing handler registration |
| Panel buttons unresponsive | `anchor_restore_total{result="view_missing"}` | cog failed to load, view subsystem renamed |
| Help category shows commands that don't run | `!platform identity` | identity-contract drift |
| Balance "lost" coins | `economy_audit_log` for the user_id | overdraft path; missing debit reason |
| Tournament didn't pay out | `economy_audit_log` filtered to `tournament:*` / `rps:*` / `blackjack:*` reasons | service exception was silenced; check ERROR logs |
| Tournament-entry refund on restart | `economy_audit_log` filtered to `*_tournament:restart_refund` or `*_tournament:guild_remove_refund` | normal cog_load / on_guild_remove recovery for an interrupted tournament |
| Bot eats CPU | `task_outcome_total` rate | runaway `tasks.spawn` loop |
| Migrations stuck | `pg_advisory_lock` may be held; check `pg_stat_activity` for the lock owner | concurrent deploy holding the lock |

---

## 12. Identity contract — STRICT mode (default-on as of S5.1)

`utils.subsystem_registry.validate_identity_contract` runs at every
startup and surfaces drift between the five identity surfaces (see §1).
Two enforcement modes coexist; **STRICT is the default as of Phase S5.1**
(previously opt-in via `IDENTITY_CONTRACT_STRICT=true`).

| Mode | Trigger | Behaviour on fatal-tier finding |
|---|---|---|
| **STRICT** (default) | both opt-out env vars unset | Logs the structured summary at WARNING, increments `identity_contract_findings_total{kind}`, posts a Discord webhook embed via `WebhookReporter.on_identity_findings`, AND raises `SystemExit(1)`.  Bot refuses to start on drift. |
| **Advisory** (opt-out) | `STRICT_DISABLED=1` (or `true`/`yes`/`on`) — canonical S5.1 escape hatch; OR `IDENTITY_CONTRACT_STRICT=false` — legacy pre-S5.1 opt-out, still honored | Everything STRICT does *except* the SystemExit.  Bot starts anyway; drift is visible in logs / metrics / `!platform identity`. |

### Tier classification

| Bucket | Tier | Auto-heal? |
|---|---|---|
| `entry_point_missing_command` | fatal | No (likely cog load failure — operator must reload) |
| `router_prefix_unknown` | auto_healable | Yes via `!platform identity --fix` (unregister) |
| `view_subsystem_unknown` | auto_healable | Yes via `!platform identity --fix` (unregister) |
| `db_anchor_subsystem_unknown` | auto_healable | Yes via `!platform identity --fix` (mark stale) |

Source of truth: `IDENTITY_FINDING_TIER` in
`utils/subsystem_registry.py`.  The invariant test
`tests/unit/registry/test_identity_contract.py::TestIdentityFindingTier::
test_tier_map_covers_every_finding_bucket` fails CI if a new bucket
is added without a classification.

### Pre-S5.1 promotion runbook (historical)

Before S5.1 the promotion was an explicit `IDENTITY_CONTRACT_STRICT=true`
opt-in.  S5.1 flipped the default — every new deploy is STRICT unless
opted out.  The old runbook is preserved here for reference and for
operators rolling forward from a stale env config:

1. **Verify clean state.** SSH or `!platform identity`; expected
   output: ``All four identity surfaces agree.`` (the all-green
   embed).
2. **Apply auto-heal if necessary.** Run `!platform identity --fix`
   to clear any orphan router prefixes, orphan view subsystems, or
   orphan `panel_anchors` rows surfaced by step 1.  Fatal-tier
   findings require a cog reload (`!reload <cog>`); auto-heal will
   not touch them.
3. **Re-verify clean state.** Re-run `!platform identity`; expected
   output: clean.
4. **(S5.1+: no longer needed)** Previously: export
   `IDENTITY_CONTRACT_STRICT=true`.  Now STRICT is the default — no
   env var needed.  Operators who still set this var will see no
   behaviour change (it's redundant under the new default).
5. **Roll the deploy.** Startup will refuse the launch if any
   fatal-tier finding reappears; the webhook embed names the
   offending surface so operators can roll back or fix forward.

### Failure modes under STRICT

- **Cog fails to load** → `entry_point_missing_command` → STRICT
  aborts startup.  Recovery: revert the deploy or fix the cog and
  redeploy.  Do NOT turn STRICT off as a workaround — the abort is
  the safety net catching a real regression.
- **DB anchor row references a removed subsystem** → STRICT does
  NOT abort (this is `auto_healable`-tier, not `fatal`).  Run
  `!platform identity --fix` from any admin channel.

### Emergency escape hatch (S5.1)

If a fatal-tier finding is blocking a deploy AND you cannot fix
forward in the window required by your SLA:

1. Set `STRICT_DISABLED=1` in the host environment.
2. Redeploy.  Startup completes in Advisory mode; the bot is back up.
3. **Drop the env var as soon as the underlying drift is fixed** —
   leaving Advisory mode latent re-opens the silent-drift window
   STRICT was promoted to close.

The legacy `IDENTITY_CONTRACT_STRICT=false` opt-out also still works
for operators rolling forward from a pre-S5.1 env config.  Both
opt-outs produce identical Advisory-mode behaviour.
