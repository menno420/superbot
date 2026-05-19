# Help / Command Surface Map

Source-of-truth inventory for every loaded cog/subsystem and how each is
reachable today through Help, hubs, and typed commands. Captured at HEAD
`7f85d9a` and updated alongside the Help routing PR.

The columns that matter most are **owner**, **panel**, **Help route**,
**hub route**, and **recommended placement**. Command lists are
representative, not exhaustive — large alias/legacy families are
summarized with a count.

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
| `admin` | `admin_cog.py` | `adminmenu`, `serverstats`, `cog`, `loadall`, `unloadall`, `restart`, `loglevel` | — | `_AdminPanelView` | `!help admin` → command-list | dropdown Admin → panel | hub child (top-level Admin) |
| `blackjack` | `blackjack_cog.py:95` | `blackjack`, `bj`, `bjtournament`, `bjstart`, `bjstatus` | — | `BlackjackPanelView` | `!help blackjack` → command-list | reached via Games | hub child (Games) |
| `chain` | `chain_cog.py` | `chain`, `chainmenu` | — | `ChainPanelView` | `!help chain` → command-list | reached via Games / Community | hub child |
| `channel` | `channel_cog.py:144` | `lock`, `unlock` | several `*_channel`-family commands | `ChannelPanelView` | `!help channel` → command-list | reached via Admin | hub child (Admin) |
| `cleanup` | `cleanup_cog.py:324` | `cleanuphistory`, `word`, `wordmenu`, `cleanup` | — | `CleanupHubView` | `!help cleanup` → command-list | reached via Moderation | hub child (Moderation) |
| `community` | `community_cog.py` | `community` | — | `CommunityHubView` | `!help community` → command-list | dropdown Community → panel | hub top-level |
| `counting` | `counting_cog.py` | `countingmenu`, `start_match`, `end_match`, `reset_count` | — | `CountingPanelView` | `!help counting` → command-list | reached via Games / Community | hub child |
| `deathmatch` | `deathmatch_cog.py` | `dm_challenge`, `deathmatch`, `dm`, `dm_help` | — | `DeathmatchPanelView` | `!help deathmatch` → command-list | reached via Games | hub child (Games) |
| `diagnostic` | `diagnostic_cog.py:70` | `diagnostics`, `diag`, `latency`, `platform` (group, 20+ subcommands) | — | `_DiagnosticsHubView` (generic hook); `_PlatformHubView` (new platform hook) | `!help diagnostic` → command-list (wrong: should open Platform Hub); `!help diagnostics`/`diag` → not currently routed to panel | Hub key `diagnostic` is "Platform / Diagnostics" → calls `build_help_menu_view` → **wrong view (Diagnostics, not Platform)** | hub top-level (Platform); `diagnostics`/`diag` open Diagnostics Hub |
| `economy` | `economy_cog.py` | `economymenu`, `daily`, `work`, `shop`, `balance`/`bal`/`wallet` | several admin/legacy commands | `EconomyPanelView` | `!help economy` → command-list (wrong: should open Economy hub) | dropdown Economy → panel | hub top-level |
| `games` | `games_cog.py` | `games` | — | `GamesHubView` | `!help games` → command-list (wrong: should open Games hub) | dropdown Games → panel | hub top-level (cleanest model) |
| `general` | `general_cog.py` | `fact`, `joke`, `quote`, `motivate`, `greet` | — | (small panel) | `!help general` → command-list | none today | hub child (Utility, future) |
| `help` | `help_cog.py` | `help` (alias `hilfe`) | — | **no panel hook (Help itself is the panel)** | n/a | dropdown root | Help Home |
| `inventory` | `inventory_cog.py:376` | `inventory`, `inv` | — | `InventoryPanelView` | `!help inventory` → command-list | top-level today | hub child (Economy, future) |
| `leaderboard` | `leaderboard_cog.py:200` | (none public-flagged; entry inferred from registry) | — | `LeaderboardPanelView` | `!help leaderboard` → command-list | top-level today | hub child (Economy / Community) |
| `logging` | `logging_cog.py:88` | `logging` | — | `LoggingPanelView` | `!help logging` → command-list | reached via Moderation / Admin | hub child |
| `mining` | `mining_cog.py:65` | `mineinv`/`mineinventory`, `minestats` | mining game flow commands (start/dig/etc.) | `MiningHubView` | `!help mining` → command-list | reached via Games / Economy cross-link | hub child (Games) |
| `moderation` | `moderation_cog.py` | `modmenu`, `warn`, `timeout`, `kick`, `ban`, `unban`, `clearwarnings`, `modlogs` | — | `ModPanelView` | `!help moderation` → command-list (wrong: should open Moderation hub) | dropdown Moderation → panel | hub top-level |
| `proof_channel` | `proof_channel_cog.py:113` | `prizestatus`, `prizemenu`, `timedprize` | — | `ProofPanelView` | `!help proof` → command-list | reached via Moderation | hub child (Moderation) |
| `role` | `role_cog.py:334` | `roles`, `rolesettings`, `rolemenu` (legacy alias) | 8+ legacy commands: `rolecreator`, `createrole`, `deleterole`, `setrole`, `unsetrole`, `assignroles`, `debugroles`, `refreshmembers`, plus react-role family | `RolePanelView` | `!help roles` → command-list | reached via Community | hub child (Community); legacy commands remain as hidden compatibility |
| `rps_tournament` | `rps_tournament_cog.py:118` | `rpsregister`/`rpsreg`, `rpsstart`/`rpsbegin`, `rpsbot`, `rpsmatchup`, `rpshelp`, `rpssettings` | — | `RpsPanelView` | `!help rps` → command-list | reached via Games | hub child (Games) |
| `settings` | `settings_cog.py` | (entry via `!settings`) | — | `SettingsHubView` | `!help settings` → command-list (wrong: should open Settings hub) | dropdown Settings → panel | hub top-level |
| `utility` | `utility_cog.py` | `utilitymenu`, `clear`/`purge`, `info`, `serverinfo`, `userinfo`, `avatar`, `remind` | — | `UtilityPanelView` | `!help utility` → command-list (wrong: should open Utility hub) | dropdown Utility → panel | hub top-level |
| `xp` | `xp_cog.py` | `xpmenu`, `rank`, `givexp`, `resetxp`, `xpconfig` | — | `XpPanelView` | `!help xp` → command-list | reached via Community | hub child (Community); admin controls live in panel |

