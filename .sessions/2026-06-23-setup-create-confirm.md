# 2026-06-23 — Final Review create-count guard + #1351 ledger drift fix

> **Status:** `in-progress` — born-red card (Q-0133). Flip to `complete` as the final step.
> Owner-directed (chat: "continue from where you left off" → the create-count confirmation summary
> teed up at the end of the #1357 wedge session). PR auto-merges on green (Q-0123).

## Arc

#1355/#1357 gave `/setup-describe` the power to **create** channels/roles from a description.
Creating resources is higher-impact and harder to undo than binding existing ones, so the apply
screen should call out *what will be made* before the operator commits — the polish flagged as
#1357's session idea (Q-0089). This session adds that guard.

Also: the SessionStart ledger check surfaced **#1351 (fishing trophy records) as real drift** — a
merge older than the reconciliation marker #1352 that the #1352 pass missed (not benign
newest-merge lag). Per Q-0166 ("fix drift you can SEE on sight"), fixed it in passing.

## Plan (this PR)

- `views/setup/final_review.py` — a `_created_resource_names()` helper (handles both staged shapes:
  `SetupOperation` create kinds → `resource_name`; `SetupRecommendation` `mode="create"` →
  `target_name`) and a distinct **"➕ N new resource(s) will be created"** field on the pre-apply
  embed, naming the resources. Bind-only plans are unchanged.
- `docs/current-state.md` — add #1351 to the fishing Recently-shipped bullet (drift fix; no new
  top-level entry, so the ratchet is unaffected).
- Tests in `test_final_review_caveat.py`.

**Contained:** rendering-only on the read path — no mutation/apply changes.

## Status

In progress — born-red. Close-out written as the final step before flipping to `complete`.
