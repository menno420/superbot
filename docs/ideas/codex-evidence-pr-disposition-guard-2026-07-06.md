# Idea: codex/evidence-PR disposition guard

> **Status:** `ideas` · captured by the band-#1770 reconciliation pass (2026-07-06) · Sector S4 ·
> Disposable (Q-0105).

## The friction

The band-#1770 pass had to disposition **5 open Codex Gate V evidence PRs** (#1752–#1755 C2–C5, #1758
C1) whose deliverable docs were already **consumed** into merged corrections/synthesis docs
(#1756/#1759/#1767). The raw evidence PRs are neither stale-and-closable (their content is real evidence)
nor cleanly mergeable in a docs-only pass — they just sit open, and each reconciliation pass re-inspects
them by hand to decide "already folded in, or still needed?" The band-#1710 pass hit the same shape with
codex review docs #1695–#1699 (dispositioned a session later via the #1719 sweep).

## The guard

A warn-only checker (small disposable, `scripts/`) that flags an **open PR on a `codex/*` (or evidence)
branch whose added doc filename/path already appears referenced inside a doc that has since merged to
`main`** (e.g. a `*-findings-corrections-*.md` / `*-SYNTHESIS.md` that names or supersedes it). Output:
"PR #N's deliverable `C4-…md` is consumed into merged `…corrections…md` — likely merge-or-close, not
leave-open." It turns the hand judgment ("is this evidence already folded in?") into a per-pass signal so
the raw evidence PRs get an explicit merge-or-close decision instead of accumulating unreviewed across
bands.

## Why it's worth having

Same stdlib / advisory / disposable shape as the open-PR staleness classifier and the
reconcile-headline-sector-currency-check sibling. It closes a real recurring cost of the
verification-fleet workflow: an owner-launched Codex fan-out produces raw sub-report PRs faster than any
one lane merges them, and without a signal they quietly pile up. Low value if the fleet stops producing
raw PRs; disposable if it proves noisy (Q-0105).
