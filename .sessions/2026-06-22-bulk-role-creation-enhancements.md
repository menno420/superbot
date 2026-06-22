# 2026-06-22 — Bulk role creation enhancements

> **Status:** `in-progress`

Owner follow-up to #1300 (bulk role packs). Three asks + "find the most efficient
way, compare options":

1. **Enlarge the standard preset roles** (`ROLE_PRESETS`) **and make them
   multi-select** (bulk-create several at once).
2. **Bulk custom-role creation** — type many role names → create them all.
3. **Optional colour preset select** — pick a colour from a preset list (easy,
   no hex typing); optional.

## Approach (compared in the response; chosen = reuse the shipped flow)

Most efficient = reuse the just-shipped `RolePackView` + `ensure_role`:
- **Essentials pack** in `role_packs.py` (the enlarged standard roles) → appears in
  the existing category multiselect for free → "multi-select standard presets".
  `_helpers.ROLE_PRESETS` derived from it (one data source; single-create panel +
  test unchanged).
- **✏️ Custom (bulk)** button on `RolePackView` → names modal (one per line /
  comma-separated) → **optional** colour preset select (enlarged `_COLOR_OPTIONS`)
  or "create with no colour" → `ensure_role` loop.
- Enlarge `_COLOR_OPTIONS` for the preset colour selects.

No schema change; pure data + UI on the existing audited create seam. Works on
both surfaces (creation panel + menu builder) since they share `RolePackView`.

Owner-directed (Q-0191): PR ready, auto-merge armed.
