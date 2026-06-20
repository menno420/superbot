# Session — funny-franklin · BUG-0016 root-cause hardening (single-source reconcile-issue body)

> **Status:** `complete`

**Run type:** routine · dispatch
**Branch:** `claude/funny-franklin-qpth6s`

## Context (after a re-sync mid-run)
Empty scheduled dispatch fire. Started on **BUG-0016** (reconciliation-trigger stale
cadence copy). Mid-run a long gap elapsed and `main` advanced #1102 → #1139; a concurrent
dispatch run had already FIXED BUG-0016 (corrected the strings) — so my string-fix slice
was redundant. I rebased onto latest main and kept only the **novel root-cause** half:
that run explicitly left the drift class ("optionally have the checker be the single source")
unbuilt.

## What this PR does
Eliminate the BUG-0016 drift class at the root: the canonical reconcile-issue body now lives
in `scripts/check_reconciliation_due.py` (`issue_body()`, built from `STEP`, exposed via
`--issue-body`), and `reconciliation-trigger.yml` **echoes** it instead of carrying its own
hardcoded copy. The cadence numbers (STEP=30, full-band) can never desync between the firing
logic and the issue prose again. Tested.
