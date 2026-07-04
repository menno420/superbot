# Rebuild discovery map — community, economy, progression, games, and product loops

> **Status:** `historical` — repo-grounded rebuild discovery audit report; source + merged PRs win.  
> **Audit part:** 3 of 4 — community/economy/progression/games/product loops.  
> **Date:** 2026-07-02.  
> **Mode:** repo-grounded rebuild discovery mapping only. No implementation approval. No source edits.  
> **Allowed output:** this report only.  
> **Truth order used:** source + merged repo state first; binding docs second; current-state ledgers third; planning/completion/readiness docs as supporting context.

## 1. Executive summary

### Strongest reusable product/game/community ideas

1. **Mother hubs backed by registry metadata.** The current bot has a useful product shape: top-level hubs (`games`, `economy`, `community`, `utility`) plus child subsystems declared in `SUBSYSTEMS.parent_hub` and displayed through `hub_registry.HUBS`. Preserve the idea, but rebuild it as a first-class route graph with one panel grammar, not one-off buttons per cog.
2. **Audited shared-state writers.** Coins, XP, and karma already have explicit service seams (`economy_service`, `xp_service`, `karma_service`) and invariant tests. This is the most important rebuild foundation: product loops should depend on mutation result objects, not write tables directly.
3. **Game-specific pure engines plus thin Discord adapters.** Blackjack has `blackjack_engine.py`; fishing/mining/creatures/farm have pure catalog/math modules under `utils/`; creature battle has a service-level simulation. Preserve this split: pure simulation is reusable and testable, while views/cogs should only orchestrate.
4. **Activity-game progression stack.** Mining/fishing/creatures/farm combine collection, skill/gear growth, unlocks, leaderboards, and repeated short actions. This is the best product depth in the repo and should inform a fresh `ActivityGameSpec` family.
5. **Collection-first UX.** Fishing catch log, creatures dex, mining inventory/gear/title panels, inventory category browser, and leaderboards prove that SuperBot's strongest user loop is “do a small action → gain a resource/record → view progress → improve odds/output.”
6. **Shared restart-safety ideas.** `game_state_service` and migrations `015`/`018` give a good checkpoint pattern for persistent pending games. RPS/blackjack use it for tournaments or pending sessions; other games deliberately use persistent per-player progression instead of preserving every ephemeral interaction.
7. **Visual cards and panels.** Leaderboard cards, mining paper-doll/gear renders, world cards, and compact embeds make progression tangible. Rebuild should treat card rendering as a reusable capability with graceful fallback.

### Best progression loops

- **Daily/recurring economy:** `!daily`, work jobs, balance, shop, peer `give/pay`, and treasury contribution/disbursement are straightforward social currency loops.
- **Mining:** mine/explore/dig/descent → collect ores/resources → sell/craft/equip/repair/build structures → improve depth/capacity/stats/title → leaderboard/world identity.
- **Fishing:** cast/reel minigame → catch species/weight/drops → energy/rod/bait/venue/weather/gear affect odds → craft rods/baits/charms/curios/structures → fish log/trophies/leaderboard.
- **Creatures:** catch → collection/dex → XP/levels → level-normalized PvP → records/leaderboards/rematch.
- **Farm:** idle eggs accrue while away → collect once → buy chickens/upgrade coop → flock-size leaderboard.
- **Counting/chain:** channel community challenge loops with persistent channel state and scoreboards.
- **Competitive games:** blackjack, RPS, deathmatch, and casino provide session/challenge/tournament patterns; strongest reusable pieces are challenge acceptance, set-once settlement, tournament registration, rules buttons, and post-game replay/back navigation.

### Best economy/inventory/collection mechanics

- **Audited `economy_service` methods** (`credit`, `debit`, `transfer`, `bet_and_settle`, `refund`, transaction variants) should become an `EconomyLedger` with typed reasons, actor/context, idempotency, and event emission.
- **Inventory as an aggregation layer** is useful but currently split: generic `utils/db/inventory.py` plus mining/fishing stores. A rebuild should unify item catalogs, ownership, quantity, rarity, value, use action, crafting, and display metadata.
- **Crafting recipes** are rich across mining (`recipes.py`, forge/workshop), fishing (`bait`, `rods`, `curios`, charms), and structures. Extract `CraftingRecipeSpec` and `CostVector` primitives.
- **Collection/dex/logbook** should be common: fish species + best weight, creature dex + elements, mining item categories/titles, curios/cosmetics.
- **Leaderboards** already aggregate XP, economy, creatures, fishing, farm, counting, and other providers. Rebuild should use `LeaderboardSpec` per domain with ranking key, tie-breakers, empty states, privacy, and card renderer.

### Biggest fragmentation to avoid

- **Panel grammar fragmentation:** hubs use `HubView`, some game panels use custom `discord.ui.View`, some browsers use `BaseView`, and many commands still build custom ephemeral/public behavior.
- **Inventory fragmentation:** generic inventory, mining inventory, equipment, fishing bait/rod/venue/energy, creature logs, and farm state are separate vertical tables and browsers. That may be fine internally, but the product layer should expose one inventory/collection grammar.
- **Game session fragmentation:** challenge flows, timeouts, stale-state behavior, persistent checkpoints, and settle-once logic are reimplemented differently in blackjack, RPS, deathmatch, creatures, casino, counting, and chain.
- **Economy mutation fragmentation risk:** source mostly enforces economy writes through service, but mining/fishing/farm have direct inventory/resource writes and game-specific coin/cost paths. Rebuild should make coin, item, and XP mutation seams equally explicit.
- **Leaderboards are provider-like but not fully standardized:** several games still cannot join unified leaderboards because they lack per-player persisted stats.
- **Public/ephemeral and back/help/hub behavior is inconsistent:** good conventions exist, but every new game currently has to rediscover them.

## 2. Source route and verification

### Docs read or sampled

Binding and orientation docs:

- `.claude/CLAUDE.md`
- `docs/collaboration-model.md`
- `docs/current-state.md`
- `docs/current-state/S1-bot.md`
- `docs/AGENT_ORIENTATION.md`
- `docs/architecture.md`
- `docs/ownership.md`
- `docs/runtime_contracts.md`
- `docs/repo-navigation-map.md`
- `docs/repo-review-map.md`
- `docs/ultracode/README.md`
- `docs/subsystems/games.md`
- `docs/planning/feature-completion/README.md`
- `docs/planning/feature-completion/units/blackjack.md`
- `docs/planning/production-readiness/*` was searched for relevant game/economy/readiness references.

