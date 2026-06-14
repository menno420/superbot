# Idea — `check_current_state_ledger` should print each missing PR's merge-commit subject

> **Status:** `ideas` — capture, **not** a plan, **not** approval. Source code and the
> binding contracts win over this file. Small/safe grooming-lane candidate (a tooling
> convenience for the reconciliation routine).

## The friction (observed this pass)

`scripts/check_current_state_ledger.py --strict` reports *which* PR numbers are missing from
the ledger (e.g. the band-#820 pass started with "12 recent merged PR(s) not in
current-state.md": #803, #805, #806, #808, #810, #811, #812, #813, #814, #815, #816, #818).
But it prints **only the numbers** — so the reconciler's very next step is always a manual
`git log --grep "Merge pull request #N"` loop to recover *what each PR actually did* before it
can write an honest `Recently shipped` entry. The band-#820 pass ran exactly that loop by hand.

## The improvement

When the checker lists a missing PR, also print the **merge-commit subject (and the first
content-commit subject)** for that PR number, e.g.:

```
  - #814  ci: cut code-quality cost — concurrency cancel, caching, parallel pytest
  - #815  test: make suite parallel-safe, re-enable pytest -n auto (~3x CI speedup)
```

It already walks `git log` to build the merged-PR set, so the subject is in hand — this is a
formatting change, not new data-gathering. It also gracefully covers the gaps a reconciler
otherwise has to investigate (a number with no merge commit = a closed/unmerged PR or a
`continue` issue — the checker could annotate `(no merge commit — closed/unmerged?)`).

## Why it's worth having

- It collapses the single most repetitive manual step of every Q-0107 reconciliation pass
  into the report the routine already reads first.
- It reduces the risk of **mis-attributing** a ledger entry (writing the wrong scope for a PR
  number), because the subject is shown next to the number at the point of need.
- It is a runtime-lane (`scripts/`) change, so it is **out of scope for a docs-only
  reconciliation self-merge pass** — captured here for a tooling session, not actioned now.

## Caveat / disposability (Q-0105)

A convenience for the reconciler, not a correctness guard — if it ever proves noisy or the
subject-extraction is unreliable across squash/rebase merge styles, drop it. Pairs naturally
with the deeper [`ledger-checker-range-scope-2026-06-13.md`](./ledger-checker-range-scope-2026-06-13.md)
fix (both touch the same script).
