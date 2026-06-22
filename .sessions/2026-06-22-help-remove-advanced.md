# 2026-06-22 — Remove the redundant "All Commands / Advanced" help surface

> **Status:** `complete`

Owner-directed follow-up to the help-menu regrouping (#1290): after every
subsystem was homed into a hub, the "All Commands / Advanced" view only
re-listed the 7 hubs with a different layout — redundant. Owner chose
**remove it** (over expanding it to a flat all-subsystems index).

## Shipped

Removed the entry point **and** the now-dead machinery behind it:
- `cogs/help/panels.py` — deleted `HelpPanelView`, `_build_page_embed`,
  `_PAGE_SIZE`, `_TIER_GROUPS`; `HelpCategoryView` lost the "All Commands /
  Advanced" dropdown option + its `_on_select` branch. The file is now just
  the category index (476 → 146 LOC).
- `cogs/help/route.py` — dropped `ADVANCED_ALIASES`, the `advanced` branch in
  `open_route`, and `"advanced"` from the `HelpRoute` kind Literal (4 kinds now).
- `cogs/help_cog.py` — dropped the `HelpPanelView` / `_build_page_embed` /
  `_PAGE_SIZE` / `ALL_COMMANDS_KEY` re-exports, `_build_help_page_view`, and the
  "Advanced / All Commands" field in `build_categories_overview_embed`.
- `services/help_projection.py` — removed `advanced_subsystems()`.
- `utils/hub_registry.py` — removed `ALL_COMMANDS_KEY`.
- Stale comments/docstrings updated across `settings_cog`, `general_cog`,
  `views/games/hub`, `views/diagnostic/__init__`, `message_anchor_manager`,
  and `docs/help-command-surface-map.md` (binding; routing summary + the
  "Advanced remains necessary" bullet rewritten, the dead `HUB_PANEL_BUILDERS`
  override prose fixed).
- Tests: deleted the advanced-surface tests, inverted the "Advanced row
  present" assertions to "absent", and re-pointed the parent-hub-filter tests
  at the category index. Full suite green (11525 passed, 2 xfailed by design);
  arch 0 errors; `check_docs --strict` ✓.

Typed `!help advanced` / `all` / `commands` now fall through to the not-found
fallback (the surface is gone); every feature stays reachable through its hub
in ≤2 clicks, and typed `!help <name>` still resolves straight to any panel.

## ⚑ Self-initiated

None — owner-directed (the "expand or remove" question + the
AskUserQuestion-confirmed "remove"). PR opened ready, auto-merge armed
(Q-0191 owner-directed → merge on green).

## 💡 Session idea (Q-0089)

**Carry the #1290 `--check` guard idea forward and make it catch _orphans
specifically_** — a registry invariant test (or the grouping-sim `--check`
mode) that fails when a subsystem has no `parent_hub` AND is not itself a hub
host. This session is the proof the gap matters: with the Advanced catch-all
removed, an un-homed subsystem is now *completely unreachable* from the menu
(before, it at least fell into Advanced). The safety net is gone, so the guard
that asserts "every subsystem is homed" graduated from nice-to-have to
genuinely load-bearing. Small, stdlib, disposable (Q-0105).

## ⟲ Previous-session review (Q-0102)

The previous session (#1290, the regrouping) did the hard part well — the
simulation-first approach produced a defensible, owner-confirmed grouping. But
it **left a loose end it could have seen**: once everything was homed, the
Advanced view became dead weight, and the session shipped without noticing the
new redundancy (the owner caught it). Improvement for the system: when a change
makes a *catch-all* surface redundant (Advanced was a fallback for orphans;
orphans are gone), that's a signal to re-evaluate the fallback in the same pass,
not a follow-up. A "did this change strand or hollow out an adjacent surface?"
prompt in the regrouping/IA checklist would have surfaced it. (Captured as the
forward idea — make the orphan guard load-bearing now that the net is gone.)

## 🔎 Doc audit (Q-0104)

- `check_docs --strict` ✓ · `check_architecture --mode strict` 0 errors ·
  `check_quality --full` ✓.
- Binding `help-command-surface-map.md` updated (no Advanced browser; empty
  `HUB_PANEL_BUILDERS`; Platform reached via the Server & Admin panel).
- `current-state` Recently-shipped intentionally not touched — #1290 and this
  PR are recorded by the auto-triggered Q-0107 reconciliation pass (the
  twentieth already ran at #1290; next at #1320). Unmerged PR correctly absent.

## Context delta

- **Needed but not pointed to:** the breadth of the *advanced/HelpPanelView*
  blast radius lived only in grep — ~12 test files + 5 comment-only references
  across cogs/views referenced the class. The context map flagged importers but
  not that most were docstring-only. A "comment vs code reference" split in the
  context map would have saved a triage pass.
- **Pointed to but didn't need:** CodeGraph again added nothing — this was a
  deletion best driven by `grep` for the removed symbols + the context-map
  importer list.
