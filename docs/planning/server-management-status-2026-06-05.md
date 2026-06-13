# Server Management — Status Tracker

> **Status:** `historical` — completed-initiative record (re-badged by the 2026-06-13 workflow
> reconciliation pass). Server management is **structurally complete** through PR14 (#584); the **only**
> remainder is the gated **PR13 AI generation layer**, now tracked in [`roadmap.md`](../roadmap.md)
> → *Later (gated)*. Retained as the **single record** of what
> the server-management initiative has actually shipped and what is queued next.
> When this tracker and the roadmap / implementation plan disagree about *what is
> done*, **this tracker (cross-checked against source) wins**; the roadmap remains
> the target architecture and the implementation plan remains the PR-scope detail.
>
> **Date:** 2026-06-05 (originally verified @ `f0f0824` / #523; updated 2026-06-06
> for PR8+PR9, then for **PR10's first–fifth slices** — config-backed moderation
> behaviour, require-reason, bot-readiness diagnostics, configurable warn escalation,
> the post-action message cleanup sweep, and the optional public moderation log).
> **Body is current through PR14** (the unified Server Management Hub, built
> 2026-06-08, merged via **#584** — server management is **structurally complete**).
> **PR10 is COMPLETE** (all six slices shipped, incl.
> moderator/trusted roles + capabilities, ADR-008). PR11's **governance** section is
> deferred (owner decision Q-0008); **PR13's deterministic role-templates slice was
> built 2026-06-08** and **only its gated AI generation layer remains queued**
> *(header corrected 2026-06-10 — it previously still queued PR14)* — the "Shipped" +
> "Remaining queue" sections below are authoritative. PR13 also fixed a latent PR11
> regression (the roles section's `set_role_threshold` op could never be staged — the
> DB op-kind gate + CHECK were never widened; migration 059 closes it).
>
> **Companion docs (read together):**
> - `docs/planning/server-management-roadmap-2026-06-05.md` — target architecture
>   + maintainer decisions. Its Phase 0–5 PR *ordering* is **superseded** (see below).
> - `docs/planning/server-management-implementation-plan-2026-06-05.md` — the
>   dependency-ordered PR1→PR14 scope detail that the shipped work follows.
> - Binding contracts updated by this work: `docs/ownership.md`,
>   `docs/architecture/service_ownership.md`, `docs/server-logging.md`,
>   `docs/setup-platform/resource-provisioning-overview.md`, `docs/audits/direct-db-exception-ledger.md`.

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

### PR10 (fourth slice) — Post-action message cleanup, requested at the seam *(shipped 2026-06-07)*

Makes the **post-kick/ban message sweep** first-class and configurable while keeping
moderation/cleanup separation intact (roadmap: *"a moderation action may request an
explicit cleanup operation, but it must not duplicate cleanup policy logic"* and
*"treat message deletion as irreversible"*). Scalar/KV, **no migration**, **default
OFF** (behaviour-preserving).

- **Two new settings** (`cogs/moderation/schemas.py`, schema → v4):
  `post_action_cleanup` — enum `none` (default) / `kick` / `ban` / `both`, an
  `allowed_values` Select (key `MOD_POST_ACTION_CLEANUP`); and
  `post_action_cleanup_limit` — numeric-presets scan bound (1–500, default 100;
  key `MOD_POST_ACTION_CLEANUP_LIMIT`). Both consolidated into the
  `moderation_config` canonical constants (drift-pinned by the schema test).
- **`moderation_config`** gains the two fields on `ModerationPolicy`, an
  `effective_post_action_cleanup_limit` clamp, and a **pure**
  `cleanup_applies_to(action, policy)` (fail-safe: an unknown value never sweeps).
- **`moderation_service.kick` / `.ban`** take an optional invoking `channel` and,
  when the policy covers the action, **request** the sweep from the cleanup
  subsystem (`services.history_cleanup.build_author_cleanup_plan` +
  `apply_history_cleanup_plan`) — moderation re-implements no deletion mechanics.
  Best-effort: a missing Read History / Manage Messages yields a `blocked`
  `CleanupOutcome`, never undoing the (already-succeeded) kick/ban. A meaningful
  sweep (`deleted > 0`) is audited as its own `post_action_cleanup` action; the cog
  + the panel's kick/ban modals render the outcome via the shared pure
  `cogs/moderation/_helpers.render_cleanup_outcome_line`.
- **Root-cause cleanup (found while building):** the `!cleanuphistory` delete loop
  was extracted into `apply_history_cleanup_plan`, so the command and the moderation
  sweep now share **one** deletion path (helper-policy 2-caller rule).
  `server_logging` gained a `post_action_cleanup` embed style (teal 🧽).
- **Pinned by** `cleanup_applies_to` + clamp + policy cases in
  `test_moderation_config.py`, author-plan + apply cases in the new
  `test_history_cleanup.py`, kick/ban-cleanup (configured / disabled / no-channel /
  blocked / empty-sweep) cases in `test_moderation_service.py`, and the
  `post_action_cleanup` shape + drift guard in `test_moderation_schemas.py`.
  Command-map doc updated for the doc-pin tests.
- **Remaining PR10 queue:** moderator/trusted **roles + capabilities** and dedicated
  **log destinations** — both cross-cutting (capability-authority seam /
  server-logging subsystem) and each carrying an owner decision.

### PR10 (fifth slice) — Optional public moderation log *(shipped 2026-06-07)*

The "optional public-log destinations" half of the dedicated-log-destinations item.
An **operator-opt-in** public channel that announces selected actions, **redacting
the acting moderator** (owner decision 2026-06-07: public entries show action + member
+ reason, not who moderated). Scalar/KV, **no migration**, **default OFF**.

- **Two new settings** (`cogs/moderation/schemas.py`, schema → v5):
  `public_log_actions` — enum `none` (default) / `bans` / `removals` (kick+ban) /
  `all` (warn+timeout+kick+ban), an `allowed_values` Select (key
  `MOD_PUBLIC_LOG_ACTIONS`); and `public_log_channel` — a `channel` SettingSpec
  (native picker; empty = off; key `MOD_PUBLIC_LOG_CHANNEL`). unban / clearwarnings /
  the post-action sweep / system auto-deletes are **never** publicised.
- **`moderation_config`** gains the two fields, a `public_log_channel_id` parse
  (fail-safe → 0), and a **pure** `public_log_includes(action, policy)`.
- **Delivery stays in `server_logging`** (it owns log delivery): a **separate**
  `_on_moderation_action_public` subscriber on `moderation.action_taken` (the staff
  path is untouched) pre-filters to disciplinary actions, loads the policy, and posts
  `format_public_log_embed` (member + reason; **no actor, no guild id**). Independent
  of the `logging.enabled` staff switch; fail-safe + counted
  (`mod_public_sent` / `mod_public_skipped`).
- **Pinned by** `public_log_includes` + channel-id parse cases in
  `test_moderation_config.py`, the redaction + routing (sends / not-selected /
  channel-unresolvable / Forbidden / non-disciplinary-prefilter) cases in
  `test_server_logging.py`, and the `public_log_*` shapes + drift guard + **v5** in
  `test_moderation_schemas.py`. Command-map + server-logging docs updated.
- **Remaining PR10 queue:** moderator/trusted **roles + capabilities** — the last
  PR10 item (the capability-native tier-grant; owner decision 2026-06-07: a configured
  role resolves to the `moderator` tier, routed through the capability resolver).

### PR10 (final slice) — Moderator/trusted roles + capabilities *(shipped 2026-06-07)*

The **last PR10 item** and the highest-stakes change in the workstream (it changes
*who can ban members*). Decision of record: **[ADR-008](../decisions/008-moderator-role-capability-native-authority.md)**
(owner decision Q-0006 → A — capability-native role→tier grant). Scalar/KV,
**no migration**, **behaviour-preserving by default**.

- **Tier grant in the governance resolver** (`governance/resolver.py`):
  `_resolve_member_tier` gains a **moderator-role** grant symmetric to the existing
  trusted-role grant. A member holding the guild's configured
  `moderator_tier_role_id` resolves to the `moderator` tier. Both grants only
  **raise** a tier (never demote a real admin/owner) and **fail toward the lower
  tier** on a config-read error — a configured role can only ever *add* standing.
  Read via the new `config_arbitration.get_moderator_tier_role` (mirrors
  `get_trusted_tier_role`).
- **Behaviour-preserving OR-gate on the surfaces:** the mod cog's eight prefix
  commands (`_require_mod`) and the panel `interaction_check` admit on
  `Discord permission` **OR** the moderation capability (via `ui_permissions`,
  new `can_execute_ctx` for the prefix path). The permission path is unchanged and
  checked first, so no one who can moderate today loses access; denial raises
  `MissingPermissions` so the error UX is preserved. The `/moderation` slash keeps
  its Discord `default_permissions` UI default (documented boundary).
- **Configured via the Settings hub** (owner decision: Settings-hub role setting):
  two role-typed `SettingSpec`s (`moderator_role` / `trusted_role`,
  `input_hint="role"`, schema → **v6**) on the moderation schema, written through the
  audited `SettingsMutationPipeline` and gated by `moderation.settings.configure`
  (administrator floor). This also makes the previously inert trusted role
  configurable.
- **Pinned by** `tests/unit/governance/test_role_tier_grants.py` (grant-via-role,
  no-escalation, no-regression, precedence, cross-guild deny, fail-toward-lower),
  `tests/unit/cogs/test_moderation_role_authority.py` (the cog + panel OR-gate), and
  the `moderator_role` / `trusted_role` shapes + **v6** in `test_moderation_schemas.py`.
  Live-booted (clean start, settings registry 0 findings). ADR + command-map +
  capability-authority + folio docs updated.
- **PR10 is now complete.** Next: **PR11** (setup role/moderation/governance sections).

### PR11 (moderation + roles slices) — Setup sections *(built 2026-06-07)*

Owner decision **Q-0008 → "Moderation + Roles"** (router): build the moderation and roles
setup sections this session; **defer the governance section** (cleanup already owns the main
governance write; capability-override / command-access setup is a separate, design-led
follow-up). Both sections are draft-first — they stage `SetupOperation`s; **Final Review is
the only apply gate** (no setup view imports a mutation pipeline; invariant
`test_setup_operations_invariants.py` preserved).

- **Moderation section** (`views/setup/sections/moderation.py`, order 65) — surfaces PR10's
  config via existing **`set_setting`** drafts (subsystem `moderation`): `dm_on_action`,
  `require_reason`, `warn_escalation_action`, `moderator_role`. Recommended-ops builder
  stages a safe baseline (DM-on-action + require-a-reason). No new op-kind, no migration —
  reuses the `SettingsMutationPipeline` dispatch. The fuller surface stays in
  `!settings → Moderation`.
- **Roles section** (`views/setup/sections/roles.py`, order 55) — time-/XP-based auto-role
  tiers for **existing** roles (no second resource-creation path). Adds a new
  **`set_role_threshold`** op-kind to `services/setup_operations.py`, routed through the new
  audited **`role_automation.set_{time,xp}_threshold`** seam (a service, not a raw DB write,
  per the no-`utils.db` invariant; mirrors the cog-routing no-pipeline pattern) — captures
  `role_id` so a rename does not orphan the tier, and emits `audit.action_recorded`. Final
  Review gains an explicit `role_threshold` apply phase **and a read-only
  `_preflight_set_role_threshold` adapter** — current→proposed tier diff plus a
  "bot can't assign this role" note (missing / above-bot / no Manage Roles) folded into the
  preview, so Final Review is not blind to role feasibility (the actual assignment stays
  separately guarded by `role_automation.check_preflight`).
- **Pinned by** `tests/unit/views/setup/sections/test_moderation_section.py`,
  `test_roles_section.py`, `tests/unit/services/test_setup_operations_role_threshold.py`,
  `test_role_automation_thresholds.py`, and the registration manifest. Full CI mirror green;
  live-booted clean (both sections register, 0 ERROR/CRITICAL).
- **Remaining in PR11 — the governance section (deferred Q-0008; scope set by Q-0011,
  2026-06-07).** When built, it should configure two things, staged as `SetupOperation`s
  through Final Review like every other section (no new resource path): **(1) capability
  overrides** — delegate moderation/admin capability to a role via the per-guild
  `capability_execution_overrides` seam (`governance`); and **(2) command-access policy** —
  which channels the bot responds in (`command_access_service`). Both likely need a new
  op-kind (`set_capability_override` / `set_command_access`) routed through their canonical
  service, mirroring the `set_cog_routing` no-pipeline pattern. Not started — sequence after
  PR12 unless the maintainer pulls it forward.

### PR12 — Setup diagnostics & repair *(built 2026-06-07)*

A reusable, **read-only** diagnostics layer that inspects a guild's
server-management config, classifies what is broken / stale / unsafe /
incomplete, explains each finding, and — for the safe, deterministic
cases — stages typed `SetupOperation` repairs that **Final Review (the
only apply gate)** dispatches through the existing canonical pipelines.
**No new op-kind, no migration, no second mutation system.** Verify merge
status on live GitHub.

- **`services/setup_diagnostics.py` (new, service-owned — *not* a view):**
  `SetupDiagnosticFinding` (frozen: stable `code`, severity, subsystem,
  `section_slug`, resource type/id, summary/detail, repairability,
  `repair_label`, `repair_ops` batch, advisory note, notes) +
  `SetupDiagnosticsReport` (severity-sorted, with `counts` / `repairable`
  / `advisory` / `is_healthy` partitions) + `collect_setup_diagnostics`
  + `staged_repair_ops`. It **composes existing read-only detectors — it
  does not re-detect**: `resource_health.inspect` (bindings), `utils.db.roles`
  + `utils.role_feasibility` (auto-role tiers), `config_arbitration`
  (moderator/trusted roles), `cleanup_diagnostics.collect_cleanup_diagnostics`
  (cleanup). Living in `services/` (not a view) is deliberate — the future
  Server-Management Hub (PR14) renders the same report unchanged.
- **Severities** `blocker` / `warning` / `advisory` / `info`;
  **repairability** `auto_repairable` / `conditionally_repairable` /
  `advisory_only` / `blocked`.
- **The one safe automatic repair this slice ships:** a dead binding
  (`stale_binding` / `wrong_type`) → a single **`clear_binding`** op
  (deterministic, id-free, reversible — re-bind afterwards). Everything
  else is **advisory_only** or **blocked** by design: missing/unbound
  bindings (operator must pick the target — no guess, no auto-create),
  permission/hierarchy blockers (a Discord-side change the bot must not
  make — never auto-reorders roles), stale/unassignable auto-role tiers
  (point to `!roles`; no threshold-clear op-kind exists yet — PR13),
  stale moderator/trusted role (re-pick in the Moderation section), and
  stale/ineffective cleanup rows (the cleanup panel already owns the fix).
- **`views/setup/sections/diagnostics.py` (new section, order 85,
  standard+advanced):** renders the grouped findings (severity-bucketed,
  capped) and a **“Stage safe repairs”** button that drafts the
  auto-repairable ops with `staging_kind="repair"` /
  `section_slug="diagnostics"` provenance, plus **“Re-scan.”** No
  `recommended_ops_builder` — repairs are staged deliberately, never
  swept in by the hub's “Apply all recommended.” Partial-apply rendering
  is inherited free (repairs are ordinary `SetupOperation`s through the
  unchanged Final-Review path).
- **Pinned by** `tests/unit/services/test_setup_diagnostics.py`
  (classification, repair generation, composition, fail-safe collectors),
  `tests/unit/views/setup/sections/test_diagnostics_section.py` (staging
  only auto-repairable, never applies, DM-reject, re-scan),
  `tests/unit/invariants/test_setup_diagnostics_readonly.py` (no mutation
  pipeline import/call, no `setup_draft` import — generation ≠ staging),
  and the registration manifest. Full CI mirror green (7949 passed).
- **Deferred (documented, not snuck in):** a `clear_role_threshold` op-kind
  + conditional binding-repair (pick-a-target) → PR13/follow-up; governance
  diagnostics → the deferred governance setup section (Q-0008/Q-0011).

### PR13 (deterministic slice) — Role templates *(built 2026-06-08)*

The deterministic foundation of "optional role templates" (roadmap §"Optional
deterministic role templates"): built-in, **opt-in** role bundles the setup
wizard previews against the guild and stages as role-creation ops. The **AI
generation layer is deferred to a PR13 follow-up** (high-sensitivity, not
live-testable without provider keys; the roadmap sequences deterministic
first). **No second resource path** — creation routes through the audited
`RoleLifecycleService`. Verify merge status on live GitHub.

- **`services/setup_role_templates.py` (new, pure — *not* `governance.role_templates`):**
  `RoleSuggestion` (name / purpose / colour / hoist / mentionable / optional
  `time_days` / `xp_level` — **structurally no permissions field**) +
  `RoleTemplate` (slug / display_name / category / suggestions) + 6 built-in
  templates (community hierarchy, moderation team, gaming/event, time-/XP-
  progression, support server) + `validate_template` / `validate_suggestion`
  (bounds, duplicate names, fail-safe colour parse) + a **pure** `plan_template`
  (partitions create-vs-already-exists against the guild's roles; no I/O). Lives
  in `services/` so the future hub (PR14) reuses it; distinct from the
  permission-tier `governance.role_templates` (documented in its docstring).
- **New `create_managed_role` op-kind** (`services/setup_operations.py`) routes
  through **`RoleLifecycleService.apply(operation="create")`** — the audited
  manual-role owner, *not* `ResourceProvisioningPipeline` (which owns
  subsystem-bound create-or-reuse; a template role is an unbound operator
  label). The new role's id is threaded into the audited
  `role_automation.set_{time,xp}_threshold` seam as a **best-effort tier
  companion** (a failed tier never undoes the created role). Read-only preflight
  adapter (ABSENT→proposed + a Manage-Roles note) + `_label` arm. No direct
  `guild.create_role` in `setup_operations` (the `test_setup_operations_invariants`
  AST pin holds).
- **`views/setup/sections/role_templates.py` (new section, order 56,
  standard+advanced):** pick a template → preview (✅ exists / ➕ create) →
  **"Stage new roles"** drafts one `create_managed_role` op per missing role.
  `recommended_ops_builder=None` (creating roles is deliberate, never swept into
  "apply all recommended"). **Final Review is the only apply gate** (no mutation
  pipeline import).
- **Root-cause fixes found while building (the setup-draft op-kind gap):**
  1. **PR11 regression — `set_role_threshold` could never be staged.** It was
     wired into the dispatcher + `services.setup_draft` risk map but **never**
     into `utils.db.setup_draft._KNOWN_OP_KINDS` nor the migration-035 CHECK, so
     the shipped roles section raised `ValueError` at the DB gate (the staging
     path was unit-mocked, so CI stayed green). **Migration 059** widens the
     CHECK and the Python gate adds both kinds.
  2. **Threshold slot-collision.** The draft replace-on-conflict key is
     `(op_kind, subsystem, setting_name, binding_name)` (no `target_id`), so two
     roles' time tiers collided on `(set_role_threshold, roles, "time", '')` and
     the second silently overwrote the first. `roles.py` now sets
     `binding_name="tier:{role_id}"`; `role_templates` uses
     `binding_name="role:{name}"` — per-row slot discriminators.
  3. **Drift guard.** `tests/unit/db/test_setup_draft_op_kind_parity.py` now pins
     the dispatcher `_KNOWN_KINDS`, the DB `_KNOWN_OP_KINDS`, and the
     migration-059 CHECK to **one set** — the missing dispatcher↔gate check that
     would have caught the PR11 gap.
- **Pinned by** `tests/unit/services/test_setup_role_templates.py`,
  `test_setup_operations_create_managed_role.py`,
  `tests/unit/views/setup/sections/test_role_templates_section.py`, the parity
  guard, and a roles-section regression case. Full CI mirror green (8009 passed);
  **live-booted clean** (migration 059 applied, SetupCog/section register, DB
  CHECK verified to accept both kinds, 0 ERROR/CRITICAL).
- **Deferred to the PR13 AI follow-up:** "Generate with AI" — request modal →
  AI gateway → strict structured suggestion → the same `validate_*` /
  safety-filter → preview/accept/reject/edit → the same `create_managed_role`
  staging path. The deterministic `setup_role_templates` validation is the
  safety filter it will reuse.

### PR14 — Server Management Hub *(built 2026-06-08)*

The capstone: one **navigation** surface — a persistent `!servermanagement`
(+ aliases `!servermenu` / `!guildmenu`) and an ephemeral `/server-management` —
composing the specialised managers (moderation, channels, roles, cleanup, setup)
behind read-only health badges. The hub holds **no domain logic, no new
mutation / op-kind / migration, and no settings** — every action routes into an
existing manager's panel. Verify merge status on live GitHub.

- **`services/server_management_hub.py` (new, read-only, fail-safe):**
  `collect_hub_status(guild) -> HubStatus` composes per-manager badges
  (🟢/🟡/⛔/❓) from the existing detectors (`utils.moderation_feasibility`,
  `utils.role_feasibility`, the Manage-Channels perm) plus a cross-cutting
  config-health line from the already-fail-safe `setup_diagnostics` report and a
  completeness % from `setup_readiness`. In `services/` so the future web
  companion (Q-0002) reuses it; **never raises** (a broken detector → ❓ badge).
- **`views/server_management/hub.py` (new):** `ServerManagementHubView`
  (`PersistentView`, `@register`, `SUBSYSTEM="servermanagement"`) — one button per
  manager + Refresh. Routes via
  `interaction.client.get_cog(...).build_help_menu_view(interaction)` (the proven
  Games-hub pattern) with a Back-to-hub button, so the view carries **no
  module-level `cogs` import** (Setup delegates to `open_wizard_from_slash` via a
  lazy import). **Authority is an administrator floor** re-checked on every
  interaction (mirrors `ModPanelView`, ADR-005) — not anchor ownership, so the same
  view backs both the anchored prefix panel and the anchorless ephemeral slash.
  Restoration is automatic (no-arg constructor + static `servermanagement:*`
  custom_ids + `restore_anchors`).
- **`cogs/server_management_cog.py` (new thin cog):** `!servermanagement` (anchored
  via `panel_manager.get_or_render_panel`) + `/server-management` (ephemeral) + a
  `build_help_menu_view` help-dropdown hook. Added to `INITIAL_EXTENSIONS`.
- **Registered first-class (owner decision Q-0016, 2026-06-08):** `servermanagement`
  is a real `SUBSYSTEMS` + `HUBS` entry (administrator tier) + a `KNOWN_PANEL_COMMANDS`
  entry — like every other hub — so it is help-discoverable and the
  identity-contract / orphan-cog / db-anchor diagnostics stay clean. (The
  alternative — a standalone persistent view with no subsystem — left an
  `auto_healable` identity finding the platform self-heal would unregister.) The
  registry **key is `servermanagement`** (no underscore) to match
  `cog_name_to_subsystem`; module paths stay readable (`server_management`).
- **Pinned by** `tests/unit/services/test_server_management_hub.py` +
  `tests/unit/views/test_server_management_hub_view.py` (registration, admin-floor
  `interaction_check`, manager routing + Back-button, missing-cog / hook-failure,
  Setup delegation, Refresh, no module-level cogs import, first-class subsystem),
  plus updated hub / help / discoverability enumerations. Full CI mirror green
  (8062 passed); arch strict 0 errors; **live-booted clean** (cog loads, view
  registered under `servermanagement`, `Identity-contract: clean … STRICT=on`,
  0 ERROR/CRITICAL). **Restart-restoration live-check + a real operator
  click-through remain for the maintainer's bot.**
- **Server-management: the PR14 capstone is built. The only remaining queued item
  is the PR13 AI generation follow-up** (gated/sensitive — see the PR13 subsection).

---

## Remaining queue (starts at PR11)

Per the implementation plan's dependency order. PR7–PR9 shipped (see above).

| PR | Objective | Depends on |
|---|---|---|
| **PR10** | Moderation first-class configuration. **COMPLETE** — all six slices shipped (DMs, ban message-purge, timeout ceiling, require-reason, bot-readiness diagnostics, configurable warn escalation, post-action message cleanup, optional public log, **and moderator/trusted roles + capabilities** — ADR-008, see above). | #521 |
| **PR11** | Setup role/moderation/governance sections. **Moderation + Roles sections built in the moderation + roles slices (2026-06-07); Governance section deferred (Q-0008).** | PR5, PR8–PR10, #522 |
| **PR12** | Setup diagnostics & repair. **Built 2026-06-07** (read-only `setup_diagnostics` service + Diagnose & repair section; `clear_binding` the one safe auto-repair, everything else advisory/blocked — see subsection above). | PR5, #522 |
| **PR13** | Deterministic + AI role templates. **Deterministic slice built 2026-06-08** (built-in templates + `create_managed_role` op + setup section; see subsection above). **AI generation layer is the remaining PR13 follow-up.** | PR5, #523 |
| **PR14** | Server Management Hub (last). **Built 2026-06-08** (persistent `!servermanagement` + `/server-management` composing the managers behind read-only badges; registered first-class `servermanagement` subsystem + hub — owner decision Q-0016 — see subsection above). | all managers |

Near-term completion items folded into the above: finish PR2's diagnostics/findings
model and selector paging/search (in PR6 as the first production consumer); finish
PR4's clone / overwrites / creation routing (in PR7).
