# 2026-06-25 — settle-once money-safety CI guard (check_consistency Rule 6)

> **Status:** `in-progress`
> **Run type:** routine · dispatch
> **Branch:** `claude/funny-franklin-ry0ygk` · **PR:** (born-red, opening)

## What I'm about to do

Scheduled dispatch fire, no work order. Survey found the headline ▶ items across sectors
mostly gated (owner / prod creds / external-data / design-review) — Project Moon PR 2 and
absence-guard Layer B both deliberately deferred for a Q-0086 runtime walk; setup PR 3b needs
live-bot verification. So per Q-0172 I'm promoting a clean, decided-lane, offline-verifiable
idea and building it:

**`settle-once-architecture-guard-2026-06-24.md`** → a new `scripts/check_consistency.py`
**Rule 6 (`settle_once_adoption`)**: a wager-settling site (a call to
`game_wager_workflow.settle_pvp` / `refund_pvp`) must adopt the settle-once guard — either its
enclosing class mixes in `SettleOnceMixin` / calls `claim_settlement()`, or its enclosing
function calls `claim_settlement()` (the blackjack module-level-settle shape). Mechanizes the
by-hand double-settlement review that found BUG-0013 + three more sites (PRs #1444/#1445), for
a money-safety class. **Warn-first** (severity=`warning`, the idea's prescribed posture +
the mixin is young) — cannot redden CI. Runs clean today (both wager-settle callers already
adopt). Self-initiated (flagged on the run report).
