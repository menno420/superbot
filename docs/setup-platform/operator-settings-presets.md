# Operator Settings & Provisioning Presets

> **Status:** `living-ledger` — Reference only

Scope: Future Settings Manager, Resource Provisioning, Cleanup, Logging, Access, Setup Wizard, and Help/Menu UX  
Runtime impact: None  
Owner intent: Capture preferred operator defaults and safe presets before UI/setup implementation begins.

This document records preferred defaults, naming conventions, safe setup presets, and expected UX behavior for future SuperBot configuration work.

It is not a binding architecture contract. The authoritative implementation remains the Global Settings & Customization Manager roadmap and the platform services it defines:

- `SettingsRegistry`
- `SettingsResolution`
- `SettingsMutationPipeline`
- `BindingMutationPipeline`
- `ResourceProvisioningCatalogue`
- `ResourceProvisioningPipeline`
- future Settings Manager views
- future Cleanup Policy Manager
- future Access Policy Manager
- future Setup Wizard

## Core safety rules

### No silent auto-create

SuperBot should never silently create Discord channels, roles, categories, or threads.

Resource creation must happen only through one of these explicit flows:

- confirmed Settings Manager action;
- confirmed Setup Wizard action;
- confirmed subsystem setup-pack action;
- explicit operator command that clearly says it will create resources.

Startup must never auto-create resources.

### Create/reuse flow

Every resource-binding UI should offer:

- choose existing resource;
- create new resource;
- use standard suggested name;
- use custom name;
- choose category where applicable;
- choose permission template where applicable;
- preview before applying;
- explicit confirmation before creation.

### Ownership boundaries

- Scalar settings are changed through `SettingsMutationPipeline`.
- Discord resource pointers are changed through `BindingMutationPipeline`.
- Discord resource creation is handled by `ResourceProvisioningPipeline`.
- Access policies use governance scope-chain logic.
- Cleanup lists/policies use cleanup policy/list services.
- Setup Wizard consumes these systems; it must not directly edit cog internals.

## Standard category presets

These names are suggestions. The final UI should always allow selecting an existing category or entering a custom category name.

### General bot categories

- `SuperBot`
- `SuperBot Setup`
- `SuperBot Logs`
- `SuperBot Admin`
- `Bot Commands`
- `Server Management`
- `Community`
- `Games`
- `Economy`
- `Moderation`
- `Staff`
- `Archive`

### Recommended category descriptions

| Category | Purpose |
|---|---|
| `SuperBot` | General bot-created channels and panels. |
| `SuperBot Setup` | Temporary setup wizard or setup checklist channels. |
| `SuperBot Logs` | Moderation, cleanup, economy, audit, and diagnostic logs. |
| `SuperBot Admin` | Admin-only bot controls and settings panels. |
| `Bot Commands` | Public command/panel channels. |
| `Games` | Game commands and game-specific panels. |
| `Economy` | Economy, shop, inventory, trading, rewards. |
| `Moderation` | Staff-only moderation and cleanup controls. |
| `Archive` | Optional destination for old generated channels. |

## Standard channel-name presets

### Platform and admin

| Purpose | Suggested names |
|---|---|
| Admin control channel | `bot-admin`, `superbot-admin`, `admin-bot-controls` |
| Setup channel | `bot-setup`, `superbot-setup`, `setup-wizard` |
| Bot command channel | `bot-commands`, `commands`, `superbot` |
| Platform diagnostics | `bot-diagnostics`, `platform-status`, `bot-health` |
| Settings panel | `bot-settings`, `settings`, `server-settings` |

### Logging

| Purpose | Suggested names |
|---|---|
| General moderation logs | `mod-logs`, `moderation-logs`, `staff-logs` |
| Cleanup logs | `cleanup-logs`, `auto-delete-logs`, `filter-logs` |
| Economy logs | `economy-log`, `economy-logs`, `transaction-logs` |
| Runtime logs | `bot-runtime`, `runtime-logs`, `bot-events` |
| Audit logs | `audit-log`, `settings-audit`, `bot-audit` |
| Critical alerts | `critical-alerts`, `bot-critical`, `urgent-logs` |
| Debug logs | `debug-logs`, `bot-debug`, `dev-logs` |

