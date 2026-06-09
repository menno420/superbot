# SuperBot — Ownership boundaries

> **Status:** `binding` — Every module/table/event listed here has a
> single owner that decides what is or isn't legal to do with it.
> Touching state owned by another subsystem requires going through
> that subsystem's service layer (or proposing a contract change).
>
> **Companions:** `docs/architecture.md` (layering + invariants),
> `docs/runtime_contracts.md` (lifecycle guarantees),
> `docs/helper-policy.md` (placement / promotion rules for any new
> helper introduced while applying these ownership rules),
> `docs/AGENT_ORIENTATION.md` (which doc to read for which task).

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
| `services/moderation_service.py` | every moderation action (`warnings`, `mod_logs`, Discord ban/kick/timeout calls), including system `auto_delete` | call `warn`/`timeout`/`kick`/`ban`/`unban`/`clear_warnings`/`auto_delete`. Both manual surfaces (`cogs/moderation_cog.py`, `views/moderation/modals.py`) route here — pinned by `tests/unit/invariants/test_no_direct_moderation_writes.py`. Each action fans out **three signals** via `_record_action`: the `mod_logs` row (authoritative history), the best-effort `audit.action_recorded` companion, and the `moderation.action_taken` domain event (companion + event share one `mutation_id`). Clear-warnings stores the token **`clearwarnings`** (one word). |
| `services/channel_lifecycle_service.py` (`ChannelLifecycleService`) | channel **rename / move / delete / reorder** (single + batch) — the *change* ops `ResourceProvisioningPipeline` does not own | call `ChannelLifecycleService().apply(...)` with a `ChannelLifecycleRequest`. Checks the bot's Manage Channels permission; irreversible `delete` requires `confirmed=True`; per-channel Discord failures become failed `StepResult`s (no raise). `reorder` sends channel(s) to the top/bottom of their category (`channel.move`, compensatable). Emits the best-effort `audit.action_recorded` companion + `channel.lifecycle_changed` (shared `mutation_id`). `ChannelCog` is pinned against direct `.delete()`/`.edit()` by `tests/unit/invariants/test_no_direct_channel_mutations.py`. **Not yet owned:** create / clone / overwrites / lock / arbitrary before-after reorder / category CRUD UI (still on cog/util paths). |
| `services/role_lifecycle_service.py` (`RoleLifecycleService`) | operator-driven role **create / edit / delete** (the role *object* lifecycle) | call `RoleLifecycleService().apply(...)` with a `RoleLifecycleRequest`. Checks the bot's Manage Roles permission + the per-role manageability verdict (via `utils.role_feasibility`); irreversible `delete` requires `confirmed=True`. Emits the `audit.action_recorded` companion + `role.lifecycle_changed` (shared `mutation_id`). The audited `guild.create_role` caller for *manual* roles (subsystem role provisioning still goes through `ResourceProvisioningPipeline`). `role_cog` + `views/roles/*` pinned by `tests/unit/invariants/test_no_direct_role_mutations.py`. **Not owned:** member assignment (reaction roles / automation `add_roles`/`remove_roles` stay on current paths). |
| `services/lifecycle/contracts.py` | the shared lifecycle **contract types** (`StepResult`, `LifecyclePreview`, `LifecycleResult`, `.first_error`), the reversibility vocabulary (`reversible`/`compensatable`/`irreversible`), the outcome set (`success`/`partial`/`blocked`/`declined`/`discord_failed`), and `emit_lifecycle_audit` | reuse these for any new lifecycle/change service (channels + roles shipped). Mirrors the `ResourceProvisioningPipeline` shape for ops provisioning does not own. |
| `services/blackjack_engine.py` | pure card/hand/deck math (no I/O) | call `rank_value`/`hand_value`/`new_deck`/`hand_str`/`is_blackjack`. No copy-pasted card logic in cogs. |
| `services/game_state_service.py` | in-flight game state checkpoints (`game_state` table) | call `save`/`load`/`clear`/`list_active_for_subsystem`.  JSONB payload; cogs own their schemas. |
| `services/governance_service.py` (legacy shim) | the public surface re-exported from `governance/*` | re-exports only.  No business logic should live here. |
| `governance/writes.py:GovernanceMutationPipeline` | every governance write (subsystem_visibility, cleanup_policies, capability_overrides, audit log) | use the pipeline.  INV-E (`test_apply_template_uses_pipeline`). |
| `services/btd6_view_model_service.py` | BTD6 view-model construction, the data-freshness contract, and the `context_id` format (`^btd6_[a-z_]+:[A-Za-z0-9_-]+$`) | call `build_*_view_model(...)` instead of reading `btd6_facts` rows directly from cogs/views. The `context_id` regex is the handle a future Team Panel attaches to — never widen it without a migration. Pinned by `tests/unit/cogs/test_btd6_context_id_contract.py`. |
| `services/health_snapshot_service.py` (+ `services/health_contracts.py`) | the operational **health read model** — `HealthSnapshot` / `SubsystemHealth` / `OperationalHealthFinding` contracts, deterministic severity aggregation, and the per-audience redaction projection (`project_for_audience`) | **read-only** — composes existing observability seams (`diagnostics_service` — incl. the opt-in `recent_errors` log-buffer provider grouped via `health_observations`, `platform_consistency`, `startup_outcome`, `lifecycle`, `tasks`, `resource_health`, AI read-models) plus the `utils.db.health.ping` probe; owns **no table** and never mutates. Heavy sources are imported function-locally (import-safe). Pinned read-only by `tests/unit/services/test_health_readonly_invariants.py`; import-safety by `test_health_import_safety.py`; redaction omission by `test_health_redaction.py`. |
| `services/health_findings_service.py` (+ `utils/db/health_findings.py`) | the **persistent operational-health findings** store (`operational_health_findings` + `operational_health_finding_aggregates`, migration 057) | **sole writer** — call `record_findings` / `run_retention`; never write those tables elsewhere. Recurrence dedupes by `fingerprint` (counts accumulate across boots); resolved/ignored detail is rolled into the aggregates table and pruned after 30d. System-driven (no user actor) → no `emit_audit_action`; recording is driven from `bot1` after the settled-startup snapshot, not from the read model. Pinned by `tests/unit/invariants/test_inv_health_findings_service.py`. |

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
| `role`         | `role_thresholds`, `reaction_roles`            | role create/edit/delete via `services/role_lifecycle_service.py`; `role_thresholds` **writes** via the audited `services/role_automation.set_{time,xp}_threshold` seam (P0C, #592 — drift-fenced; see the "Role-threshold writes — NORMALIZED" note in the Known-drift list below); reads + `reaction_roles` direct via `utils/db/roles.py`. Time/XP tiers are **id-keyed dual-read** (migration 056: nullable `role_id`/`display_name`; resolved id-first, normalized-name fallback) and tier removal uses the field-specific `clear_role_time_threshold` / `clear_role_xp_threshold` — never the destructive full-row delete |
| `moderation`   | `warnings`, `mod_logs`                         | `services/moderation_service.py` (preferred); `utils/db/moderation.py` direct for read-only / legacy callers |
| `xp`           | `xp.xp`, `xp.level`, `xp.messages`, `xp.last_xp` | `services/xp_service.py` |
| `economy`      | `economy`, `job_progress`, `economy_audit_log`   | `services/economy_service.py` |
| `inventory`    | `inventory`                                    | direct via `utils/db/inventory.py` |
| `cleanup`      | `prohibited_words`                             | direct via `utils/db/moderation.py` |
| `chain`        | `chain_channels`                               | direct via `utils/db/games/chain.py` |
| `counting`     | `counting_state`                               | direct via `utils/db/games/counting.py` |
| `mining`       | `mining_inventory`, `mining_equipment`         | direct via `utils/db/games/mining*.py` |
| `deathmatch`   | `deathmatch_stats`                             | direct via `utils/db/games/deathmatch.py` |
| `rps_tournament` | `rps_players`, `rps_matches`                 | direct via `utils/db/games/rps.py`; balance mutations via economy_service |
| `blackjack`    | (uses `xp.coins`; tournament state in `guild_settings`) | balance via economy_service |
| `channel`      | (uses Discord API; visibility via governance)  | rename/move/delete/reorder via `services/channel_lifecycle_service.py`; visibility via governance pipeline; declared creation via `ResourceProvisioningPipeline` |
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

### Feature stale-state cleanup (RC-7)

Garbage-collecting stale *persisted feature state* is split so `core/runtime`
never owns a feature's domain rules:

| Concern | Owner | Notes |
|---|---|---|
| GC scheduling (the 5-min sweep loop) | `core.runtime.session_gc` | Calls `cleanup_registry.run_all()`; knows nothing about economy or games. |
| The provider registry | `core.runtime.cleanup_registry` | Pure `core` (stdlib only). `register(name, provider)` / `run_all()`; isolates a failing provider so one bad sweep cannot block the rest. |
| Stale `game_state` reclamation + refund | `services.game_state_cleanup` | Owns the ADR-002 refund-on-abandon contract (`economy_service.refund`, opt-in on a positive int `bet`). Registered via `install()` from `bot1` at startup. |

A new feature that persists stakes registers **its own** provider here (a
`services/*_cleanup.py` that `install()`s into `cleanup_registry`) instead of
adding economy/game logic to `session_gc`.

---

## Settings & platform-flag ownership

Operator configuration spans three systems. Each has one canonical write
seam and one canonical read seam; cogs and views never touch the
underlying storage directly.

| Config kind | Storage | Write seam | Read seam |
|---|---|---|---|
| Scalar guild settings | `guild_settings` KV + `settings_mutation_audit` | `services.settings_mutation.SettingsMutationPipeline` | `services.settings_resolution.resolve_setting` / `resolve_value` |
| Feature / platform flags | `feature_flag_global_overrides`, `feature_flag_guild_overrides`, `environment_tiers`, `feature_flag_audit` | `services.rollout_mutation.RolloutMutationPipeline` | `core.runtime.feature_flags.is_enabled` / `resolve_with_provenance` |
| AI env flags | environment only (no DB) | n/a (env-driven) | `core.runtime.ai.feature_flags` |

Scalar settings are declared as `SettingSpec`s in
`cogs/<subsystem>/schemas.py` and catalogued read-only by
`core.runtime.settings_registry`. Flags are declared in
`core.runtime.feature_flags`. `docs/setup-platform/settings-customization-roadmap.md`
is the authority on the three lanes (settings / binding / provisioning).

### Mutation authority + kill-switches (ADR-005)

Authorizing a settings / binding / provisioning mutation is owned by the governance
capability resolver — **not** by the pipelines themselves:

| Concern | Owner | Notes |
|---|---|---|
| Capability resolution | `governance.capability.actor_holds_capability` | Administrator floor keyed on the declared `capability_required`; bound to the **target** guild; revoke-only per-guild overlay over `capability_execution_overrides`. v1 keeps one floor. |
| Mutation kill-switches | `core.runtime.feature_flags.is_operator_disabled` | `settings.mutation.primary` / `resource_provisioning.primary`. Default-ALLOW; blocks only on an explicit operator OFF; **fails open**. |
| Panel-callback re-check | `views.base.interaction_is_admin` | Mutating panels reachable without an admin-gated entry (e.g. via Help) must re-check authority. |

Full contract: [`docs/capability-authority.md`](capability-authority.md).

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
| `moderation.action_taken` | `services/moderation_service.py` | `mutation_id`, `guild_id`, `target_id`, `actor_id`, `action` (`warn`/`timeout`/`kick`/`ban`/`unban`/`clearwarnings`, or `auto_delete:<rule>` for system auto-mod), `reason`, plus per-action extras (e.g. `until` for timeouts) |
| `channel.lifecycle_changed` | `services/channel_lifecycle_service.py` | `mutation_id`, `guild_id`, `operation` (`rename`/`move`/`delete`/`reorder`), `outcome`, `applied[]`, `failed[]`, `occurred_at`. Advisory; subscriber failure logged + swallowed (Discord state is authoritative). |
| `role.lifecycle_changed` | `services/role_lifecycle_service.py` | `mutation_id`, `guild_id`, `operation` (`create`/`edit`/`delete`), `outcome`, `applied[]`, `failed[]`, `occurred_at`. Advisory; subscriber failure logged + swallowed (Discord state is authoritative). |
| `audit.action_recorded` | every mutation pipeline/service via `services.audit_events.emit_audit_action` (settings, bindings, participation, resource provisioning, moderation, channel lifecycle, …) | the 11 required fields documented in `docs/server-logging.md` § "Payload contract" (`mutation_id`, `subsystem`, `mutation_type`, `target`, `scope`, `guild_id`, `prev_value`, `new_value`, `actor_id`, `actor_type`, `occurred_at`). **Best-effort** generic audit-routing companion consumed by `services.server_logging`; **not** a domain history store. |

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

> See also **`docs/audits/direct-db-exception-ledger.md`** (RC-8A) — the per-cog catalog
> of direct `utils.db` reads/writes, classified `accepted-read` /
> `accepted-direct-write` / `service-migration-required`.

These calls are **forbidden** outside their owning module:

| Symbol | Owner | Forbidden in |
|---|---|---|
| `db.add_coins` / `utils.db.economy.add_coins` | `services/economy_service.py` | every cog, every other service. |
| `db.set_coins` / `utils.db.economy.set_coins` | `services/economy_service.py` | every cog, every other service. |
| Raw SQL `UPDATE xp ... coins` / `INSERT INTO xp (..., coins ...)` | `services/economy_service.py` + `utils/db/economy.py` | every other production file. |
| `db.set_subsystem_visibility` / raw writes to `subsystem_visibility` | `GovernanceMutationPipeline` | every cog, every other service. |
| `db.set_cleanup_policy` / raw writes to `cleanup_policies` | `GovernanceMutationPipeline` | every cog, every other service. |
| `db.write_governance_audit` | `GovernanceMutationPipeline` + `governance/execution._audit_internal_bypass` | every other module.  See "Audit-write carve-out" below. |
| AI policy writes (`utils.db.ai.upsert_*_policy` / `bump_generation` / `upsert_instruction_profile`) | `services/ai_policy_mutation.py` + `services/ai_instruction_mutation.py` | every cog, every view, every other service.  AI configuration: see `docs/ai-config-ownership.md` (binding). |
| `utils.db.ai.record_decision` | `services/ai_decision_audit_service.py` | every other module.  The audit row is written exactly once per natural-language stage invocation. |

The first two row-pairs are enforced by INV-F (AST test) for economy
and INV-E (`test_apply_template_uses_pipeline`) for visibility /
cleanup pipeline writes.  Add to those tests when introducing future
forbid-lists.  The AI snapshot / readiness services are pinned to
*non-mutating* by `tests/unit/services/test_ai_readonly_invariants.py`.

### Audit-write carve-out

`db.write_governance_audit` has **one** allowed caller outside the
pipeline: `governance.execution._audit_internal_bypass`
(`disbot/governance/execution.py:111`), invoked from
`resolve_execution()` only when `check_visibility=False`
(`disbot/governance/execution.py:249` — the internal / AI-triggered
bypass path).

Why it exists:

- Internal bypasses skip the visibility gate, so the only in-memory
  record is the `EVT_EXECUTION_ALLOWED` event with `bypass: True`.
  A durable row in `governance_audit_log` keeps the bypass
  reconstructable from the DB alone (DEBT-002 — required before
  AI / plugin expansion).
- The write is **append-only** and matches the same audit-row shape
  the pipeline emits.  No governed state (`subsystem_visibility`,
  `cleanup_policies`, `capability_execution_overrides`) is mutated.
- The call is **best-effort**: failures are logged at WARNING and
  swallowed, so a broken audit write cannot block the legitimate
  execution that the bypass already authorised.

Why it isn't routed through the pipeline:

- The pipeline owns visibility / cleanup / override mutations, all of
  which take templates and emit `governance.*.changed` events.  An
  internal-bypass audit row is a **fact**, not a mutation — there is
  no template to validate, no cache to invalidate, no consumer event
  to emit beyond the `EVT_EXECUTION_ALLOWED` already fired by
  `resolve_execution`.  Forcing it through the pipeline would mean
  inventing a synthetic mutation just to write the row.

If a second non-pipeline caller appears, **promote the
`_audit_internal_bypass` helper** (move it next to the pipeline, give
it a public name, document the new caller here) rather than scattering
direct `db.write_governance_audit` calls across the codebase.  INV-E
does not currently AST-scan `write_governance_audit`; if you tighten
it later, exempt this one file by path.

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

## Direct vs. draft mutation lanes (binding)

There are **two** sanctioned write lanes plus a read lane. A mutation lands in
exactly one; the choice is determined by the *shape* of the change, not by which
panel the operator happens to be in. This is the canonical rule behind the
per-surface map in
[`docs/planning/adaptive-setup-access-routine-platform-2026-06-08.md` §5](planning/adaptive-setup-access-routine-platform-2026-06-08.md)
— that table is the inventory; this is the rule.

| Lane | When to use it | How it writes | Examples |
|---|---|---|---|
| **Direct (focused/runtime)** | A single-domain, reversible, operator-initiated action whose effect the operator can see and undo immediately. | Through the domain's **canonical audited service / mutation pipeline** (the "Mutation semantics" contract above) — synchronously, no staging. | A moderation action (`ModerationService`); one typed setting edit (`SettingsMutationPipeline`); a command-access policy write (`command_access_service`); a role exemption (`role_exemption_service`); a cleanup-policy change; a confirmed channel/role lifecycle op (`ChannelLifecycleService` / `RoleLifecycleService`). |
| **Draft → Final Review (compound/config)** | A compound, multi-setting, cross-subsystem, generated, or higher-risk configuration change — anything where the operator should preview the whole set and an authority recheck must happen at apply time. | Staged as `SetupOperation` rows via `setup_draft`, applied **only** through `views/setup/final_review.py` (authority recheck → ordered apply → partial recovery → audit). | Setup wizard sections; cog-routing profiles; (future) Guild Feature Profile apply; (future) Access Map edits; (future) medium/high-risk routine config actions. |
| **Read-only (projection)** | Answering "what is true / who can see what / what is unhealthy" without changing anything. | No writes. Composes existing owners' read models. | `setup_diagnostics`; server-management health badges; the (future) Access Map projection; Help Preview. |

**Hard rules:**

1. **Compound config never takes the direct lane.** If a change spans more than one
   setting/resource, crosses subsystems, is machine-generated (profile / routine /
   AI), or is classified medium/high risk, it **must** stage `SetupOperation` rows
   and apply through Final Review. New op kinds require the dispatcher + DB gate +
   SQL `CHECK` parity (see `services/setup_operations.py`).
2. **Direct edits stay focused and reversible.** A direct-lane writer touches one
   domain through its canonical service and emits its audit row in the same
   transaction. It never writes another domain's tables (use that domain's service)
   and never stages a draft on the operator's behalf for a change they did not
   preview.
