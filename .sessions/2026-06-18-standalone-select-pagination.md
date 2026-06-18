# 2026-06-18 — Migrate standalone-ephemeral select pickers onto `PaginatedSelectView`

> **Status:** `complete`

## What & why
Continued the consistency-linter migration slice (current-state ▶ Next action): moved the
**three cleanly standalone single-select ephemeral pickers** onto the shared
`views/paginated_select.py` `PaginatedSelectView` primitive (shipped #1047). Each was a bespoke
`discord.ui.View` + `discord.ui.Select` pair that front-truncated its options with `[:25]` —
the latent #1040 silent-drop class (an enum with >25 allowed values, or a guild with >25
time/xp threshold roles, would lose every option past the 25th, unreachable).

## Change (PR #1048)
- `views/settings/edit_enum.py` — replaced `EnumSettingSelectView`(discord.ui.View) + `_EnumSelect`
  with a `build_enum_select_view(author, …)` factory returning a `PaginatedSelectView`; the
  mutation + parent-refresh logic moved into an `on_select` closure. Call site updated in
  `subsystem_view.py` (passes `interaction.user` as the invoker).
- `views/roles/time_roles_panel.py` — `_TimeRemoveView`/`_TimeRemoveSelect` retired; `remove_btn`
  now builds a `PaginatedSelectView` over `self._remove_threshold`.
- `views/roles/xp_roles_panel.py` — `_XpRemoveView`/`_XpRemoveSelect` retired; same shape, with
  the defer-ephemeral-before-write ACK ordering preserved (the `test_xp_remove_defer` regression).
- Tests repointed: `test_view_base_class_conformance.py` (dropped the 3 now-migrated allowlist
  entries — the ratchet **shrank**, the intended direction), `test_role_panels_discordpy_compat.py`
  (collision guard repointed onto the shared `_WindowSelect`), `test_xp_remove_defer.py`
  (exercises `XpRolesPanel._remove_threshold`), `test_settings_edit_modals.py` +
  `test_settings_cog_edit_routes.py` (construct/assert via `build_enum_select_view` /
  `PaginatedSelectView`). `edit_channel.py` docstring xref updated.

## Outcome
- Linter: `select_option_truncation` 31→28, `panel_base_class` 29→26 (each migration retired
  **both** findings for its file). Arch `baseview_inheritance` debt 12→9.
- `check_quality.py --full` green (10650 passed); `check_architecture --mode strict` 0 errors.

## Handoff — next consistency-linter slice
The **28 remaining `select_option_truncation` candidates are all embedded in multi-control views**
(`selectors/`, `mining/` market/recipe/gear/workshop, `settings/subsystem_view` edit/reset,
`channels/move_panel`+`visibility_panel`, `access/explorer`). `PaginatedSelectView` is a
*standalone* view, so it does NOT drop into these — they need a **design step**: either a new
windowed-*embedded*-select helper (a `Select` owning page state + re-render, plus parent ◀/▶
buttons preserved across flips) or per-view nav. Treat it as a small plan, not a mechanical swap.
`access/explorer` (subsystems ~35 today) and the guild-channel/category selects are genuine
>25 truncations; several mining selects may instead be bounded-catalogue allowlist candidates —
verify counts before paginating.

## 💡 Session idea
The conformance ratchet (`test_view_base_class_conformance.py`) and the consistency linter both
track the **same** `baseview_inheritance` / `panel_base_class` set, by two different mechanisms
(a frozen-set unit test vs. an AST rule). They drifted apart historically (the linter found 30,
the ratchet 12, because the ratchet exempts framework homes + game-state paths the linter also
exempts but enumerated differently). Idea: have the consistency linter's `panel_base_class` rule
**derive its exemptions from the architecture checker's `baseview_inheritance` config** (one
source of truth for "what may extend `discord.ui.View`"), so the two can never disagree on the
allowlist — closing a small but real "two checkers, one rule, two answers" drift class.

## ⟲ Previous-session review (#1047, cog-routing-pagination)
#1047 did the hard, correct foundational work — built the reusable `PaginatedSelectView`, fixed a
real >25-roles bug, AND triaged 53 candidates → 31 genuine with per-callback allowlist reasons —
which is exactly what made *this* session a clean mechanical follow-through. One thing it could
have flagged more loudly: its handoff listed `move_panel`/`visibility_panel`/`access/explorer`/
`subsystem_view` under "standalone-ephemeral pickers first", but they're actually **embedded** in
multi-control views (a channel multi-select + buttons, a scope select, etc.), so they don't fit
the standalone primitive. The classification was optimistic. **System improvement:** when a
handoff buckets follow-up work as "mechanical", it should state the *structural test* that puts an
item in the easy bucket (here: "the select is the sole control in its own ephemeral view"), so the
next session can verify the bucket rather than discover mid-task that half of it isn't mechanical.
I corrected the bucketing in this run's handoff + the plan doc.

## 📤 Run report
- **Run type:** routine · dispatch
- **Result:** shipped PR #1048 (1 complete slice) — standalone select pickers → `PaginatedSelectView`.
- **⚑ Self-initiated:** none (this is the named current-state ▶ Next-action slice).
- **⚑ Owner-decisions:** none.
- **⚑ Owner-manual-steps:** none (merge auto-deploys; deterministic view-layer change, no data/migration).