### Log-level route names

These are future route presets. They should not replace v1 `mod_channel` / `cleanup_channel` bindings.

- `log-channel-debug`
- `log-channel-info`
- `log-channel-warning`
- `log-channel-error`
- `log-channel-critical`

Recommended future route model:

| Route | Suggested channel | Notes |
|---|---|---|
| `moderation.info` | `mod-logs` | Normal moderation actions. |
| `cleanup.info` | `cleanup-logs` | Auto-delete and filter actions. |
| `runtime.warning` | `bot-runtime` | Non-fatal runtime warnings. |
| `runtime.error` | `bot-critical` | Errors requiring operator attention. |
| `settings.audit` | `settings-audit` | Settings changes and provisioning actions. |
| `economy.info` | `economy-logs` | Economy/admin transaction logs. |

### XP and leaderboard

| Purpose | Suggested names |
|---|---|
| Level-up announcements | `level-ups`, `xp-levels`, `rank-ups` |
| XP commands | `xp`, `levels`, `rank` |
| Leaderboards | `leaderboards`, `server-rankings`, `top-members` |

### Cleanup

| Purpose | Suggested names |
|---|---|
| Cleanup control panel | `cleanup-settings`, `filter-settings`, `moderation-cleanup` |
| Cleanup logs | `cleanup-logs`, `filter-logs`, `auto-delete-logs` |
| Prohibited-word review | `word-filter`, `blocked-words`, `filter-review` |
| Cleanup testing | `cleanup-test`, `filter-test`, `mod-test` |

### Roles

| Purpose | Suggested names |
|---|---|
| Role menu | `role-menu`, `self-roles`, `roles` |
| Reaction roles | `reaction-roles`, `role-reactions`, `pick-roles` |
| Role admin | `role-admin`, `role-settings`, `role-management` |

### Economy and inventory

| Purpose | Suggested names |
|---|---|
| Economy commands | `economy`, `coins`, `money` |
| Shop | `shop`, `market`, `store` |
| Inventory | `inventory`, `items`, `backpack` |
| Economy logs | `economy-logs`, `transaction-logs`, `coin-logs` |
| Trading | `trading`, `marketplace`, `trade-hub` |

### Games

| Purpose | Suggested names |
|---|---|
| Games hub | `games`, `game-room`, `play` |
| Blackjack | `blackjack`, `casino`, `cards` |
| RPS | `rps`, `rock-paper-scissors`, `rps-arena` |
| Deathmatch | `deathmatch`, `arena`, `battle` |
| Game tournaments | `tournaments`, `events`, `competition` |

### Counting and chain

| Purpose | Suggested names |
|---|---|
| Counting | `counting`, `count-to-infinity`, `numbers` |
| Chain | `chain`, `word-chain`, `message-chain` |
| Counting logs | `counting-logs`, `counting-admin`, `counting-review` |

### Mining

| Purpose | Suggested names |
|---|---|
| Mining commands | `mining`, `mine`, `mining-hub` |
| Mining panel | `mining-panel`, `mining-menu`, `mine-menu` |
| Mining logs | `mining-logs`, `mine-logs`, `resource-logs` |

### Proof channel

| Purpose | Suggested names |
|---|---|
| Proof submissions | `proof-submissions`, `proofs`, `submit-proof` |
| Proof review | `proof-review`, `staff-proof-review`, `proof-queue` |
| Approved proof archive | `approved-proofs`, `proof-archive`, `verified-proof` |

### Welcome/general

| Purpose | Suggested names |
|---|---|
| Welcome | `welcome`, `start-here`, `introductions` |
| Rules | `rules`, `server-rules`, `guidelines` |
| Announcements | `announcements`, `updates`, `news` |
| General bot panel | `bot-panel`, `server-panel`, `community-panel` |

