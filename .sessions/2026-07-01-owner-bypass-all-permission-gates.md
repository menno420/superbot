# 2026-07-01 — Owner bypasses ALL permission gates (not just administrator)

> **Status:** `in-progress`

**Run type:** owner-directed (bug report — screenshot; explicit "do everything as owner")

## What I'm about to do

Owner screenshot (July 1): `/help → Roles → Role Menus → New Menu/Edit` replies **"You need the
Manage Roles permission to do that."** Directive: *"make sure that I can do everything with this bot as
owner."*

**Gap:** #1573/#1577 made the owner bypass the **`administrator`** gate everywhere. But many surfaces gate
on a **specific** permission — `manage_roles` (role menus / role creation), `manage_guild`,
`manage_channels`, `manage_messages`, `moderate_members`, `create_instant_invite` — and those still deny
the owner. Gates come in several shapes (I keep missing one): `@commands.has_permissions(X=True)`,
`@app_commands.checks.has_permissions(X=True)`, bare `@has_permissions(X=True)`, single-line
`if user.guild_permissions.X`, and **split-line** `perms = getattr(user, "guild_permissions", None)` then
`perms.X` (e.g. `views/roles/role_menu_builder.py`).

**Plan — generalize + guard-driven completeness:**
1. Generalize `core/runtime/permission_checks.py` to *any* permission:
   `member_has_perms_or_owner(user, **perms)`, `perms_or_owner(**perms)` (prefix),
   `app_perms_or_owner(**perms)` (slash). `admin_or_owner`/`app_admin_or_owner` become thin wrappers so
   #1577's call sites are unchanged.
2. **A guard that enumerates EVERY raw permission gate** (any `has_permissions(...)` decorator in cogs +
   any interacting-user `guild_permissions.<perm>` read outside the canonical helpers). Run it → it lists
   the full offender set → fix until empty. The guard is the completeness proof (no more missed shapes).
3. Sweep decorators (script) → `perms_or_owner` / `app_perms_or_owner`; sweep inline gates → route through
   `member_has_perms_or_owner` (or add owner-bypass to the `_admin`/`_can_manage`-style helpers).
4. Leave the bot's OWN capability checks (`me.guild_permissions` / `guild.me`) — those gate what the *bot*
   can do, not the user.
5. Tests for the generalized helpers + the new gates; full mirror; flip card to complete.
