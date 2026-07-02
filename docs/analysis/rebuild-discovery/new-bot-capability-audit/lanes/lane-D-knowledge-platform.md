# Lane D — Knowledge, AI & Platform (Axis 1)

> **Status:** `reference` — this lane's workspace. The surface-unit inventories below are **pre-extracted** (facts only, tier columns blank). The Lane D agent **verifies + completes them against source**, fills BOTH tier columns, writes each subsystem's §2 manifest sketch, dispositions tier-3s, and adds reconsider/optimize recommendations — per [`../BRIEF.md`](../BRIEF.md). Treat the inventory as a starting scaffold, not ground truth.

**Subsystems:** ai, btd6, project_moon, help, settings, logging, diagnostic, ux_lab, utility, general, proof_channel

**Method:** [`../BRIEF.md`](../BRIEF.md) · [`../PARTITION.md`](../PARTITION.md) · `tools/grammar_spike/` · `../ground-truth/command-surface.json`.

---

### ai
_cogs: disbot/cogs/ai_cog.py, disbot/cogs/ai_review_cog.py_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !ai | command (group) | cogs/ai_cog.py:365 | | | |
| !ai status | command | cogs/ai_cog.py:371 | | | |
| !ai readiness | command | cogs/ai_cog.py:379 | | | |
| !ai settings | command | cogs/ai_cog.py:409 | | | |
| !ai why-no-response | command | cogs/ai_cog.py:417 | | | |
| !ai policy | command | cogs/ai_cog.py:460 | | | |
| !ai diagnostics | command | cogs/ai_cog.py:498 | | | |
| !ai providers | command | cogs/ai_cog.py:503 | | | |
| !ai routing | command | cogs/ai_cog.py:508 | | | |
| !ai forget | command | cogs/ai_cog.py:523 | | | |
| !ai support-report | command | cogs/ai_cog.py:551 | | | |
| !aimenu | command (prefix) | cogs/ai_cog.py:519 | | | |
| /ai status | command (slash) | cogs/ai_cog.py:581 | | | |
| /ai readiness | command (slash) | cogs/ai_cog.py:589 | | | |
| /ai diagnostics | command (slash) | cogs/ai_cog.py:623 | | | |
| /ai providers | command (slash) | cogs/ai_cog.py:634 | | | |
| /ai routing | command (slash) | cogs/ai_cog.py:645 | | | |
| /ai forget | command (slash) | cogs/ai_cog.py:660 | | | |
| /ai support-report | command (slash) | cogs/ai_cog.py:689 | | | |
| /ai policy | command (slash) | cogs/ai_cog.py:713 | | | |
| /ai settings | command (slash) | cogs/ai_cog.py:755 | | | |
| /aimenu | command (slash) | cogs/ai_cog.py:777 | | | |
| !aireview | command (group) | cogs/ai_review_cog.py:172 | | | |
| !aireview channel | command | cogs/ai_review_cog.py:200 | | | |
| !aireview off | command | cogs/ai_review_cog.py:223 | | | |
| !aireview list | command | cogs/ai_review_cog.py:237 | | | |
| !aireview export | command | cogs/ai_review_cog.py:275 | | | |
| !aireview resolve | command | cogs/ai_review_cog.py:332 | | | |
| !aireview preset | command (group) | cogs/ai_review_cog.py:351 | | | |
| !aireview preset add | command | cogs/ai_review_cog.py:365 | | | |
| !aireview preset from | command | cogs/ai_review_cog.py:381 | | | |
| !aireview preset list | command | cogs/ai_review_cog.py:444 | | | |
| !aireview preset remove | command | cogs/ai_review_cog.py:480 | | | |
| AI settings panel view | panel/view | cogs/ai_cog.py:151-154 | | | `_build_ai_settings_panel` returns embed+View (⚠ view class unverified, not read in full) |
| AI help menu embed/view | panel/view | cogs/ai_cog.py:788-791 | | | `build_help_menu_view` returns embed+View for aimenu |
| on_raw_reaction_add (ai review) | listener | cogs/ai_review_cog.py:119 | | | reaction-based review triage listener |
| bus.on EVT_AI_REVIEW_LOGGED | listener (EventBus) | cogs/ai_review_cog.py:109 | | | subscribes `_review_sub` in cog_load, unsubscribed line 112 |
| _on_review_logged | listener (internal handler) | cogs/ai_review_cog.py:151 | | | handles the EVT_AI_REVIEW_LOGGED payload |
| ai_policy_mutation bus.emit | event | services/ai_policy_mutation.py:382 | | | emits policy-change event with guild_id/mutation_id |
| ai_policy_mutation bus.emit (2) | event | services/ai_policy_mutation.py:544 | | | second emit site in same service |
| ai_review_log_service bus.emit | event | services/ai_review_log_service.py:297 | | | emits review-logged event consumed by ai_review_cog |
| setting: AI_ENABLED | setting | utils/settings_keys/ai.py:10 | | | `ai_enabled` guild toggle |
| setting: AI_NATURAL_LANGUAGE_ENABLED | setting | utils/settings_keys/ai.py:11 | | | `ai_natural_language_enabled` toggle |
| setting: AI_DEFAULT_PROVIDER | setting | utils/settings_keys/ai.py:12 | | | `ai_default_provider` key |
| setting: AI_DEFAULT_MODEL | setting | utils/settings_keys/ai.py:13 | | | `ai_default_model` key |
| setting: AI_MINIMUM_LEVEL_DEFAULT | setting | utils/settings_keys/ai.py:14 | | | `ai_minimum_level_default` key |
| setting: AI_COOLDOWN_SECONDS | setting | utils/settings_keys/ai.py:15 | | | `ai_cooldown_seconds` key |
| setting: AI_FRESH_USER_MENTION_ALLOWANCE | setting | utils/settings_keys/ai.py:16 | | | `ai_fresh_user_mention_allowance` key |
| setting: AI_GUILD_INSTRUCTION_PROFILE | setting | utils/settings_keys/ai.py:17 | | | `ai_guild_instruction_profile` key |
| setting: AI_MEMORY_WINDOW_MINUTES | setting | utils/settings_keys/ai.py:24 | | | `ai_memory_window_minutes` key |
| setting: AI_MEMORY_CHANNEL_SCAN_ENABLED | setting | utils/settings_keys/ai.py:30 | | | `ai_memory_channel_scan_enabled` key |
| setting: AI_REVIEW_CHANNEL | setting | utils/settings_keys/ai.py:35 | | | `ai_review_channel` key |
| store: ai_review_log | store | utils/db/ai_review.py:1 | | | table for logged AI answers, migration 100 |
| store: ai_answer_presets | store | utils/db/ai_presets.py:26 | | | table for guild-curated preset answers |
| SUBSYSTEMS["ai"] registry entry | registry/entry_points | utils/subsystem_registry.py:1122 | | | entry_points `ai`, `aimenu`; capabilities `ai.platform.view`, `ai.diagnostics.view`, `ai.provider.view`, `ai.routing.view`, plus M1 settings-UI capability (list truncated at read, ⚠ unverified full capability list) |
| help catalogue entry | help | services/help_catalogue.py | | | ⚠ unverified — no direct "ai"/ai_cog reference found via grep; may be covered generically |

