# Session — reconcile-marker band-consistency guard (+ marker conflation fix)

> **Status:** `in-progress` — born-red card (Q-0133). Flips to `complete` as the final step.
> **Run type:** routine · dispatch

## What I'm about to do

Promote the freshly-captured idea
[`reconcile-trigger-band-consistency-guard-2026-06-26`](../docs/ideas/reconcile-trigger-band-consistency-guard-2026-06-26.md)
into a shipped guard (Q-0172 self-initiated promotion — idea→ship, no dispatch order this fire):

1. **`scripts/check_reconcile_marker.py`** — a warn-first, stdlib, disposable (Q-0105) guard that
   asserts the `Last reconciliation pass:** PR #N` marker in `current-state.md` is internally
   consistent: (a) the leading `#N` equals the parenthetical "reset to the latest merged PR #R"
   value (the conflation guard — the idea's core), (b) the `band-#M` label has `M = (N // 30) * 30`
   (the cadence boundary), and (c) the linked `reconciliation-pass-*` doc exists on disk. Folds into
   the existing `check_current_state_ledger` / `check_reconciliation_due` family.
2. **Fix the live drift it catches** (bugs-first / Q-0166): the 26th pass set the marker to its own
   PR `#1472` while its parenthetical (and the convention "reset to the latest PR") say `#1470` —
   correct it to `#1470`.
3. Tests in `tests/unit/scripts/`; mark the idea shipped; add a discoverability pointer.

Why offline-fit: no dispatch work order this fire, most feature lanes are owner/live-bot/design-gated,
and this is the "leave the next run better-equipped" lane the loop exists for — fully offline,
test-covered, zero runtime risk.
