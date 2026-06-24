# Session — 2026-06-24 · settle-once terminal guard for game-state views

> **Status:** `in-progress` — born-red opener. Scheduled dispatch fire (no work order); FIX-phase
> correctness slice. Building a shared settle-once guard for game-state views to close the
> "no cross-game test proves terminal controls cannot trigger a second settlement" readiness row.

**Trigger:** scheduled dispatch (empty fire). Phase gate = FIX (bugs/correctness first). The two OPEN
bug sub-cases (BUG-0019 #1, BUG-0009 newest-towers) are owner/data-gated, so I took the next correctness
priority: a "Not Done" row in the games production-readiness map
([map](../planning/production-readiness/games-production-readiness-map-2026-06-12.md)) — *"no cross-game
test proves terminal controls cannot trigger a second settlement after a result, timeout, or delayed
duplicate interaction."* Continues the BUG-0013 challenge-timer lineage.

## What I'm about to do

- **`disbot/views/terminal_guard.py`** (new) — a `SettleOnceMixin` giving any game-state view one atomic
  claim on its terminal/settlement transition (`claim_settlement()` returns `True` exactly once;
  `is_settled` property). Synchronous check-and-set, race-free on discord.py's single event loop when
  taken before the handler's first `await`.
- **Adopt it in the two clearest double-settlement cases:**
  - **RPS PvP** (`views/rps/pvp_play.py`) — `_resolve()` is reachable twice (both-picks race ·
    timeout racing a final pick) → today it relies *solely* on the wager workflow's idempotency and
    still posts a duplicate result embed. Guard `_resolve` at the top.
  - **Deathmatch bot-duel** (`views/games/deathmatch_panel.py`) — `_finish`/`on_timeout` guard via the
    bespoke `duel.is_over`; route both through the shared claim.
- Harden the silently-swallowed timeout `message.edit` failures (`except Exception: pass`) in those two
  views to log at debug (match `BaseView.on_timeout`).
- **Tests:** primitive unit test + per-game "settles once / second call short-circuits" regression tests.
- Flip the games-map row toward Done; sharpen current-state ▶ Next action with the remaining adopters
  (blackjack PvP) for a follow-up PR.

⚑ Self-initiated: advancing a production-readiness "Not Done" row (correctness/safety), no dispatch/owner
ask. Contained, reversible, test-covered.