**Unit kinds present:** command, panel, setting, listener, event, store, registry/entry_points, help (unverified)
**Structural-pattern flags:** gateway (@commands.Cog.listener `on_raw_reaction_add`) listener + EventBus `bus.on`/`bus.emit` pub-sub (EVT_AI_REVIEW_LOGGED, ai_policy_mutation events); none of stateful game loop / wait_for wizard / scheduled loop / voice observed in these two cog files.


---

### btd6
_cogs: disbot/cogs/btd6_cog.py, disbot/cogs/btd6_events_cog.py, disbot/cogs/btd6_ops_cog.py, disbot/cogs/btd6_reference_cog.py, disbot/cogs/btd6_strategy_cog.py_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !btd6menu | command | disbot/cogs/btd6_cog.py:171 | | | |
| /btd6menu | command | disbot/cogs/btd6_cog.py:182 | | | |
| !btd6events (group) | command | disbot/cogs/btd6_events_cog.py:38 | | | |
| !btd6events live | command | disbot/cogs/btd6_events_cog.py:48 | | | |
| !btd6events event | command | disbot/cogs/btd6_events_cog.py:58 | | | |
| !btd6events leaderboard | command | disbot/cogs/btd6_events_cog.py:72 | | | |
| !btd6events sources | command | disbot/cogs/btd6_events_cog.py:85 | | | |
| !btd6events source-health | command | disbot/cogs/btd6_events_cog.py:90 | | | |
| !btd6events latest-data | command | disbot/cogs/btd6_events_cog.py:99 | | | |
| !btd6events refresh-source | command | disbot/cogs/btd6_events_cog.py:104 | | | |
| !btd6events grounding | command | disbot/cogs/btd6_events_cog.py:123 | | | |
| !btd6ops (group) | command | disbot/cogs/btd6_ops_cog.py:41 | | | |
| !btd6ops readiness | command | disbot/cogs/btd6_ops_cog.py:52 | | | |
| !btd6ops runs | command | disbot/cogs/btd6_ops_cog.py:59 | | | |
| !btd6ops source_enable | command | disbot/cogs/btd6_ops_cog.py:71 | | | |
| !btd6ops source_disable | command | disbot/cogs/btd6_ops_cog.py:84 | | | |
| !btd6ops seed-data | command | disbot/cogs/btd6_ops_cog.py:97 | | | |
| !btd6ops announcechannel | command | disbot/cogs/btd6_ops_cog.py:105 | | | |
| !btd6ref (group) | command | disbot/cogs/btd6_reference_cog.py:37 | | | |
| !btd6ref tower | command | disbot/cogs/btd6_reference_cog.py:47 | | | |
| !btd6ref hero | command | disbot/cogs/btd6_reference_cog.py:51 | | | |
| !btd6ref round | command | disbot/cogs/btd6_reference_cog.py:55 | | | |
| !btd6ref income | command | disbot/cogs/btd6_reference_cog.py:65 | | | |
| !btd6ref rbe | command | disbot/cogs/btd6_reference_cog.py:75 | | | |
| !btd6ref relic | command | disbot/cogs/btd6_reference_cog.py:85 | | | |
| !btd6ref ct | command | disbot/cogs/btd6_reference_cog.py:90 | | | |
| !btd6strat (group) | command | disbot/cogs/btd6_strategy_cog.py:39 | | | |
| !btd6strat browse | command | disbot/cogs/btd6_strategy_cog.py:49 | | | |
| !btd6strat mine | command | disbot/cogs/btd6_strategy_cog.py:58 | | | |
| !btd6strat strategy | command | disbot/cogs/btd6_strategy_cog.py:73 | | | |
| !btd6strat strategy-audit | command | disbot/cogs/btd6_strategy_cog.py:90 | | | |
| !btd6strat submit | command | disbot/cogs/btd6_strategy_cog.py:99 | | | |
| !btd6strat pending | command | disbot/cogs/btd6_strategy_cog.py:111 | | | |
| !btd6strat strategies | command | disbot/cogs/btd6_strategy_cog.py:135 | | | |
| !btd6strat why-no-response | command | disbot/cogs/btd6_strategy_cog.py:144 | | | |
| BTD6PanelView | panel/view | disbot/views/btd6/panel.py:159 | | | |
| BTD6AdminView | panel/view | disbot/views/btd6/admin_panel.py:86 | | | |
| BTD6CategoryView | panel/view | disbot/views/btd6/hub_panels.py:291 | | | |
| CTGroupConfirmView | panel/view | disbot/views/btd6/ct_group_flow.py:109 | | | |
| CTGroupEntryView | panel/view | disbot/views/btd6/ct_group_flow.py:218 | | | |
| HeroBrowserView / HeroDetailView | panel/view | disbot/views/btd6/hero_browser_view.py:196,213 | | | |
| HeroStatsView | panel/view | disbot/views/btd6/hero_stats_view.py:55 | | | |
| LeaderboardBrowserView/KindListView/DetailView | panel/view | disbot/views/btd6/leaderboard_browser_view.py:200,208,226 | | | |
| LiveOverviewView/LiveEventsBrowserView/EventDetailView | panel/view | disbot/views/btd6/live_events_view.py:327,448,486 | | | |
| ParagonStatsView | panel/view | disbot/views/btd6/paragon_stats_view.py:145 | | | |
| ParagonCalculatorView/ParagonRequirementsView | panel/view | disbot/views/btd6/paragon_view.py:493,594 | | | |
| StrategyReviewView | panel/view | disbot/views/btd6/strategy_review.py:133 (extends discord.ui.View directly, ⚠ unverified why) | | | |
| TowerBrowserView/TowerDetailView | panel/view | disbot/views/btd6/tower_browser_view.py:264,305 | | | |
| TowerEventsView | panel/view | disbot/views/btd6/tower_events_view.py:43 | | | |
| TowerStatsView | panel/view | disbot/views/btd6/tower_stats_view.py:98 | | | |
| BTD6_STRATEGY_SUBMISSION_CHANNEL | setting | disbot/utils/settings_keys/btd6.py:31 | | | |
| BTD6_CT_GROUP_ID | setting | disbot/utils/settings_keys/btd6.py:33 | | | |
| BTD6_VERSION_ANNOUNCEMENT_CHANNEL | setting | disbot/utils/settings_keys/btd6.py:35 | | | |
| btd6 SUBSYSTEMS capabilities (query.ask, strategy.view, diagnostics.view, settings.configure) | setting | disbot/utils/subsystem_registry.py:801-805 | | | |
| BTD6EventsCog / BTD6OpsCog / BTD6ReferenceCog / BTD6StrategyCog / BTD6Cog classes | listener (Cog registration) | disbot/cogs/btd6_cog.py:64; btd6_events_cog.py:26; btd6_ops_cog.py:31; btd6_reference_cog.py:24; btd6_strategy_cog.py:27 | | | |
| BTD6Cog.cog_load auto-seed check | listener/lifecycle | disbot/cogs/btd6_cog.py:70,112,115 | | | |
| btd6.version_detected subscriber (_on_version_detected) | listener | disbot/services/btd6_version_announce.py:111 | | | |
| btd6.version_detected emit | event | disbot/services/btd6_patch_service.py:150-151 | | | |
| btd6_data.py table(s) — game data blobs store | store | disbot/utils/db/btd6_data.py:1 (⚠ unverified exact CREATE TABLE — no CREATE TABLE found in file, likely migration-owned) | | | |
| btd6_sources.py table(s) — source registry/health store | store | disbot/utils/db/btd6_sources.py:1 (⚠ unverified) | | | |
| btd6_strategies.py table(s) — strategy submissions store | store | disbot/utils/db/btd6_strategies.py:1 (⚠ unverified) | | | |
| help entries for btd6 commands | help | docs/help-command-surface-map.md (⚠ unverified line-level; grep hit, not confirmed per-command) | | | |

