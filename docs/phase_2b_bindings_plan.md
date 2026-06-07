# Phase 2b — Guild Bindings (HISTORICAL)

> **Status:** `historical` — ⛔ **HISTORICAL — shipped in PR #73** (plus PR #74
> circular-import hotfix). This document was the pre-implementation
> plan for Phase 2b; it is preserved unchanged below for historical
> context, but is no longer the source of truth.
>
> **What actually shipped vs. the plan below:**
> - ✅ `subsystem_bindings` + `binding_audit_log` (migration 022)
> - ✅ `BindingMutationPipeline` (7-step contract, not the 6-step
>   variant sketched below — the 7th step is the explicit "return
>   result with `mutation_id`" handoff that the pipeline contract
>   standardized on)
> - ✅ `BindingValue` typed read model
> - ✅ `validate_binding_target` (structural-vs-permission split
>   landed in PR #72 hardening)
> - ✅ `EVT_BINDING_CHANGED` catalogued; zero consumers today
> - ✅ `!platform bindings` diagnostics surface
> - 🟡 **Backfill DEFERRED.** The legacy-fallback / dual-write /
>   `bindings.primary` flip strategy described below is correct in
>   spirit but is reordered: the feature-flag evaluator (Phase 2d /
>   PR-2/3 of the consistency plan) and central read-source
>   arbitration (PR-4) must land *before* backfill writes (PR-5/6) and
>   the canary flip (PR-7). Per-cog branching on `bindings.primary`
>   described below is **forbidden** — all flag-gated reads route
>   through `core/runtime/config_arbitration.read_config`.
> - 🟡 **XP threshold roles EXCLUDED from binding migration** — the
>   1:N (level → role) shape does not fit the 1:1
>   `subsystem_bindings(guild_id, subsystem, binding_name)` schema. A
>   dedicated `xp_threshold_roles(guild_id, level, role_id)` table is
>   the right shape when admin UX motivates it.
>
> **Forward pointer:** the operational truth map is
> `docs/platform-consistency-ledger.md`; the active implementation
> plan is in the session-attached Phase 2 plan file. Do not extend
> this document — extend the ledger and the active plan instead.
>
> ---
>
> ## Original plan text follows (do not edit)
>
> **Status:** plan, not implementation.  Phase 2a hardening (PR #72)
> lands first; this document describes what the *next* PR should
> contain, in scope.  It is intentionally narrow — bindings only.  The
> sibling Phase 2 sub-phases (participation, feature flags) ship in
> separate PRs.

## Goal

Replace the raw-string `channel_id` / `role_id` pattern in
`guild_settings` with a typed `subsystem_bindings` table backed by a
mutation pipeline.  Every later phase (4c diagnostics, 6.5 routing, 7
wizard, 7.5 provisioning) reads bindings, never raw IDs.

## Scope (hard limits)

| In scope                                              | Out of scope                          |
|-------------------------------------------------------|---------------------------------------|
| `subsystem_bindings` table + migration                | Setup wizard UI                        |
| `BindingMutationPipeline` (6-step contract)           | Resource provisioning (Phase 7.5)      |
| `BindingValue` typed model + `get_binding` accessor   | Participation tables (Phase 2c)        |
| Legacy `db.get_setting` fallback for migrated keys    | Feature flag runtime (Phase 2d)        |
| Backfill plan for ≥6 raw-id keys                      | Command behavior changes               |
| Diagnostics provider + `!platform bindings`           | Cross-guild template support           |
| Tests for missing / wrong-kind / unknown subsystem    |                                        |

## Storage shape (migration 022)

```sql
CREATE TABLE IF NOT EXISTS subsystem_bindings (
    guild_id          BIGINT      NOT NULL,
    subsystem         TEXT        NOT NULL,
    binding_name      TEXT        NOT NULL,
    kind              TEXT        NOT NULL,
    target_id         BIGINT,         -- NULL for unbound slots
    status            TEXT        NOT NULL DEFAULT 'unresolved',
    last_validated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    version           INTEGER     NOT NULL DEFAULT 1,
    PRIMARY KEY (guild_id, subsystem, binding_name),
    CHECK (kind   IN ('channel', 'role', 'category', 'thread', 'member')),
    CHECK (status IN ('bound', 'unresolved', 'missing', 'invalid'))
);
CREATE INDEX IF NOT EXISTS idx_subsystem_bindings_guild_status
    ON subsystem_bindings (guild_id, status);
```

The `kind` and `status` CHECK constraints reuse the Phase 2a taxonomy
(plus `member` — bindings can target users; Phase 2a resources do not
include members because they are not provisionable).

## Modules to add

```
disbot/core/runtime/bindings.py        — BindingStore + typed read API
disbot/services/binding_mutation.py    — BindingMutationPipeline (6-step)
disbot/utils/db/bindings.py            — CRUD primitives
```

## Read path

`disbot/utils/guild_config_accessors.py` gets a new `get_binding`:

```python
async def get_binding(
    guild_id: int,
    subsystem: str,
    binding_name: str,
) -> BindingValue:
    ...
```

`BindingValue` exposes `target_id: int | None`, `status: ResourceStatus`,
`last_validated_at: datetime`.  Consumers never touch raw target IDs;
the resolver path is always `get_binding(...) → BindingValue →
core.resources.channel_service.get_channel(target_id)` etc.

## Write path

`BindingMutationPipeline` mirrors `GovernanceMutationPipeline`'s
contract.  The six steps:

1. **Input validation** — kind matches a declared `BindingSpec`, target
   exists per `core.resources.discovery.resolve_resource`.
2. **Authority validation** — `capability_required` from the
   `BindingSpec` resolved through Phase 4.5's `access_control_service`
   shell.  Phase 2b accepts a placeholder that requires `administrator`
   tier; Phase 4.5 swaps in the typed capability check.
3. **Read old value** — fetched via `bindings.get_binding`.  Used by
   the audit row.
4. **DB write + audit** — single transaction.  Audit row carries
   `mutation_id`, actor, before/after target IDs.
5. **Cache invalidation** — `guild_config` invalidation for the
   binding namespace key (`subsystem.binding_name`); resource cache
   not touched.
6. **Event emission** — `EVT_BINDING_CHANGED` with the audit
   `mutation_id`.

## Legacy fallback + backfill strategy

Keys to migrate (initial set):

| Key                       | Subsystem    | Binding name        | Kind    |
|---------------------------|--------------|---------------------|---------|
| `XP_ANNOUNCE_CHANNEL`     | xp           | `announce_channel`  | channel |
| `ECONOMY_LOG_CHANNEL`     | economy      | `log_channel`       | channel |
| `TRUSTED_TIER_ROLE_ID`    | governance   | `trusted_role`      | role    |
| `XP_THRESHOLD_ROLES` ids  | xp           | (per-threshold)     | role    |
| `WARN_*` (no resource id) | moderation   | n/a — settings, not bindings | —  |

Backfill runs once at startup behind a feature flag
(`bindings.primary` from Phase 1d declarations — Phase 2b reads it
directly until Phase 2d's runtime evaluator lands):

* **Pre-flip release** (`bindings.primary = false`):
  reads come from `guild_settings` (legacy); writes go to *both*
  tables (legacy + `subsystem_bindings`) so a flag flip is reversible.
* **Flip release** (`bindings.primary = true`):
  reads from `subsystem_bindings`; legacy `guild_settings` rows kept
  as fallback for one full release.
* **Cleanup release**:
  legacy `db.set_setting` calls for migrated keys are AST-blocked;
  the legacy rows can be archived.

The backfill itself runs under `pg_advisory_lock` (mirrors migration
runner's safety primitive) and writes are tagged
`actor_type='backfill_v1'` in the audit table so the inflation is
distinguishable from operator writes.

## Diagnostics + observability

* `!platform bindings` admin command — per-subsystem binding count
  histogram + status counts (`bound`/`missing`/`unresolved`/`invalid`).
* Prometheus metrics:
    * `subsystem_bindings_status_total{subsystem,status}`
    * `binding_mutation_total{subsystem,outcome}`
* EventBus event `EVT_BINDING_CHANGED` in
  `core.events_catalogue.KNOWN_EVENTS` (Phase 4c subscribes for
  cache-status updates; Phase 6.5 will subscribe for notification
  routing once it lands).

## Identity contract

No new surface added in Phase 2b — the schema-side identity contract
extension lands in Phase 6.  Phase 2b only adds soft validation: the
`BindingMutationPipeline` rejects a `binding_name` not declared in
the corresponding `SubsystemSchema` from Phase 1a.

## Test plan (target ≥ 30 tests)

Required coverage:

| Area                               | Test |
|------------------------------------|------|
| Pipeline rejects unknown subsystem | binding for `unknown_subsystem.foo` fails at step 1 |
| Pipeline rejects undeclared name   | binding for declared subsystem but unknown name fails |
| Pipeline rejects wrong kind        | channel-kind binding gets a role id → INVALID, audit row written, no write to bindings table |
| Pipeline rejects below-tier actor  | non-administrator caller raises UnauthorizedBindingMutation |
| Pipeline commits + emits event     | audit row written; cache invalidated; event emitted with `mutation_id` |
| Pipeline rollback on event failure | audit + DB row stays; emit failure logged but does not raise |
| `get_binding` returns BindingValue with status, target_id, timestamp |
| `get_binding` UNRESOLVED when row missing |
| Legacy fallback ON: reads from `guild_settings` |
| Legacy fallback OFF: reads from `subsystem_bindings` |
| Backfill writes `actor_type='backfill_v1'` audit row |
| Backfill is idempotent under repeat |

## Behavior impact

Zero command-facing changes in Phase 2b.  Existing cogs continue to
read via their typed accessors (`get_xp_config`, etc.); the only
visible difference is the new `!platform bindings` admin surface and
the `bindings.primary` flag declaration becoming queryable through
the Phase 4 diagnostics path once 2d ships.

## What's blocked until Phase 2b lands

* Phase 4c resource diagnostics needs `subsystem_bindings` to compute
  "which binding does this missing resource belong to?".  Phase 4c
  can ship a subset (purely resource-side findings) without 2b, but
  the binding-aware findings are blocked.
* Phase 7 wizard cannot persist binding writes until the pipeline
  exists.  The wizard's screen primitives (Phase 5b) can still be
  built; the commit path is the blocker.
* Phase 7.5 setup packs need a binding to point at the resource they
  provisioned.  Until 2b, packs would have to write raw IDs to
  `guild_settings` — exactly the regression 2b is designed to prevent.
* Phase 6.5 notification routing reads
  `binding_value.target_id` for "where to deliver" — blocked.

Phases 2c (participation), 2d (feature flags), 4c (resource
diagnostics in isolation), and 4.5 (governance access-control,
including the role-template surfaces) are *not* blocked by 2b and
can be sequenced in any order relative to it.

---

**Next-PR shape:**
single PR titled "Phase 2b — Guild Bindings + BindingMutationPipeline",
roughly 1500–2000 LOC including migration + tests, no behavior
changes for existing flows.
