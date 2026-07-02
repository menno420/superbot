# Lane A — Governance & Safety (Axis 1)

> **Status:** `reference` — this lane's workspace. The surface-unit inventories below are **pre-extracted** (facts only, tier columns blank). The Lane A agent **verifies + completes them against source**, fills BOTH tier columns, writes each subsystem's §2 manifest sketch, dispositions tier-3s, and adds reconsider/optimize recommendations — per [`../BRIEF.md`](../BRIEF.md). Treat the inventory as a starting scaffold, not ground truth.

**Subsystems:** admin, server_management, moderation, automod, image_moderation, security, cleanup, role, channel, welcome, ticket

**Method:** [`../BRIEF.md`](../BRIEF.md) · [`../PARTITION.md`](../PARTITION.md) · `tools/grammar_spike/` · `../ground-truth/command-surface.json`.

---

### admin
_cogs: disbot/cogs/admin_cog.py_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !adminmenu | command | cogs/admin_cog.py:36 | | | |
| /admin | command | cogs/admin_cog.py:51 | | | |
| !serverstats | command | cogs/admin_cog.py:75 | | | |
| !cog | command | cogs/admin_cog.py:97 | | | |
| !loadall | command | cogs/admin_cog.py:124 | | | |
| !unloadall | command | cogs/admin_cog.py:147 | | | |
| !coglist (aliases: cogs, listcogs, cogslist) | command | cogs/admin_cog.py:174 | | | |
| !syncslash (alias: syncs) | command | cogs/admin_cog.py:198 | | | |
| !slashes (alias: slashlist) | command | cogs/admin_cog.py:295 | | | |
| !restart | command | cogs/admin_cog.py:365 | | | |
| !loglevel | command | cogs/admin_cog.py:393 | | | |
| _AdminPanelView | panel | cogs/admin_cog.py:467 | | | |
| Stats button | panel | cogs/admin_cog.py:496 | | | |
| Cog List button | panel | cogs/admin_cog.py:516 | | | |
| Reload All button | panel | cogs/admin_cog.py:534 | | | |
| Log Level button (opens modal) | panel | cogs/admin_cog.py:561 | | | |
| Settings button (navigates to settings panel) | panel | cogs/admin_cog.py:575 | | | |
| Channels/AI/Platform/Diagnostics/UX Lab/Logging/Cleanup/Help nav buttons | panel | cogs/admin_cog.py:585-673 | | | |
| Overview back button | panel | cogs/admin_cog.py:699 | | | |
| _LogLevelModal | panel | cogs/admin_cog.py:763 | | | |
| on_ready startup message | listener | cogs/admin_cog.py:409 | | | |
| build_help_menu_view (help-menu direct-nav hook returning admin panel) | help | cogs/admin_cog.py:43 | | | |

**Unit kinds present:** command, panel, listener, help
**Structural-pattern flags:** gateway listener (`@commands.Cog.listener()` on_ready at line 409); modal wizard-lite (`_LogLevelModal`, a single-step `discord.ui.Modal`, not a multi-step wait_for wizard); no `bus.on`/EventBus subscription, no `emit_audit_action` calls, no owned DB tables/settings keys found in this cog — it is primarily a navigation hub delegating to other subsystems' panels (settings, channels, AI, platform, diagnostics, logging, cleanup, help) via nav buttons; no scheduled `@tasks.loop`; no voice.

---

### server_management
_cogs: disbot/cogs/server_management_cog.py_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !servermanagement (aliases: servermenu, guildmenu) | command | disbot/cogs/server_management_cog.py:45 | | | |
| /server-management | command | disbot/cogs/server_management_cog.py:80 | | | |
| ServerManagementHubView | panel/view | disbot/views/server_management/hub.py:117 | | | |
| 🛡️ Moderation button (routes to moderation cog panel) | panel/view | disbot/views/server_management/hub.py:174-185 | | | |
| 📺 Channels button (routes to channels cog panel) | panel/view | disbot/views/server_management/hub.py:187-198 | | | |
| 🎭 Roles button (routes to roles cog panel) | panel/view | disbot/views/server_management/hub.py:200-211 | | | |
| 🧹 Cleanup button (routes to cleanup cog panel) | panel/view | disbot/views/server_management/hub.py:213-224 | | | |
| 🧩 Setup button (opens setup wizard) | panel/view | disbot/views/server_management/hub.py:226-243 | | | |
| 🔓 Access Map button (opens AccessMapView) | panel/view | disbot/views/server_management/hub.py:245-277 | | | |
| 👁 Help Preview button (opens HelpPreviewView) | panel/view | disbot/views/server_management/hub.py:279-311 | | | |
| ✏️ Help editor button (opens HelpEditorHomeView) | panel/view | disbot/views/server_management/hub.py:313-345 | | | |
| 🔄 Refresh button (re-renders hub status) | panel/view | disbot/views/server_management/hub.py:347-355+ (body truncated, ⚠ unverified past line 355) | | | |
| AccessMapView (read-only access-decision subpanel) | panel/view | disbot/views/server_management/access_map.py:363 | | | |
| HelpPreviewView (read-only help-preview subpanel) | panel/view | disbot/views/server_management/access_map.py:401 | | | |
| build_help_menu_view hook (help-menu direct-nav entry to hub) | help | disbot/cogs/server_management_cog.py:59-71 | | | |
| SUBSYSTEMS["server_management"] registry entry (display/tags/entry_points, capabilities empty) | setting | disbot/utils/subsystem_registry.py:94-118 | | | |