**Unit kinds present:** command, panel, setting, listener, event, store, help

**Structural-pattern flags:** gateway/EventBus listener (`bus.on(EVT_BTD6_VERSION_DETECTED, ...)` in disbot/services/btd6_version_announce.py:111) driving a version-announcement event chain; cog_load-time auto-seed lifecycle check (disbot/cogs/btd6_cog.py:70-115) rather than a scheduled `@tasks.loop`; heavy multi-step browser/hub panel views (Hero/Tower/Leaderboard/Live-events/Paragon browsers) implying wizard-like paginated navigation, though no explicit `wait_for` was found in the grepped cogs. No `@bot.event` or `@tasks.loop` found directly in the btd6 cog files (⚠ unverified exhaustive — only cogs/services named `btd6*` were grepped, not the full `disbot/cogs/btd6/` package internals).

---

### project_moon
_cogs: disbot/cogs/project_moon_cog.py_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !pm | command (group) | disbot/cogs/project_moon_cog.py:74 | | | |
| /pm | command (slash) | disbot/cogs/project_moon_cog.py:175 | | | |
| !pm lookup (aliases: search, what) | command (subcommand) | disbot/cogs/project_moon_cog.py:84 | | | |
| !pm list | command (subcommand) | disbot/cogs/project_moon_cog.py:100 | | | |
| !pm origins (aliases: origin, literary) | command (subcommand) | disbot/cogs/project_moon_cog.py:139 | | | |
| !pm sinner (aliases: sinners) | command (subcommand) | disbot/cogs/project_moon_cog.py:144 | | | |
| !pm sin (aliases: sins, affinity) | command (subcommand) | disbot/cogs/project_moon_cog.py:149 | | | |
| !pm status (aliases: statuses, keyword) | command (subcommand) | disbot/cogs/project_moon_cog.py:154 | | | |
| !pm ego (aliases: grade) | command (subcommand) | disbot/cogs/project_moon_cog.py:159 | | | |
| !pm damage (aliases: damagetype) | command (subcommand) | disbot/cogs/project_moon_cog.py:164 | | | |
| !pm mechanic (aliases: mechanics, combat) | command (subcommand) | disbot/cogs/project_moon_cog.py:169 | | | |
| LimbusBrowseView | panel/view | disbot/views/projmoon/browse.py:185 | | | |
| _KindButton | panel/view (component) | disbot/views/projmoon/browse.py:140 | | | |
| _OverviewButton | panel/view (component) | disbot/views/projmoon/browse.py:155 | | | |
| _OriginsButton | panel/view (component) | disbot/views/projmoon/browse.py:170 | | | |
| build_help_menu_view | help hook (help-menu direct-nav) | disbot/cogs/project_moon_cog.py:191 | | | |
| project_moon.lookup.view (entry_points/help metadata) | setting/registry entry | disbot/utils/subsystem_registry.py:808 | | | |

**Unit kinds present:** command, panel/view, help hook, setting/registry entry.

**Structural-pattern flags:** none obvious — read-only, deterministic reference cog; no @bot.event / bus.on listener, no bus.emit / emit_audit_action event, no DB store (grep of utils/db + migrations found no project_moon-owned table — "No writes, no DB, no AI gateway" per module docstring, disbot/cogs/project_moon_cog.py:16), no scheduled loop, no voice, no wait_for wizard, no settings_keys constant (subsystem_registry entries above are metadata/entry-points, not a db.get_setting key — ⚠ unverified whether any settings_keys constant exists elsewhere for this subsystem, grep found none).

---

