# Games Actionability Sweep — Operator Handoff

> **Status:** `historical` — **complete** as of PR 9. This doc captures what shipped

across PRs 1–8 in the Help/Games actionability sweep, the manual
smoke matrix operators should run after a fresh deploy, and the
explicitly-deferred work the next session should consider.

## What shipped

The sweep turned the Help → Games path from a discovery-only
directory into a true playable launcher, plus added the first
per-game settings-and-readiness surface. Eight PRs landed in
sequence; this section names each and what it touched.

### PR 1 — Help/Games actionability contract tests

Added `tests/unit/help/test_help_actionability_contract.py`, which
classifies every terminal Help/Games panel button as one of:

* `action_*` (modal / new view / external message)
* `navigation_button` (Back / Overview / Cancel)
* `read_only_diagnostic_button` (Rules / Status / Leaderboard)
* `allowed_command_reference` (allowlisted prefix-only surface)
* `instruction_only` (the regression case — FAILS the contract)
* `empty_view` (also FAILS)

Each visible Games subsystem must reach at least one `action_*`
button. The three regressions (`rps_tournament`, `blackjack`,
`deathmatch`) shipped as `xfail(strict=True)` markers that PRs 4–6
each removed by turning xfail → xpass → strict failure → mandatory
marker removal.

### PR 2 — Games Hub v2 + Community back-button fix

* Replaced the `_GamesHubSelect` dropdown with direct `_GameHubButton`
  children — one per visible game, Competitive on row 0 (primary
  style), Activities on row 1 (success style).
* Fixed the long-standing Community navigation gap:
  `_CommunityChildButton.callback` now calls
  `attach_back_to_community_button(sub_view, parent_view._author)`
  after a successful child build, mirroring the Games hub pattern.
* Hard rule: every rendered hub button must open a real existing
  surface. No placeholder / "coming soon" / disabled buttons.

### PR 3 — RPS display rename

* `display_name` = **"Rock Paper Scissors"** (was "RPS Tournament").
* Help aliases `rps`, `rock paper scissors`, `rps_tournament` all
  resolve to the same canonical subsystem panel.
* Class rename `RPSTournamentCog` → `RockPaperScissorsCog`, with
  `RPSTournamentCog = RockPaperScissorsCog` back-compat alias.
* Canonical `SUBSYSTEMS` key stays `rps_tournament` for back-compat
  with saved state, providers, tournament `kind`, rank-provider
  aliases. The full canonical-key migration is deferred (see
  Deferred section below).

### PR 4 — RPS playable panel

`RPSPanelView` became actionable: Quick Play, Bet Match (10/25/50/
100/Custom), Challenge Player (UserSelect → PvP), Tournament
(admin: Open Registration / non-admin: Join when active), Rules.
All buttons reuse the existing `_RpsView`, `_RpsPvpChallengeView`,
`_RpsRegistrationView`, and the cog's `rps_register` /
`try_register_player` — no duplicate engine logic.

### PR 5 — Blackjack playable panel

`BlackjackPanelView` became actionable: Solo Free Play, Solo Bet
(presets + Custom modal), Challenge Player, Tournament (admin
opens registration), Status, Rules. A new
`disbot/cogs/blackjack/actions.py` module wraps the existing
`_Game`, `_active`, `_pvp`, `_tournaments`, `BlackjackView`,
`_ChallengeView`, `_TournRegistrationView` — same engine state the
typed commands use.

### PR 6 — Deathmatch playable panel + bot duels

* Replaced the previous empty `discord.ui.View()` with
  `DeathmatchPanelView`: Fight Bot, Challenge Player, Rules.
* New `_BotDuelView` adds player-vs-bot duels reusing the existing
  `_Duel` state class. Bot AI v1: 70/30 attack/defend at full HP,
  more defensive as HP drops below 50%.
* **Plan §13 critical rule**: bot duels do NOT call
  `cog.update_leaderboard` or `db.update_deathmatch`. PvP duels
  retain the existing leaderboard write path unchanged. Two
  `assert_not_called()` tests pin this invariant.
* `!deathmatch @bot` remains rejected on the typed-command path;
  only the panel's Fight Bot button is the supported bot-duel
  entry point.

### PR 7 — Shared back-to-panel button helper

`views/games/common.py` introduced `BackToPanelButton`, an
evidence-driven extraction of a pattern that repeated 3× in the
RPS panel. The RPS panel migrated to use it; Blackjack and
Deathmatch migration is deferred to a follow-up after their PRs
merge to avoid cross-branch conflicts.