Key doc facts used:

- Architecture defines services as audited cross-subsystem mutation paths and names INV-F/INV-G for economy/XP sole-writer invariants.
- Runtime contracts name `economy_audit_log` as durable and in-process counting/blackjack/RPS as expected restart-loss areas, with refunds/recovery for some stakes.
- Repo navigation maps the cogs/views/services/DB ownership for each subsystem in this report.
- Completion ledger has every in-scope unit assessed, but none owner-certified as complete as of the repo snapshot.
- Current-state records recent additions such as karma reaction grants, inventory detail density/sort/filter, fishing rod recipe browser, farm and fishing leaderboard providers, peer economy transfer, creature panel/dex, blackjack PvP bet selector/edge tests, and owner-gated inventory item-action/capability cleanup gaps.

### Source roots inspected

- Cogs: `disbot/cogs/economy_cog.py`, `inventory_cog.py`, `treasury_cog.py`, `xp_cog.py`, `karma_cog.py`, `leaderboard_cog.py`, `community_cog.py`, `community_spotlight_cog.py`, `general_cog.py`, `four_twenty_cog.py`, `games_cog.py`, `blackjack_cog.py`, `casino_cog.py`, `deathmatch_cog.py`, `rps_tournament_cog.py`, `counting_cog.py`, `chain_cog.py`, `mining_cog.py`, `fishing_cog.py`, `creature_cog.py`, `creature_battle_cog.py`, `farm_cog.py`, `help_cog.py`.
- Views: `disbot/views/economy/`, `treasury/`, `xp/`, `games/`, `blackjack/`, `casino/`, `community/`, `counting/`, `creature/`, `creature_battle/`, `farm/`, `fishing/`, `mining/`, `rps/`.
- Services: `economy_service.py`, `treasury_service.py`, `xp_service.py`, `karma_service.py`, `blackjack_engine.py`, `blackjack_state.py`, `blackjack_persistence.py`, `mining_workflow.py`, `fishing_workflow.py`, `creature_workflow.py`, `creature_battle_service.py`, `farm_workflow.py`, `game_state_service.py`, `game_xp_service.py`, `chain_service.py`.
- DB helpers: `disbot/utils/db/economy.py`, `inventory.py`, `treasury.py`, `xp.py`, `karma.py`, and `disbot/utils/db/games/*` for chain/counting/creatures/creature battles/deathmatch/farm/fishing/mining/RPS/game state/game XP.
- Pure data/math/catalogs: `disbot/utils/mining/*`, `disbot/utils/fishing/*`, `disbot/utils/creatures/*`, `disbot/utils/farm/*`, `disbot/data/fishing/fish.json`, `disbot/data/creatures/creatures.json`.
- Registries: `disbot/utils/subsystem_registry.py`, `disbot/utils/hub_registry.py`.
- Tests: relevant `tests/unit/cogs`, `tests/unit/services`, `tests/unit/db`, `tests/unit/invariants`, `tests/unit/utils`, and `tests/unit/views` suites listed by file discovery.

### Commands run and results

- `find /workspace -name AGENTS.md -print` — no `AGENTS.md` files found under `/workspace`.
- `git status --short` — clean before report creation.
- `sed -n ...` over the required docs — succeeded; output was large and partially truncated in the terminal transcript, so subsequent targeted `rg`/source reads were used.
- `gh pr list --state open --limit 20 --json number,title,headRefName,author,url` — failed: `gh: command not found`. Open PR status could not be verified with GitHub CLI from this container.
- `rg -n "production-readiness|economy|inventory|..." docs/...` — succeeded; found relevant current-state/readiness references.
- `python3.10 scripts/context_map.py <target>` for all six required targets — failed before execution because `python3.10` is not available on PATH under the active pyenv shim: `pyenv: python3.10: command not found` and it notes version `3.10.20` exists.
- `~/.pyenv/versions/3.10.20/bin/python scripts/context_map.py <target>` for all six required targets — failed with `ModuleNotFoundError: No module named 'yaml'`.
- `python3.10 scripts/check_architecture.py --mode strict` — failed for the same pyenv shim issue: `python3.10: command not found`.
- `python3.10 scripts/check_docs.py` — failed for the same pyenv shim issue: `python3.10: command not found`.
- `python scripts/check_architecture.py --mode strict` — succeeded as a fallback: 0 errors, 49 tracked warnings.
- `python scripts/check_docs.py` — initially reported the new report missing a status badge/orphan link; after marking this report `historical`, it passed all checks.
- `find disbot/cogs disbot/views disbot/services disbot/utils/db ...` — succeeded; produced the scoped file inventory.
- `rg -n "^(class|def|async def) " ...` — succeeded; produced cogs/views/services function/class inventory.
- Python AST snippets using default `python` — succeeded for registry extraction where possible.

### Open PR / active gate status

- **Open PRs:** not verified; GitHub CLI is unavailable in this container. Treat PR #1509, if still open, as advisory only per prompt. No source claims in this report depend on PR #1509 being merged.
- **Completion gate:** all in-scope units are `assessed` in `docs/planning/feature-completion/README.md`; none are owner-certified. That is a product/completion status, not a prohibition on source mapping.
- **Owner/live gates observed from current-state/certs:** inventory item actions and some content/art/live walkthrough items remain owner-gated; blackjack certification still needs owner decisions/live walkthrough; live Discord verification was not performed.
- **No active source off-limits gate found** for mapping these lanes. Owner-gated art/content/data is noted as a verification limit, not used as proof.

### Verification limits

- No live Discord or production database access.
- No GitHub CLI; open PR verification unavailable.
- Required `context_map.py` and check scripts could not run under requested command because of local Python/pyyaml environment issues.
- This is a static source/docs audit; UI behavior is inferred from code and tests, not clicked live.
- Source line numbers are intentionally not embedded in this report because it is a design map; final response will cite changed report lines.

## 3. Product surface inventory

Legend for current state: **Done** = implemented enough to map from source/tests; **Partial** = functional with known gaps/fragmentation; **In-flight/gated** = source/docs name remaining owner/live/content work; **Unclear** = needs live/prod or PR verification.

