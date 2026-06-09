# Help / Command Surface Map

> **Status:** `binding` — Cog/command surface inventory; pinned to code by a doc-test.

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

9 hubs in `disbot/utils/hub_registry.py`. Every hub key matches a
`SUBSYSTEMS` key so Help can resolve a hub entry to its host cog.

| key | display | entry | host cog | panel | min tier |
| --- | --- | --- | --- | --- | --- |
| `games` | 🎮 Games | `!games` | `games_cog` | `GamesHubView` (`views/games/hub.py`) | user |
| `btd6` | 🐵 BTD6 Assistant | `!btd6` | `btd6_cog` | `BTD6PanelView` | user |
| `economy` | 💰 Economy | `!economymenu` | `economy_cog` | `EconomyPanelView` | user |
| `moderation` | 🛡️ Moderation & Safety | `!modmenu` | `moderation_cog` | `ModPanelView` | moderator |
| `community` | 🌱 Community | `!community` | `community_cog` | `CommunityHubView` | user |
| `utility` | 🧰 Utility | `!utilitymenu` | `utility_cog` | `UtilityPanelView` | user |
| `admin` | ⚙️ Admin / Operations | `!adminmenu` | `admin_cog` | `_AdminPanelView` | administrator |
| `settings` | 🔧 Settings / Configuration | `!settings` | `settings_cog` | `SettingsHubView` | administrator |
| `diagnostic` | 🩺 Platform / Diagnostics | `!platform` | `diagnostic_cog` | `_PlatformHubView` | administrator |
| `server_management` | 🧭 Server Management | `!servermanagement` | `server_management_cog` | `ServerManagementHubView` (`views/server_management/hub.py`) | administrator |

## 2. Subsystem inventory

26 cogs in `disbot/config.py:33-58`. 25 of 26 expose
`build_help_menu_view`; only `help_cog` itself does not. The Help route
resolver therefore opens a real panel for every subsystem except `help`,
and only falls back to the command-list embed when the hook is missing
or raises.

