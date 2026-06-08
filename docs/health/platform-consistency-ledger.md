# SuperBot — Platform Consistency Ledger

> **Status:** `living-ledger` — reference contract shape + **stale status
> snapshot**. The ownership/domain shapes remain useful, but many implementation
> cells below still describe pre-ship Phase-2 state and are **not a current work
> queue**. Verify every cell against source and the relevant subsystem folio/tracker;
> see `docs/audits/implementation-readiness-review-2026-06-06.md`. Binding mutation,
> lifecycle, and layering authority lives in `docs/ownership.md`,
> `docs/runtime_contracts.md`, and `docs/architecture.md`.
>
> **Purpose:** Prevent duplicate systems by codifying ownership for every
> runtime domain and every subsystem. Every contributor (human or
> agent) should consult this document before adding a new table, cache,
> mutation path, event, or UI surface.
>
> **Companion docs:** `docs/ownership.md` (mutation authority + dep
> direction), `docs/architecture.md` (layering + invariants),
> `docs/runtime_contracts.md` (lifecycle guarantees),
> `docs/setup-platform/roadmap_setup_platform.md` (phase plan).

---

## How to use this document

> **Freshness warning:** use the shapes/checklists below to avoid duplicate systems,
> but do not infer that a `❌`, `🚧`, or named PR is current until source verification.

- **Adding a new domain?** First add a row to §1 with empty cells, then
  fill them as PRs land. The empty row is the contract.
- **Adding a new subsystem?** Add a row to §2 with `❌` in every cell
  that doesn't apply yet. Coming back to fill cells is how we measure
  consistency progress.
- **Wiring lifecycle cleanup?** §3 lists every guild-keyed table that
  must have a `delete_for_guild` hook called from
  `guild_lifecycle.teardown`.
- **Catalog a new event?** Add it to §4 with all required fields.
- **About to flip a feature flag or migrate a read path?** Re-read §5
  before writing code.

Cells use these markers consistently:
- ✅ shipped + live on `main`
- 🟡 partial / declarations only / shipped but not yet consumed
- 🚧 in-flight in a named PR
- ❌ not yet built
- N/A genuinely does not apply

---

## 1. Domain contract ledger

The runtime substrate is partitioned into the domains below. Each
domain has one owner package, one mutation authority, one cache, one
event surface, one diagnostics provider, one teardown hook, and one
future setup-wizard consumer. Mixing two domains in one PR violates
the doctrine.

### Resources — physical Discord objects as typed runtime values

| Aspect | Status / location |
|---|---|
| Owner package | ✅ `core/resources/` |
| DB tables | ✅ `resource_validation_cache` (migration 020/021) |
| Mutation authority | 🟡 `core/resources/mutation.py` shell (provisioning is post-Phase 2) |
| Read authority | ✅ `core/resources/discovery.py` (`list_resources`, `resolve_resource`, `validate_resource`) |
| Cache authority | ✅ `resource_validation_cache` + `utils/db/resource_cache.py` (`delete_for_guild` available) |
| Event authority | ❌ no `EVT_RESOURCE_*` events yet — diagnostics-driven for now |
| Diagnostics surface | ✅ `!platform resources` (+ `core/resources/__init__.py` registers a provider) |
| Teardown hook | 🚧 wired in PR-1: `resource_cache.delete_for_guild` |
| Status semantics | ✅ `ResourceStatus.BOUND` is **structural-only** — not permission-ready (`core/resources/status.py:83`) |
| Wizard consumer | reads only; wizard never mutates resources directly. Provisioning runtime is post-Phase 2. |

### Bindings — subsystem → resource intent

| Aspect | Status / location |
|---|---|
| Owner package | ✅ `core/runtime/bindings.py` + `services/binding_mutation.py` |
| DB tables | ✅ `subsystem_bindings`, `binding_audit_log` (migration 022) |
| Mutation authority | ✅ `BindingMutationPipeline` (7-step contract; `services/binding_mutation.py`) |
| Read authority | ✅ `core.runtime.bindings.get_binding` returning `BindingValue` |
| Cache authority | ✅ `guild_config` namespace `subsystem.binding_name` |
| Event authority | ✅ `EVT_BINDING_CHANGED = "bindings.changed"` (zero consumers today) |
| Diagnostics surface | ✅ `!platform bindings` (per-subsystem histogram + status counts) |
| Teardown hook | 🚧 wired in PR-1: `delete_active_bindings_for_guild` (audit preserved) |
| Wizard consumer | commits via `BindingMutationPipeline`; never writes raw target_ids |

