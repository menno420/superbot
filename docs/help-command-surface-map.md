# Help / Command Surface Map

> **Status:** `binding` — Cog/command surface inventory; pinned to code by a doc-test.

Source-of-truth inventory for every loaded cog/subsystem and how each is
reachable today through Help, hubs, and typed commands. Originally captured at
HEAD `38353aa` (post-PR-#142, post-PR-#143); prose counts re-verified against
source 2026-06-09 at `7534e3e` (#641), then **pinned to the live registries by
`tests/unit/docs/test_help_surface_map_doc.py` (scoreboard Lane 8)** — a drifted
count now fails CI instead of rotting silently. The Help routing unification
landed in PR #142; this doc reflects the merged state, not the pre-PR
perspective.

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
- 43 of the 58 loaded extensions (`config.INITIAL_EXTENSIONS`) define
  `build_help_menu_view` — equivalently, 41 of the 42 subsystem-owning
  cogs expose it. The 14 extensions without the hook: the bootstrap
  access guard (not a Help surface), `help_cog` itself (it IS the Help
  surface), the five split BTD6 support cogs (`btd6_reference` /
  `btd6_events` / `btd6_strategy` / `paragon` / `btd6_ops` — their
  commands route under the one `btd6` subsystem via `btd6_cog`'s hook),
  `setup_cog` (an orchestrator with no `SUBSYSTEMS` row — the advanced
  `!setupadvanced` / `/setup-advanced` wizard + on-join launcher + `/setup-*`
  helpers),
  `quicksetup_cog` (the Essential Setup front door — the primary `!setup` /
  `/setup` — no subsystem row),
  `hermes_cog` (the Hermes→Claude dispatch bridge — admin-only slash
  commands, no subsystem row), `media_maintenance_cog` (the YouTube
  cache-retention task owner — no commands, no subsystem row),
  `health_maintenance_cog` (the health-findings retention task owner —
  no commands, no subsystem row), `role_grants_cog` (free temp-role
  grants — a sweep task-loop plus `!temprole`, no subsystem row), and
  `starboard_cog`
  (the Starboard / Hall-of-Fame raw-reaction listener plus the `!starboard`
  config command — no subsystem row of its own). "Loaded
  extension", "subsystem", and "Help category" are different concepts —
  do not conflate them (help audit §4). **Per-command reachability of these
  no-row cogs is guarded** by `scripts/check_command_reachability.py` +
  `tests/unit/invariants/test_command_reachability.py` (discoverability audit
  Session 1, 2026-06-23): every member-tier command must resolve to a homed
  help-list **or** a panel button/text, else it is a recorded gap — the per-cog
  gap ledger is [`docs/audits/command-reachability-gaps-2026-06-23.md`](audits/command-reachability-gaps-2026-06-23.md).
- After the help-menu regrouping (PR #1290) `diagnostic` is a child of the
  Server & Admin hub, not a top-level hub. `HUB_PANEL_BUILDERS` is now empty
  (the legacy Platform override was dropped). Typed `platform` opens the
  Server & Admin hub; `diagnostics`/`diag`/`diagnostic` resolve to the
  Diagnostics subsystem panel. The Platform view is reached via the Server &
  Admin panel's Platform button.
- **Batch 6 (HLP-2, PR #657) — one effective-access seam.** Every Help
  render path (Home hub index · typed/dropdown routes · command embeds ·
  dedicated-panel dispatch) consumes
  `services/help_projection.HelpProjection`. Consequences for every row
  below: Home hides a hub whose host subsystem is governance-hidden in
  scope (no longer tier-only); a typed/selected target the projection
  hides renders the same not-found fallback as a nonexistent name; the
  single-command route applies the same hidden/disabled/classification
  filter as the command-list embed. Routing/command-access locks do
  **not** hide — Help advertises locked features (the
  `help_advertises_locked` diagnostic is the operator warning surface).

## 1. Mother hubs

8 hubs in `disbot/utils/hub_registry.py`. Every hub key matches a
`SUBSYSTEMS` key so Help can resolve a hub entry to its host cog. The
help-menu regrouping (PR #1290) consolidated the four former child-less
admin hubs (Admin, Settings, Diagnostics/Platform, Server Management) into
one **Server & Admin** (`admin`) section — `settings` / `diagnostic` /
`server_management` are now `admin` children (reached from the Server &
Admin panel), not top-level hubs — so the admin-side index dropped 10 → 7.
The eight former orphan subsystems were homed at the same time (see § 2),
so every feature is reachable in ≤ 3 clicks with no paginated-Advanced detour.

| key | display | entry | host cog | panel | min tier |
| --- | --- | --- | --- | --- | --- |
| `games` | 🎮 Games | `!games` | `games_cog` | `GamesHubView` (`views/games/hub.py`) | user |
| `btd6` | 🐵 BTD6 Assistant | `!btd6` | `btd6_cog` | `BTD6PanelView` | user |
| `economy` | 💰 Economy | `!economymenu` | `economy_cog` | `EconomyPanelView` | user |
| `moderation` | 🛡️ Moderation & Safety | `!modmenu` | `moderation_cog` | `ModPanelView` | moderator |
| `community` | 🌱 Community | `!community` | `community_cog` | `CommunityHubView` | user |
| `utility` | 🧰 Utility | `!utilitymenu` | `utility_cog` | `_UtilityPanelView` (hybrid: own actions + child buttons → general · four_twenty, since PR #1370) | user |
| `admin` | ⚙️ Server & Admin | `!adminmenu` | `admin_cog` | `_AdminPanelView` (children: settings · diagnostic · server_management · channel · ai · ux_lab) | administrator |

## 2. Subsystem inventory

43 registered subsystems in `utils/subsystem_registry.py` (one row
each below); 58 loaded extensions in `config.INITIAL_EXTENSIONS` (the
extension↔subsystem mapping is many-to-one — see the routing summary
above for the 15 extensions without a hook). Every subsystem's host cog
defines `build_help_menu_view` except `help` itself, so the Help route
resolver opens a real panel for every subsystem except `help`, and only
falls back to the command-list embed when the hook is missing or raises.

| subsystem | owner | public commands (sample) | hidden / legacy | panel hook | Help route today | Hub route today | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `admin` | `admin_cog.py` | `adminmenu`, `serverstats`, `cog`, `loadall`, `unloadall`, `restart`, `loglevel` | — | `_AdminPanelView` | `!help admin` → opens Admin panel (shared resolver) | dropdown Admin → panel | hub top-level (Admin) |
| `ai` | `ai_cog.py` | `ai`, `aimenu`, `ai status`, `ai diagnostics`, `ai providers`, `ai routing`, `ai settings` | — | `AIPanelView` | `!help ai` → opens AI Platform panel (shared resolver) | reached via Admin / Diagnostics | central AI policy host (M1+); auto-dispatched settings via `ai settings` and `!settings` hub |
| `automod` | `automod_cog.py` | `automod` | — | `HubView` | `!help automod` → automod policy summary (shared resolver) | reached via Moderation; `parent_hub="moderation"` (Q-0108) | hub child (Moderation) — declared; config via `!settings` → Automod |
| `image_moderation` | `image_moderation_cog.py` | `imagemod` | — | `HubView` | `!help image_moderation` → image-mod policy summary (shared resolver) | reached via Moderation; `parent_hub="moderation"` (Q-0108) | hub child (Moderation) — declared; config via `!settings` → Image moderation |
| `btd6` | `btd6_cog.py` | `btd6`, `btd6menu`, `btd6 ask`, `btd6 tower`, `btd6 hero`, `btd6 round`, `btd6 relic`, `btd6 ct`, `btd6 leaderboard`, `btd6 live`, `btd6 event`, `btd6 status`, `btd6 diagnostics`, `btd6 test-intent` | — | `BTD6PanelView` | `!help btd6` → opens BTD6 panel (shared resolver) | dropdown BTD6 → panel | hub top-level (BTD6 Assistant) |
| `blackjack` | `blackjack_cog.py:95` | `blackjack`, `bj`, `bjtournament`, `bjstart`, `bjstatus` | — | `BlackjackPanelView` | `!help blackjack` → opens Blackjack panel (shared resolver) | reached via Games | hub child (Games) |
| `casino` | `casino_cog.py` | `casino`, `poker`, `holdem` | — | `CasinoHubView` | `!help casino` → opens Casino hub (shared resolver) | reached via Games | hub child (Games) |
| `chain` | `chain_cog.py` | `chain`, `chainmenu` | — | `_ChainMenuView` | `!help chain` → opens Chain panel (shared resolver) | reached via Games / Community | hub child |
| `channel` | `channel_cog.py:144` | `lock`, `unlock` | several `*_channel`-family commands | `_ChannelManagerView` | `!help channel` → opens Channel panel (shared resolver) | reached via Admin | hub child (Admin) |
| `cleanup` | `cleanup_cog.py:324` | `cleanuphistory`, `word`, `wordmenu`, `cleanup` | — | `CleanupPanelView` | `!help cleanup` → opens Cleanup panel (shared resolver) | reached via Moderation; `parent_hub="moderation"` since PR #3 | hub child (Moderation) — declared |
| `community` | `community_cog.py` | `community` | — | `CommunityHubView` | `!help community` → opens Community panel (shared resolver) | dropdown Community → panel | hub top-level |
| `community_spotlight` | `community_spotlight_cog.py` | `spotlight` (alias `activity`) | — | `SpotlightView` | `!help` → Community → Spotlight (shared resolver) | reached via Community; `parent_hub="community"` since the Q-0025 scaffold lane | hub child (Community) — read-only live dashboard |
| `counters` | `counters_cog.py` (+ `cogs/counters/`) | `counters` | — | `HubView` | `!help counters` → counter policy summary (shared resolver) | hub-less; surfaced via `!settings` → Counters + the `!counters` summary (administrator tier) | live member-count channels (Q-0110); config via `!settings` → Counters; slow rename loop (rate-limit-safe) |
| `counting` | `counting_cog.py` | `countingmenu`, `start_match`, `end_match`, `reset_count` | — | `_CountingHubView` | `!help counting` → opens Counting panel (shared resolver) | reached via Games / Community | hub child |
| `deathmatch` | `deathmatch_cog.py` | `dm_challenge`, `deathmatch`, `dm`, `dm_help` | — | `DeathmatchPanelView` | `!help deathmatch` → opens Deathmatch panel (shared resolver) | reached via Games | hub child (Games) |
| `diagnostic` | `diagnostic_cog.py:70` | `diagnostics`, `diag`, `latency`, `platform` (group, 20+ subcommands) | — | `_DiagnosticsHubView` (generic hook); `_PlatformHubView` (platform builder) | `!help platform` / `!help diagnostic` → opens Platform Hub via the `HUB_PANEL_BUILDERS["diagnostic"]` override; `!help diagnostics` / `!help diag` → opens Diagnostics subsystem via the subsystem-alias branch (not the Platform hub) | hub top-level "Platform / Diagnostics" via the override; sibling subsystem aliases reach Diagnostics | hub top-level (Platform); `diagnostics`/`diag` open Diagnostics Hub |
| `economy` | `economy_cog.py` | `economymenu`, `daily`, `work`, `shop`, `balance`/`bal`/`wallet` | several admin/legacy commands | `EconomyPanelView` | `!help economy` → opens Economy panel (shared resolver) | dropdown Economy → panel | hub top-level |
| `games` | `games_cog.py` | `games` | — | `GamesHubView` | `!help games` → opens Games hub (shared resolver) | dropdown Games → panel | hub top-level (cleanest model) |
| `general` | `general_cog.py` | `fact`, `joke`, `quote`, `motivate`, `greet` | — | `_GeneralPanelView` | `!help general` → opens General panel (shared resolver) | reached via Utility (`parent_hub="utility"` since PR #3) | hub child (Utility) — declared |
| `four_twenty` | `four_twenty_cog.py` | `420`, `fourtwenty` | — | `_FourTwentyPanelView` | `!help 420` → opens 420 panel (shared resolver) | reached via Utility (`parent_hub="utility"` since PR #420) | hub child (Utility) — declared; passive `FourTwentyStage` 🍃-reacts to `420` mentions |
| `help` | `help_cog.py` | `help` (alias `hilfe`) | — | **no panel hook (Help itself is the panel)** | n/a (Help Home embeds + `HelpCategoryView` dropdown) | dropdown root | Help Home |
| `inventory` | `inventory_cog.py:376` | `inventory`, `inv` | — | `UnifiedInventoryView` | `!help inventory` → opens Inventory panel (shared resolver) | reached via Economy (Inventory btn → in-place edit + Back-to-Economy; PR #143). `parent_hub="economy"` since PR #3. | hub child (Economy) — declared |
| `treasury` | `treasury_cog.py` | `treasury`/`bank`/`pool` (+ `contribute`, `grant` subcommands) | — | `TreasuryCog` | `!help treasury` → actionable Treasury panel (Help hook → `TreasuryView`: Contribute · Refresh) | Economy-hub child (`parent_hub="economy"`, user tier); reachable via the 🏛️ **Treasury button on the Economy panel** (`economy:treasury`, since the panel-link fix), `!treasury`, and `!help treasury` | the bot's first **server-owned** coin pool (the economy↔governance seam) — members contribute their own coins (a sink); managers disburse with `!treasury grant @member <amount>` (a `manage_guild` gate) |
| `leaderboard` | `leaderboard_cog.py:200` | (none public-flagged; entry inferred from registry) | — | `LeaderboardView` | `!help leaderboard` → opens Leaderboard panel (shared resolver) | `parent_hub="economy"` since PR #3; Community cross-link migrates in PR #4 | hub child (Economy) — declared; Community cross-link in PR #4 |
| `logging` | `logging_cog.py:88` | `logging` | — | `LoggingPanelView` | `!help logging` → opens Logging panel (shared resolver) | reached via Moderation / Admin; `parent_hub="moderation"` since PR #3 | hub child (Moderation) — declared |
| `mining` | `mining_cog.py:65` | `mineinv`/`mineinventory`, `minestats` | mining game flow commands (start/dig/etc.) | `MiningHubView` | `!help mining` → opens Mining panel (shared resolver) | reached via Games (primary, `parent_hub="games"`); Economy hub declares Mining as a `cross_link_children` since PR #3 | hub child (Games); Economy cross-link |
| `fishing` | `fishing_cog.py` | `fish`, `fishlog`/`fishdex`, `fishtop`/`topfishers` | — | `FishingCog` | `!help fishing` → static fishing overview (Help hook; no persistent panel yet) | hub-less; surfaced via the typed `!fish`/`!fishlog`/`!fishtop` commands (user tier) | hub-less for PR 1 (like `welcome`/`counters`); an actionable Games/Explore-hub panel is a later plan slice |
| `creature` | `creature_cog.py` (+ `creature_battle_cog.py`) | `creatures`/`creaturemenu`/`pets`, `catch`/`hunt`, `dex`/`collection`, `dextop`/`topcatchers` | — | `CreatureMenuView` (both cogs' Help hooks) | `!help creature` → interactive `CreatureMenuView` panel (Help hook) | Games-hub child → the `CreatureMenuView` panel (catch · dex browser · challenge · ladder · how-to) | catch+collection + level-normalized PvP (`creature_battle_cog`: `!cbattle`/`!cbattletop`/`!cbrecord`); the interactive game panel + dex browser shipped 2026-06-29 (#1546, completion cert #1/#2) |
| `farm` | `farm_cog.py` | `farm`/`chickenfarm`/`coop` | — | `FarmCog` | `!help farm` → actionable Farm panel (Help hook → `FarmMenuView`: Collect · Shop · Refresh) | Games-hub child (`activities`, user tier); also reachable via `!farm` and the Explore world hub | the bot's first **idle** game — hens lay eggs over time (pure `settle()` accrual), collected for coins + game XP; coins buy hens / coop upgrades |
| `project_moon` | `project_moon_cog.py` | `pm`/`limbus`/`projectmoon` (+ `pm sinner`/`sin`/`status`/`ego`/`damage`/`lookup`/`list` subcommands) | — | `LimbusBrowseView` | `!help project_moon` → Limbus browse panel (Help hook → `LimbusBrowseView`: one button per category) | its own **top-level Project Moon hub** (like BTD6 — a knowledge domain, not a Games activity); also reachable via `!pm` and `/pm` | read-only Limbus knowledge (Q-0192 Project Moon program, PR 1) — structural/lore facts; AI grounding path is a later PR |
| `moderation` | `moderation_cog.py` | `modmenu`, `warn`, `timeout`, `kick`, `ban`, `unban`, `clearwarnings`, `modlogs` | — | `ModPanelView` | `!help moderation` → opens Moderation panel (shared resolver) | dropdown Moderation → panel | hub top-level |
| `proof_channel` | `proof_channel_cog.py:113` | `prizestatus`, `prizemenu`, `timedprize` | — | `_PrizeManagerView` | `!help proof` → opens Proof Channel panel (shared resolver) | reached via Moderation; `parent_hub="moderation"` since PR #3 | hub child (Moderation) — declared |
| `role` | `role_cog.py:334` | `roles`, `rolesettings`, `rolemenu` (legacy alias) | 8+ legacy commands: `rolecreator`, `createrole`, `deleterole`, `setrole`, `unsetrole`, `assignroles`, `debugroles`, `refreshmembers`, plus react-role family | `RoleHubPanelView` | `!help roles` → opens Role panel (shared resolver) | reached via Community; `parent_hub="community"` since PR #3 | hub child (Community) — declared; legacy commands remain as hidden compatibility |
| `rps_tournament` | `rps_tournament_cog.py:118` | `rpsregister`/`rpsreg`, `rpsstart`/`rpsbegin`, `rpsbot`, `rpsmatchup`, `rpshelp`, `rpssettings` | — | `RPSPanelView` | `!help rps` → opens RPS panel (shared resolver) | reached via Games | hub child (Games) |
| `security` | `security_cog.py` (+ `cogs/security/`) | `security` | — | `HubView` | `!help security` → security policy summary (shared resolver) | hub-less; surfaced via `!settings` → Security + the `!security` summary (administrator tier) | raid detection + account-age filter on join (Q-0111 tiers 1+2); config via `!settings` → Security; actions route through moderation_service |
| `server_management` | `server_management_cog.py` | `servermanagement`, `servermenu`, `guildmenu`, `/server-management` | — | `ServerManagementHubView` | `!help` → Server Management (shared resolver) | dropdown Server Management → panel | hub top-level (operator) — composes moderation/channels/roles/cleanup/setup |
| `settings` | `settings_cog.py` | (entry via `!settings`) | — | `SettingsHubView` | `!help settings` → opens Settings panel (shared resolver) | dropdown Settings → panel | hub top-level |
| `utility` | `utility_cog.py` | `utilitymenu`, `clear`/`purge`, `info`, `serverinfo`, `userinfo`, `avatar`, `remind` | — | `_UtilityPanelView` | `!help utility` → opens Utility panel (shared resolver) | dropdown Utility → panel | hub top-level |
| `ux_lab` | `ux_lab_cog.py` | `uxlab` (alias `interfacelab`), `/uxlab` | — | `UxLabHomeView` (wings in `views/ux_lab/`) | `!help` → UX Lab (shared resolver; administrator tier) | admin-tier top-level (design workbench, no parent hub) | zero-write interface gallery (UX Lab plan 2026-06-12) |
| `welcome` | `welcome_cog.py` | `welcome` | — | `HubView` | `!help welcome` → welcome policy summary (shared resolver) | hub-less; surfaced via `!settings` → Welcome + the `!welcome` summary (administrator tier) | member greetings/farewell + optional entry role (Q-0110); config via `!settings` → Welcome |
| `xp` | `xp_cog.py` | `xpmenu`, `rank`, `givexp`, `resetxp`, `xpconfig`, `xpimport` | — | `_XpHubView` | `!help xp` → opens XP panel (shared resolver) | reached via Community; `parent_hub="community"` since PR #3 | hub child (Community) — declared; admin controls live in panel |
| `karma` | `karma_cog.py` | `thanks` (aliases `rep`/`thank`), `karma`, `karma give`, `/karma` | — | `HubView` (karma card) | `!help karma` → karma card (shared resolver) | reached via Community; `parent_hub="community"` (2026-06-22) | hub child (Community) — peer reputation; audited `karma_service` seam + `karma` leaderboard category |
| `ticket` | `ticket_cog.py` | `ticket` (group: `new`/`close`/`claim`/`add`/`remove`), `ticketpanel`, `ticketsetup`, `ticketlimit`, `ticketblacklist` | — | `TicketHubView` | `!help ticket` → opens the ticket hub (shared resolver) | reached via Community; `parent_hub="community"` (user tier); also via the public launcher panel + the AI `open_support_ticket` tool | hub child (Community) — private support tickets, open by command, panel button, or natural language; audited `ticket_mutation` seam; claim/close/transcript |

## 3. Known inconsistencies (resolved by PR #142 / PR #143)

> **RESOLVED 2026-06-09 (Q-0044 + Q-0025):** Community Spotlight is registered as a
> `community`-hub child via the `scripts/new_subsystem.py` scaffold lane — see its
> §2 row. The greedy `!hub`/`!server` aliases were dropped the same day; `!spotlight`
> (alias `!activity`) remains, plus the `build_help_menu_view` direct-navigation hook.

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
- **No "All Commands / Advanced" browser (removed PR #1294).** Once every
  subsystem was homed under a hub (PR #1290), the paginated Advanced browser
  only re-listed the hub hosts — redundant with the category index — so it
  was removed. Power-users who know a command name still bypass the hubs via
  the typed `!help <name>` route, which resolves straight to the panel.
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
  _(Both scalars were later **retired in P0-3 arc PR 2 / #794**, which also
  taught `BindingMutationPipeline` to accept `actor_type='system'` — the
  listener-actor gap noted here is closed, and the writes now land in
  `binding_audit_log`.)_
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
