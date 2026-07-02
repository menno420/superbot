# Lane C — Games & Community (Axis 1)

> **Status:** `reference` — this lane's workspace. The surface-unit inventories below are **pre-extracted** (facts only, tier columns blank). The Lane C agent **verifies + completes them against source**, fills BOTH tier columns, writes each subsystem's §2 manifest sketch, dispositions tier-3s, and adds reconsider/optimize recommendations — per [`../BRIEF.md`](../BRIEF.md). Treat the inventory as a starting scaffold, not ground truth.

**Subsystems:** games, blackjack, deathmatch, rps_tournament, counting, chain, leaderboard, community, community_spotlight, karma

**Method:** [`../BRIEF.md`](../BRIEF.md) · [`../PARTITION.md`](../PARTITION.md) · `tools/grammar_spike/` · `../ground-truth/command-surface.json`.

---

### games
_cogs: disbot/cogs/games_cog.py, disbot/cogs/blackjack_cog.py, disbot/cogs/rps_tournament_cog.py_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !games | command | disbot/cogs/games_cog.py:39 | | | |
| !world | command | disbot/cogs/games_cog.py:45 | | | |
| !worldcard (alias !mystats) | command | disbot/cogs/games_cog.py:59 | | | |
| /games (slash) | command | disbot/cogs/games_cog.py:84 | | | |
| !blackjack (alias !bj) | command | disbot/cogs/blackjack_cog.py:432 | | | |
| !bjtournament (alias !bjtourn) | command | disbot/cogs/blackjack_cog.py:518 | | | |
| !bjstart | command | disbot/cogs/blackjack_cog.py:579 | | | |
| !bjstatus | command | disbot/cogs/blackjack_cog.py:590 | | | |
| !rpsregister (alias !rpsreg) | command | disbot/cogs/rps_tournament_cog.py:199 | | | |
| !rpsstart (alias !rpsbegin) | command | disbot/cogs/rps_tournament_cog.py:369 | | | |
| !rpsbot | command | disbot/cogs/rps_tournament_cog.py:411 | | | |
| !rpsmatchup | command | disbot/cogs/rps_tournament_cog.py:424 | | | |
| !rpshelp | command | disbot/cogs/rps_tournament_cog.py:723 | | | |
| !rpssettings | command | disbot/cogs/rps_tournament_cog.py:741 | | | |
| !rps | command | disbot/cogs/rps_tournament_cog.py:772 | | | |
| build_help_menu_view hook | help | disbot/cogs/games_cog.py:73 | | | |
| GamesHubView | panel/view | disbot/views/games/hub.py:304 | | | |
| ExploreWorldHubView | panel/view | disbot/views/explore/world_hub.py:243 | | | |
| _GameHubButton | panel/view | disbot/views/games/hub.py:269 | | | |
| games/blackjack_panel.py hub-child panel | panel/view | disbot/views/games/blackjack_panel.py:1 | | | |
| games/rps_panel.py hub-child panel | panel/view | disbot/views/games/rps_panel.py:1 | | | |
| games/deathmatch_panel.py hub-child panel | panel/view | disbot/views/games/deathmatch_panel.py:1 | | | |
| BlackjackView (solo) | panel/view | disbot/views/blackjack/solo_view.py:38 | | | |
| _BlackjackSoloResultView | panel/view | disbot/views/blackjack/solo_view.py:245 | | | |
| _ChallengeView (blackjack pvp) | panel/view | disbot/views/blackjack/pvp_view.py:31 | | | |
| _TournRegistrationView (blackjack) | panel/view | disbot/views/blackjack/tournament_views.py:42 | | | |
| _TournBlackjackView | panel/view | disbot/views/blackjack/tournament_views.py:67 | | | |
| _RpsView (solo) | panel/view | disbot/views/rps/solo_play.py:37 | | | |
| _RpsSoloResultView | panel/view | disbot/views/rps/solo_play.py:141 | | | |
| _RpsMovePickerView | panel/view | disbot/views/rps/move_picker.py:12 | | | |
| _RpsPvpChallengeView | panel/view | disbot/views/rps/pvp_challenge.py:28 | | | |
| _RpsPvpPlayView | panel/view | disbot/views/rps/pvp_play.py:72 | | | |
| _RpsPvpResultView | panel/view | disbot/views/rps/pvp_play.py:30 | | | |
| _RpsRegistrationView | panel/view | disbot/views/rps/registration.py:15 | | | |
| ACTIVE_TOURNAMENT | setting | disbot/utils/settings_keys/games.py:12 | | | |
| RPS_DEFAULT_ENTRY_FEE | setting | disbot/utils/settings_keys/games.py:16 | | | |
| BLACKJACK_DEFAULT_ENTRY_FEE | setting | disbot/utils/settings_keys/games.py:20 | | | |
| DEATHMATCH_TURN_TIMEOUT | setting | disbot/utils/settings_keys/games.py:25 | | | |
| BlackjackCog.on_guild_remove | listener | disbot/cogs/blackjack_cog.py:298 | | | |
| BlackjackCog.on_raw_reaction_add (bj tournament reg) | listener | disbot/cogs/blackjack_cog.py:410 | | | |
| RpsTournamentCog.on_guild_remove | listener | disbot/cogs/rps_tournament_cog.py:183 | | | |
| RpsTournamentCog.on_reaction_add (rps registration) | listener | disbot/cogs/rps_tournament_cog.py:534 | | | |
| game_wager_workflow.recover_escrow (blackjack pvp escrow refund on guild remove) | event | disbot/cogs/blackjack_cog.py:365 | | | |
| game_wager_workflow.recover_escrow (rps pvp escrow refund on guild remove) | event | disbot/cogs/rps_tournament_cog.py:190 | | | |
| game_state rows (generic per-subsystem state store, used by blackjack solo/pvp/tournament) | store | disbot/services/game_state_service.py:48 | | | |
| rps_players table | store | disbot/utils/db/migrations.py:291 | | | |
| ⚠ unverified: rps_matches table (noted dropped in migration 019 per comment) | store | disbot/utils/db/games/rps.py:17 | | | |

