# Help / Command Surface Map

Source-of-truth inventory for every loaded cog/subsystem and how each is
reachable today through Help, hubs, and typed commands. Captured at HEAD
`38353aa` (post-PR-#142, post-PR-#143). The Help routing unification
landed in PR #142; this doc now reflects the merged state, not the
pre-PR perspective.

The columns that matter most are **owner**, **panel**, **Help route**,
**hub route**, and **recommended placement**. Command lists are
representative, not exhaustive — large alias/legacy families are
summarized with a count.

Post-PR-#142 routing summary (relevant to every row in §2):

- Typed `!help <name>` and the Help dropdown share a single resolver in
  `disbot/cogs/help/route.py` (`resolve_route` + `open_route`). Both
  routes call the host cog's `build_help_menu_view` hook for hub +
  subsystem destinations and fall back to a command-list embed only
  when the hook is missing or raises.
- 23 of 24 loaded cogs expose `build_help_menu_view`. `help_cog` itself
  is the exception — it IS the Help surface, so there is no hook.
- The hub key `diagnostic` is "Platform / Diagnostics". The override
  table `HUB_PANEL_BUILDERS["diagnostic"] = "build_platform_help_menu_view"`
  routes hub → Platform Hub. Subsystem aliases `diagnostics`/`diag`
  resolve to the Diagnostics subsystem (not the Platform hub).

## 1. Mother hubs

8 hubs in `disbot/utils/hub_registry.py`. Every hub key matches a
`SUBSYSTEMS` key so Help can resolve a hub entry to its host cog.

| key | display | entry | host cog | panel | min tier |
| --- | --- | --- | --- | --- | --- |
| `games` | 🎮 Games | `!games` | `games_cog` | `GamesHubView` (`views/games/hub.py`) | user |
| `economy` | 💰 Economy | `!economymenu` | `economy_cog` | `EconomyPanelView` | user |
| `moderation` | 🛡️ Moderation & Safety | `!modmenu` | `moderation_cog` | `ModPanelView` | moderator |
| `community` | 🌱 Community | `!community` | `community_cog` | `CommunityHubView` | user |
| `utility` | 🧰 Utility | `!utilitymenu` | `utility_cog` | `UtilityPanelView` | user |
| `admin` | ⚙️ Admin / Operations | `!adminmenu` | `admin_cog` | `_AdminPanelView` | administrator |
| `settings` | 🔧 Settings / Configuration | `!settings` | `settings_cog` | `SettingsHubView` | administrator |
| `diagnostic` | 🩺 Platform / Diagnostics | `!platform` | `diagnostic_cog` | `_PlatformHubView` | administrator |

## 2. Subsystem inventory

24 cogs in `disbot/config.py:33-58`. 23 of 24 expose
`build_help_menu_view`; only `help_cog` itself does not. The Help route
resolver therefore opens a real panel for every subsystem except `help`,
and only falls back to the command-list embed when the hook is missing
or raises.

| subsystem | owner | public commands (sample) | hidden / legacy | panel hook | Help route today | Hub route today | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `admin` | `admin_cog.py` | `adminmenu`, `serverstats`, `cog`, `loadall`, `unloadall`, `restart`, `loglevel` | — | `_AdminPanelView` | `!help admin` → opens Admin panel (shared resolver) | dropdown Admin → panel | hub top-level (Admin) |
| `blackjack` | `blackjack_cog.py:95` | `blackjack`, `bj`, `bjtournament`, `bjstart`, `bjstatus` | — | `BlackjackPanelView` | `!help blackjack` → opens Blackjack panel (shared resolver) | reached via Games | hub child (Games) |
| `chain` | `chain_cog.py` | `chain`, `chainmenu` | — | `ChainPanelView` | `!help chain` → opens Chain panel (shared resolver) | reached via Games / Community | hub child |
| `channel` | `channel_cog.py:144` | `lock`, `unlock` | several `*_channel`-family commands | `ChannelPanelView` | `!help channel` → opens Channel panel (shared resolver) | reached via Admin | hub child (Admin) |
| `cleanup` | `cleanup_cog.py:324` | `cleanuphistory`, `word`, `wordmenu`, `cleanup` | — | `CleanupHubView` | `!help cleanup` → opens Cleanup panel (shared resolver) | reached via Moderation | hub child (Moderation) |
| `community` | `community_cog.py` | `community` | — | `CommunityHubView` | `!help community` → opens Community panel (shared resolver) | dropdown Community → panel | hub top-level |
| `counting` | `counting_cog.py` | `countingmenu`, `start_match`, `end_match`, `reset_count` | — | `CountingPanelView` | `!help counting` → opens Counting panel (shared resolver) | reached via Games / Community | hub child |
| `deathmatch` | `deathmatch_cog.py` | `dm_challenge`, `deathmatch`, `dm`, `dm_help` | — | `DeathmatchPanelView` | `!help deathmatch` → opens Deathmatch panel (shared resolver) | reached via Games | hub child (Games) |
| `diagnostic` | `diagnostic_cog.py:70` | `diagnostics`, `diag`, `latency`, `platform` (group, 20+ subcommands) | — | `_DiagnosticsHubView` (generic hook); `_PlatformHubView` (platform builder) | `!help platform` / `!help diagnostic` → opens Platform Hub via the `HUB_PANEL_BUILDERS["diagnostic"]` override; `!help diagnostics` / `!help diag` → opens Diagnostics subsystem via the subsystem-alias branch (not the Platform hub) | hub top-level "Platform / Diagnostics" via the override; sibling subsystem aliases reach Diagnostics | hub top-level (Platform); `diagnostics`/`diag` open Diagnostics Hub |
| `economy` | `economy_cog.py` | `economymenu`, `daily`, `work`, `shop`, `balance`/`bal`/`wallet` | several admin/legacy commands | `EconomyPanelView` | `!help economy` → opens Economy panel (shared resolver) | dropdown Economy → panel | hub top-level |
| `games` | `games_cog.py` | `games` | — | `GamesHubView` | `!help games` → opens Games hub (shared resolver) | dropdown Games → panel | hub top-level (cleanest model) |
| `general` | `general_cog.py` | `fact`, `joke`, `quote`, `motivate`, `greet` | — | `_GeneralPanelView` | `!help general` → opens General panel (shared resolver) | reached via Utility (future, once `parent_hub` is set) | hub child (Utility, future) |
| `help` | `help_cog.py` | `help` (alias `hilfe`) | — | **no panel hook (Help itself is the panel)** | n/a (Help Home embeds + `HelpCategoryView` dropdown) | dropdown root | Help Home |
| `inventory` | `inventory_cog.py:376` | `inventory`, `inv` | — | `UnifiedInventoryView` | `!help inventory` → opens Inventory panel (shared resolver) | reached via Economy (Inventory btn → in-place edit + Back-to-Economy; PR #143) | hub child (Economy, future) |
| `leaderboard` | `leaderboard_cog.py:200` | (none public-flagged; entry inferred from registry) | — | `LeaderboardView` | `!help leaderboard` → opens Leaderboard panel (shared resolver) | top-level today; cross-linked from Economy / Community (future) | hub child (Economy / Community) |
| `logging` | `logging_cog.py:88` | `logging` | — | `LoggingPanelView` | `!help logging` → opens Logging panel (shared resolver) | reached via Moderation / Admin | hub child |
| `mining` | `mining_cog.py:65` | `mineinv`/`mineinventory`, `minestats` | mining game flow commands (start/dig/etc.) | `MiningHubView` | `!help mining` → opens Mining panel (shared resolver) | reached via Games (primary) / Economy cross-link | hub child (Games) |
| `moderation` | `moderation_cog.py` | `modmenu`, `warn`, `timeout`, `kick`, `ban`, `unban`, `clearwarnings`, `modlogs` | — | `ModPanelView` | `!help moderation` → opens Moderation panel (shared resolver) | dropdown Moderation → panel | hub top-level |
| `proof_channel` | `proof_channel_cog.py:113` | `prizestatus`, `prizemenu`, `timedprize` | — | `_PrizeManagerView` | `!help proof` → opens Proof Channel panel (shared resolver) | reached via Moderation | hub child (Moderation) |
| `role` | `role_cog.py:334` | `roles`, `rolesettings`, `rolemenu` (legacy alias) | 8+ legacy commands: `rolecreator`, `createrole`, `deleterole`, `setrole`, `unsetrole`, `assignroles`, `debugroles`, `refreshmembers`, plus react-role family | `RoleHubPanelView` | `!help roles` → opens Role panel (shared resolver) | reached via Community | hub child (Community); legacy commands remain as hidden compatibility |
| `rps_tournament` | `rps_tournament_cog.py:118` | `rpsregister`/`rpsreg`, `rpsstart`/`rpsbegin`, `rpsbot`, `rpsmatchup`, `rpshelp`, `rpssettings` | — | `RPSPanelView` | `!help rps` → opens RPS panel (shared resolver) | reached via Games | hub child (Games) |
| `settings` | `settings_cog.py` | (entry via `!settings`) | — | `SettingsHubView` | `!help settings` → opens Settings panel (shared resolver) | dropdown Settings → panel | hub top-level |
| `utility` | `utility_cog.py` | `utilitymenu`, `clear`/`purge`, `info`, `serverinfo`, `userinfo`, `avatar`, `remind` | — | `_UtilityPanelView` | `!help utility` → opens Utility panel (shared resolver) | dropdown Utility → panel | hub top-level |
| `xp` | `xp_cog.py` | `xpmenu`, `rank`, `givexp`, `resetxp`, `xpconfig` | — | `_XpHubView` | `!help xp` → opens XP panel (shared resolver) | reached via Community | hub child (Community); admin controls live in panel |

## 3. Known inconsistencies (resolved by PR #142 / PR #143)

These three classes of bug were live before PR #142 / PR #143. All are
now resolved in `main` and pinned by tests under `tests/unit/help/` and
`tests/unit/views/`. They remain documented here so a future reader
encountering similar drift recognises the prior shape.

1. **Typed Help and dropdown Help diverged.** Pre-PR-#142,
   `!help <category>` iterated `SUBSYSTEMS` and rendered
   `build_cog_embed` — it never consulted `hub_registry`, never called
   `build_help_menu_view`, and never attached Back-to-Help. The
   dropdown (`HelpCategoryView._on_select`) did all three. Same word,
   two different surfaces.
   *Resolution:* PR #142 introduced `disbot/cogs/help/route.py` with
   `HelpRoute` / `HelpOpener` / `resolve_route` / `open_route`. Typed
   Help and the dropdown both go through the same resolver. Pinned by
   `tests/unit/help/test_help_typed_category_routes.py` and
   `tests/unit/help/test_help_route_resolution.py`.

2. **Platform Help route mismatched its panel.** The hub `diagnostic`
   was registered as "Platform / Diagnostics" with entry `!platform`,
   but `DiagnosticCog.build_help_menu_view` returned
   `_DiagnosticsHubView`. The Help dropdown therefore opened the wrong
   hub when the user picked "Platform / Diagnostics".
   *Resolution:* PR #142 added a sibling builder
   `build_platform_help_menu_view` returning `_PlatformHubView`, plus a
   per-hub override table `HUB_PANEL_BUILDERS["diagnostic"] = "build_platform_help_menu_view"`
   in `help_cog.py`. The generic hook stays on Diagnostics so Admin →
   Diagnostics still works. Pinned by
   `tests/unit/help/test_platform_diagnostics_split.py`.

3. **Help Home rows were uneven.** `build_categories_overview_embed`
   showed an `Includes: ...` line for Games (populated
   `primary_children`) and nothing for Economy / Moderation / Community
   / Utility (empty `primary_children` per S7–S10 v1).
   *Resolution:* PR #142 removed `Includes:` entirely and uses uniform
   two-line rows. Pinned by `tests/unit/help/test_help_home_copy.py`.

PR #143 (menu navigation lifecycle) addressed a separate class of bug
— detached panel messages, dead-end result screens, and a no-op root
"Overview" button on Mining — which were lifecycle issues, not Help
routing issues. See `tests/unit/views/test_economy_inventory_edit.py`,
`tests/unit/views/test_economy_work_result.py`,
`tests/unit/views/test_mining_no_root_overview.py`,
`tests/unit/views/test_mining_back_to_help.py`, and
`tests/unit/views/test_mining_back_to_games.py`.

## 4. Architectural notes

- **Games is the cleanest current model.** Hub view is registry-driven
  via `parent_hub`, has all six game children explicitly listed, and
  the hub UI is built from a single source.
- **S7–S10 Help promotions (Economy / Moderation / Community / Utility)
  are first-pass.** Their hubs route to existing panels via
  `build_help_menu_view`. Their `primary_children` are empty until a
  follow-up PR flips `parent_hub` metadata on `inventory`, `leaderboard`,
  `xp`, `role`, `cleanup`, `logging`, `proof_channel`, and `general` —
  tracked as plan PR #3.
- **Role public entry is `!roles`.** Legacy `rolemenu` and the
  rolemenu-style command family remain registered as hidden
  compatibility — they will not surface in Help.
- **Utility / Proof / Channel exposure.** Several admin tools (channel
  lock/unlock, proof prize controls, cleanup history) are reached
  primarily through hub panels — `!help <name>` resolves to those
  panels via the shared resolver. The hub panels are the canonical
  exposure point; typed commands still work for power users.
- **XP mixes user rank display with admin controls.** The XP panel
  surfaces both. Admin-only routing belongs in the panel, not in the
  command list. Marked for a future split if/when XP gets its own hub.
- **Advanced remains necessary but secondary.** Power-users who know a
  command name should not have to navigate hubs to find it.
- **Back-to-X helpers are siblings, not a framework.** Four helpers
  exist today and follow the same shape (label, custom_id, parent
  builder, row 4, secondary style):
  `_attach_back_to_help_button` in `cogs/help_cog.py:167`,
  `attach_back_to_admin_button` in `cogs/admin_cog.py:229`,
  `attach_back_to_settings_button` in `views/settings/subsystem_view.py:240`,
  `attach_back_to_games_button` in `views/games/hub.py:113`, and
  (added in PR #143) `attach_back_to_economy_button` in
  `views/economy/main_panel.py`. All five wrap
  `views/navigation.py:attach_back_button`. Future hub children should
  reuse one of these helpers rather than create a parallel one.

## 5. Future routing surfaces

Tracked as the stabilization-plan PR sequence
(`/root/.claude/plans/superbot-planning-jolly-wadler.md` §8). Listed
here so a future reader can map this doc to the in-flight plan.

- **`parent_hub` metadata for S7–S10 children** (plan PR #3) —
  declare `parent_hub` on `inventory → economy`, `leaderboard →
  economy`, `xp → community`, `role → community`, `cleanup →
  moderation`, `logging → moderation`, `proof_channel → moderation`,
  `general → utility`. After it lands, the *Recommendation* column
  below the corresponding rows changes from "hub child (... future)"
  to "hub child (...) — declared".
- **Community metadata-driven hub** (plan PR #4) — replace
  `CommunityHubView._HUB_CHILDREN` hardcoded tuple with SUBSYSTEMS
  discovery, mirroring `views/games/hub.py:discover_game_children`.
- **XP config modal pipeline migration** (plan PR #5) — three modals
  in `disbot/views/xp/modals.py` write directly via `db.set_setting`;
  migrate to `SettingsMutationPipeline`.
- **Economy log-channel pipeline migration** (plan PR #6) — preferred
  via `BindingMutationPipeline`.
- **Settings numeric presets + channel/role selectors** (plan PR #7).
- **Settings default-on with kill switch** (plan PR #8).
- **Slash front door** `/help` (plan PR #9) — reuses `resolve_route` +
  `open_route` + `HelpOpener.from_interaction`. Broader slash rollout
  (`/games`, `/economy`, etc.) follows in subsequent PRs.
- **Setup wizard** (`!setup`) — deferred until the S7 logging-route
  pipeline, S8 cleanup-policy pipeline, S10 preset packs, and the P5
  platform UI framework all land. See `docs/roadmap_setup_platform.md`.
