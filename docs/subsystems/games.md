# Games subsystem — folio

> **Status:** `living-ledger` (area index). Source + ADR-002 win.
> **Last updated:** 2026-06-09.

## What & where

Games covers the Games hub and playable/actionable flows for blackjack, RPS and
RPS tournaments, deathmatch, mining, counting/chain, and their economy rewards.
Start in `disbot/cogs/games_cog.py`, `disbot/views/games/`,
`disbot/cogs/blackjack/`, `disbot/views/blackjack/`,
`disbot/cogs/rps_tournament/`, `disbot/views/rps/`, `disbot/cogs/mining/`,
`disbot/views/mining/`, `disbot/services/game_state_service.py`,
`disbot/services/economy_service.py`, and `disbot/utils/db/games/`.

## Rules & approved structures (binding — link, don't restate)

- **ADR-002:** in-flight game state is intentionally not guaranteed restart-safe.
  This is accepted behavior, not a bug or a proposal target. Existing game-state
  infrastructure is best-effort; do not introduce Redis or promise recovery.
- Money must not be lost on restart. Follow each game's existing economy-service /
  payout path and keep wager settlement idempotent or safely recoverable where the
  source already provides that contract.
- Views must acknowledge interactions, enforce the initiating player/authority, and
  handle timeout/terminal states safely. Reuse shared panel/back helpers where the
  actionability roadmap points to them.

## Current state

- `docs/archive/games-actionability-roadmap.md` is complete: hubs and the principal RPS,
  blackjack, and deathmatch panel paths became actionable; settings/readiness and
  back-navigation contracts were added.
- Terminal-button behavior/history is guarded by the help/games actionability tests;
  the 2026-06-06 readiness review found no source/test evidence of an unresolved
  terminal-state “interaction failed” regression. Future changes should inspect terminal callbacks, disabled-state edits, timeout
  handling, and expired-interaction failure paths first.
- Blackjack has solo/PvP/tournament flows; RPS has solo/PvP/tournament persistence;
  mining owns its item/recipe/reward/exploration loop plus a typed inventory and a
  persistent depth/biome "Descent" (Surface→Magma; `mining_player_state`, descent gated
  by equipped-light `depth_access`, pure logic in `cogs/mining/world.py`). These mining
  writes are **direct-lane game state** by design (`docs/ownership.md`; RC-8A ledger),
  not an audited-service gap. Economy is a dependency for bets/rewards, not a place for
  game cogs/views to duplicate balance writes.
- **Cross-game character stats: `utils/equipment.py`** is the shared, pure gear→stats
  read model (`EffectiveStats` + the gear catalogue + `compute_stats`). Equipment is
  guild-scoped game state in `mining_equipment` (`utils/db/games/`); one `!equip`/
  `!unequip`/`!gear` path serves every slot. Mining reads `mining_power`/`light_radius`/
  `depth_access`; **deathmatch reads `damage`/`defense`/`max_health`** from each fighter's
  equipped combat gear (weapon/armor) — a small, fair edge tunable in `_GEAR`. Add a new
  game's stat dependency by reading the block, never by importing another game's items.
- **Mining economy loop: `cogs/mining/market.py`** — sell raw resources for coins
  (faucet, reusing `items.item_value`) and buy gear with coins (sink), closing the
  mine→sell→upgrade→descend loop. The one mining path that touches money: coins move
  **only** through the audited `services.economy_service` (`credit`/`debit` → audit row +
  balance event); the inventory side stays direct-lane. Surfaced via `!sell`/`!sellall`/
  `!buy`/`!market` and a Market panel on the hub.
- **Character overview: `views/mining/character_panel.py`** — a read-only profile embed
  (`!character`/`!profile` + a hub Character button) that **aggregates, owns nothing**:
  position, equipped gear + `EffectiveStats`, coins, and inventory net worth, each read from
  its existing owner. The brainstorm §7.6 stat-card seed (no PIL yet); it grows for free as
  game-XP / skills / titles land.
- Known game UX follow-ups are not stability failures; cite the accepted #535
  baseline rather than claiming a fresh live retest.

## Plans / pending approval

The deferred section of `docs/archive/games-actionability-roadmap.md` is contextual, not a
blanket approval. It includes bounded follow-ups such as inventory architecture,
RPS canonical-key/package cleanup, bot-duel settings/stats, leaderboards, setup, and
shared back-button adoption. Do **not** propose restart-safe game state.

## Ideas (not approved)

`docs/ideas/mining_exploration_brainstorm.md` records mining design intent/ideas;
`docs/ideas/fun-and-ease-brainstorm-2026-06-09.md` adds the 2026-06-09 fun/ease batch
(several game-facing: server goals, bounties, rivalries, word game, treasure hunts).
Its ⭐ pets cluster is structured in
[`../planning/pets-companions-plan-2026-06-09.md`](../planning/pets-companions-plan-2026-06-09.md)
(Later horizon — gated behind the Wave-1 keystone slices + balance review). Apply the
ideas promotion path before implementing unapproved game expansions.

## Next candidates

1. Pick a bounded deferred actionability follow-up and inspect its view lifecycle,
   terminal-button behavior, interaction checks, and failure handling first.
2. Trace any wager/reward change end-to-end through the game's persistence and
   `economy_service`; add tests for duplicate/failed/timeout paths.
3. Run the roadmap's manual smoke matrix when live Discord verification is required;
   do not infer it from unit tests.

## Related docs

`docs/decisions/002-game-state-not-restart-safe.md`,
`docs/archive/games-actionability-roadmap.md`, `docs/ideas/mining_exploration_brainstorm.md`,
`docs/current-state.md`, `docs/runtime_contracts.md`.

## Product-growth roadmap drafts (not approved)

The [games/mining/idle roadmap draft](../planning/games-mining-idle-roadmap-2026-06-08.md) routes poker, blackjack variants, mining depth/co-op/idle, and crafting handoffs while preserving ADR-002. Cross-cutting game-facing ideas are routed through the [social/community/progression](../planning/social-community-progression-roadmap-2026-06-08.md) and [economy/marketplace/rewards](../planning/economy-marketplace-rewards-roadmap-2026-06-08.md) drafts. The [idea inventory](../planning/idea-roadmap-inventory-2026-06-08.md) owns lifecycle outcomes; none of these drafts is an active implementation lane.