## Standard role-name presets

### Admin/staff roles

- `Bot Admin`
- `SuperBot Admin`
- `Server Admin`
- `Moderator`
- `Helper`
- `Staff`
- `Trusted Staff`
- `Trial Moderator`

### Bot/system roles

- `SuperBot`
- `Bot Managed`
- `Bot Muted`
- `Bot Ignored`
- `No XP`
- `XP Exempt`
- `Cleanup Exempt`
- `Filter Exempt`
- `Economy Exempt`
- `Game Exempt`

### User-facing roles

- `Member`
- `Verified`
- `Trusted`
- `Active Member`
- `VIP`
- `Booster`
- `Event Participant`
- `Tournament Player`

### Level roles

- `Level 5`
- `Level 10`
- `Level 25`
- `Level 50`
- `Level 100`
- `Veteran`
- `Elite`
- `Legend`

### Economy roles

- `Rich`
- `Trader`
- `Shopkeeper`
- `Investor`
- `Miner`
- `Collector`

### Game roles

- `Gamer`
- `Champion`
- `Tournament Winner`
- `Arena Player`
- `Blackjack Player`
- `RPS Player`

## Permission template presets

These are conceptual templates for `ResourceProvisioningPipeline` / setup-pack UI. Exact Discord overwrites should be implemented carefully later.

### Public bot command channel

Intent: Users can run safe public commands.

Suggested overwrites:

- everyone: view channel, send messages, read history;
- bot: view channel, send messages, manage messages if needed;
- staff: manage messages;
- no admin-only controls visible here.

### Admin bot control channel

Intent: Bot owner/admin settings and diagnostics.

Suggested overwrites:

- everyone: no view;
- admin/staff role: view channel, send messages, read history;
- bot: view channel, send messages, embed links, manage messages.

### Log channel

Intent: Bot writes logs; normal users cannot post.

Suggested overwrites:

- everyone: no send messages; optionally no view for staff-only logs;
- staff: view channel, read history;
- bot: view channel, send messages, embed links, attach files if needed.

### Setup wizard channel

Intent: Temporary or controlled setup flow.

Suggested overwrites:

- everyone: no send messages or no view, depending on server preference;
- server owner/admin: view channel, interact;
- bot: view channel, send messages, manage messages.

### Role menu channel

Intent: Users can interact with role menus but not clutter the channel.

Suggested overwrites:

- everyone: view channel, read history, use application commands/interactions;
- everyone: no send messages if using only buttons/selects;
- bot: send messages, manage messages.

### Game channel

Intent: Public games with normal message permissions.

Suggested overwrites:

- everyone: view channel, send messages, read history;
- bot: view channel, send messages, manage messages as needed;
- staff: manage messages.

### Proof submission channel

Intent: Users submit proof; staff reviews.

Suggested overwrites:

- everyone: view/send if public proof submissions are desired;
- or user-only create thread/post model later;
- staff: manage messages, read all submissions;
- bot: manage messages, create threads if enabled.

## Setup-pack presets

Setup packs should be guided bundles that create or bind multiple resources. Every pack should show a preview and require confirmation before creating anything.

### Minimal setup pack

Purpose: Basic bot operation without heavy configuration.

Includes:

- bot command channel;
- admin/settings channel;
- platform diagnostics available;
- help menu reachable;
- no optional feature channels created.

Suggested resources:

- `bot-commands`
- `bot-admin`

### Logging setup pack

Purpose: Centralize logs safely.

Includes:

- mod log channel;
- cleanup log channel;
- optional audit/settings log channel later;
- logging enabled toggle;
- auto-create policy confirmation.

Suggested resources:

- `mod-logs`
- `cleanup-logs`
- `settings-audit` later
- `bot-critical` later

Preset modes:

- simple: one `mod-logs` channel for all moderation/cleanup;
- split: `mod-logs` + `cleanup-logs`;
- advanced: debug/info/warning/error/critical routes.

