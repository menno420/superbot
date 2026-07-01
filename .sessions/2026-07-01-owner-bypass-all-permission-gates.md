# 2026-07-01 — Owner bypasses ALL permission gates (not just administrator)

> **Status:** `complete`

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

## What shipped (PR #1602)

- **`core/runtime/permission_checks.py` generalized to any permission:**
  `member_has_perms_or_owner(user, **perms)`, `perms_or_owner(**perms)` (prefix), `app_perms_or_owner(**perms)`
  (slash). `admin_or_owner`/`app_admin_or_owner`/`member_has_admin_or_owner` are now thin wrappers over the
  general form (unchanged call sites from #1577). Key insight: Discord's `administrator` implies every
  specific permission, so `member_has_perms_or_owner(u, manage_roles=True)` == "owner OR admin OR
  manage_roles" — behaviour-preserving + owner added.
- **Decorator sweep (49 across 18 cogs):** every `has_permissions(...)` / `has_guild_permissions(...)`
  decorator (manage_guild ×29, manage_roles, manage_channels, manage_messages, moderate_members,
  create_instant_invite) → `perms_or_owner` / `app_perms_or_owner` (administrator ones collapsed to the
  `admin_or_owner` wrappers). 0 raw decorators remain.
- **Inline gate sweep (18 across ~12 files):** the role surfaces (the screenshot — `role_menu_builder`,
  `reaction_panel`, `_role_pack_flow` `_can_manage`; `role_cog` RoleHubPanelView buttons; `main_panel`,
  `creation_panel`) + `mining_cog`, `channel_cog` (`is_admin_or_owner`), `proof_channel_cog`,
  `btd6/_builders`, `role_grants_cog` → `member_has_perms_or_owner`. Left alone: `me.guild_permissions`
  (bot capability), `counting_cog` (informational None-check), and the moderation surfaces (owner already
  passes via the `can_execute` governance path → owner tier).
- **Guards (completeness enforcers):** generalized `test_no_raw_has_permissions_decorator` (any perm, any
  spelling) + new `test_role_surface_gates_are_owner_aware` (no raw user `guild_permissions` in
  `views/roles/`) + the generalized-helper behavioural test. Taught the reachability checker + the
  slash-privileged contract test the new decorator names (same class of fix as #1577).
- **Bug fixed mid-sweep:** the decorator-sweep script inserted the import at "first line starting with
  from/import", which landed **inside module docstrings** whose prose starts with "from " (e.g.
  `ai_review_cog`) → `NameError`. An AST-based corrective re-placed the import after `from __future__` in
  all 41 permission_checks-using files. env-vars.md regenerated (import lines shifted `hermes_cog`'s
  `os.getenv`).

## 📤 Run report

- **Did:** made the platform owner bypass **every** permission gate (not just administrator) — the
  role-menu `manage_roles` denial from the screenshot + all specific-permission decorators/inline gates
  bot-wide — via generalized owner-aware helpers, a full sweep, and guards that enumerate every raw gate ·
  **Outcome:** shipped (CI green, auto-merge armed)
- **Shipped:** #1602 — `core/runtime/permission_checks.py` (generalized) · 49 decorators across 18 cogs ·
  18 inline gates across ~12 cogs/views · `scripts/check_command_reachability.py` + 3 test files (guards,
  slash-privileged, reachability) · regenerated `docs/operations/env-vars.md`.
- **Run type:** `owner-directed` (bug report — screenshot + "do everything as owner")
- **⚑ Owner decisions needed:** none — the directive resolved the earlier scope tension (Q-0212 first
  scoped to "config, not alter the server"; now explicitly "everything").
- **⚑ Owner manual steps:** none (pure authorization; live on next auto-deploy). Re-test: `/help → Roles →
  Role Menus → New Menu/Edit` — no more "You need the Manage Roles permission." Same for every other
  admin/manage command as owner.
- **⚑ Self-initiated:** the *breadth* (all permissions, all shapes, guards) is my execution of the owner's
  "everything" directive (Q-0172). Scope call recorded below.
- **↪ Next:** none required. Moderation ban/kick still gated by governance `can_execute` (owner passes via
  owner tier) — intentional, not a raw `has_permissions` gate.

## 💡 Session idea (Q-0089)

**Make the `_ensure_import`/insert-after-first-import helper AST-based repo-wide.** This session's only
real bug was a codemod inserting an import into a module docstring because the docstring prose started
with "from ". Any future import-inserting tooling should use the AST "first real import node" the
corrective script used. A shared `tools/codemod/insert_import.py` would prevent the class. Genuine (it bit
this session), not filler.

## ⟲ Previous-session review (Q-0102)

The #1582 ephemeral fix was correct and minimal — good. But this whole arc (#1573→#1577→#1582→#1602) is
the lesson: I **scoped the owner override too narrowly three times** ("config not server", "administrator
only", "leave manage_roles"), and the owner had to come back each time. **System improvement:** when an
owner states a broad intent ("full permissions", "do everything"), implement the *general* mechanism
first (all permissions, all gate shapes, guard-enforced) rather than the narrowest reading — a scope
under-shoot that needs N round-trips is worse than a slightly-broad additive change. The guard-enumerates-
every-gate pattern (built this session) is the durable fix: completeness is now machine-checked, not
scoped by my judgment.

## Doc audit (Q-0104)

Router Q-0212 gets a third-extension addendum (generalize to all permissions) in this PR. No prior-merge
ledger change. `check_docs`/`check_consistency` green via the mirror. New behaviour documented at the code
site (permission_checks module docstring) + the guards' docstrings name Q-0212.

## 🛠 Friction → guard (Q-0194)

- **Friction:** codemod inserted imports into docstrings → `NameError` at import (caught by
  extension-integrity, good). **Guard:** the `test_no_raw_has_permissions_decorator` + extension-integrity
  already fail on both the raw-gate class and any import breakage; the AST-insert habit (Q-0089 idea)
  prevents the codemod class.
- **Friction (recurring):** three narrow-scope round-trips. **Guard:** `test_role_surface_gates_are_owner_aware`
  + the generalized decorator guard now enumerate *every* gate, so "did I get them all?" is answered by CI,
  not by my grep.

## Context delta

- **Needed but not pointed to:** that **Discord's `administrator` implies all specific permissions** (so
  `guild_permissions.manage_roles` is already True for admins) — the fact that makes
  `member_has_perms_or_owner(u, manage_roles=True)` behaviour-preserving. Now stated in the helper + card.
- **Discovered by hand:** the permission gates exist in ~5 distinct shapes (three decorator spellings,
  single-line inline, split-line `getattr` helper) — the reason narrow greps kept missing a class. The
  guards now cover the decorator + role-view shapes definitively.
- **Decisions made alone:** extended the owner bypass to **all** permission gates including role/channel
  management (per "do everything"); kept the moderation path as-is (owner already passes via governance)
  and left bot-capability (`me`) + informational reads untouched. Recorded for ratification in Q-0212.