### Feature flags — environment tier + rollout + per-guild override

| Aspect | Status / location |
|---|---|
| Owner package | 🟡 `core/runtime/feature_flags.py` (declarations only — `FeatureFlag`, `EnvironmentTier`, `RolloutPolicy`) |
| DB tables | ❌ `feature_flag_state` (PR-2), `environment_tiers` (PR-2), `feature_flag_audit` (PR-3) |
| Mutation authority | ❌ `RolloutMutationPipeline` (PR-3) |
| Read authority | ❌ `is_enabled(flag_name, guild_id=None)` evaluator (PR-2) |
| Cache authority | ❌ per-flag in-process cache with TTL + explicit clear (PR-2); event-driven invalidation arrives in PR-3 |
| Event authority | ❌ `EVT_FEATURE_FLAGS_CHANGED`, `EVT_ROLLOUT_ADVANCED`, `EVT_ENVIRONMENT_TIER_CHANGED` (PR-3) |
| Diagnostics surface | 🟡 `!platform flags` shows declarations only; extended to show `effective_value + source` in PR-2 |
| Teardown hook | ❌ wired in PR-2: `feature_flag_state.delete_for_guild`, `environment_tiers.delete_for_guild` (audit preserved) |
| Wizard consumer | reads via `is_enabled`; never mutates from UI directly |
| Bootstrap policy | env override > `feature_flag.primary` gate > DB > declaration (DB unreachable → declared defaults + bootstrap metric, never raise) |

### Read-source arbitration — legacy settings vs bindings

| Aspect | Status / location |
|---|---|
| Owner package | ❌ `core/runtime/config_arbitration.py` (PR-4) |
| DB tables | N/A (compatibility layer over existing tables) |
| Mutation authority | N/A (read-only) |
| Read authority | ❌ `read_config(guild_id, subsystem, binding_name, legacy_key) -> ConfigReadResult` (PR-4) |
| Cache authority | inherits from `core.runtime.bindings` + `guild_config`; arbitration adds no cache of its own |
| Event authority | N/A |
| Diagnostics surface | ❌ consistency provider in PR-4; aggregated as `!platform consistency` in PR-10 |
| Teardown hook | N/A |
| Wizard consumer | wizard previews use `ConfigReadResult.source` and `binding_status` to show provenance |
| Hard rule | **no cog branches on `is_enabled("bindings.primary", …)` directly** — only the arbitration layer is allowed to |

### Participation — per-user opt-in, subscriptions, preferences, visibility

| Aspect | Status / location |
|---|---|
| Owner package | 🟡 `core/runtime/participation_schema.py` (declarations only); runtime in PR-8/9 |
| DB tables | ❌ `user_participation`, `user_subscriptions`, `user_preferences`, `user_visibility_overrides` (+ audit tables). **All four MUST include `guild_id`** for scoped retention. (PR-8) |
| Mutation authority | ❌ `ParticipationMutationPipeline` with four entrypoints, one per concern (PR-9) |
| Read authority | ❌ `utils/user_config_accessors.py` typed accessors (PR-8) |
| Cache authority | ❌ `core/runtime/user_config.py` per-(user, guild) cache with bounded TTL + max-size eviction (PR-8) |
| Event authority | ❌ `EVT_PARTICIPATION_CHANGED`, `EVT_SUBSCRIPTION_CHANGED`, `EVT_USER_PREFERENCE_CHANGED`, `EVT_USER_VISIBILITY_CHANGED` (PR-9) |
| Diagnostics surface | 🟡 `!platform participation-schemas` (declarations); runtime provider in PR-8 |
| Teardown hook | ❌ guild-leave deletes guild-scoped rows; user-leave (future) deletes user-scoped rows; audit preserved |
| Wizard consumer | participation hub UI is post-Phase 2; wizard must not mutate participation directly |
| Hard rule | **four separate tables, four separate entrypoints — never collapsed into one user settings blob** |

### Governance — visibility, cleanup, capabilities, role-tier mapping

