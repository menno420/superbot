# Idea — a reconciliation-band coverage linter (prose PR-list vs. git merged set)

> **Status:** `ideas` — raised by the band-#2340 Q-0107 reconciliation pass (2026-08-05, Q-0089).
> Lane: S4 (docs system) / S3 (engine tooling). Size: small (one stdlib+git checker + test).

## The problem

Under oracle-freeze the reconciliation pass is now almost entirely mechanical: each pass hand-writes
two grouped Recently-shipped bullets — one **dashboard-refresh** list and one **non-dashboard** list —
whose job is to *cover every merged PR in the band* (`prev marker+1 … new marker`). Today nothing
verifies that coverage:

- `check_current_state_ledger.py` only asserts the **last 15 merged PRs are present** somewhere in the
  ledger — it does not check that a *specific band's* grouped entries are complete.
- `check_reconcile_marker.py` (shipped 2026-06-27) verifies the **marker number** is the reset target,
  not the pass's own PR — but says nothing about the grouped PR-list prose.
- `check_docs.py` verifies **reachability/badges/ratchet**, not PR-number completeness.

So a pass can silently drop a PR from the grouped list, double-count one, or mis-split dashboard vs.
non-dashboard, and every checker stays green. At ~20–30 PRs/band, all hand-transcribed, this is a real
drift class the current guards are blind to — exactly the "a green check that contradicts the evidence
is a bug in the check" gap (Q-0120).

## The guard

A small offline checker `scripts/check_reconcile_band_coverage.py` that, given the previous marker and
the new marker (both already in `current-state.md`):

1. Computes from `git log` the set of PR numbers merged in `(prev, new]` (merge-commit `#N` parse, the
   same source `check_current_state_ledger.py` already uses).
2. Extracts the PR numbers named in the **two newest grouped bullets** of § Recently shipped.
3. Asserts the prose set ⊇ the git band set (every merged PR is accounted for), reports any **missing**
   or **extra** numbers, and — as a soft signal — flags a PR that appears in the *dashboard* bullet but
   whose branch head is not `bot/dashboard-refresh` (mis-split).

Keep it a **standalone disposable** (Q-0105 header: provenance + "delete if noisy over a few passes"),
sibling to `check_reconcile_marker.py`, not folded into the ledger checker. Wire it into
`/session-close` (or the reconcile routine's verification block) as warn-only first, promote to a CI
gate only once it's proven quiet across a few passes.

## Why it's worth having

It closes the loop the other three guards leave open: the pass's *narrative completeness* becomes
machine-checked instead of trusted, so the ledger stays a faithful index of what merged even as the
bands are dominated by near-identical generated-artifact PRs that are easy to mis-count by hand. It also
makes the pass faster — the agent stops eyeballing 20+ PR numbers and lets the checker confirm the split.
