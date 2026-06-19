# 2026-06-19 — Consistency-linter Lane A2: window the per-panel embedded selects

> **Status:** `in-progress`

## Arc (what I'm about to do)

Execute the live ▶ Next action (band-#1050 queue, **Lane A2** of the
[repo-consistency-linter plan](../docs/planning/repo-consistency-linter-plan-2026-06-17.md),
Q-0170): migrate the **7 remaining per-panel embedded selects** off front-truncating
`discord.ui.Select` subclasses (`options[:25]` / `specs[:25]` / `rules[:25]`, the
#1040 silent-drop class) onto the #1050 `attach_windowed_select` embedded helper —
the same pattern Lane A1 (#1054) used for the shared `views/selectors/` primitives.

Targets (the 7 `select_option_truncation` warn-only findings):

- `views/access/explorer.py:77` — subsystem picker
- `views/channels/create_panel.py:59` — category picker
- `views/channels/move_panel.py:40` — destination-category picker
- `views/diagnostic/automation_panel.py:238` — automation-rule picker
- `views/settings/subsystem_view.py:439,584` — edit + reset setting selects
- `views/setup/sections/channels.py:301` — channel-binding picker

Expected result: `select_option_truncation` warn-only **7 → 0**.
