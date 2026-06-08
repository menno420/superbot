# Games, Mining, and Idle Growth — roadmap draft

> **Status:** `plan` — planning/routing draft; not implementation approval.
> **Horizon:** Later, except the already-promoted `!explore` wiring plan. **Boundary:** ADR-002 accepts non-restart-safe game sessions.

## Planning contract

- **Status:** roadmap draft; routing only, not approval and not an active implementation lane.
- Source code, merged PRs, binding contracts, subsystem folios, and `docs/current-state.md` outrank this draft.
- Preserve domain-service mutation ownership, direct-vs-draft lane rules, deterministic event flow, auditability, rollback safety, observability, cache invalidation, and testability.
- Before implementation, re-verify source, live PRs, the relevant folio, and every named gate.

## Context and objective

This draft groups multiplayer poker, blackjack follow-ups, mining depth, an active+idle mining hybrid, bosses/events/co-op, blueprint crafting, and existing deferred games follow-ups. It extends existing game/mining owners and explicitly rejects Redis or restart-safe game-state proposals.

## Scope

- Multiplayer Texas Hold'em tables (3–6), lobby/blinds/hand progression, economy wagers.
- Blackjack variants/side bets after engine/balance review.
- Mining deeper floors, bosses, deterministic/random events, co-op, and an offline-resource/active-boost hybrid.
- Blueprint drops routed to the economy/crafting roadmap.
- Existing bounded games actionability follow-ups and the already-promoted mining wire plan.

## Out of scope

Redis, cross-process game state, restart-safe sessions/checkpointing, a standalone idle resource loop, or economy effects outside `economy_service`.

## Current state and seams to reuse

Games use `game_state_service`, game-specific engines/cogs/views, `economy_service`, and game DB helpers. Mining has shipped exploration, item, reward, and recipe modules; `docs/planning/mining-wire-exploration-plan.md` already owns the safe wiring slice.

Likely roots: `disbot/services/game_state_service.py`, `disbot/services/blackjack_engine.py`, `disbot/services/economy_service.py`, `disbot/cogs/blackjack/`, `disbot/cogs/mining/`, `disbot/cogs/mining_cog.py`, `disbot/views/games/`, `disbot/views/mining/`, and `disbot/utils/db/games/`.

## Proposed phases

1. **Use existing plans:** wire exploration only after maintainer approval; separately select one bounded archived actionability follow-up.
2. **Mining progression contract:** define deterministic depth/event/boss/reward boundaries, balance simulation, and co-op ownership without changing persistence assumptions.
3. **Idle extension:** specify offline accrual caps, anti-abuse, clock handling, active boosts, and economy sink/source effects; extend mining only.
4. **Blackjack variants:** isolated rules/odds/balance plan with explicit UI and payout audit.
5. **Poker concept/architecture:** concurrency, table lifecycle, disconnect/refund semantics, moderation, and economy escrow before implementation sequencing.
6. **Crafting handoff:** blueprint-drop events feed the economy-owned item/crafting contract.

## Dependencies and gates

ADR-002 remains binding; economy ledger/refund safety; deterministic event flow; abuse/balance review; social/guild decisions for guild battles or co-op identity; and owner approval before promoting any raw idea.

## Risks and mechanics

Poker and co-op are high concurrency/moderation risk. Restarts must cancel/refund according to ADR-002, not resume. Offline accrual needs bounded time calculations and test clocks. Additive migrations, idempotent rewards, cache invalidation, reconciliation reads, simulation tests, and safe-disable flags are required.

## Migration, cache, audit, rollback, and test implications

Any progression/item schema is additive; ephemeral game sessions remain non-migrated under ADR-002. Cache invalidation follows mining/economy owners. Audit stakes, rewards, refunds, offline accrual, and balance-sensitive events. Rollback cancels/refunds through existing owners and disables the feature; it never resumes games. Tests require deterministic engines, fake clocks, concurrency/disconnect/restart cases, payout/refund idempotency, simulations, and view flows.

## Open questions and next session

- Product/balance review is required for poker stakes, side bets, idle caps, and co-op rewards.
- **Recommended next model/session:** Sonnet may execute only the separately approved mining-wire plan; Opus should revise poker/idle/mining-depth architecture. Codex remains mapping-only for game-state persistence proposals.
