# 2026-06-18 — Migrate standalone-ephemeral select pickers onto `PaginatedSelectView`

> **Status:** `in-progress`

## What I'm about to do
Continue the consistency-linter migration slice (current-state ▶ Next action): move the
**cleanly standalone single-select ephemeral pickers** onto the shared
`views/paginated_select.py` `PaginatedSelectView` primitive (shipped #1047) — retiring both
their `select_option_truncation` and `panel_base_class` linter findings and fixing the
latent #1040 >25-option silent-drop bug in each.

Targets (the three genuine standalone pickers; the rest — selectors/, mining, subsystem_view,
channels panels, access/explorer — are embedded in multi-control views and need per-consumer
windowing, a later slice):
- `views/settings/edit_enum.py` — `EnumSettingSelectView`/`_EnumSelect`
- `views/roles/time_roles_panel.py` — `_TimeRemoveView`/`_TimeRemoveSelect`
- `views/roles/xp_roles_panel.py` — `_XpRemoveView`/`_XpRemoveSelect`
