# Server Management — Status Tracker

> **Status:** `living-ledger` — living status ledger. This is the **single current record** of what
> the server-management initiative has actually shipped and what is queued next.
> When this tracker and the roadmap / implementation plan disagree about *what is
> done*, **this tracker (cross-checked against source) wins**; the roadmap remains
> the target architecture and the implementation plan remains the PR-scope detail.
>
> **Date:** 2026-06-05 (originally verified @ `f0f0824` / #523; updated 2026-06-06
> for PR8+PR9, then for **PR10's first + second + third slices** — config-backed
> moderation behaviour, require-reason, bot-readiness diagnostics, and configurable
> warn escalation). **Body is current through PR10's third slice; the remaining PR10
> items + PR11–PR14 are the queue** — the "Shipped" + "Remaining queue" sections
> below are authoritative.
>
> **Companion docs (read together):**
> - `docs/planning/server-management-roadmap-2026-06-05.md` — target architecture
>   + maintainer decisions. Its Phase 0–5 PR *ordering* is **superseded** (see below).
> - `docs/planning/server-management-implementation-plan-2026-06-05.md` — the
>   dependency-ordered PR1→PR14 scope detail that the shipped work follows.
> - Binding contracts updated by this work: `docs/ownership.md`,
>   `docs/architecture/service_ownership.md`, `docs/server-logging.md`,
>   `docs/resource-provisioning-overview.md`, `docs/direct-db-exception-ledger.md`.

---

## How the two planning docs relate (PR order reconciliation)

