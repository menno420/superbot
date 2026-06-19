# 2026-06-19 — Dispatch: BUG-0016 stale cadence copy + follow-ons

> **Status:** `in-progress`

## Arc

Scheduled dispatch, no work order → advance the next plan slice. The website two-site
split's buildable wave is shipped (#1109 + back-half #1112…#1118); the remaining website
slices are owner-paced rollout / security-review-gated. So **bugs first**: the bug book has
**BUG-0016 OPEN** — the `reconciliation-trigger` workflow's issue body + header comment carry
stale cadence copy ("multiple-of-20" / "next ~9 PRs") that drifted past Q-0134 (cadence → 30)
and Q-0164 (plan the full band, not ~9). The bug book itself scopes it as a one-PR string fix
for a dispatch routine.

About to: fix the stale strings in `.github/workflows/reconciliation-trigger.yml`, mark
BUG-0016 FIXED, then take a second ungated lane (consistency-linter rule extension or a small
stdlib guard) if capacity remains.

## Shipped

_(pending)_

## 📤 Run report

_(pending — flipped to complete as the final step)_
