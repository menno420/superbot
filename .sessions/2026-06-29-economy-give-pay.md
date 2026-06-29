# 2026-06-29 — Economy give/pay (S1 deepening win, slice 2)

> **Status:** `in-progress` — born-red (Q-0133). Run type: routine · dispatch.

**Branch:** `claude/give-pay-economy` (off `main` @ #1540 merge, `58c55473`).

## What I'm about to do (intentions)

Slice 2 of this empty-fire dispatch run (slice 1 = #1540, Fishing leaderboard provider, merged). The
S1 completion-first assessment flagged finding (b): **"Economy's missing public `give`/`pay` (the
`transfer()` primitive exists)."** A peer coin-transfer command is the turn-key deepening win — the
audited, atomic `economy_service.transfer()` already exists (one asyncpg transaction, writes
`economy_audit_log`, emits `EVT_BALANCE_CHANGED`); it's just not surfaced as a user command.

Planned:
1. `cogs/economy_cog.py` — new `!give @user <amount>` command (aliases `pay`), routing through the
   existing `economy_service.transfer(...)`. Validation: usage hint on missing args, reject bot target /
   self / non-positive amount; friendly `InsufficientFundsError` message; success embed (both balances) +
   the standard `post_log_embed` audit line. Member-tier, in the already-homed Economy cog → reachable.
2. Tests: a focused `tests/unit/cogs/test_economy_give.py` — happy path calls `transfer` with the right
   args + sends the embed; self / bot / non-positive / missing-args rejected (transfer NOT called);
   insufficient funds → friendly message.
3. Regenerate `site.json`/`data.js`/`dashboard.json` for the new command (static-scan, BUG-0018/0022).

Offline, contained, reversible (play-money, audited), test-covered → self-merge on green (Q-0113).
Owner-flagged direction; no new external/irreversible surface. No DB migration.
