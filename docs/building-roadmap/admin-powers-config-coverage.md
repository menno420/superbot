# Admin Powers — Config Coverage Map

> **Status:** `plan` — admin-powers config-coverage backlog; cross-check source.

Runtime impact: None
Scope: Pipeline-ownership map for every category of admin/operator config — answers "who owns the write path for this kind of change?"

This document captures the ownership rule for every category of admin
or operator change. It is **a reference, not a refactor plan** —
existing surfaces are not in scope. New admin/settings work should
align with the rules here so we stop accumulating ad-hoc write paths.

Related references:

- `command-integration-standard.md` — non-negotiable rules every command/panel must obey
- `hub-ui-standard.md` — hub/panel shape standard
- `config-input-standard.md` — input-collection standard (the front end that calls these pipelines)
- `../settings-customization-roadmap.md`
- `../platform-consistency-ledger.md`

---

## Why this doc exists

Several subsystems still write directly from view callbacks or admin
commands into ``guild_config`` (or the relevant table) without going
through a pipeline. The result is the same operation having a different
side-effect surface depending on which entry point the operator used:

- Some surfaces emit an audit row; others don't.
- Some invalidate the relevant cache; others rely on next-fetch
  staleness.
- Some emit a domain event so listeners react; others mutate silently.

This doc is the canonical answer to "for this kind of change, which
pipeline must the write path go through?" — so any new admin surface
or any future migration of an old surface can pick the right back end
without re-deriving the rules.

---

## Statement

> **Feature Action Panels are valid. Direct mutation from view callbacks
> is the anti-pattern.**

A view callback that opens a confirm step, gathers input, and then calls
a mutation pipeline is the canonical shape. The thing we are migrating
away from is the view callback that writes to the DB itself, calls
``guild_config.set`` directly, or otherwise side-steps the pipeline.

---

## Default-on canonical surface

The Settings Manager cog (``!settings``) is the canonical landing
surface for scalar config changes that go through
``SettingsMutationPipeline``. Since stabilization-plan PR #8 it
defaults ON — administrators see the hub the first time they
invoke ``!settings`` without any opt-in. The feature flag remains
in place as a kill-switch (``SUPERBOT_FF_SETTINGS__MANAGER_COG__ENABLED=off``
env override or the future ``!platform flags`` command) so a guild
experiencing trouble can disable the runtime behaviour without
touching deploy artefacts.

The flag flip is independent of the architectural ownership rules
below — those describe which pipeline owns each category of change
regardless of whether the front-end happens to ride the Settings
Manager cog or some other surface.

---

## Ownership rules

Eight categories of change, eight ownership rules.

### 1. Scalar settings → `SettingsMutationPipeline`

**Examples:** XP cooldown, daily reward amount, raid threshold,
welcome message, level-up message template, feature toggles whose
shape is `setting_key=value`.

**Pipeline:** `services/settings_mutation.py:SettingsMutationPipeline`.

**Contract:**
- Validates against the `SettingSpec` (type, bounds, regex).
- Writes the new value to `guild_settings`.
- Writes an audit row to `audit_log` with operator id, before/after.
- Invalidates the `guild_config` cache for this guild.
- Emits a `setting_changed` domain event.

**Front-end strategies:** `boolean_buttons`, `enum_select`,
`numeric_presets`, `text_modal`, `advanced_custom`.

### 2. Bindings → `BindingMutationPipeline`

**Examples:** mod role, admin role, audit log channel, mod log channel,
welcome channel, level-up channel, prize drop channel, custom XP role
thresholds.

**Pipeline:** `services/binding_mutation.py:BindingMutationPipeline`.

**Contract:**
- Validates the target exists in the guild (role/channel still present).
- Validates the binding spec (e.g. role tier doesn't exceed operator's
  own).
- Writes the binding row.
- Writes an audit row.
- Invalidates the binding cache (and any downstream caches the
  `BindingSpec` declares).