### help
_cogs: disbot/cogs/help_cog.py, disbot/cogs/help/panels.py, disbot/cogs/help/route.py (support modules, not a Cog subclass)_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !help | command | disbot/cogs/help_cog.py:284 | | | |
| /help | command | disbot/cogs/help_cog.py:370 | | | |
| HelpCategoryView | panel/view | disbot/cogs/help/panels.py:38 | | | |
| HelpCategoryView._on_select | listener (component callback) | disbot/cogs/help/panels.py:94 | | | |
| HelpEntityEditorView | panel/view | disbot/views/help/editor.py:285 | | | |
| EntityPickerView | panel/view | disbot/views/help/editor.py:435 | | | |
| _ResetAllConfirmView | panel/view | disbot/views/help/editor.py:526 | | | |
| HelpEditorHomeView | panel/view | disbot/views/help/editor.py:567 | | | |
| HomeMessageBuilderView | panel/view | disbot/views/help/home_builder.py:158 | | | |
| HelpEntityEditorView Hide/Rename/Reset buttons | panel control | disbot/views/help/editor.py:309-373 | | | |
| HelpEditorHomeView Hubs/Subsystems/Reset-all buttons | panel control | disbot/views/help/editor.py:570-614 | | | |
| HomeMessageBuilderView Edit/Preview/Save/Reset buttons | panel control | disbot/views/help/home_builder.py:217-337 | | | |
| help.menu.view | setting/capability | disbot/utils/subsystem_registry.py:1071 | | | |
| help.settings.configure | setting/capability | disbot/utils/subsystem_registry.py:1072 | | | |
| set_overlay_fields | mutation (hide/rename/redescribe entity) | disbot/services/help_overlay_mutation.py:150 | | | |
| set_home_message | mutation (Help-Home title/body/color) | disbot/services/help_overlay_mutation.py:238 | | | |
| reset_guild_overlay | mutation (reset all overlay rows) | disbot/services/help_overlay_mutation.py:326 | | | |
| audit.action_recorded (help overlay writes) | event | disbot/services/help_overlay_mutation.py:363 (via services/audit_events.emit_audit_action) | | | |
| help_overlay table | store | disbot/migrations/064_help_overlay.sql:26 (widened 067_help_overlay_home_message.sql) | | | |
| get_guild_help_overlay | store accessor / cache | disbot/services/help_overlay.py:148 | | | |
| build_help_catalogue | help catalogue builder | disbot/services/help_catalogue.py:116 | | | |
| build_single_command_embed / build_not_found_embed | help entry rendering | disbot/cogs/help/route.py:166,192 | | | |

**Unit kinds present:** command, panel/view, panel control (button), setting/capability, mutation, event, store, help-catalogue/rendering helper

**Structural-pattern flags:** none obvious (no @bot.event/bus.on listener, no wait_for wizard, no scheduled loop, no voice); Help editor views are persistent-view button/select panels reached from the Server Management hub, not a gateway listener.


---

### settings
_cogs: disbot/cogs/settings_cog.py_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !settings | command (prefix group) | disbot/cogs/settings_cog.py:121 | | | |
| !settings access | command (subcommand) | disbot/cogs/settings_cog.py:161 | | | |
| /settings | command (slash) | disbot/cogs/settings_cog.py:194 | | | |
| build_help_menu_view | help/nav hook | disbot/cogs/settings_cog.py:174 | | | |
| SettingsHubView | panel/view (hub) | disbot/views/settings/hub.py:330 | | | |
| _SubsystemSelect | panel/view (component) | disbot/views/settings/hub.py:138 | | | |
| _GroupPageButton | panel/view (component) | disbot/views/settings/hub.py:191 | | | |
| _OpenNeedsSetup | panel/view (component) | disbot/views/settings/hub.py:219 | | | |
| _OpenInvalid | panel/view (component) | disbot/views/settings/hub.py:237 | | | |
| _OpenMissingBindings | panel/view (component) | disbot/views/settings/hub.py:258 | | | |
| _OpenAudit | panel/view (component) | disbot/views/settings/hub.py:279 | | | |
| _OpenCommandAccess | panel/view (component) | disbot/views/settings/hub.py:300 | | | |
| SubsystemSettingsView | panel/view (drill-down) | disbot/views/settings/subsystem_view.py:609 | | | |
| RecentChangesView | panel/view (audit) | disbot/views/settings/audit_view.py:130 | | | |
| InvalidSettingsView | panel/view | disbot/views/settings/invalid_settings.py:111 | | | |
| MissingBindingsView | panel/view | disbot/views/settings/missing_bindings.py:103 | | | |
| NeedsSetupView | panel/view | disbot/views/settings/needs_setup.py:131 | | | |
| CommandAccessView | panel/view | disbot/views/settings/edit_command_access.py:492 | | | |
| ChannelSettingSelectView | panel/view (discord.ui.View direct) | disbot/views/settings/edit_channel.py:157 | | | |
| RoleSettingSelectView | panel/view (discord.ui.View direct) | disbot/views/settings/edit_role.py:155 | | | |
| NumericPresetsView | panel/view (discord.ui.View direct) | disbot/views/settings/edit_number_presets.py:161 | | | |
| NumberSettingModal | panel/view (modal) | disbot/views/settings/edit_number.py:21 | | | |
| TextSettingModal | panel/view (modal) | disbot/views/settings/edit_text.py:19 | | | |
| _DisabledHelpHookView | panel/view (fallback) | disbot/cogs/settings_cog.py:216 | | | |
| settings.manager.view | setting/capability | disbot/utils/subsystem_registry.py (SUBSYSTEMS["settings"]["capabilities"]) | | | |
| settings.manager_cog.enabled | setting (feature flag) | disbot/cogs/settings_cog.py:41 (`_FLAG_NAME`) | | | |
| guild_settings | store (table, KV settings) | disbot/utils/db/settings.py:1; CREATE TABLE disbot/utils/db/migrations.py:272 | | | |
| get_setting / set_setting | store (accessor) | disbot/utils/db/settings.py:21,29 | | | |
| set_value_with_audit | store (accessor, audited write) | disbot/utils/db/settings_audit.py:33 | | | |
| list_recent_for_guild / list_recent_for_key | store (accessor, audit history) | disbot/utils/db/settings_audit.py:133,155 | | | |
| settings.changed (EVT_SETTINGS_CHANGED) | event (bus.emit) | disbot/services/settings_mutation.py:614 | | | |
| emit_audit_action (settings mutation) | event (audit) | disbot/services/settings_mutation.py:385 | | | |

**Unit kinds present:** command, panel/view, setting, store, event, help
**Structural-pattern flags:** wait_for wizard-style modal flows (NumberSettingModal, TextSettingModal use discord.ui.Modal submit, not raw wait_for); no @bot.event/bus.on listener owned by this subsystem (it only emits `settings.changed`, does not subscribe); no scheduled loop; no voice; no stateful game loop. Otherwise: none obvious.

---

