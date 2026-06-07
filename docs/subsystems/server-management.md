# Server management subsystem — folio

> **Status:** `living-ledger` (area index). Source + the status tracker win.
> **Last updated:** 2026-06-06.

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
- **"Should I add a manager/panel?"** → check the tracker's Remaining queue first;
  reuse selectors + provisioning previews; never add a second resource-creation path.

## Rules & approved structures (binding — link, don't restate)

- `docs/planning/server-management-status-2026-06-05.md` is authoritative for
  shipped/queued status. Its body supersedes old PR ordering in the roadmap.
- The roadmap defines target architecture and settled decisions; the implementation
  plan defines dependency/scoping detail. Neither overrides source or the tracker.
- Manual lifecycle mutations route through domain services and audit paths. Resource
  creation must preserve `docs/resource-provisioning-overview.md` and the
  no-silent-auto-create invariant. Authority checks follow
  `docs/capability-authority.md`.
- Role/channel choices should be dynamic selectors with stable IDs where persisted;
  avoid free-text resource names and stale static option lists.

## Current state

- Shipped foundations include moderation service convergence, shared role feasibility
  + multi-role selection, audited channel rename/move/delete/reorder lifecycle,
  audited role create/edit/delete lifecycle, selector-driven ID-first time/XP
  role thresholds, and **config-backed moderation** (PR10 first–third slices —
  DM-on-action, ban message-purge, timeout ceiling, require-reason, and configurable
  warn escalation (`warn_escalation_action`), all applied at the
  `services/moderation_service` mutation seam via `services/moderation_config.py`, plus
  a read-only bot-readiness panel line from `utils/moderation_feasibility.py`).
- Channel creation remains owned by resource provisioning; clone, overwrites, and
  some category/lifecycle follow-ups remain outside the shipped lifecycle service.
- Cleanup and setup exist today, but the tracker queues their server-management
  convergence/expansion rather than treating the old roadmap sequence as shipped.
- Known UX follow-ups: moderation member quicksearch via `discord.ui.UserSelect`
  (`unban` remains ID-based); bulk **Clear missing** on time/XP panels; selector-ize
  Edit Role.

## Plans / pending approval

The status tracker's remaining queue is the only current sequencing authority.
Cleanup versioning + builder/dry-run/panel diagnostics shipped 2026-06-06 (PR8+PR9,
presets-only). **PR10 (moderation configuration) is underway**: its first slice
(config-backed behaviour — DM-on-action, ban message-purge, timeout ceiling), second
slice (require-reason enforcement + bot-readiness diagnostics), and third slice
(configurable warn escalation — `warn_escalation_action`, owned at the warn seam) have
shipped; the **remaining PR10 items** (moderator/trusted roles + capabilities,
dedicated log destinations, post-action cleanup hook) come next, then setup
role/moderation/governance and repair sections, role templates, and finally the
unified Server Management Hub. Link to the tracker for exact order and dependencies
rather than copying them here.

## Ideas (not approved)

Arbitrary channel before/after positioning, revert-safe-changes UX, first-class
category management, and broader role/template UX remain follow-ups, not permission
to bypass lifecycle/provisioning services.

**Owner intent (2026-06-07, `docs/owner/maintainer-question-router.md` Q-0002):** the
owner-facing control center stays **Discord-first** — keep services / read-models
reusable so a web companion is *possible* later, but do not start web work now.

## Next candidates

1. Continue PR10: its first–third slices shipped; the next step is the **remaining
   PR10 items** (mod-roles + capabilities, dedicated log destinations, post-action
   cleanup hook). Verify source before using either older planning document.
2. Take one bounded known UX follow-up (member quicksearch or role selector/cleanup)
   without changing lifecycle ownership.
3. When extending setup, reuse provisioning previews/confirmation and capability
   checks instead of introducing a second resource-creation path.

## Related docs

`docs/planning/server-management-status-2026-06-05.md`,
`docs/planning/server-management-roadmap-2026-06-05.md`,
`docs/planning/server-management-implementation-plan-2026-06-05.md`,
`docs/resource-provisioning-overview.md`, `docs/capability-authority.md`,
`docs/server-logging.md`.