### Economy and inventory

| Subsystem | Registry key | Parent hub/group | Entry commands | Views/panels/modals/selectors | Services/engines | DB/tables/migrations | Settings | Events/audit | Tests | Current state |
|---|---|---|---|---|---|---|---|---|---|---|
| Economy hub/currency | `economy` | top-level hub | `economymenu`, `daily`, `work`, `balance`; current-state also names `give/pay` | `EconomyPanelView`, `attach_back_to_economy_button`, work/shop subviews, job/shop selects, work result view | `economy_service`, `economy_flow_service`, `economy_helpers` | `utils/db/economy.py`; migration `014_economy_audit_log.sql`; core economy balance tables are referenced in architecture/runtime docs | `cogs/economy/schemas.py`; `settings_keys/economy.py` | `economy_audit_log`; service emits balance/audit events; INV-F invariant | `test_economy_service*`, `test_economy_db_txn`, `test_economy_flow_service`, `test_economy_log_channel_pipeline`, view tests | **Done/Partial** — core loop strong; rebuild should preserve audit seam and simplify UI grammar. |
| Inventory | `inventory` | `economy` | `inventory` | `UnifiedInventoryView`, `_CategoryView`, category/detail pages, sort/filter selects/buttons; no separate `views/inventory/` directory found | Mostly cog/read aggregation; mining/fishing workflow mutate game inventories | `utils/db/inventory.py`; mining/fishing inventory-like tables under `utils/db/games/*` | no dedicated schema found in scoped files | direct inventory DB helpers; owner-gated audit/capability cleanup named in current-state | `test_inventory_display_logic`, `test_economy_inventory_edit`, inventory view/cog tests | **Partial/gated** — browser is rich, actions/audit model not fully unified. |
| Treasury | `treasury` | `economy` | `treasury` | `views/treasury/menu.py`, `TreasuryMenuView`, `ContributeModal`; Economy treasury button | `treasury_service` | `utils/db/treasury.py`; migration `092_guild_treasury.sql` | no dedicated schema found | transfers member coins into server pool; disbursement gated to managers; should audit via economy/treasury DB | `test_treasury_service`, `test_treasury_cog`, `test_treasury_contribute_modal`, economy treasury button test | **Done/Partial** — good collective economy idea; rebuild needs explicit server-wallet ledger primitive. |

### Progression and community

| Subsystem | Registry key | Parent hub/group | Entry commands | Views/panels/modals/selectors | Services/engines | DB/tables/migrations | Settings | Events/audit | Tests | Current state |
|---|---|---|---|---|---|---|---|---|---|---|
| XP & levels | `xp` | `community` | `xpmenu`, `rank` | `views/xp/main_panel.py`, config/import panels, rank view, modals | `xp_service`, `xp_role_sync`, `xp_helpers`, `xp_migration` | `utils/db/xp.py`; migration `003_role_xp_thresholds.sql`; XP tables | `cogs/xp/schemas.py`, `settings_keys/xp.py` | `xp_service.award/import/reset`; `xp.level_up` feeds spotlight; INV-G sole writer | XP cog/listener/service/import/rank tests and invariant | **Done/Partial** — strong general progression seam; needs fresh `ProgressionTrackSpec`. |
| Karma | `karma` | `community` | `thanks`, `karma` | mostly cog embeds/cards; no `views/karma/` directory found | `karma_service`, `karma_config` | `utils/db/karma.py`; migration `093_karma.sql` | `cogs/karma/schemas.py`, `settings_keys/karma.py`; `karma.reaction_emoji` opt-in | audited `karma_service.give`, cooldown/daily cap/self-protection; reaction source | `test_karma_service`, `test_karma_reaction`, schema tests, INV-K invariant | **Done/Partial** — good social reputation loop; UI less panelized than XP. |
| Leaderboards | `leaderboard` | `economy` with community cross-link | `leaderboard`, `lb` | `LeaderboardView`, provider select, card rendering | provider/read-only aggregation inside cog/rank providers | reads XP/economy/game DB modules; no single leaderboard table | n/a | read-only | `test_leaderboard_card`, empty states, provider tests in game units | **Done/Partial** — valuable aggregation; some games need persisted per-user stats first. |
| Community hub | `community` | top-level hub | `community` | `CommunityHubView`, dynamic child buttons, back-to-community helper | hub discovery only | registry driven | n/a | no business mutations | `test_community_hub_view` | **Done** as navigation; rebuild should keep dynamic discovery. |
| Community spotlight | `community_spotlight` | `community`/activities | `spotlight` | in-cog `SpotlightView`, `GamesView`, `_GameSelect` | read-only rank providers; EventBus `xp.level_up` feed | reads `utils/db/xp.py` and game providers | no dedicated schema found | reacts to XP/rank events | `test_community_spotlight_cog` | **Done/Partial** — good “show active community” idea; panel lives in cog. |
| General | `general` | `utility` | `generalmenu` | in-cog panel, trivia reveal view, 8-ball modal | content loader only | no scoped DB | content JSON/static | no audit | general cog tests if present | **Done/Partial** — utility/social mini-features, not core rebuild priority. |
| 420 easter egg | `four_twenty` | `utility` | `420`, `fourtwenty` | `_FourTwentyPanelView`, stage/content | content loader/stage | static content/assets | none | none | not central | **Acceptable specialization**; mention only as reusable content-panel pattern. |
| Utility hub | `utility` | top-level hub | `utilitymenu`, `myprofile`, `avatar`, `serverinfo`, `ping` | utility/general views if present; general/four_twenty children | mostly cog utilities | no scoped DB | none | none | utility/general tests | **Done/Partial** — out of core scope except profile/status UX. |

### Games hub and competitive/activity games