| Aspect | Status / location |
|---|---|
| Owner package | ✅ `governance/` |
| DB tables | ✅ `subsystem_visibility`, `cleanup_policies`, `capability_execution_overrides`, `governance_audit_log` |
| Mutation authority | ✅ `GovernanceMutationPipeline` (`governance/writes.py`) |
| Read authority | ✅ `governance/resolver.py`, `governance/execution.py` |
| Cache authority | ✅ `governance/cache.py` (version-stamped) |
| Event authority | ✅ `governance.visibility.changed`, `governance.cleanup.changed`, `governance.cache.invalidated`, `governance.execution.allowed`, `governance.execution.denied` |
| Diagnostics surface | ✅ `!platform status`, `!platform identity`, `!platform caches` |
| Teardown hook | ✅ `forget_guild_capabilities` + `cache.forget_guild` |
| Wizard consumer | commits via `GovernanceMutationPipeline` |

### Diagnostics — operator control plane

| Aspect | Status / location |
|---|---|
| Owner package | ✅ `services/diagnostics_service.py` + `cogs/diagnostic_cog.py` |
| DB tables | N/A (read-only providers) |
| Mutation authority | N/A |
| Read authority | ✅ provider registry — domains register `_snapshot` providers |
| Cache authority | N/A (on-demand snapshots) |
| Event authority | N/A (observation only) |
| Diagnostics surface | ✅ 16 `!platform` subcommands (status, anchors, identity, runtime, caches, locks, tasks, views, slow, sessions, schemas, participation-schemas, resource-requirements, bindings, resources, flags) |
| Teardown hook | N/A |
| Wizard consumer | wizard reads diagnostics for readiness checks |
| Standard shape | 🚧 PR-10 unifies all providers to `{status, summary, counts, findings, recommended_action}` and adds `!platform consistency`, `!platform migrations`, `!platform health` |

### Logical migrations — checkpoints for data migrations (separate from schema migrations)

| Aspect | Status / location |
|---|---|
| Owner package | ❌ added in PR-5 alongside binding backfill |
| DB tables | ❌ `platform_migration_checkpoints(name, guild_id NULL, status, version, started_at, completed_at, summary_json)` (PR-5) |
| Mutation authority | ❌ the migration script that owns the operation |
| Read authority | ❌ `!platform migrations` |
| Cache authority | N/A |
| Event authority | N/A |
| Diagnostics surface | ❌ `!platform migrations` (PR-5; standardized in PR-10) |
| Teardown hook | preserve (forensic value); per-guild rows can be purged on guild leave if owner prefers |
| Wizard consumer | wizard reads checkpoint state for setup readiness |

### UI framework — panels, navigation, components

| Aspect | Status / location |
|---|---|
| Owner package | 🟡 `core/runtime/persistent_views.py`, `core/runtime/panel_manager.py`, `core/runtime/interaction_router.py`, `core/runtime/navigation_stack.py`, ad-hoc `views/<sub>/` |
| DB tables | ✅ `panel_anchors`, `runtime_sessions`, `runtime_session_state` |
| Mutation authority | ✅ `message_anchor_manager` for anchors; `session_manager` for sessions; `state_store` for session state |
| Read authority | ✅ same as above |
| Cache authority | ✅ in-process registries (`_REGISTRY`, `_handlers`, scope locks) |
| Event authority | N/A |
| Diagnostics surface | ✅ `!platform anchors`, `!platform sessions`, `!platform views`, `!platform locks` |
| Teardown hook | ✅ `delete_guild_panel_anchors`, `delete_sessions_for_guild`, `delete_guild_session_state` |
| Wizard consumer | wizard implementation post-Phase 2 — must use shared components (PR-11) |
| Standard shape | 🚧 PR-11 normalizes help/back/edit-vs-send + safe-defer; component registry **plan** only |

---

## 2. Subsystem consistency ledger

Each subsystem must eventually meet the columns below. `❌` means the
subsystem has not yet adopted the substrate piece; this is the
consistency punch list for post-Phase 2 work.

Columns:
- **Reg**: in `utils/subsystem_registry.SUBSYSTEMS`
- **Cmds**: commands declared and matched to entry_points
- **Sch**: `SubsystemSchema` (Phase 1a) registered
- **PSch**: `ParticipationSchema` (Phase 1b) registered
- **Res**: `ResourceRequirement` (Phase 1c) declared
- **Bind**: `BindingSpec` slots declared
- **Legacy**: still reads `guild_settings` keys
- **Mut**: writes via the owning service / pipeline only
- **Evts**: emits catalogued events
- **Diag**: contributes a `_snapshot` provider
- **UI**: ships PersistentView panel
- **Life**: teardown / forget_guild hook wired
- **Tests**: dedicated test directory under `tests/unit/<sub>/`

