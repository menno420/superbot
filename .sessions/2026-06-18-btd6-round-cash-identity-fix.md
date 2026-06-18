# 2026-06-18 — BTD6 round_cash identity ABR fix (Codex P2 on #1035)

> **Status:** `in-progress`
> Owner-live follow-up to #1035. Fixing the one real Codex review finding on that PR.

**PR:** (this PR) — gate the `round_cash` identity sentence to reconciling ranges.
**Branch:** `claude/zen-wright-77q0ru` (reset onto main after #1035 merged).

## What I'm about to do / did

#1035 (BTD6 answer fixes) merged. Codex left one review comment (P2) — verified real:

- **The bug:** the new `round_cash` `identity` sentence was gated only on `cumulative_at_end is not
  None`. For an ABR range that spans the unplayed rounds 1-2 (e.g. `round_cash(1, 3, abr)`), the
  cumulative totals start at round 3, so `cumulative_at_end - cumulative_before_start` omits rounds
  1-2's cash and **contradicts** `range_cash` (range_cash=418 but the sentence said 790-650=140).
  Because the tool spec tells the model to quote `identity` verbatim, that could surface contradictory
  math.
- **The fix:** emit `identity` only when the subtraction actually reconciles
  (`round(cumulative_at_end - cumulative_before_start, 2) == range_cash`). Self-validating, so it's
  honest for the ABR-unplayed case (the existing `cumulative_note` already explains that boundary) and
  any future data edge — never publish a quote-verbatim sentence the numbers disprove. Verified:
  ABR 3-10 (played range) keeps its identity; ABR 1-3 / 1-5 / 2-4 now omit it.

Also reconciled the living ledger (#1034/#1035/#1036).

## Verification

- `python3.10 scripts/check_quality.py --full` → green (10490 passed, 38 skipped).
- New tests in `test_btd6_abr_rounds`: no identity for ABR ranges spanning rounds 1-2; identity present
  + reconciling for an entirely-played ABR range.
- Codex review thread resolved.

## 💡 Session idea

**Idea:** a tiny invariant test that asserts *whenever* `round_cash` returns an `identity`, the
arithmetic in it reconciles (`cumulative_at_end - cumulative_before_start == range_cash`) — parametrized
over a spread of standard + ABR ranges. **Why:** the identity is a model-quoted string; this pins the
"never emit a self-contradictory identity" property as a property, not just two example cases, so the
next person who touches the gate can't silently reintroduce the #1035 P2.

## ⟲ Previous-session review

The previous session (#1035, this conversation) shipped the four fixes with full local CI + tests, but
**missed the ABR-unplayed edge** on the new identity field — its test only covered a standard range
(8-66) and the ABR tests predated the field, so the contradiction slipped through; Codex caught it.
The improvement (captured as this session's idea): when a new field is *handed to the model to quote
verbatim*, its tests must cover the round-set/edge axes the surrounding function already special-cases
(the ABR `lo < 3` boundary was right there in the same function). Codex acting as the independent
reviewer worked exactly as the Q-0174 integration intended.

## 📤 Run report

- **Did:** gated the `round_cash` identity to reconciling ranges (Codex P2 fix) + ledger reconcile ·
  **Outcome:** shipped, CI green
- **Run type:** manual (owner-live)
- **⚑ Self-initiated:** none (owner asked me to review Codex's comments; ledger reconcile is on-sight)
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none
- **↪ Next:** optional identity-reconciles invariant test (session idea)
