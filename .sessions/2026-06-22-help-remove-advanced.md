# 2026-06-22 — Remove the redundant "All Commands / Advanced" help surface

> **Status:** `in-progress`

Owner-directed follow-up to the help-menu regrouping (#1290): after every
subsystem was homed into a hub, the "All Commands / Advanced" view only
re-listed the 7 hubs with a different layout — redundant. Owner chose
**remove it** (over expanding it to a flat all-subsystems index).

## What I'm about to do
- Remove the "All Commands / Advanced" entry point (HelpCategoryView dropdown
  option + the embed field) and the now-dead machinery behind it: `HelpPanelView`,
  `_build_page_embed`, `_PAGE_SIZE`, `_TIER_GROUPS`, the `advanced` route kind +
  `ADVANCED_ALIASES`, `advanced_subsystems()`, and `ALL_COMMANDS_KEY`.
- The 7 hubs already reach every feature in ≤2 clicks, so nothing is lost.
- Update the affected help/registry tests + comments that reference the surface.
