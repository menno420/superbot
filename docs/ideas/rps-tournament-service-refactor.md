# Idea — refactor RPS tournament orchestration out of the cog

> **Status:** `ideas` — not approved for implementation; a preserved refactor spec. **Not a
> plan, not approval.** Captured 2026-06-13 from GitHub issue **#229** (owner-authored
> 2026-05-20) so the decomposition lives in the repo, then the issue was closed (GitHub issues
> are not this repo's planning home — `docs/` is). Promote to a `docs/planning/` plan before building.
> **Subsystem:** rps_tournament — the RPS tournament cog/service.

## Problem

`disbot/cogs/rps_tournament_cog.py` still owns too much runtime state + business flow, even
though some helper/persistence/recovery/bot-match code already lives in `cogs/rps_tournament/`
submodules. The cog directly owns: `tournament_active`, `registration_active`, `players`,
`scores`, `matches`, `current_round`, `match_channels`, `entry_fee`, `paid_players`; the
registration countdown/reminder task; bracket shuffling + round pairing; manual matchup
mutation; move capture + match resolution; winner payout + completion cleanup. This makes it
hard to test, hard to recover after restarts, and inconsistent with the platform direction
(cogs own Discord entry points; **services** own deterministic orchestration).

**Money note (2026-06-12):** the wagered PvP + tournament *money* path is already audited via
`services/game_wager_workflow.py` (#748 — escrow-at-accept, idempotent settle/refund/payout).
This refactor is about the **orchestration/state** decomposition, not the money seam; keep the
wager-workflow boundary intact.

## Target architecture

`RockPaperScissorsCog` becomes the Discord boundary only (arg parsing · permission decorators ·
user-facing embeds · interaction/view entry points · message-pipeline handoff), delegating to:

```
RPS commands/listeners/views
  → RpsTournamentService → RpsTournamentRuntime / state model → RPS rules engine
                         → channel/resource helpers → economy/game_wager_workflow
                         → tournament_state_service → persistence/recovery helpers
```

## Proposed extraction steps (contained series, tests + smoke per step)

1. **Pure state + decision model** — typed dataclasses (`RpsTournamentRuntime`,
   `RpsPlayerState`, `RpsMatchState`, `RpsRoundPlan`, `RpsMatchResult`); move pure decisions
   first (validate start, shuffle/pair, byes, apply move, resolve round, match-complete,
   tournament-complete). No Discord calls.
2. **Service orchestration boundary** — `RpsTournamentService` owns the runtime transitions
   (start/cancel registration, register player, start tournament, manual matchup, next round,
   submit move, complete match/tournament). The cog becomes a thin adapter.
3. **Persistence + recovery alignment** — persist enough to recover (registration metadata,
   registered/paid ids, current-round ids, active match-channel ids, match state/moves/wins);
   recovery restores or cleanly refunds/cancels rather than relying on in-memory lists.
   *(Respect ADR-002: game state is not restart-safe by design — scope recovery to clean
   refund/cancel, not full mid-match restoration, unless ADR-002 is revisited.)*
4. **Timeout cleanup** — deterministic cleanup of abandoned registration countdowns, stale
   match channels, inactive players/matches, restart-during-tournament, via
   `core.runtime.tasks` naming/cancellation conventions.
5. **Shared tournament abstractions** — only after RPS is stable, extract *proven* overlap with
   blackjack tournament flow (active-tournament guard, registration lifecycle, fees/refunds/
   payouts, channel cleanup, recovery hooks, status reporting). Avoid a premature generic
   framework.

## Acceptance criteria

Cog no longer owns bracket/match state; cog methods are mostly adapters; pure logic + state
transitions are unit-tested without Discord objects; recovery/timeout explicit + tested;
`!rpsregister` / `!rpsstart` / `!rpsmatchup` / `!rpsbot` / `!rps` still work; the Games/Help
RPS panel still delegates to the same path; economy debit/credit unchanged + auditable; match
channels cleaned up deterministically on completion/cancel/restart.

## Routing

Games lane — folio [`subsystems/games.md`](../subsystems/games.md). **Priority (owner, #229):**
medium-high, *before* large new game/tournament features; a contained refactor series, not a
text cleanup. Promote to a `docs/planning/` plan (2–3 PR slices) when scheduled. Adjacent
prior art to reuse: `services/mining_workflow.py` (cog→service decomposition pattern) and
`services/game_wager_workflow.py` (the money seam).