### logging
_cogs: disbot/cogs/logging_cog.py, disbot/cogs/logging/panel.py, disbot/cogs/logging/select_view.py, disbot/cogs/logging/provision_view.py, disbot/cogs/logging/routes_panel.py, disbot/cogs/logging/schemas.py_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !logging | command (group) | disbot/cogs/logging_cog.py:313 | | | |
| !logging status | command | disbot/cogs/logging_cog.py:329 | | | |
| !logging set <kind> | command | disbot/cogs/logging_cog.py:335 | | | |
| !logging create <kind> | command | disbot/cogs/logging_cog.py:372 | | | |
| !logging routes | command | disbot/cogs/logging_cog.py:401 | | | |
| !logging test | command | disbot/cogs/logging_cog.py:421 | | | |
| on_message_delete | listener | disbot/cogs/logging_cog.py:170 | | | |
| on_message_edit | listener | disbot/cogs/logging_cog.py:179 | | | |
| on_member_join | listener | disbot/cogs/logging_cog.py:199 | | | |
| on_member_remove | listener | disbot/cogs/logging_cog.py:212 | | | |
| on_member_update | listener | disbot/cogs/logging_cog.py:221 | | | |
| on_audit_log_entry_create | listener | disbot/cogs/logging_cog.py:257 | | | |
| on_voice_state_update | listener | disbot/cogs/logging_cog.py:267 | | | |
| on_raw_message_delete | listener | disbot/cogs/logging_cog.py:285 | | | |
| _on_moderation_action (EVT_MOD_ACTION → private log) | event listener (bus.on) | disbot/services/server_logging.py:1854 | | | |
| _on_moderation_action_public (EVT_MOD_ACTION → public log) | event listener (bus.on) | disbot/services/server_logging.py:1855 | | | |
| _on_audit_action (EVT_AUDIT_ACTION_RECORDED) | event listener (bus.on) | disbot/services/server_logging.py:1856 | | | |
| LoggingPanelView | panel/view | disbot/cogs/logging/panel.py:49 | | | |
| LogChannelSelectView | panel/view | disbot/cogs/logging/select_view.py:129 | | | |
| LogChannelProvisionView | panel/view | disbot/cogs/logging/provision_view.py:181 | | | |
| LoggingRoutesView | panel/view | disbot/cogs/logging/routes_panel.py:223 | | | |
| _RouteSelect | panel/view (sub-component) | disbot/cogs/logging/routes_panel.py:188 | | | |
| _LogChannelSelect | panel/view (sub-component) | disbot/cogs/logging/select_view.py:90 | | | |
| _ClearBindingButton | panel/view (sub-component) | disbot/cogs/logging/select_view.py:114 | | | |
| _ConfirmCreateButton | panel/view (sub-component) | disbot/cogs/logging/provision_view.py:144 | | | |
| _CancelButton | panel/view (sub-component) | disbot/cogs/logging/provision_view.py:160 | | | |
| LOGGING_ENABLED | setting | disbot/utils/settings_keys/logging.py:10 | | | |
| LOGGING_MOD_CHANNEL | setting | disbot/utils/settings_keys/logging.py:13 | | | |
| LOGGING_CLEANUP_CHANNEL | setting | disbot/utils/settings_keys/logging.py:17 | | | |
| LOGGING_AUTO_CREATE_CHANNELS | setting | disbot/utils/settings_keys/logging.py:22 | | | |
| LOGGING_MESSAGES_ENABLED | setting | disbot/utils/settings_keys/logging.py:43 | | | |
| LOGGING_MEMBERS_ENABLED | setting | disbot/utils/settings_keys/logging.py:44 | | | |
| LOGGING_ROLES_ENABLED | setting | disbot/utils/settings_keys/logging.py:45 | | | |
| LOGGING_MODERATION_ENABLED | setting | disbot/utils/settings_keys/logging.py:73 | | | |
| LOGGING_CHANNELS_ENABLED | setting | disbot/utils/settings_keys/logging.py:74 | | | |
| LOGGING_SERVER_ENABLED | setting | disbot/utils/settings_keys/logging.py:75 | | | |
| LOGGING_VOICE_ENABLED | setting | disbot/utils/settings_keys/logging.py:76 | | | |
| LOGGING_EVENT_ROUTING | setting | disbot/utils/settings_keys/logging.py:83 | | | |
| LOGGING_IGNORED_CHANNELS | setting | disbot/utils/settings_keys/logging.py:91 | | | |
| LOGGING_IGNORED_USERS | setting | disbot/utils/settings_keys/logging.py:92 | | | |
| capability logging.settings.configure | setting (capability) | disbot/utils/subsystem_registry.py:1205 | | | |
| capability logging.channel.bind | setting (capability) | disbot/utils/subsystem_registry.py:1206 | | | |
| capability logging.channel.create | setting (capability) | disbot/utils/subsystem_registry.py:1207 | | | |
| guild key-value settings store (no dedicated logging table found) | store | disbot/utils/db/ ⚠ unverified — no `log_bindings`/`log_channel` table located | | | |
| help entry for `logging` subsystem | help | disbot/services/help_catalogue.py ⚠ unverified — no explicit "logging" string match found in help_catalogue.py | | | |

**Unit kinds present:** command, listener, event listener (bus.on), panel/view, setting (incl. capability), store, help

**Structural-pattern flags:** gateway (`@commands.Cog.listener()` on 8 Discord events: message delete/edit, member join/remove/update, audit-log-entry, voice-state, raw-message-delete) + EventBus `bus.on(...)` listener (3 subscriptions in server_logging.py) + select/confirm wizard-style views (LogChannelSelectView, LogChannelProvisionView). No stateful game loop, no scheduled loop, no voice-channel-audio usage (voice unit here is only voice-state-change logging, not audio).


---

