# Idea — planned-slice hit-rate tracker (the reconciliation queue's accountability metric)

> **Status:** `ideas` — raised by the band-#1380 Q-0107 reconciliation pass (2026-06-24).
> Lane: S4 (docs system) / S3 (the engine's tooling). Size: small, `ready`-adjacent (stdlib script + test).

## The problem

Every Q-0107 pass writes a §4 forward queue (slice → PR-lineage) and the *next* pass hand-counts how many
of those slices actually shipped — "~1/11 planned slices executed" (band-#1350), "2/12" (band-#1380). The
band-#1320 pass *proposed* measuring this "buffer-becomes-band" gap; three passes later it's still a prose
sentence re-derived by hand each time, which means:

- the count is **unverifiable** (an agent eyeballs the queue against the band's merges),
- it's **not trend-able** (no pass can say "the hit rate is rising/falling across the last 5 bands"), and
- the recurring conclusion ("the queue over-indexes on gated runtime lanes") stays an *impression*, never a
  measured fact the owner can act on.

## The idea

A tiny `scripts/check_plan_hit_rate.py` (stdlib, read-only, disposable per Q-0105) that, given a pass
record's §4 queue table and the next band's merged-PR list:

1. parses each slice row's `#NNNN` PR-lineage references (and the plan-doc it points at),
2. checks which of those PRs appear in the next band's actual merges (the ledger / git log), and
3. prints the **hit rate** — `executed / planned` — plus which named slices shipped vs. carried forward.

A pass would run it once on the *previous* pass's record (the band whose results are now known) and paste
the measured line into its §2 scorecard, replacing the hand-counted prose. Over several passes the numbers
accumulate into a trend the owner can read: *is the forward queue predictive of what gets built, or is it
aspirational backlog the bands route around?*

## Why it's worth having

It closes the loop the band-#1320 pass opened and the band-#1350 idea (new-subsystem follow-up tracker)
complements: that idea feeds the queue from *real shipped depth*; this idea *measures whether the queue
predicts the band*. Together they make the reconciliation queue self-auditing — the planning half of the
session-chain self-audit the workflow is built around. It's also genuinely small: one stdlib parser over
markdown tables we already author in a fixed shape, with the band-#1380 record as a ready first fixture.

## Honest caveat

The §4 tables are markdown authored by hand, so the parser must tolerate prose drift (a slice row may cite
PRs in prose, not a clean `#A · #B` cluster) — the same non-monotonic-cluster hazard `trim_recently_shipped.py`
already handles. Build it to read only the leading `#NNNN` references per row and warn (never fail) on a
row it can't parse, so it stays a convenience reporter, not a gate.