3. **Projections never mutate.** A read model / drift provider / badge computes from
   existing owners; if it finds something to fix, it returns a *repair proposal*
   that the operator stages as a draft (the `setup_diagnostics` pattern) — it does
   not write.
4. **Prohibited paths (enforced by review + negative tests):** a compiler, routine,
   or AI adapter must **never** call a view callback or a Discord resource API
   directly, and must **never** call a canonical mutation service except via the
   draft/Final-Review or (low-risk only) approved-action seam. They emit
   `SetupOperation` drafts or dispatch through the canonical executor — never a
   side-channel write. Cogs/views never write DB directly (the
   "Direct DB writes — explicit blocklist" above).

**Known drift to normalize before automation:**

- ✅ **Role-threshold writes — NORMALIZED (P0C, 2026-06-08).** All six time/XP
  threshold write sites (the role panels' Seed-Defaults, time/XP modals, the
  created-role XP companion, the `_ensure_defaults` boot seed, and the `!setrole`
  command) now route through the audited
  `services.role_automation.set_time_threshold` / `set_xp_threshold` seam (DB write
  **plus** `audit.action_recorded`, and the XP path also invalidates the XP-threshold
  cache). The single canonical seam a future profile/routine draft compiles into now
  exists. The convergence is locked by
  `tests/unit/invariants/test_no_direct_role_threshold_writes.py` — its allowlist is
  now **empty**, so *any* direct `utils.db.roles.set_role_threshold*` call from the
  role command/view surface fails CI.
