# 2026-06-21 — Reaction-roles PR 2: in-Discord role-menu builder

> **Status:** `in-progress` — building PR 2 of the reaction-roles overhaul
> ([plan](../docs/planning/reaction-roles-overhaul-plan-2026-06-21.md)): the modern in-Discord
> role-menu builder (Surface B) — dropdown-default `RoleMenuView` + operator builder with
> edit-in-place / theme presets / message templates, all writes through the audited
> `reaction_role_service`. **HOLD:** depends on PR 1 (foundation) being built in a parallel
> session; this card stays red until PR 1 has merged and this branch is reconciled onto it.

> **Run type:** `manual`

## Arc (what this session is about to do)

PR 2 from the locked plan (§4 + §4.6, owner decisions §9):
- `views/roles/role_menu_view.py` — `RoleMenuView(PersistentView)`: dropdown (default) or buttons,
  server-side mode enforcement (unique / max_roles), ephemeral confirms, re-attached on restart.
- `views/roles/role_menu_builder.py` — operator builder off the Reaction Roles panel: title/desc,
  windowed role picker, style/mode/limit, **theme presets**, **message templates**, **edit-in-place**, Post.
- `utils/role_menu_presentation.py` — theme + template catalogues (pure data on `ui_constants`).
- All writes via `reaction_role_service` (audited); re-attach loop wired in `bot1.on_ready`.

## ⚠️ PR 1 coordination

PR 1 (parallel session) owns: `services/reaction_role_service.py` (creation), migration 078,
`utils/db/role_menus.py`, the cog reaction-listener re-routing, the `guild_lifecycle.py` hook.
This branch includes a copy of the foundation it strictly needs, built to the plan's **locked
spec**, so PR 2 is self-contained + CI-green. **Reconcile before merge:** rebase onto PR 1, take
PR 1's foundation, keep only PR 2's additions (menu service methods + the new view/builder files).

## 📤 Run report (filled at close)

- **Did:** _pending_
- **Shipped:** _pending PR #_
- **Run type:** `manual`
- **⚑ Self-initiated:** none (owner-requested task: build PR 2→PR 5 of the reaction-roles overhaul)
- **↪ Next:** PR 3 (Carl-parity modes + interactive emoji panel) · PR 4 (free temp roles) · PR 5 (analytics)
