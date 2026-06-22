# 2026-06-22 — Role list colours + per-role bulk colour

> **Status:** `in-progress`

Owner-relayed, two asks (screenshots: the 🗂️ Role Management list is plain white
text, while the 💬 Reaction Roles panel shows coloured role mentions):

1. **Make the Role Management list show each role's colour** like the reaction-role
   menu does — i.e. render roles as **mentions** (`role.mention`), which Discord
   auto-colours, instead of plain bold `role.name`.
2. **For bulk roles, add an optional per-role colour chooser**, using the same
   "walk each one with a picker" method the reaction-role flow uses to match emotes
   to roles (`_BindEmotesView`). Apply to the **custom bulk** path (typed names),
   alongside the existing "one colour for all" / "no colour".

## Plan

- `management_panel.py` build_embed: `**{role.name}**` → `{role.mention}`.
- `_role_pack_flow.py`: add a "🎨 Per-role colours" button on `_BulkColourView`
  that opens a `_PerRoleColourView` walker (one colour preset select per name,
  including a "no colour" option), then bulk-creates via the shared `_create_roles`.
- Tests for both.

Owner-directed (Q-0191): PR ready, auto-merge armed.
