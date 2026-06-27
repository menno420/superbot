# Idea — a per-band "queue-execution rate" line in each reconciliation pass record

> **Status:** `ideas` · captured 2026-06-27 (band-#1500 reconciliation pass, Q-0089)
> **Subsystem:** S4 docs-system / the reconciliation routine
> **Lane:** `ready` (small, docs+tooling, no runtime) — precursor to E3 (planned-slice hit-rate tracker)

## The observation

Three of the last four reconciliation bands (#1410, #1470, #1500) executed **zero** named §4
forward-queue slices. The work was real and valuable — owner-directed correctness arcs (BTD6
QA-accuracy this band) and autonomous hardening / self-improving-workflow guards — but **none of it
was a slice the previous pass had named in its §4 "next band" table.**

That is not a failure: the maintainer steering a band toward a live bug is exactly what the workflow
exists to support (Q-0172, the idea gate is gone; bugs-first jumps the queue). But it *is* an
**invisible signal**. Each pass re-plans and carries forward the same §4 queue (Project Moon seam,
giveaway PR 1, hub-rendering, card-engine next surfaces, botsite React PR 2 …) and nobody tracks how
often a named slice actually ships. The queue could be stale, mis-prioritised, or genuinely blocked,
and the pass record would read identically either way.

## The idea

Add one **computed line** to each pass record's §2 scorecard:

> **Queue slices executed this band: 0 of 16 named (§4 carried forward intact).**

Derived mechanically: take the prior pass's §4 slice IDs (A1, A2, …), check each against the band's
merged PRs, count the hits. It makes the planning-vs-reality gap legible **across** bands — a reader
(or the owner) sees at a glance whether the queue is being drained, ignored, or re-planned in circles.

## Why it's worth having

- **It's the manual version of E3** (the planned-slice hit-rate tracker idea, band-#1380). Writing the
  line by hand for a few passes proves the metric is real and worth automating before building the
  checker — the same "prove it manually, then build the guard" pattern that produced
  `check_reconcile_marker.py` (#1495) from the band-#1470 marker-conflation observation.
- **It surfaces a decision for the owner early:** if queue-execution stays at 0 for several bands, the
  queue itself needs attention (re-prioritise, unblock, or accept it's a backlog the fleet picks from
  opportunistically rather than a plan it executes top-down). Right now that conclusion is buried in
  prose each pass.
- **Near-zero cost:** one line, computed from data the pass already has open.

## Smallest first step

Add the line to the next pass's §2 by hand (compare prior §4 IDs to the band's PRs). If it reads
useful after 2–3 passes, promote E3 to build the checker that computes it.