### Cleanup setup pack

Purpose: Configure server safety and cleanup behavior.

Includes:

- cleanup settings page;
- cleanup logging route;
- prohibited words page;
- warning behavior;
- strictness;
- exempt roles;
- ignored channels;
- test/preview cleanup rule.

Suggested resources:

- `cleanup-logs`
- `cleanup-settings`
- `filter-test`

Default safe preset:

- cleanup enabled: false until configured;
- strictness: normal;
- warning messages: enabled;
- warning delete delay: 5–10 seconds;
- command cleanup: enabled only in configured command channels;
- prohibited-word cleanup: enabled only after word list exists.

### XP setup pack

Purpose: Configure XP and leaderboards.

Includes:

- XP min/max;
- cooldown;
- level-up channel;
- XP ignored channels;
- leaderboard visibility;
- optional level roles later.

Suggested resources:

- `level-ups`
- `leaderboards`

Default safe preset:

- XP enabled globally except ignored channels;
- no XP in staff/log/setup channels;
- announce channel optional;
- leaderboard public unless server owner chooses private.

### Role setup pack

Purpose: Configure self-roles and role automation.

Includes:

- role menu channel;
- self-role categories;
- default role;
- skip roles;
- maximum self-roles;
- reaction-role bridge later;
- XP role integration later.

Suggested resources:

- `role-menu`
- `role-admin`

Default safe preset:

- role menu created but no roles assigned until admin configures them;
- self-role enabled only after at least one category exists;
- no automatic default-role assignment unless explicitly enabled.

### Economy setup pack

Purpose: Configure money/rewards/trading safely.

Includes:

- economy enabled toggle;
- economy log channel;
- starting balance;
- daily/work rewards;
- cooldowns;
- transfer limits;
- gambling integration toggle;
- shop/inventory pages.

Suggested resources:

- `economy`
- `shop`
- `inventory`
- `economy-logs`

Default safe preset:

- economy enabled: off until configured;
- transfers enabled only after limits are set;
- economy logs strongly recommended.

### Games setup pack

Purpose: Configure game channels and economy integration.

Includes:

- games category;
- blackjack channel;
- RPS channel;
- deathmatch channel;
- tournament channel;
- min/max bet where relevant;
- cooldowns;
- economy integration toggle.

Suggested resources:

- `games`
- `blackjack`
- `rps`
- `deathmatch`
- `tournaments`

Default safe preset:

- game commands restricted to game channels;
- economy integration disabled until economy is configured.

### Counting setup pack

Purpose: Configure counting gameplay.

Includes:

- counting channel;
- reset behavior;
- failure behavior;
- turn-taking;
- invalid-message cleanup;
- leaderboard visibility.

Suggested resources:

- `counting`
- `counting-logs`

Default safe preset:

- counting restricted to one channel;
- invalid count cleanup enabled if Cleanup is configured;
- leaderboard public by default.

### Chain setup pack

Purpose: Configure chain/word-chain gameplay.

Includes:

- chain channel;
- chain rules;
- reset behavior;
- strictness;
- invalid-message cleanup;
- word constraints.

Suggested resources:

- `chain`
- `chain-logs`

Default safe preset:

- one active chain channel;
- strictness normal;
- cleanup integration optional.

### Mining setup pack

Purpose: Configure mining feature.

Includes:

- mining command channel;
- mining panel;
- cooldown;
- reward ranges;
- rare drop rates;
- economy integration;
- allowed channels.

Suggested resources:

- `mining`
- `mining-panel`
- `mining-logs`

Default safe preset:

- mining restricted to mining channel;
- economy integration disabled until economy is configured.

### Proof-channel setup pack

Purpose: Configure proof submission/review flow.

Includes:

- proof submission channel;
- proof review channel or staff view;
- approval role;
- proof format;
- auto-threading later;
- retention/archive.

Suggested resources:

