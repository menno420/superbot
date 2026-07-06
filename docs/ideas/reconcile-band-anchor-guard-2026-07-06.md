# Idea — reconcile-band anchor guard (a checker for the three-restatement band number)

> **Status:** `ideas` · captured 2026-07-06 (35th Q-0107 reconciliation pass, band-#1740, Q-0089).
> **Class:** workflow / tooling · **Owner-aligned:** yes (extends the "enforce, don't exhort" guard
> family, Q-0132/Q-0194). **Size:** S (one stdlib checker + a test).

## The friction

Every reconciliation pass hand-edits the **same band number in three places** in `current-state.md`:
1. the `**Last reconciliation pass:** PR #N` marker block,
2. the ▶ Next-action **S4 sector table row** (`Nth pass done (band-#N); next recon at #N+30`),
3. the "due once merged PRs cross **#N+30**" line (restated in both `current-state.md` and
   `current-state/S4-docs.md`).

These are four restatements of two derived facts (the just-finished band, and the next-due boundary).
`check_current_state_ledger.py` catches a *missing PR*; nothing catches these four drifting apart. It
is exactly the class Q-0120's #763 false-green warns about — a hand-maintained restatement with no
detector. This pass touched all four by hand; a slip in any one silently misstates project state until
a human notices.

## The guard

A tiny read-only checker (`scripts/check_recon_marker_consistency.py`, stdlib, disposable per Q-0105):
parse the three/four anchors, assert the marker band `N`, the "pass done (band-#N)", and the "next
recon at #N+30" / "cross #N+30" numbers are mutually consistent (marker = latest, next = marker + 30).
Warn-only first (like `check_dashboard_data --drift`), graduate to a `check_docs` sub-check once proven
across a couple of passes. Costs nothing on green; fails loudly the first time a pass forgets one of
the four edits.

## Why it's worth having

The reconciliation routine is the highest-frequency editor of these anchors, so a marker/next-due drift
is both likely and invisible — precisely the self-catching-its-own-mistakes goal of the guard family.
Cheap, docs-scoped (free to ship, no owner gate), and it removes a recurring manual-consistency chore
from every future pass.