### diagnostic
_cogs: disbot/cogs/diagnostic_cog.py, disbot/cogs/diagnostic/platform_group.py (+ _platform_embeds.py, _log_buffer.py, _backfill.py, _helpers.py)_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !diagnostics / diag | command (prefix) | disbot/cogs/diagnostic_cog.py:57 | | | |
| !lifecycle / lc | command (prefix) | disbot/cogs/diagnostic_cog.py:64 | | | |
| /platform | command (slash) | disbot/cogs/diagnostic_cog.py:116 | | | |
| !listcmds / list_commands_detailed | command (prefix) | disbot/cogs/diagnostic_cog.py:137 | | | |
| !findcmd / find_command | command (prefix) | disbot/cogs/diagnostic_cog.py:148 | | | |
| !validatejson / validate_json_files | command (prefix) | disbot/cogs/diagnostic_cog.py:183 | | | |
| !checkdb / check_database | command (prefix) | disbot/cogs/diagnostic_cog.py:190 | | | |
| !diag_status / diagnostic_bot_status | command (prefix) | disbot/cogs/diagnostic_cog.py:201 | | | |
| !latency | command (prefix) | disbot/cogs/diagnostic_cog.py:208 | | | |
| !sysinfo / system_info | command (prefix) | disbot/cogs/diagnostic_cog.py:220 | | | |
| !querylogs / query_logs | command (prefix) | disbot/cogs/diagnostic_cog.py:231 | | | |
| !errors / recent_errors | command (prefix) | disbot/cogs/diagnostic_cog.py:238 | | | |
| !testnotify / test_notification | command (prefix) | disbot/cogs/diagnostic_cog.py:245 | | | |
| !platform (group) | command (group) | disbot/cogs/diagnostic/platform_group.py:110 | | | |
| platform status | command (subcommand) | disbot/cogs/diagnostic/platform_group.py:131 | | | |
| platform setup_readiness | command (subcommand) | disbot/cogs/diagnostic/platform_group.py:137 | | | |
| platform anchors | command (subcommand) | disbot/cogs/diagnostic/platform_group.py:156 | | | |
| platform identity | command (subcommand) | disbot/cogs/diagnostic/platform_group.py:162 | | | |
| platform runtime | command (subcommand) | disbot/cogs/diagnostic/platform_group.py:179 | | | |
| platform health | command (subcommand) | disbot/cogs/diagnostic/platform_group.py:185 | | | |
| platform startup | command (subcommand) | disbot/cogs/diagnostic/platform_group.py:207 | | | |
| platform findings | command (subcommand) | disbot/cogs/diagnostic/platform_group.py:234 | | | |
| platform finding <action> | command (subcommand) | disbot/cogs/diagnostic/platform_group.py:267 | | | |
| platform lifecycle | command (subcommand) | disbot/cogs/diagnostic/platform_group.py:315 | | | |
| platform caches | command (subcommand) | disbot/cogs/diagnostic/platform_group.py:321 | | | |
| platform media | command (subcommand) | disbot/cogs/diagnostic/platform_group.py:327 | | | |
| platform economy | command (subcommand) | disbot/cogs/diagnostic/platform_group.py:340 | | | |
| platform economy_trend | command (subcommand) | disbot/cogs/diagnostic/platform_group.py:351 | | | |
| platform locks | command (subcommand) | disbot/cogs/diagnostic/platform_group.py:363 | | | |
| platform tasks | command (subcommand) | disbot/cogs/diagnostic/platform_group.py:369 | | | |
| platform views | command (subcommand) | disbot/cogs/diagnostic/platform_group.py:375 | | | |
| platform slow | command (subcommand) | disbot/cogs/diagnostic/platform_group.py:381 | | | |
| platform automation | command (subcommand) | disbot/cogs/diagnostic/platform_group.py:387 | | | |
| platform sessions | command (subcommand) | disbot/cogs/diagnostic/platform_group.py:402 | | | |
| platform schemas | command (subcommand) | disbot/cogs/diagnostic/platform_group.py:416 | | | |
| platform settings_registry | command (subcommand) | disbot/cogs/diagnostic/platform_group.py:422 | | | |
| platform setting <subsystem> <name> | command (subcommand) | disbot/cogs/diagnostic/platform_group.py:428 | | | |
| platform customization | command (subcommand) | disbot/cogs/diagnostic/platform_group.py:442 | | | |
| platform provisioning | command (subcommand) | disbot/cogs/diagnostic/platform_group.py:448 | | | |
| platform participation_schemas | command (subcommand) | disbot/cogs/diagnostic/platform_group.py:454 | | | |
| platform resource_requirements | command (subcommand) | disbot/cogs/diagnostic/platform_group.py:460 | | | |
| platform bindings | command (subcommand) | disbot/cogs/diagnostic/platform_group.py:466 | | | |
| platform resources | command (subcommand) | disbot/cogs/diagnostic/platform_group.py:472 | | | |
| platform flags | command (subcommand) | disbot/cogs/diagnostic/platform_group.py:478 | | | |
| platform flag_manager | command (subcommand) | disbot/cogs/diagnostic/platform_group.py:484 | | | |
| platform migrations | command (subcommand) | disbot/cogs/diagnostic/platform_group.py:507 | | | |
| platform consistency | command (subcommand) | disbot/cogs/diagnostic/platform_group.py:513 | | | |
| platform backfill <action> | command (subcommand) | disbot/cogs/diagnostic/platform_group.py:522 | | | |
| platform command_access | command (subcommand) | disbot/cogs/diagnostic/platform_group.py:533 | | | |
| platform access | command (subcommand) | disbot/cogs/diagnostic/platform_group.py:559 | | | |
| _PaginatorView | panel/view | disbot/views/diagnostic/paginator.py:21 | | | generic paginated embed view, BaseView subclass |
| _DiagnosticsHubView | panel/view | disbot/views/diagnostic/hub_panel.py:41 | | | diagnostics hub panel, HubView subclass, opened by !diagnostics |
| FlagManagerView | panel/view | disbot/views/diagnostic/flag_manager.py:304 | | | feature-flag manager panel, HubView subclass |
| AutomationPanelView | panel/view | disbot/views/diagnostic/automation_panel.py:396 | | | automation status panel, HubView subclass |
| _PlatformHubView | panel/view | disbot/views/diagnostic/platform_panel.py:332 | | | platform hub panel, HubView subclass opened by !platform |
| diagnostic.health.view | setting/capability | disbot/utils/subsystem_registry.py:1094 | | | capability entry in SUBSYSTEMS["diagnostic"] |
| diagnostic.latency.check | setting/capability | disbot/utils/subsystem_registry.py:1095 | | | capability entry in SUBSYSTEMS["diagnostic"] |
| btd6.diagnostics.view | setting/capability (⚠ unverified subsystem owner) | disbot/utils/subsystem_registry.py:803 | | | referenced under related capability list, unclear which SUBSYSTEMS entry owns it |
| health_findings store | store | disbot/utils/db/health_findings.py:1 | | | DB accessors for operational health findings table |
| 057_operational_health_findings | store (migration) | disbot/migrations/057_operational_health_findings.sql:1 | | | creates operational_health_findings table |
| platform_consistency store (⚠ related, not solely owned) | store | disbot/utils/db/platform_consistency.py:1 | | | consistency-layer DB accessors, adjacent subsystem per folio |
| send_panel (diagnostics hub) | panel entry point | disbot/cogs/diagnostic_cog.py:60 | | | opens _DiagnosticsHubView via send_panel |
| send_panel (platform hub) | panel entry point | disbot/cogs/diagnostic/platform_group.py:127 | | | opens _PlatformHubView via send_panel |
| send_panel (automation panel) | panel entry point | disbot/cogs/diagnostic/platform_group.py:398 | | | opens AutomationPanelView via send_panel |
| send_panel (flag manager) | panel entry point | disbot/cogs/diagnostic/platform_group.py:499 | | | opens FlagManagerView via send_panel |
| diagnostic_helpers.build overview embed | help/embed | disbot/services/diagnostic_helpers.py:45 | | | static "Select a diagnostic tool below" overview embed |
| _log_buffer.recent | log/store helper | disbot/cogs/diagnostic/_log_buffer.py:1 | | | in-memory recent-log buffer used by querylogs/errors |


