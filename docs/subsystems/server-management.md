# Server management subsystem — folio

> **Status:** `living-ledger` (area index). Source + the status tracker win.
> **Last updated:** 2026-06-08.

## What & where

Server management covers operator-facing moderation, channel and role lifecycle,
cleanup policy, setup, and the future unified hub. Inspect first:
`disbot/cogs/channel_cog.py`, `disbot/views/channels/`,
`disbot/services/channel_lifecycle_service.py`, `disbot/cogs/role_cog.py`,
`disbot/views/roles/`, `disbot/services/role_lifecycle_service.py`,
`disbot/cogs/moderation_cog.py`, `disbot/views/moderation/`,
`disbot/services/moderation_service.py`, `disbot/cogs/cleanup_cog.py`,
`disbot/services/cleanup_profiles.py`, `disbot/cogs/setup_cog.py`, and
`disbot/views/setup/`.

## Debug router (if X, inspect Y first)

- **Commands aren't deleted / wrong delete timing** → it's cleanup *resolution*,
  not the cog. Order: `governance/cleanup.py::resolve_cleanup_policy` →
  `_build_scope_chain` (walks **channel → category → guild → default**; threads
  inherit — RC-5, no thread scope) → `cleanup_policies` rows. **Gotcha:** a
  guild-default row must be keyed by `scope_id=guild_id`
  (`services/cleanup_levels.cleanup_scope_id`) — a row at `scope_id=0` is silently
  never read. `!cleanup` → **Cleanup Policies** (`services/cleanup_diagnostics.py`)
  flags stale/ineffective rows. Pins: `tests/unit/governance/test_cleanup_scope.py`,
  `test_cleanup_resolution_behavior.py`.
- **A mutation didn't audit / emit an event** → it must route through
  `governance/writes.py::GovernanceMutationPipeline` (DB + `governance_audit_log` +
  `EVT_*` + cache invalidation in one txn). A cog/view writing the DB directly is the
  bug — see `docs/ownership.md` "Direct DB writes — blocklist".
- **Channel rename/move/delete/reorder misbehaves** →
  `services/channel_lifecycle_service.py` (owns all four; emits
  `channel.lifecycle_changed`). Channel *creation* is resource provisioning — a
  different owner.
- **Role create/edit/delete or time/XP threshold automation** →
  `services/role_lifecycle_service.py` + feasibility checks; thresholds are ID-first
  selectors persisted per guild.
- **Auto-mod deletion missing from the audit log** → it must go through
  `moderation_service.auto_delete` (writes `mod_logs` + `EVT_MOD_ACTION`); a raw
  `message.delete()` in a cog is the gap.
- **"What's broken / stale / unsafe in a guild's config?" (diagnostics)** → the read-only
  detectors already emit a **reusable findings model — compose them, don't re-detect**:
  `services/resource_health.py::inspect` (per-binding stale/missing/wrong-type/permission/
  hierarchy verdicts), `services/cleanup_diagnostics.py` (stale/ineffective cleanup rows),
  `utils/role_feasibility.py` + `utils/db/roles.py` (auto-role tier staleness/feasibility),
  `core/runtime/config_arbitration.py` (moderator/trusted role config). **`services/setup_diagnostics.py`
  (PR12)** is the canonical composer: it maps those verdicts into typed
  `SetupDiagnosticFinding`s + safe `clear_binding` repair ops for Final Review, and is the
  layer the future Server-Management Hub (PR14) should reuse. Note the *axis*:
  `setup_blockers.py` / `setup_readiness.py` answer "is the bot's substrate built?" — a
  different question from per-guild config health.
- **A new setup op-kind won't stage / silently overwrites another row** → the
  setup-draft op-kind is a **three-place contract**: add it to (1) the dispatcher
  `services/setup_operations.py::_KNOWN_KINDS` + a dispatch arm, (2) the DB gate
  `utils/db/setup_draft.py::_KNOWN_OP_KINDS`, **and** (3) a migration that widens the
  `setup_draft_operations.op_kind` CHECK. Miss (2)/(3) and staging raises `ValueError`
  / a CHECK violation at runtime even though the dispatcher accepts it (this is the bug
  PR11's `set_role_threshold` hit; migration 059 + the
  `test_setup_draft_op_kind_parity.py` drift guard close it). **Slot key gotcha:** the
  draft replace-on-conflict index is `(op_kind, subsystem, setting_name, binding_name)`
  — it does **not** include `target_id`, so per-target ops (one row per role/channel)
  must encode the target into `setting_name`/`binding_name` or they collide and the last
  write wins.
