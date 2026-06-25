# 2026-06-25 — BTD6 eval anchors: projected-total convention (S2 P1-1)

> **Status:** `complete` — ready to merge (Q-0133). Run type: routine · dispatch.

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

## What shipped (PR #1460)

- `tests/evals/test_btd6_grounding_anchors.py`: a `_projected_total(start_cash, start,
  end, roundset)` derive helper + **four** projected-total `Anchor`s
  (`8094+13093.9=21187.9` · `20000+19840=39840` · `26932+29386.7=56318.7` ABR
  `5443+113872.3=119315.3`). Each now carries both drift directions (data drift +
  rubric-prose drift), same as the existing range/rubric anchors.
- Corrected the module curation note: the convention IS cleanly reproducible
  (`total = stated_start + range_cash`, the stated start being the user-message
  constant — NOT cumulative-from-round-1; a naive `round_cash(1, N)` is "~$10 off"
  only because it's the wrong accessor). The numbers that *stay* unanchored are now
  named precisely: the two distractors the rubric tells the judge to reject
  ($71,315.20, $107,164.60) and the bare user-supplied starting figures (inputs, not
  data-derived truths).

## Verification

- `tests/evals/test_btd6_grounding_anchors.py`: **42 passed** (was 34 — +8 = 4 anchors
  × 2 directions).
- `python3.10 scripts/check_quality.py --full`: **12519 passed, 48 skipped, 2 xfailed**
  (green).
- `python3.10 scripts/check_architecture.py --mode strict`: **0 errors** (4 pre-existing
  `baseview_inheritance` WARNs only; test-only change touches no `disbot/`).
- `check_docs.py` / `check_consistency.py`: green via `--check-only`.

## Drift cleanup (bugs-first)

Removed a stale claim file `docs/owner/claims/claude-funny-franklin-1318v3.md` — its
session (the #1458 fixture-anchor run) closed and merged; zero open PRs confirms it.

## 💡 Session idea (Q-0089)

**Distractor "negative anchor" guard.** The eval set documents distractors the judge
must REJECT ($71,315.20 = the from-round-1 cumulative mislabel; $107,164.60 = the
standard-set figure given as the ABR answer). Today nothing pins that those values
stay *un*-reproducible — if a future data/seed change ever made a distractor
accidentally equal a clean `btd6_*_service` derivation, the case would silently stop
guarding the exact confusion it was written for (a grounded-looking wrong answer). A
tiny `NEGATIVE_ANCHOR` table (`value`, `case_id`, `derivation-that-must-NOT-equal-it`)
asserting each documented distractor is **not** cleanly derivable would close that
blind spot — the inverse of the positive anchors, cheap, offline. Dedup-checked
`docs/ideas/` + this file's history: distinct from #1458's *coverage-report* idea
(which inventories *missing* positive anchors; this guards *intentional* non-anchors).

## ⟲ Previous-session review (Q-0102)

Prev = `2026-06-25-btd6-fixture-anchor-guard.md` (#1458, the fixture-drift anchor
guard). **Did well:** genuinely careful curation — it refused to anchor figures it
couldn't derive exactly (Q-0120 discipline) rather than asserting a possibly-wrong
truth, and it left a precise ▶ Next handoff that made *this* run trivial to pick up.
**What it missed:** its "naive `round_cash(1, N)` is ~$10 off" probe used the wrong
accessor — the projected totals are `stated_start + range_cash`, not a
cumulative-from-round-1 figure — so it under-covered four cleanly-derivable truths out
of caution. The caution was the right *instinct* (better an honest gap than a lying
guard); the gap was just resolvable. **System improvement it surfaces:** the anchor
helpers hardcode the stated-start constant (`8094`, …) separately from the case's
`user_message` — a future guard could parse the start out of the case's prompt so the
anchor and the prompt can't silently drift apart. (Captured as a follow-on thought, not
built this run — small, advisory.)

## 📤 Run report

- **Did:** empty scheduled fire → advanced S2 P1-1 by closing #1458's ▶ Next handoff:
  anchored the four BTD6 projected-total eval figures after nailing the
  starting-cash convention (`total = stated_start + range_cash`) · **Outcome:** shipped
- **Shipped:** #1460 — `_projected_total` helper + 4 projected-total anchors +
  corrected curation note; offline test-only; CI green (12519 passed)
- **Run type:** `routine · dispatch` (Q-0165)
- **⚑ Owner decisions needed:** `none`
- **⚑ Owner manual steps:** `none`
- **⚑ Self-initiated:** `none` (advanced an existing plan slice / explicit handoff, S2
  P1-1; no new idea promoted to a plan/build this PR)
- **↪ Next:** S2 P1-1 — (a) #1458's **eval-anchor coverage report** idea (inventory every
  numeric token in `cases.py` rubrics + fixtures, report which lack an Anchor/FixtureAnchor,
  with an allowlist for distractors + user-inputs) is the natural next tooling slice; (b)
  the **distractor negative-anchor guard** above; live `llm_judge` battery + absence-guard
  Layer B stay creds-/review-gated.

