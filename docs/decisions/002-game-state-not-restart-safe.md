# ADR-002: In-flight game state is not guaranteed restart-safe

**Status:** Accepted (2025-Q2)
**Supersedes:** none
**Superseded by:** none

## Context

Cogs that hold game state in instance attributes or module-level
dicts (blackjack `_active` / `_pvp` / `_tournaments`,
rps_tournament `self.players` / `self.scores` / `self.matches`,
counting per-channel cache) **lose that state on bot restart**.

The forensic audit identified this as G8 and the runtime contracts
doc (`docs/runtime_contracts.md` §8) flags it.  The user-visible
worst case is an in-progress blackjack hand evaporating mid-bet:
the user is out coins, and we have no record of the wager.

Building full restart-safe state for every game would require:

- A persistent session store per game shape (counting per-channel
  scoreboard, blackjack hand state, RPS tournament tree).
- Migration to the cogs to checkpoint on every turn.
- Restore logic to re-attach views on cog_load.
- Resolve "what happens if the schema changes between save and
  load" — version every payload, write migrations, etc.

That's weeks of work for a UX edge case that hits only during
graceful restarts (rare in production).

P2 PR-13 shipped the **infrastructure** for game-state persistence
(migration 015 `game_state`, `services/game_state_service.py` with
JSONB payload + UNIQUE per (user, channel, subsystem)) and a
**refund path** (`services/economy_service.refund`) so the
economic harm — the only durable harm — can be fully reversed
without per-cog game-state code.

## Decision

**Per-cog game-state restoration is opt-in, not guaranteed.**

- The infrastructure (`game_state_service`, migration 015) is
  available for cogs that want it.
- Cogs that choose to use it follow the contract documented in
  `services/game_state_service.py` (JSONB payload owned per
  subsystem, checkpoint on each turn, clear on completion,
  list_active at cog_load).
- The default behaviour for in-flight games is: **a restart
  cancels the game; any staked coins are refunded via
  `economy_service.refund(reason="<subsystem>:refund:shutdown")`**.

## Consequences

- Users do not lose money to a restart.
- Users *do* lose in-progress hands / tournaments / count streaks
  until the owning cog adopts checkpointing.
- The refund audit-log row makes "did you really lose those
  coins?" trivially answerable from `economy_audit_log` filtered
  on `reason LIKE '%:refund:%'`.
- New cogs that handle money MUST emit a refund on shutdown unless
  they implement full checkpointing.  Add this to the cog review
  checklist.

## Re-evaluation criteria

Move toward universal checkpointing if:

1. **Restart frequency rises.** Operational data shows restarts
   are no longer rare (deployment frequency, crash rate).
2. **A single game type dominates user reports.** If 80% of
   "lost my game" complaints map to one cog, that cog gets
   prioritised for adoption — not a blanket promotion.
3. **The infrastructure proves correct at scale.** First cog to
   adopt (likely blackjack tournament) validates the JSONB schema
   approach; broader rollout follows once that adoption is stable
   for at least one quarter.

## Notes for implementers

- A cog that takes a bet **must** register a shutdown hook (via
  `bot1.py` or a cog_unload path) that calls
  `economy_service.refund` for every active bet.  The hook does
  NOT have to restore the game; refunding is sufficient to honour
  this ADR.
- If a cog adopts `game_state_service`:
  - Save on every state-mutating turn (idempotent).
  - Clear on natural game completion.
  - Restore inside cog_load before any user interaction routes
    through this cog (use `tasks.spawn` for the restore sweep if
    it might take >1s).
  - Version the JSONB payload (`{"version": 1, "hand": [...], ...}`)
    so future schema changes can be handled with a fallback.
