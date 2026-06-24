# Session — 2026-06-24 · settle-once guard for blackjack PvP (slice 2)

> **Status:** `in-progress` — born-red opener. Continues the same dispatch run that shipped PR #1444
> (settle-once terminal guard). This slice completes the money-path coverage: blackjack PvP settlement.

**Trigger:** continuation of this run's own handoff. PR #1444 closed the cross-game terminal contract for
RPS PvP + deathmatch bot-duel; the documented remaining adopter is **blackjack PvP/tournament
settlement** — the other money-handling terminal path.

## What I'm about to do

- **Relocate `SettleOnceMixin` → `disbot/utils/terminal_guard.py`** (from `views/`). Blackjack's terminal
  state is `_PvPState`, which lives in `services/` — and **`services/` may not import `views/`**
  (zero-tolerance arch rule). The mixin is pure logic with no view dependency, and is now needed by both
  `services/` and `views/`, so per `docs/helper-policy.md` its correct home is `utils/`. Update the two
  existing importers (RPS PvP, deathmatch bot-duel) + move its unit test.
- **Adopt in blackjack PvP:** `_PvPState(SettleOnceMixin)`; guard `_resolve_pvp` at the top so a second
  settlement (a `BlackjackView` terminal firing `on_finish` twice, or any re-entry) short-circuits — no
  duplicate result embed, no redundant (idempotent) wager settle. Today the `_pvp.pop(key, None)` is a
  de-facto guard but doesn't short-circuit.
- Blackjack regression test (settles once / second `_resolve_pvp` no-ops); update the games-map doc path.

⚑ Self-initiated: completing a production-readiness "Not Done"→Done correctness/safety row, no
dispatch/owner ask. Contained, reversible, test-covered.
