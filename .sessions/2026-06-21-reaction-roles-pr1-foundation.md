# 2026-06-21 — Reaction-roles overhaul PR 1: audited seam + menu data layer

> **Status:** `in-progress` — building PR 1 (the foundation) of the reaction-roles overhaul
> ([plan](../docs/planning/reaction-roles-overhaul-plan-2026-06-21.md)). Runtime code, but
> **additive + behaviour-preserving** (existing reaction roles work identically; new tables empty =
> no-op) → self-merge on green (Q-0113). Flips `complete` last (Q-0133).

> **Run type:** `manual`

## Arc

Owner asked me to build PR 1 while a parallel session builds PR 2–5 (I wrote that handoff prompt
in-chat). PR 1 = (1) close the long-standing audit-seam debt for the existing emoji reaction-roles,
and (2) lay the role-menu data foundation the parallel PR 2 builder consumes.

## What shipped

- **`disbot/services/reaction_role_service.py`** — the audited write seam. `bind_emoji` /
  `unbind_emoji` persist via the DB layer **and** emit `audit.action_recorded` (subsystem `role`),
  mirroring `role_exemption_service`; `get_binding` / `list_bindings` are the read passthroughs the
  listener uses. Closes the `general-feature-layer-analysis` finding (cog wrote straight to the DB).
- **`disbot/utils/db/role_menus.py`** + **migration `078_reaction_role_menus.sql`** — the role-menu
  data model: `role_menus` (style defaults to `dropdown`, the locked decision; `mode`, `max_roles`,
  `theme`) + `role_menu_options` (FK CASCADE). Full CRUD + `delete_for_guild`. Additive — empty
  tables are byte-identical to the pre-overhaul bot; the legacy `reaction_roles` table is untouched.
- **`disbot/cogs/role_cog.py`** — routed all reaction-role *writes* (`!reactroles` /
  `!removereactrole`) and the listener/`!listreactroles` *reads* through the service. No
  user-facing behaviour change; bindings persist identically, now with an audit trail.
- **`disbot/guild_lifecycle.py`** — teardown step 23 purges `role_menus` for a departed guild
  (options cascade); INV-I satisfied.
- **Tests** — `test_reaction_role_service.py` (audit emission + read passthrough),
  `test_role_menus.py` (RETURNING id + delete count + upsert/order SQL), and two steps added to
  `test_guild_lifecycle_teardown.py` (step 23 awaited + failure-isolated).

## Verification

- `check_architecture --mode strict` → **0 errors**.
- `check_quality --full` → black/isort/ruff + `mypy disbot/` (Success, 747 files) + **11103 passed**.
- Targeted: 27 passed.

(Body close-out + run report filled at session close.)