| Subsystem | Reg | Cmds | Sch | PSch | Res | Bind | Legacy | Mut | Evts | Diag | UI | Life | Tests |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| admin | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | N/A | N/A | ❌ | ✅ (via diag cog) | ❌ | N/A | 🟡 |
| help | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | N/A | N/A | ❌ | ❌ | ✅ Pattern A | N/A | 🟡 |
| diagnostic | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | N/A | N/A | ❌ | ✅ (owner) | ❌ | N/A | 🟡 |
| general | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | N/A | ❌ | ❌ | ❌ | N/A | 🟡 |
| role | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | direct `utils/db/roles.py` | ❌ | ❌ | ✅ Pattern A | N/A | 🟡 |
| moderation | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | `WARN_*` | `services/moderation_service.py` | ✅ `moderation.action_taken` | ❌ | ✅ Pattern A | N/A | ✅ |
| xp | ✅ | ✅ | 🟡 declared | 🟡 declared | ❌ | 🚧 PR-5/6 `announce_channel` | `XP_ANNOUNCE_CHANNEL`, threshold roles | `services/xp_service.py` | ✅ `xp.awarded`, `xp.level_up`, `xp.reset` | ❌ | ❌ | N/A | ✅ |
| economy | ✅ | ✅ | ❌ | ❌ | ❌ | 🚧 PR-5/6 `log_channel` | `ECONOMY_LOG_CHANNEL` | `services/economy_service.py` | ✅ `economy.balance_changed` | ❌ | ✅ Pattern B | N/A | ✅ |
| inventory | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | direct `utils/db/inventory.py` | ❌ | ❌ | ❌ | N/A | 🟡 |
| cleanup | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | direct `utils/db/moderation.py` | ❌ | ❌ | ❌ | N/A | 🟡 |
| chain | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | direct `utils/db/games/chain.py` | ❌ | ❌ | ❌ | N/A | 🟡 |
| counting | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | direct `utils/db/games/counting.py` | ❌ | ❌ | ❌ | N/A | 🟡 |
| mining | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | direct `utils/db/games/mining.py` | ❌ | ❌ | ✅ Pattern A | N/A | 🟡 |
| deathmatch | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | direct `utils/db/games/deathmatch.py` | ❌ | ❌ | ❌ | N/A | 🟡 |
| rps_tournament | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | `economy_service` for balance | ❌ | ❌ | ❌ | N/A | 🟡 |
| blackjack | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | tournament state in `guild_settings` | `economy_service` for balance | ❌ | ❌ | ❌ | N/A | 🟡 |
| channel | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | governance pipeline | ❌ | ❌ | ❌ | N/A | 🟡 |
| proof_channel | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | `economy_service` | ❌ | ❌ | ❌ | N/A | 🟡 |
| utility | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | N/A | ❌ | ❌ | ❌ | N/A | 🟡 |
| leaderboard | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | N/A read-only | ❌ | ❌ | ❌ | N/A | 🟡 |
| governance | ✅ | ✅ | N/A platform | N/A | N/A | 🚧 PR-5/6 `trusted_role` | `TRUSTED_TIER_ROLE_ID` | `GovernanceMutationPipeline` | ✅ five gov events | ✅ | N/A | ✅ |

Notes:
- **`Life N/A`** for subsystems means the subsystem has no per-guild
  in-process cache to forget; the DB tables it owns are purged via the
  existing guild_lifecycle steps.
- **`Tests 🟡`** means basic coverage exists but is incomplete relative
  to the consistency contract (no enum drift / no pipeline contract /
  no event payload tests).
- The 🚧 markers for `xp.announce_channel`, `economy.log_channel`, and
  `governance.trusted_role` track the three keys that will be backfilled
  in PR-5/6 and flipped via canary in PR-7. **XP threshold roles
  intentionally deferred** — list-shaped 1:N data does not fit the 1:1
  `subsystem_bindings` schema; a dedicated table is the right shape
  when admin UX motivates it.

---

## 3. Data retention policy