### PR 8 — Game settings schemas + readiness integration

The first per-game `SubsystemSchema` for RPS, Blackjack, and
Deathmatch, each declaring one `SettingSpec` whose key the runtime
actually reads (plan §2.12 hard rule):

* `RPS_DEFAULT_ENTRY_FEE` — read by `!rpsregister` when omitted.
* `BLACKJACK_DEFAULT_ENTRY_FEE` — read by `!bjtournament` when
  omitted.
* `DEATHMATCH_TURN_TIMEOUT` — read by `_ChallengeView.btn_accept`
  when spawning `_DuelView`.

Readiness integration is automatic: `services.setup_readiness.
collect` walks `all_schemas()` so the new schemas surface in
`!platform setup-readiness` rows without any additional plumbing.

### PR 9 — This doc

Operator-facing roadmap + deferred-inventory note. No code
changes.

## Manual smoke matrix

Run after a fresh deploy. Each item is either ✅ (verified live)
or **PENDING** (couldn't verify in the sandbox / awaiting first
live test).

### Hubs

* [ ] `!games` opens the playable Games hub with direct game buttons.
* [ ] `/games` opens the same hub via slash.
* [ ] Help → Games opens the playable hub.
* [ ] Community → XP child panel shows Back-to-Community.
* [ ] Community → Leaderboard child panel shows Back-to-Community.

### RPS (PR 3 + PR 4)

* [ ] `!help rps`, `!help rock paper scissors`, `!help rps_tournament`
  all open the same panel labelled "Rock Paper Scissors".
* [ ] Help → Games → RPS → Quick Play opens `_RpsView` with
  Rock/Paper/Scissors buttons.
* [ ] Bet Match preset (10/25/50/100) spawns playable view with bet.
* [ ] Bet Match → Custom opens modal, validates integer + non-negative.
* [ ] Challenge Player → UserSelect → opens PvP challenge.
* [ ] Tournament → admin sees "Open Registration", click delegates
  to `!rpsregister` flow.
* [ ] `!rps`, `!rpsregister`, `!rpsstart` still work unchanged.
* [ ] `!leaderboard rps` still works.

### Blackjack (PR 5)

* [ ] Help → Games → Blackjack → Solo Free Play opens
  `BlackjackView` with Hit/Stand/Double.
* [ ] Solo Bet preset starts game with bet (10/25/50/100/Custom).
* [ ] Solo Bet → Custom opens modal, validates input.
* [ ] Challenge Player → UserSelect → opens `_ChallengeView`.
* [ ] Tournament → admin "Open Registration" spawns
  `_TournRegistrationView` + ✅ reaction.
* [ ] Status button shows existing tournament if any.
* [ ] `!blackjack`, `!bj`, `!bjtournament`, `!bjstart`, `!bjstatus`
  all still work unchanged.

### Deathmatch (PR 6)

* [ ] Help → Games → Deathmatch opens `DeathmatchPanelView` (no
  longer empty).
* [ ] Fight Bot starts a playable bot duel.
* [ ] Player Attack/Defend triggers bot's auto-response.
* [ ] Win/loss shown in result embed.
* [ ] Bot win/loss does **NOT** change PvP leaderboard
  (`!leaderboard deathmatch` unchanged after a bot duel).
* [ ] PvP duel **DOES** update PvP leaderboard as before.
* [ ] Challenge Player → UserSelect → opens PvP challenge.
* [ ] `!deathmatch @user` still works unchanged.
* [ ] `!deathmatch @bot` still rejected on the command path.

### Back navigation chains

* [ ] Help → Games → RPS → Bet Match → Back to RPS → main RPS panel
  → Back to Games → Back to Help.
* [ ] Same chain for Blackjack.
* [ ] Same chain for Deathmatch.

### Settings + readiness (PR 8)

* [ ] `!platform setup-readiness` shows rows for `rps_tournament`,
  `blackjack`, `deathmatch` with `settings_declared >= 1`.
* [ ] Setting an `rps_default_entry_fee` value via the settings
  manager makes `!rpsregister` (without args) use it.
* [ ] Same for `blackjack_default_entry_fee` + `!bjtournament`.
* [ ] Same for `deathmatch_turn_timeout` + the `_DuelView` timeout.
* [ ] Defaults (0 fee, 60s timeout) are used when the setting is
  unset.

## Deferred — next session candidates

These items were explicitly out of scope for the actionability
sweep per the plan §12 + §13 acceptance checklists. They're
recorded here so the next session can prioritize.

