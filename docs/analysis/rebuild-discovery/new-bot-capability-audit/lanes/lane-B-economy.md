# Lane B — Economy & Character-sim (Axis 1)

> **Status:** `reference` — this lane's workspace. The surface-unit inventories below are **pre-extracted** (facts only, tier columns blank). The Lane B agent **verifies + completes them against source**, fills BOTH tier columns, writes each subsystem's §2 manifest sketch, dispositions tier-3s, and adds reconsider/optimize recommendations — per [`../BRIEF.md`](../BRIEF.md). Treat the inventory as a starting scaffold, not ground truth.

**Subsystems:** economy, inventory, treasury, mining, fishing, creature, farm, xp, casino, four_twenty, counters

**Method:** [`../BRIEF.md`](../BRIEF.md) · [`../PARTITION.md`](../PARTITION.md) · `tools/grammar_spike/` · `../ground-truth/command-surface.json`.

---

### economy
_cogs: disbot/cogs/economy_cog.py_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !economymenu | command | disbot/cogs/economy_cog.py:66 | | | |
| /economy | command | disbot/cogs/economy_cog.py:85 | | | |
| !daily | command | disbot/cogs/economy_cog.py:218 | | | |
| !work | command | disbot/cogs/economy_cog.py:284 | | | |
| !shop | command | disbot/cogs/economy_cog.py:326 | | | |
| !balance (bal, wallet) | command | disbot/cogs/economy_cog.py:335 | | | |
| !setlogchannel | command | disbot/cogs/economy_cog.py:353 | | | |
| !joblist (jobs) | command | disbot/cogs/economy_cog.py:365 | | | |
| EconomyPanelView | panel | disbot/views/economy/main_panel.py:43 | | | |
| _ShopView | panel | disbot/views/economy/shop_panel.py:28 | | | |
| _ShopSubView | panel | disbot/views/economy/shop_panel.py:125 | | | |
| _WorkView | panel | disbot/views/economy/work_panel.py:38 | | | |
| _WorkSubView | panel | disbot/views/economy/work_panel.py:174 | | | |
| _WorkResultView | panel | disbot/views/economy/work_panel.py:207 | | | |
| economy.log_channel (binding) | setting | disbot/core/runtime/config_arbitration.py:579 | | | |
| capabilities: economy.currency.view/earn, shop.browse/buy, settings.configure | setting | disbot/utils/subsystem_registry.py:166-172 | | | |
| on_ready (ensure economy-log channel) | listener | disbot/cogs/economy_cog.py:100 | | | |
| on_guild_join (ensure economy-log channel) | listener | disbot/cogs/economy_cog.py:106 | | | |
| bus.emit(EVT_BALANCE_CHANGED) x5 | event | disbot/services/economy_service.py:81,118,270,278,319 | | | |
| table: economy (coins/streak/last_daily/last_worked) | store | disbot/utils/db/economy.py:224-296 | | | |
| table: xp (coins column, level, work pay) | store | disbot/utils/db/economy.py:25-210 | | | |
| table: job_progress (times_worked per job) | store | disbot/utils/db/economy.py:308-327 | | | |
| table: economy_audit_log | store | disbot/utils/db/economy.py:88-187 | | | |
| help entry — economy hub via build_help_menu_view | help | disbot/cogs/economy_cog.py:73 | | | |

**Unit kinds present:** command, panel, setting, listener, event, store, help
**Structural-pattern flags:** gateway listener (`@commands.Cog.listener()` on `on_ready`/`on_guild_join` for auto-provisioning the economy-log channel); no wait_for wizard, no scheduled loop, no voice; persistent panel view (`EconomyPanelView` via `panel_manager`) with cooldown-gated sub-flows (daily/work).

---