Lifecycle-completeness contract: every guild-keyed table must have a
`delete_for_guild` hook called from `guild_lifecycle.teardown`, or
explicitly opt out with a documented retention rationale.

| Data | Policy | Owner | Wired in |
|---|---|---|---|
| `panel_anchors` | delete on guild leave | UI framework | existing |
| `runtime_sessions` | delete on guild leave (cascades state) | session_manager | existing |
| `runtime_session_state` | cascade from session delete | state_store | existing |
| `governance_audit_log` | preserve (append-only) | governance | N/A |
| `capability_execution_overrides` | delete on guild leave (`forget_guild_capabilities`) | governance | existing |
| governance cache | invalidate on guild leave | governance | existing |
| `guild_config` cache | forget on guild leave | runtime | existing |
| scope_locks (per-cog) | teardown on guild leave | runtime | existing |
| `resource_validation_cache` | delete on guild leave | resources | 🚧 PR-1 |
| `subsystem_bindings` (active rows) | delete on guild leave | bindings | 🚧 PR-1 |
| `binding_audit_log` | **preserve** (append-only; forensic value) — split cleanup primitive so active-row delete does NOT touch audit | bindings | 🚧 PR-1 splits primitives |
| `feature_flag_state` (per-guild rows) | delete on guild leave; global rows preserved | feature flags | PR-2 |
| `environment_tiers` (per-guild rows) | delete on guild leave | feature flags | PR-2 |
| `feature_flag_audit` | preserve (append-only) | feature flags | PR-3 |
| `user_participation`, `user_subscriptions`, `user_preferences`, `user_visibility_overrides` | **guild-scoped rows deleted on guild leave**; user-scoped semantics await user_lifecycle | participation | PR-8 |
| participation audit tables | preserve | participation | PR-8 |
| `platform_migration_checkpoints` | preserve (forensic); per-guild rows may be purged on guild leave at owner's option | logical migrations | PR-5 |
| `economy_audit_log` | preserve | economy_service | N/A |
| `mod_logs` | preserve | moderation_service | N/A |
| `schema_migrations` | preserve | migration runner | N/A |

**Rationale for audit-preserve:** audit tables are append-only by
design intent. Purging them on guild leave erases the forensic trail
the column was added for. Storage cost is negligible. If a guild
re-adds the bot, preserved audit context is more valuable than a clean
slate. **Owner has confirmed: preserve `binding_audit_log` on guild
leave.**

**Rationale for guild-scoped participation tables:** the four
participation tables MUST include `guild_id` even though they key on
`user_id` for read access. Without `guild_id`, guild-leave cannot
purge a user's participation in that guild — the data leaks across
guilds the user is also in, and GDPR-style deletion is impossible
without account-level lifecycle. Add `guild_id` to every PK and add
guild-scoped `delete_for_guild` hooks in PR-8.

---

## 4. Event payload contract

Every catalogued event (`core/events_catalogue.KNOWN_EVENTS`) must
specify the fields below in the emitting module's docstring AND in
`docs/ownership.md`'s event table.

Required fields on every event:
- `mutation_id` — UUID; idempotency key, propagated end-to-end
- `occurred_at` — UTC timestamp
- domain identity field — `guild_id` or `user_id` or `flag_name`
- prev → new transition fields (when applicable)
- actor: `actor_id`, `actor_type`
- source domain (implicit from emitter)

Semantics:
- **Advisory.** Events are emitted after DB commit. Subscriber failure
  is logged with `mutation_id`, never raised. DB is authoritative.
- **At-most-once per emit.** Replay safety lives in the subscriber
  (`mutation_id` is the idempotency key).
- **Cataloged.** `bus.emit` warns if the name is not in
  `core/events_catalogue.KNOWN_EVENTS`.

Events introduced by Phase 2 plan (status: ❌ until their PR lands):

