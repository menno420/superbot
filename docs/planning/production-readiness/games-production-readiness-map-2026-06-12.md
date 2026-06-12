# Games production-readiness map — 2026-06-12

> **Status:** `audit` — verified production-readiness review; docs-only. Source code and merged
> PRs win over older documentation.  This review does **not** require restart-safe game
> state and does **not** propose Redis; ADR-002 makes loss of in-flight game state an
> accepted limitation.  The production requirement is that interrupted games do not
> lose users' staked money.
>
> **Verdict:** **Partial.** The Games hub, all named game cogs, their principal panels,
> counting persistence, mining workflow boundary, shared state infrastructure, and
> economy-service routing exist and are substantially tested.  The main blockers are
> wager lifecycle/atomicity gaps, incomplete adoption of shared game XP outside mining,
> and missing end-to-end/live verification plus a cross-game terminal-state contract.

## Current verified state

- The Games hub discovers visible child subsystems and opens actionable panels for RPS,
  blackjack, deathmatch, mining, and counting. There is intentionally no cross-game
  leaderboard button because no such user surface exists.
- Blackjack provides solo, PvP, and tournament play. Solo/PvP hands and paid tournament
  entries use `game_state_service`; startup recovery clears or refunds rather than
  promising seamless continuation.
- RPS provides solo, PvP, bot matches, quick play, and tournaments. PvP pending/play and
  paid tournament entries use `game_state_service`; recovery clears/refunds as needed.
- Deathmatch provides PvP and bot duels, guild-scoped PvP stats, mining-equipment combat
  stats, and gear-wear ticks. It has no coin wager and intentionally does not count bot
  duels on the PvP leaderboard.
- Mining is the most mature workflow boundary: all scoped mutations route through
  `services/mining_workflow.py`, with transaction-scoped inventory/equipment/depth,
  economy, durability, and game-XP writes. Pure item, market, recipe, exploration,
  reward, loadout, workshop, and world rules live under `utils/mining/`.
- Counting is a channel-message game with multiple parsing/mode paths, per-channel
  locks, a staff management panel, and guild-scoped JSON state persistence. It has no
  economy or game-XP effects.
- `game_state_service` is an opt-in JSONB checkpoint/refund aid, not a restart-safety
  promise. `game_xp_service` is a shared progression service in architecture, but its
  current award catalogue and production callers cover only mining/crafting.
