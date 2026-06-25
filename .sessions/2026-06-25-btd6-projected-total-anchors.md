# 2026-06-25 — BTD6 eval anchors: projected-total convention (S2 P1-1)

> **Status:** `in-progress`

## Goal (dispatch run, empty scheduled fire → advance the next plan slice)

Empty scheduled fire, no open PRs. Per the routine: advance the next **▶ startable**
slice. Picked up the explicit ▶ Next handoff from the previous S2 P1-1 run
(`2026-06-25-btd6-fixture-anchor-guard.md`, #1458): *"anchor the remaining range-cash
convention figures after nailing the exact cumulative/starting-cash convention (a naive
`round_cash(1, N)` is ~$10 off)."*

## What I'm about to do

The four **range** figures (rounds 60-68 / 50-60 / 54-70 / ABR 25-83) are already
anchored via `_range_cash(start, end)`. The genuinely-uncovered rubric truths are the
**projected running totals** the same cases assert ($21,187.90 / $39,840 / $56,318.70 /
$119,315.30 ABR). The previous run left them unanchored believing the convention wasn't
cleanly reproducible — but the "~$10 off" came from trying `round_cash(1, N)`
(cumulative-from-round-1), which is the *wrong* accessor. Verified empirically: each
projected total is exactly `stated_starting_cash + round_cash(start, end).range_cash`
(8094+13093.9=21187.9 · 20000+19840=39840 · 26932+29386.7=56318.7 · 5443+113872.3=119315.3
— all exact). So the convention IS nailed: **projected_total = stated_start + range_cash**,
the stated start being the user-message constant in each case (NOT cumulative from round 1).

Slice 1: add a `_projected_total(...)` derive helper + four projected-total anchors, and
correct the module curation note (the convention is reproducible; the only deliberately-
unanchored rubric numbers are the *distractors* the rubric tells the judge to reject
— $71,315.20, $107,164.60 — and the bare user-supplied starting figures, which are not
data-derived truths).

Offline test-only change (no `disbot/` runtime). Self-mergeable.