**Unit kinds present:** command, panel/view, help (no dedicated setting, listener, event, or store unit found and owned by this subsystem — it is a routing-only hub with `capabilities: []` per subsystem_registry.py:118, and no table/migration or `bus.on`/`bus.emit`/`emit_audit_action` call was found under `disbot/cogs/server_management_cog.py`, `disbot/views/server_management/`, or `disbot/services/server_management_hub.py`).

**Structural-pattern flags:** none obvious for its own code (no `@bot.event`, no `bus.on`/`bus.emit`, no `wait_for` wizard, no scheduled loop, no voice) — it is a thin PersistentView routing hub that delegates via `interaction.client.get_cog(...).build_help_menu_view` to other subsystems' cogs (moderation, channels, roles, cleanup, setup), which may themselves carry those patterns but are out of scope here.

---

### moderation
_cogs: disbot/cogs/moderation_cog.py, disbot/cogs/moderation/__init__.py, disbot/cogs/moderation/schemas.py_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !modmenu | command | disbot/cogs/moderation_cog.py:79 | | | |
| /moderation | command | disbot/cogs/moderation_cog.py:98 | | | |
| !warn | command | disbot/cogs/moderation_cog.py:128 | | | |
| !timeout | command | disbot/cogs/moderation_cog.py:155 | | | |
| !kick | command | disbot/cogs/moderation_cog.py:181 | | | |
| !ban | command | disbot/cogs/moderation_cog.py:213 | | | |
| !unban | command | disbot/cogs/moderation_cog.py:246 | | | |
| !clearwarnings | command | disbot/cogs/moderation_cog.py:277 | | | |
| !modlogs | command | disbot/cogs/moderation_cog.py:292 | | | |
| ModPanelView | panel | disbot/views/moderation/main_panel.py:36 | | | |
| warn_btn (mod:warn) | panel | disbot/views/moderation/main_panel.py:63-70 | | | |
| timeout_btn (mod:timeout) | panel | disbot/views/moderation/main_panel.py:72-79 | | | |
| kick_btn (mod:kick) | panel | disbot/views/moderation/main_panel.py:81-88 | | | |
| ban_btn (mod:ban) | panel | disbot/views/moderation/main_panel.py:90-97 | | | |
| unban_btn (mod:unban) | panel | disbot/views/moderation/main_panel.py:99-106 | | | |
| modlogs_btn (mod:logs) | panel | disbot/views/moderation/main_panel.py:108-116 | | | |
| clearwarnings button (mod: clear warnings) | panel | disbot/views/moderation/main_panel.py:117+ | | | |
| _WarnModal | panel | disbot/views/moderation/modals.py:48 | | | |
| _TimeoutModal | panel | disbot/views/moderation/modals.py:95 | | | |
| _KickModal | panel | disbot/views/moderation/modals.py:160 | | | |
| _BanModal | panel | disbot/views/moderation/modals.py:215 | | | |
| _UnbanModal | panel | disbot/views/moderation/modals.py:271 | | | |
| _ModLogsModal | panel | disbot/views/moderation/modals.py:313 | | | |
| _ClearWarningsModal | panel | disbot/views/moderation/modals.py:349 | | | |
| WARN_THRESHOLD | setting | disbot/cogs/moderation/schemas.py:193 | | | |
| WARN_TIMEOUT_MINS | setting | disbot/cogs/moderation/schemas.py:205 | | | |
| MOD_WARN_ESCALATION_ACTION | setting | disbot/cogs/moderation/schemas.py:217 | | | |
| MOD_DM_ON_ACTION | setting | disbot/cogs/moderation/schemas.py:234 | | | |
| MOD_DM_ACTIONS | setting | disbot/cogs/moderation/schemas.py:248 | | | |
| MOD_DM_TEMPLATE | setting | disbot/cogs/moderation/schemas.py:263 | | | |
| MOD_REQUIRE_REASON | setting | disbot/cogs/moderation/schemas.py:276 | | | |
| MOD_BAN_DELETE_MESSAGE_DAYS | setting | disbot/cogs/moderation/schemas.py:289 | | | |
| MOD_MAX_TIMEOUT_MINUTES | setting | disbot/cogs/moderation/schemas.py:303 | | | |
| MOD_POST_ACTION_CLEANUP | setting | disbot/cogs/moderation/schemas.py:320 | | | |
| MOD_POST_ACTION_CLEANUP_LIMIT | setting | disbot/cogs/moderation/schemas.py:335 | | | |
| MOD_PUBLIC_LOG_ACTIONS | setting | disbot/cogs/moderation/schemas.py:352 | | | |
| MOD_PUBLIC_LOG_CHANNEL | setting | disbot/cogs/moderation/schemas.py:367 | | | |
| MODERATOR_TIER_ROLE_ID | setting | disbot/cogs/moderation/schemas.py:390 | | | |
| TRUSTED_TIER_ROLE_ID | setting | disbot/cogs/moderation/schemas.py:405 | | | |
| EVT_MOD_ACTION (moderation.action_taken) | event | disbot/services/moderation_service.py:88,226 | | | |
| audit.action_recorded (emit_audit_action) | event | disbot/services/moderation_service.py:213 | | | |
| mod_logs table | store | disbot/utils/db/migrations.py:257; disbot/utils/db/moderation.py:44,66 | | | |
| warnings store (get/add/clear_warning) | store | disbot/utils/db/moderation.py:12,20,32 | | | |
| moderation_service.warn | service-fn | disbot/services/moderation_service.py:361 | | | |
| moderation_service.timeout | service-fn | disbot/services/moderation_service.py:446 | | | |
| moderation_service.kick | service-fn | disbot/services/moderation_service.py:484 | | | |
| moderation_service.ban | service-fn | disbot/services/moderation_service.py:530 | | | |
| moderation_service.unban | service-fn | disbot/services/moderation_service.py:587 | | | |
| moderation_service.clear_warnings | service-fn | disbot/services/moderation_service.py:605 | | | |
| server_logging._on_moderation_action (bus.on EVT_MOD_ACTION) | listener | disbot/services/server_logging.py:1854 | | | |
| server_logging._on_moderation_action_public (bus.on EVT_MOD_ACTION) | listener | disbot/services/server_logging.py:1855 | | | |

