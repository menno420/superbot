# 2026-06-30 — Role-menu builder live-preview fix (ephemeral re-render)

> **Status:** `in-progress` — born-red card (Q-0133). Run type: manual · owner-directed (bug report
> from a live screen recording).

**Branch:** `claude/reaction-roles-counter-bgxnyd` (restarted from `main` @ #1606 — prior PRs #1570/#1571
merged; this is a fresh change).

## What I'm about to do (intentions)

The owner sent a 55-second screen recording testing the reaction-roles builder and reported: **the
Style toggle "works but the panel does not update", the chosen role pack isn't shown, and the posted
channel isn't shown.** Reviewed every frame: all three changes **actually take effect** (the menu
posts to `#reaction-roles` with the three RSVP **buttons**), but the builder's **preview panel never
re-renders** — it stays frozen on "Roles: none yet / Style: Dropdown / Channel: #bots" the whole time.

**Root cause (one bug, all three symptoms):** the whole reaction-roles hub is **ephemeral** ("Only you
can see this"), and `RoleMenuBuilder._rerender()` refreshed the panel via `self.message.edit()` — but
**an ephemeral message can't be edited with `Message.edit()`**; it can only be edited through the
interaction/webhook token. So every draft mutation (`self.style`/`self.role_ids`/`self.channel`/
`self.show_counts`) was applied and used correctly at Post time, but the `Message.edit()` silently
failed → the preview froze. The codebase already has the right primitive: `interaction_helpers.safe_edit`.

Planned:
1. `RoleMenuBuilder`: store `self._panel_interaction` (the token that owns the ephemeral panel); route
   `_rerender()` + a new `_show_parent()` through `safe_edit(self._panel_interaction, …)`, falling back
   to `Message.edit` for any non-ephemeral caller.
2. Set/refresh `_panel_interaction` at every panel-open (`new_btn` / `_open_editor` / `_duplicate_menu`)
   and at each direct panel interaction (Style/Counts toggles, Text/Limit modals). Sub-flow pickers
   (Roles/Colours/Packs/Channel/Template/Theme/Mode) already call `_rerender()`, so they're fixed for
   free once the choke point routes through the token.
3. Fix `_open_editor`/`_duplicate_menu` to render the builder on the interaction's own message (they too
   used `self.message.edit` → Edit/Duplicate would have failed to open on the ephemeral message).
4. Same one-line fix for the sibling `RoleMenuListView._rerender()` (the menu **list** would go stale
   after delete/repost) + set its token in `reaction_panel.menus_btn`.
5. Tests for the re-render routing.

Contained, reversible, test-covered; needs a live-bot re-test (the owner is testing live) to confirm the
panel now updates. No migration, no new commands.

## What shipped

_(filled in at close)_

## Context delta

_(filled in at close)_
