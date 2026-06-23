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

## What I did
- **panel.py (PR 1):** `policy_btn` / `behavior_btn` / `tools_btn` now
  `interaction.response.edit_message(...)` the persistent anchor to the chooser page
  instead of `send_message`-ing a new ephemeral. The `handle_ai_interaction` router
  fallback (post-restart path) was migrated to `edit_message` too, for parity.
  `AIPanelView` stays persistent (custom_ids unchanged). → 3 findings cleared.
- **chooser sub-trees (PR 2):** `PolicyChooserView` (5), `BehaviorChooserView` (5),
  `ToolsChooserView` (4) — every scope button now `edit_message`-es the anchor to the
  scope picker / preview / list / matrix / advanced page, each carrying a Back button
  that rebuilds its parent page in place. → 14 findings cleared.
- **New `views/ai/_nav.py`:** a small page-swap Back-button helper (synchronous
  `edit_message` parent rebuild + the AI-home page builder + the 25-component cap
  contract). Each chooser carries a `↩ AI home` Back button; each scope page carries a
  `↩ AI <chooser>` Back button.
- Added `build_{policy,behavior,tools}_chooser_page()` Back-target builders (exported
  from the package `__init__`s).
- Reserved ephemerals for confirmations / errors only (the modal submits, the dry-run
  preview/matrix results, and the guarded `guild is None` validation toast stay
  ephemeral — none are flagged).
- Did NOT change view base classes (still `discord.ui.View`); the blanket
  `canonical_helpers.yaml` `views/ai/` exemption is left as a harmless no-op (Phase 3,
  coordinator-owned). No scope select exceeds 25 options here (native
  Channel/Role/Category selects are server-side paginated; presets ≤ 7) so
  `attach_windowed_select` was not needed and `select_option_truncation` stays clean.

## Verification
- `python3.10 scripts/check_consistency.py`: **36 → 19** warnings; **`views/ai/`
  `edit_in_place` findings = 0** (the 19 remaining are all casino/cleanup/roles — other
  units). Exact drop = 17, as required.
- `python3.10 scripts/check_quality.py --full`: green (black/isort/ruff/tool-pins/
  check_docs/check_consistency, mypy 824 files no issues, pytest 12134 passed).
- `python3.10 scripts/check_architecture.py --mode strict`: exit 0, no `views/ai/`
  findings.
- AI test slice: 157 passed (142 existing updated to the in-place contract + 15 new in
  `test_inplace_nav.py`).

## Findings flagged for coordinator allowlisting
None — every one of the 17 `views/ai/` findings was a genuine navigation case and was
**fixed to true in-place**. No `consistency_exceptions.yml` entry requested.

## ⚑ Self-initiated
None — owner-directed Ultracode unit (coordinator-assigned U1). One additive choice
within scope: the new `views/ai/_nav.py` page-Back helper (a contained convenience,
fully test-covered, no shared-helper promotion).
