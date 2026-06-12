# Games subsystem — folio

> **Status:** `living-ledger` (area index). Source + ADR-002 win.
> **Last updated:** 2026-06-11.

## What & where

Games covers the Games hub and playable/actionable flows for blackjack, RPS and
RPS tournaments, deathmatch, mining, counting/chain, and their economy rewards.
Start in `disbot/cogs/games_cog.py`, `disbot/views/games/`,
`disbot/cogs/blackjack/`, `disbot/views/blackjack/`,
`disbot/cogs/rps_tournament/`, `disbot/views/rps/`, `disbot/utils/mining/`, `disbot/services/mining_workflow.py`,
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

## Production-readiness review

- Current verified map: [`docs/planning/production-readiness/games-production-readiness-map-2026-06-12.md`](../planning/production-readiness/games-production-readiness-map-2026-06-12.md).

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
  by equipped-light `depth_access`, pure logic in `utils/mining/world.py`). **Mining
  writes route through `services/mining_workflow.py`** (RS02, Q-0071/Q-0072): one DB
  transaction per operation, coin legs via `economy_service.{debit,credit}_in_txn`,
  events after commit, AST-fenced by `tests/unit/invariants/test_mining_write_boundary.py`
  (reads stay direct via `utils/db/games/mining*.py`). The pure mining domain (items
  taxonomy, recipes, loot, world, exploration, pricing, durability helpers) lives in
  **`utils/mining/`** — shared by the service, the cog, and the views. Economy is a
  dependency for bets/rewards, not a place for game cogs/views to duplicate balance
  writes.
- **Wagered PvP + tournament money routes through `services/game_wager_workflow.py`**
  (P0-1, PR #748): the same one-transaction-per-op seam as mining, for every two-party /
  paid-entry coin move. **D1 escrow-at-accept** — PvP stakes leave both wallets atomically
  with a per-player `*_escrow` `game_state` row when a challenge is accepted (`open_pvp_wager`),
  so the loser can never be short at settle (the old credit-then-`allow_overdraft`-debit
  **mint window** is gone). `settle_pvp` / `refund_pvp` / `payout_tournament` are idempotent
  by `FOR UPDATE` row-consumption (replay = no-op, never double-pays); `enter_tournament`
  debits the fee + writes the recovery row in one txn. Escrow/entry rows carry the `bet`
  key, so the 24h `game_state` GC + `recover_escrow` (cog_load / on_guild_remove) refund any
  stranded stake. AST-fenced by `tests/unit/invariants/test_game_wager_write_boundary.py`
  (no `economy_service.credit/.debit` in the wager files; `allow_overdraft=True` solo-only).
  **Solo** flows (single player vs the house) stay on `economy_service` directly — no
  counterparty, no mint risk.
- **Shared game-XP track: `services/game_xp_service.py`** (Wave 2 seed, 2026-06-10) —
  the second XP track (chat XP keeps driving auto-roles untouched): guild-scoped
  `game_xp` rows per game, central award policy (XP ≈ effort/risk; money moves award 0),
  per-game daily soft cap, **shared level derived from `SUM(xp)`** via the chat curve
  (prestige + leaderboard, never content gates). A new game awards XP by calling
  `game_xp_service.award(...)` inside its workflow transaction and emitting the
  catalogued `game_xp.*` events after commit. Leaderboards: `gamexp` + `crafting`
  rank providers.
- **Duels tick combat-gear wear (Q-0054, shipped 2026-06-10):** a finished PvP
  deathmatch wears each human fighter's equipped combat pieces once
  (`ACTION_DUEL` in `utils/mining/workshop.py` — all six set slots since the
  V-16 set model — applied via `mining_workflow.wear_tick` at the win/timeout
  paths; bot duels excluded) — combat gear is fully in the
  craft→break→repair loop.
- **Cross-game character stats: `utils/equipment.py`** is the shared, pure gear→stats
  read model (`EffectiveStats` + the gear catalogue + `compute_stats`). Equipment is
  guild-scoped game state in `mining_equipment` (`utils/db/games/`); one `!equip`/
  `!unequip`/`!gear` path serves every slot. Mining reads `mining_power`/`light_radius`/
  `depth_access`; **deathmatch reads `damage`/`defense`/`max_health`** from the equipped
  combat gear. **The V-16 set-piece model shipped 2026-06-11 (Q-0092):** 9 slots
  (weapon/shield/helmet/chestplate/leggings/boots join tool/light/charm), 6 combat
  families × 5 tiers (bronze<iron<silver<gold<diamond — **bronze + silver are real
  mining ores** with loot rows), a same-tier full-set bonus (`set_bonus`, never
  defense), forge recipes per tier ore, and migration 068 folding the legacy
  "armor" items/slot into the chestplate/shield slots. Numbers are owner-delegated
  and **pinned by `tests/unit/utils/test_gear_set_numbers.py`** (monotonic ladders +
  duel-sim win-rate bands); rationale:
  [`../planning/gear-set-numbers-2026-06-11.md`](../planning/gear-set-numbers-2026-06-11.md).
  Add a new game's stat dependency by reading the block, never by importing another
  game's items.
- **Paper-doll character render: `utils/character_render.py`** (V-16 phase 1, the
  minebot `/gear` restoration) — a pure, manifest-driven compositor: base figure +
  per-slot sprites at `SLOT_ANCHORS`, **procedural tier-palette placeholders** until
  the owner's PNG pack drops into `disbot/assets/gear/` (naming convention
  in that directory's README — `{family}_{tier}.png`, hot-swap, no code change).
  Attached by `!gear` (embed image) and the hub Gear button (ephemeral follow-up);
  embed fallback always (Pillow-optional, corrupt sprites fall back per-layer).
- **Mining economy loop** — sell raw resources for coins (faucet, reusing
  `items.item_value`) and buy gear with coins (sink), closing the
  mine→sell→upgrade→descend loop. Pricing is pure (`utils/mining/market.py`); the
  money+inventory moves are `mining_workflow.sell`/`sell_all`/`buy` — **both legs in
  one transaction** (`mining:sell_ore`/`mining:buy_gear` audit reasons). Surfaced via
  `!sell`/`!sellall`/`!buy`/`!market` and a Market panel on the hub. The recipe
  catalog is reconciled to the item taxonomy (curated economy, owner decision
  2026-06-10) and self-governing via `tests/unit/utils/test_recipes_catalog_alignment.py`.
- **Character overview: `views/mining/character_panel.py`** — a read-only profile embed
  (`!character`/`!profile` + a hub Character button) that **aggregates, owns nothing**:
  position + deepest record, game level + XP bar, equipped gear + `EffectiveStats`, coins,
  and net worth. **The §7.6 PIL stat card shipped 2026-06-10** (`utils/mining_render.py`
  `build_stat_card_spec`/`render_stat_card`, attached by `!character`; embed fallback
  always), alongside the inventory PNG card on the hub Inventory button. The gear UI is
  `views/mining/gear_panel.py` (slot→item selects + ✨ Equip Best) and the categorized
  crafting UI is `views/mining/recipe_browser.py` (paginated past 25 recipes).
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
