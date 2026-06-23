# Session — U1 AI panels → in-place navigation (Ultracode worker)

> **Status:** `in-progress`

Ultracode fleet worker **U1**. Branch `claude/u1-ai-inplace-nav` off clean `origin/main`.

## What I'm about to do
Drive the 17 `edit_in_place` consistency findings in `disbot/views/ai/` to 0, following
`docs/planning/ai-panel-inplace-navigation-plan-2026-06-19.md` **PR 1 + PR 2 only**:

- **PR 1 scope:** `AIPanelView.policy_btn`/`behavior_btn`/`tools_btn` (panel.py:215/239/263) —
  convert from `send_message`-ing a new ephemeral chooser to `interaction.response.edit_message(...)`
  an in-place page swap of the same anchor (HubView-style page model + Back affordance to AI home).
  Keep `AIPanelView` persistent (custom_ids unchanged).
- **PR 2 scope:** the 14 chooser findings — behavior/chooser.py (5), policy/chooser.py (5),
  tools/chooser.py (4) — migrate chooser -> scope-picker -> confirmation onto in-place `edit_message`
  page swaps of the one anchor. Ephemerals reserved for confirmations/errors only. Windowed-select
  (`views/paginated_select.attach_windowed_select`) for >25-option scope selects.

Scope-fenced to `disbot/views/ai/**` + mirrored tests. Born-red — coordinator flips/merges in Phase 2.

## ⚑ Self-initiated
None — owner-directed Ultracode unit (coordinator-assigned U1).