| Event | Emitter | Required payload fields | PR |
|---|---|---|---|
| `feature_flags.changed` | `RolloutMutationPipeline.set_flag_state` | `flag_name, guild_id, prev_state, new_state, mutation_id, occurred_at, actor_id, actor_type` | PR-3 |
| `rollout.advanced` | `RolloutMutationPipeline.set_rollout_percent` | `flag_name, prev_percent, new_percent, mutation_id, occurred_at, actor_id, actor_type` | PR-3 |
| `environment_tier.changed` | `RolloutMutationPipeline.set_environment_tier` | `guild_id, prev_tier, new_tier, mutation_id, occurred_at, actor_id, actor_type` | PR-3 |
| `participation.changed` | `ParticipationMutationPipeline.set_participation` | `user_id, guild_id, subsystem, prev_state, new_state, mutation_id, occurred_at, actor_id, actor_type` | PR-9 |
| `subscription.changed` | `ParticipationMutationPipeline.set_subscription` | `user_id, guild_id, subsystem, topic, prev_enabled, new_enabled, mutation_id, occurred_at, actor_id, actor_type` | PR-9 |
| `user_preference.changed` | `ParticipationMutationPipeline.set_preference` | `user_id, guild_id, key, mutation_id, occurred_at, actor_id, actor_type` (value intentionally omitted) | PR-9 |
| `user_visibility.changed` | `ParticipationMutationPipeline.set_visibility` | `user_id, guild_id, subsystem, prev_visibility, new_visibility, mutation_id, occurred_at, actor_id, actor_type` | PR-9 |

---

## 5. Hard rules before Phase 2 PRs begin

These are non-negotiable. Each is enforced (or will be) by tests.