- **"Should I add a manager/panel?"** → check the tracker's Remaining queue first;
  reuse selectors + provisioning previews; never add a second resource-creation path.
- **"Adding a new operator *hub*?"** → an operator hub is a **first-class subsystem** (owner
  decision Q-0016; every existing hub is one — admin/moderation/settings/games/…). Wire **all**
  of: (1) a `SUBSYSTEMS` entry + (2) a `HUBS` entry (administrator tier) + (3) a
  `KNOWN_PANEL_COMMANDS` entry, (4) a `build_help_menu_view` hook on the cog, (5)
  help-surface-map §1+§2 rows, (6) a command-map `### <subsystem>` section, and (7) the hub-set
  / help-category / discoverability **enumeration tests**. **Gotcha:** the registry **key must
  equal `cog_name_to_subsystem(YourCog)`** — it strips `Cog` + lowercases with **no** underscore
  (so `ServerManagementCog` ⇒ `servermanagement`), and that same string must be the view's
  `SUBSYSTEM` classvar **and** the `panel_manager.get_or_render_panel` anchor string, or the
  identity-contract (view), command-surface-ledger (orphan-cog), and db-anchor findings all fire.
  A registered `PersistentView` whose `SUBSYSTEM` is not in `SUBSYSTEMS` is an `auto_healable`
  orphan the platform self-heal would unregister. Working exemplar:
  `views/server_management/hub.py` + `cogs/server_management_cog.py` (PR14).

## Rules & approved structures (binding — link, don't restate)

- `docs/planning/server-management-status-2026-06-05.md` is authoritative for
  shipped/queued status. Its body supersedes old PR ordering in the roadmap.
- The roadmap defines target architecture and settled decisions; the implementation
  plan defines dependency/scoping detail. Neither overrides source or the tracker.
- Manual lifecycle mutations route through domain services and audit paths. Resource
  creation must preserve `docs/setup-platform/resource-provisioning-overview.md` and the
  no-silent-auto-create invariant. Authority checks follow
  `docs/capability-authority.md`.
- Role/channel choices should be dynamic selectors with stable IDs where persisted;
  avoid free-text resource names and stale static option lists.

## Current state

- Shipped foundations include moderation service convergence, shared role feasibility
  + multi-role selection, audited channel rename/move/delete/reorder lifecycle,
  audited role create/edit/delete lifecycle, selector-driven ID-first time/XP
  role thresholds, and **config-backed moderation** (PR10 first–fifth slices —
  DM-on-action, ban message-purge, timeout ceiling, require-reason, configurable
  warn escalation (`warn_escalation_action`), an optional post-kick/ban message
  sweep (`post_action_cleanup`, default OFF, *requested* from
  `services/history_cleanup.py`), and an optional **public moderation log**
  (`public_log_actions` / `public_log_channel`, default OFF, moderator-redacted,
  delivered by `services/server_logging.py`), all applied at / consumed from the
  `services/moderation_service` seam via `services/moderation_config.py`, plus a
  read-only bot-readiness panel line from `utils/moderation_feasibility.py`), and
  **capability-native moderator/trusted roles** (PR10 final slice, ADR-008: a configured
  `moderator_role` grants the `moderator` tier via `governance/resolver.py`, OR-gated on
  the cog + panel to preserve Discord-perm holders; both roles settable in the Settings
  hub at the administrator floor).
- Channel creation remains owned by resource provisioning; clone, overwrites, and
  some category/lifecycle follow-ups remain outside the shipped lifecycle service.
- Cleanup and setup exist today; setup convergence has begun — the setup wizard now has
  **moderation** and **roles** sections (PR11 moderation + roles slices, 2026-06-07) that
  stage `set_setting` / `set_role_threshold` drafts through the Final-Review apply gate, plus
  a **Diagnose & repair** section (PR12, 2026-06-07) backed by the read-only
  `services/setup_diagnostics.py` layer — it composes the existing detectors
  (`resource_health`, `role_feasibility`, `config_arbitration`, `cleanup_diagnostics`) into
  typed findings and stages the one safe auto-repair (`clear_binding` for a dead binding) as
  a `SetupOperation`; every other finding is advisory/blocked. The diagnostics model lives in
  `services/` so the future hub reuses it. **Deterministic role templates shipped 2026-06-08**
  (PR13 deterministic slice): `services/setup_role_templates.py` (built-in, permission-free
  role bundles + pure `plan_template`) + a new audited **`create_managed_role`** op-kind
  (routes through `RoleLifecycleService`, optional time/XP tier companion) + a **Role
  templates** setup section. That work also fixed a latent PR11 regression (the roles section's
  `set_role_threshold` op was never added to the DB op-kind gate/CHECK, so it couldn't stage —
  migration 059 + a drift-guard test close it). **The unified Server Management Hub (PR14) was
  built 2026-06-08** — a persistent `!servermanagement` + ephemeral `/server-management`
  composing the managers behind read-only health badges, registered **first-class** as the
  `servermanagement` subsystem + hub (owner decision Q-0016) via
  `services/server_management_hub.py` + `views/server_management/hub.py` +
  `cogs/server_management_cog.py`. The tracker's only remaining server-management item is the
  **gated PR13 AI template layer**.
