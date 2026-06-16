# Session — BTD6 round-range cash comparison floor (AI §7.5)

> **Status:** `in-progress`

**Branch:** `claude/magical-rubin-7iavf2` · **Date:** 2026-06-16 · scheduled dispatch (empty work
order → advance the next plan slice)

## What I'm about to do

The live ▶ NEXT buildable plan-first lane is **the AI §7 next workflow family**. §7.5 (multi-entity
comparison) has shipped its **cost** members — tower-vs-tower (#946) and by-difficulty (#950). The
plan lists two members still unbuilt: **paragon degree/resource** and **round-range cash**. I'm
building the **round-range** member — it has clean, fully-deterministic data (`round_cash` already
owns inclusive-range cash for both the standard and ABR round sets), so it ships under Q-0048 with no
prod-check, exactly like the sibling cost builders.

Question shape: "which earns more cash, rounds 20-40 or 40-60?" — rank the total cash of **two or
more** round ranges. This is the §7.5 comparison member of the BUG-0009 "grounded values, wrong
assembly" class: each per-round figure is grounded, but a model can mis-state *which range earns
more / by how much*, and the value-only faithfulness guard can't catch a mis-ranking.

Plan (mirrors #946/#950 exactly, contained + test-covered):
- `btd6_data_service.compare_round_ranges(ranges, *, roundset="default")` — the §7.5 round-range
  rank/diff primitive; price each inclusive range once via the existing `round_cash`, dedup
  normalized ranges, rank by cash **descending** (the question asks which earns *more*), fail closed
  (<2 distinct priceable ranges).
- `btd6_context_service.deterministic_round_range_comparison_reply` — high-precision floor: an
  earning-comparison cue (`more cash`/`earn more`/`which … money` + comparison signal) + a cash noun
  + **two or more** parsed round ranges; ABR cue → the ABR round set. `None` otherwise (a single
  range is the round-cash workflow's job — they stay non-overlapping on range count, and the floor
  short-circuits before the workflow ever runs). Appended to `deterministic_btd6_list_reply`.
- Tests: firing (2 ranges / 3 ranges / single-round endpoints / ABR cue / spread / tie), and the
  negatives (one range → defer to workflow, no cash cue, no comparison signal, strategy).

If capacity remains: assess the **paragon** §7.5 member as a second slice.