| Subsystem | Registry key | Parent hub/group | Entry commands | Views/panels/modals/selectors | Services/engines | DB/tables/migrations | Settings | Events/audit | Tests | Current state |
|---|---|---|---|---|---|---|---|---|---|---|
| Games hub | `games` | top-level hub | `games` | `GamesHubView`, `_GameHubButton`, no-panel embed, back-to-games helper | registry discovery | registry only | none | no business mutation | `test_games_cog`, `test_games_hub_view`, common/back tests | **Done** as navigation; actionability contract is important. |
| Blackjack | `blackjack` | `games`/competitive | `blackjack`, `bj` | `BlackjackPanelView`, bet preset/custom modal, challenge opponent/bet pickers, solo/PvP/tournament views, result/replay/back | `blackjack_engine`, `blackjack_state`, `blackjack_persistence`; cog state | `game_state` checkpoints; no dedicated bankroll table; economy audit for coins | `cogs/blackjack/schemas.py` (`default_entry_fee`) | solo via `economy_service`; PvP/tournament via wager/escrow/refund; settle-once tests | engine, solo/PvP/tournament persistence, edge cases, panel stake picker, settle-once, replay | **Done/assessed; not certified** — best competitive-game template; split/insurance/surrender/live owner items remain. |
| Casino/poker | `casino` | `games`/competitive | `casino`, `poker`, `holdem` | `CasinoHubView`, `PokerLobbyView`, `SeatLobbyView`, `PokerSeatView`, action buttons | in-view poker table/session | in-memory/ephemeral play chips per current-state; no persisted per-player stats | no schema found | no real economy audit; ephemeral chips | `test_casino.py` | **Partial** — fun session pattern, weak rebuild foundation unless formalized. |
| Deathmatch | `deathmatch` | `games`/competitive | `deathmatch`, `dm` | `DeathmatchPanelView`, bot duel, PvP challenge/result views | cog duel state; mining/equipment stats and wear | `utils/db/games/deathmatch.py`; mining equipment/wear dependencies | `cogs/deathmatch/schemas.py` | gear wear ticks; no default coin staking yet | deathmatch bot/challenge/combat/gear/guild/PvP tests | **Done/Partial** — good gear-dependent combat loop; rebuild should isolate `CombatResolver`. |
| RPS tournament/PvP | `rps_tournament` | `games`/competitive | `rps` | RPS panel, solo play/replay, PvP challenge/play, registration/move picker | tournament helpers/rules/stage; in-memory + persistence helper | `utils/db/games/rps.py`; migrations `005`, `019`; game_state for pending | `cogs/rps_tournament/schemas.py` | stakes/refunds via economy paths in cog; persistent pending sessions | RPS naming, PvP, pending persistence, tournament persistence/stage, view tests | **Done/Partial** — good challenge/tournament lifecycle; standardize with `ChallengeSession`. |
| Counting | `counting` | `games`/activities; community cross-link | `count_info`, `counttop`, `countingmenu` | `views/counting/hub_panel.py` with channel/mode selects/toggles/reset/disable/refresh | counting handler/game_logic/parsing/stage/leaderboard | `utils/db/games/counting.py`; migration `005` game PKs | likely counting settings in cog package | channel game events/save outcomes; in-process current state per runtime docs | counting channel/modes/parsing/persistence/leaderboard tests | **Done/Partial** — strong community-channel loop; restart/persistence rules need fresh base. |
| Word chain | `chain` | `games`/activities; community cross-link | `chainmenu`, `chain` | in-cog `ChainMenuView`, create/delete/limit modals | `chain_service` | `utils/db/games/chain.py`; migration `005` game PKs | none found | service emits mutation events; chain write boundary invariant | chain cog prefix/stage/service/invariant tests | **Done/Partial** — channel game, no per-user leaderboard without new writes. |

### Exploration, collection, and idle games

| Subsystem | Registry key | Parent hub/group | Entry commands | Views/panels/modals/selectors | Services/engines | DB/tables/migrations | Settings | Events/audit | Tests | Current state |
|---|---|---|---|---|---|---|---|---|---|---|
| Mining | `mining` | `games`/activities; economy cross-link | `minemenu`, `mine` plus many subcommands | `MiningHubView`, home/market/forge/gear/grid/vault/workshop/skills/titles/recipes/how-to/character/loadout panels, build modal | `mining_workflow`; pure modules for capacity, energy, grid, exploration, rewards, items, recipes, skills, structures, world, titles; renderer | many `utils/db/games/mining*`; migrations `016`, `017`, `060`, `061`, `063`, `066`, `070`, `072`, `073`, `074`, `085`, `086`, `101` | none scoped beyond game settings | direct resource/equipment writes; coin buy/sell through economy; game XP/world identity | extensive mining cog/db/services/utils/views tests and invariant | **Done/Partial** — deepest product loop; also biggest fragmentation source. |
| Fishing | `fishing` | `games`/activities | `fish`, `fishlog`; current code includes many related commands/buttons | `FishingMenuView`, `FishingCastView`, bait shop, rod shop, rod recipe browser, structures hub, dock/boathouse/fishery/tide pool | `fishing_workflow`; pure modules for fish, bait, rods, energy, venue, weather, weight, rewards, gear, minigame, curios | `utils/db/games/fishing*`; migrations `075`, `076`, `087`, `088`, `091`, `094`, `095`; uses mining inventory for some materials | none found | item/energy/collection writes; economy purchases; game XP | broad fishing workflow/bait/charm/curio/rod/db/utils/view tests | **Done/Partial** — best collection/odds/crafting loop; should become shared `CollectionGameSpec`. |
| Creatures | `creature` | `games`/activities | `creatures`, `catch`, `dex`, `cbattle`, `cbrecord`, `cbattletop` | `CreatureMenuView`, dex filter/select, challenge select, battle challenge/rematch/render | `creature_workflow`, `creature_battle_service`; pure creature catalog/battle/encounters | `utils/db/games/creatures.py`, `creature_battles.py`; migrations `077`, `082`; data `creatures.json` | none found | collection/PvP record writes; game XP | creature workflow/battle/catalog/menu/challenge/rematch tests | **Done/Partial** — high-value catch+dex+PvP template; needs live owner cert. |
| Farm | `farm` | `games`/activities | `farm` | `FarmMenuView`, `FarmShopView` | `farm_workflow`; pure farm math/state | `utils/db/games/farm.py`; migration `090_chicken_farm.sql` | none found | idle settle-once collect; economy purchases; leaderboard provider | farm workflow/db/utils/menu tests | **Done/Partial** — cleanest idle accrual model; preserve. |
| Shared game state | n/a service | used by games | n/a | n/a | `game_state_service`, `game_state_cleanup` | `utils/db/games/game_state.py`; migrations `015`, `018` | TTL constants | checkpoint save/load/clear/list stale; recovery/refund use | `test_game_state_service` | **Done as primitive** — rebuild should formalize session persistence policy. |
| Shared game XP | n/a service | cross-game | n/a | identity/profile displays | `game_xp_service` | `utils/db/games/game_xp.py`; migration `065_game_xp.sql` | none | `award`, `emit_award_events`, `world_identity` | game XP db/service tests | **Done/Partial** — good cross-game progression primitive. |