- `proof-submissions`
- `proof-review`
- `approved-proofs`

Default safe preset:

- no auto-approval;
- staff review required;
- proof archive optional.

### Staff/admin setup pack

Purpose: Configure bot operator spaces.

Includes:

- bot admin channel;
- platform diagnostics;
- settings panel;
- access policy panel;
- setup wizard channel.

Suggested resources:

- `bot-admin`
- `bot-settings`
- `platform-status`
- `bot-setup`

Default safe preset:

- restricted to admin/staff;
- no public access.

## Cleanup presets

### Cleanup strictness presets

| Preset | Meaning |
|---|---|
| `off` | Cleanup disabled except manual/admin actions. |
| `light` | Only obvious command cleanup or explicitly configured words. |
| `normal` | Balanced cleanup for commands, configured prohibited words, and warnings. |
| `strict` | Aggressive cleanup for configured policies; should require preview/testing. |

### Warning presets

| Preset | Suggested behavior |
|---|---|
| `silent` | Delete without warning where allowed. |
| `brief` | Post short warning and delete after 5 seconds. |
| `normal` | Post clear warning and delete after 10 seconds. |
| `educational` | Longer warning explaining the rule, delete after 15–30 seconds. |

### Cleanup channel-policy presets

| Preset | Suggested behavior |
|---|---|
| `inherit` | Use guild/category default. |
| `disabled` | No cleanup in this channel. |
| `commands-only` | Clean bot commands only. |
| `word-filter-only` | Apply prohibited-word cleanup only. |
| `full-cleanup` | Apply all configured cleanup behavior. |
| `staff-exempt` | Cleanup applies, but staff/exempt roles bypass. |
| `announcement-safe` | Disable command/game chatter and cleanup user command attempts. |

### Cleanup ignored-channel suggestions

- rules
- announcements
- staff
- mod-logs
- cleanup-logs
- bot-admin
- bot-setup
- audit-log
- proof-review

These should become typed list/policy storage later, not permanent CSV settings.

## Logging presets

### Logging mode presets

| Preset | Meaning |
|---|---|
| `off` | No server logging. |
| `moderation-only` | Log moderation actions only. |
| `cleanup-only` | Log cleanup/auto-delete actions only. |
| `moderation-and-cleanup` | Separate moderation and cleanup logs. |
| `combined-basic` | One channel for all core logs. |
| `advanced-routes` | Separate routes by event type or severity. |

### Log-level presets

| Level | Intended use |
|---|---|
| `debug` | Developer/troubleshooting only. Usually off. |
| `info` | Normal actions and successful events. |
| `warning` | Recoverable issues, degraded behavior. |
| `error` | Failures requiring attention. |
| `critical` | Severe events requiring quick action. |

### Default logging recommendation

- Start with `moderation-and-cleanup`.
- Use `mod-logs` and `cleanup-logs`.
- Keep debug routes disabled by default.
- Add critical route later if runtime alerts become user-facing.

## Access-policy presets

Access policies must reuse governance scope-chain logic.

### Scope behavior

| Action | Meaning |
|---|---|
| `enable here` | Enable subsystem in this scope. |
| `disable here` | Disable subsystem in this scope. |
| `inherit` | Use parent category/guild setting. |
| `preview` | Show effective policy and source. |
| `explain` | Explain why a command is allowed/blocked. |

### Common access presets

| Preset | Suggested behavior |
|---|---|
| `public-everywhere` | Public subsystem usable everywhere except ignored system channels. |
| `commands-channel-only` | Subsystem usable only in bot command channels. |
| `category-only` | Subsystem usable only in selected category. |
| `staff-only` | Subsystem usable only in staff/admin channels. |
| `disabled-by-default` | Must be explicitly enabled per scope. |
| `games-category-only` | Game cogs enabled only in `Games` category. |
| `economy-safe` | Economy allowed in economy/game channels, disabled in logs/staff/rules. |
| `cleanup-global` | Cleanup applies globally, with explicit ignored scopes. |