- Known UX follow-ups: moderation member quicksearch via `discord.ui.UserSelect`
  (`unban` remains ID-based); bulk **Clear missing** on time/XP panels; selector-ize
  Edit Role.

## Plans / pending approval

The status tracker's remaining queue is the only current sequencing authority.
Cleanup versioning + builder/dry-run/panel diagnostics shipped 2026-06-06 (PR8+PR9,
presets-only). **PR10 (moderation configuration) is COMPLETE**: all six slices shipped —
config-backed behaviour (DM-on-action, ban message-purge, timeout ceiling),
require-reason + bot-readiness diagnostics, configurable warn escalation
(`warn_escalation_action`), post-action message cleanup (`post_action_cleanup`,
requested from the cleanup subsystem), the optional public moderation log
(`public_log_actions` / `public_log_channel`, moderator-redacted, delivered by
`server_logging`), and **moderator/trusted roles + capabilities** (ADR-008,
capability-native: a configured role resolves to the `moderator` tier via the governance
tier resolver). **PR11's moderation + roles setup sections are built** (2026-06-07, owner
decision Q-0008; governance section deferred). **PR12 (setup diagnostics & repair) was
built 2026-06-07** (read-only `setup_diagnostics` service + a Diagnose & repair section;
`clear_binding` is the one safe auto-repair, everything else advisory/blocked). **PR13's
deterministic role-templates slice shipped 2026-06-08, and PR14 (the unified Server Management
Hub) was built 2026-06-08** (registered first-class as the `servermanagement` subsystem + hub,
owner decision Q-0016). The only remaining item is the gated PR13 AI generation layer. Link to
the tracker for exact order and dependencies rather than copying them here.

## Ideas (not approved)

Arbitrary channel before/after positioning, revert-safe-changes UX, first-class
category management, and broader role/template UX remain follow-ups, not permission
to bypass lifecycle/provisioning services.

**Owner intent (2026-06-07, `docs/owner/maintainer-question-router.md` Q-0002):** the
owner-facing control center stays **Discord-first** — keep services / read-models
reusable so a web companion is *possible* later, but do not start web work now.

## Next candidates

1. **PR10 is complete** (all six slices, ending with moderator/trusted **roles +
   capabilities** — ADR-008). **PR11's moderation + roles setup sections are built**
   (2026-06-07, owner decision Q-0008): the moderation section stages `set_setting` drafts
   for the PR10 knobs; the roles section adds a `set_role_threshold` op-kind (routed through
   the audited `role_automation.set_{time,xp}_threshold` seam) for time/XP auto-role tiers.
   PR11's **governance** section is **deferred** (cleanup already owns the main governance
   write). **PR12 (setup diagnostics & repair) shipped 2026-06-07** — the read-only
   `setup_diagnostics` service + Diagnose & repair section (reuses `resource_health` /
   `role_feasibility` / `cleanup_diagnostics`; `clear_binding` the lone safe auto-repair,
   staged through Final Review). **PR13's deterministic role-templates slice shipped 2026-06-08**
   (`setup_role_templates` + `create_managed_role` + Role-templates section), and **PR14 (the
   unified Server Management Hub) was built 2026-06-08** (first-class `servermanagement`
   subsystem + hub, Q-0016 — composes the managers behind read-only badges, no new mutation
   path). The lane's only remaining item is the **gated PR13 AI generation follow-up**. Reuse
   provisioning previews/confirmation + capability checks; never add a second resource-creation
   path.
2. Take one bounded known UX follow-up (member quicksearch or role selector/cleanup)
   without changing lifecycle ownership.
3. When extending setup, reuse provisioning previews/confirmation and capability
   checks instead of introducing a second resource-creation path.

## Related docs

`docs/planning/server-management-status-2026-06-05.md`,
`docs/planning/server-management-roadmap-2026-06-05.md`,
`docs/planning/server-management-implementation-plan-2026-06-05.md`,
`docs/planning/server-management-pr14-hub-plan.md` (PR14 hub plan),
`docs/setup-platform/resource-provisioning-overview.md`, `docs/capability-authority.md`,
`docs/server-logging.md`.
