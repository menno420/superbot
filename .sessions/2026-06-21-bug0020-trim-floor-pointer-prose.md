# 2026-06-21 — BUG-0020: trim_recently_shipped floor-pointer prose contamination

> **Status:** `in-progress` — born-red session card (Q-0133). Will flip to `complete` as the
> deliberate final step once CI is green.

> **Run type:** routine · dispatch

## What I'm about to do

Fix **BUG-0020** (OPEN, tooling) at the root: `scripts/trim_recently_shipped.py`'s floor-pointer
recompute scans the *whole* archive for `#N` and takes min/max over **all** matches, so it picks up
stray references in prose (a `band-#1170` parenthetical note, `#1` rank notation) and writes a wrong
`Older merges (#HIGH … #LOW)` span. The fix: recompute the span from **archived bullet headers only**
— each bullet's leading PR-reference cluster (so grouped non-monotonic bands like `#690 · #721` still
contribute their newest member), never free-floating `#N` in prose. Ships with a regression test that
feeds an archive whose prose carries a stray high/low `#N` and asserts the span ignores it.

Contained, reversible, test-covered, docs/tooling only (no `disbot/` runtime) → self-merge on green
(Q-0113).
