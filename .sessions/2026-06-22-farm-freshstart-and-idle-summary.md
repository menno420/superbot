# 2026-06-22 — farm fresh-start faucet fix + "while you were away" idle summary

> **Status:** `in-progress` — born-red card (Q-0133); flips to `complete` as the final step.
> Continuation of the idle-farm session (#1328 merged). PR auto-merges on green (Q-0123).

## What I'm about to do

Two cohesive changes on the chicken farm's accrual read path:

1. **Bug fix (root, jumps the queue):** a brand-new farm's coop settles to **full** because
   `chicken_farm.eggs_updated_at` defaults to epoch 0 — `settle()` then measures elapsed time
   from 1970, so every new player can collect a free full coop (~40 coins) on first `!farm`.
   Fix at the root: normalize an uninitialized timestamp (`ts == 0`) to *now* in the workflow
   read path, so idle accrual starts from first contact (empty coop), not from 1970. One
   helper used by `get_state` / `collect` / `buy_chicken` / `upgrade_coop`. + a regression test.

2. **Idea → build (Q-0172):** the "while you were away" offline-progress summary I captured
   last session ([`docs/ideas/idle-game-offline-summary-2026-06-22.md`]). A pure
   `utils/idle_summary.py` (`format_duration` + `summarize_idle_gain`) that narrates the
   return-moment ("While you were away (2h 14m), your hens laid **17** eggs"); the farm panel
   shows it on open. Reuses the existing settle deltas; `format_duration` also replaces the
   farm menu's local `_fmt_wait` (de-dup, the rule-of-three start).

Will fill in Shipped / Verification / enders below before flipping to `complete`.