## 3. Known inconsistencies (resolved by this PR)

1. **Typed Help and dropdown Help diverge.** `!help <category>` in
   `help_cog.py:609-674` iterates `SUBSYSTEMS` and renders
   `build_cog_embed` — it never consults `hub_registry`, never calls
   `build_help_menu_view`, and never attaches Back-to-Help. The dropdown
   (`HelpCategoryView._on_select`, lines 536-602) does all three. Same
   word, two different surfaces.
2. **Platform Help route mismatch.** The hub `diagnostic` is registered
   as "Platform / Diagnostics" with entry `!platform`
   (`hub_registry.py:184-191`), but `DiagnosticCog.build_help_menu_view`
   returns `_DiagnosticsHubView` (`diagnostic_cog.py:70-81`). The Help
   dropdown therefore opens the wrong hub when the user picks "Platform
   / Diagnostics". The fix is a sibling builder
   `build_platform_help_menu_view` returning `_PlatformHubView`, plus a
   per-hub override table in `help_cog.py`. The generic hook stays on
   Diagnostics so Admin → Diagnostics still works.
3. **Help Home rows are uneven.** `build_categories_overview_embed`
   shows an `Includes: ...` line for Games (populated
   `primary_children`) and nothing for Economy / Moderation / Community
   / Utility (empty `primary_children` per S7–S10 v1). The new copy
   removes `Includes:` entirely and uses uniform two-line rows.

## 4. Architectural notes

- **Games is the cleanest current model.** Hub view is registry-driven
  via `parent_hub`, has all six game children explicitly listed, and
  the hub UI is built from a single source.
- **S7–S10 Help promotions (Economy / Moderation / Community / Utility)
  are first-pass.** Their hubs route to existing panels via
  `build_help_menu_view`. Their `primary_children` are empty until
  follow-ups flip `parent_hub` metadata on the relevant subsystems.
- **Role public entry is `!roles`.** Legacy `rolemenu` and the
  rolemenu-style command family remain registered as hidden
  compatibility — they will not surface in Help.
- **Utility / Proof / Channel exposure gaps.** Several admin tools
  (channel lock/unlock, proof prize controls, cleanup history) are
  reachable only through hub panels — `!help <name>` resolves but the
  command-list embed undersells them. Hub panels are the canonical
  exposure point.
- **XP mixes user rank display with admin controls.** The XP panel
  surfaces both. Admin-only routing belongs in the panel, not in the
  command list. Marked for a future split if/when XP gets its own hub.
- **Advanced remains necessary but secondary.** Power-users who know a
  command name should not have to navigate hubs to find it.

## 5. Future routing surfaces (not in scope here)

The following are intentionally out of scope for the Help routing PR
and are listed only to make the eventual landing surface clearer:

- **Slash front door** (`/help`, `/games`, etc.) — needs `HelpRoute`
  shared with the slash registrar.
- **Setup wizard** (`!setup`) — first-run onboarding that walks an
  admin through binding the required channels/roles.
- **Hub v2 redesigns** — explicit `parent_hub` metadata on Inventory,
  Leaderboard, XP, Role, Cleanup, Logging, Proof, Channel, General.
- **Direct-write remediation** — view callbacks that mutate state
  directly today should route through mutation pipelines.
