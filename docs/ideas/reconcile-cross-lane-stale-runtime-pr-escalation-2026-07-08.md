# Idea — reconcile pass: escalate cross-lane-orphaned runtime PRs

> **Status:** `ideas` — captured by the band-#1860 (thirty-ninth) Q-0107 reconciliation pass (2026-07-08).
> Lane: S4 tooling / S5 ops. Size: small, stdlib, disposable (Q-0105).

## The gap (evidenced this pass)

The 6 dependabot dep-bump PRs **#1761–#1766** have now been recorded "**left in flight — runtime, not this
docs-only lane**" by **four consecutive** reconciliation passes: the 36th (band-#1770), 37th (band-#1800),
38th (band-#1830), and this 39th (band-#1860). Each pass is individually *correct* — a docs-only Q-0107 pass
must not merge runtime dependency changes — but the aggregate behavior is a bug: these PRs fall in the seam
**between two lanes**. The reconciliation lane can't touch them, and the execution/dispatch lane hasn't
picked them up either, so "not my lane" has quietly become "no lane," and green, mergeable PRs rot for
weeks. This is the same failure the Q-0125 disposition rule was written to prevent (#766 red for ~21h) — just
slower and cross-lane instead of within-pass.

The existing [`reconcile-open-pr-staleness-classifier`](reconcile-open-pr-staleness-classifier-2026-06-22.md)
idea buckets open PRs by age/label/CI, but it stops at *classification* — it does not close the loop by
**routing** a correctly-deferred PR to the lane that *can* act on it, nor does it notice the multi-pass
re-deferral pattern that is the actual smell here.

## The proposal

Add a tiny **cross-pass memory + escalation** step to the reconciliation routine (a few lines in
`band_pr_status.py --open-prs`, or a standalone `scripts/check_cross_lane_stale_prs.py`):

1. Read the last N pass records' "left in flight" PR lists (they are structured prose in
   `docs/planning/reconciliation-pass-*.md`).
2. When a runtime PR appears in **≥3 consecutive** passes' deferral lists *and* is still open + green +
   mergeable, emit **one loud line** — on the run-report `⚑ Owner-decisions` line and in `current-state.md`
   ▶ Next action — e.g. *"6 dependabot dep-bumps (#1761–#1766) have idled ≥4 reconciliation passes; the
   execution routine should merge them or the owner should batch-auto-merge."*

That converts a silent re-defer into an **actionable hand-off** exactly once (idempotently, not every pass),
so a cross-lane orphan gets surfaced to a human/lane that can clear it instead of accumulating forever.

## Why it's worth having

It closes a real, *observed* leak in the two-lane model (docs-reconciliation vs. execution) with almost no
code, and it generalizes: any PR class the docs lane correctly can't own but that no other lane claims will
now get escalated rather than orphaned. Kit-portable — the same seam exists in any repo that runs a
docs-only reconciliation lane alongside an execution lane.
</content>