### Subsystem registry and help

| Surface | File(s) | Role | Current state |
|---|---|---|---|
| Immutable subsystem metadata | `disbot/utils/subsystem_registry.py` | registry key, display name, entry points, visibility, parent hub, hub group, dependencies, capabilities | Strong source of truth; rebuild should make this schema typed/data-driven. |
| Hub presentation registry | `disbot/utils/hub_registry.py` | top-level hub display/order/children/cross-links | Strong idea; currently separate from route/action specs. |
| Help catalogue/panels | `disbot/cogs/help_cog.py` and help catalogue services | resolves visible commands, hub panels, back to help | Useful unified discovery layer; rebuild should avoid command-only hidden features. |

## 4. Best ideas/functions/classes to preserve

| Source | Problem solved | User value | Technical value | Rebuild decision | Hidden dependencies |
|---|---|---|---|---|---|
| `services/economy_service.credit/debit/transfer/bet_and_settle/refund` | safe coin mutation with audit | trustworthy balances, refunds, wagering | sole writer, transaction variants, audit reasons | **Copy idea, redesign API** as `EconomyLedger`/`CurrencyMutationResult` | DB economy tables, audit log, event bus, invariant tests, reason taxonomy |
| `services/xp_service.award/import_level/reset` | shared XP mutation and level transitions | consistent rank/progression | sole writer, event emission | **Copy nearly as-is conceptually** into `ProgressionTrackSpec` | XP DB, role sync, level-up events, settings |
| `services/karma_service.give` | peer reputation with cooldown/caps/self-block | social recognition without spam | audited seam and typed errors | **Copy idea** | karma settings, reaction listener, daily cap/cooldown DB |
| `services/treasury_service.contribute/disburse` | collective server wallet | community funding/sinks | server-owned balance model | **Redesign around idea** | economy debit/credit, manager permissions, treasury table |
| `views/economy/main_panel.EconomyPanelView` | central money hub | balance/work/shop/inventory/treasury reachable | persistent hub route | **Redesign around unified hub grammar** | registry, child panels, public/ephemeral choices |
| `cogs/inventory_cog.UnifiedInventoryView` + `_group_page_by_rarity` | readable mixed inventory browser | large inventory is understandable | pure grouping/sorting helpers | **Copy helper ideas** | item metadata from multiple catalogs; owner-gated actions |
| `services/blackjack_engine` | pure blackjack math | fair cards/hand values | deterministic unit-tested engine | **Copy nearly as-is** | view/cog game-state; omitted rule decisions |
| `views/blackjack/solo_view.BlackjackView` and result view | full interactive card loop | hit/stand/double/replay/back | action view + replay pattern | **Redesign around `GameViewBase`** | economy service, timeouts, user authority |
| `views/blackjack/pvp_view` + `SettleOnceMixin` usage | prevent duplicate settlement | no double payout/loss | idempotent interaction settlement | **Copy idea into `ChallengeSession`** | economy escrow, interaction replay behavior |
| `views/games/blackjack_panel.BlackjackPanelView` | game-specific landing page | solo/bet/PvP/tournament/rules from one place | reusable panel composition | **Copy pattern, standardize** | games hub back buttons, custom modals |
| `services/game_state_service.save/load/clear/list_stale` | restart checkpoints for sessions | fewer lost tournaments/pending games | typed-ish JSON state with TTL/version | **Copy idea, strengthen typing** | migrations 015/018, cleanup, recovery code |
| `services/game_xp_service.award/world_identity` | cross-game identity | global game progression/name/title | reusable game progression | **Copy idea** | game_xp DB, mining titles, profile displays |
| `services/mining_workflow.mine/explore/dig/craft/buy/sell/equip/save_loadout/build_structure` | deep resource/progression economy | lots to do and optimize | vertical workflow concentrated in service | **Redesign around shared specs** | many mining DB modules, economy, equipment, assets |
| `utils/mining/grid.py` + `mining_workflow.dig/descend` | deterministic exploration map | spatial mining fantasy | pure seed/grid math | **Copy idea** | guild seed/world DB, depth records |
| `utils/mining/recipes.py` + recipe browser | crafting visibility | clear next goals | data-driven recipes | **Copy idea as `CraftingRecipeSpec`** | item catalog, inventory source, forge gates |
| `views/mining/gear_panel` + character render | gear optimization and visual identity | paper-doll/status payoff | renderer fallback, equipment stats | **Redesign around `CardRendererSpec`** | gear assets, Pillow optional, equipment DB |
| `services/fishing_workflow.begin_cast/commit_catch` | staged cast/reel loop | active minigame with anticipation | separates start parameters from commit | **Copy idea** | energy, bait, rod, weather, venue, gear stats |
| `utils/fishing/weather/weight/rewards/minigame` | odds modifiers and catch properties | variety and trophy chase | pure math modules | **Copy nearly as-is conceptually** | fish data, balancing docs/tests |
| `fishing_workflow.craft_bait/craft_pearl_bait/craft_rod/craft_charm/craft_curio` | multiple material sinks | long-term goals beyond selling | repeatable recipes and material consumption | **Extract shared crafting primitive** | mining inventory store, fishing catalogs |
| `views/fishing/rod_recipe_browser.RodRecipeBrowserView` | live craft progress | users know what to collect next | recipe progress UI | **Copy UX pattern** | eligible-count helpers, fish/material catalogs |
| `services/creature_workflow.catch` | catch/collect loop | collection progress and random encounters | compact workflow with XP | **Copy idea** | creatures DB/data, game XP |
| `services/creature_battle_service.build_normalized_team/resolve_pvp` | fair creature PvP | collection can be used competitively | pure normalized battle resolver | **Copy idea** | creature catalog, battle records, challenge UI |
| `views/creature/menu.CreatureDexView` | filtered collection browser | understand collection gaps | generic dex filter pattern | **Copy as `CollectionDexSpec`** | creature elements/data |
| `services/farm_workflow.collect/buy_chicken/upgrade_coop` | idle accrual with upgrades | reward for returning | simple settle-once math | **Copy nearly as-is conceptually** | farm DB, economy, time source |
| `cogs/leaderboard_cog.LeaderboardView` | unified standings | social comparison | provider-like rendering | **Redesign as `LeaderboardSpec`** | per-domain persisted stats, card renderer |
| `views/games/hub.discover_game_children` / `views/community/hub.discover_community_children` | dynamic hub lists | discoverability | registry-driven UI | **Copy idea** | parent_hub/cross-link contracts |
| `views/games/common.BackToPanelButton` and hub back helpers | navigation consistency | less dead-end UI | simple reusable component | **Copy and make universal** | panel builder callbacks |