**Unit kinds present:** command, panel (view+buttons+modals), setting, event, store, service-fn, listener (external subscriber)

**Structural-pattern flags:** gateway listener via EventBus (`bus.on(EVT_MOD_ACTION, ...)` consumed externally in server_logging.py, not within this cog itself — cross-subsystem wiring, verified only by grep since neither CodeGraph nor Grimp would connect emitter→subscriber); persistent panel view (`ModPanelView(PersistentView)`) with modal-based wizard-lite interactions (each button opens a `discord.ui.Modal`, not a multi-step `wait_for` wizard). No scheduled loop, no voice, no stateful game loop obvious in this subsystem's own files. ⚠ unverified: whether `!modlogs`/`_ModLogsModal` and `!clearwarnings`/`_ClearWarningsModal` are wired 1:1 with matching capability strings — not fully cross-checked against `subsystem_registry.py` capability list beyond what's quoted above.


---

### automod
_cogs: disbot/cogs/automod_cog.py, disbot/cogs/automod/listener.py, disbot/cogs/automod/schemas.py_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !automod | command | disbot/cogs/automod_cog.py:119 | | | |
| build_help_menu_view (help-dropdown hook, HubView) | panel/view | disbot/cogs/automod_cog.py:124 | | | |
| AutomodStage (message_pipeline stage, order=5) | listener | disbot/cogs/automod_cog.py:37 | | | |
| cog_load registers pipeline stage + schema | listener | disbot/cogs/automod_cog.py:59 | | | |
| cog_unload unregisters pipeline stage | listener | disbot/cogs/automod_cog.py:66 | | | |
| process_message (per-message evaluate+act) | listener | disbot/cogs/automod/listener.py:28 | | | |
| bus.emit("automod.rule_triggered") | event | disbot/cogs/automod/listener.py:114 | | | |
| setting: enabled (master switch) | setting | disbot/cogs/automod/schemas.py:115 | | | |
| setting: spam_enabled | setting | disbot/cogs/automod/schemas.py:128 | | | |
| setting: invites_enabled | setting | disbot/cogs/automod/schemas.py:137 | | | |
| setting: caps_enabled | setting | disbot/cogs/automod/schemas.py:146 | | | |
| setting: mentions_enabled | setting | disbot/cogs/automod/schemas.py:155 | | | |
| setting: spam_count | setting | disbot/cogs/automod/schemas.py:164 | | | |
| setting: spam_window_seconds | setting | disbot/cogs/automod/schemas.py:178 | | | |
| setting: caps_percent | setting | disbot/cogs/automod/schemas.py:189 | | | |
| setting: mentions_count | setting | disbot/cogs/automod/schemas.py:203 | | | |
| setting: exempt_roles | setting | disbot/cogs/automod/schemas.py:214 | | | |
| setting: exempt_channels | setting | disbot/cogs/automod/schemas.py:226 | | | |
| capability: automod.settings.configure | setting | disbot/utils/subsystem_registry.py:539 | | | |

**Unit kinds present:** command, panel, listener, event, setting
**Structural-pattern flags:** message-pipeline stage listener (not @bot.event/bus.on directly — registered via core.runtime.message_pipeline.register, order=5, fail-open); emits one advisory bus event (automod.rule_triggered); no dedicated DB table/store (uses legacy scalar guild-settings KV, no migration); no wizard/wait_for, no scheduled loop, no voice. Otherwise none obvious.

---

