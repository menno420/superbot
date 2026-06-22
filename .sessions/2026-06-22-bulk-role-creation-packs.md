# 2026-06-22 — Bulk role creation via preset packs

> **Status:** `in-progress`

Owner-relayed user request: add **bulk role creation** modelled on the existing
colour-reaction-role flow — pick a category (gaming / moderation / …), then a
**multiselect of predefined roles** that match the type, and the bot creates them
all in one step. Mirrors the shipped 🎨 Colours auto-create UX
(`role_menu_builder._ColourRolesView` → `ensure_color_role`) but with curated
*functional* role packs instead of colours.

## Plan (about to build)

1. **Catalogue** — `disbot/utils/role_packs.py` (pure data, mirrors
   `role_menu_presentation.py`): `RolePack`/`PackRole` dataclasses + curated
   categories (Gaming, Staff/Moderation, Pronouns, Notifications, Region,
   Interests). Accessors `packs()` / `get_pack()`.
2. **Seam** — generalize the reuse-or-create logic into
   `reaction_role_service.ensure_role`; `ensure_color_role` delegates (no
   behaviour change; existing tests stay green).
3. **Surface A — standalone create** (`RoleCreatePanel`): 📦 Role Packs button →
   category select → role multiselect → audited bulk create into the server.
4. **Surface B — into a menu** (`role_menu_builder`): 📦 Packs button beside
   🎨 Colours → bulk-create + add to the menu draft (the literal "colour reaction
   roles" mirror).
5. Tests + docs.

Owner-directed (Q-0191): PR opens ready, auto-merge armed, not held for review.