- Emits a `binding_changed` event for listeners (e.g. logging service
  re-resolves routes).

**Front-end strategies:** `role_select`, `channel_select`,
sometimes `member_select` for member-typed bindings.

### 3. Resources → `ResourceProvisioningPipeline`

**Examples:** creating the moderation log channel from scratch,
ensuring the mute role exists with the right permissions, allocating a
new economy currency category.

**Pipeline:** `services/resource_provisioning.py:ResourceProvisioningPipeline`.

**Contract:**
- Checks whether the resource already exists (idempotent by design).
- Creates the resource if needed via the Discord API.
- Persists the resulting id into the relevant binding via
  `BindingMutationPipeline`.
- Writes an audit row.
- Emits a `resource_provisioned` event.

**Front-end strategies:** `Provision` button on the relevant config
panel; typically used during the setup wizard's first-run flow.

### 4. Access / visibility → governance writes

**Examples:** raising a member to operator tier, granting a one-off
override (allow this user to use this command despite the default
visibility rule), pausing a subsystem for one guild.

**Pipeline:** `services/governance_service.py` write APIs (the
mutation surface is split across `governance_service` and the rules
modules under `governance/`).

**Contract:**
- Validates the operator's own tier covers the grant.
- Writes the access record (or override row).
- Writes an audit row.
- Invalidates the per-member visibility cache.
- Emits a `governance_changed` event for the visibility cache.

**Front-end strategies:** `role_select` or `member_select` plus a
required confirm (any grant is a power-elevation surface).

### 5. Cleanup policies / word lists → cleanup service / cleanup storage

**Examples:** adding a word to the blocked list, removing a word,
adjusting the cleanup retention window, enabling regex mode.

**Pipeline:** `cogs/cleanup/` services (the cleanup subsystem owns its
own store — there is no `CleanupMutationPipeline` because the wordlist
is stored as a structured column, not as guild_settings scalars).

**Contract:**
- Validates regex compiles (when regex mode).
- Writes the new list to the cleanup store.
- Writes an audit row.
- Invalidates the cleanup compiled-pattern cache.
- Emits a `cleanup_policy_changed` event so any in-flight cleanup task
  re-reads the policy on its next iteration.

**Front-end strategies:** `text_modal` for word add/remove,
`boolean_buttons` for mode toggles, `numeric_presets` for retention.

### 6. Logging routes → logging service / route pipeline

**Examples:** routing audit-log events to a specific channel, splitting
mod-log routing from member-event routing, attaching a webhook for one
event type.

**Pipeline:** logging service write paths in `cogs/logging/` and
`services/server_logging.py`.

**Contract:**
- Validates the destination is reachable (channel or webhook).
- Writes the route to the logging-route store.
- Writes an audit row.
- Invalidates the logging-route cache.
- Emits a `logging_route_changed` event for the dispatcher to re-read.

**Front-end strategies:** `channel_select` per route, plus
`enum_select` for event-type when the route is event-scoped.

### 7. Feature flags → `RolloutMutationPipeline`

**Examples:** enabling a feature for one guild, setting a rollout
percentage, scheduling a flag flip, pausing a flag.

**Pipeline:** `services/rollout_mutation.py:RolloutMutationPipeline`.

**Contract:**
- Validates the flag is declared in the feature-flag registry.
- Validates the new state matches the flag's declared shape (boolean,
  percentage, scheduled).
- Writes the new state to the flag store.
- Writes an audit row.
- Invalidates the flag evaluator cache.
- Emits a `flag_changed` event so the evaluator re-reads on next check.

**Front-end strategies:** `boolean_buttons` for simple toggles,
`numeric_presets` for percentage rollouts, `text_modal` for scheduled
flips.

### 8. Game / economy runtime state → domain services

**Examples:** crediting/debiting a wallet, awarding XP, opening a
blackjack round, transferring inventory items.

**Pipeline:** domain services under `services/` — `economy_service`,
`xp_service`, `blackjack_engine`, `moderation_service`,
`game_state_service`, etc. Each owns its own transactional API.

