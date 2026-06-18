# 2026-06-18 — Repo consistency linter PR 1 (harness + edit-in-place rule) + ledger reconcile

> **Status:** `in-progress`

## What I'm about to do
Scheduled dispatch (no work order). The ▶ Next action's fishing reconciliation
(#1039/#1041) is **already merged** — verified against `main`; the live ledger
line is stale. So this run:

1. **Bugs-first ledger fix (Q-0166):** reconcile the 4 merged PRs the SessionStart
   banner flagged (#1038–#1041) into `current-state.md` § Recently shipped and
   repoint the stale ▶ Next action line (it still calls the fishing reconciliation
   "in flight").
2. **Build PR 1 of the owner-directed repo-consistency-linter (Q-0170):** the
   `scripts/check_consistency.py` harness + rule 1 (edit-in-place), warn-only,
   modeled on `check_architecture.py`, with the `consistency_exceptions.yml`
   allowlist + positive/negative test fixtures. Plan:
   `docs/planning/repo-consistency-linter-plan-2026-06-17.md`.

Will flip this card to `complete` as the deliberate final step.