### Inventory architecture redesign

The current `UnifiedInventoryView` is sufficient for now. A full
redesign would introduce:

```
disbot/core/items/
├── catalogue.py           # canonical ItemSpec catalog
├── item_types.py          # Material / Tool / Equipment / Consumable
├── rarity.py              # rarity tiers + drop tables
└── item_effects.py        # on-use / on-equip effect engine

disbot/services/inventory_service.py
- grant_item / consume_item / transfer_item
- craft_item / equip_item / resolve_effect

disbot/views/inventory/
├── hub.py                 # multi-category inventory hub
├── category_view.py       # per-category browsing
├── item_detail.py         # individual item + actions
├── crafting_view.py       # recipe browser
└── equipment_view.py      # loadout management
```

Logical inventory sections to surface: Materials, Tools, Equipment,
Consumables, Crafted Items, Economy Items, Quest/Event Items,
Trophies/Badges.

**Trigger to start**: all 12 DoD items from the operating-contract
plan §8 pass (which they will once PRs 5–8 merge), AND there's a
concrete user-facing requirement for richer item interaction beyond
what `UnifiedInventoryView` provides.

### RPS canonical-key migration

`SUBSYSTEMS["rps_tournament"]` stays canonical through this sweep.
A future dedicated PR can migrate to `SUBSYSTEMS["rps"]` if the
team decides the cleanup is worth it. The migration must handle
in a single atomic change:

* `SUBSYSTEMS` key rename + all dependent dict accesses.
* Saved-state subsystem column rename (DB migration).
* Rank-provider key aliases.
* `tournament_state_service` `kind` value.
* Readiness rows.

Until then, `rps_tournament` is the canonical key; "Rock Paper
Scissors" is the display name.

### RPS package move

`disbot/cogs/rps_tournament/` could become `disbot/cogs/rps/` for
naming consistency. Deferred until after the canonical-key
migration — moving the package without renaming the key would
create confusion.

### Bot-duel difficulty settings

Deathmatch bot-duel AI v1 ships with one fixed strategy (HP-biased
attack/defend). A `deathmatch_bot_difficulty` setting could pick
between easy / normal / hard with different attack/defend ratios.
Add only if user feedback motivates it.

### Bot-duel stats provider

Bot-duel wins/losses currently stay off the PvP leaderboard. A
separate `deathmatch_bot` rank provider could track bot-duel stats
in their own category. Defer until requested.

### Game Leaderboards hub button

PR 2 deliberately omitted a "🏆 Game Leaderboards" button from the
Games Hub because no real cross-game leaderboard surface exists.
Add when the underlying surface is built.

### Full setup wizard

The plan deliberately stopped at "expose settings + readiness
surface them" without building a step-by-step setup wizard. The
data path is wizard-compatible; the wizard UI is the remaining
work.

### Migrate Blackjack + Deathmatch to BackToPanelButton

PR 7 introduced `views/games/common.BackToPanelButton` but only
migrated the RPS panel to use it. After PRs 5 + 6 merge, a small
follow-up should:

* Replace `_BlackjackBackToPanelButton` with the shared helper.
* Replace `_DeathmatchBackToPanelButton` with the shared helper.
* Consider extracting `BetPresetView` (RPS + Blackjack both have
  the 10/25/50/100/Custom shape) and `OpponentSelectView` (all
  three games have a UserSelect for PvP).

### Additional game settings

PR 8 added one `SettingSpec` per game. Future settings to wire (per
the original plan §5):

**RPS**: `default_mode`, `default_best_of`, `registration_duration`,
`bot_match_enabled`, `tournament_channel`.

**Blackjack**: `default_bet_presets`, `default_tournament_rounds`,
`default_registration_duration`, `tournament_category_name`,
`announce_channel`.

**Deathmatch**: `base_hp`, `attack_damage`, `critical_chance`,
`defense_reduction`, `bot_enabled`, `bot_difficulty`.

Each requires the runtime read to be wired before the setting lands
(plan §2.12 hard rule).

## Cross-references

* Operating-contract plan: `/root/.claude/plans/current-baseline-for-the-polished-tarjan.md`.
* Settings command map: `docs/setup-platform/settings-customization-command-map.md`.
* Architecture overview: `docs/architecture.md`.
* Setup-readiness service: `disbot/services/setup_readiness.py`.
* Actionability invariant: `tests/unit/help/test_help_actionability_contract.py`.
* Shared game helpers: `disbot/views/games/common.py`.