### inventory
_cogs: disbot/cogs/inventory_cog.py_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !inventory (alias !inv) | command | disbot/cogs/inventory_cog.py:562 | | | |
| _CategoryView | panel/view | disbot/cogs/inventory_cog.py:271 | | | |
| UnifiedInventoryView (hub) | panel/view | disbot/cogs/inventory_cog.py:465 | | | |
| build_help_menu_view | panel/view (help-menu builder) | disbot/cogs/inventory_cog.py:574 | | | |
| send_panel usage (inventory hub) | panel/send | disbot/cogs/inventory_cog.py:572 | | | |
| inventory.item.view (capability) | setting/capability | disbot/utils/subsystem_registry.py:193 | | | |
| inventory.item.use (capability) | setting/capability | disbot/utils/subsystem_registry.py:194 | | | |
| inventory.craft.recipe (capability) | setting/capability | disbot/utils/subsystem_registry.py:195 | | | |
| inventory table | store | disbot/utils/db/migrations.py:234 | | | |
| get_inventory | store/helper | disbot/utils/db/inventory.py:13 | | | |
| add_item | store/helper | disbot/utils/db/inventory.py:21 | | | |
| try_grant_unique_item | store/helper | disbot/utils/db/inventory.py:39 | | | |
| has_item | store/helper | disbot/utils/db/inventory.py:69 | | | |

**Unit kinds present:** command, panel/view, setting (registry capability), store (table + db helpers)
**Structural-pattern flags:** none obvious — no @bot.event/bus.on listener, no wait_for wizard, no scheduled loop, no voice found in disbot/cogs/inventory_cog.py; ⚠ unverified whether bus.emit/emit_audit_action is called elsewhere (e.g. economy_cog/mining_cog) for inventory-owned events — not found directly in inventory_cog.py or utils/db/inventory.py.

---

### treasury
_cogs: disbot/cogs/treasury_cog.py_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !treasury (aliases: bank, pool) | command | disbot/cogs/treasury_cog.py:42-50 | | | |
| !treasury contribute (aliases: donate, deposit) | command | disbot/cogs/treasury_cog.py:52-59 | | | |
| !treasury grant (aliases: disburse, payout) | command | disbot/cogs/treasury_cog.py:61-80 | | | |
| build_help_menu_view (Help-menu hook) | command-adjacent/help | disbot/cogs/treasury_cog.py:84-89 | | | |
| TreasuryView | panel/view | disbot/views/treasury/menu.py:76-120 | | | |
| TreasuryView.contribute_btn ("Contribute" button) | panel/view | disbot/views/treasury/menu.py:102-112 | | | |
| TreasuryView.refresh_btn ("Refresh" button) | panel/view | disbot/views/treasury/menu.py:114-120 | | | |
| _ContributeModal | panel/view | disbot/views/treasury/menu.py:123-158 | | | |
| Economy hub "🏛️ Treasury" button (economy:treasury) | panel/view (entry point) | disbot/views/economy/main_panel.py:292-308 | | | |
| treasury.pool.view / treasury.pool.contribute / treasury.pool.disburse capabilities | setting/registry | disbot/utils/subsystem_registry.py:206-229 | | | |
| guild_treasury table | store | disbot/migrations/092_guild_treasury.sql:15-19 | | | |
| get_treasury / credit_treasury / try_debit_treasury (CRUD primitives) | store | disbot/utils/db/treasury.py:24-88 | | | |
| treasury_service.contribute (audited write) | event/mutation | disbot/services/treasury_service.py:70-118 | | | |
| treasury_service.disburse (audited write) | event/mutation | disbot/services/treasury_service.py:121-181 | | | |
| bus.emit(economy_service.EVT_BALANCE_CHANGED, reason=treasury:contribute) | event | disbot/services/treasury_service.py:104-111 | | | |
| bus.emit(economy_service.EVT_BALANCE_CHANGED, reason=treasury:disburse) | event | disbot/services/treasury_service.py:167-174 | | | |

**Unit kinds present:** command, panel/view, setting (capability registry, no user-facing settings_keys found), store, event (mutation-emitted, reused economy event name — treasury has no event of its own), help (Help-menu hook). No dedicated `listener` (`@bot.event`/`bus.on`) found for this subsystem — it only emits, does not subscribe.

**Structural-pattern flags:** none obvious (no stateful game loop, no gateway/listener subscription, no wait_for wizard, no scheduled loop, no voice). Treasury is a straightforward panel+modal+audited-mutation subsystem; note it reuses economy's `EVT_BALANCE_CHANGED` event rather than emitting its own event name, and has no `settings_registry`/`db.get_setting` entries — only `subsystem_registry.py` capability strings.

---

