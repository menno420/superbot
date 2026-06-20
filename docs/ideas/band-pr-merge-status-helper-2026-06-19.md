# Reconciliation helper: classify a band's PRs as merged / closed-unmerged / open

> **Status:** `historical` ✅ **SHIPPED 2026-06-20** as `scripts/band_pr_status.py` +
> `tests/unit/scripts/test_band_pr_status.py`, wired into the reconciliation routine's STEP 2
> (`docs/operations/autonomous-routines.md`). Pure `classify_band()` core; git for merged-on-main +
> the `check_loop_health.py` gh→REST fallback for the closed-unmerged/open half (degrades to a
> labelled note, never hard-fails). Verified against live GitHub on the band-#1170 band (#1173–#1180
> merged, #1172 open, #1171 = the reconcile *issue*). Disposable (Q-0105). Original idea body kept
> below. Session idea (2026-06-19, Q-0089, from the band-#1140 reconciliation pass).
> **Subsystem:** operations / tooling (the reconciliation routine). Source + binding contracts win.

## The gap this pass hit

The reconciliation routine's ledger step relies on `check_current_state_ledger.py`, which greps
`main` for merge-commit / squash subjects (`Merge pull request #N`, `(#N)`) to find merged PRs not yet
in the ledger. That works for the *recording* step, but it **cannot tell a closed-unmerged PR apart
from a genuinely-missing merged one**. This pass had to verify by hand — via `list_pull_requests` +
`git branch --contains` + reading squash subjects — that **#1133 was superseded by #1128 and closed
*unmerged*** (so it correctly gets no ledger entry), while #1127/#1130/#1131/#1132/#1134–#1140 were
genuinely merged and missing. That manual cross-reference is exactly the #763-class false-green risk
the Q-0120/Q-0181 ground-truth discipline warns about: a tool that *looks* authoritative but silently
omits a case the human then reconstructs ad-hoc.

## The idea

A small stdlib **`scripts/band_pr_status.py`** that takes the reconciliation marker (`--since #N`) and,
for every PR number from there up to `HEAD`, prints a one-line **merge classification**:

- **merged** — a squash/merge commit for `#N` is reachable from `main` (the branch head is an ancestor
  of `main`, or a `(#N)` / `Merge pull request #N` subject exists on `main`);
- **closed-unmerged** — the PR is closed but its head is *not* reachable from `main` (the #1133 case);
- **open** — still open (cross-checked against `list_pull_requests`).

Output is a table the routine pastes straight into the pass record's §1 — so the "which PRs need a
ledger entry" decision is **deterministic and auditable**, not a per-PR hand check. It makes the
reconcile ledger step reproducible and removes the one manual judgement call that this pass (and the
#763 false-green) got wrong-by-omission elsewhere.

## Why it's worth having

- **Closes a real ground-truth gap** the routine hits every pass (Q-0120/Q-0181): merged-vs-closed is
  currently a manual call.
- **Cheap + disposable** (Q-0105): stdlib + `git` + one MCP/`gh` read; read-only; delete if it proves
  noisy. Pairs naturally with the existing `check_current_state_ledger.py` (could even merge into it as
  a `--band-status` mode rather than a new script — an executor decides at build time).

→ relates `scripts/check_current_state_ledger.py` · the reconciliation routine
(`docs/operations/autonomous-routines.md`) · Q-0107 (reconciliation) · Q-0120 (verify vs ground truth)
· Q-0181 (ground-truth audit) · the `loop-health-gh-unavailable-fallback` idea (sibling control-plane
read-fallback).
