# Session — reaction-roles overhaul PR 2 (in-Discord role-menu builder)

> **Status:** `in-progress`
> **Run type:** routine · dispatch
> **Branch:** `claude/funny-franklin-ocwbje`

## What I'm about to do

Build **PR 2** of the reaction-roles overhaul plan
([plan](../docs/planning/reaction-roles-overhaul-plan-2026-06-21.md) §4 / §9) — the
buildable-now in-Discord **role-menu builder (Surface B)** on the PR 1 foundation
(audited `reaction_role_service` + migration 078 `role_menus`/`role_menu_options`,
merged #1220):

- **Public persistent menu** (`views/roles/role_menu_view.py`) — dropdown-default
  (owner-locked §9) or buttons, rendered as a public message; click/select toggles
  roles with an ephemeral confirm. Restart-durable via discord.py `DynamicItem`
  (menu_id/role_id encoded in the custom_id — no per-message anchor, multi-user).
  Server-side mode enforcement (`unique` clears siblings, `max_roles` caps).
- **Operator builder** (`views/roles/role_menu_builder.py`) — title/description,
  windowed role multi-select, style/mode/limit, **theme presets** (§4.6b),
  **starter templates** (§4.6c), **edit-in-place** (§4.6a) — re-renders the row and
  edits the live message, no repost.
- **Audited menu writes** added to `reaction_role_service` (create/update/delete).
- Pure toggle/reconcile logic in `utils/role_menu_logic.py` (testable).
- Wired into `ReactionRolesPanel` (New Menu / Manage Menus); `DynamicItem`s
  registered at startup.

Substantial runtime + new persistent surface → **`needs-hermes-review`** (Q-0117),
**not** an autonomous self-merge.

## Verification (gate)

```
python3.10 scripts/check_architecture.py --mode strict
python3.10 scripts/check_quality.py --full
python3.10 scripts/check_docs.py --strict
```
