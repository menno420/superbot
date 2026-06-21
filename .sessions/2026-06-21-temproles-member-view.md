# 2026-06-21 — `!temproles` member-facing temp-role listing

> **Status:** `in-progress` — building the flagged loose-end from the reaction-roles
> PR 3–5 session: a member-facing view consuming the orphaned
> `role_grants.list_for_member`. Additive runtime (a new read-only command + a
> read seam on the existing audited service); existing behaviour unchanged.

> **Run type:** `routine · dispatch`

## Plan (about to do)

The reaction-roles overhaul shipped free temp roles (#1227) with `grant`/`sweep`,
but `role_grants.list_for_member` was left with no UI consumer (flagged loose end).
This session adds:

1. `role_grants_service.list_active_grants(guild, member_id)` — a pure read seam
   that resolves roles, drops vanished roles + already-lapsed-but-unswept grants.
2. `!temproles [@member]` on `RoleGrantsCog` — lists the caller's own active temp
   roles (role + relative expiry); an optional `@member` is staff-only (manage_roles).
3. Tests for the service read + the command.

CI mirror green + arch strict before flip-to-complete.