- Live GitHub review on **2026-06-12** found one open PR: screenshot-only live-testing
  evidence [#704](https://github.com/menno420/superbot/pull/704). It contains working
  mining hub, mine result, inventory, gear, workshop, recipe-picker, and character-card
  screenshots, but no source changes or failure-path evidence. Recent merged
  source-changing PRs reviewed for this map: [#661](https://github.com/menno420/superbot/pull/661),
  [#663](https://github.com/menno420/superbot/pull/663),
  [#664](https://github.com/menno420/superbot/pull/664),
  [#665](https://github.com/menno420/superbot/pull/665),
  [#667](https://github.com/menno420/superbot/pull/667),
  [#671](https://github.com/menno420/superbot/pull/671),
  [#683](https://github.com/menno420/superbot/pull/683), and
  [#702](https://github.com/menno420/superbot/pull/702). These establish the mining
  workflow boundary, shared game XP, mining BaseView migration, and current gear model.

## Scope inventory

Status meanings: **Done** = implemented with a credible automated contract; **Partial** =
implemented but has a correctness, lifecycle, coverage, or adoption gap; **Not Done** =
required game-facing capability or contract is absent.

| Item | Path | Type | Status | Reason | Evidence |
|---|---|---|---|---|---|
| Games entry cog | `disbot/cogs/games_cog.py` | cog / commands | Done | Prefix and slash entry points build the shared Games hub. | `games_menu`, `games_slash`, `build_help_menu_view`; `test_games_cog.py` |
| Games hub | `disbot/views/games/hub.py` | view / discovery | Done | Discovers visible children, renders actionable buttons, handles missing/failing child cogs, and preserves back navigation. | `discover_game_children`, `build_games_hub_panel`, `GamesHubView`; `test_games_hub_view.py` |
| Shared game panel back button | `disbot/views/games/common.py` | shared view helper | Done | Shared callback defers safely and rebuilds parent panel; RPS, blackjack, and deathmatch subpanels use it. | `BackToPanelButton`; `test_games_common.py` |
| Blackjack panel | `disbot/views/games/blackjack_panel.py` | hub/subviews | Done | Solo/free/bet, challenge, tournament/status, rules, and back paths are actionable. | `BlackjackPanelView` and subviews; `test_game_panels.py`, `test_games_common.py` |
| Blackjack cog and state | `disbot/cogs/blackjack_cog.py`, `disbot/cogs/blackjack/` | cog / domain / persistence | Partial | Solo, PvP, tournament, recovery, and settings exist; paid-entry debit→checkpoint and some payouts are not one atomic workflow. | recovery methods, `_persistence.py`, `actions.py`; blackjack persistence tests |
| Blackjack play views | `disbot/views/blackjack/` | game views | Partial | Solo replay and terminal controls are tested; PvP/tournament settlement uses sequential economy operations and lacks a full terminal/lifecycle contract. | `solo_view.py`, `pvp_view.py`, `tournament_views.py`; `test_blackjack_solo_replay.py` |
| RPS panel | `disbot/views/games/rps_panel.py` | hub/subviews | Done | Solo, bet presets, challenge, tournament controls/status, rules, and back paths are actionable. | `RPSPanelView` and subviews; panel/common tests |
| RPS cog and state | `disbot/cogs/rps_tournament_cog.py`, `disbot/cogs/rps_tournament/` | cog / rules / persistence | Partial | Solo/PvP/bot/tournament paths exist; tournament paid-entry debit→checkpoint and payout lifecycle are not transactional end to end. | `_persistence.py`, `_stage.py`, `_quickplay.py`, `_bot_matches.py`; RPS persistence/stage tests |
| RPS play views | `disbot/views/rps/` | game views | Partial | Solo terminal/replay behavior is well pinned; PvP settlement is sequential credit then overdraft-enabled debit and timeout edits swallow failures. | `solo_play.py`, `pvp_challenge.py`, `pvp_play.py`, `registration.py`, `move_picker.py`; `test_rps_solo_replay.py` |
| Deathmatch panel | `disbot/views/games/deathmatch_panel.py` | hub / bot-duel view | Partial | Bot duel and challenge paths work and terminal buttons disable; timeout edit failures are silently swallowed and no direct terminal-view tests pin the bot-duel view. | `_BotDuelView`, `DeathmatchPanelView`; `test_deathmatch_bot_duel.py`, `test_game_panels.py` |
| Deathmatch cog/domain | `disbot/cogs/deathmatch_cog.py`, `disbot/cogs/deathmatch/` | cog / PvP combat | Partial | PvP/bot combat, guild-scoped stats, equipment stats, and wear exist; PvP in-flight state is memory-only and the lifecycle has limited direct view coverage. This is accepted for state, but still a live-verification gap. | `_Duel`, `_DuelView`, `_ChallengeView`, actions; deathmatch stats/scope/wear tests |
| Mining cog | `disbot/cogs/mining_cog.py` | cog / command adapters | Done | Game-facing commands route mutations through the mining workflow and retain direct DB access only for reads. | commands from `mine` through `quick_craft`, plus admin reset/grant; mining write-boundary invariant |
| Mining workflow | `disbot/services/mining_workflow.py` | mutation workflow | Done | Owns mine, harvest, explore, use/equip, depth, craft/repair, buy/sell, durability, admin mutations, economy legs, XP awards, transactions, and post-commit events. | workflow characterization and invariant tests; PRs #661/#663/#664/#665/#667 |
| Mining pure domain | `disbot/utils/mining/` | pure rules/helpers | Done | Typed items, prices, recipes, rewards, exploration, loadouts, workshop, names, and depth/biome rules are separated and tested. | mining utils/cog unit tests |
| Mining views | `disbot/views/mining/` | hub / action panels | Partial | Hub, mine loop, gear, market, workshop, recipe browser, character, and navigation exist; many read paths remain view-owned and PR #704 supplies only happy-path live screenshots, not lifecycle/failure verification. | mining view test family; PR #683 |
| Counting cog | `disbot/cogs/counting_cog.py` | cog / commands / lifecycle | Partial | Start/stop/config/leaderboard and pipeline integration exist with persisted guild state; writes are spawned asynchronously, so a process crash can lose the latest accepted count. That is accepted state loss, but observability/live recovery remain operational gaps. | `_save_guild`, counting commands/listener; counting persistence/handler/stage tests |
| Counting domain | `disbot/cogs/counting/` | parser / modes / handler / stage | Done | Parsing has bounded expensive operations; mode math and V/M/A message handling are separated and heavily tested. | `_constants.py`, `parsing.py`, `game_logic.py`, `handler.py`, `_stage.py`; counting test family |
| Counting manager view | `disbot/views/counting/hub_panel.py` | staff game view | Partial | Actionable manager exists, but it uses a cog-wide lock and spawned saves and has no dedicated interaction-lifecycle test family. | `_CountingHubView`; counting cog/persistence tests |
| Shared game state | `disbot/services/game_state_service.py`; migrations `015`, `018` | service / DB path | Done | Versioned JSONB save/load/clear/list/stale-GC infrastructure exists and is tested. Adoption remains intentionally opt-in under ADR-002. | `test_game_state_service.py`; ADR-002 |
| Shared game XP | `disbot/services/game_xp_service.py`; `disbot/utils/db/games/game_xp.py`; migration `065` | service / DB path | Partial | Atomic award policy, soft cap, shared levels, events, and leaderboards exist, but only mining/crafting award XP. | `test_game_xp_service.py`, `test_game_xp_db.py`; mining workflow callers |
| Economy side-effect seam | `disbot/services/economy_service.py` | service | Partial | Scoped game coin mutations use the required service seam, and mining uses transaction variants; several wager flows still compose multiple service calls non-atomically. | economy invariant/service tests; scoped call-site review |
| Game DB modules | `disbot/utils/db/games/` | DB adapters | Partial | Guild-scoped adapters exist for chain, counting, deathmatch, game XP, mining inventory/equipment/wear/state, and RPS. There is no blackjack-specific stats/history DB module, and direct adapters intentionally provide no workflow atomicity. | DB test family; migrations `002`, `005`, `015`–`018`, `060`–`066` |

## Game-facing function map

This is the callable/user-facing map, grouped by owning surface so every production path
has one readiness disposition without turning the inventory into a method-per-row dump.

| Game/surface | Game-facing functions and paths | Status | Short reason |
|---|---|---|---|
| Games hub | `!games`, `/games`, Help → Games, child-button dispatch, Back to Games/Help | Done | All visible children are actionable and fallback behavior is tested. |
| Blackjack solo | `!blackjack [bet]`, panel free/bet presets/custom; hit, stand, double, replay | Partial | Play works; economy is service-routed, but settlement/restart/live lifecycle is not verified end to end. |
| Blackjack PvP | `!blackjack @user [bet]`, panel opponent select; accept/decline, hit/stand, resolve | Partial | Checkpointing exists; two-party settlement is non-atomic and allows loser overdraft semantics. |
| Blackjack tournament | `!bjtournament`, `!bjstart`, `!bjstatus`, panel open/status/join; tournament hand/result | Partial | Paid entries recover/refund, but debit→checkpoint and multi-winner payout are not atomic/idempotent workflows. |
| RPS solo/quick | `!rps`, panel free/bet/custom; rock/paper/scissors, replay | Done | Terminal shell disabling, replay, insufficient-balance handling, and safe edits are directly tested. |
| RPS PvP | panel challenge/user select; accept/decline; move pick/resolve | Partial | Pending/play checkpointing exists; settlement is sequential credit then overdraft-enabled debit. |
| RPS bot match | `!rpsbot`; channel move handling | Partial | Play path exists, but state is module-memory only and has limited dedicated test/lifecycle coverage. Accepted for restart state, not for verification. |
| RPS tournament | `!rpsregister`, `!rpsstart`, `!rpsmatchup`, `!rpshelp`, `!rpssettings`; registration/reaction/match/round/payout | Partial | Tournament stage/persistence are tested; money lifecycle and live Discord reaction/channel behavior remain gaps. |
| Deathmatch PvP | `!deathmatch`/`!dm_challenge`; accept/decline; attack/defend; leaderboard update | Partial | Combat/stats/gear are tested; direct interaction terminal/timeout and live challenge coverage are incomplete. |
| Deathmatch bot duel | Games panel Fight Bot; attack/defend/auto-response/result | Partial | Correctly excludes PvP leaderboard and disables terminal buttons; direct timeout/error coverage is weak. |
| Mining | `!minemenu`, mine/harvest/explore/inventory/stats/build/use/equip/gear/character/descend/ascend/sell/buy/market/workshop/repair/quick-craft plus panels | Done | Mutations consistently route through one transactional workflow and have broad unit/invariant coverage. |
| Mining admin | `!reset_inventory`, `!give` | Done | Permission-gated adapters route through workflow audit/event paths. |
| Counting | `!countingmenu`, start/stop/config/leaderboard commands, counting-channel messages, manager buttons | Partial | Parser/modes/persistence are strong; latest-state durability and interaction/live coverage are limited by accepted asynchronous state handling. |

## Per-game readiness

| Game | Core play | State path | DB path | Economy | Game XP | Views/lifecycle | Overall |
|---|---|---|---|---|---|---|---|
| Games hub | Done | N/A | Registry/projection reads | N/A | N/A | Done | **Done** |
| Blackjack | Done | Partial: checkpoint + clear/refund, not seamless recovery | Shared `game_state`; no game stats/history table | Partial: service-routed, non-atomic wager lifecycle | Not Done | Partial | **Partial** |
| RPS / tournament | Done | Partial: checkpointed PvP/tournament; bot state memory-only | `game_state`, `rps_players` | Partial: service-routed, non-atomic PvP/entry/payout lifecycle | Not Done | Partial | **Partial** |
| Deathmatch | Done | Accepted memory-only | `deathmatch_stats`; mining gear/wear reads/writes | N/A | Not Done | Partial | **Partial** |
| Mining | Done | Persistent inventory/equipment/wear/depth; action state need not survive restart | Four mining adapters + `game_xp` + economy tables | Done | Done | Partial: automated breadth and happy-path screenshots, no failure-path live verification | **Partial** |
| Counting | Done | Partial/accepted: memory cache + async persisted snapshots | `counting_state` JSON | N/A | Not Done | Partial | **Partial** |

## Required before production-ready

1. **Define and enforce safe wager workflows.** Preserve the economy-service ownership
   rule while making each paid entry and settlement atomic or provably idempotent. The
   immediate cases are blackjack PvP/tournament and RPS PvP/tournament. A crash must not
   create free coins, double payouts, or an uncheckpointed paid entry.
2. **Pin terminal interaction behavior per game.** Add one explicit contract covering
   acknowledgement/defer, authorization, terminal disable/stop, timeout edit behavior,
   repeated clicks, expired interaction behavior, and settlement-before-render ordering.
3. **Run live verification.** Exercise the principal panel and command paths against a
   real Discord guild and Postgres, including timeout, restart/refund, insufficient
   funds, duplicate click/reaction, and missing-permission cases.
4. **Decide shared game-XP adoption.** Either add centrally governed awards for
   blackjack/RPS/deathmatch/counting or explicitly gate those games from the shared
   prestige track. The current “shared by all games” description exceeds source truth.
5. **Prove recovery/refund operations.** Add integration/live evidence that each paid
   tournament entry is checkpointed after debit, recovered/refunded once, and cleared
   without double refund after interruption or guild removal.

## Bugs, inconsistencies, and risks

| Finding | Severity | Status | Evidence / impact |
|---|---|---|---|
| RPS and blackjack PvP settle with a winner `credit` followed by loser `debit(..., allow_overdraft=True)` rather than one atomic transfer/workflow. | High | Open | A failure between calls can mint coins; a loser can spend funds before settlement and still fund only a floor-zero debit. |
| RPS and blackjack paid tournament registration debit before saving the recovery checkpoint. | High | Open | A crash in the gap can lose an entry fee with no row available to refund, contrary to ADR-002's money-safety requirement. |
| Tournament payouts/refunds are multi-call processes without a durable idempotency key or single owning transaction. | High | Open | Interruption during iteration can produce partial or repeated settlement. |
| Shared game XP describes a cross-game track but only mining/crafting have award constants/callers. | Medium | Open | Prestige and leaderboard participation are uneven and source contradicts “shared by all game cogs.” |
| Several timeout/error edits catch broad exceptions and silently `pass`. | Medium | Open | Expired/missing messages avoid crashes but failures are not observable and users may see stale enabled controls. |
| No repository-wide game terminal-state invariant exists. | Medium | Open | RPS solo is pinned, but equivalent guarantees can regress independently in other views. |
| Counting manager mutations use the cog-wide lock while message handling uses per-channel scope locks. | Low | Open | Correctness is protected, but unrelated manager operations serialize and the locking model is inconsistent. |
| Blackjack has no guild-scoped stats/history adapter comparable to RPS/deathmatch. | Low | Gated/product choice | Play is functional; only required if blackjack history/leaderboards are a production requirement. |

## Economy/game-XP side-effect correctness

### Correct

- All scoped game **coin mutations** found in source call `economy_service`; no game cog
  or view directly writes coin balances.
- Mining buy/sell/repair operations use `debit_in_txn` / `credit_in_txn` inside the
  workflow transaction, and events emit after commit.
- Mining action XP is awarded with the workflow connection and emitted after commit.
- Money-only mining actions award zero game XP, preventing buy/sell XP farming.
- Deathmatch and counting currently have no coin side effects; bot deathmatches do not
  mutate the PvP leaderboard.

### Partial or incorrect for production

- “Uses `economy_service`” is necessary but not sufficient: sequential service calls in
  PvP and tournaments do not create an atomic multi-leg game workflow.
- `economy_service.bet_and_settle` itself performs a balance read followed by a separate
  write and is not used by the reviewed game paths; its name should not be treated as
  proof of transaction-level settlement.
- Tournament entry checkpointing is not in the same transaction as entry-fee debit.
- Shared game XP is correct for mining/crafting, absent for every other reviewed game.

## Interaction lifecycle and terminal-state button issues

- **Good:** RPS solo defers before its economy write, swaps to a disabled result shell,
  provides replay/back actions, and has direct replay/timeout tests.
- **Good:** Blackjack solo disables action buttons on finish and provides a replay result
  view; replay behavior has direct tests.
- **Good:** Deathmatch PvP and bot-duel terminal paths disable controls and stop the view.
- **Partial:** RPS PvP/challenge and blackjack tournament timeout handlers catch and hide
  message-edit failures; no shared observable timeout policy exists.
- **Partial:** Deathmatch bot-duel timeout disables controls only if its stored message can
  be edited, and the exception is silently ignored.
- **Partial:** Mining views inherit the shared BaseView lifecycle, but real Discord
  interaction expiry/defer/edit sequences have not been live-verified in this review.
- **Not Done:** no cross-game test proves terminal controls cannot trigger a second
  settlement after a result, timeout, or delayed duplicate interaction.

## Gated or accepted limitations

- In-flight game state is **intentionally not guaranteed restart-safe**. Do not make
  seamless recovery, Redis, or an external state store a readiness requirement.
- Memory-only deathmatch duels, RPS bot matches, and the newest counting cache state are
  acceptable only while paid money remains safe and interruption behavior is clear.
- A cross-game leaderboard hub is gated until there is a real cross-game surface.
- Blackjack stats/history, deathmatch bot-duel stats, richer bot difficulty, more game
  settings, and inventory architecture redesign are product choices, not current
  readiness blockers.
- Mining view-owned **reads** through `utils/db/games/mining*.py` are allowed; the
  production boundary applies to writes.

## Simplification opportunities

- Introduce one game-wager workflow abstraction owned above `economy_service` for entry,
  escrow/validation, settlement, refund, and idempotency rather than duplicating
  sequential calls in views/cogs.
- Move settlement orchestration out of Discord views (`rps/pvp_play.py`,
  `blackjack/pvp_view.py`, tournament views) into testable game workflow functions.
- Reuse one terminal-result/timeout helper for disable → edit → stop → observable failure.
- Reconcile counting manager locks with the per-channel scope-lock model.
- Make the game-XP catalogue explicitly declare participating games so docs, rank
  providers, and award callers cannot drift.
- Consider a shared opponent picker and bet-preset component only after wager semantics
  are centralized; UI deduplication should not hide divergent money rules.

## Tests and live-verification gaps

### Strong automated coverage

- Hub discovery/actionability/back navigation and game panel composition.
- Blackjack solo replay and solo/PvP/tournament checkpoint/recovery behavior.
- RPS naming, rules/stage, tournament persistence, PvP pending persistence, and solo
  terminal replay behavior.
- Deathmatch bot strategy, combat stats, guild scope, and gear wear.
- Mining workflow characterization, write-boundary invariant, domain rules, DB adapters,
  and major panel/navigation families.
- Counting parser, modes, handler, pipeline stage, and persistence.
- Shared game-state, game-XP DB/service, and economy service/invariant behavior.

### Missing or insufficient

- Atomicity/failure-injection tests across every multi-leg wager and tournament payout.
- Duplicate/delayed interaction tests proving exactly-once game settlement.
- Direct terminal/timeout tests for blackjack PvP/tournament, RPS PvP/tournament,
  deathmatch PvP/bot, counting manager, and the full mining family.
- Real Postgres integration proof for interruption/refund/idempotency paths.
- Live Discord verification of reactions, temporary match channels, permissions,
  component expiry, timeouts, and back-navigation chains. PR #704 gives useful mining
  happy-path screenshots but does not close these failure-path gaps.
- Participation tests for non-mining games in shared game XP (currently impossible
  because the production award paths do not exist).

## Recommended next session

Run a **docs-to-tests wager and terminal-state characterization session**, without
changing product rules first:

1. Enumerate the exact paid-entry and settlement sequence for blackjack PvP/tournament
   and RPS PvP/tournament.
2. Add failure-injection characterization tests at every boundary between economy call,
   checkpoint write/clear, payout, and result edit.
3. Add a cross-game terminal-state test matrix for duplicate click, timeout, stale
   interaction, disabled controls, and exactly-once settlement.
4. Live-verify the same matrix in one test guild/Postgres instance.
5. Use the evidence to design a single economy-service-backed wager workflow in a later
   implementation session. Do not add Redis or require restart-safe in-flight play.