---

### ux_lab
_cogs: disbot/cogs/ux_lab_cog.py_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !uxlab (alias !interfacelab) | command | disbot/cogs/ux_lab_cog.py:57 | | | |
| /uxlab | command | disbot/cogs/ux_lab_cog.py:68 | | | |
| build_help_menu_view (help/hub direct-nav hook) | help | disbot/cogs/ux_lab_cog.py:42 | | | |
| cog_load (registers persistent view) | listener | disbot/cogs/ux_lab_cog.py:35 | | | |
| UxLabHomeView | panel/view | disbot/views/ux_lab/home.py:78 | | | |
| ExhibitWingView | panel/view | disbot/views/ux_lab/wing.py:38 | | | |
| ButtonsWingView | panel/view | disbot/views/ux_lab/buttons.py:263 | | | |
| _TimeoutDemoView | panel/view | disbot/views/ux_lab/buttons.py:252 | | | |
| _ConfirmDeleteModal | panel/view | disbot/views/ux_lab/buttons.py:228 | | | |
| CompareView | panel/view | disbot/views/ux_lab/compare.py:143 | | | |
| _VerdictModal | panel/view | disbot/views/ux_lab/compare.py:102 | | | |
| EmbedsWingView | panel/view | disbot/views/ux_lab/embeds.py:146 | | | |
| ImageWingView | panel/view | disbot/views/ux_lab/image_cards.py:195 | | | |
| _LabLayout (discord.ui.LayoutView) | panel/view | disbot/views/ux_lab/layout_v2.py:108 | | | |
| LayoutWingView | panel/view | disbot/views/ux_lab/layout_v2.py:143 | | | |
| MockupsWingView | panel/view | disbot/views/ux_lab/mockups.py:106 | | | |
| _ThresholdModal | panel/view | disbot/views/ux_lab/mockups.py:473 | | | |
| _ShortLongModal | panel/view | disbot/views/ux_lab/modals.py:136 | | | |
| _LabelSelectModal | panel/view | disbot/views/ux_lab/modals.py:157 | | | |
| _ValidationModal | panel/view | disbot/views/ux_lab/modals.py:191 | | | |
| _DraftModal | panel/view | disbot/views/ux_lab/modals.py:214 | | | |
| _ReportFormModal | panel/view | disbot/views/ux_lab/modals.py:232 | | | |
| _TemplateModal | panel/view | disbot/views/ux_lab/modals.py:254 | | | |
| ModalsWingView | panel/view | disbot/views/ux_lab/modals.py:279 | | | |
| UxLabPersistentDemo | panel/view | disbot/views/ux_lab/persistent_demo.py:23 | | | |
| ProbesBenchView | panel/view | disbot/views/ux_lab/probes.py:104 | | | |
| _SearchModal | panel/view | disbot/views/ux_lab/selects.py:160 | | | |
| SelectsWingView | panel/view | disbot/views/ux_lab/selects.py:177 | | | |

**Unit kinds present:** command, panel/view (incl. modals), help, listener (cog_load registration only). No `setting` unit (capabilities list is empty by design — "zero-write workbench"), no `event` (emit_audit_action), no `store` (DB tables) found — confirmed by grep returning no matches, consistent with the code comment "the lab mutates nothing (CI-fenced by tests/unit/invariants/test_ux_lab_zero_write.py)".

**Structural-pattern flags:** persistent view registered at cog_load (UxLabPersistentDemo, PersistentView, added via bot.add_view — a restart-surviving component-listener pattern); several `discord.ui.Modal` wizards (_ConfirmDeleteModal, _VerdictModal, _ThresholdModal, _ShortLongModal, _LabelSelectModal, _ValidationModal, _DraftModal, _ReportFormModal, _TemplateModal, _SearchModal) simulating wait_for-style forms; no @bot.event/bus.on gateway listener, no scheduled loop, no voice. Otherwise none obvious.

---

### utility
_cogs: disbot/cogs/utility_cog.py_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !utilitymenu | command | cogs/utility_cog.py:82 | | | |
| /utility | command | cogs/utility_cog.py:99 | | | |
| !myprofile | command | cogs/utility_cog.py:116 | | | |
| /myprofile | command | cogs/utility_cog.py:135 | | | |
| !clear (alias !purge) | command | cogs/utility_cog.py:162 | | | |
| !info | command | cogs/utility_cog.py:181 | | | |
| !serverinfo | command | cogs/utility_cog.py:251 | | | |
| !userinfo | command | cogs/utility_cog.py:260 | | | |
| !avatar | command | cogs/utility_cog.py:269 | | | |
| !remind | command | cogs/utility_cog.py:277 | | | |
| !invite | command | cogs/utility_cog.py:292 | | | |
| !poll | command | cogs/utility_cog.py:298 | | | |
| !ping | command | cogs/utility_cog.py:316 | | | |
| !botinfo (alias !about) | command | cogs/utility_cog.py:334 | | | |
| !membercount (alias !members) | command | cogs/utility_cog.py:374 | | | |
| _UtilityPanelView | panel | cogs/utility_cog.py:472 | | | Main hub panel opened by utilitymenu/utility slash |
| _UtilityChildButton | panel | cogs/utility_cog.py:461 | | | HubChildButton subclass for child-subsystem nav |
| attach_back_to_utility_button | panel | cogs/utility_cog.py:416 | | | Adds Back-to-Utility button to child views |
| _PollModal | panel | cogs/utility_cog.py:643 | | | discord.ui.Modal collecting poll question/options |
| _RemindModal | panel | cogs/utility_cog.py:684 | | | discord.ui.Modal collecting reminder minutes/message |
| cog_unload (reminder task cleanup) | listener | cogs/utility_cog.py:72 | | | Cancels in-memory "utility:" tasks on unload |