## 5. Game/economy loop extraction and future primitives

### Daily/recurring rewards

- **Current evidence:** economy `daily`, fishing energy regeneration, farm idle egg accrual, XP per message, karma daily caps/cooldowns.
- **Reusable primitive:** `RewardSpec` with `cadence`, `cooldown`, `cap`, `grant vector`, `audit reason`, and `presentation`.
- **Fresh-repo target:** recurring rewards should never be ad hoc commands; they should be `RewardClaim` instances with standardized cooldown messaging and audit.

### Work/earn actions

- **Current evidence:** economy work jobs, mining mine/harvest/sell, fishing catches/drops, farm collect, creature catch XP.
- **Reusable primitive:** `GameActionSpec` (`cost`, `roll`, `rewards`, `state changes`, `cooldown`, `public/private result`).
- **Fresh-repo target:** every earn action returns a typed result object that views can render consistently.

### Spend/sink actions

- **Current evidence:** shop purchases, mining buy/repair/craft/build/vault upgrade, fishing rods/bait/charms/structures, farm chickens/coops, treasury contributions, blackjack/RPS wagers.
- **Reusable primitive:** `CostVector` + `EconomyLedger` + `InventoryMutationResult`.
- **Fresh-repo target:** coin and item spends should share validation, preview, confirmation, and transaction semantics.

### Inventory and item use

- **Current evidence:** `inventory_cog` browser, mining item use/equip/unequip/cook, fishing bait/rod/charms/curios, equipment loadouts.
- **Reusable primitive:** `ItemCatalogSpec` with item type, rarity, stackability, value, use action, equip slot, source game, display fields.
- **Fresh-repo target:** separate physical tables may remain, but UI reads from one catalog/index.

### Crafting/upgrades

- **Current evidence:** mining recipes/forge/workshop/structures; fishing bait/pearl bait/rods/charms/curios/structures; farm upgrades.
- **Reusable primitive:** `CraftingRecipeSpec` and `UpgradeTrackSpec` with requirements, preview, progress, craft result, and failure reasons.
- **Fresh-repo target:** recipe browsers should be generic and fed by data, not hand-built per game.

### Collection/dex/logbook

- **Current evidence:** fish catch log/species/best weight, creature dex/elements, mining inventory/titles/world identity, curios, farm flock.
- **Reusable primitive:** `CollectionDexSpec` with discovered/undiscovered, filters, sort, per-entry stats, and completion metrics.
- **Fresh-repo target:** every collection game gets the same dex, detail page, progress bar, and leaderboard integration.

### Leaderboards

- **Current evidence:** unified leaderboard provider, community spotlight, counting leaderboard, fishing/farm/creature providers, XP/economy standings.
- **Reusable primitive:** `LeaderboardSpec` with `rank_source`, `metric`, `tie_breakers`, `scope`, `empty_state`, `card_renderer`, `privacy`.
- **Fresh-repo target:** adding a game leaderboard requires only persisted stats plus a spec.

### PvP challenge flows

- **Current evidence:** blackjack PvP challenge, RPS PvP challenge/move picker, creature battle challenge/rematch, deathmatch challenge, tournament registration.
- **Reusable primitive:** `ChallengeSession` with participants, stake/escrow, accept/decline/timeout, authority checks, settle-once, rematch, back route.
- **Fresh-repo target:** one challenge base handles custom IDs, timeouts, persistent checkpoint policy, and duplicate interactions.

### Idle accrual/settle-once flows

- **Current evidence:** farm collect, fishing energy, mining energy, structure effects, cooldown-like work/daily.
- **Reusable primitive:** `IdleAccrualSpec` with `last_settled_at`, production rate, capacity, modifiers, collect transaction.
- **Fresh-repo target:** idle games should compute accrual from state at read/collect time, not schedule background grants.

### Pure simulation/math engines

- **Current evidence:** blackjack engine, fishing odds/minigame/weather/weight, mining grid/rewards/energy/capacity, creature battle, farm math.
- **Reusable primitive:** `GameEngine` modules with no Discord/DB imports and simulation tests.
- **Fresh-repo target:** every product loop has a pure engine package plus adapter layer.

### Game XP / cross-game progression

- **Current evidence:** `game_xp_service`, mining titles, world identity, game activity awards.
- **Reusable primitive:** `ProgressionTrackSpec` for global bot XP and per-game XP, with events and unlock hooks.
- **Fresh-repo target:** avoid hard-coded game names; registry declares progression tracks.

### Persistent vs non-restart-safe state

- **Current evidence:** `game_state_service` checkpoint rows; runtime docs call out in-process counting/blackjack/RPS state; blackjack/RPS have recovery/refund tests for money safety.
- **Reusable primitive:** `GameSessionPersistencePolicy` (`ephemeral`, `checkpointed`, `authoritative`) with TTL, recovery handler, refund handler.
- **Fresh-repo target:** every game declares restart behavior before implementation.

### Visual cards/PIL/assets

- **Current evidence:** leaderboard cards, mining gear/character render, world cards, creature/fishing/mining embeds, asset folders.
- **Reusable primitive:** `CardRendererSpec` with data projection, asset manifest, fallback embed, cache key.
- **Fresh-repo target:** rendering is optional and tested; missing/corrupt assets degrade gracefully.

## 6. User-facing UI grammar

### Best current UX conventions

