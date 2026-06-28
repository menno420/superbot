# Idea — a "queue-staleness age" tag per §4 forward-queue slice

> **Status:** `ideas` — captured 2026-06-28 (band-#1530 reconciliation pass, Q-0089).
> Subsystem: S4 docs-system / S3 self-improving-workflow tooling.

## The gap

Each Q-0107 pass carries the §4 forward-queue (slices A1, A2, B0, B1, C1…) forward, band after band.
The band-#1500 pass added the **queue-execution-rate** line — *how many* named slices a band executed
(0 of 16 for band-#1530). That tells you the queue isn't moving, but not **which slices are stuck or
how long they've been stuck**. A slice carried unchanged across many bands is one of two things:

- **genuinely blocked** — it should be moved to the gated/owner-paced list, not left looking buildable; or
- **chronically deprioritised** — the owner should learn his forward queue no longer reflects what the
  fleet actually builds, so he can re-order it or drop the dead slices.

Today both look identical: a row in the §4 table with no history.

## The idea

Tag each §4 slice with a one-token **carried-since** age, e.g. `A1 … (carried since band-#1380)`. The
pass sets it when a slice first appears and leaves it untouched while the slice is carried; when a band
finally executes the slice, it drops off the queue and the tag with it. Reading down the table, a cluster
of `carried since band-#1380` rows is an immediate, legible signal that the queue has drifted from
reality.

## Why it's worth having

- It converts the band-#1500 execution-rate *count* into a per-slice *history* — the difference between
  "the queue didn't move this band" and "this specific slice has been ignored for five bands."
- It gives the owner an early, low-noise prompt to re-prioritise or prune, instead of the queue silently
  accreting dead slices that make the backlog look deeper than it is.
- It is the manual precursor to **E3** (the planned-slice hit-rate tracker): once the age is written by
  hand for a few passes and proves useful, the same `completion_scoreboard`-style reader that E3 builds
  can compute it automatically from the pass-record history.

## Cost / shape

Pure docs convention to start (one token per slice row in the pass record's §4 table). No code until E3
graduates it. Disposable (Q-0105) if it proves noisy.