1. **Import-cycle regression.** `utils/helpers.py` and
   `governance/__init__.py` MUST NOT contain top-level
   `from core.runtime import ...` statements (PR #74 fix).
   `tests/unit/runtime/test_import_cycle_regression.py` guards this.

2. **No direct DB writes to domain tables outside the domain's DB
   module or pipeline.** AST scan to be added per domain as it lands.

3. **No cog branches on `is_enabled("bindings.primary", ...)`
   directly.** Only `core/runtime/config_arbitration.py` may. AST
   scan to be added in PR-4.

4. **No collapsed user participation blob.** The four participation
   concerns are four separate tables, four separate mutation
   entrypoints, four separate events. There is no "user settings
   service" or "participation blob accessor."

5. **No setup UI direct mutation calls.** When setup work begins, an
   AST scan must enforce that `cogs/setup/` and `views/setup/` route
   all writes through pipelines.

6. **Feature flags must use the runtime evaluator (post-PR-2).** AST
   scan: any code reading a declared flag uses `is_enabled(...)`, not
   direct DB reads or `FEATURE_FLAGS[name].default`.

7. **Enum drift guards.** Every CHECK constraint has a Python ↔ DB
   alignment test. Pattern: `test_resource_kind_alignment.py`,
   `test_binding_constraints_alignment.py`. Extend per new table.

8. **`ResourceStatus.BOUND` is structural-only.** No permission check
   may treat `BOUND` as evidence of permission readiness.

9. **Guild teardown completeness.** Every module under `utils/db/`
   exposing `delete_for_guild` is invoked from
   `guild_lifecycle.teardown` (allowlist user-keyed exceptions).

10. **Views do not own persistence.** No `cogs/*/views/*.py` or
    `views/**.py` calls `utils/db/*` writes directly.

11. **Event subscriber failure is logged, not raised.** Verified by a
    subscriber-failure test per pipeline.

12. **Bootstrap fallback policy.** With `feature_flag.primary = off`
    (env), evaluator never queries DB. With DB connection failure,
    evaluator returns declared defaults and emits bootstrap metric.

13. **Backfill rows are tagged.** Every backfill-written binding row
    has `actor_type="backfill"` in its audit row, enabling rollback
    by predicate.

14. **Standard library hashing only.** Rollout hashing uses
    `hashlib.sha256` — no new `mmh3` or other hashing dependency
    unless already present.

---

## 6. Do-not-start-yet list

> **Status update (2026-05-31) — reconciled with shipped code.** The
> **guild setup wizard shipped** after this list was written
> (`cogs.setup_cog`, registered in `disbot/config.py`; built and
> live-tested 2026-05-29). Per "the source file wins," it is removed from
> the list below — it is now in *finalization*, not greenfield. See
> `docs/setup-platform/setup_wizard_finalization_plan.md`. The per-user surfaces remain
> deferred.

These must not be implemented until the Phase 2 substrate is complete
(PR-0 through PR-10 on `main` and stable, setup readiness gate
satisfied):

- ~~Setup wizard UI~~ → **SHIPPED** (guild scope): routes every write
  through the canonical mutation pipelines, read-only preflight, audited
  session lifecycle. Finalization tracked in
  `docs/setup-platform/setup_wizard_finalization_plan.md`.
- Resource provisioning runtime (creating channels/roles/categories on
  the operator's behalf) — *note: the `ResourceProvisioningPipeline` is now
  invoked by the shipped wizard with explicit confirmation (no silent
  auto-create); the broader provisioning runtime stays deferred*
- `/myprofile` or any participation hub UI — **still deferred** (plan-only;
  the participation backend exists but has zero UI callers)
- Notification routing (DMs, reminders, opt-in notifications)
- Production flip of `bindings.primary` (canary in PR-7 only;
  production flip is its own future PR after canary observation)
- Removal of legacy `guild_settings` rows for migrated keys (legacy
  fallback retained for at least one release post-production-flip)
- Admin override on participation mutations (PR-9 ships only user-self)
- Discord-facing command for setting feature flags (DB/script only in
  PR-3; command is a follow-up)
- Component registry implementation (planned in PR-11; implemented
  post-Phase 2)
- Economy reminder subscriptions, leaderboard visibility flip,
  moderation participation gating (out of scope until participation
  substrate is proven)
- Any new "settings service" or god-object that collapses
  participation, subscriptions, preferences, visibility
- XP threshold role bindings via the existing 1:1 binding schema

---

## 7. Open documents and their status

| Doc | Status | Action |
|---|---|---|
| `docs/architecture.md` | ✅ current | none |
| `docs/ownership.md` | ✅ current | extend per new domain as PRs land |
| `docs/runtime_contracts.md` | ✅ current | extend per new lifecycle as PRs land |
| `docs/setup-platform/roadmap_setup_platform.md` | ✅ current high-level | this ledger is the operational truth map; the roadmap remains the strategic plan |
| `docs/archive/phase_2b_bindings_plan.md` | 🟡 **historical** — shipped in PR #73 (see banner) | preserved for context; do not extend |
| `docs/decisions/*` | ✅ current | add ADR per architectural decision (e.g. `003-binding-audit-preserve.md` would be the next) |
| `docs/architecture/service_ownership.md` | ✅ created 2026-05-24 | quick-lookup companion to `ownership.md`; update when `ownership.md` changes |
| `docs/audits/mutation_boundary_audit.md` | ✅ created 2026-05-24 | first formal mutation audit; update as new mutation paths land |

---

## 8. Phase 2 implementation PR sequence

This is the operational plan. Each PR is small, modular, and gated.
Full detail in the plan file referenced by the active session.

| PR | Title | Risk | Migration |
|---|---|---|---|
| PR-0 | platform consistency ledger + stale-doc classification | 🟢 | none |
| PR-1 | guild teardown cleanup (split binding primitives + wire) | 🟢 | none |
| PR-2 | feature flag evaluator foundation (+ env tiers, bootstrap policy) | 🟡 | 023, 024 |
| PR-3 | rollout mutation + feature flag audit + events | 🟡 | 025 |
| PR-4 | central read-source arbitration (ConfigReadResult) | 🟢 | none |
| PR-5 | binding backfill dry-run + reconciliation + checkpoints | 🟢 | 026 |
| PR-6 | binding backfill write phase (idempotent, audited) | 🟡 | 027 if needed |
| PR-7 | `bindings.primary` canary flip via arbitration | 🔴 per-guild | none |
| PR-8 | participation storage + cache (guild-scoped tables) | 🟡 | 028 |
| PR-9 | participation mutation pipeline + XP opt-out proof | 🟡 | none |
| PR-10 | diagnostics consistency surface (+ consistency/migrations/health) | 🟢 | none |
| PR-11 | UI consistency foundation (help/back/edit-vs-send + component plan) | 🟡 | none |
| PR-12 | setup wizard plan refresh (plan only) | 🟢 | none |

Migration numbering reserved: 023 (feature_flag_state), 024
(environment_tiers), 025 (feature_flag_audit), 026
(platform_migration_checkpoints), 027 (binding actor_type if needed),
028 (user_participation suite + audit).

---

> **Ledger doctrine.** This document is consulted before code. New
> entries (domain or subsystem) MUST be added before the PR that
> introduces them lands, so the ledger is always the up-to-date map.
> Cells move from ❌ → 🚧 → ✅ as PRs ship.
