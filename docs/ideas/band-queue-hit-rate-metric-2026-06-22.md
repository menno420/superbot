# Idea — measure whether the planned next-band queue actually predicts the band

> **Status:** `ideas` — capture only, **not a plan, not approval**. Source + binding contracts win.
> **Subsystem:** none (agent-workflow / meta — the reconciliation loop).

## The observation

Every Q-0107 reconciliation pass plans a "next full band" (~30 slices of buildable work, depth ≥
cadence per Q-0164). But almost every *subsequent* pass then records the same finding in prose:
"the buffer became the band" / "only N of the planned slots executed" — band-#870 (~3/10),
band-#900 (slot-2 over-delivered while the rest was buffer), band-#1260 ("only B1 executed"),
band-#1320 (a full unplanned **fishing minigame** arc + role-management + dependabot dominated; the
planned A1–E3 queue mostly carried forward untouched). The pattern is real, repeatedly documented,
and *qualitative only* — no pass has ever put a number on it.

## The idea

Extend `scripts/band_pr_status.py` (which already groups a band's merged PRs by theme for the
`--themes` skeleton) with a **`--queue-hit-rate`** mode: given the previous pass record's §4 queue
(the slice table) and the band's actual merged PRs, emit one line —

```
band-#1320 queue hit-rate: 2/11 planned slices shipped (18%) · 6 unplanned PRs became the band
```

Track that one number in each pass record's §2 (band scorecard). After a handful of passes the
series itself is the signal: if the hit-rate stays low (it visibly does), that is **data-driven
evidence** that deep 30-slice forward planning over-invests, and the owner can decide to shift the
cadence toward a lighter, more reactive queue (plan ~1 band's *highest-value* lanes, not pad to 30).
If it climbs, planning-ahead is paying off and should stay. Either way the owner learns it from a
metric, not from re-reading ten prose retrospectives.

## Why it's worth having

- It turns the single most-repeated qualitative finding in the pass records into one decision-grade
  number — the natural sibling of `band_pr_status.py --themes` (#1271), the trim actuator (#1206),
  and the open-PR staleness classifier idea (2026-06-22): the pass keeps gaining machine help for
  the parts that were pure manual judgment.
- It is cheap and stdlib (parse the prev pass §4 table + `git log` the band), warn-only, disposable
  (Q-0105) — no runtime risk, docs/tooling only.
- It directly serves the loop's purpose: *is the planning ritual earning its keep?* is exactly the
  kind of self-audit the reconciliation routine exists to perform.

## Not this

Not an *enforcement* gate — a low hit-rate is information, never a failure. The buffer-becoming-the-
band is often the *right* outcome (owner-steered work outranks a stale queue, Q-0124). The metric
just makes the trade-off visible.
