# Idea — scale the ledger-checker window to "merges since the last reconciliation marker"

> **Status:** `ideas` — capture, **not** a plan, **not** approval. Source code and the
> binding contracts win over this file. Small/safe grooming-lane candidate (a tooling
> precision tweak for the reconciliation/`session-close` loop).

## The friction (observed this session, 2026-06-19, band-#1080 reconciliation pass)

`scripts/check_current_state_ledger.py` checks a **fixed window** of the last `DEFAULT_WINDOW = 15`
merged PRs. But at burst velocity a single band between reconciliation passes can exceed that: this
pass found the band #1060→#1094 had **~21 merges absent** from the ledger, yet the window-15 strict run
flagged only **13**. The other ~8 (#1064, #1068, #1070, #1072, #1075, #1077, #1079, plus older edges)
were caught **only because the routine manually per-PR-grepped the whole band** — exactly the manual
step the checker is supposed to replace. A future fast band that nobody hand-greps would silently leave
older real drift unrecorded while the guard reported "last 15 merged PRs all present ✓" — a near-miss of
the same false-green class the range-scope fix (`ledger-checker-range-scope-2026-06-13`) already closed
for ranges.

## The improvement

Make the default window **dynamic**: read the `Last reconciliation pass: PR #M` marker from
`current-state.md` and check **every merge newer than #M** (the actual band the next pass is responsible
for), not a fixed 15. Fall back to 15 only if the marker is unparseable. Concretely:

- Add a `_marker_pr()` helper that greps the `Last reconciliation pass:` line for `#(\d+)`.
- In `find_missing`, when `--window` is not explicitly passed, set the effective window to
  `max(DEFAULT_WINDOW, <merges since #M>)` so a slow band still gets the floor of 15 and a fast band
  gets full band coverage.
- Keep `--window N` as an explicit override (unchanged).

This makes the strict run **self-sizing to the cadence**, so the reconciliation routine no longer needs
the by-hand full-band grep, and `/session-close`'s strict gate can't false-green on a band that outran
15 merges.

## Why it's worth having

Directly removes a manual step the routine ran this pass and closes a structural false-green window. Same
spirit as the existing `ledger-guard-benign-lag-vs-drift` and `range-scope` precision tweaks — both
already in the ideas backlog — but addresses the *size* of the window rather than its *contents*.
Stdlib-only, disposable (Q-0105), test with a marker-far-behind fixture.