### image_moderation
_cogs: disbot/cogs/image_moderation_cog.py, disbot/cogs/image_moderation/listener.py, disbot/cogs/image_moderation/schemas.py_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !imagemod | command | cogs/image_moderation_cog.py:123 | | | |
| build_help_menu_view (help-dropdown hook) | help | cogs/image_moderation_cog.py:128 | | | |
| ImageModerationStage (message-pipeline stage, order=25) | listener | cogs/image_moderation_cog.py:41-54 | | | |
| cog_load registers pipeline stage + schema | listener | cogs/image_moderation_cog.py:63-68 | | | |
| cog_unload unregisters pipeline stage | listener | cogs/image_moderation_cog.py:70-73 | | | |
| process_message (scan attachments → act) | listener | cogs/image_moderation/listener.py:52-109 | | | |
| bus.emit("image_moderation.flagged") | event | cogs/image_moderation/listener.py:184-191 | | | |
| setting: enabled (master switch) | setting | cogs/image_moderation/schemas.py:96-108 | | | |
| setting: sexual_enabled | setting | cogs/image_moderation/schemas.py:109-117 | | | |
| setting: violence_enabled | setting | cogs/image_moderation/schemas.py:118-126 | | | |
| setting: harassment_enabled | setting | cogs/image_moderation/schemas.py:127-135 | | | |
| setting: hate_enabled | setting | cogs/image_moderation/schemas.py:136-144 | | | |
| setting: threshold_percent | setting | cogs/image_moderation/schemas.py:145-158 | | | |
| setting: exempt_roles | setting | cogs/image_moderation/schemas.py:159-170 | | | |
| setting: exempt_channels | setting | cogs/image_moderation/schemas.py:171-182 | | | |
| SubsystemSchema registration (IMAGE_MODERATION_CONFIG_SCHEMA) | setting | cogs/image_moderation/schemas.py:186-197 | | | |
| store: no dedicated table — uses legacy scalar guild-settings KV table (⚠ unverified table name, no migration file found) | store | disbot/services/image_moderation_config.py (load_policy) | | | |

**Unit kinds present:** command, help, listener, event, setting, store
**Structural-pattern flags:** none obvious — no @bot.event/bus.on listener registration (stage is invoked synchronously via message_pipeline, not EventBus subscription), no wait_for wizard, no scheduled loop, no voice, no dedicated panel/view (help hook reuses generic HubView with a read-only embed).


---

### security
_cogs: disbot/cogs/security_cog.py, disbot/cogs/security/schemas.py, disbot/cogs/security/__init__.py_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !security | command | disbot/cogs/security_cog.py:108 | | | |
| on_member_join | listener | disbot/cogs/security_cog.py:46 | | | |
| cog_load (register_schemas) | listener/setup-hook | disbot/cogs/security_cog.py:39 | | | |
| build_help_menu_view | panel/help-hook | disbot/cogs/security_cog.py:120 | | | |
| _policy_embed | panel (status embed) | disbot/cogs/security_cog.py:57 | | | |
| security.enabled | setting | disbot/cogs/security/schemas.py:97 | | | |
| security.alert_channel | setting | disbot/cogs/security/schemas.py:108 | | | |
| security.raid_enabled | setting | disbot/cogs/security/schemas.py:120 | | | |
| security.raid_join_count | setting | disbot/cogs/security/schemas.py:128 | | | |
| security.raid_window_seconds | setting | disbot/cogs/security/schemas.py:139 | | | |
| security.raid_slowmode_channel | setting | disbot/cogs/security/schemas.py:150 | | | |
| security.raid_slowmode_seconds | setting | disbot/cogs/security/schemas.py:161 | | | |
| security.raid_lockdown_seconds | setting | disbot/cogs/security/schemas.py:172 | | | |
| security.age_enabled | setting | disbot/cogs/security/schemas.py:184 | | | |
| security.age_min_days | setting | disbot/cogs/security/schemas.py:192 | | | |
| security.age_action | setting | disbot/cogs/security/schemas.py:202 | | | |
| security.raid_detected | event | disbot/services/security_service.py:45 | | | |
| security.account_flagged | event | disbot/services/security_service.py:46 | | | |
| SUBSYSTEMS["security"] entry (capability security.settings.configure) | setting-registry entry | disbot/utils/subsystem_registry.py:705 | | | |

**Unit kinds present:** command, listener, panel, setting, event, setting-registry entry
**Structural-pattern flags:** gateway (@commands.Cog.listener on_member_join, member-join screening) listener; scheduled/delayed lockdown-lift via asyncio (services/security_service.py `_hold_then_lift`/`_clear_lock_after`, timer not a cron loop); no stateful game loop, no wait_for wizard, no voice. No dedicated DB table/store — settings are legacy scalar KV only (schema comment confirms "no migration").


---

