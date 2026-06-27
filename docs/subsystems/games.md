# Games subsystem — folio

> **Status:** `living-ledger` (area index). Source + ADR-002 win.
> **Last updated:** 2026-06-19 (plan pointers refreshed: fishing/hub/faucet-sink active; mining-structures shipped → historical).

## What & where

Games covers the Games hub and playable/actionable flows for blackjack, RPS and
RPS tournaments, deathmatch, mining, counting/chain, and their economy rewards.
Start in `disbot/cogs/games_cog.py`, `disbot/views/games/`,
`disbot/cogs/blackjack/`, `disbot/views/blackjack/`,
`disbot/cogs/rps_tournament/`, `disbot/views/rps/`, `disbot/utils/mining/`, `disbot/services/mining_workflow.py`,
`disbot/views/mining/`, `disbot/services/game_state_service.py`,
`disbot/services/economy_service.py`, and `disbot/utils/db/games/`.

## Federated Explore world spine (the open-world hub)

The **open-world** games (mining · fishing · later pets/survival) are tied together by a
top-level **Explore world hub** — the "town square" a player walks out into — separate from
the competitive **Games hub** (`!games`, blackjack/RPS/deathmatch). Spine PR 1 (federated
Explore-hub plan, merged #1156):

- **`disbot/services/world_registry.py`** — the registry seam. Each world is a `WorldEntry`
  (`key/label/emoji/description/opener/order`); `register_world_entry` is idempotent (de-dup by
  key) and `get_world_entries` returns them sorted by `(order, label)`. **Pure**: it stores the
  `opener` as an opaque callable and imports no view, so it never creates a `services → views`
  edge. A new world docks in by registering an entry — no edit to the hub.
- **`disbot/views/explore/world_hub.py`** — `ExploreWorldHubView(HubView)` +
  `build_world_hub_embed()`, one button per registered world. Built-ins: **Mine** → the mining
  hub, **Fish** → a fishing entry card (fishing is hub-less). An opener-less entry renders a
  generic coming-soon card. Mirrors the registry-driven `views/games/hub.py` pattern.
- **`!world`** (in `games_cog.py`) opens the hub directly; the mining `🗺️ Explore` button
  (custom_id `mining:explore_hub`) forwards to it.
- **Invariant:** `tests/unit/invariants/test_world_registry_parity.py` asserts every registered
  world `key` resolves to a real `SUBSYSTEMS` entry (no silent dead-end buttons).

**Adding a world:** register a `WorldEntry` (key = the subsystem key) at the owning cog's setup,
with an `opener(interaction, view)` that enters that world in place. The built-in Mine/Fish
defaults live in `world_hub.ensure_default_world_entries()` because their openers are view-layer
code; a self-contained subsystem registers from its own module. **Next spine slices** (plan §4):
PR 2 = make the global (`game_xp` SUM) vs per-game tree split explicit (per-game skill trees need a
`player_skills` `game` discriminator — a schema slice, verify live first); PR 3 = a cross-game
identity read-card. Gated open-world layers (gear auto-equip · survival overlay · biome map) wait
on **Q-0182**.

## Casino — group card games (multiplayer, per-player ephemeral)

The **Casino** (`casino` subsystem, `disbot/cogs/casino_cog.py`) is a Games-hub
child for **group** card games where every seated player gets their **own
auto-updating ephemeral message**, so a whole table plays at once. v1 ships
**multiplayer Texas Hold'em poker**; roulette and other games dock into the same
hub. Reached via `Games → 🎰 Casino` and `!casino` / `!poker`.

- **The marquee mechanic** is the per-player ephemeral broadcast
  (`disbot/views/casino/poker_table.py`): a Discord ephemeral message can only be
  edited via the interaction token that created it, so the table keeps each
  seat's `discord.InteractionMessage` handle (captured at **Join**) and, on every
  state change, re-renders + edits **every** seat's private panel plus the public
  spectator board. A per-turn idle clock (90 s) auto-checks/folds an AFK seat. The
  generic "shared table + per-player ephemeral broadcaster" can be lifted out of
  `poker_table.py` into a reusable `views/casino/table.py` on the rule of three.
- **Layering mirrors the other games:** pure reusable card model `utils/cards/`
  (`Card`/`Deck` with *rankable* ordered ranks — blackjack's helpers stay
  blackjack-specific) · pure poker domain `utils/poker/` (`evaluate.py` best-5-of-7
  hand scoring + `engine.py` the Hold'em state machine: blinds, betting, all-ins,
  **side pots**, showdown) — both Discord-free and fully unit-tested · the view
  layer is a thin renderer. `services → views` is never crossed (no service —
  see money note).
- **Money (v1 scope):** **table play-chips** only (start 1000, blinds 5/10) — chips
  never leave the table, so no economy seam is involved and it sits trivially
  inside the free-for-everyone / no-pay-to-win mission (Q-0190). **Real-coin
  buy-in/cash-out is a deliberate follow-up** needing N-party escrow through
  `game_wager_workflow` (the money-safety seam), plus game-XP on table finish.
- **ADR-002:** in-flight table state is in-memory and **not restart-safe** by
  design, exactly like blackjack/RPS.
- **Design + research record:** [`../planning/casino-poker-design-2026-06-22.md`](../planning/casino-poker-design-2026-06-22.md)
  (the `tools/sim/casino_games_sim.py` scorecard that picked Hold'em + the engine's
  Monte-Carlo chip-conservation/odds validation). **Follow-ups:** real-coin
  buy-in · roulette · multiplayer blackjack table · custom raise-amount modal.

## Idle games (accrue-over-time)

The **chicken farm** (`farm` subsystem, `disbot/cogs/farm_cog.py`) is the bot's first
**idle** game — progress accrues while the player is away. Hens lay eggs over time;
the player collects them for coins + game XP and spends coins on more hens (faster
lay rate) and a bigger coop (larger egg cap). It is a Games-hub child (`activities`)
also reachable via `!farm` and the Explore world hub.

- **Idle accrual reuses the `settle()` pattern** (a stored value + a timestamp,
  computed from elapsed time in pure code), exactly like `utils/fishing/energy.py` /
  `utils/mining/energy.py` — **no background ticker, no Redis** (ADR-001/002). The
  effective egg count at any instant is `utils/farm/settle()` over the stored
  `(eggs, eggs_updated_at)` on the `chicken_farm` row (migration 090). Because all
  state lives in that one row, the farm is incidentally fully restart-safe.
- **Layering mirrors fishing:** pure domain `utils/farm/` (accrual, capacity,
  pricing) · audited write boundary `services/farm_workflow.py` (RS02/Q-0071: one
  txn per op, coin legs via `economy_service.*_in_txn`, events after commit) · CRUD
  `utils/db/games/farm.py` · views `views/farm/` (`FarmMenuView` + `FarmShopView`).
- **Faucet discipline:** the egg-collect faucet is deliberately modest (one free
  starter hen banks ~40 coins over ~100 min idle) — the owner's standing
  "rewards too large & too frequent" caution. Buying hens scales the faucet but
  each costs more coins (the sink), so the loop stays self-balancing. Tunables are
  pure constants in `utils/farm/farm.py`.
- **Return-moment summary (`utils/idle_summary.py`, PR #1331):** a pure, game-agnostic
  helper (`format_duration` + `summarize_idle_gain`) renders the "🌙 While you were away
  (2h 14m) you gained N eggs" blurb on the farm panel from the settle delta
  (`farm_workflow.get_status` reports `eggs_gained`/`elapsed_seconds`/`at_capacity`). A
  second idle system reuses it as-is — the rule-of-three start the shared-`settle()`
  extraction will follow.
- **Fresh-start contract (PR #1331):** `chicken_farm.eggs_updated_at` defaults to epoch 0,
  and settling from 1970 would instantly fill a new coop (a free full collect). The
  workflow's `_stored_state` normalizes a zero timestamp to *now* so idle accrual starts
  from first contact (an empty coop) — pinned by `tests/unit/services/test_farm_workflow.py`.
  Any new idle system on the `(value, timestamp)` pattern must apply the same normalization.
- **Adding another idle game:** follow this layering, register a `GAME_*` constant in
  `game_xp_service`, add the `SUBSYSTEMS` entry under the Games hub, and reuse
  `settle()` + `idle_summary` (extract the shared `settle/spend` core into `utils/` only on
  the rule of three — a *third* settle-based system).

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

## Feature-completion certification

- The *feature/UX-completeness* axis (orthogonal to the risk-axis readiness map above) is tracked per
  game in [`docs/planning/feature-completion/`](../planning/feature-completion/README.md): each game is
  a unit scored against [`rubric-game.md`](../planning/feature-completion/rubric-game.md) and certified
  `✔` only on evidence + owner sign-off (Q-0209). Worked pilot:
  [Blackjack](../planning/feature-completion/units/blackjack.md) (◐ assessed).

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
- **Vault — safe stash (§7.5 structure, #884)** — a per-player protected store separate
  from the active pack: deposit moves items out of `mining_inventory` into `mining_vault`
  (migration 070), withdraw moves them back, both legs atomic via
  `mining_workflow.vault_deposit`/`vault_withdraw`/`vault_deposit_all_resources`
  (no coins move → item-state direct-lane, no audit leg; the atomicity is the contract).
  Surfaced via `!vault`/`!stash`/`!unstash` and a `🏦 Vault` hub panel. The Vault-cap sink (v2, #897),
  Forge (#905), and Home (#910) **all shipped** — the
  [mining-structures-skill-tree-plan](../planning/mining-structures-skill-tree-plan-2026-06-14.md) is now
  `historical` (every slice landed); only the owner-gated V-16 phase-2 PNG sprites remain.
- **Skill tree — capped specialization (§7.4, Slice D, #891)** — `player_skills` (migration 071)
  + `services/skill_service.py` owns every allocation; four branches
  (mining/combat/fortune/crafting), **per-branch cap 10, soft total cap 20** (< 4×10 ⇒ you can't
  max all → forced specialization). Points derive from the shared game-XP level
  (`min(level, 20) − spent`); `allocate` is self-service, `respec` is a coin sink (the repair
  precedent). Pure `utils/mining/skills.py` (`skill_stats`) merges with gear through
  `utils/mining/character.py` `character_stats`, adopted at `mining_workflow.descend` —
  **empty allocations are byte-identical to gear-only stats** (invariant-tested). Surfaced via
  `!skills`/`!skill <branch>` and a `🌳 Skills` hub panel. **Respec polish (Slice E, #912):** the
  Respec button now opens a confirm card (cost + point preview, nothing charged until you choose) and
  offers a cheaper **single-branch** respec (`skill_service.respec_branch`).
- **Titles — earned identity text (§7.6, Slice F, #912)** — pure `utils/mining/titles.py` catalogue;
  the **earned** set is *derived* from existing progression (a skill branch at cap, deepest biome
  reached, game level), so nothing is granted on a mutation path — only the equipped *choice* persists
  (`mining_player_state.equipped_title`, migration 074). `services/title_service.py` owns equip/unequip
  (the `set_equipped_title` write primitive is on the RS02 boundary ratchet) and gates the displayed
  title on still being earned (a respec silently un-displays a mastery title). Surfaced via `!titles`,
  a `🏆 Titles` button on the Skills panel, and the equipped title on the Character embed. **Additive
  — no title equipped → byte-identical.** Depth-milestone titles are biome-*named* so they extend
  cleanly when the **P6 grid** deepens the world.
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

**Active games plans** (live buildable set — full index: [`planning/README.md`](../planning/README.md)):
- [fishing-minigame-design](../planning/fishing-minigame-design-2026-06-22.md) — sim-backed
  (`tools/sim/fishing_minigame_sim.py`) interactive catch loop. **PR1 building/shipped:** `!fish` now
  launches an interactive `cast → wait → BITE → reel` view (`views/fishing/cast_view.py`); the catch is
  rolled at cast (`fishing_workflow.roll_cast`) and committed only on a successful reel
  (`commit_catch`) — a missed/early reel = the fish gets away (owner decision). Tuning is pure +
  testable (`utils/fishing/minigame.py`: ~2.5 s window, 3–6 s bite + fake-out). **PR2 (the hybrid)
  shipped/building:** hooking a **trophy** (top third of the unlocked band) starts a short
  **reel-fight** — 2–4 more timed taps (scale with size), each able to snap free; land them all to
  commit. **PR3 (rod ladder) shipped/building:** `!rod` buys up a 5-tier rod ladder
  (`utils/fishing/rods.py`; bronze→diamond, coins, audited `fishing_workflow.buy_rod`); each tier
  turns the 4 knobs — `window_bonus` (reaction window), `bite_speed` (faster bite), `rarity_pull`
  (bigger catches within-band), `escape_resist` (fewer fight escapes). Level = *what* you catch;
  rod = *how well*. **Interactive menu shipped:** `!fishing` (and the Help-hub fishing panel) is a
  real `FishingMenuView` (🎣 Cast launches the minigame in place · 🎒 Rod opens the shop · 📖 Fishdex)
  — `build_help_menu_view` returns it instead of the old static empty view. **Energy pacing shipped:**
  fishing has its own ⚡ energy bar (`utils/fishing/energy.py`, `fishing_energy` table, separate from
  mining per owner decision) — each cast spends 1, regens ~1/30s; `fishing_workflow.begin_cast` gates
  it. Now that casting is finite, fish **sell for ≈ `size_rank` (1–21 coins)**, up from the old 1–7
  (`utils/mining/items.py` `_fish_value`). **Deferred to next PR:** boat/deepwater venue.
- [fishing-open-world-expansion-plan](../planning/fishing-open-world-expansion-plan-2026-06-18.md) —
  Phase 1 fishing v1 **shipped**; **gear loadout presets shipped #1499** (named save/swap sets:
  `mining_loadout_presets` migration 101 + `mining_workflow.{save,apply,list,delete}_loadout` +
  `💾 Loadouts` gear-panel surface + `!loadout`). Phase 2 (boat/open-world) stays owner-design-gated (Q-0175).
  **Fish *use* is now decided + shipped (#1289, owner 2026-06-22):** a caught fish enters the mining
  inventory (`fishing_workflow.fish` grants it; the catch-log stays the dex), is **sellable** for coins
  (modest, size-scaled `RESOURCE` value in `utils/mining/items.py`), and is **cookable** into a
  `cooked fish` food (+30 energy) at a built **Campfire** structure (`!cook`,
  `mining_workflow.cook`; campfire in `utils/mining/structures.py`). Balance caveat: fishing is currently
  unpaced, so fish sell value is kept low on purpose (don't re-open the mining-faucet fix via fishing).
- [mining-hub-redesign](../planning/mining-hub-redesign-2026-06-15.md) — owner-picked Option A sub-hub split.
  **PR2 (hub declutter) shipped:** the main hub is now six buttons (⛏️ Mine · 🌲 Harvest · 🗺️ Explore ·
  🧍 Character · 🧰 Gear · 🔨 Workshop); a **Character** sub-hub (`views/mining/character_hub.py`)
  groups Overview/Inventory/Stats/Skills/Vault/Home and an **Explore** stub sub-hub
  (`views/mining/explore_hub.py`) previews the open-world explorer (Fishing/Roam/Quests — early).
  **PR3 (grid Mine) shipped (2026-06-22, #1281):** the Mine action is now a (x, y, z) grid navigator
  (`views/mining/grid_mine_view.py` `MineGridView`) over a **seed-deterministic procedural world**
  (pure `utils/mining/grid.py`; z = the existing depth band, so `utils/mining/world.py` balance carries
  over), with **per-guild shareable seed** + **fog-of-war discovery** (migration 085: `pos_x`/`pos_y` +
  `mining_world` + `mining_discovered`; `utils/db/games/mining_grid.py` on the RS02 seam). `!mine` opens
  it; `!mineworld` shows/reseeds the shared seed. It **replaced** the interim linear `MineView`. v1 is
  **encounter-free** (owner Q-0173: encounters are a deferred later session →
  [`../ideas/mining-grid-encounters-2026-06-22.md`](../ideas/mining-grid-encounters-2026-06-22.md)).
  **Dig IS movement (owner correction, 2026-06-22):** the navigator is **six directional dig buttons**
  — each dig moves you into the adjacent cell **and** mines it (`mining_workflow.dig(direction)`, one
  transaction: move + loot + fog-mark + wear + the down-dig depth-record bonus); no separate move /
  "Mine here".
- [games-economy-faucet-sink-diagnostic-plan](../planning/games-economy-faucet-sink-diagnostic-plan-2026-06-15.md) —
  read-only economy faucet/sink read model. **Shipped #1044** (`!platform economy [days]` — the
  whole-window mint/drain/net/ratio + verdict aggregate) **+ the per-day trend view (2026-06-27):
  `!platform economytrend [days]`** (`economy_flow_service.build_flow_timeseries` → a daily
  minted/drained/net series + a net-flow sparkline + a rising/falling/steady read), so an operator can
  watch inflation *over time*, not just at one snapshot. The §6 health-finding follow-up (a persistent
  finding when a guild sustains the `inflating ⚠` verdict) stays **design-for-review** (per-guild verdict
  vs. the guild-agnostic findings store — see the plan §6).
- [mining-economy-balance-2026-06-22](../planning/mining-economy-balance-2026-06-22.md) — **sim-pinned
  rebalance numbers** for the live grid-Mine faucet (owner: "rewards too large & too frequent"). The
  simulator (`tools/game_sim/mining_economy_sim.py`) quantifies the live faucet at ~7–55× a `!daily`/hr
  and recommends a config (frequency brake + smaller base roll + flatter tool curve + 12% bonanza) that
  lands every player at ~1–3 dailies/active-hr. Design record — owner approves + picks the frequency
  mechanic (energy vs cooldown) before any runtime edit.
- *Shipped → `historical`:* [mining-structures-skill-tree-plan](../planning/mining-structures-skill-tree-plan-2026-06-14.md)
  (every slice landed) · [games-wager-money-safety-plan](../planning/games-wager-money-safety-plan-2026-06-12.md) (#748).

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
