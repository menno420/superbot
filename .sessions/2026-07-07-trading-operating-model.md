# 2026-07-07 — Trading operating model (Q-0251: decision ledger + sniper bucket + 3-way hybrid)

> **Status:** `in-progress`
> **Branch:** `claude/rebuild-plan-consolidation-c34c0b` (restarted from main after #1796)
> **Continues:** the 2026-07-07 consolidation conversation (PRs #1791–#1796)

## What is about to happen

The owner elaborated the trading repo's operating model live: (1) trades are **mock trades** —
document the decision, check the result after the decided time (no execution needed); (2)
backtest across multiple stocks, crypto eventually as *data* if helpful; (3) score strategies by
gain % over set time / set trade count; (4) rare-but-precise strategies (the 5-trades-no-losers
class) deserve a home despite tiny samples; (5) the eventual **3-way hybrid**: active trading /
swing trading / reserve-save sections, the reserve waiting for lucky moments or pre-decided entry
levels. Record as **Q-0251** + extend the capture doc's Part 3 with the strengthened design
(git-timestamped decision ledger as tamper-evident forward-testing; sniper bucket with
uncertainty-aware stats + notification wiring; the hybrid as a backtestable allocator layer with
pre-declared reserve-deployment rules).

## Close-out

_(to be written at close)_
