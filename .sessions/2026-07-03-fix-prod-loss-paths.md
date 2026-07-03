# 2026-07-03 — Fix two confirmed prod loss paths (from the engine-room audit)

> **Status:** `in-progress`
> **Branch:** `claude/fix-prod-loss-paths-2026-07-03` · **PR:** (pending first push)
> **Session type:** runtime bug-fix (owner-directed follow-up to the PROMPT-A engine-room
> audit #1690). Fixes two CONFIRMED live loss paths the audit surfaced; owner picked "fix the
> 2 prod bugs" from the question panel.

## What I'm about to do

Both bugs verified against source this session before scoping:

1. **Blackjack tournament entry-fee forfeit on a `BLACKJACK_TOURNAMENT_VERSION` bump.**
   `disbot/cogs/blackjack_cog.py` `_recover_blackjack_tournament`: the version-mismatch branch
   does `clear_by_id(row["id"]) + continue`, skipping the refund block — so on the next schema
   version bump, every in-flight tournament's entry fee is forfeited, directly contradicting the
   method's own docstring ("this one MUST refund"). **Fix:** refund the entry fee (`state["bet"]`)
   regardless of version before clearing — the money was debited at launch and is owed whether or
   not the rest of the state schema still parses.

2. **XP (and every additive on_message effect) double-fires during the LP-4 deploy handoff.**
   `bot1.py` releases the runtime lock *before* `bot.close()` drains (deliberate, fixes ~85s
   downtime), so the incoming replica connects while the draining instance is still processing.
   Discord delivers `MESSAGE_CREATE` to both gateway connections during the overlap, and
   `db.add_xp` is additive with no per-message idempotency → double XP. **Fix (root, whole class):**
   gate `core/runtime/message_pipeline.dispatch()` on `lifecycle.is_shutting_down()` — a draining
   instance runs no message stages; the incoming replica owns ongoing traffic. One chokepoint fixes
   xp / counting / chain / cleanup / rps / four_twenty / btd6 (all pipeline stages), not just XP.

Plus regression tests for both, `check_quality --full` + `check_architecture --mode strict`.

<!-- close-out appended before flipping to complete -->