### Suggested subsystem access defaults

| Subsystem | Suggested default |
|---|---|
| Admin | staff-only |
| Platform/Diagnostic | staff-only |
| Settings | staff-only |
| Help | public-everywhere |
| XP | public channels, ignored in logs/staff/setup |
| Cleanup | global with ignored scopes |
| Logging | staff-only |
| Economy | commands-channel-only or economy category |
| Games | games-category-only |
| Counting | counting channel only |
| Chain | chain channel only |
| Mining | mining channel/category only |
| Proof Channel | submit/review channels only |
| Role | role menu channel + staff role admin |
| Moderation | staff-only |

## Settings presets by subsystem

### Moderation settings

Potential scalar settings:

- `warn_threshold`
- `warn_timeout_minutes`
- `dm_user_on_action`
- `escalation_enabled`
- `default_timeout_minutes`
- `delete_command_after_action`

Potential bindings:

- `mod_log_channel`
- `moderator_role`
- `muted_role`

### XP settings

Potential scalar settings:

- `xp_min`
- `xp_max`
- `xp_cooldown`
- `level_up_message_enabled`
- `leaderboard_public`
- `xp_enabled`

Potential bindings:

- `announce_channel`
- future `level_role_*`

Potential policies:

- ignored channels;
- ignored roles;
- per-channel XP multiplier later.

### Logging settings

Scalar settings:

- `logging.enabled`
- `logging.auto_create_channels`

Bindings:

- `logging.mod_channel`
- `logging.cleanup_channel`

Future route model:

- `logging_routes`
- level-specific route bindings.

### Cleanup settings

Scalar settings:

- `cleanup.enabled`
- `cleanup.strictness`
- `cleanup.command_cleanup_enabled`
- `cleanup.prohibited_words_enabled`
- `cleanup.warning_enabled`
- `cleanup.warning_delete_delay`
- `cleanup.scan_history_limit`

List/policy settings:

- prohibited words;
- exempt roles;
- exempt users;
- ignored channels;
- channel-specific overrides.

### Role settings

Potential scalar settings:

- `self_roles_enabled`
- `reaction_roles_enabled`
- `max_self_roles`
- `default_role_enabled`
- `xp_roles_enabled`
- `time_roles_enabled`

Potential bindings:

- `role_menu_channel`
- `default_role`

Lists:

- skip roles;
- self-role categories;
- managed role groups.

### Economy settings

Potential scalar settings:

- `economy.enabled`
- `starting_balance`
- `daily_reward`
- `work_min_reward`
- `work_max_reward`
- `daily_cooldown`
- `work_cooldown`
- `transfer_limit`
- `gambling_enabled`

Potential bindings:

- `economy_log_channel`

### Games settings

Potential scalar settings:

- `games.enabled`
- `blackjack.enabled`
- `blackjack.min_bet`
- `blackjack.max_bet`
- `blackjack.cooldown`
- `rps.enabled`
- `deathmatch.enabled`
- `tournaments.enabled`

Potential access policies:

- restrict games to games category;
- staff-only tournament admin.

### Counting settings

Potential scalar settings:

- `counting.enabled`
- `counting.reset_on_fail`
- `counting.delete_invalid`
- `counting.require_turns`
- `counting.leaderboard_public`

Potential bindings:

- `counting_channel`

### Chain settings

Potential scalar settings:

- `chain.enabled`
- `chain.strictness`
- `chain.reset_on_fail`
- `chain.delete_invalid`
- `chain.word_constraints_enabled`

Potential bindings:

- `chain_channel`

### Mining settings

Potential scalar settings:

- `mining.enabled`
- `mining.cooldown`
- `mining.min_reward`
- `mining.max_reward`
- `mining.rare_drop_chance`
- `mining.economy_integration_enabled`

Potential bindings:

- `mining_channel`
- `mining_panel_channel`

### Proof channel settings

Potential scalar settings:

