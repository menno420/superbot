# 2026-07-06 — Verify PR #1743 + CodeQL stuck-scan watchdog

> **Status:** `in-progress` — born-red hold (Q-0133). Flip to `complete` as the deliberate final step.

## What this session is doing

Continuation of the CI-setup arc (PRs #1737 / #1739 / #1743). Two parts:

1. **Verify** the previous session's (PR #1743) `check_ci_coverage.py` self-silencing fix is correct.
2. **Continue** the ranked handoff (`docs/planning/ci-followups-handoff-2026-07-05.md`) — build the
   next offline-buildable items:
   - the shared idempotent **`owner_alert`** helper (the PR #1743 Q-0089 session idea — the explicit
     prerequisite the CodeQL watchdog "reuses `open_alert_issue`'s idempotent pattern");
   - the **CodeQL stuck-scan watchdog** (handoff item #2 / design §C.2 / plan A10) that bounds the one
     residual the merge-protection ruleset leaves open (a scan that starts then errors/hangs);
   - the **alerting-only leg** wired into the non-required `ci-rerun-watchdog.yml`.

_(Body — verification result, shipped, findings, run report — written as the deliberate final step.)_