The roadmap (#520) proposed a Phase 0–5 ordering that led with **selectors
(PR 1A) → mutation primitives (PR 1B) → moderation (PR 2A) → channel lifecycle
(PR 2B)**. The implementation plan (#521) then **re-sequenced** that into a
dependency-ordered PR1→PR14 list that leads with **moderation convergence**,
because moderation was the cheapest, fully self-contained convergence win and the
exemplar for the invariant pattern every later PR reuses.

**The implementation plan's order is what shipped.** The roadmap's Phase-ordering
is therefore superseded as an *execution sequence* (its architecture and
maintainer decisions still stand). Mapping:

| Shipped PR | Plan label | Roadmap label | Notes |
|---|---|---|---|
| #520 | — | Phase 0 / PR 0 | Roadmap document only. |
| #521 | PR1 | PR 2A | Moderation convergence (led, ahead of selectors). |
| #522 | PR2 | PR 1A (partial) | Role feasibility model + `MultiRoleSelector` only. |
| #523 | PR3 + PR4 | PR 1B + PR 2B (partial) | Lifecycle contract + channel rename/move/delete only. |

---

## Shipped

### #520 — Server Management Roadmap (docs only)
Landed `docs/planning/server-management-roadmap-2026-06-05.md`: source-grounded
target architecture, the seven settled maintainer decisions, and the capability
matrix. No behavior change.

### #521 — PR1: Moderation service convergence
Routes **every manual moderation action** through `services/moderation_service.py`;
no surface mutates `mod_logs` / Discord directly anymore.

- **Both manual surfaces converged:** the prefix commands (`cogs/moderation_cog.py`)
  and the 7 modals (`views/moderation/modals.py`) now call
  `moderation_service.{warn,timeout,kick,ban,unban,clear_warnings}`. Hierarchy/owner
  checks and the warn-threshold read stay at the cog/view layer (the service does
  **not** re-check permissions).
- **Three audit signals per action**, fanned out by the shared `_record_action`
  helper (mirrors `resource_provisioning.py`):
  1. **`mod_logs` row** (`db.log_mod_action`) — the **authoritative, append-only
     moderation history**. Source of truth for `modlogs`; no `mutation_id` column,
     no migration.
  2. **`audit.action_recorded`** (`emit_audit_action`) — a **best-effort generic
     audit-routing companion** consumed by `services.server_logging` (one canonical
     embed to the audit channel). **NOT** a second history store; a dropped
     companion never invalidates the `mod_logs` row.
  3. **`moderation.action_taken`** (`EVT_MOD_ACTION`) — the domain event, now
     carrying the **same `mutation_id`** as the companion for correlation.
- **`clearwarnings` is the stored/domain token** (one word) — chosen to match every
  row the pre-convergence surfaces already wrote, so history and `modlogs` rendering
  stay consistent. (The previously-unused service path used `clear_warnings`; that
  was changed *to* `clearwarnings`, **not** the other way around — so **no display
  normalization was needed**, contrary to the plan's Rev-2 / Open-Question #1.)
- **`auto_delete` also routes through `_record_action` now.** Before #521 it emitted
  only `mod_logs` + `EVT_MOD_ACTION`; it now **also emits the `audit.action_recorded`
  companion** (with `actor_type="system"`, `actor_id` `None`/`0`). System auto-deletes
  therefore appear on the audit channel too, keyed `auto_delete:<rule>`.
- **Pinned by** `tests/unit/invariants/test_no_direct_moderation_writes.py` (AST scan
  of `cogs/moderation*` + `views/moderation*`): no direct
  `db.add_warning|clear_warnings|log_mod_action` or `member/guild.kick|ban|unban|timeout`
  outside `moderation_service`. Reads (`db.get_mod_logs`) stay allowed.

### #522 — PR2: Role feasibility model + `MultiRoleSelector`
The shared resource-safety foundation for roles (a partial PR 1A — selectors only,
no diagnostics findings model yet).

- **`utils/role_feasibility.py` (new, pure):** `RoleFeasibility` (frozen) + reason
  codes (`SELECTABLE`, `EVERYONE`, `MANAGED`, `ABOVE_BOT`, `BOT_MISSING_MANAGE_ROLES`,
  `ABOVE_ACTOR`); `evaluate_role(...)`, `manageable_roles(...)` (partition into
  manageable vs. excluded-with-reason), `not_everyone` (default picker filter),
  `summarize_exclusions(...)`. Decomposes the checks already embedded in
  `services.role_automation.check_preflight` and `services.resource_health._inspect_role`
  into one reusable source of truth. `utils` layer — stdlib + `discord` only, so both
  `services/` and `views/` may import it.
- **`views/selectors/multi_role.py` (new):** `MultiRoleSelector`, the role-typed
  sibling of `MultiChannelSelector`; returns role ids, applies a `role_filter`
  (default `not_everyone`) before Discord's 25-option cap. Exported from
  `views/selectors/__init__.py`.
- **Adopted in** `views/roles/exemptions_panel.py` (replaced the bespoke native
  `RoleSelect`). Other role pickers (template_picker, ai/policy role view,
  settings/edit_role, roles/management_panel) **still use native `RoleSelect`** — not
  yet converged.
- **Deferred follow-ups:** paging/search beyond 25, stale-selection revalidation, the
  full `Finding`/`FeasibilityReport` diagnostics model, and `resource_health` taxonomy
  alignment.
- **Pinned by** `tests/unit/utils/test_role_feasibility.py`,
  `tests/unit/views/test_selectors.py`, `tests/unit/views/test_role_exemptions_panel.py`.

### #523 — PR3 + PR4: Lifecycle contract + `ChannelLifecycleService`
The shared lifecycle-mutation contract landing with its first consumer.

- **PR3 — `services/lifecycle/contracts.py` (new):** the reusable typed shapes for the
  *change* operations provisioning does not own — `StepResult`, `LifecyclePreview`,
  `LifecycleResult` (all frozen); the **reversibility vocabulary**
  (`reversible` / `compensatable` / `irreversible`); the **outcome classifier**
  (`success` / `partial` / `blocked` / `declined` / `discord_failed`) via
  `classify_outcome`; and `emit_lifecycle_audit` — the best-effort
  `audit.action_recorded` companion wrapper (mirrors the moderation three-signal
  pattern). Re-exported from `services/lifecycle/__init__.py`.
- **PR4 — `services/channel_lifecycle_service.py` (new):** `ChannelLifecycleService`
  is the canonical owner of channel **rename / move / delete only** (single + batch).
  It checks the bot's **Manage Channels** permission (actor authority stays at the cog,
  as with `moderation_service`); requires `confirmed=True` for irreversible deletes
  (the typed command invocation *is* the confirmation); captures per-channel Discord
  failures as **failed steps** rather than raising (partial-failure reporting); and
  emits the audit companion + domain event sharing one `mutation_id`.
- **Routed:** the `channel_cog` typed commands `delete`, `bulkdelete`, `move`, `rename`,
  and the `evt …delete` path now go through the service.
- **New catalogued event** `channel.lifecycle_changed` (advisory; payload
  `mutation_id, guild_id, operation, outcome, applied[], failed[], occurred_at`).
- **Pinned by** `tests/unit/invariants/test_no_direct_channel_mutations.py` — scoped to
  the **`ChannelCog` class body** and to `.delete()` / `.edit()` only (so the sibling
  paginator's legitimate `self.message.edit` is not a false positive), plus
  `tests/unit/services/test_lifecycle_contracts.py` and
  `tests/unit/services/test_channel_lifecycle_service.py`.
- **Deferred follow-ups (still on their current cog paths):** channel **creation**
  (owned by `utils.channels` / `ResourceProvisioningPipeline` + the no-silent-auto-create
  invariant — see `cogs/channel_cog.py` `evt create`), **clone**, **lock/unlock**,
  **permission overwrites** (`set` / `set_permissions`), the channel/move-reorder
  **panel UI**, and first-class **category lifecycle**. The invariant pins only
  `.delete()` / `.edit()` for now — these other operations are not yet routed.

### PR5 — Role lifecycle service + non-destructive time/XP thresholds (#525)
The role-domain sibling of the channel lifecycle service, plus the data-loss fix
for threshold removal.

- **`services/role_lifecycle_service.py` (new):** `RoleLifecycleService` owns
  operator-driven role **create / edit / delete**. Checks the bot's Manage Roles
  permission + the per-role manageability verdict (consuming **#522**
  `utils/role_feasibility.py`); irreversible `delete` requires `confirmed=True`;
  Discord failures become a failed `StepResult`. Built on **#523**'s
  `services/lifecycle` contract; emits the `audit.action_recorded` companion +
  the new catalogued **`role.lifecycle_changed`** event (shared `mutation_id`).
  It is the audited `guild.create_role` caller for *manual* roles and is added to
  the `test_no_silent_auto_create.py` allowlist (subsystem role provisioning still
  goes through `ResourceProvisioningPipeline`).
- **Routed:** `role_cog` `createrole` / `deleterole`, `views/roles/creation_panel`
  (create), and `views/roles/management_panel` (edit + delete). `role_cog` and
  `creation_panel` were **removed** from the no-silent-auto-create allowlist (their
  `create_role` now routes through the service).
- **Non-destructive threshold removal (the data-loss fix):** new field-specific
  `db.clear_role_time_threshold` / `clear_role_xp_threshold` replace the destructive
  full-row `remove_role_threshold` at the three removal sites (`role_cog.unsetrole`,
  `time_roles_panel`, `xp_roles_panel`). Clearing one tier now preserves the other;
  the row is deleted only when no automation field remains. (Previously, removing a
  role's time tier silently wiped its XP tier — see the old `unsetrole` comment.)
- **Shared contract:** added `LifecycleResult.first_error` (used by both the role
  cog and views, avoiding a `cogs → views` helper dependency).
- **Pinned by** `tests/unit/invariants/test_no_direct_role_mutations.py` (role
  create/edit/delete must route; `*.message.edit` paginator refreshes excluded by
  receiver), `tests/unit/services/test_role_lifecycle_service.py`, and
  `tests/unit/db/test_roles_threshold_clear.py`.
- **Deferred (per the PR5 scoping decision):** the `role_thresholds`
  `role_id`/`display_name` schema migration + dual-read groundwork → **PR6** (where
  the ID-persisting selector is its real consumer); member assignment routing
  (reaction roles / automation `add_roles`/`remove_roles`); role reorder; templates.

### PR6 — Dynamic time/XP role config + role-id dual-read (#526)
Closes the free-text role-name foot-gun: both automation sections are now
selector-driven and persist stable role ids.

- **Migration 056** — additive nullable `role_id` / `display_name` on
  `role_thresholds` (the deferred PR5 groundwork, landed *with* its consumer).
- **DB layer (`utils/db/roles.py`)** — `set_role_threshold` / `set_role_xp_threshold`
  take optional `role_id` / `display_name` (COALESCE-preserved on conflict);
  `get_role_thresholds` / `get_xp_threshold_roles` return them. Backward-compatible
  for legacy name-only callers.
- **Selector-driven UI** — the free-text "role name" modals in `time_roles_panel`
  and `xp_roles_panel` are replaced by a role **picker → numeric modal** flow
  (`RoleSelector` → `TimeDaysModal` / `XpLevelModal`), so a persisted threshold
  always references a role that exists, capturing its id + name snapshot.
- **ID-first (dual-read) resolution** — `role_automation.compute_assignments` and
  the XP listener resolve each tier id-first (normalized-name fallback), so a role
  **rename no longer orphans its tier**. `RoleThreshold` gained `role_id`.
- **Stale diagnostics** — both panels flag a tier whose role can no longer be
  resolved (`⚠️ role missing`).
- **Defaults are suggestions** — `_ensure_defaults` and the panel's "Seed Defaults"
  button only seed defaults whose role **exists** (capturing its id); the phantom
  `Neu/Iron/Beacon` name rows are no longer auto-persisted.
- **Pinned by** `tests/unit/db/test_roles_role_id.py`,
  `tests/unit/views/test_role_threshold_selectors.py`, and new id-first /
  rename-survival cases in `test_role_automation.py` + `test_xp_listener_roles.py`.
- **Deferred:** role reorder and templates (PR13); member-assignment routing.

---

## Reconciliations applied this pass (source ↔ docs)

1. **Clear-warnings token.** Docs that predicted `clear_warnings` + display
   normalization were corrected to the shipped reality: **`clearwarnings`** (one word),
   no normalization. Touches the implementation plan, `docs/ownership.md`,
   `docs/architecture/service_ownership.md`, and `docs/server-logging.md`.
2. **One tiny source fix (not docs-only).** `services/server_logging.py`'s
   `_ACTION_COLOR` / `_ACTION_ICON` keyed the clear-warnings style on the old
   `clear_warnings` token, so after #521 the live `clearwarnings` action rendered with
   the generic dark-grey • style instead of the intended blurple 🧹. Added the
   canonical `clearwarnings` key (kept `clear_warnings` as a back-compat alias) and a
   regression test (`test_format_log_embed_clearwarnings_uses_blurple`). The previous
   `test_server_logging.py` routing loop tested only the dead token, so CI had stayed
   green while the live token went unstyled.
3. **Direct-DB ledger.** `moderation_cog`'s warn/clear-warnings direct DB writes are
   gone (routed through the service, AST-pinned); the only remaining direct `db.*` in
   the cog is the read `db.get_mod_logs`.

---

### PR7 — Channel move/reorder panel + reorder primitive *(shipped)*
The deferred move/reorder UI from #523, routed through the lifecycle service.

- **Service: new `reorder` operation** on `ChannelLifecycleService` — sends
  channel(s) to the **top / bottom** of their category via `channel.move`
  (reversibility = compensatable). The service now owns
  `rename` / `move` / `delete` / `reorder`.
- **Move/Reorder panel** (`views/channels/move_panel._MoveSubView`) — wired into
  the channel hub (`!channelmenu` → "Move / Reorder"). Multi-select channels →
  **Move to Category** (destination picker) or **Send to Top / Bottom**, applied
  through the audited service with per-channel partial-failure reporting.
- **`channel.lifecycle_changed`** now also covers `reorder`.
- **Pinned by** new reorder cases in
  `tests/unit/services/test_channel_lifecycle_service.py` +
  `tests/unit/views/test_channel_move_panel.py` (the panel routes through the
  service and guards empty selection / unchosen destination).
- **Deferred:** arbitrary before/after positioning, "Revert Safe Changes", and
  first-class category create/rename/delete UI (categories are already movable /
  renamable / deletable through the service as `GuildChannel`s).

### PR8 + PR9 — Cleanup versioning, builder, dry-run, panel diagnostics *(shipped 2026-06-06)*

Shipped together on one branch (`claude/nifty-cerf-59MKG`). **Presets-only (lean)**
per maintainer decision — every write maps to the existing three `cleanup_policies`
columns through the unchanged governance pipeline.

- **PR8** — migration `058` adds `policy_version INTEGER NOT NULL DEFAULT 1`
  (additive; PK + RC-5 `scope_type` CHECK untouched; resolved behaviour
  byte-identical). `services.cleanup_levels`: `level_for_columns` round-trip +
  `POLICY_VERSION`. `get_all_cleanup_for_guild` returns `policy_version`.
- **PR9** — `services/cleanup_diagnostics.py` (async, presets-only):
  `collect_cleanup_diagnostics` (per-scope levels, stale-scope + ineffective-row
  detection), `preview_cleanup_change` (side-effect-free dry-run via the **real**
  resolver, so preview == runtime), `apply_cleanup_change` (audited apply through
  the unchanged pipeline). `views/cleanup/policy_panel.py`: diagnostics view +
  presets builder (scope → level → dry-run → confirm → apply), admin re-check at
  the mutation point. Surfaced via a "Cleanup Policies" button on the cleanup hub
  (`cogs/cleanup/panel.py`).
- **Root-cause fix (found while building):** the setup wizard wrote guild-default
  cleanup at `scope_id=0`, but the resolver looks up guild policy at
  `scope_id=guild_id` — so **guild-default never took effect**. Centralised the
  write-side convention in `cleanup_levels.cleanup_scope_id()` and fixed
  `setup_operations._apply_set_cleanup_policy`. Verified live + regression-pinned.
- **Descope vs the implementation plan:** the plan's PR8 JSONB "dimensions" column
  is **deferred** (no consumer yet); only `policy_version` shipped. Diagnostics
  flag legacy `scope_id=0` guild rows as ineffective (re-set to fix).

### PR10 (first slice) — Config-backed moderation behaviour *(shipped 2026-06-06)*

The first slice of PR10's "first-class moderation configuration": the
behaviour knobs that map directly to a Discord API effect, applied **at the
`services.moderation_service` mutation seam** so every surface (prefix
commands, the seven panel modals, and the future hub) honours them without
re-reading config — the same "guard at the mutation seam" discipline PR1 used
for the audit fan-out. **No migration** — the settings are ordinary scalar
guild settings, operator-editable today through the `!settings → Moderation`
widget dispatcher.

- **`services/moderation_config.py` (new):** `ModerationPolicy` (frozen read
  model) + `load_policy(guild_id)` (composed via `settings_resolution.resolve_value`)
  + `render_dm_message(...)` (a **pure**, no-I/O DM renderer). Owns the canonical
  default constants shared with the schema (drift-pinned).
- **Four settings** (`cogs/moderation/schemas.py`, schema → v2): `dm_on_action`
  (bool toggle), `dm_template` (free-text, `{guild}`/`{action}`/`{reason}`/`{user}`
  tokens — plain replacement, never `str.format`), `ban_delete_message_days`
  (numeric-presets 0/1/7), `max_timeout_minutes` (numeric-presets; default 40320 =
  Discord's 28-day max). New keys in `utils/settings_keys/moderation.py`.
- **Service wiring (`services/moderation_service.py`):** `warn`/`timeout`/`kick`/`ban`
  load the policy and apply it — best-effort notify-the-member DM (before removal
  for kick/ban so the user is still reachable; after the action for warn/timeout),
  ban message-purge via `delete_message_seconds` (only when configured), timeout
  clamped down to the configured ceiling. **Behaviour-preserving by default**: an
  unconfigured guild gets the exact pre-PR10 calls.
- **Pinned by** `tests/unit/services/test_moderation_config.py`,
  new config cases in `tests/unit/services/test_moderation_service.py`, and
  `tests/unit/cogs/test_moderation_schemas.py` (incl. a spec-default ↔ policy-default
  drift guard). Booted live (boot_id `a6a24aea`) — ModerationCog loads with the v2
  schema, 0 ERROR/CRITICAL.
- **Remaining PR10 queue:** moderator/trusted **roles + capabilities**, dedicated
  **log destinations** (today rides `logging_mod_channel` + the generic audit
  channel), **escalation-rule** config, and a **post-action cleanup** hook. These
  touch the capability-authority seam or other subsystems.

### PR10 (second slice) — Required-reason enforcement + bot-readiness diagnostics *(shipped 2026-06-07)*

Two contained remaining PR10 items, kept consistent with the first slice's
service-seam discipline:

- **`require_reason`** (bool setting; warn / kick / ban) — enforced at the
  `moderation_service` seam via a new `ReasonRequiredError` raised **before** any side
  effect; the cog + the seven modals catch it and tell the operator a reason is
  required. **Timeout is exempt** (its reason carries the duration). Placeholder-aware
  (`moderation_config.has_reason` treats `"No reason provided"` as no reason), so the
  surfaces needed only the catch — no reason-handling rewrite.
- **Bot-readiness diagnostics** — new pure `utils/moderation_feasibility.py`
  (`evaluate_moderation_readiness` / `render_readiness_line`, mirroring
  `utils/role_feasibility.py`); the mod panel embed gains a read-only **"🤖 Bot
  readiness"** field (has Ban/Kick/Timeout? where does my top role sit?) so an operator
  sees *before* clicking why an action might fail.
- **Pinned by** `tests/unit/utils/test_moderation_feasibility.py`,
  `tests/unit/cogs/test_moderation_panel_embed.py`, require-reason cases in
  `test_moderation_service.py`, and `has_reason` / `require_reason` cases in
  `test_moderation_config.py` + `test_moderation_schemas.py`.

### PR10 (third slice) — Configurable warn escalation, owned at the seam *(shipped 2026-06-07)*

Makes the warn→escalation ladder first-class and configurable, and moves its
orchestration **off the surfaces into `moderation_service`** — deleting the
copy-pasted escalation block the cog and the panel's `_WarnModal` each carried
(the in-source comment said it stayed surface-side "until moderation config owns
it"). Scalar/KV, **no migration**, behaviour-preserving by default.

- **One new setting** (`cogs/moderation/schemas.py`, schema → v3):
  `warn_escalation_action` — enum `timeout` (default = today) / `kick` / `ban` /
  `none`, an `allowed_values` Select; key `MOD_WARN_ESCALATION_ACTION`. The
  existing `warn_threshold` / `warn_timeout_minutes` defaults were consolidated
  into the `moderation_config` canonical constants (one source of truth, drift-pinned).
- **`moderation_config`** gains the three escalation fields on `ModerationPolicy`
  plus a **pure** `evaluate_escalation(count, policy)` (fail-safe to no-op on an
  unknown action).
- **`moderation_service.warn`** now returns a frozen `WarnOutcome` and **owns the
  ladder**: at `warn_threshold` it runs the configured terminal action via the
  sibling `timeout`/`kick`/`ban` functions (so it stays audited + DM'd) and resets
  the count on success; a Discord `Forbidden` is reported on the outcome (soft
  warning), not raised. The cog + `_WarnModal` render the outcome via the shared
  pure `cogs/moderation/_helpers.render_warn_outcome_lines`.
- **Pinned by** `evaluate_escalation` + policy cases in `test_moderation_config.py`,
  escalation (timeout/kick/ban/none/below-threshold/Forbidden-blocked) cases in
  `test_moderation_service.py`, the `warn_escalation_action` shape + drift guard in
  `test_moderation_schemas.py`, and the rewritten warn-modal cases in
  `test_moderation_modals_defer.py`. Command-map doc updated for the doc-pin tests.
- **Remaining PR10 queue:** moderator/trusted **roles + capabilities**, dedicated
  **log destinations**, and a **post-action cleanup** hook.

---

## Remaining queue (starts at PR10)

Per the implementation plan's dependency order. PR7–PR9 shipped (see above).

| PR | Objective | Depends on |
|---|---|---|
| **PR10** | Moderation first-class configuration. **First + second + third slices shipped** (DMs, ban message-purge, timeout ceiling, require-reason, bot-readiness diagnostics, configurable warn escalation — see above). Remaining: mod-roles + capabilities, dedicated log destinations, post-action cleanup hook. | #521 |
| **PR11** | Setup role/moderation/governance sections. | PR5, PR8–PR10, #522 |
| **PR12** | Setup diagnostics & repair. | PR5, #522 |
| **PR13** | Deterministic + AI role templates. | PR5, #523 |
| **PR14** | Server Management Hub (last). | all managers |

Near-term completion items folded into the above: finish PR2's diagnostics/findings
model and selector paging/search (in PR6 as the first production consumer); finish
PR4's clone / overwrites / creation routing (in PR7).