- **Actionable hubs:** Games, Economy, and Community hubs discover children from the registry and give buttons, not just command lists.
- **Game-specific panels:** Blackjack and deathmatch panels are strong: overview, main actions, rules, challenge, and back route are in one place.
- **Collection browsers:** inventory grouping/sort/filter, creature dex filters, fishing log, mining recipe browser, and rod recipe progress are strong patterns.
- **Back buttons:** `BackToPanelButton`, `attach_back_to_games_button`, `attach_back_to_economy_button`, and `attach_back_to_community_button` are valuable, even if fragmented.
- **Result views with replay/rematch:** blackjack replay, RPS replay, creature rematch, and deathmatch result back navigation are good retention loops.
- **Confirmation/progress views:** treasury contribution modal, blackjack custom bet modals, mining build modal, crafting progress browsers, and challenge accept/decline flows are good patterns.
- **Rules/how-to affordances:** blackjack rules, mining how-to, creature how-to/dex, fishing menu/rules reduce hidden mechanics.

### Inconsistent or fragmented UX conventions

- **Different base classes:** `PersistentView`, `HubView`, `BaseView`, raw `discord.ui.View`, and in-cog views are mixed without a single game/session base.
- **Public vs ephemeral:** hubs often edit/respond ephemerally; game sessions may be public; command-only features vary. A rebuild needs a response policy per action type.
- **Timeout behavior:** solo blackjack 120s, PvP 60s, tournaments configurable, challenge views custom, mining/fishing panels different. Standardize stale-game UX.
- **Back/help/hub navigation:** multiple attach helpers exist. Rebuild should make `Back`, `Home`, `Help`, and `Rules` route slots universal.
- **Selectors and pagination:** category selects, type selects, item selects, leaderboards, dex filters, recipe browsers, and shop tables duplicate paging/list logic.
- **Hidden command-only surfaces:** some deep actions are reachable from panels, others remain command-first or in-cog; completion docs repeatedly identify missing buttons as gaps.
- **Game state messages:** some games disable controls and show result views; others rely on in-memory objects or command replies.

### Recommended fresh UI grammar

- `HubRoute`: top-level or child hub with registry-backed children, cross-links, and visibility.
- `GamePanel`: overview + primary actions + collection/progression + rules + back.
- `ActionView`: a single action session with owner/participant authority, timeout, result renderer.
- `BrowserView`: shared pagination/filter/sort for inventory, dex, recipes, leaderboards.
- `ConfirmModal/View`: standardized custom amount/stake/build/contribute flows.
- `ResultView`: replay/rematch/back/share buttons and disabled stale controls.

## 7. Hidden dependencies and rebuild hazards

1. **Coin sole-writer invariant.** Architecture and tests enforce balance mutation through `economy_service`. A rebuild must preserve this stronger than source does today: no direct table update, no hidden game mint, every mutation reason typed.
2. **XP sole-writer invariant.** `xp_service` owns shared XP. Game XP is separate; distinguish global XP, per-game XP, and social karma.
3. **Karma service invariant.** Karma grants include anti-abuse rules; reaction grants must use same service.
4. **Cross-game economy dependencies.** Mining, fishing, farm, blackjack, RPS, proof-channel-like rewards, and treasury all touch coins differently. Wagers need escrow/refund semantics; shops/crafting need cost vector transactions.
5. **Inventory fragmentation.** Mining inventory doubles as generic material store for fishing pearls/coral/curios; fishing rods/bait/venue/energy use separate tables; generic inventory browser aggregates views. Rebuild needs explicit catalog ownership and item namespace rules.
6. **Registry parent-hub assumptions.** `hub_registry.HUBS.primary_children` must match `SUBSYSTEMS.parent_hub`; Help/hubs rely on this roster. Fresh repo should generate one from the other or validate at startup/CI.
7. **Persistent custom IDs and views.** Persistent hubs/custom IDs must remain stable across restarts. Games with dynamic session IDs need a versioned custom-id scheme.
8. **Migrations/table schemas.** Relevant migrations include `003`, `005`, `014`, `015`, `016`, `017`, `018`, `019`, `060`, `061`, `063`, `065`, `066`, `070`, `072`, `073`, `074`, `075`, `076`, `077`, `082`, `085`, `086`, `087`, `088`, `090`, `091`, `092`, `093`, `094`, `095`, `101`. A clean rebuild should not blindly port these; derive a smaller schema from primitives.
9. **Asset paths.** Mining gear/character render and other visual cards depend on assets under `disbot/assets/`; creatures/fishing depend on data JSON. Missing owner art must not block mechanics; use manifests and fallbacks.
10. **Data files.** `disbot/data/fishing/fish.json` and `disbot/data/creatures/creatures.json` are product content sources. Treat content schema as versioned, not incidental.
11. **Leaderboard assumptions.** Not every game has per-user persisted stats. Casino, blackjack, and word chain need new stat writes before unified leaderboards are honest.
12. **Restart-safety decisions.** Some in-memory game sessions are accepted if money-safe; others checkpoint. Rebuild must make this explicit per game and test recovery/refund.
13. **Rate limits/concurrency locks.** Economy and XP service concurrent tests exist. Challenge settle-once tests exist. Idle collect/crafting should use transaction locks or idempotency.
14. **Owner-gated art/content/future mechanics.** Inventory item actions, live walkthroughs, some art/content drops, and blackjack rule decisions remain owner/live-gated in docs. Do not infer product completion from source presence.
15. **Help/actionability contracts.** Games hub children are expected to expose real action buttons. Hidden command-only features degrade product value.

## 8. Fragmentation and duplication inventory

### Critical rebuild lessons

- **Do not duplicate balance mutation paths.** Files: `economy_service.py`, mining/fishing/farm/blackjack/RPS workflows. Lesson: one ledger, typed mutation result, no direct coin writes.
- **Do not let each game invent challenge/session lifecycle.** Files: blackjack PvP/tournament views, RPS views, deathmatch panel/cog, creature challenge/rematch, casino poker. Lesson: `ChallengeSession` + `GameSessionPersistencePolicy`.
- **Do not split inventory UX from item ownership.** Files: `inventory_cog.py`, `utils/db/inventory.py`, `utils/db/games/mining*`, `fishing*`, creature/farm stores. Lesson: catalog/index with game-specific storage adapters.
- **Do not hide product loops behind commands.** Completion docs repeatedly push panels/buttons. Lesson: every registry child needs a `GamePanel`/`HubRoute` route.

### Important improvements