### cleanup
_cogs: disbot/cogs/cleanup_cog.py, disbot/cogs/cleanup/panel.py, disbot/cogs/cleanup/schemas.py_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !cleanuphistory | command | cogs/cleanup_cog.py:325 | | | |
| !word (group, invoke_without_command) | command | cogs/cleanup_cog.py:488 | | | |
| !word add | command | cogs/cleanup_cog.py:502 | | | |
| !word remove | command | cogs/cleanup_cog.py:521 | | | |
| !word list | command | cogs/cleanup_cog.py:540 | | | |
| !wordmenu | command | cogs/cleanup_cog.py:554 | | | |
| !cleanup | command | cogs/cleanup_cog.py:563 | | | |
| on_guild_remove | listener | cogs/cleanup_cog.py:317 (@commands.Cog.listener) | | | purges cleanup state on guild removal ⚠ unverified detail |
| CleanupStage (message-pipeline stage) | listener | cogs/cleanup_cog.py:97 | | | auto-mod tier stage order=10, runs remove_unwanted_message |
| _WordMenuView | panel | cogs/cleanup_cog.py:638 | | | HubView for word-list add/remove/menu |
| _AddWordModal | panel | cogs/cleanup_cog.py:592 | | | modal collecting a prohibited word to add |
| _RemoveWordModal | panel | cogs/cleanup_cog.py:615 | | | modal collecting a prohibited word to remove |
| _ScanHistoryModal | panel | cogs/cleanup_cog.py:710 | | | modal for channel-history scan params |
| CleanupPanelView | panel | cogs/cleanup/panel.py:122 | | | HubView entry panel for cleanup subsystem |
| CleanupPolicyPanelView | panel | views/cleanup/policy_panel.py:702 | | | HubView for per-scope cleanup-level policy config |
| _CustomLevelView | panel | views/cleanup/policy_panel.py:448 | | | BaseView for custom cleanup-level configuration |
| _ConfirmApplyView | panel | views/cleanup/policy_panel.py:541 | | | BaseView confirming policy apply |
| _ScopeSelect / _CategoryPickSelect / _ChannelPickSelect / _LevelSelect / _DeleteAfterSelect / _CustomYesNoSelect / _RemoveSelect | panel (select components) | views/cleanup/policy_panel.py:233,271,294,317,386,410,640 | | | scope/category/channel/level/delete-after/remove select widgets inside policy panel |
| _CustomPreviewButton | panel | views/cleanup/policy_panel.py:435 | | | button previewing a custom cleanup level |
| cleanup_spam_window_seconds | setting | utils/settings_keys/cleanup.py:20 | | | scalar KV setting: !cleanuphistory duplicate-message window (default 15s) |
| cleanup capabilities (cleanup.word.add / cleanup.word.remove / cleanup.history.scan / cleanup.policy.configure) | setting | utils/subsystem_registry.py:509-514 | | | declared capability list in SUBSYSTEMS["cleanup"] |
| cleanup_policies (table) | store | migrations/004_governance_tables.sql:24 | | | per-scope cleanup behavior overrides, governance-owned |
| cleanup_policies.policy_version (column) | store | migrations/058_cleanup_policy_version.sql:29 | | | additive version marker, behavior-neutral |
| wordfilter_config (table) | store | migrations/097_wordfilter_strict.sql:27 | | | prohibited-word list + strict-mode config, ⚠ unverified column detail |
| governance/cleanup.py resolver | event/other | governance/cleanup.py | | | resolves effective cleanup policy per scope ⚠ unverified — not read in full |

**Unit kinds present:** command, panel, setting, listener, store
**Structural-pattern flags:** gateway listener (`@commands.Cog.listener` on_guild_remove; `CleanupStage` message-pipeline hook acting like an inline gateway filter); wizard-style modal chain (`_AddWordModal`/`_RemoveWordModal`/`_ScanHistoryModal`) but no `wait_for`-based wizard found; no stateful game loop; no scheduled loop found; no voice.

---

### role
_cogs: disbot/cogs/role_cog.py, disbot/cogs/role_grants_cog.py_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !roles | command | disbot/cogs/role_cog.py:354 | | | |
| !rolesettings | command | disbot/cogs/role_cog.py:369 | | | |
| !roleinfo | command | disbot/cogs/role_cog.py:375 | | | |
| !rolemenu | command | disbot/cogs/role_cog.py:414 | | | |
| !rolecreator | command | disbot/cogs/role_cog.py:423 | | | |
| !assignroles | command | disbot/cogs/role_cog.py:433 | | | |
| !createrole | command | disbot/cogs/role_cog.py:444 | | | |
| !deleterole | command | disbot/cogs/role_cog.py:483 | | | |
| !setrole | command | disbot/cogs/role_cog.py:504 | | | |
| !unsetrole | command | disbot/cogs/role_cog.py:537 | | | |
| !debugroles | command | disbot/cogs/role_cog.py:567 | | | |
| !refreshmembers | command | disbot/cogs/role_cog.py:578 | | | |
| !reactroles (alias !reaktionsrollen) | command | disbot/cogs/role_cog.py:651 | | | |
| !removereactrole | command | disbot/cogs/role_cog.py:689 | | | |
| !listreactroles | command | disbot/cogs/role_cog.py:709 | | | |
| !temprole | command | disbot/cogs/role_grants_cog.py:63 | | | |
| !temproles | command | disbot/cogs/role_grants_cog.py:106 | | | |
| RoleHubView | panel | disbot/views/roles/main_panel.py:11 | | | |
| ManagementPanel (+ _EditRolePickView/_DeleteRolesView/_ConfirmDeleteView) | panel | disbot/views/roles/management_panel.py:18 | | | |
| RoleCreatePanel / RoleAutomationView | panel | disbot/views/roles/creation_panel.py:63,312 | | | |
| DiagnosticsPanel | panel | disbot/views/roles/diagnostics_panel.py:36 | | | |
| RoleExemptionsPanel | panel | disbot/views/roles/exemptions_panel.py:23 | | | |
| ReactionRolesPanel (+ _AddSourceView/_BindEmotesView/_AfterBindView) | panel | disbot/views/roles/reaction_panel.py:48 | | | |
| RoleMenuListView / RoleMenuBuilder (+ sub-pick views) | panel | disbot/views/roles/role_menu_builder.py:94,449 | | | |
| RoleMenuView (persistent published menu) | panel | disbot/views/roles/role_menu_view.py:232 | | | |
| TimeRolesPanel (+ _TempRolesView/_TimeRolePickView) | panel | disbot/views/roles/time_roles_panel.py:31 | | | |
| XpRolesPanel (+ _XpRolePickView) | panel | disbot/views/roles/xp_roles_panel.py:23 | | | |
| RolePackView (+ _BulkColourView/_PerRoleColourView) | panel | disbot/views/roles/_role_pack_flow.py:66 | | | |
| setting: time_roles_stack | setting | disbot/cogs/role/schemas.py:34 | | | |
| setting: xp_roles_stack | setting | disbot/cogs/role/schemas.py:46 | | | |
| setting: reaction_roles_enabled | setting | disbot/cogs/role/schemas.py:58 | | | |
| role_check (24h loop, time/XP auto-assignment) | scheduled loop | disbot/cogs/role_cog.py:284 | | | |
| _sweep_loop (temp-role expiry sweep) | scheduled loop | disbot/cogs/role_grants_cog.py:42 | | | |
| on_raw_reaction_add (reaction-role grant) | listener | disbot/cogs/role_cog.py:591 | | | |
| on_raw_reaction_remove (reaction-role revoke) | listener | disbot/cogs/role_cog.py:616 | | | |
| on_member_join (tenure/xp role backfill check) | listener | disbot/cogs/role_cog.py:731 | | | |
| emit_audit_action (role grant/revoke, automation) | event | disbot/services/role_automation.py:660,684,747,799,856,900 | | | |
| emit_audit_action (reaction role bind/remove) | event | disbot/services/reaction_role_service.py:865,891,919 | | | |
| store: role_thresholds (tenure/XP thresholds) | store | disbot/utils/db/roles.py:19-149 | | | |
| store: role_automation_exemptions | store | disbot/utils/db/roles.py:160 ⚠ unverified table name from docstring | | | |
| store: reaction_roles | store | disbot/utils/db/roles.py:201-260 | | | |
| store: reaction role message modes | store | disbot/utils/db/roles.py:262-303 | | | |

