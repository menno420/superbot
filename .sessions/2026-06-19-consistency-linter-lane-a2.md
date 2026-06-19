# 2026-06-19 — Consistency-linter Lane A2: window the per-panel embedded selects

> **Status:** `complete`

## Arc

Executed the live ▶ Next action (band-#1050 queue, **Lane A2** of the
[repo-consistency-linter plan](../docs/planning/repo-consistency-linter-plan-2026-06-17.md),
Q-0170): migrated the **7 remaining `select_option_truncation` findings** — the per-panel
embedded selects that front-truncate their option list (`options[:25]` / `specs[:25]` /
`rules[:25]`, the #1040 silent-drop class) — onto the #1050 `attach_windowed_select` embedded
helper, the same pattern Lane A1 (#1054) used for the shared `views/selectors/` primitives.

## Shipped (#1056)

- **All 7 per-panel selects → `attach_windowed_select`** (each fits the host's 5-row budget;
  nav renders only when a list spans >25, so the common case stays a plain select):
  - `views/access/explorer.py` — subsystem picker → `_attach_subsystem_select` (windowed,
    `select_row=0`/`nav_row=3`).
  - `views/channels/create_panel.py` — category picker; **retired the bespoke `_CategorySelect`
    class + its `views.channels`/`cogs.channel_cog` re-exports**, callback became
    `_CreateSubView._on_category_picked`. Dropped the old `[:15]`/`<24` truncation.
  - `views/channels/move_panel.py` — destination-category picker → `_attach_category_select`
    (nav shares row 3 with the back button); retired its `_CategorySelect`.
  - `views/diagnostic/automation_panel.py` — rule picker → `_attach_rule_select`. Added a new
    **`SelectWindow.detach()`** to `views/paginated_select.py` so `_rerender` can swap the option
    list cleanly after a mutation (replaces the old "remove `_RuleSelect`, re-add" dance).
  - `views/settings/subsystem_view.py` — **both** the edit + reset selects. The edit dispatcher
    was extracted from the old `_EditSettingSelect.callback` to a module-level, unit-testable
    **`dispatch_edit_setting(interaction, subsystem, name)`**; `_attach_edit_select` /
    `_attach_reset_select` host the windowed selects (rows 1/2, nav 3/4).
  - `views/setup/sections/channels.py` — channel-binding picker → `_attach_binding_select`.
- **Result:** `select_option_truncation` warn-only **7 → 0** — the rule now runs **clean on the
  whole `views/` tree**, so it becomes a graduation candidate (flip to error + `code-quality.yml`
  wire-in) after a couple more quiet sessions.
- **Tests** refactored for the new `attach_*` / `dispatch_*` API (no behavioural regressions):
  `test_settings_input_hint_dispatch.py` + `test_settings_cog_edit_routes.py` now call
  `dispatch_edit_setting` directly; `test_create_panel_multi.py` finds the windowed category
  select by placeholder; `test_channel_select_owner_view.py` dropped the retired `_CategorySelect`
  case; `test_access_explorer.py` updated for the no-front-truncation builder + windowed nav
  buttons. CI mirror green (**10658 passed, 38 skipped**); `check_architecture --mode strict` exit 0.

## Continuation (the handoff)

The `select_option_truncation` lane is **fully consumed** (15 → 7 in A1, 7 → 0 here). The next
consistency-linter slice — any of:

1. **Graduation prep for rule 4** — once it stays at 0 across a couple more sessions, flip it to
   `error` and wire it into `code-quality.yml` (plan step 3b). Not yet — it only just hit 0.
2. **The `panel_base_class` double-win** — migrate the settings select-views that still extend
   `discord.ui.View` directly (`ChannelSettingSelectView`, `RoleSettingSelectView`,
   `NumericPresetsView`, + `SetupLauncherView`, `_RankView`, `_BotDuelView`) onto `BaseView`. Each
   retires **both** a `panel_base_class` finding and a `baseview_inheritance` arch-debt row, the
   exact ratchet #1048 did (12 → 9). `panel_base_class` is currently **26**.
3. **Triage the `edit_in_place` backlog (45)** — split clear false-positives (RPS join, setup
   launcher sub-flows that genuinely open a new ephemeral) → allowlist, real bugs (e.g.
   `DiagnosticsPanel.refresh_btn` showing a toast instead of re-rendering) → fix.

Behind the linter lane: procedures→skills Batch 1, owner-review-inbox Phase 1, the small stdlib
guards. No PLAN-BACKLOG-THIN flag.

## ⟲ Previous-session review (Q-0102)

The A1 session (#1054, selectors-windowing) was a clean, well-scoped slice and left an unusually
good handoff — it named the exact 7 A2 targets, the row-budget pattern, and the
`access_map._attach_feature_detail_select` reference to copy. That precision is *why* A2 went
fast. One thing it could have done better: it left a latent **row-budget hazard** in `move_panel`
(the channel multi-select nav already claims row 4) without flagging it, so a naïve A2 could have
collided two windowed selects on one row; I caught it and split the category nav onto row 3.
**System improvement surfaced:** the consistency plan's per-panel handoff would be stronger if it
recorded each target's *current row map* (which rows/navs are already occupied), since the windowed
helper's correctness depends entirely on free-row availability — that's the one non-mechanical part
of an otherwise mechanical migration. I've kept the plan's A2 entry pointing at the
`select_row`/`nav_row` pattern; a future "embedded-select migration" rule could even *check* the
row budget statically.

## 💡 Session idea (Q-0089)

**A `consistency` linter rule that flags row-budget over-subscription in a `discord.ui.View`** —
statically sum each view's declared `row=`/`select_row=`/`nav_row=` assignments (a select occupies
a whole row; buttons pack 5/row; a windowed select's nav adds a conditional row) and warn when the
worst case exceeds Discord's 5-row / 25-item limits. This is the natural rule-5 for the consistency
linter: the *one* hazard the select-windowing migrations repeatedly had to reason about by hand
(this session's `move_panel` near-collision), and a class Discord rejects at runtime with an opaque
error. Genuinely worth having — it would have caught the hazard the A1 handoff missed. Captured
here as a session idea, not built (it's a fresh rule = its own slice).

## 📊 Doc audit (Q-0104)

- `check_current_state_ledger --strict`: 2 recent merged PRs not yet in the ledger — **#1053** and
  **#1055**, both *newer* than the reconciliation marker **#1050** → **benign newest-merge lag**
  (the Q-0166 exception; the #1080 reconciliation pass records them). Not this session's drift.
- Updated the linter plan (Lane A2 entry) + current-state ▶ Next action to mark A2 shipped and
  point at the next slice. New public symbol `dispatch_edit_setting` + `SelectWindow.detach()` are
  documented in their modules.
- No new owner decisions; nothing captured only in chat that belongs in a doc.

## 📤 Run report

- **Did:** windowed the 7 remaining per-panel embedded selects (consistency-linter Lane A2),
  driving `select_option_truncation` to 0 across the whole `views/` tree. · **Outcome:** shipped
- **Shipped:** #1056 — 7 selects → `attach_windowed_select` across 6 view files, + a new
  `SelectWindow.detach()`, + the extracted `dispatch_edit_setting`; tests refactored.
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** `none`
- **⚑ Owner manual steps:** `none`
- **⚑ Self-initiated:** `none` (executed the dispatched live ▶ Next action; the row-budget linter
  rule is *captured* as a session idea, not built)
- **↪ Next:** the next consistency-linter slice — rule-4 graduation prep, the `panel_base_class`
  double-win migration, or the `edit_in_place` triage (see continuation above).

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 1 (#1056, on green) |
| CI-red rounds | 1 (born-red session gate by design; local mirror green before flip) |
| `select_option_truncation` findings | 7 → 0 |
| New ideas contributed | 1 (row-budget over-subscription linter rule) |
| Ideas groomed | 0 (capacity went to the substantial A2 slice) |