### mining
_cogs: disbot/cogs/mining_cog.py (Discord plumbing only); domain in disbot/services/mining_workflow.py; UI in disbot/views/mining/*_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !minemenu | command | disbot/cogs/mining_cog.py:57 | | | |
| !mine | command | disbot/cogs/mining_cog.py:91 | | | |
| !fastmine | command | disbot/cogs/mining_cog.py:102 | | | |
| !chop | command | disbot/cogs/mining_cog.py:118 | | | |
| !mineinv (aliases: mineinventory) | command | disbot/cogs/mining_cog.py:137 | | | |
| !minestats | command | disbot/cogs/mining_cog.py:150 | | | |
| !build (alias: craft) | command | disbot/cogs/mining_cog.py:193 | | | |
| !buildlist | command | disbot/cogs/mining_cog.py:209 | | | |
| !buildable | command | disbot/cogs/mining_cog.py:240 | | | |
| !explore | command | disbot/cogs/mining_cog.py:265 | | | |
| !use | command | disbot/cogs/mining_cog.py:281 | | | |
| !cook | command | disbot/cogs/mining_cog.py:292 | | | |
| !equip | command | disbot/cogs/mining_cog.py:315 | | | |
| !unequip | command | disbot/cogs/mining_cog.py:326 | | | |
| !gear | command | disbot/cogs/mining_cog.py:338 | | | |
| !loadout (alias: loadouts) | command | disbot/cogs/mining_cog.py:361 | | | |
| !character (aliases: profile, char) | command | disbot/cogs/mining_cog.py:411 | | | |
| !descend | command | disbot/cogs/mining_cog.py:441 | | | |
| !ascend | command | disbot/cogs/mining_cog.py:458 | | | |
| !mineworld | command | disbot/cogs/mining_cog.py:474 | | | |
| !sell | command | disbot/cogs/mining_cog.py:501 | | | |
| !sellall | command | disbot/cogs/mining_cog.py:516 | | | |
| !buy | command | disbot/cogs/mining_cog.py:522 | | | |
| !market | command | disbot/cogs/mining_cog.py:535 | | | |
| !vault | command | disbot/cogs/mining_cog.py:571 | | | |
| !stash | command | disbot/cogs/mining_cog.py:585 | | | |
| !unstash | command | disbot/cogs/mining_cog.py:605 | | | |
| !vaultupgrade | command | disbot/cogs/mining_cog.py:625 | | | |
| !skills | command | disbot/cogs/mining_cog.py:637 | | | |
| !skill | command | disbot/cogs/mining_cog.py:651 | | | |
| !titles | command | disbot/cogs/mining_cog.py:674 | | | |
| !forge | command | disbot/cogs/mining_cog.py:690 | | | |
| !home | command | disbot/cogs/mining_cog.py:706 | | | |
| !workshop | command | disbot/cogs/mining_cog.py:722 | | | |
| !repair | command | disbot/cogs/mining_cog.py:736 | | | |
| !quickcraft | command | disbot/cogs/mining_cog.py:750 | | | |
| !reset_inventory (admin) | command | disbot/cogs/mining_cog.py:758 | | | |
| MiningHubView (PersistentView, @register) | panel | disbot/views/mining/main_panel.py:146-147 | | | |
| MineGridView (BaseView) | panel | disbot/views/mining/grid_mine_view.py:84 | | | |
| MiningCharacterHubView (HubView) | panel | disbot/views/mining/character_hub.py:91 | | | |
| MiningForgeView (HubView) | panel | disbot/views/mining/forge_panel.py:76 | | | |
| MiningGearView (HubView) | panel | disbot/views/mining/gear_panel.py:358 | | | |
| MiningLoadoutView (HubView) | panel | disbot/views/mining/gear_panel.py:621 | | | |
| MiningHomeView (HubView) | panel | disbot/views/mining/home_panel.py:72 | | | |
| MiningHowToView (HubView) | panel | disbot/views/mining/how_to_panel.py:50 | | | |
| MiningMarketView (HubView) | panel | disbot/views/mining/market_panel.py:271 | | | |
| MiningRecipeBrowserView (HubView) | panel | disbot/views/mining/recipe_browser.py:240 | | | |
| MiningSkillsView (HubView) | panel | disbot/views/mining/skills_panel.py:65 | | | |
| MiningRespecView (HubView) | panel | disbot/views/mining/skills_panel.py:206 | | | |
| MiningTitlesView (HubView) | panel | disbot/views/mining/titles_panel.py:108 | | | |
| MiningVaultView (HubView) | panel | disbot/views/mining/vault_panel.py:153 | | | |
| MiningWorkshopHubView (HubView) | panel | disbot/views/mining/workshop_hub.py:41 | | | |
| MiningWorkshopView (HubView) | panel | disbot/views/mining/workshop_panel.py:159 | | | |
| capability: mining.resource.mine | setting | disbot/utils/subsystem_registry.py:279 | | | |
| capability: mining.resource.view | setting | disbot/utils/subsystem_registry.py:280 | | | |
| entry_points: minemenu, mine | setting | disbot/utils/subsystem_registry.py:269 | | | |
| dependency: economy (hard dep) | setting | disbot/utils/subsystem_registry.py:271 | | | |
| EVT_BALANCE_CHANGED (repair coin spend) | event | disbot/services/mining_workflow.py:258 | | | |
| EVT_BALANCE_CHANGED (_emit_balance helper) | event | disbot/services/mining_workflow.py:533 | | | |
| store: mining_inventory | store | disbot/utils/db/games/mining.py:32 | | | |
| store: mining_equipment | store | disbot/utils/db/games/mining_equipment.py:45 | | | |
| store: mining_gear_wear | store | disbot/utils/db/games/mining_gear_wear.py:53 | | | |
| store: mining_player_state (pos, depth, equipped_title, last_broken_item) | store | disbot/utils/db/games/mining_player_state.py:48 | | | |
| store: mining_world (grid seed) | store | disbot/utils/db/games/mining_grid.py:93 | | | |
| store: mining_loadout_presets | store | disbot/utils/db/games/mining_loadout.py:45 | | | |
| store: mining_structures | store | disbot/utils/db/games/mining_structures.py:26 | | | |
| store: mining_vault | store | disbot/utils/db/games/mining_vault.py:25 | | | |
| store: player_skills (shared, mining-consumed) | store | disbot/utils/db/games/player_skills.py:25 | | | |
| cog_check: guild-only gate | ⚠ unverified — structural, not a listener | disbot/cogs/mining_cog.py:47 | | | |

**Unit kinds present:** command, panel, setting, event, store
**Structural-pattern flags:** wait_for wizard likely inside modals (e.g. `_BuildModal` referenced in module docstring, disbot/cogs/mining_cog.py:8) — ⚠ unverified, not directly confirmed by grep; grid navigation (MineGridView) is a stateful roam/interact loop via persistent buttons, not a `@bot.event`/`bus.on` listener or scheduled loop. No `@bot.event`, `Cog.listener`, or `bus.on` found in mining files (mining only emits `bus.emit(EVT_BALANCE_CHANGED)`, it does not subscribe). No scheduled task loop or voice usage found.


---

### fishing
_cogs: disbot/cogs/fishing_cog.py_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !fish | command | disbot/cogs/fishing_cog.py:76 | | | |
| !fishing (fishmenu) | command | disbot/cogs/fishing_cog.py:87 | | | |
| !forecast (fishforecast, fishingweather) | command | disbot/cogs/fishing_cog.py:98 | | | |
| !sail (setsail) | command | disbot/cogs/fishing_cog.py:117 | | | |
| !fishlog (fishdex) | command | disbot/cogs/fishing_cog.py:131 | | | |
| !fishtop (topfishers) | command | disbot/cogs/fishing_cog.py:145 | | | |
| !trophies (bigfish, fishtrophy) | command | disbot/cogs/fishing_cog.py:172 | | | |
| !rod (rodshop, buyrod) | command | disbot/cogs/fishing_cog.py:197 | | | |
| !bait (baitshop, buybait) | command | disbot/cogs/fishing_cog.py:208 | | | |
| !craftbait (baitcraft) | command | disbot/cogs/fishing_cog.py:222 | | | |
| !craftcharm (charmcraft) | command | disbot/cogs/fishing_cog.py:246 | | | |
| !craftrod (rodcraft) | command | disbot/cogs/fishing_cog.py:272 | | | |
| !rodrecipes (rodrecipe, rrecipes) | command | disbot/cogs/fishing_cog.py:283 | | | |
| !craftpearl (pearlcraft) | command | disbot/cogs/fishing_cog.py:289 | | | |
| !curios (curio, carvings) | command | disbot/cogs/fishing_cog.py:319 | | | |
| !tidepool (reef, tidepools) | command | disbot/cogs/fishing_cog.py:350 | | | |
| !dock (pier, fishingdock) | command | disbot/cogs/fishing_cog.py:362 | | | |
| !boathouse (moorings, boat) | command | disbot/cogs/fishing_cog.py:374 | | | |
| !fishery (hatchery, fishfarm) | command | disbot/cogs/fishing_cog.py:386 | | | |
| !craftcurio (carve, curiocraft) | command | disbot/cogs/fishing_cog.py:399 | | | |
| build_help_menu_view (help-menu hook) | help | disbot/cogs/fishing_cog.py:423 | | | |
| FishingMenuView | panel/view | disbot/views/fishing/menu.py:203 | | | |
| FishingCastView | panel/view | disbot/views/fishing/cast_view.py:142 | | | |
| _FishingDoneView | panel/view | disbot/views/fishing/cast_view.py:545 | | | |
| RodShopView | panel/view | disbot/views/fishing/rod_shop.py:89 | | | |
| BaitShopView | panel/view | disbot/views/fishing/bait_shop.py:209 | | | |
| RodRecipeBrowserView | panel/view | disbot/views/fishing/rod_recipe_browser.py:104 | | | |
| TidePoolView | panel/view | disbot/views/fishing/tide_pool.py:84 | | | |
| DockView | panel/view | disbot/views/fishing/dock.py:80 | | | |
| BoathouseView | panel/view | disbot/views/fishing/boathouse.py:81 | | | |
| FisheryView | panel/view | disbot/views/fishing/fishery.py:82 | | | |
| StructuresView (⚠ unverified — not entry-linked from cog commands) | panel/view | disbot/views/fishing/structures_hub.py:93 | | | |
| capability: fishing.catch.fish | setting/capability | disbot/utils/subsystem_registry.py:313 | | | |
| capability: fishing.collection.view | setting/capability | disbot/utils/subsystem_registry.py:314 | | | |
| entry_points [fish, fishlog] (registry) | setting | disbot/utils/subsystem_registry.py:299 | | | |
| event: economy_service.EVT_BALANCE_CHANGED (rod purchase) | event | disbot/services/fishing_workflow.py:644 | | | |
| event: economy_service.EVT_BALANCE_CHANGED (bait purchase) | event | disbot/services/fishing_workflow.py:723 | | | |
| store: fishing_catch_log | store | disbot/migrations/075_fishing_catch_log.sql:10 | | | |
| store: fishing_rod | store | disbot/migrations/087_fishing_rod.sql:12 | | | |
| store: fishing_energy | store | disbot/migrations/088_fishing_energy.sql:14 | | | |
| store: fishing_bait | store | disbot/migrations/091_fishing_bait.sql:16 | | | |
| store: fishing_venue | store | disbot/migrations/094_fishing_venue.sql:12 | | | |

**Unit kinds present:** command, panel/view, help, setting/capability, event, store

**Structural-pattern flags:** wait_for wizard (FishingCastView bite/reel timing, disbot/views/fishing/cast_view.py) — no @bot.event/bus.on listener found in fishing_cog.py or fishing_workflow.py (⚠ unverified: only bus.emit calls confirmed, no bus.on subscriber found in fishing files); no scheduled loop or voice usage found.


---

### creature
_cogs: disbot/cogs/creature_cog.py, disbot/cogs/creature_battle_cog.py_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !catch (alias hunt) | command | disbot/cogs/creature_cog.py:58 | | | |
| !creatures (alias creaturemenu, pets) | command | disbot/cogs/creature_cog.py:69 | | | |
| !dex (alias collection) | command | disbot/cogs/creature_cog.py:78 | | | |
| !dextop (alias topcatchers) | command | disbot/cogs/creature_cog.py:85 | | | |
| !cbattle (alias creaturebattle) | command | disbot/cogs/creature_battle_cog.py:72 | | | |
| !cbrecord (alias battlerecord) | command | disbot/cogs/creature_battle_cog.py:89 | | | |
| !cbattletop (alias pvptop, battletop) | command | disbot/cogs/creature_battle_cog.py:96 | | | |
| CreatureMenuView | panel | disbot/views/creature/menu.py:60 | | | |
| CreatureDexView | panel | disbot/views/creature/menu.py:184 | | | |
| CreatureChallengeSelectView | panel | disbot/views/creature/menu.py:213 | | | |
| CreatureBattleChallengeView | panel | disbot/views/creature_battle/challenge.py:30 | | | |
| CreatureRematchView | panel | disbot/views/creature_battle/rematch.py:28 | | | |
| build_help_menu_view (creature_cog) | help | disbot/cogs/creature_cog.py:98 | | | |
| build_help_menu_view (creature_battle_cog) | help | disbot/cogs/creature_battle_cog.py:50 | | | |
| creature_collection_log table | store | disbot/migrations/077_creature_collection_log.sql:1 | | | ⚠ unverified line num, file exists |
| creature_battle_record table | store | disbot/migrations/082_creature_battle_record.sql:1 | | | ⚠ unverified line num, file exists |
| SUBSYSTEMS["creature"] capabilities/entry_points | setting | disbot/utils/subsystem_registry.py:324 | | | registry entry, no discrete settings_keys found |

**Unit kinds present:** command, panel, help, store, setting (registry entry only — no `settings_keys`/`db.get_setting` usage found)
**Structural-pattern flags:** wait_for-style challenge/accept view (CreatureBattleChallengeView) acting as a PvP challenge wizard; no @bot.event/bus.on listeners, no @tasks.loop scheduled loop, no voice usage, no audited emit_audit_action call (comment in creature_battle_service.py explicitly notes writes are not audit-emitted) — otherwise none obvious.

---

### farm
_cogs: disbot/cogs/farm_cog.py_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !farm (aliases: chickenfarm, coop) | command | disbot/cogs/farm_cog.py:43-44 | | | |
| build_help_menu_view (Help hub hook) | help | disbot/cogs/farm_cog.py:51-56 | | | |
| Explore-world "farm" entry (_register_farm_world / WorldEntry) | listener | disbot/cogs/farm_cog.py:59-98 | | | |
| FarmMenuView | panel/view | disbot/views/farm/menu.py:164 | | | |
| FarmMenuView.collect_btn (🥚 Collect) | panel/view | disbot/views/farm/menu.py:197-207 | | | |
| FarmMenuView.shop_btn (🛒 Shop) | panel/view | disbot/views/farm/menu.py:209-219 | | | |
| FarmMenuView.refresh_btn (🔄 Refresh) | panel/view | disbot/views/farm/menu.py:221-227 | | | |
| FarmShopView | panel/view | disbot/views/farm/menu.py:230 | | | |
| FarmShopView.buy_btn (🐔 Buy hen) | panel/view | disbot/views/farm/menu.py:253-260 | | | |
| FarmShopView.upgrade_btn (🏠 Upgrade coop) | panel/view | disbot/views/farm/menu.py:267-273 | | | |
| FarmShopView.back_btn (◀ Back) | panel/view | disbot/views/farm/menu.py:275-296 | | | |
| SUBSYSTEMS["farm"] capabilities (farm.egg.collect, farm.coop.manage) | setting | disbot/utils/subsystem_registry.py:364-386 | | | |
| economy_service.EVT_BALANCE_CHANGED emit on collect | event | disbot/services/farm_workflow.py:158-165 | | | |
| economy_service.EVT_BALANCE_CHANGED emit on buy_chicken | event | disbot/services/farm_workflow.py:235-242 | | | |
| economy_service.EVT_BALANCE_CHANGED emit on upgrade_coop | event | disbot/services/farm_workflow.py:296-303 | | | |
| chicken_farm table (per user+guild flock/coop/egg-accrual state) | store | disbot/migrations/090_chicken_farm.sql:12-19 | | | |
| get_chicken_farm / set_chicken_farm CRUD | store | disbot/utils/db/games/farm.py:42,97 | | | |

**Unit kinds present:** command, panel, listener (world-hub registration), help, setting, event, store

**Structural-pattern flags:** none obvious (no `@bot.event`/`bus.on` listeners, no `wait_for` wizard, no scheduled loop/ticker — idle accrual is pure `settle()` math computed on read per ADR-001/002 — no voice usage).


---

### xp
_cogs: disbot/cogs/xp_cog.py, disbot/cogs/xp/listener.py, disbot/cogs/xp/stage.py, disbot/cogs/xp/schemas.py_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !xpmenu | command | disbot/cogs/xp_cog.py:92 | | | |
| !rank | command | disbot/cogs/xp_cog.py:120 | | | |
| !givexp | command | disbot/cogs/xp_cog.py:179 | | | |
| !resetxp | command | disbot/cogs/xp_cog.py:197 | | | |
| !xpconfig | command | disbot/cogs/xp_cog.py:210 | | | |
| !xpimport | command | disbot/cogs/xp_cog.py:218 | | | |
| _XpHubView | panel | disbot/views/xp/main_panel.py:17 | | | |
| XpConfigView | panel | disbot/views/xp/config_panel.py:22 | | | |
| XpImportView | panel | disbot/views/xp/import_panel.py:30 | | | |
| XpImportSetupView | panel | disbot/views/xp/import_panel.py:213 | | | |
| _RankView | panel | disbot/views/xp/rank_view.py:19 | | | |
| _GiveXpModal | panel | disbot/views/xp/modals.py:208 | | | |
| _ResetXpModal | panel | disbot/views/xp/modals.py:251 | | | |
| _XpRangeModal | panel | disbot/views/xp/modals.py:290 | | | |
| _XpCooldownModal | panel | disbot/views/xp/modals.py:333 | | | |
| _XpChannelModal | panel | disbot/views/xp/modals.py:360 | | | |
| xp_min | setting | disbot/cogs/xp/schemas.py:75 | | | |
| xp_max | setting | disbot/cogs/xp/schemas.py:84 | | | |
| xp_cooldown | setting | disbot/cogs/xp/schemas.py:93 | | | |
| announce_channel (binding) | setting | disbot/cogs/xp/schemas.py:58 | | | |
| on_message listener (handle_message via stage pipeline) | listener | disbot/cogs/xp/listener.py:93 | | | |
| MessagePipelineStage.process (xp stage wrapper) | listener | disbot/cogs/xp/stage.py:35 | | | |
| EVT_XP_AWARDED emit | event | disbot/services/xp_service.py:126 | | | |
| EVT_LEVEL_UP emit | event | disbot/services/xp_service.py:136 | | | |
| EVT_XP_RESET emit | event | disbot/services/xp_service.py:239 | | | |
| audit.action_recorded (emit_audit_action, xp reset) | event | disbot/services/xp_service.py:247 | | | |
| xp table (user_id, guild_id, xp, level, messages, last_xp) | store | disbot/utils/db/xp.py:76 | | | |
| xp threshold role migration ⚠ unverified (may belong to role subsystem) | store | disbot/migrations/003_role_xp_thresholds.sql:1 | | | |

**Unit kinds present:** command, panel, setting, listener, event, store
**Structural-pattern flags:** gateway listener (on_message via MessagePipelineStage, effectively a `@bot.event`-style hook) present; no stateful game loop, no wait_for wizard beyond modals, no scheduled loop, no voice.


---

### casino
_cogs: disbot/cogs/casino_cog.py_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !casino | command | disbot/cogs/casino_cog.py:41 | | | |
| !poker (alias !holdem) | command | disbot/cogs/casino_cog.py:47 | | | |
| build_help_menu_view (help-menu hook) | help | disbot/cogs/casino_cog.py:67 | | | |
| CasinoHubView | panel/view | disbot/views/casino/hub.py:50 | | | |
| build_casino_hub_panel | panel | disbot/views/casino/hub.py:118 | | | |
| build_casino_hub_embed | panel | disbot/views/casino/hub.py:23 | | | |
| PokerLobbyView | panel/view | disbot/views/casino/poker_table.py:566 | | | |
| SeatLobbyView | panel/view | disbot/views/casino/poker_table.py:606 | | | |
| PokerEndView | panel/view | disbot/views/casino/poker_table.py:626 | | | |
| PokerSeatView | panel/view | disbot/views/casino/poker_table.py:685 | | | |

**Unit kinds present:** command, panel/view, help
**Structural-pattern flags:** stateful game loop (in-memory `_tables` dict keyed by channel_id, `PokerTable` class managing multi-seat live state, disbot/views/casino/poker_table.py:62-109); no listener/bus.on, no bus.emit/audit events found, no settings_registry entries found, no DB store/migration table found (ephemeral play-chips, not persisted) — otherwise none obvious (no wait_for wizard, no scheduled loop, no voice).


---

### four_twenty
_cogs: disbot/cogs/four_twenty_cog.py_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !420 (aliases fourtwenty, fourtwenty420) | command | disbot/cogs/four_twenty_cog.py:186 | | | |
| four_twenty.panel.view (_FourTwentyPanelView) | panel/view | disbot/cogs/four_twenty_cog.py:204 | | | |
| wisdom_btn button | panel/view | disbot/cogs/four_twenty_cog.py:218 | | | |
| fact_btn button | panel/view | disbot/cogs/four_twenty_cog.py:232 | | | |
| overview_btn button | panel/view | disbot/cogs/four_twenty_cog.py:246 | | | |
| FourTwentyStage (message_pipeline stage, registered in cog_load) | listener | disbot/cogs/four_twenty_cog.py:107 | | | |
| build_help_menu_view (help-menu direct-navigation hook) | help | disbot/cogs/four_twenty_cog.py:195 | | | |
| SUBSYSTEMS["four_twenty"] registry entry (capabilities/entry_points) | setting | disbot/utils/subsystem_registry.py:1031 | | | |

**Unit kinds present:** command, panel/view, listener, help, setting (registry entry only — no db.get_setting keys, no store tables, no bus.emit events found; subsystem is observe-only/stateless per module docstring).

**Structural-pattern flags:** listener via message-pipeline stage (`FourTwentyStage`, registered/unregistered in `cog_load`/`cog_unload`, not a raw `@bot.event`/`bus.on`) — no stateful game loop, no wait_for wizard, no scheduled loop, no voice. No `emit_audit_action`/`bus.emit` calls found (⚠ unverified beyond docstring claim "nothing here writes to the DB or mutates economy/XP").

---

### counters
_cogs: disbot/cogs/counters_cog.py (+ disbot/cogs/counters/schemas.py, disbot/cogs/counters/__init__.py)_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !counters | command | disbot/cogs/counters_cog.py:159 | | | |
| !counterpreset | command | disbot/cogs/counters_cog.py:173 | | | |
| /counters | command | disbot/cogs/counters_cog.py:227 | | | |
| _counter_sync_loop | scheduled loop | disbot/cogs/counters_cog.py:57 | | | |
| _before_counter_sync_loop (before_loop hook) | listener | disbot/cogs/counters_cog.py:84 | | | |
| cog_load (registers schema, starts loop) | listener | disbot/cogs/counters_cog.py:44 | | | |
| cog_unload (cancels loop) | listener | disbot/cogs/counters_cog.py:51 | | | |
| build_help_menu_view (help-menu direct-nav hook) | help | disbot/cogs/counters_cog.py:238 | | | |
| counters.updated (bus.emit event) | event | disbot/services/counter_service.py:130 | | | |
| enabled (master switch) | setting | disbot/cogs/counters/schemas.py:88 | | | |
| total_channel / humans_channel / bots_channel (channel bindings) | setting | disbot/cogs/counters/schemas.py:99 | | | |
| total_template / humans_template / bots_template (name templates) | setting | disbot/cogs/counters/schemas.py:128 | | | |
| counters.settings.configure (capability gate) | setting | disbot/cogs/counters/schemas.py:44 | | | |

**Unit kinds present:** command, scheduled loop, listener, help, event, setting

**Structural-pattern flags:** scheduled loop (`@tasks.loop`, `_counter_sync_loop`, 10-min cadence) driving Discord channel renames; no persistent discord.ui.View/panel (status is a plain embed reused via HubView from the help menu); no dedicated DB table — config is guild-settings KV only (SubsystemSchema-declared); no gateway/@bot.event, no wait_for wizard, no voice.