**Unit kinds present:** command, panel, setting, listener, event, store, help
**Structural-pattern flags:** stateful game loop (blackjack/RPS solo, pvp, tournament state machines) · gateway listener (`on_guild_remove`, `on_raw_reaction_add`, `on_reaction_add`) · reaction-based registration wizard (RPS/blackjack tournament sign-up via reactions, not `wait_for`) · ADR-002 declares this game state intentionally not-restart-safe (best-effort recovery on cog_load, e.g. `_cleanup_orphaned_tournaments`); no scheduled `tasks.loop` or voice usage found in these three cog files.

---

### blackjack
_cogs: disbot/cogs/blackjack_cog.py (+ disbot/cogs/blackjack/{schemas,_state,_persistence,actions}.py, disbot/views/blackjack/*, disbot/views/games/blackjack_panel.py)_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !blackjack / !bj | command | disbot/cogs/blackjack_cog.py:431 | | | |
| !bjtournament / !bjtourn | command | disbot/cogs/blackjack_cog.py:516 | | | |
| !bjstart | command | disbot/cogs/blackjack_cog.py:577 | | | |
| !bjstatus | command | disbot/cogs/blackjack_cog.py:589 | | | |
| build_help_menu_view (hub direct-nav hook) | help | disbot/cogs/blackjack_cog.py:101 | | | |
| BlackjackPanelView | panel/view | disbot/views/games/blackjack_panel.py:586 | | | |
| _BlackjackBetPresetView | panel/view | disbot/views/games/blackjack_panel.py:185 | | | |
| _BlackjackChallengeSelectView | panel/view | disbot/views/games/blackjack_panel.py:307 | | | |
| _BlackjackChallengeBetView | panel/view | disbot/views/games/blackjack_panel.py:371 | | | |
| _BlackjackTournamentSubView | panel/view | disbot/views/games/blackjack_panel.py:496 | | | |
| BlackjackView (solo game board) | panel/view | disbot/views/blackjack/solo_view.py:38 | | | |
| _BlackjackSoloResultView | panel/view | disbot/views/blackjack/solo_view.py:245 | | | |
| _ChallengeView (PvP challenge accept) | panel/view | disbot/views/blackjack/pvp_view.py:31 | | | |
| _TournRegistrationView | panel/view | disbot/views/blackjack/tournament_views.py:42 | | | |
| _TournBlackjackView | panel/view | disbot/views/blackjack/tournament_views.py:67 | | | |
| default_entry_fee | setting | disbot/cogs/blackjack/schemas.py:29 | | | |
| on_guild_remove (departed-guild cleanup + refunds) | listener | disbot/cogs/blackjack_cog.py:298 | | | |
| on_raw_reaction_add (✅ tournament registration) | listener | disbot/cogs/blackjack_cog.py:410 | | | |
| cog_load recovery tasks (solo/pvp/escrow/tournament) | listener | disbot/cogs/blackjack_cog.py:123 | | | |
| game_state store (shared table, subsystem keys BLACKJACK_SOLO/PVP/TOURNAMENT) | store | disbot/migrations/015_game_state.sql:1 ⚠ unverified line | | | |
| blackjack.game.play / blackjack.tournament.manage capabilities | setting | disbot/utils/subsystem_registry.py:747 | | | |

**Unit kinds present:** command, panel, setting, listener, store, help (no dedicated `event`/emit_audit_action call found directly in blackjack cog — economy_service.credit/refund and game_wager_workflow handle audit emission downstream; ⚠ unverified whether blackjack itself emits audit events directly).

**Structural-pattern flags:** stateful game loop (solo/PvP/tournament in-memory dict state `_active`/`_pvp`/`_tournaments`); gateway listener (`on_guild_remove`, `on_raw_reaction_add`); scheduled/timer task (tournament auto-start `asyncio.sleep` + `tasks.spawn`); no `wait_for` wizard or voice usage observed.


---

### deathmatch
_cogs: disbot/cogs/deathmatch_cog.py, disbot/views/games/deathmatch_panel.py, disbot/cogs/deathmatch/schemas.py_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !dm_challenge (aliases: deathmatch, challenge, dm) | command | disbot/cogs/deathmatch_cog.py:445 | | | |
| !dm_help (alias: deathmatch_help) | command | disbot/cogs/deathmatch_cog.py:498 | | | |
| challenge_error | listener (command error handler) | disbot/cogs/deathmatch_cog.py:486 | | | |
| Deathmatch.cog_load (registers settings schema) | listener (cog lifecycle) | disbot/cogs/deathmatch_cog.py:411 | | | |
| _DuelView | panel/view | disbot/cogs/deathmatch_cog.py:94 | | | |
| _DuelView.btn_attack | panel/view control | disbot/cogs/deathmatch_cog.py:193 | | | |
| _DuelView.btn_defend | panel/view control | disbot/cogs/deathmatch_cog.py:204 | | | |
| _DuelView.on_timeout | panel/view lifecycle | disbot/cogs/deathmatch_cog.py:151 | | | |
| _ChallengeView | panel/view | disbot/cogs/deathmatch_cog.py:274 | | | |
| _ChallengeView.btn_accept | panel/view control | disbot/cogs/deathmatch_cog.py:329 | | | |
| _ChallengeView.btn_decline | panel/view control | disbot/cogs/deathmatch_cog.py:385 | | | |
| DeathmatchPanelView | panel/view (hub) | disbot/views/games/deathmatch_panel.py:603 | | | |
| DeathmatchPanelView.btn_fight_bot | panel/view control | disbot/views/games/deathmatch_panel.py:616 | | | |
| DeathmatchPanelView.btn_challenge | panel/view control | disbot/views/games/deathmatch_panel.py:644 | | | |
| DeathmatchPanelView.btn_rules | panel/view control | disbot/views/games/deathmatch_panel.py:660 | | | |
| _BotDuelView | panel/view | disbot/views/games/deathmatch_panel.py:192 | | | |
| _BotDuelResultView | panel/view (result/rematch) | disbot/views/games/deathmatch_panel.py:347 | | | |
| _PvpDuelResultView | panel/view (result/rematch) | disbot/views/games/deathmatch_panel.py:391 | | | |
| _DeathmatchChallengeSelectView | panel/view | disbot/views/games/deathmatch_panel.py:493 | | | |
| _DeathmatchOpponentSelect | panel/view (UserSelect) | disbot/views/games/deathmatch_panel.py:500 | | | |
| turn_timeout | setting | disbot/cogs/deathmatch/schemas.py:32 | | | |
| deathmatch.game.challenge | setting/capability | disbot/utils/subsystem_registry.py:858 | | | |
| deathmatch.stat.view | setting/capability | disbot/utils/subsystem_registry.py:859 | | | |
| deathmatch_stats | store (table) | disbot/utils/db/migrations.py:313 | | | |
| update_deathmatch | store (mutation fn) | disbot/utils/db/games/deathmatch.py (⚠ unverified line) | | | |
| get_deathmatch_leaderboard | store (query fn) | disbot/utils/db/games/deathmatch.py (⚠ unverified line) | | | |
| get_deathmatch_stats | store (query fn) | disbot/utils/db/games/deathmatch.py (⚠ unverified line) | | | |
| !leaderboard deathmatch | help/reference (cross-cog leaderboard arg) | disbot/cogs/leaderboard_cog.py:217 | | | |
| deathmatch registry entry | help/registry entry (entry_points: deathmatch, dm) | disbot/utils/subsystem_registry.py:838 | | | |

**Unit kinds present:** command, listener, panel/view, setting, store, help/reference

**Structural-pattern flags:** stateful game loop (in-memory `active_duels` turn-based duel state machine in `Deathmatch` cog); gateway-adjacent view timeouts (`on_timeout` in `_DuelView`/`_ChallengeView`, discord.ui.View timeout, not `@bot.event`); no `wait_for` wizard, no scheduled loop, no voice usage observed.


---

### rps_tournament
_cogs: cogs/rps_tournament_cog.py (+ cogs/rps_tournament/* submodules: schemas.py, rules.py, _persistence.py, _bot_matches.py, _stage.py, _quickplay.py, _helpers.py)_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !rpsregister (alias !rpsreg) | command | cogs/rps_tournament_cog.py:199 | | | |
| !rpsstart (alias !rpsbegin) | command | cogs/rps_tournament_cog.py:369 | | | |
| !rpsbot | command | cogs/rps_tournament_cog.py:411 | | | |
| !rpsmatchup | command | cogs/rps_tournament_cog.py:424 | | | |
| !rpshelp | command | cogs/rps_tournament_cog.py:724 | | | |
| !rpssettings | command | cogs/rps_tournament_cog.py:741 | | | |
| !rps | command | cogs/rps_tournament_cog.py:772 | | | |
| on_guild_remove | listener | cogs/rps_tournament_cog.py:183 | | | |
| on_reaction_add | listener | cogs/rps_tournament_cog.py:534 | | | |
| RpsTournamentStage (message_pipeline stage) | listener | cogs/rps_tournament/_stage.py (registered cogs/rps_tournament_cog.py:145) | | | |
| _RpsRegistrationView | panel/view | disbot/views/rps/registration.py:15 | | | |
| _RpsMovePickerView | panel/view | disbot/views/rps/move_picker.py:12 | | | |
| _RpsPvpChallengeView | panel/view | disbot/views/rps/pvp_challenge.py:28 | | | |
| _RpsPvpResultView | panel/view | disbot/views/rps/pvp_play.py:30 | | | |
| _RpsPvpPlayView | panel/view | disbot/views/rps/pvp_play.py:72 | | | |
| _RpsView | panel/view | disbot/views/rps/solo_play.py:37 | | | |
| _RpsSoloResultView | panel/view | disbot/views/rps/solo_play.py:141 | | | |
| _RpsBetPresetView | panel/view | disbot/views/games/rps_panel.py:212 | | | |
| _RpsBetPresetButton | panel/view | disbot/views/games/rps_panel.py:229 | | | |
| _RpsBetCustomButton | panel/view | disbot/views/games/rps_panel.py:248 | | | |
| _RpsCustomBetModal | panel/view | disbot/views/games/rps_panel.py:261 | | | |
| _RpsChallengeSelectView | panel/view | disbot/views/games/rps_panel.py:293 | | | |
| _RpsOpponentSelect | panel/view | disbot/views/games/rps_panel.py:308 | | | |
| _RpsTournamentSubView | panel/view | disbot/views/games/rps_panel.py:353 | | | |
| _RpsTournamentStartButton | panel/view | disbot/views/games/rps_panel.py:379 | | | |
| _RpsTournamentJoinButton | panel/view | disbot/views/games/rps_panel.py:413 | | | |
| _RpsTournamentMatchupButton | panel/view | disbot/views/games/rps_panel.py:447 | | | |
| _RpsMatchupSelect | panel/view | disbot/views/games/rps_panel.py:483 | | | |
| RPSPanelView (hub panel, build_help_menu_view hook) | panel/view | disbot/views/games/rps_panel.py:567 (built cogs/rps_tournament_cog.py:127-131) | | | |
| RPS_DEFAULT_ENTRY_FEE (default entry fee setting) | setting | cogs/rps_tournament/schemas.py:25,74 (utils/settings_keys.py) | | | |
| RPS_CONFIG_SCHEMA / register_schemas() | setting | cogs/rps_tournament/schemas.py:51,58 | | | |
| capability rps_tournament.game.join | setting | disbot/utils/subsystem_registry.py:882 | | | |
| capability rps_tournament.tournament.manage | setting | disbot/utils/subsystem_registry.py:883 | | | |
| rps_players table | store | disbot/utils/db/migrations.py:291 | | | |
| rps (help entry alias) | help | disbot/cogs/help/route.py:72 | | | |
| rock paper scissors (help entry alias) | help | disbot/cogs/help/route.py:73 | | | |
| ⚠ unverified: audit-event emission for tournament entry fee | event | routed via services.game_wager_workflow.enter_tournament (cogs/rps_tournament_cog.py:~305), not confirmed to emit_audit_action directly in this subsystem's own files | | | |

**Unit kinds present:** command, listener (Cog.listener + message_pipeline stage), panel/view, setting (settings_key + subsystem schema + capabilities), store, help. No standalone `bus.emit`/`emit_audit_action` calls found directly inside rps_tournament's own files (grep was empty) — fee/escrow mutation delegates to `services.game_wager_workflow` / `services.tournament_state_service`, marked ⚠ unverified above.

**Structural-pattern flags:** stateful game loop (per-instance tournament state: `self.players`/`self.scores`/`self.matches`/`self.current_round`); gateway listener (`@commands.Cog.listener()` on_guild_remove, on_reaction_add); scheduled/background loop (`registration_countdown`, `tasks.spawn` reminder + recovery tasks in `cog_load`); wizard-like multi-step registration → bracket flow. No `@bot.event` top-level handlers, no voice usage.

---

### counting
_cogs: disbot/cogs/counting_cog.py, disbot/cogs/counting/_stage.py, disbot/cogs/counting/handler.py, disbot/cogs/counting/parsing.py, disbot/cogs/counting/game_logic.py, disbot/cogs/counting/_channel_manager.py, disbot/cogs/counting/leaderboard.py_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !countingmenu (cm) | command | disbot/cogs/counting_cog.py:179 | | | |
| !start_match (sm) | command | disbot/cogs/counting_cog.py:196 | | | |
| !end_match (em) | command | disbot/cogs/counting_cog.py:383 | | | |
| !reset_count (rc) | command | disbot/cogs/counting_cog.py:432 | | | |
| !toggle_turns (tt) | command | disbot/cogs/counting_cog.py:487 | | | |
| !count_info (ci) | command | disbot/cogs/counting_cog.py:517 | | | |
| !counttop (ct, counting_top) | command | disbot/cogs/counting_cog.py:572 | | | |
| !count_rules (cr) | command | disbot/cogs/counting_cog.py:604 | | | |
| !set_skip_numbers (ssn) | command | disbot/cogs/counting_cog.py:635 | | | |
| !toggle_reset_on_wrong_count (trwc) | command | disbot/cogs/counting_cog.py:686 | | | |
| _CountingHubView | panel/view | disbot/views/counting/hub_panel.py:168 | | | staff config hub, extends HubView, opened by !countingmenu |
| counting message-count listener (⚠ unverified wiring) | listener | disbot/cogs/counting/_stage.py:54 | | | wraps `_process_counting_message`; triggering on_message hook not located in counting_cog.py itself — likely wired via message_router/stage dispatch elsewhere |
| counting guild state store | store | disbot/utils/db/games/counting.py:8 | | | `get_counting_state`/`set_counting_state` — per-guild counting state (channels, counts, modes) |
| subsystem_registry entry | setting | disbot/utils/subsystem_registry.py:886 | | | SUBSYSTEMS["counting"] capabilities incl. `counting.game.play`, `counting.game.configure`; entry_points count_info/counttop/countingmenu |

**Unit kinds present:** command, panel, setting, listener, store
**Structural-pattern flags:** stateful game loop (turn/mode/skip-number state machine driven by message parsing in handler.py/game_logic.py); no @bot.event/bus.on found directly in counting_cog.py — message intake wiring (`_process_counting_message`) is invoked from `_stage.py`, exact listener registration point unverified (⚠); no scheduled loop or voice usage found.


---

### chain
_cogs: disbot/cogs/chain_cog.py_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !chain | command (group) | disbot/cogs/chain_cog.py:69 | | | |
| !chain create | command (subcommand) | disbot/cogs/chain_cog.py:79 | | | |
| !chain delete | command (subcommand) | disbot/cogs/chain_cog.py:134 | | | |
| !chain setlimit | command (subcommand) | disbot/cogs/chain_cog.py:167 | | | |
| !chain removelimit | command (subcommand) | disbot/cogs/chain_cog.py:216 | | | |
| !chain list | command (subcommand) | disbot/cogs/chain_cog.py:270 | | | |
| !chainmenu | command (prefix) | disbot/cogs/chain_cog.py:253 | | | |
| chain.game.play | setting/capability | disbot/utils/subsystem_registry.py:930 (~capabilities list) | | | |
| chain.game.configure | setting/capability | disbot/utils/subsystem_registry.py:930 (~capabilities list) | | | |
| _ChainMenuView | panel/view | disbot/cogs/chain_cog.py:580 | | | |
| _CreateChainModal | panel/view (modal) | disbot/cogs/chain_cog.py:408 | | | |
| _DeleteChainModal | panel/view (modal) | disbot/cogs/chain_cog.py:452 | | | |
| _SetLimitModal | panel/view (modal) | disbot/cogs/chain_cog.py:488 | | | |
| _ClearLimitModal | panel/view (modal) | disbot/cogs/chain_cog.py:542 | | | |
| on_ready listener | listener | disbot/cogs/chain_cog.py:381-382 | | | |
| _process_chain_message | listener (pipeline hook, non-Discord-decorator) | disbot/cogs/chain_cog.py:310 | | | |
| emit_audit_action (via chain_service._emit) | event | disbot/services/chain_service.py:89-100 | | | |
| chain_channels table | store | disbot/utils/db/games/chain.py:1 | | | |

**Unit kinds present:** command, setting/capability, panel/view (incl. modals), listener, event, store
**Structural-pattern flags:** message-pipeline listener (`_process_chain_message`, invoked from ChainStage in message pipeline, not a bare @bot.event) plus a HubView-based panel with modal-driven wizard-like flows (Create/Delete/SetLimit/ClearLimit modals); no scheduled loop, no voice, no wait_for-based multi-step wizard beyond modals, no persistent stateful game loop beyond simple counter (`chain_count` increment).


---

### leaderboard
_cogs: disbot/cogs/leaderboard_cog.py_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !leaderboard (aliases: lb, rankings, minelb, miningleaderboard, fishlb, dm_leaderboard, dm_lb, rpslb, farmlb, countlb, counting_leaderboard) | command | disbot/cogs/leaderboard_cog.py:216 | | | |
| LeaderboardView | panel/view | disbot/cogs/leaderboard_cog.py:137 | | | |
| _CategorySelect (discord.ui.Select, category dropdown callback) | panel/view | disbot/cogs/leaderboard_cog.py:152 | | | |
| build_help_menu_view (help-menu direct-navigation hook returning hub) | panel/view | disbot/cogs/leaderboard_cog.py:243 | | | |
| leaderboard.xp.view (capability) | setting | disbot/utils/subsystem_registry.py:956 | | | |
| leaderboard.economy.view (capability) | setting | disbot/utils/subsystem_registry.py:957 | | | |
| SUBSYSTEMS["leaderboard"] entry (entry_points leaderboard/lb, parent_hub economy) | setting | disbot/utils/subsystem_registry.py:937 | | | |
| RankProvider registry (_PROVIDERS, ALIASES map — xp/coins/mining/creatures/fishing/farm/gamexp/crafting/deathmatch/rps/counting/karma providers) | store (read-only aggregation, ⚠ unverified as "owned" store — no dedicated leaderboard table; providers read other subsystems' tables) | disbot/services/rank_providers.py:627 | | | |
| render_leaderboard_image (image-card rendering helper used by cog) | ⚠ unverified — helper, not a discrete grammar unit | disbot/utils/ux_patterns/image_builders.py | | | |

**Unit kinds present:** command, panel/view, setting, store (aggregation-only, no owned table)
**Structural-pattern flags:** none obvious — no @bot.event/bus.on listener, no wait_for wizard, no scheduled loop, no voice; cog is a stateless embed-rendering shell over the `services.rank_providers` registry (per module docstring), with a single command + a category-select dropdown view. No dedicated `help_catalogue.py` entry or DB table found for this subsystem — it aggregates read access to other subsystems' data (xp, economy/coins, mining, deathmatch, rps, farm, counting, karma, etc.).


---

### community
_cogs: disbot/cogs/community_cog.py, disbot/cogs/community_spotlight_cog.py_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !community | command | disbot/cogs/community_cog.py:41 | | | |
| /community | command | disbot/cogs/community_cog.py:55 | | | |
| !spotlight (alias !activity) | command | disbot/cogs/community_spotlight_cog.py:300 | | | |
| CommunityHubView | panel/view | disbot/views/community/hub.py:259 | | | |
| SpotlightView | panel/view | disbot/cogs/community_spotlight_cog.py:129 | | | |
| GamesView | panel/view | disbot/cogs/community_spotlight_cog.py:191 | | | |
| _GameSelect (select menu) | panel/view | disbot/cogs/community_spotlight_cog.py:213 | | | |
| _CommunityChildButton | panel/view | disbot/views/community/hub.py:230 | | | |
| build_community_hub_panel | panel/view | disbot/views/community/hub.py:144 | | | |
| CommunityCog.build_help_menu_view | help | disbot/cogs/community_cog.py:47 | | | |
| CommunitySpotlightCog.build_help_menu_view | help | disbot/cogs/community_spotlight_cog.py:278 | | | |
| xp_service.EVT_LEVEL_UP subscription | listener | disbot/cogs/community_spotlight_cog.py:252 (bus.on, cog_load) | | | |
| _on_level_up handler | listener | disbot/cogs/community_spotlight_cog.py:260 | | | |
| _cache_trim_loop | scheduled loop | disbot/cogs/community_spotlight_cog.py:271 (@tasks.loop(hours=1)) | | | |

**Unit kinds present:** command, panel/view, help, listener, scheduled loop
**Structural-pattern flags:** listener (bus.on subscription to xp_service.EVT_LEVEL_UP in cog_load, plus bus.off in cog_unload) and a scheduled loop (@tasks.loop(hours=1) cache-trim). No stateful game loop, no wait_for wizard, no voice. No dedicated DB table/store or settings-registry key owned by this subsystem — community_cog is a router-only hub with no business logic; community_spotlight_cog reads XP/economy data via existing providers (xp_service, rank_providers, db.get_guild_xp_totals) rather than owning its own store.

---

### community_spotlight
_cogs: disbot/cogs/community_spotlight_cog.py_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !spotlight (alias !activity) | command | disbot/cogs/community_spotlight_cog.py:304 | | | |
| SpotlightView | panel/view | disbot/cogs/community_spotlight_cog.py:129 | | | |
| SpotlightView.xp_leaders button | panel/view | disbot/cogs/community_spotlight_cog.py:141 | | | |
| SpotlightView.richest button | panel/view | disbot/cogs/community_spotlight_cog.py:151 | | | |
| SpotlightView.games button | panel/view | disbot/cogs/community_spotlight_cog.py:162 | | | |
| SpotlightView.refresh button | panel/view | disbot/cogs/community_spotlight_cog.py:179 | | | |
| GamesView | panel/view | disbot/cogs/community_spotlight_cog.py:191 | | | |
| GamesView.back button | panel/view | disbot/cogs/community_spotlight_cog.py:199 | | | |
| _GameSelect | panel/view | disbot/cogs/community_spotlight_cog.py:213 | | | |
| build_help_menu_view | help/hub entry | disbot/cogs/community_spotlight_cog.py:278 | | | |
| community_spotlight.dashboard.view | capability/setting | disbot/utils/subsystem_registry.py:641 | | | |
| xp.level_up listener (bus.on) | listener | disbot/cogs/community_spotlight_cog.py:252 | | | |
| _on_level_up handler | listener | disbot/cogs/community_spotlight_cog.py:260 | | | |
| _cache_trim_loop (@tasks.loop hours=1) | scheduled loop | disbot/cogs/community_spotlight_cog.py:271 | | | |
| cog_load (bus.on + loop.start) | listener/loop setup | disbot/cogs/community_spotlight_cog.py:251 | | | |
| cog_unload (bus.off + loop.cancel) | listener/loop teardown | disbot/cogs/community_spotlight_cog.py:256 | | | |

**Unit kinds present:** command, panel/view (buttons + select), help/hub entry, setting/capability, listener (EventBus), scheduled loop.
**Structural-pattern flags:** EventBus listener (`bus.on(xp_service.EVT_LEVEL_UP, ...)`), scheduled loop (`@tasks.loop(hours=1)` cache trim); no `@bot.event`, no `wait_for` wizard, no voice, no direct DB writes/owned tables (reads only via `db.get_guild_xp_totals` and rank providers) — no store unit found.

---

### karma
_cogs: disbot/cogs/karma_cog.py, disbot/cogs/karma/schemas.py_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !thanks (aliases !rep, !thank) | command | disbot/cogs/karma_cog.py:209 | | | |
| !karma [member] | command | disbot/cogs/karma_cog.py:224 | | | |
| !karma add @user [reason] | command | disbot/cogs/karma_cog.py:235 | | | |
| /karma [member] | command (slash) | disbot/cogs/karma_cog.py:248 | | | |
| build_help_menu_view (Community-hub karma card hook) | panel/hub-hook | disbot/cogs/karma_cog.py:74 | | | |
| HubView (karma card view) | panel/view | disbot/cogs/karma_cog.py:91 (constructed; class in views/base.py) | | | |
| on_raw_reaction_add (react-to-thank) | listener | disbot/cogs/karma_cog.py:95-96 | | | |
| karma.enabled | setting | disbot/cogs/karma/schemas.py:76 | | | |
| karma.cooldown_seconds | setting | disbot/cogs/karma/schemas.py:87 | | | |
| karma.daily_cap | setting | disbot/cogs/karma/schemas.py:101 | | | |
| karma.reaction_emoji | setting | disbot/cogs/karma/schemas.py:112 | | | |
| karma.granted (EVT_KARMA_GRANTED) | event | disbot/services/karma_service.py:38,178 | | | |
| karma / karma_audit_log tables | store | disbot/migrations/093_karma.sql:15,32; disbot/utils/db/karma.py:30-207 | | | |
| help entry | help | ⚠ unverified — no `karma` entry found in disbot/services/help_catalogue.py; discovered via SUBSYSTEMS entry_points/capabilities in disbot/utils/subsystem_registry.py:416-437 | | | |

**Unit kinds present:** command, panel/hub-hook, view, setting, listener, event, store, (help entry unverified/absent)
**Structural-pattern flags:** gateway listener (`@commands.Cog.listener()` on `on_raw_reaction_add`, react-to-thank) — no stateful game loop, no wait_for wizard, no scheduled loop, no voice.
