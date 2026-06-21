# 2026-06-21 — Role presets + role-management UX overhaul

> **Status:** `in-progress` — born-red HOLD (Q-0133). Flip to `complete` as the deliberate
> final step once the work + close-out docs land.

> **Run type:** `manual` (owner-directed, screenshots + in-chat requirements)

## Arc

Owner-directed from a `!roles` diagnostics screenshot ("Role Automation ⚠️ missing: Neu, Normal,
Iron, Gold, Diamand, Netherite, Beacon") plus three follow-up UX asks. Four threads, all inside
the role-management subsystem (`disbot/views/roles/` + `cogs/role_cog.py` + `_helpers`):

1. **Remove the hardcoded German/Minecraft tier names** (`_DEFAULT_THRESHOLDS` =
   Neu/Normal/Iron/Gold/Diamand/Netherite/Beacon) and the `_ensure_defaults` seeding entirely —
   role automation now loads **only real server roles**; add a **🧹 Clear missing** purge so the
   phantom stale rows those names left in the DB can be cleared (the diagnostics "missing:" line).
2. **Create role** — a creation *menu* with **preset role names** + **colour presets** to pick,
   custom (full modal) still available. Presets live ONLY in this menu (owner constraint).
3. **Edit role** — pick the role from a **select** instead of typing its name.
4. **Delete role** — **multi-select + confirmation** instead of single immediate delete.

## Status: building. (placeholder — close-out notes below on flip-to-complete.)

## 📤 Run report

- **Did:** (in progress)
- **Run type:** `manual`