| subsystem | owner | public commands (sample) | hidden / legacy | panel hook | Help route today | Hub route today | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `admin` | `admin_cog.py` | `adminmenu`, `serverstats`, `cog`, `loadall`, `unloadall`, `restart`, `loglevel` | — | `_AdminPanelView` | `!help admin` → opens Admin panel (shared resolver) | dropdown Admin → panel | hub top-level (Admin) |
| `ai` | `ai_cog.py` | `ai`, `aimenu`, `ai status`, `ai diagnostics`, `ai providers`, `ai routing`, `ai settings` | — | `AIPanelView` | `!help ai` → opens AI Platform panel (shared resolver) | reached via Admin / Diagnostics | central AI policy host (M1+); auto-dispatched settings via `ai settings` and `!settings` hub |
| `btd6` | `btd6_cog.py` | `btd6`, `btd6menu`, `btd6 ask`, `btd6 tower`, `btd6 hero`, `btd6 round`, `btd6 relic`, `btd6 ct`, `btd6 leaderboard`, `btd6 live`, `btd6 event`, `btd6 status`, `btd6 diagnostics`, `btd6 test-intent` | — | `BTD6PanelView` | `!help btd6` → opens BTD6 panel (shared resolver) | dropdown BTD6 → panel | hub top-level (BTD6 Assistant) |
| `blackjack` | `blackjack_cog.py:95` | `blackjack`, `bj`, `bjtournament`, `bjstart`, `bjstatus` | — | `BlackjackPanelView` | `!help blackjack` → opens Blackjack panel (shared resolver) | reached via Games | hub child (Games) |
| `chain` | `chain_cog.py` | `chain`, `chainmenu` | — | `_ChainMenuView` | `!help chain` → opens Chain panel (shared resolver) | reached via Games / Community | hub child |
| `channel` | `channel_cog.py:144` | `lock`, `unlock` | several `*_channel`-family commands | `_ChannelManagerView` | `!help channel` → opens Channel panel (shared resolver) | reached via Admin | hub child (Admin) |
| `cleanup` | `cleanup_cog.py:324` | `cleanuphistory`, `word`, `wordmenu`, `cleanup` | — | `CleanupPanelView` | `!help cleanup` → opens Cleanup panel (shared resolver) | reached via Moderation; `parent_hub="moderation"` since PR #3 | hub child (Moderation) — declared |
| `community` | `community_cog.py` | `community` | — | `CommunityHubView` | `!help community` → opens Community panel (shared resolver) | dropdown Community → panel | hub top-level |
| `counting` | `counting_cog.py` | `countingmenu`, `start_match`, `end_match`, `reset_count` | — | `_CountingHubView` | `!help counting` → opens Counting panel (shared resolver) | reached via Games / Community | hub child |
| `deathmatch` | `deathmatch_cog.py` | `dm_challenge`, `deathmatch`, `dm`, `dm_help` | — | `DeathmatchPanelView` | `!help deathmatch` → opens Deathmatch panel (shared resolver) | reached via Games | hub child (Games) |
| `diagnostic` | `diagnostic_cog.py:70` | `diagnostics`, `diag`, `latency`, `platform` (group, 20+ subcommands) | — | `_DiagnosticsHubView` (generic hook); `_PlatformHubView` (platform builder) | `!help platform` / `!help diagnostic` → opens Platform Hub via the `HUB_PANEL_BUILDERS["diagnostic"]` override; `!help diagnostics` / `!help diag` → opens Diagnostics subsystem via the subsystem-alias branch (not the Platform hub) | hub top-level "Platform / Diagnostics" via the override; sibling subsystem aliases reach Diagnostics | hub top-level (Platform); `diagnostics`/`diag` open Diagnostics Hub |
| `economy` | `economy_cog.py` | `economymenu`, `daily`, `work`, `shop`, `balance`/`bal`/`wallet` | several admin/legacy commands | `EconomyPanelView` | `!help economy` → opens Economy panel (shared resolver) | dropdown Economy → panel | hub top-level |
| `games` | `games_cog.py` | `games` | — | `GamesHubView` | `!help games` → opens Games hub (shared resolver) | dropdown Games → panel | hub top-level (cleanest model) |
| `general` | `general_cog.py` | `fact`, `joke`, `quote`, `motivate`, `greet` | — | `_GeneralPanelView` | `!help general` → opens General panel (shared resolver) | reached via Utility (`parent_hub="utility"` since PR #3) | hub child (Utility) — declared |
| `four_twenty` | `four_twenty_cog.py` | `420`, `fourtwenty` | — | `_FourTwentyPanelView` | `!help 420` → opens 420 panel (shared resolver) | reached via Utility (`parent_hub="utility"` since PR #420) | hub child (Utility) — declared; passive `FourTwentyStage` 🍃-reacts to `420` mentions |
| `help` | `help_cog.py` | `help` (alias `hilfe`) | — | **no panel hook (Help itself is the panel)** | n/a (Help Home embeds + `HelpCategoryView` dropdown) | dropdown root | Help Home |
| `inventory` | `inventory_cog.py:376` | `inventory`, `inv` | — | `UnifiedInventoryView` | `!help inventory` → opens Inventory panel (shared resolver) | reached via Economy (Inventory btn → in-place edit + Back-to-Economy; PR #143). `parent_hub="economy"` since PR #3. | hub child (Economy) — declared |
| `leaderboard` | `leaderboard_cog.py:200` | (none public-flagged; entry inferred from registry) | — | `LeaderboardView` | `!help leaderboard` → opens Leaderboard panel (shared resolver) | `parent_hub="economy"` since PR #3; Community cross-link migrates in PR #4 | hub child (Economy) — declared; Community cross-link in PR #4 |
| `logging` | `logging_cog.py:88` | `logging` | — | `LoggingPanelView` | `!help logging` → opens Logging panel (shared resolver) | reached via Moderation / Admin; `parent_hub="moderation"` since PR #3 | hub child (Moderation) — declared |
| `mining` | `mining_cog.py:65` | `mineinv`/`mineinventory`, `minestats` | mining game flow commands (start/dig/etc.) | `MiningHubView` | `!help mining` → opens Mining panel (shared resolver) | reached via Games (primary, `parent_hub="games"`); Economy hub declares Mining as a `cross_link_children` since PR #3 | hub child (Games); Economy cross-link |
| `moderation` | `moderation_cog.py` | `modmenu`, `warn`, `timeout`, `kick`, `ban`, `unban`, `clearwarnings`, `modlogs` | — | `ModPanelView` | `!help moderation` → opens Moderation panel (shared resolver) | dropdown Moderation → panel | hub top-level |
| `proof_channel` | `proof_channel_cog.py:113` | `prizestatus`, `prizemenu`, `timedprize` | — | `_PrizeManagerView` | `!help proof` → opens Proof Channel panel (shared resolver) | reached via Moderation; `parent_hub="moderation"` since PR #3 | hub child (Moderation) — declared |
| `role` | `role_cog.py:334` | `roles`, `rolesettings`, `rolemenu` (legacy alias) | 8+ legacy commands: `rolecreator`, `createrole`, `deleterole`, `setrole`, `unsetrole`, `assignroles`, `debugroles`, `refreshmembers`, plus react-role family | `RoleHubPanelView` | `!help roles` → opens Role panel (shared resolver) | reached via Community; `parent_hub="community"` since PR #3 | hub child (Community) — declared; legacy commands remain as hidden compatibility |
| `rps_tournament` | `rps_tournament_cog.py:118` | `rpsregister`/`rpsreg`, `rpsstart`/`rpsbegin`, `rpsbot`, `rpsmatchup`, `rpshelp`, `rpssettings` | — | `RPSPanelView` | `!help rps` → opens RPS panel (shared resolver) | reached via Games | hub child (Games) |
| `server_management` | `server_management_cog.py` | `servermanagement`, `servermenu`, `guildmenu`, `/server-management` | — | `ServerManagementHubView` | `!help` → Server Management (shared resolver) | dropdown Server Management → panel | hub top-level (operator) — composes moderation/channels/roles/cleanup/setup |
| `settings` | `settings_cog.py` | (entry via `!settings`) | — | `SettingsHubView` | `!help settings` → opens Settings panel (shared resolver) | dropdown Settings → panel | hub top-level |
| `utility` | `utility_cog.py` | `utilitymenu`, `clear`/`purge`, `info`, `serverinfo`, `userinfo`, `avatar`, `remind` | — | `_UtilityPanelView` | `!help utility` → opens Utility panel (shared resolver) | dropdown Utility → panel | hub top-level |
| `xp` | `xp_cog.py` | `xpmenu`, `rank`, `givexp`, `resetxp`, `xpconfig` | — | `_XpHubView` | `!help xp` → opens XP panel (shared resolver) | reached via Community; `parent_hub="community"` since PR #3 | hub child (Community) — declared; admin controls live in panel |

## 3. Known inconsistencies (resolved by PR #142 / PR #143)

> **DECIDED, registration queued (Q-0044 answered 2026-06-09) — Community Spotlight
> is still outside the Help/hub surface until the scaffold lane ships.**
> `cogs/community_spotlight_cog.py` (merged via #613/#614, side-lane) registers
> `!spotlight` (alias `!activity` — the greedy `!hub`/`!server` aliases were
> **dropped 2026-06-09** per Q-0044) with its own panel (`SpotlightView`), but is
> **not yet** in `utils/subsystem_registry.py` / `utils/hub_registry.py` — invisible
> to typed Help routes, the Help dropdown, and this doc's §2 inventory (whose
> doc-test pins only *registered* subsystems). **The decision:** build the Q-0025
> `new_subsystem.py` scaffold, then register Spotlight as a `community`-hub child
> (its panel adopts the hub-navigation standard in the same move). When that lane
> ships: add the §2 row and delete this banner.

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
  have declared parent_hub metadata for their children since PR #3.**
  `inventory` and `leaderboard` point at Economy; `xp` and `role` point
  at Community; `cleanup`, `logging`, and `proof_channel` point at
  Moderation; `general` points at Utility. Each parent hub's
  `primary_children` tuple in `hub_registry.py` mirrors that set. The
  hub views still render children via their own discovery — Games uses
  `discover_game_children()` from SUBSYSTEMS; Community uses a
  hardcoded `_HUB_CHILDREN` tuple that PR #4 will migrate to
  registry-driven discovery.
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
(`/root/.claude/plans/superbot-planning-jolly-wadler.md` §8). All
nine PRs have landed; this section is now a historical map between
the plan numbers and the merge PR numbers, plus the work that remains
beyond the plan.

- **`parent_hub` metadata for S7–S10 children** (plan PR #3) —
  **done** via PR #145. `parent_hub` declared on `inventory → economy`,
  `leaderboard → economy`, `xp → community`, `role → community`,
  `cleanup → moderation`, `logging → moderation`,
  `proof_channel → moderation`, `general → utility`. The eight rows
  above now read "hub child (...) — declared". Mining is additionally
  declared as a `cross_link_children` on the Economy hub.
- **Community metadata-driven hub** (plan PR #4) — **done** via
  PR #146. `CommunityHubView` discovers primary children from
  `SUBSYSTEMS` (`parent_hub == "community"`) and cross-links from
  `hub_registry.get_hub("community").cross_link_children`, mirroring
  the Games hub pattern. Button labels now come from registry
  metadata (`emoji` + `display_name`).
- **XP config modal pipeline migration** (plan PR #5) — **done** via
  PR #147. The three XP config modals (`_XpRangeModal`,
  `_XpCooldownModal`, `_XpChannelModal`) now route through
  `SettingsMutationPipeline().set_value(...)`; a new
  `xp_announce_channel` SettingSpec carries the channel-id-as-str
  shape. Each write lands a `settings_mutation_audit` row.
- **Economy log-channel pipeline migration** (plan PR #6) — **done**
  via PR #148. Used `SettingsMutationPipeline` (not
  `BindingMutationPipeline`) because two of the three call sites are
  listener-triggered with no actor; the binding pipeline currently
  requires an administrator-tier actor. The existing `log_channel`
  BindingSpec stays as the typed-resource declaration; the new
  `economy_log_channel` SettingSpec drives the write path. Same
  duality the PR #5 commit documented for `xp_announce_channel`.
- **Settings numeric presets + channel/role selectors** (plan PR #7)
  — **done** via PR #149. Added `SettingSpec.input_hint` +
  `SettingSpec.presets` fields and three new widget modules
  (`edit_channel.py`, `edit_role.py`, `edit_number_presets.py`).
  Opted in `xp_announce_channel`, `economy_log_channel`
  (`input_hint="channel"`), and `xp_cooldown`
  (`input_hint="numeric_presets"`, six presets).
- **Settings default-on with kill switch** (plan PR #8) — **done**
  via PR #150. `SETTINGS_MANAGER_COG_ENABLED.default_value` flipped
  to `True`; kill-switch path
  (`SUPERBOT_FF_SETTINGS__MANAGER_COG__ENABLED=off` env override or
  the future `!platform flags` command) unchanged.
- **Slash front door** `/help` (plan PR #9) — **done** via PR #151.
  `HelpCog.help_slash` reuses `resolve_route` + `open_route` +
  `HelpOpener.from_interaction` + `_attach_back_to_help_button`.
  Responses are ephemeral. Broader slash rollout (`/games`,
  `/economy`, `/community`, `/utility`, `/moderation`, `/admin`,
  `/platform`, `/settings`) follows in subsequent PRs and uses the
  same 30-line recipe.
- **Setup wizard** (`!setup`) — deferred until the S7 logging-route
  pipeline, S8 cleanup-policy pipeline, S10 preset packs, and the P5
  platform UI framework all land. See `docs/setup-platform/roadmap_setup_platform.md`.