**Unit kinds present:** command, panel, setting, listener, event, store, scheduled loop
**Structural-pattern flags:** scheduled loop (role_check 24h, temp-role sweep loop); gateway listener (on_raw_reaction_add/remove, on_member_join) driving role grant/revoke; no stateful game loop, no wait_for wizard observed, no voice.


---

### channel
_cogs: disbot/cogs/channel_cog.py_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !channelmenu | command | disbot/cogs/channel_cog.py:192 | | | |
| !set | command | disbot/cogs/channel_cog.py:210 | | | |
| !evt | command | disbot/cogs/channel_cog.py:233 | | | |
| !create | command | disbot/cogs/channel_cog.py:278 | | | |
| !bulkdelete | command | disbot/cogs/channel_cog.py:329 | | | |
| !del | command | disbot/cogs/channel_cog.py:380 | | | |
| !list | command | disbot/cogs/channel_cog.py:405 | | | |
| !clone | command | disbot/cogs/channel_cog.py:437 | | | |
| !move | command | disbot/cogs/channel_cog.py:470 | | | |
| !lock | command | disbot/cogs/channel_cog.py:498 | | | |
| !unlock | command | disbot/cogs/channel_cog.py:514 | | | |
| !channelinfo | command | disbot/cogs/channel_cog.py:531 | | | |
| !rename | command | disbot/cogs/channel_cog.py:570 | | | |
| !slowmode | command | disbot/cogs/channel_cog.py:598 | | | |
| !topic | command | disbot/cogs/channel_cog.py:641 | | | |
| !permissions | command | disbot/cogs/channel_cog.py:673 | | | |
| !bulkcreate | command | disbot/cogs/channel_cog.py:704 | | | |
| _ChannelManagerView (main hub panel) | panel/view | disbot/views/channels/main_panel.py:22 | | | HubView subclass, entry point for !channelmenu |
| _CreateSubView | panel/view | disbot/views/channels/create_panel.py:41 | | | BaseView subclass for channel creation flow |
| _DeleteSubView | panel/view | disbot/views/channels/delete_panel.py:38 | | | BaseView subclass for channel deletion flow |
| _DeleteConfirmView | panel/view | disbot/views/channels/delete_panel.py:178 | | | BaseView confirmation sub-panel for delete |
| _ChannelListPaginatorView | panel/view | disbot/views/channels/list_panel.py:118 | | | ⚠ extends discord.ui.View directly, not BaseView (documented exception) |
| _MoveSubView | panel/view | disbot/views/channels/move_panel.py:80 | | | BaseView subclass for move-channel flow |
| _RestrictSubView | panel/view | disbot/views/channels/restrict_panel.py:34 | | | BaseView subclass for access-restriction flow |
| _VisibilitySubView | panel/view | disbot/views/channels/visibility_panel.py:39 | | | BaseView subclass for visibility toggle flow |
| _SubsystemToggleView | panel/view | disbot/views/channels/visibility_panel.py:181 | | | BaseView subclass toggling subsystem visibility |
| channel.create.text | capability/setting | disbot/utils/subsystem_registry.py:485 | | | SUBSYSTEMS["channel"] capability entry |
| channel.create.voice | capability/setting | disbot/utils/subsystem_registry.py:486 | | | SUBSYSTEMS["channel"] capability entry |
| channel.delete.any | capability/setting | disbot/utils/subsystem_registry.py:487 | | | SUBSYSTEMS["channel"] capability entry |
| channel.restrict.apply | capability/setting | disbot/utils/subsystem_registry.py:488 | | | SUBSYSTEMS["channel"] capability entry |
| channel.visibility.configure | capability/setting | disbot/utils/subsystem_registry.py:489 | | | SUBSYSTEMS["channel"] capability entry |
| entry_point: channelmenu | setting (registry) | disbot/utils/subsystem_registry.py:474 | | | entry_points list for subsystem registry card |

