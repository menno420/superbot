# 2026-06-24 — /btd6ref round accepts a round RANGE

> **Status:** `in-progress` — owner-reported (Discord): the `/round` value lookup
> is single-round only; he wants a range. Born-red card; flips to `complete` last.

> **Run type:** `manual · owner-directed`

Owner: *"about the /command round values etc, it seems now it's only possible to
ask for a single round, not a range."* True for `/btd6ref round` (param `number:
int`, single). `/btd6ref income` and `/btd6ref rbe` already take `start_round` +
`end_round` ranges (from #1404) — but neither gives the *combined* round-values
view, and `round` is the obvious command for it.

## What I'm about to do
- Add an optional `end_round` to `/btd6ref round` (+ `!btd6ref round`): single round
  keeps the detailed embed; a range renders a combined per-round table
  (round | RBE | cash | cumulative) + totals, via a new
  `_builders.build_round_range_embed` off `round_rbe` + `round_cash` (the same
  audited engines, so numbers match the income/rbe commands and the AI floors).
- Tests for the range embed + the single-round path still working.
