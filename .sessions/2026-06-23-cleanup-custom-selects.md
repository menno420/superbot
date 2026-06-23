# 2026-06-23 — Button/select-driven Custom cleanup level (no typing)

> **Status:** `in-progress` — owner-directed. "The custom setting feels outdated; preferably most actions
> should be done by buttons and select menus, typing should be a last resort only." Part 2 of the owner's
> cleanup-config feedback (part 1 = the Command Access delete-blocked toggle, #1359). Open PR born-red per
> Q-0133; flip to `complete` as the final step.

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

_(filled in at close)_
