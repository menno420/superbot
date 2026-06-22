# 2026-06-22 — NEW idle egg/chicken farm game

> **Status:** `in-progress` — born-red card (Q-0133); flips to `complete` as the final step.
> Owner-directed task ("Idle egg/chicken farm") → build it end-to-end (Q-0191 merge-immediately).
> PR auto-merges on green (Q-0123) once the card flips.

## What I'm about to do

Stand up a brand-new **idle egg/chicken farm** game — the bot's first *idle* (accrue-over-time)
activity, complementing the active games (mining grid, fishing, creatures). The idle mechanic
reuses the proven **`settle()` lazy-accrual pattern** (stored value + timestamp, computed from
elapsed time — no background ticker, no Redis: ADR-001/002): hens lay eggs over time, capped by
coop capacity, so a returning player banks idle progress without a scheduler.

The loop:
- **Collect** settled eggs → coins (a modest faucet) + game XP.
- **Buy chickens** (coin sink, price scales) → faster lay rate.
- **Upgrade coop** (coin sink) → larger egg cap → bank more while idle.

Mirrors the fishing arc's layering exactly: pure domain (`utils/farm/`) · audited write boundary
(`services/farm_workflow.py`, RS02/Q-0071 one-txn-per-op, economy legs via `*_in_txn`) · CRUD
(`utils/db/games/farm.py`) · views (`views/farm/`) · cog (`cogs/farm_cog.py`) · `SUBSYSTEMS` entry
(Games hub child) · Explore-world registration · shared game-XP (`GAME_FARM`).

Will fill in Shipped / Verification / enders below before flipping the card to `complete`.