**Unit kinds present:** command, panel, setting (capability/registry entry)
**Structural-pattern flags:** none obvious — no `@bot.event`/`bus.on` listener, no `bus.emit`/`emit_audit_action` call found in channel_cog.py or disbot/views/channels/*, no `wait_for` wizard, no scheduled loop, no voice handling, and no dedicated `*_mutation.py` or DB table found under `utils/db/` for this subsystem (⚠ unverified — no channel-specific store/settings-key module located; channel commands appear to act directly on Discord guild objects rather than through a persisted store).


---

### welcome
_cogs: disbot/cogs/welcome_cog.py, disbot/cogs/welcome/schemas.py (services: disbot/services/welcome_service.py, disbot/services/welcome_config.py)_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !welcome | command | disbot/cogs/welcome_cog.py:162 | | | |
| on_member_join | listener | disbot/cogs/welcome_cog.py:47 | | | |
| on_member_remove | listener | disbot/cogs/welcome_cog.py:56 | | | |
| welcome.member_greeted | event | disbot/services/welcome_service.py:267-271 (EVT_WELCOME_MEMBER_GREETED, emitted from handle_member_join) | | | |
| build_help_menu_view (help-dropdown hook, read-only policy embed) | panel/view | disbot/cogs/welcome_cog.py:167-185 | | | |
| _policy_embed (policy summary embed builder used by !welcome and help view) | panel/view | disbot/cogs/welcome_cog.py:66-153 | | | |
| enabled (master switch) | setting | disbot/cogs/welcome/schemas.py:145-155 (WELCOME_ENABLED) | | | |
| join_enabled | setting | disbot/cogs/welcome/schemas.py:156-163 (WELCOME_JOIN_ENABLED) | | | |
| leave_enabled | setting | disbot/cogs/welcome/schemas.py:164-171 (WELCOME_LEAVE_ENABLED) | | | |
| channel | setting | disbot/cogs/welcome/schemas.py:172-183 (WELCOME_CHANNEL) | | | |
| join_message | setting | disbot/cogs/welcome/schemas.py:184-195 (WELCOME_JOIN_MESSAGE) | | | |
| leave_message | setting | disbot/cogs/welcome/schemas.py:196-207 (WELCOME_LEAVE_MESSAGE) | | | |
| entry_role | setting | disbot/cogs/welcome/schemas.py:208-219 (WELCOME_ENTRY_ROLE) | | | |
| card_enabled | setting | disbot/cogs/welcome/schemas.py:220-230 (WELCOME_CARD_ENABLED) | | | |
| dm_enabled | setting | disbot/cogs/welcome/schemas.py:231-242 (WELCOME_DM_ENABLED) | | | |
| dm_message | setting | disbot/cogs/welcome/schemas.py:243-254 (WELCOME_DM_MESSAGE) | | | |
| min_account_age_days | setting | disbot/cogs/welcome/schemas.py:255-267 (WELCOME_MIN_ACCOUNT_AGE_DAYS) | | | |
| delete_after_seconds | setting | disbot/cogs/welcome/schemas.py:268-279 (WELCOME_DELETE_AFTER_SECONDS) | | | |
| register_schemas (registers WELCOME_CONFIG_SCHEMA on cog_load) | setting (registration) | disbot/cogs/welcome_cog.py:39-42 | | | |
| entry-role grant (via moderation's audited role path, per schema hint) | ⚠ unverified capability | disbot/cogs/welcome/schemas.py:213-215 (hint text only; grant call not located in this pass) | | | |
| welcome subsystem registry entry (entry_points, capability tag "welcome.settings.configure") | subsystem-registry | disbot/utils/subsystem_registry.py:649-668 | | | |
| store: no dedicated welcome table found — all settings are scalar guild-settings KV (legacy `settings` table), not a migration-owned table | store | ⚠ unverified — grep of disbot/utils/db and migrations found no welcome-specific table | | | |

**Unit kinds present:** command, panel/view, setting, listener, event, subsystem-registry entry. No dedicated `store` (table) or `help_catalogue` entries found for welcome.

**Structural-pattern flags:** gateway/listener pattern (`@commands.Cog.listener()` on `on_member_join`/`on_member_remove`, `discord.py` event dispatch) — no stateful game loop, no `wait_for` wizard, no scheduled loop, no voice.

---

### ticket
_cogs: disbot/cogs/ticket_cog.py_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !ticket | command (group) | disbot/cogs/ticket_cog.py:135 | | | |
| !ticket new (aliases: open, create) | command (subcommand) | disbot/cogs/ticket_cog.py:141 | | | |
| !ticket close | command (subcommand) | disbot/cogs/ticket_cog.py:155 | | | |
| !ticket claim | command (subcommand) | disbot/cogs/ticket_cog.py:179 | | | |
| !ticket add | command (subcommand) | disbot/cogs/ticket_cog.py:195 | | | |
| !ticket remove | command (subcommand) | disbot/cogs/ticket_cog.py:211 | | | |
| !ticketpanel | command (prefix) | disbot/cogs/ticket_cog.py:238 | | | |
| !ticketsetup | command (prefix) | disbot/cogs/ticket_cog.py:245 | | | |
| !ticketlimit | command (prefix) | disbot/cogs/ticket_cog.py:277 | | | |
| !ticketblacklist | command (group) | disbot/cogs/ticket_cog.py:289 | | | |
| !ticketblacklist add | command (subcommand) | disbot/cogs/ticket_cog.py:294 | | | |
| !ticketblacklist remove | command (subcommand) | disbot/cogs/ticket_cog.py:310 | | | |
| TicketLauncherView | panel/view | disbot/views/tickets/launcher.py:19 | | | |
| post_launcher() | panel/view | disbot/views/tickets/launcher.py:42 | | | |
| TicketControlView | panel/view | disbot/views/tickets/control.py:63 | | | |
| build_control_view() | panel/view | disbot/views/tickets/control.py:144 | | | |
| TicketCloseModal | panel/view (modal) | disbot/views/tickets/control.py:24 | | | |
| TicketConfirmView | panel/view | disbot/views/tickets/confirm.py:22 | | | |
| TicketOpenModal | panel/view (modal) | disbot/views/tickets/_shared.py:72 | | | |
| TicketHubView | panel/view | disbot/views/tickets/hub.py:63 | | | |
| open_ticket_hub() | panel/view | disbot/views/tickets/hub.py:137 | | | |
| TicketConfigPanelView | panel/view | disbot/views/tickets/config_panel.py:123 | | | |
| open_ticket_config_panel() | panel/view | disbot/views/tickets/config_panel.py:268 | | | |
| _StaffRoleSelect | panel/view (component) | disbot/views/tickets/config_panel.py:88 | | | |
| _LogChannelSelect | panel/view (component) | disbot/views/tickets/config_panel.py:105 | | | |
| build_help_menu_view() | help | disbot/cogs/ticket_cog.py:329 | | | |
| ticket.ticket.open (capability/entry) | setting | disbot/utils/subsystem_registry.py:254 | | | |
| ticket.ticket.manage (capability) | setting | disbot/utils/subsystem_registry.py:255 | | | |
| ticket.config.update (capability) | setting | disbot/utils/subsystem_registry.py:256 | | | |
| ticket_config row (staff_role/log_channel/max_open/ping_staff/enabled) | setting | disbot/utils/db/tickets.py:44 | | | |
| bus.on("ticket.opened") → _on_ticket_opened | listener | disbot/cogs/ticket_cog.py:57 | | | |
| bus.on("ticket.open_requested") → _on_ticket_open_requested | listener | disbot/cogs/ticket_cog.py:58 | | | |
| bus.emit("ticket.opened") | event | disbot/services/ticket_mutation.py:200 | | | |
| bus.emit("ticket.closed") | event | disbot/services/ticket_mutation.py:331 | | | |
| bus.emit("ticket.open_requested") (from AI tool) | event | disbot/services/ai_tools.py:2494 | | | |
| emit_audit_action mutation_type="open" | event | disbot/services/ticket_mutation.py:194 | | | |
| emit_audit_action mutation_type="claim" | event | disbot/services/ticket_mutation.py:289 | | | |
| emit_audit_action mutation_type="close" | event | disbot/services/ticket_mutation.py:326 | | | |
| emit_audit_action mutation_type="add_participant" | event | disbot/services/ticket_mutation.py:422 | | | |
| emit_audit_action mutation_type="remove_participant" | event | disbot/services/ticket_mutation.py:448 | | | |
| emit_audit_action mutation_type="config" | event | disbot/services/ticket_mutation.py:562 | | | |
| emit_audit_action mutation_type="blacklist" | event | disbot/services/ticket_mutation.py:593 | | | |
| ticket_config table | store | disbot/migrations/098_tickets.sql:23 | | | |
| tickets table | store | disbot/migrations/098_tickets.sql:46 | | | |
| ticket_blacklist table | store | disbot/migrations/098_tickets.sql:78 | | | |
| ticket_* CRUD functions (get_config/upsert_config/create/get/get_by_channel/count_open_for_user/list_for_user/list_open/set_claim/close/is_blacklisted/add_blacklist/remove_blacklist) | store | disbot/utils/db/tickets.py:28 | | | |

**Unit kinds present:** command, panel, setting, listener, event, store, help

**Structural-pattern flags:** gateway/bus.on listener present (`bus.on("ticket.opened")`, `bus.on("ticket.open_requested")` in `TicketCog.cog_load`, disbot/cogs/ticket_cog.py:57-58); no stateful game loop, no wait_for wizard, no scheduled loop, no voice.