- **Centralize browser/pagination/filtering.** Files: inventory category views, mining recipe/market/gear selectors, fishing rod recipe/bait/structure views, creature dex, leaderboard select.
- **Centralize stale/timeout UX.** Files: blackjack, RPS, deathmatch, creature, casino, fishing cast. Use standard disabled state + result/reopen action.
- **Centralize public/ephemeral policy.** Hubs can be private, game sessions often public, admin flows private; make response policy explicit.
- **Standardize settings/schema exposure.** XP/economy/karma/blackjack/deathmatch/RPS have schemas; many games rely on constants/data only.
- **Standardize audit event naming.** Economy audit has reason strings; chain has mutation result/events; karma has source. Fresh repo should use event/reason enums.

### Cleanup

- In-cog view classes for community spotlight/general/four_twenty/chain could move behind shared view primitives in a rebuild.
- Multiple `attach_back_to_*` helpers can become one route-aware back button.
- Repeated select option formatting, item line rendering, and empty-state embed code can become UI components.
- Naming drift between command aliases, registry keys, and cogs should be mechanically validated.

### Acceptable specialization

- Blackjack hand rendering and rules are game-specific.
- Fishing weather/weight/venue/rod math is domain-specific.
- Mining spatial grid/depth/gear wear is domain-specific.
- Creature elements/battle normalization is domain-specific.
- Farm idle math is small enough to stay specialized behind a common idle interface.

## 9. Future new-repo recommendations tied to source evidence

1. **`EconomyLedger`** — based on `economy_service` and `economy_audit_log`. Owns all coin balance mutations, escrow, refunds, transfers, treasury movement, and audit events.
2. **`CurrencyMutationResult`** — based on `TreasuryResult`, economy service errors, and work/shop result views. Standardizes success/failure/balance delta/new balance/audit id.
3. **`ProgressionTrackSpec`** — based on `xp_service`, `game_xp_service`, mining titles/world identity, fishing/creature XP. Defines level curve, award actions, unlocks, events.
4. **`RewardSpec`** — based on daily/work/farm collect/fishing drops/mining harvest. Declares cadence, cooldown, reward roll, cap, and audit.
5. **`ItemCatalogSpec`** — based on mining items/equipment, fishing fish/bait/rods/curios, creature catalog, inventory browser metadata. Unifies display names, rarity, value, stack/equip/use semantics.
6. **`CraftingRecipeSpec`** — based on mining recipes, fishing bait/rod/charm/curio recipes, farm upgrades. Supports material progress, craft button eligibility, transaction preview.
7. **`CollectionDexSpec`** — based on creature dex and fishing log; supports filters, undiscovered states, collection percentage, best record fields.
8. **`GameActionSpec`** — based on mining `mine/dig/explore`, fishing `begin_cast/commit_catch`, creature `catch`, farm `collect`, economy `work`. Returns typed action results.
9. **`GameViewBase`** — based on `HubView`, `BaseView`, `PersistentView`, blackjack/RPS/deathmatch custom views. Handles owner/participant checks, response policy, timeout, stale state, back/help/rules slots.
10. **`ChallengeSession`** — based on blackjack/RPS/deathmatch/creature challenge flows. Handles participant selection, accept/decline, stake/escrow, timeout/refund, settle-once, rematch.
11. **`IdleAccrualSpec`** — based on farm, fishing/mining energy, structures. Computes elapsed production with capacity and modifier tracks.
12. **`LeaderboardSpec`** — based on `LeaderboardCog` providers and current-state additions for fishing/farm. Requires rank source, metric, tie-breakers, empty state, display/card fields.
13. **`CardRendererSpec`** — based on leaderboard cards, mining render, world cards, and embed fallbacks. Declares asset manifest, renderer, fallback, cache/invalidation.
14. **`GameSessionPersistencePolicy`** — based on `game_state_service` and runtime docs. Every game must declare `ephemeral`, `checkpointed`, or `authoritative`, with recovery/refund tests.
15. **`RouteRegistry`** — based on `subsystem_registry` + `hub_registry` + Help. One typed manifest should declare key, commands, hub, children, settings, permissions, panel builder, and completion metadata.

## 10. Handoff to other mapping sessions

### Needs from Part 1 — platform/UI primitives

- Final route/hub/view base recommendations for `HubView`, `BaseView`, `PersistentView`, safe interaction helpers, custom-id versioning, and public/ephemeral policy.
- Help catalogue and registry architecture: whether `subsystem_registry` and `hub_registry` should merge in a clean repo.
- Standard browser/pagination/select/modal components.
- Card rendering/asset manifest/fallback policy.
- Session persistence/custom ID/runtime session conventions.

### Needs from Part 2 — admin/safety dependencies

- Permission/capability model for economy settings, treasury disbursement, counting/chain channel configuration, XP/karma settings, and admin resets.
- Audit log schema and governance event taxonomy for currency, XP, karma, item grants, treasury, and settings changes.
- Anti-abuse/rate-limit policy for work/daily/karma/reactions/games.
- Production migration and rollback rules for user balances/items/game state.
- Operator diagnostics needed for “lost coins”, “lost XP”, “stuck tournament”, “stale challenge”, and “bad item grant”.

### Needs from Part 4 — AI/data/knowledge dependencies

- Whether AI assistant should summarize or guide user-facing game/product loops without mutating state.
- Content/data schema recommendations for fish/creatures/items/recipes and how AI can safely explain them.
- Knowledge-card rendering conventions that should align with game card renderers.
- Boundaries between AI recommendations and authoritative game mechanics; AI must not invent odds, rewards, or item effects outside versioned data specs.

## 11. Rebuild conclusion

The current bot has enough good product material to justify using it as a design mine for a clean rebuild, but not by copying the repo structure. The highest-value preservation target is the **loop grammar**:

1. hub → panel → action → result → replay/back;
2. earn → collect → craft/upgrade/equip → improve odds/output;
3. collection → dex/logbook → leaderboard/social proof;
4. challenge → accept/escrow → play → settle once → rematch;
5. idle accrue → settle once → reinvest.

A fresh SuperBot should start from shared primitives for these loops and then plug in mining, fishing, creatures, farm, blackjack, RPS, deathmatch, counting, chain, economy, XP, karma, inventory, treasury, and leaderboards as specs/adapters. That would keep the current bot's strongest user-facing ideas while avoiding the fragmentation that came from organically growing each game and hub separately.
