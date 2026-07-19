# Idea: reconciliation cadence should exclude generated / automated PRs

> **Status:** `ideas` — session idea (Q-0089), captured 2026-07-19 (49th Q-0107 reconciliation pass,
> band-#2160). Not approved for implementation. · **Subsystem:** none (agent-workflow / meta)

## The observation

The Q-0107 reconciliation cadence fires when merged **PR numbers** cross a multiple of 30
(`scripts/check_reconciliation_due.py`, `STEP = 30`). It counts by *raw PR number*, not by
*substantive* work. On band-#2160 that produced a badly skewed ratio:

- **29 PRs merged (#2132–#2160). 23 of them (79%) were automated `bot/dashboard-refresh`
  PRs** — generated-artifact regenerations of `dashboard/data/dashboard.json` under the
  Q-0167 refresh loop. Only **6** were substantive (docs/CI/tooling).
- The prior band (#2100→#2130) was the same shape: 22 of ~29 were dashboard refreshes.

Because the dashboard-refresh loop mints PR numbers at machine speed, the cadence advances
~5× faster than substantive work warrants, and the **docs-reconciliation routine — which
costs owner attention (a `reconcile` issue, a self-merged PR, a THIN-flag the owner must
mentally reclassify)** — fires roughly every 1–2 days on a repo that is **intentionally
frozen as the superbot-next oracle** with essentially no substantive drift to reconcile.
The routine keeps running the full "plan the next 30-PR band" machinery over a band that is
79% automated noise.

## The idea

Make the cadence track **substantive merged PRs**, not raw PR numbers. Concretely: when
`check_reconciliation_due.py` counts merges to decide whether a band boundary was crossed,
**exclude PRs whose merge subject is a known generated/automated class** — at minimum the
`bot/dashboard-refresh` branch (and optionally grouped Dependabot bumps). The band boundary
then advances only as real work lands, so the reconciliation routine fires at a cadence that
matches actual doc-drift rate rather than artifact churn.

Two implementation shapes, cheapest first:
1. **Filter by merge-subject pattern** — the checker already parses merge subjects
   (`_MERGE_SUBJECT_RE`); add an exclusion list (`from menno420/bot/dashboard-refresh`,
   `dependabot`) so those merges don't advance the substantive counter. Marker semantics
   unchanged; only the *count that triggers a pass* changes. Small, stdlib, reversible.
2. **Separate "artifact" PRs from the ledger entirely** — a bigger change: stop counting
   generated-artifact PRs as ledgerable merges at all (they already collapse into one grouped
   Recently-shipped bullet per band). Out of scope for a first cut.

## Why it's worth having

- **Reduces false-alarm fatigue.** Today the owner sees a THIN flag or a reconcile issue on a
  frozen repo every couple of days and has to remember "that's just dashboard churn." A
  substantive-only cadence fires when there's genuinely something to reconcile.
- **Measurable.** The skew is concrete (79% / 76% of the last two bands were automated), so
  the fix's effect is measurable: bands would take ~5× longer to fill, matching the real work
  rate.
- **Aligned with the freeze posture.** With superbot frozen as an oracle, the *only* honest
  reason to run a reconciliation pass is real doc drift — which tracks substantive merges,
  not artifact regenerations.

## Reliability / kill-switch

`check_reconciliation_due.py` already carries a Q-0105 "unverified — delete if it misfires"
header. This change keeps that posture: it is a pure-stdlib pattern-exclusion, reversible by
dropping the exclusion list. Verify across a few bands that the excluded set matches only true
generated PRs before trusting the new cadence.
