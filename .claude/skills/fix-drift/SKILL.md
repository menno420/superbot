# /fix-drift

The drift-on-sight pass (owner directive Q-0166): run the ledger/docs checkers, fix what's actually
drifted, and stop — no full reconciliation. Lets any session clean spotted drift fast.

## What this does

Runs the **reconcile** half of the Q-0107 pass (`docs/operations/autonomous-routines.md` STEP 2
"RECONCILE") *targeted at drift you have already spotted* — the ledger checker, the docs checker, and
a fix of what they flag — without doing a whole reconciliation pass or any planning. This is the
"fix it on sight" mechanism from `.claude/CLAUDE.md` § "Bugs first, durably" (Q-0166): docs/ledger
drift you can SEE is a bug -> fix it now, don't defer it to the next 30-PR pass. Wrapper around the
existing checkers + the reconcile procedure, not new policy.

> Scope brake: this is **docs-only** and *targeted*. The comprehensive every-30-PR sweep + planning
> stays the reconciliation routine's job (Q-0107/Q-0124). `/fix-drift` is for the specific drift in
> front of you (a wrong ledger entry, a clearly-missing older merge, a stale pointer, a rotted link).

## Invocation

```
/fix-drift
/fix-drift "current-state still says Last reconciliation pass #1050 but #1080 merged"
```

Optionally name the drift you spotted; otherwise the checkers find it.

## Instructions for Claude

### Step 1 — sync first

A stale clone is the #1 cause of "reconciling the wrong state". `git fetch origin` and make sure
you're reading current `main` before judging drift.

### Step 2 — run the drift checkers

```bash
python3.10 scripts/check_current_state_ledger.py --strict
python3.10 scripts/check_docs.py --strict
```

The ledger checker flags merged PRs missing from `docs/current-state.md` § Recently shipped; the docs
checker flags reachability / badge / staleness issues, stale links, wrong PR numbers, broken
references.

### Step 3 — fix what actually drifted

- **Missing merged PR in the ledger** -> **verify its #number against live GitHub first** (a
  false-green checker once matched only one merge-message style and missed 5 PRs — Q-0120), then add
  it to `docs/current-state.md` § Recently shipped (or fold it into an aggregated range entry).
- **Reachability orphan** -> usually one missing README / folio link; add it.
- **Stale pointer / wrong PR number / rotted link** -> correct it to the live target.

The one drift you **leave** is *benign newest-merge lag* — the 1–2 merges newer than the
`Last reconciliation pass: #N` marker, which the next reconciliation pass records (Q-0166). Drift
**older** than the marker is a bug -> fix it now.

> **A green check that contradicts visible evidence is a bug in the *check*, not a clearance**
> (Q-0120). If a checker reports clean but you can see the drift, verify the tool against ground truth
> before trusting its green.

### Step 4 — re-run + ship

Re-run both checkers to confirm green, plus `python3.10 scripts/check_quality.py --check-only`. Ship
the fix as a small docs PR (it auto-merges on green). Do **not** expand into a full reconciliation /
planning pass — that is a separate, routine-owned job.

### Notes

- Don't touch `disbot/` runtime code here — drift-fix is docs-only. A runtime bug you *notice* goes to
  `docs/health/bug-book.md` (OPEN) for the dispatch lane, not fixed in a drift pass.
- `/fix-drift` is the fast, surgical complement to the comprehensive `/session-close` documentation
  audit (Q-0104) and the routine's full reconciliation.
