# 2026-06-23 — Button/select-driven Custom cleanup level (no typing)

> **Status:** `complete` — owner-directed. "The custom setting feels outdated; preferably most actions
> should be done by buttons and select menus, typing should be a last resort only." Part 2 of the owner's
> cleanup-config feedback (part 1 = the Command Access delete-blocked toggle, #1359). PR #1360,
> auto-merge armed on green (Q-0127); owner-directed → merge immediately (Q-0191).

> **Run type:** `manual · owner-directed`

## What I'm about to do

The cleanup policy builder's whole flow is already select/button-driven *except* the **Custom…** level,
which opens `_CustomLevelModal` — three `TextInput`s where the operator types `8`, `yes`, `no`. Replace
it with a select-driven view (no typing):

- `_CustomLevelView` (ephemeral, `BaseView`) holding the three choices as state.
- A **delete-after duration** select: Instant (0s) · 2s · 5s · 10s · 30s · 60s · 2m · 5m.
- A **delete invalid commands?** Yes/No select.
- A **delete failed commands?** Yes/No select.
- A **Preview & apply** button → the existing `preview_cleanup_columns` dry-run → `_ConfirmApplyView`.
- Each select reflects the current pick (marked default) + a one-line summary in the message; the
  `Custom…` level option routes here instead of opening the modal.

Keeps the shared columns seam + audited apply from #1345 untouched — only the *input surface* changes.

## What shipped

The Custom cleanup level is now fully select-driven — no typing:

- **`views/cleanup/policy_panel.py`** — replaced `_CustomLevelModal` (3 `TextInput`s) + the `_parse_bool`
  / numeric-range parsing with a `_CustomLevelView` (`BaseView`):
  - `_DeleteAfterSelect` — a duration menu (`_DURATION_OPTIONS`: Instant 0s · 2s · 5s · 10s · 30s · 1m ·
    2m · 5m, all within the service's 0–300 bound so no range check is needed).
  - two `_CustomYesNoSelect` pickers (delete invalid? / delete failed?).
  - `_CustomPreviewButton` → the existing `preview_cleanup_columns` dry-run → `_ConfirmApplyView`.
  - Each picker rebuilds the view (`update`) so the selected option shows as default + a one-line
    `summary()`; the `Custom…` level routes here instead of `send_modal`.
  - Dropped the now-unused `MAX_DELETE_AFTER_SECONDS` import (the menu can't produce an out-of-range value).
- **Tests** — rewrote the 3 modal tests into 5 select-flow tests: Custom opens a typing-free view (no
  `TextInput` children), durations are all in-bounds + Instant offered, the duration and Yes/No selects
  update state, and Preview routes the chosen columns through the dry-run without writing. 24 cases in the
  file green; full suite 12040; mypy clean; arch 0.

The shared columns seam + audited apply (from #1345) are untouched — only the *input surface* changed.

## Findings / decisions

- **Decision made alone — a fixed duration menu, not free numeric entry.** The owner wants "typing as a
  last resort"; 8 sensible presets (incl. Instant 0s) cover the realistic range, and because every menu
  value is in-bounds the whole "type a number / validate 0–300 / reject non-numeric" path disappears.
  Arbitrary odd values (e.g. 47s) are no longer reachable — an acceptable trade for a no-typing flow; if
  a specific value is ever needed it can be added to `_DURATION_OPTIONS`.
- **Decision made alone — rebuild-the-view on each pick** (vs mutating select defaults in place) so the
  current selection always renders as the menu default. Simple and stateless-per-render.

## 💡 Session idea

**A small `views/` helper for "stateful multi-select builder" views.** This `_CustomLevelView`
(hold a few choices as state, rebuild on each select so defaults reflect the pick, finalize with a button)
is a pattern that recurs across the codebase's select-driven panels (gear pickers, reaction-role builders,
the command-access channel select). A tiny `BaseView` subclass or mixin that standardizes "state +
rebuild-on-change + summary line" would remove the per-panel boilerplate and make every typing-free
builder consistent. (Dedup-checked `docs/ideas/` — no existing stateful-builder-helper idea.)

## ⟲ Previous-session review (Q-0102)

The previous session (#1359, the Command Access delete-blocked toggle) was a clean, well-scoped runtime
feature and correctly *split* the owner's two-part feedback into two focused PRs rather than one sprawling
change — which is exactly what let this part ship as a pure view refactor with zero migration/runtime
risk. Its one stylistic snag (black splitting an f-string into an ISC001-flagged implicit concatenation)
is a recurring micro-friction across sessions. **System improvement (initiated):** the
`PostToolUse` auto-formatter already runs black+ruff per edit, but black and ruff's ISC rule can disagree
(black *creates* the implicit concatenation ruff then rejects) — worth a journal note that f-strings with
embedded conditionals should be assigned to a local first (as I did here) to sidestep the black↔ruff
tug-of-war, saving a fix-up round trip.

## 📤 Run report

- **Did:** Replaced the typing-based Custom cleanup-level modal with a select-driven builder (duration
  menu + Yes/No pickers + Preview button) · **Outcome:** shipped (PR #1360, auto-merge armed on green)
- **Shipped:** #1360 — button/select-driven Custom cleanup level
- **Run type:** `manual · owner-directed`
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none — merged = deployed (Railway auto-redeploys `worker` on merge; view-only
  change, no migration). `!cleanup → Cleanup Policies → Set a policy → Custom…` is now typing-free.
- **⚑ Self-initiated:** no — owner-directed (the "typing should be a last resort" request).
- **↪ Next:** both parts of the owner's cleanup-config feedback are shipped (#1359 delete-blocked toggle +
  #1360 select-driven custom). Nothing pending in this lane.

## ⟳ Doc audit (Q-0104)

`check_docs --strict` green; `check_consistency` 0 errors; arch 0; mypy clean. View-only change, no new
owner decision or doc home needed beyond this log. PR not yet in `current-state` Recently-shipped (benign
newest-merge lag — recorded by the next reconciliation pass, the routine's job per Q-0124).