**Contract:**
- Validates the runtime action against domain rules (sufficient
  balance, role still present, game still active).
- Performs the runtime mutation transactionally.
- Writes an audit/event row for surfaces that require one (economy
  always; XP optionally; games on settlement only).
- Invalidates any per-user cache the service maintains.
- Emits a domain event when consumers exist (`economy.credit`,
  `xp.awarded`, `game.settled`).

**Front-end strategies:** typed commands or hub action panels.
**Runtime state is never a config field** — it does not belong on the
settings hub.

### 9. Participation state → `ParticipationMutationPipeline`

**Examples:** opting a member in/out of a tournament, registering for
a participation pool, releasing a participation hold.

**Pipeline:** `services/participation_mutation.py:ParticipationMutationPipeline`.

**Contract:**
- Validates the participation schema for the subsystem.
- Writes the participation record.
- Writes an audit row.
- Invalidates the per-subsystem participation cache.
- Emits a `participation_changed` event.

**Front-end strategies:** `member_select`, `boolean_buttons` for
self-opt-in flows, sometimes `enum_select` for tier-based pools.

---

## How to pick the right pipeline (decision flow)

1. **Is the value a single key-value scalar that lives in
   `guild_settings`?** → `SettingsMutationPipeline`.
2. **Does the value reference a Discord entity (role, channel,
   member)?** → `BindingMutationPipeline` (or `member_select` grant via
   subsystem service).
3. **Does the change create a new Discord resource (channel, role,
   webhook)?** → `ResourceProvisioningPipeline`.
4. **Does the change raise/lower a member's permissions or override
   visibility?** → governance writes (`governance_service`).
5. **Is the change a subsystem-specific policy with its own table
   (wordlist, logging route, participation roster)?** → that
   subsystem's pipeline / service.
6. **Is the change a feature-flag flip or rollout adjustment?** →
   `RolloutMutationPipeline`.
7. **Is the change runtime/domain state (wallet, XP, game)?** → that
   domain service. **Not config; do not surface on Settings.**

If none of the above match, the change is either truly novel (file an
issue) or it is multi-pipeline (a preset that flips several fields at
once — orchestrate the pipeline calls behind a confirm).

---

## Anti-patterns (don't ship these)

1. **View callback writes directly to `guild_config`.** Route through
   `SettingsMutationPipeline.set_scalar`.
2. **View callback writes to a binding table.** Route through
   `BindingMutationPipeline`.
3. **View callback grants a role or assigns a permission directly.**
   Route through the governance write API and confirm.
4. **Admin command that bypasses audit.** Every operator-visible
   mutation writes an audit row. Background reconciliation tasks may
   skip audit but must log at INFO and emit a domain event instead.
5. **Cache invalidation living in the view.** Pipelines own their
   caches. Duplicated invalidation in the view races the pipeline's
   own invalidation and risks stale reads.
6. **Two pipelines writing the same column.** Each ownership rule
   above is exclusive. If two pipelines need to touch the same field,
   factor a service the field's owner exposes and call the service —
   don't write the column twice.
7. **Mixing config and runtime on the same surface.** A "give a member
   100 XP" button on the XP settings page conflates config with runtime
   state. Runtime actions belong on action panels; config belongs on
   settings panels.

---

## Open questions (deferred)

- **Cross-subsystem presets.** The current presets framework wires each
  field through its own pipeline. A "server-type" preset that touches
  10+ subsystems is on the roadmap but needs a pre-flight that surfaces
  every individual confirm in one place.
- **Soft-locks.** Some bindings (mod role, admin role) shouldn't be
  changed during a live incident. A future "config freeze" toggle could
  pause every pipeline except governance writes — not designed yet.
- **Schema-driven pipeline dispatch.** Once every field has a
  `SettingSpec` (or equivalent) that declares its pipeline by name, the
  config UI generator can dispatch automatically. This doc is the
  contract that dispatcher would target.
