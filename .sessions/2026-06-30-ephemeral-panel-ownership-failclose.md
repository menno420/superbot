# 2026-06-30 — Fix: ephemeral persistent-panel ownership fail-close ("can no longer be verified")

> **Status:** `in-progress`

**Run type:** owner-directed (bug report — screen recording)

## What I'm about to do

Owner screen recording: opening the **Role hub via `/help` → Community → Roles** and clicking a button
produces **"This panel can no longer be verified — please re-open it."**

**Root cause (confirmed, not the permission work):**
- `RoleHubPanelView` is a `PersistentView` with `FAIL_CLOSED_ON_MISSING_ANCHOR = True`
  (`cogs/role_cog.py:77` — role management is guild-mutating, so opted into fail-closed).
- Its inherited `PersistentView.interaction_check` (`core/runtime/persistent_views.py:114`) verifies
  ownership via a **DB message-anchor row** (`db.get_panel_anchor_by_message`).
- The `/help` path renders the hub via `role_cog.build_help_menu_view()` **ephemerally**, and
  **ephemeral messages are never anchored** (only the `!roles` path anchors, via
  `panel_manager.get_or_render_panel`). Anchor missing + fail-closed → deny → the message
  (`persistent_views.py:127`).
- Anchors are DB-backed, so this is **not** a restart issue; it affects **any** user reaching a
  fail-closed panel through an ephemeral help/nav path, not just the owner.

**Fix (general, safe):** an **ephemeral message is private to the invoking user** — Discord guarantees
nobody else can see/click it — so ownership is implicit and the anchor check is meaningless there. Add a
guard at the top of `PersistentView.interaction_check`: if `interaction.message.flags.ephemeral`, return
`True` before the fail-closed branch. Fixes the whole class with no security loss. Regression test pins:
ephemeral + fail-closed + no anchor → allowed; non-ephemeral + fail-closed + no anchor → still denied.
