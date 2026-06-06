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
  audited role create/edit/delete lifecycle, and selector-driven ID-first time/XP
  role thresholds.
- Channel creation remains owned by resource provisioning; clone, overwrites, and
  some category/lifecycle follow-ups remain outside the shipped lifecycle service.
- Cleanup and setup exist today, but the tracker queues their server-management
  convergence/expansion rather than treating the old roadmap sequence as shipped.
- Known UX follow-ups: moderation member quicksearch via `discord.ui.UserSelect`
  (`unban` remains ID-based); bulk **Clear missing** on time/XP panels; selector-ize
  Edit Role.

## Plans / pending approval

The status tracker's remaining queue is the only current sequencing authority:
cleanup policy schema/versioning, cleanup builder/dry-run/diagnostics, moderation
configuration, setup role/moderation/governance and repair sections, role templates,
and finally the unified Server Management Hub. Link to the tracker for exact order
and dependencies rather than copying them here.

## Ideas (not approved)

Arbitrary channel before/after positioning, revert-safe-changes UX, first-class
category management, and broader role/template UX remain follow-ups, not permission
to bypass lifecycle/provisioning services.

## Next candidates

1. Start with the status tracker's first remaining item; verify source before using
   either older planning document.
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