- `proof.enabled`
- `proof.require_format`
- `proof.auto_thread`
- `proof.retention_days`
- `proof.staff_review_required`

Potential bindings:

- `proof_submission_channel`
- `proof_review_channel`
- `approval_role`

## Settings Manager menu expectations

### Main Settings hub

Should show:

- all subsystems;
- needs setup;
- invalid settings;
- missing bindings;
- missing resources;
- access policies;
- cleanup policies;
- logging;
- recent changes/audit;
- setup packs.

### Subsystem page

Should show:

- scalar settings;
- bindings;
- provisionable resources;
- access policy shortcut;
- existing command panel shortcut;
- help page shortcut;
- validation status;
- reset/edit buttons.

### Binding/resource page

Should show:

- current bound resource;
- choose existing;
- create new;
- suggested names;
- custom name;
- category selection;
- permission template;
- preview;
- confirmation.

### Cleanup page

Should show:

- overview;
- guild defaults;
- channel policies;
- prohibited words;
- warnings;
- exemptions;
- history scan;
- test/preview rule;
- logging status.

### Access page

Should show:

- by subsystem;
- by channel;
- by category;
- enable/disable/inherit;
- effective policy preview;
- blocked-command explanation.

## Help/menu expectations

- `!help` should expose Settings, Platform, Admin, Cleanup, Logging, Access, and major cog panels.
- `!adminmenu` should link to Settings, Platform, Logging, Cleanup, Access, and setup flows.
- `!settings` should link to subsystem settings pages and existing cog command panels.
- Cog panels should link back to relevant settings pages.
- Major flows should be button/menu-driven.
- Slash commands should later be limited to front doors:
  - `/help`
  - `/settings`
  - `/adminmenu`
  - `/platform`
  - `/minemenu`

## Setup wizard expectations

The setup wizard should consume:

- SettingsRegistry
- SettingsResolution
- SettingsMutationPipeline
- BindingMutationPipeline
- ResourceProvisioningCatalogue
- ResourceProvisioningPipeline
- AccessPolicyManager
- CleanupPolicyManager
- CustomizationCatalogue

It must not:

- write directly to cog internals;
- create resources directly;
- mutate bindings directly;
- invent its own access-policy system;
- bypass audit/event pipelines.

## Suggested setup wizard modes

### Minimal mode

Only creates or binds the essentials:

- bot command channel;
- admin/settings channel;
- help/admin/platform panels.

### Recommended mode

Configures the most useful defaults:

- logging;
- cleanup;
- XP;
- role menu;
- access policies;
- help discoverability.

### Full mode

Offers all setup packs:

- logging;
- cleanup;
- XP;
- roles;
- economy;
- games;
- counting;
- chain;
- mining;
- proof channel;
- admin/platform.

### Manual mode

Allows choosing each setting/resource one by one.

### Import/reuse mode

Uses existing channels/roles wherever possible and only creates missing resources.

## Manual smoke expectations for future stages

When the relevant stages exist, operator smoke should include:

- choose existing log channel;
- create new log channel with standard name;
- create new log channel with custom name;
- preview provisioning before confirmation;
- deny confirmation and verify no creation;
- remove bot permission and verify safe failure;
- bind created channel and verify audit row;
- edit scalar setting and verify audit row;
- reset scalar setting and verify default;
- configure cleanup strictness and preview rule;
- configure access policy and preview effective result;
- verify `!help` routes to settings/platform/cog panels.

## Deferred / not v1

These should remain later-stage features unless explicitly prioritized:

- web dashboard;
- external log storage;
- Redis;
- multi-process provisioning locks;
- full slash-command migration;
- full setup wizard before Settings Manager is stable;
- automatic resource deletion/cleanup;
- automatic role hierarchy repair;
- advanced log-routing table;
- channel-specific prohibited words, unless cleanup policy storage is ready;
- import/export settings snapshot;
- undo last setting change;
- scheduled cleanup scans;
- cross-guild templates.