- ⏳ **Channel create/edit lifecycle — still mixed.** Several channel create/edit
  paths mix direct Discord calls with `ChannelLifecycleService`; this must converge on
  a canonical audited writer **before** any profile/routine is allowed to drive channel
  lifecycle (otherwise the draft lane has no single seam to compile into). Until then,
  profiles/routines must not target that axis. This is the larger secondary gap noted
  in the planning doc §16.5; assess before automating, do not rewrite wholesale.

---

## Audit-log semantics

Three audit tables exist, all append-only:

- `governance_audit_log` (migration 006) — every governance write.
- `economy_audit_log` (migration 014) — every balance mutation.
- `mod_logs` (migration 001) — every moderator action, **and** every system
  `auto_delete` (keyed `auto_delete:<rule>`), all written by
  `moderation_service._record_action`.

These tables are **never** updated or deleted.  Compaction belongs to
DB-side retention policy, not application code.

`mod_logs` is the **authoritative** moderation history.  The
`audit.action_recorded` event that `_record_action` (and the lifecycle services)
also emit is a *best-effort routing companion* for `services.server_logging`, not
a second history store — a dropped companion never invalidates the `mod_logs` row.
Lifecycle services (channels, roles) currently persist **no** dedicated audit
table; their only audit signals are the two bus events — the
`audit.action_recorded` companion and the domain event
(`channel.lifecycle_changed` / `role.lifecycle_changed`), both best-effort, both
carrying the shared `mutation_id`. A dedicated `*_lifecycle_audit` table is a future option
per the implementation plan, not shipped.

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