**Unit kinds present:** command, panel
**Structural-pattern flags:** wait_for wizard (modal-driven poll/remind flows: _PollModal, _RemindModal); none of stateful game loop / gateway listener / scheduled loop / voice obvious. No settings/db store/event/help-catalogue units found for this subsystem — utility_cog.py has no db.get_setting, bus.emit/emit_audit_action, or bot.event/Cog.listener calls (⚠ unverified beyond grep of utility_cog.py; SUBSYSTEMS["utility"] entry has no settings keys, only capabilities utility.info.server / utility.info.user / utility.tool.ping used for entry_points/menu discovery, not DB-backed settings).

---

### general
_cogs: disbot/cogs/general_cog.py_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !generalmenu (alias !gmenu) | command | cogs/general_cog.py:87 | | | |
| !fact | command | cogs/general_cog.py:113 | | | |
| !joke | command | cogs/general_cog.py:125 | | | |
| !quote | command | cogs/general_cog.py:137 | | | |
| !trivia | command | cogs/general_cog.py:152 | | | |
| !motivate | command | cogs/general_cog.py:171 | | | |
| !eightball (alias !8ball) | command | cogs/general_cog.py:184 | | | |
| !greet | command | cogs/general_cog.py:191 | | | |
| _GeneralPanelView | panel/view | cogs/general_cog.py:246 | | | |
| _GeneralPanelView.fact_btn | panel/view | cogs/general_cog.py:262 | | | |
| _GeneralPanelView.joke_btn | panel/view | cogs/general_cog.py:276 | | | |
| _GeneralPanelView.quote_btn | panel/view | cogs/general_cog.py:290 | | | |
| _GeneralPanelView.trivia_btn | panel/view | cogs/general_cog.py:304 | | | |
| _GeneralPanelView.motivate_btn | panel/view | cogs/general_cog.py:328 | | | |
| _GeneralPanelView.eightball_btn (opens _EightBallModal) | panel/view | cogs/general_cog.py:342 | | | |
| _GeneralPanelView.greet_btn | panel/view | cogs/general_cog.py:350 | | | |
| _GeneralPanelView.overview_btn | panel/view | cogs/general_cog.py:362 | | | |
| _TriviaRevealView (reveal_btn) | panel/view | cogs/general_cog.py:222-236 | | | |
| _EightBallModal | panel/view | cogs/general_cog.py:243 | | | |
| build_help_menu_view (help-menu entry hook) | help | cogs/general_cog.py:99 | | | |
| SUBSYSTEMS["general"] capabilities: general.info.view, general.community.interact | setting | utils/subsystem_registry.py:1027-1028 | | | |
| SUBSYSTEMS["general"] entry_points: ["generalmenu"] | setting | utils/subsystem_registry.py:1017 | | | |

**Unit kinds present:** command, panel/view, help, setting

**Structural-pattern flags:** none obvious — stateless content-serving cog; no @bot.event/bus.on listeners, no DB tables/settings writes, no scheduled loops, no voice, no wait_for wizard. ⚠ unverified: docs/subsystems/general.md does not exist (checked, absent), so folio cross-reference could not be verified beyond subsystem_registry.py and source.


---

### proof_channel
_cogs: disbot/cogs/proof_channel_cog.py, disbot/cogs/proof_channel/schemas.py, disbot/cogs/proof_channel/__init__.py_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| +prize | command | disbot/cogs/proof_channel_cog.py:121 | | | |
| -prize | command | disbot/cogs/proof_channel_cog.py:138 | | | |
| prizestatus | command | disbot/cogs/proof_channel_cog.py:152 | | | |
| prizemenu | command | disbot/cogs/proof_channel_cog.py:169 | | | |
| timedprize | command | disbot/cogs/proof_channel_cog.py:184 | | | |
| _PrizeManagerView (prize manager panel) | panel/view | disbot/cogs/proof_channel_cog.py:312 | | | |
| btn_grant (🏆 Grant Access button) | panel | disbot/cogs/proof_channel_cog.py:339-343 | | | |
| btn_timed (⏱️ Timed Access button) | panel | disbot/cogs/proof_channel_cog.py:345-353 | | | |
| btn_end (🔒 End Session button) | panel | disbot/cogs/proof_channel_cog.py:355-371 | | | |
| btn_refresh (🔄 Refresh Status button) | panel | disbot/cogs/proof_channel_cog.py:373-382 | | | |
| _PrizeWinnerModal (winner input modal) | panel | disbot/cogs/proof_channel_cog.py:219-254 | | | |
| _TimedPrizeModal (duration input modal) | panel | disbot/cogs/proof_channel_cog.py:257-309 | | | |
| build_help_menu_view (help-menu direct-nav hook) | help | disbot/cogs/proof_channel_cog.py:174-180 | | | |
| proof_channel binding (channel setting) | setting | disbot/cogs/proof_channel/schemas.py:43-51 | | | |
| proof_channel.settings.configure capability | setting | disbot/utils/subsystem_registry.py:982 | | | |
| proof_channel.access.grant/revoke/timed capabilities | setting | disbot/utils/subsystem_registry.py:979-981 | | | |
| proof resource requirement (optional channel) | setting | disbot/cogs/proof_channel/schemas.py:58-70 | | | |
| cog_load → register_schemas | listener | disbot/cogs/proof_channel_cog.py:25-28 | | | |
| cog_unload → cancel proof:* tasks | listener | disbot/cogs/proof_channel_cog.py:30-33 | | | |
| _emit_prize_audit (prize_access_grant/revoke audit) | event | disbot/cogs/proof_channel_cog.py:413-454 | | | |
| proof:unlock:<guild_id> scheduled auto-unlock task | event | disbot/cogs/proof_channel_cog.py:201-216, 292-305 | | | |

**Unit kinds present:** command, panel, setting, listener, event, help
**Structural-pattern flags:** wait_for-style modal wizard (`_PrizeWinnerModal`/`_TimedPrizeModal` via `send_modal`); scheduled/timed one-shot task (`tasks.spawn` auto-unlock after duration, not a recurring loop). No `@bot.event`/`bus.on` listener beyond cog_load/cog_unload lifecycle hooks; no dedicated DB table (uses generic bindings/subsystem_schema store, not a domain table); no voice.
