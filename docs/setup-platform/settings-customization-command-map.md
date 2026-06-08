# Settings & Customization Command Map

> **Status:** `living-ledger` — Settings command map; pinned to code by doc-tests.

S0 milestone of the **Global Settings & Customization Manager** roadmap. Maps every loaded
cog and every registered subsystem against a single 24-field template so reviewers,
operators, and future setup-wizard work have one canonical reference.

This is a docs-first milestone: no code, no migrations, no behaviour change.

Sister docs:
- [`docs/setup-platform/settings-customization-roadmap.md`](settings-customization-roadmap.md) — 15-milestone
  roadmap and architecture summary.
- [`docs/setup-platform/resource-provisioning-overview.md`](resource-provisioning-overview.md) — the
  Resource Provisioning Manager (RPM) lane, the 11-step contract, the strict
  no-silent-auto-create rule, and the reserved `logging_routes` future model.

## How to read this doc

Each loaded cog has one section keyed by the canonical **subsystem** name from
`disbot/utils/subsystem_registry.py:SUBSYSTEMS`. Within each section the same 24
fields appear in the same order. Sections are populated as completely as can be
verified by static inspection of source; fields that require a runtime walk of
the command surface are marked **`(deferred to S2 ledger)`** — the ledger work in
the next roadmap milestone (`CustomizationCatalogue`) replaces those stubs with
authoritative content.

Field labels are stable so the resilient doc tests in
`tests/unit/docs/test_settings_customization_doc.py` can assert on them
without depending on bot startup or runtime registry population.

## Field template (24 fields)

1. **cog_module** — file path on disk (e.g. `disbot/cogs/cleanup_cog.py`).
2. **subsystem** — key from `utils.subsystem_registry.SUBSYSTEMS`.
3. **current_commands** — every registered `@commands.command` /
   `@app_commands.command` / `@commands.hybrid_command` discovered via static
   grep of decorators (no bot startup). For groups, subcommands are listed
   alongside the group name.
4. **current_command_groups** — every `@commands.group` / `@app_commands.Group`.
5. **current_command_panel_or_menu** — the `*menu` entrypoint or panel command
   advertised in `entry_points` for this subsystem.
6. **help_menu_discoverable** — does `!help` route to this subsystem (per
   `HelpPanelView.SUBSYSTEM`-aware iteration in `disbot/cogs/help_cog.py`).
7. **dedicated_panel_command** — explicit `@panel_command` decorator or
   `extras={"panel": True}` (post-S2 metadata). `none` if absent.
8. **help_menu_direct_navigation_hook** — does the cog implement
   `build_help_menu_view(interaction)`.
9. **existing_SettingSpec_declarations** — names of every `SettingSpec(...)`
   literal found in the cog's schemas module (static AST scan).
10. **existing_settings_keys** — constants exposed from
    `disbot/utils/settings_keys/<subsystem>.py`.
11. **existing_BindingSpec_entries** — names of every `BindingSpec(...)` literal.
12. **existing_ResourceRequirement_entries** — names of every
    `ResourceRequirement(...)` literal with its `binding_name` cross-link.
13. **current_access_policy_behavior** — `visibility_tier` + capability list
    declared in `SUBSYSTEMS[<name>]`.
14. **hardcoded_or_env_only_behavior** — Python constants, env-var reads, JSON
    file lookups that should become settings.
15. **missing_customization_commands** — admin commands that should exist but
    don't.
16. **missing_settings_pages** — settings hub subpages absent today.
17. **missing_menu_buttons_selects_modals** — specific UI primitives not yet
    wired.
18. **setting_class_per_value** — one of:
    `scalar setting | binding | access policy | list setting |`
    `channel-scoped policy | per-user preference | runtime diagnostic`.
19. **target_Settings_Manager_page** — future page path (e.g.
    `!settings subsystem cleanup`).
20. **target_mutation_path** — one of
    `SettingsMutationPipeline | BindingMutationPipeline |`
    `ResourceProvisioningPipeline | GovernanceMutationPipeline |`
    `ParticipationMutationPipeline`. May list multiple where the subsystem
    spans pipelines.
21. **target_help_or_menu_route** — how a user reaches the page (Help
    direct-nav, Admin button, Platform subcommand, slash front door).
22. **provisionable_resources** — table of
    `(binding_name, kind, priority, suggested_name, suggested_category,`
    `permission_template)` rows derived from items 11+12. `none` if the
    subsystem owns no Discord resource pointers.
23. **priority** — `P0` (first wave), `P1` (soon), `P2` (later).
24. **recommended_PR_phase** — the `S<n>` milestone in which this row first
    becomes actionable.

## Loaded cogs and registered subsystems

The 22 cogs loaded at startup come from `disbot/config.py:INITIAL_EXTENSIONS`.
The 22 subsystems live in `disbot/utils/subsystem_registry.py:SUBSYSTEMS`. The
extra subsystem with no corresponding cog file is `diagnostic` (its
`!diagnostics` + `!platform` surface lives inside
`disbot/cogs/diagnostic_cog.py`).

Cogs (22): `admin_cog`, `blackjack_cog`, `bootstrap_access_cog`,
`chain_cog`, `channel_cog`,
`cleanup_cog`, `counting_cog`, `deathmatch_cog`, `diagnostic_cog`,
`economy_cog`, `general_cog`, `help_cog`, `inventory_cog`, `leaderboard_cog`,
`logging_cog`, `mining_cog`, `moderation_cog`, `proof_channel_cog`,
`role_cog`, `rps_tournament_cog`, `settings_cog`, `setup_cog`,
`utility_cog`, `xp_cog`.

Subsystems (22): `admin`, `moderation`, `economy`, `inventory`, `mining`,
`xp`, `role`, `channel`, `cleanup`, `blackjack`, `deathmatch`,
`rps_tournament`, `counting`, `chain`, `leaderboard`, `proof_channel`,
`utility`, `general`, `help`, `diagnostic`, `settings`, `logging`.

## Per-cog inventory

### admin

1. **cog_module**: `disbot/cogs/admin_cog.py`
2. **subsystem**: `admin`
3. **current_commands**: `!adminmenu`, `!serverstats`, `!cog`, `!loadall`,
   `!unloadall`, `!restart`, `!loglevel`, `!logging status`, `!logging test`
4. **current_command_groups**: `!logging` (group at `admin_cog.py:211`).
5. **current_command_panel_or_menu**: `adminmenu` (panel command).
6. **help_menu_discoverable**: Yes — `SUBSYSTEMS["admin"]` advertises
   `adminmenu` entry point; surfaced via `HelpPanelView` iteration.
7. **dedicated_panel_command**: `none` (no `@panel_command` / `extras["panel"]`
   metadata yet).
8. **help_menu_direct_navigation_hook**: `none` (no `build_help_menu_view`).
9. **existing_SettingSpec_declarations**: none.
10. **existing_settings_keys**: none owned by admin in
    `disbot/utils/settings_keys/`.
11. **existing_BindingSpec_entries**: none.
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: `visibility_tier=owner`;
    capabilities `admin.cog.load`, `admin.cog.unload`, `admin.cog.reload`,
    `admin.server.stats`.
14. **hardcoded_or_env_only_behavior**: `!logging` subgroup currently hosts
    logging UI inside the admin cog rather than a dedicated `settings_cog`.
15. **missing_customization_commands**: a top-level `!settings` cog (planned
    in S5).
16. **missing_settings_pages**: the Settings Manager root page itself
    (planned in S5).
17. **missing_menu_buttons_selects_modals**: settings hub view + per-subsystem
    tabs (planned in S5-S10).
18. **setting_class_per_value**: n/a (admin is the management surface, not a
    settings consumer).
19. **target_Settings_Manager_page**: `!settings platform` (root).
20. **target_mutation_path**: n/a; admin commands proxy other pipelines.
21. **target_help_or_menu_route**: existing Help direct-nav + Admin button.
22. **provisionable_resources**: none.
23. **priority**: `P1` — parent for the new `!settings` cog.
24. **recommended_PR_phase**: S5.

### moderation

1. **cog_module**: `disbot/cogs/moderation_cog.py` (+ `disbot/cogs/moderation/`
   subpackage with `schemas.py`).
2. **subsystem**: `moderation`
3. **current_commands**: `!modmenu`, `!warn`, `!timeout`, `!kick`, `!ban`,
   `!unban`, `!clearwarnings`, `!modlogs`.
4. **current_command_groups**: none.
5. **current_command_panel_or_menu**: `modmenu`.
6. **help_menu_discoverable**: Yes — `SUBSYSTEMS["moderation"]` lists `modmenu`
   and per-command entry points.
7. **dedicated_panel_command**: `none`.
8. **help_menu_direct_navigation_hook**: `none`.
9. **existing_SettingSpec_declarations**: `warn_threshold`,
   `warn_timeout_minutes`, `warn_escalation_action`, `dm_on_action`,
   `dm_template`, `require_reason`, `ban_delete_message_days`,
   `max_timeout_minutes`, `post_action_cleanup`, `post_action_cleanup_limit`,
   `public_log_actions`, `public_log_channel`, `moderator_role`, `trusted_role`
   (`disbot/cogs/moderation/schemas.py`).  All but `warn_threshold` /
   `warn_timeout_minutes` are PR10 behaviour config; `warn_escalation_action` +
   those two are the escalation ladder; `post_action_cleanup` /
   `post_action_cleanup_limit` are the post-kick/ban message sweep; `public_log_actions`
   / `public_log_channel` are the optional public moderation log (delivered by
   `server_logging`); `moderator_role` / `trusted_role` are the capability-native
   tier-grant roles (ADR-008, `input_hint="role"`, admin-floor capability) — all
   applied at / consumed from the `moderation_service` / governance-tier seam.
10. **existing_settings_keys**: `WARN_THRESHOLD`, `WARN_TIMEOUT_MINS`,
    `MOD_WARN_ESCALATION_ACTION`, `MOD_DM_ON_ACTION`, `MOD_DM_TEMPLATE`,
    `MOD_REQUIRE_REASON`, `MOD_BAN_DELETE_MESSAGE_DAYS`,
    `MOD_MAX_TIMEOUT_MINUTES`, `MOD_POST_ACTION_CLEANUP`,
    `MOD_POST_ACTION_CLEANUP_LIMIT`, `MOD_PUBLIC_LOG_ACTIONS`,
    `MOD_PUBLIC_LOG_CHANNEL`
    (`disbot/utils/settings_keys/moderation.py`); plus the governance-owned
    `MODERATOR_TIER_ROLE_ID` / `TRUSTED_TIER_ROLE_ID`
    (`disbot/utils/settings_keys/governance.py`), surfaced in the moderation
    settings page as the `moderator_role` / `trusted_role` pickers.
11. **existing_BindingSpec_entries**: none (mod_log promotion planned in
    later milestone).
12. **existing_ResourceRequirement_entries**: `mod_log` with `binding_name=mod_log`,
    priority `RECOMMENDED` (`disbot/cogs/moderation/schemas.py:57-71`).
13. **current_access_policy_behavior**: `visibility_tier=moderator`;
    capabilities `moderation.warn.apply`, `moderation.timeout.apply`,
    `moderation.kick.apply`, `moderation.ban.apply`, `moderation.ban.remove`,
    `moderation.log.view`, `moderation.settings.configure`.
14. **hardcoded_or_env_only_behavior**: moderator/trusted **roles + capabilities**
    are now first-class (ADR-008): a configured `moderator_role` grants the
    `moderator` tier via the governance tier resolver, so its holders may use
    moderation actions without Discord moderation permissions; the mod cog + panel
    authorize on Discord-permission **OR** capability (behaviour-preserving — the
    permission path is unchanged), and `trusted_role` is wired symmetrically.
    Earlier, PR10 moved DM-on-action
    (`dm_on_action` / `dm_template`), the ban message-purge window
    (`ban_delete_message_days`), the timeout ceiling (`max_timeout_minutes`),
    `require_reason` (warn/kick/ban must justify; timeout exempt), the **warn
    escalation action** (`warn_escalation_action`: timeout/kick/ban/none at
    `warn_threshold`, owned at the warn seam), the **post-action cleanup sweep**
    (`post_action_cleanup`: none/kick/ban/both up to `post_action_cleanup_limit`,
    requested from the cleanup subsystem at the kick/ban seam), and the **optional
    public moderation log** (`public_log_actions`: none/bans/removals/all to
    `public_log_channel`, delivered by `server_logging` with the moderator name
    redacted) out of code into settings applied at / consumed from the
    `moderation_service` seam.  The staff mod-log still rides `logging.mod_channel`;
    the mod panel also shows a read-only bot-readiness line
    (`utils/moderation_feasibility.py`).
15. **missing_customization_commands**: `!settings moderation`
    edit/reset surface; `!moderation timeoutpresets`.
16. **missing_settings_pages**: Settings Manager moderation page.
17. **missing_menu_buttons_selects_modals**: threshold scalar editor,
    timeout-presets list editor, mod-log channel BindingSelectView.
18. **setting_class_per_value**: `warn_threshold` scalar, `warn_timeout_minutes`
    scalar, `warn_escalation_action` enum select, `dm_on_action` bool toggle,
    `dm_template` free-text, `require_reason` bool toggle,
    `ban_delete_message_days` numeric-presets, `max_timeout_minutes`
    numeric-presets, `post_action_cleanup` enum select, `post_action_cleanup_limit`
    numeric-presets, `public_log_actions` enum select, `public_log_channel`
    channel-select; `mod_log` binding (after S10 promotion).
19. **target_Settings_Manager_page**: `!settings subsystem moderation`.
20. **target_mutation_path**: `SettingsMutationPipeline` (scalars);
    `BindingMutationPipeline` (mod_log); `ResourceProvisioningPipeline`
    (create-mod-log channel flow).
21. **target_help_or_menu_route**: Help direct-nav, Admin button, Settings tab.
22. **provisionable_resources**:
    `(mod_log, CHANNEL, RECOMMENDED, mod-logs, Staff, staff-only-text)`.
23. **priority**: `P0` — first subsystem page after Settings shell + logging.
24. **recommended_PR_phase**: S10 (first of the subsystem-page sub-PRs).

### economy

1. **cog_module**: `disbot/cogs/economy_cog.py` (+ `disbot/cogs/economy/`
   subpackage with `_helpers.py`, `schemas.py`).
2. **subsystem**: `economy`
3. **current_commands**: `!economymenu`, `!daily`, `!work`, `!shop`,
   `!balance`/`!bal`/`!wallet`, `!setlogchannel`, `!joblist`/`!jobs`.
4. **current_command_groups**: none.
5. **current_command_panel_or_menu**: `economymenu`.
6. **help_menu_discoverable**: Yes.
7. **dedicated_panel_command**: `none`.
8. **help_menu_direct_navigation_hook**: `none`.
9. **existing_SettingSpec_declarations**: `economy_log_channel`
   (`disbot/cogs/economy/schemas.py`).  PR #6 promoted the log channel
   to a SettingSpec so the cog's three direct ``db.set_setting`` writes
   (``on_ready``, ``on_guild_join``, ``!setlogchannel``) route through
   ``SettingsMutationPipeline`` and land in
   ``settings_mutation_audit``.  The existing ``log_channel`` BindingSpec
   (item 11) remains the canonical typed-resource declaration and is
   read via the arbitration ladder.  Daily/work cooldowns pending
   promotion.
10. **existing_settings_keys**: `ECONOMY_LOG_CHANNEL`
    (`disbot/utils/settings_keys/economy.py`).
11. **existing_BindingSpec_entries**: `log_channel`
    (`disbot/cogs/economy/schemas.py`).
12. **existing_ResourceRequirement_entries**: `log_channel` with `binding_name`
    cross-link (`disbot/cogs/economy/schemas.py:42-57`).
13. **current_access_policy_behavior**: `visibility_tier=user`; capabilities
    `economy.currency.view`, `economy.currency.earn`, `economy.shop.browse`,
    `economy.shop.buy`, `economy.settings.configure`.
14. **hardcoded_or_env_only_behavior**: `_DAILY_COOLDOWN`, `_WORK_COOLDOWN` in
    `disbot/cogs/economy/_helpers.py`; tiered payout amounts, shop catalogue
    seed data.
15. **missing_customization_commands**: `!economy cooldowns set ...`, shop
    catalogue editor.
16. **missing_settings_pages**: Settings Manager economy page.
17. **missing_menu_buttons_selects_modals**: cooldown scalar editors, log
    channel BindingSelectView, shop list editor.
18. **setting_class_per_value**: cooldowns → scalar; log_channel → binding;
    shop catalogue → list.
19. **target_Settings_Manager_page**: `!settings subsystem economy`.
20. **target_mutation_path**: `SettingsMutationPipeline` (cooldowns);
    `BindingMutationPipeline` (log_channel); `ResourceProvisioningPipeline`
    (create-log-channel flow).
21. **target_help_or_menu_route**: Help direct-nav, Settings tab.
22. **provisionable_resources**:
    `(log_channel, CHANNEL, RECOMMENDED, economy-log, Logs, staff-only-text)`.
23. **priority**: `P1` — after moderation + xp.
24. **recommended_PR_phase**: S10.

### inventory

1. **cog_module**: `disbot/cogs/inventory_cog.py`
2. **subsystem**: `inventory`
3. **current_commands**: `!inventory`/`!inv`.
4. **current_command_groups**: none.
5. **current_command_panel_or_menu**: `inventory` entry point.
6. **help_menu_discoverable**: Yes.
7. **dedicated_panel_command**: `none`.
8. **help_menu_direct_navigation_hook**: `none`.
9. **existing_SettingSpec_declarations**: none.
10. **existing_settings_keys**: none.
11. **existing_BindingSpec_entries**: none.
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: `visibility_tier=user`; capabilities
    `inventory.item.view`, `inventory.item.use`, `inventory.craft.recipe`.
14. **hardcoded_or_env_only_behavior**: item catalogue, crafting recipes
    inline.
15. **missing_customization_commands**: per-guild item catalogue overrides
    (out of scope until v2).
16. **missing_settings_pages**: Settings Manager inventory page is `P2`.
17. **missing_menu_buttons_selects_modals**: page TBD by S2 ledger.
18. **setting_class_per_value**: list (catalogue overrides — v2 only).
19. **target_Settings_Manager_page**: `!settings subsystem inventory` (P2).
20. **target_mutation_path**: `SettingsMutationPipeline` (catalogue toggles
    once introduced).
21. **target_help_or_menu_route**: Help direct-nav.
22. **provisionable_resources**: none.
23. **priority**: `P2`.
24. **recommended_PR_phase**: post-S11.

### mining

1. **cog_module**: `disbot/cogs/mining_cog.py` (+ `disbot/cogs/mining/` package).
2. **subsystem**: `mining`
3. **current_commands**: `!mine`, `!minemenu`, `!mineinv`/`!mineinventory`,
   `!minestats`, and several hidden helper commands (deferred to S2 ledger
   for exact enumeration of hidden surface).
4. **current_command_groups**: none.
5. **current_command_panel_or_menu**: `minemenu`.
6. **help_menu_discoverable**: Yes.
7. **dedicated_panel_command**: `none`.
8. **help_menu_direct_navigation_hook**: `none`.
9. **existing_SettingSpec_declarations**: none.
10. **existing_settings_keys**: none.
11. **existing_BindingSpec_entries**: none.
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: `visibility_tier=user`; capabilities
    `mining.resource.mine`, `mining.resource.view`.
14. **hardcoded_or_env_only_behavior**: `ORE_WEIGHTS`, explore outcome table,
    cooldown constants inline.
15. **missing_customization_commands**: `!mining ore weights set ...`,
    cooldown setters.
16. **missing_settings_pages**: Settings Manager mining page.
17. **missing_menu_buttons_selects_modals**: ore-weights list editor,
    cooldown scalar editor, optional `mining_channel` BindingSelectView.
18. **setting_class_per_value**: cooldowns → scalar; ore weights → list;
    optional mining_channel → binding.
19. **target_Settings_Manager_page**: `!settings subsystem mining`.
20. **target_mutation_path**: `SettingsMutationPipeline` (scalars + list);
    `BindingMutationPipeline` + `ResourceProvisioningPipeline` (if
    `mining_channel` binding is introduced).
21. **target_help_or_menu_route**: Help direct-nav, Settings tab.
22. **provisionable_resources**:
    `(mining_channel, CHANNEL, OPTIONAL, mining-panel, Games, public-text)`
    (proposed for S10 — not declared yet).
23. **priority**: `P1`.
24. **recommended_PR_phase**: S10.

### xp

1. **cog_module**: `disbot/cogs/xp_cog.py` (+ `disbot/cogs/xp/` package with
   `schemas.py`).
2. **subsystem**: `xp`
3. **current_commands**: `!xpmenu`, `!rank`, `!givexp`, `!resetxp`,
   `!xpconfig`.
4. **current_command_groups**: none.
5. **current_command_panel_or_menu**: `xpmenu`.
6. **help_menu_discoverable**: Yes.
7. **dedicated_panel_command**: `none`.
8. **help_menu_direct_navigation_hook**: `none`.
9. **existing_SettingSpec_declarations**: `xp_min`, `xp_max`, `xp_cooldown`,
    `xp_announce_channel` (`disbot/cogs/xp/schemas.py`). PR #5 promoted
    the announce-channel scalar to a SettingSpec so all four XP config
    modals write through `SettingsMutationPipeline`; the existing
    `announce_channel` BindingSpec (item 11) remains the canonical
    typed-resource declaration and is read by the arbitration ladder.
10. **existing_settings_keys**: `XP_MIN`, `XP_MAX`, `XP_COOLDOWN`,
    `XP_ANNOUNCE_CHANNEL` (`disbot/utils/settings_keys/xp.py`).
11. **existing_BindingSpec_entries**: `announce_channel`
    (`disbot/cogs/xp/schemas.py`).
12. **existing_ResourceRequirement_entries**: `xp_resource_req_announce`
    cross-linked to `announce_channel` (`disbot/cogs/xp/schemas.py:107-117`).
13. **current_access_policy_behavior**: `visibility_tier=user`; capabilities
    `xp.rank.view`, `xp.leaderboard.view`, `xp.settings.configure`.
14. **hardcoded_or_env_only_behavior**: level-up curve constants, default
    role thresholds.
15. **missing_customization_commands**: edit/reset surface for xp_min/max
    /cooldown via `!settings xp`, level-curve editor (later).
16. **missing_settings_pages**: Settings Manager xp page.
17. **missing_menu_buttons_selects_modals**: scalar editors for min/max
    /cooldown, announce_channel BindingSelectView.
18. **setting_class_per_value**: xp_min/max/cooldown → scalar;
    announce_channel → binding.
19. **target_Settings_Manager_page**: `!settings subsystem xp`.
20. **target_mutation_path**: `SettingsMutationPipeline` (scalars);
    `BindingMutationPipeline` (announce_channel);
    `ResourceProvisioningPipeline` (create-announce-channel flow).
21. **target_help_or_menu_route**: Help direct-nav, Settings tab.
22. **provisionable_resources**:
    `(announce_channel, CHANNEL, OPTIONAL, xp-announcements, General,`
    `public-text)`.
23. **priority**: `P0` — second subsystem page after moderation.
24. **recommended_PR_phase**: S10.

### role

1. **cog_module**: `disbot/cogs/role_cog.py`
2. **subsystem**: `role`
3. **current_commands**: `!roles`, `!rolesettings`, `!rolemenu`,
   `!rolecreator`, `!assignroles`, `!createrole`, `!deleterole`, `!setrole`,
   `!unsetrole`, `!debugroles`, `!refreshmembers`, `!reactroles`,
   `!removereactrole`, `!listreactroles`.
4. **current_command_groups**: none.
5. **current_command_panel_or_menu**: `rolemenu`.
6. **help_menu_discoverable**: Yes.
7. **dedicated_panel_command**: `none`.
8. **help_menu_direct_navigation_hook**: `none`.
9. **existing_SettingSpec_declarations**: `time_roles_stack`,
   `xp_roles_stack` (`disbot/cogs/role/schemas.py`).
10. **existing_settings_keys**: `SKIP_ROLES` (legacy — no longer read at
    runtime), `TIME_ROLES_STACK`, `XP_ROLES_STACK`
    (`disbot/utils/settings_keys/role.py`).
11. **existing_BindingSpec_entries**: none.
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: `visibility_tier=administrator`;
    capabilities `role.settings.configure`, `role.threshold.configure`,
    `role.assignment.manage`, `role.reaction.manage`.
14. **hardcoded_or_env_only_behavior**: time-based role thresholds;
    reaction-role channels. Per-role XP/time exemptions are stored in the
    `role_automation_exemptions` table (migration 052), edited via the
    Roles → Exemptions panel.
15. **missing_customization_commands**: `!settings role thresholds set ...`,
    reaction-role manager UI.
16. **missing_settings_pages**: thresholds editor page (stacking toggles +
    exemptions shipped).
17. **missing_menu_buttons_selects_modals**: time/XP threshold editor
    parity; reaction-role manager.
18. **setting_class_per_value**: `time_roles_stack` / `xp_roles_stack` →
    scalar bool (Settings hub toggle); per-role `exempt_xp` / `exempt_time`
    → typed `role_automation_exemptions` rows (Roles → Exemptions panel);
    thresholds → scalar / list.
19. **target_Settings_Manager_page**: `!settings subsystem role`.
20. **target_mutation_path**: `SettingsMutationPipeline` (scalars / lists);
    `BindingMutationPipeline` (role / channel bindings);
    `ResourceProvisioningPipeline` (create role / channel flows).
21. **target_help_or_menu_route**: Help direct-nav, Admin button, Settings tab.
22. **provisionable_resources** (proposed for S10):
    `(default_role, ROLE, OPTIONAL, Member, n/a, public-mention)`,
    `(role_menu_channel, CHANNEL, OPTIONAL, role-menu, Public,`
    `public-text-locked-write)`.
23. **priority**: `P1`.
24. **recommended_PR_phase**: S10.

### channel

1. **cog_module**: `disbot/cogs/channel_cog.py`
2. **subsystem**: `channel`
3. **current_commands**: `!channelmenu`, `!set`, `!evt`, `!create`,
   `!bulkdelete`, `!del`, `!list`, `!clone`, `!move`, `!lock`, `!unlock`,
   `!channelinfo`, `!rename`, and additional helpers in `channel_cog.py`.
4. **current_command_groups**: none.
5. **current_command_panel_or_menu**: `channelmenu`.
6. **help_menu_discoverable**: Yes.
7. **dedicated_panel_command**: `none`.
8. **help_menu_direct_navigation_hook**: `none`.
9. **existing_SettingSpec_declarations**: none.
10. **existing_settings_keys**: none.
11. **existing_BindingSpec_entries**: none.
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: `visibility_tier=administrator`;
    capabilities `channel.create.text`, `channel.create.voice`,
    `channel.delete.any`, `channel.restrict.apply`,
    `channel.visibility.configure`.
14. **hardcoded_or_env_only_behavior**: channel-name conventions
    (e.g. category seeds in `disbot/config.py:CLEANUP_WHITELIST_CHANNELS`
    and similar).
15. **missing_customization_commands**: per-guild channel name / category
    convention editor.
16. **missing_settings_pages**: Settings Manager channel page.
17. **missing_menu_buttons_selects_modals**: name-convention list editor,
    category-template selector.
18. **setting_class_per_value**: convention lists → list;
    creation-template → list.
19. **target_Settings_Manager_page**: `!settings subsystem channel`.
20. **target_mutation_path**: `SettingsMutationPipeline` (lists / scalars).
    Channel resource creation itself is a `channel` subsystem responsibility
    today; once promoted, it routes through `ResourceProvisioningPipeline`.
21. **target_help_or_menu_route**: Help direct-nav, Admin button, Settings tab.
22. **provisionable_resources**: none owned today; channel templates are
    consumed by other subsystems' provisioning hints (see Logging /
    Moderation / etc.).
23. **priority**: `P2`.
24. **recommended_PR_phase**: post-S11.

### cleanup

1. **cog_module**: `disbot/cogs/cleanup_cog.py`
2. **subsystem**: `cleanup`
3. **current_commands**: `!cleanuphistory`, `!wordmenu`, `!word add`,
   `!word remove`, `!word list`.
4. **current_command_groups**: `!word` (group at `cleanup_cog.py:238`).
5. **current_command_panel_or_menu**: `wordmenu`, `cleanuphistory`.
6. **help_menu_discoverable**: Yes.
7. **dedicated_panel_command**: `none`.
8. **help_menu_direct_navigation_hook**: `none`.
9. **existing_SettingSpec_declarations**: none yet (governance owns
    cleanup_policies; cleanup-level scalars are roadmap work in S8 v2/v3).
10. **existing_settings_keys**: cleanup-related toggles live in
    `disbot/config.py` (`CLEANUP_WHITELIST_CHANNELS`, ignored-channel
    CSV in legacy KV) — to be migrated.
11. **existing_BindingSpec_entries**: none. **Cleanup must not own a
    duplicate `cleanup_log_channel` binding** — the logging subsystem owns
    `cleanup_channel`; cleanup deep-links to it.
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: `visibility_tier=administrator`;
    capabilities `cleanup.word.add`, `cleanup.word.remove`,
    `cleanup.history.scan`, `cleanup.policy.configure`.
14. **hardcoded_or_env_only_behavior**: `CLEANUP_WHITELIST_CHANNELS` in
    `disbot/config.py:83`, ignored-channels CSV, prohibited-words seed list.
15. **missing_customization_commands**: `!cleanup ignore add #channel`,
    `!cleanup unignore #channel`, `!cleanup prohibited add <word>`,
    list/clear variants.
16. **missing_settings_pages**: Settings Manager cleanup page.
17. **missing_menu_buttons_selects_modals**: ignored-channels list editor,
    prohibited-words list editor, deep-link button to Logging's
    cleanup_channel.
18. **setting_class_per_value**: ignored_channels → list (transitional CSV
    → typed channel-scoped policy in v2); prohibited_words → list (v3).
19. **target_Settings_Manager_page**: `!settings subsystem cleanup`.
20. **target_mutation_path**: `GovernanceMutationPipeline` (cleanup_policies);
    `SettingsMutationPipeline` (transitional scalars).
21. **target_help_or_menu_route**: Help direct-nav, Admin button,
    Settings tab.
22. **provisionable_resources**: none (cleanup deep-links to Logging's
    `cleanup_channel`; it does not own a duplicate binding).
23. **priority**: `P0` — biggest customization gap.
24. **recommended_PR_phase**: S8.

### community

1. **cog_module**: `disbot/cogs/community_cog.py`.
2. **subsystem**: `community`
3. **current_commands**: `!community`.
4. **current_command_groups**: none.
5. **current_command_panel_or_menu**: `community` entry — opens `CommunityHubView`
   in `disbot/views/community/hub.py`.
6. **help_menu_discoverable**: Yes (registered as a Help category via
   `utils/hub_registry.py` HUBS entry; falls back to standard `SUBSYSTEMS`
   iteration for "All Commands / Advanced").
7. **dedicated_panel_command**: `!community`.
8. **help_menu_direct_navigation_hook**: `CommunityCog.build_help_menu_view`.
9. **existing_SettingSpec_declarations**: none.
10. **existing_settings_keys**: none.
11. **existing_BindingSpec_entries**: none.
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: `visibility_tier=user`; capabilities
    `community.hub.view`.
14. **hardcoded_or_env_only_behavior**: hub children are hard-coded
    cross-link buttons (`xp`, `role`, `counting`, `chain`, `leaderboard`)
    in `views/community/hub.py:_HUB_CHILDREN`.
15. **missing_customization_commands**: none — Community is a router-only
    hub, not a configurable subsystem.
16. **missing_settings_pages**: none planned; the hub itself has no
    persisted state.
17. **missing_menu_buttons_selects_modals**: future S9b promotes XP/Role
    to `parent_hub="community"` and adds an Includes line in Help.
18. **setting_class_per_value**: n/a (router only).
19. **target_Settings_Manager_page**: none — children expose their own.
20. **target_mutation_path**: n/a; no state.
21. **target_help_or_menu_route**: Help direct-nav into `CommunityHubView`;
    each button forwards to the target cog's `build_help_menu_view` hook.
22. **provisionable_resources**: none.
23. **priority**: `P1` — interface skeleton, low risk.
24. **recommended_PR_phase**: mother-hub PR sequence Phase S9.

### games

1. **cog_module**: `disbot/cogs/games_cog.py`.
2. **subsystem**: `games`
3. **current_commands**: `!games`.
4. **current_command_groups**: none.
5. **current_command_panel_or_menu**: `games` entry — opens `GamesHubView`
   in `disbot/views/games/hub.py`.
6. **help_menu_discoverable**: Yes (via the standard `SUBSYSTEMS`
   iteration in `help_cog.py`).
7. **dedicated_panel_command**: `!games`.
8. **help_menu_direct_navigation_hook**: `GamesCog.build_help_menu_view`.
9. **existing_SettingSpec_declarations**: none.
10. **existing_settings_keys**: none.
11. **existing_BindingSpec_entries**: none.
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: `visibility_tier=user`; capabilities
    `games.hub.view`.
14. **hardcoded_or_env_only_behavior**: hub children discovered dynamically
    from `SUBSYSTEMS` entries whose `parent_hub == "games"`.
15. **missing_customization_commands**: none — Games is a router, not a
    configurable subsystem.
16. **missing_settings_pages**: none planned; the hub itself has no
    persisted state.
17. **missing_menu_buttons_selects_modals**: per-child mode/replay panels
    are layered later (Phase 7 of the interface-completion roadmap).
18. **setting_class_per_value**: n/a (router only).
19. **target_Settings_Manager_page**: none — children expose their own.
20. **target_mutation_path**: n/a; no state.
21. **target_help_or_menu_route**: Help direct-nav into `GamesHubView`,
    Games hub's select into each child's `build_help_menu_view`.
22. **provisionable_resources**: none.
23. **priority**: `P1` — interface skeleton, low risk.
24. **recommended_PR_phase**: interface-completion Phase 3.

### blackjack

1. **cog_module**: `disbot/cogs/blackjack_cog.py` (+ `disbot/cogs/blackjack/`
   package).
2. **subsystem**: `blackjack`
3. **current_commands**: `!blackjack`/`!bj`, `!bjtournament`/`!bjtourn`,
   `!bjstart`, `!bjstatus`.
4. **current_command_groups**: none.
5. **current_command_panel_or_menu**: `blackjack` entry points.
6. **help_menu_discoverable**: Yes.
7. **dedicated_panel_command**: `none`.
8. **help_menu_direct_navigation_hook**: `none`.
9. **existing_SettingSpec_declarations**: `default_entry_fee`
   (`disbot/cogs/blackjack/schemas.py`, PR 8).
10. **existing_settings_keys**: `BLACKJACK_DEFAULT_ENTRY_FEE`
    (`disbot/utils/settings_keys/games.py`).
11. **existing_BindingSpec_entries**: none.
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: `visibility_tier=user`; capabilities
    `blackjack.game.play`.
14. **hardcoded_or_env_only_behavior**: bet limits, deck rules.
15. **missing_customization_commands**: bet-limit editor.
16. **missing_settings_pages**: Settings Manager blackjack page (`P2`).
17. **missing_menu_buttons_selects_modals**: bet-limit scalar editor.
18. **setting_class_per_value**: bet limits → scalar.
19. **target_Settings_Manager_page**: `!settings subsystem blackjack` (P2).
20. **target_mutation_path**: `SettingsMutationPipeline`.
21. **target_help_or_menu_route**: Help direct-nav.
22. **provisionable_resources**: none.
23. **priority**: `P2`.
24. **recommended_PR_phase**: post-S11.

### deathmatch

1. **cog_module**: `disbot/cogs/deathmatch_cog.py`
2. **subsystem**: `deathmatch`
3. **current_commands**: `!dm_challenge`/`!deathmatch`/`!challenge`/`!dm`,
   `!dm_help`/`!deathmatch_help`.
4. **current_command_groups**: none.
5. **current_command_panel_or_menu**: `deathmatch` / `dm` entry points.
6. **help_menu_discoverable**: Yes.
7. **dedicated_panel_command**: `none`.
8. **help_menu_direct_navigation_hook**: `none`.
9. **existing_SettingSpec_declarations**: `turn_timeout`
   (`disbot/cogs/deathmatch/schemas.py`, PR 8).
10. **existing_settings_keys**: `DEATHMATCH_TURN_TIMEOUT`
    (`disbot/utils/settings_keys/games.py`).
11. **existing_BindingSpec_entries**: none.
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: `visibility_tier=user`; capabilities
    `deathmatch.game.challenge`, `deathmatch.stat.view`.
14. **hardcoded_or_env_only_behavior**: HP / damage tables inline.
15. **missing_customization_commands**: balance tweak editor.
16. **missing_settings_pages**: Settings Manager deathmatch page (`P2`).
17. **missing_menu_buttons_selects_modals**: HP scalar editor.
18. **setting_class_per_value**: HP / damage → scalar / list.
19. **target_Settings_Manager_page**: `!settings subsystem deathmatch` (P2).
20. **target_mutation_path**: `SettingsMutationPipeline`.
21. **target_help_or_menu_route**: Help direct-nav.
22. **provisionable_resources**: none.
23. **priority**: `P2`.
24. **recommended_PR_phase**: post-S11.

### rps_tournament

1. **cog_module**: `disbot/cogs/rps_tournament_cog.py`
   (+ `disbot/cogs/rps_tournament/` package).
2. **subsystem**: `rps_tournament`
3. **current_commands**: `!rps`, `!rpsregister`/`!rpsreg`,
   `!rpsstart`/`!rpsbegin`, `!rpsbot`, `!rpsmatchup`, `!rpshelp`,
   `!rpssettings`.
4. **current_command_groups**: none.
5. **current_command_panel_or_menu**: `rps` / `rpssettings`.
6. **help_menu_discoverable**: Yes.
7. **dedicated_panel_command**: `none`.
8. **help_menu_direct_navigation_hook**: `none`.
9. **existing_SettingSpec_declarations**: `default_entry_fee`
   (`disbot/cogs/rps_tournament/schemas.py`, PR 8).
10. **existing_settings_keys**: `ACTIVE_TOURNAMENT`,
    `RPS_DEFAULT_ENTRY_FEE`
    (`disbot/utils/settings_keys/games.py`).
11. **existing_BindingSpec_entries**: none.
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: `visibility_tier=user`; capabilities
    `rps_tournament.game.join`, `rps_tournament.tournament.manage`.
14. **hardcoded_or_env_only_behavior**: bracket size / scoring rules inline.
15. **missing_customization_commands**: bracket-size editor,
    `tournament_channel` selector.
16. **missing_settings_pages**: Settings Manager rps page (`P2`).
17. **missing_menu_buttons_selects_modals**: bracket scalar editor,
    tournament_channel BindingSelectView.
18. **setting_class_per_value**: bracket → scalar; tournament_channel →
    binding.
19. **target_Settings_Manager_page**: `!settings subsystem rps` (P2).
20. **target_mutation_path**: `SettingsMutationPipeline`;
    `BindingMutationPipeline` + `ResourceProvisioningPipeline` for
    `tournament_channel` once introduced.
21. **target_help_or_menu_route**: Help direct-nav.
22. **provisionable_resources** (proposed for S10):
    `(tournament_channel, CHANNEL, OPTIONAL, rps-tournament, Games,`
    `public-text)`.
23. **priority**: `P2`.
24. **recommended_PR_phase**: post-S11.

### counting

1. **cog_module**: `disbot/cogs/counting_cog.py` (+ `disbot/cogs/counting/`
   package).
2. **subsystem**: `counting`
3. **current_commands**: `!countingmenu`/`!cm`, `!start_match`/`!sm`,
   `!end_match`/`!em`, `!reset_count`/`!rc`, `!toggle_turns`/`!tt`,
   `!count_info`/`!ci`, `!count_rules`/`!cr`, `!set_skip_numbers`/`!ssn`,
   `!toggle_reset_on_wrong_count`/`!trwc`.
4. **current_command_groups**: none.
5. **current_command_panel_or_menu**: `countingmenu`.
6. **help_menu_discoverable**: Yes.
7. **dedicated_panel_command**: `none`.
8. **help_menu_direct_navigation_hook**: `none`.
9. **existing_SettingSpec_declarations**: none.
10. **existing_settings_keys**: none.
11. **existing_BindingSpec_entries**: none.
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: `visibility_tier=user`; capabilities
    `counting.game.play`, `counting.game.configure`.
14. **hardcoded_or_env_only_behavior**: skip-number list, default channel
    selection.
15. **missing_customization_commands**: `counting_channel` selector,
    rule-set editor.
16. **missing_settings_pages**: Settings Manager counting page (`P2`).
17. **missing_menu_buttons_selects_modals**: counting_channel
    BindingSelectView, skip-numbers list editor.
18. **setting_class_per_value**: skip_numbers → list; counting_channel →
    binding.
19. **target_Settings_Manager_page**: `!settings subsystem counting` (P2).
20. **target_mutation_path**: `SettingsMutationPipeline` (lists);
    `BindingMutationPipeline` + `ResourceProvisioningPipeline` for
    counting_channel.
21. **target_help_or_menu_route**: Help direct-nav.
22. **provisionable_resources** (proposed for S10):
    `(counting_channel, CHANNEL, OPTIONAL, counting, Games, public-text)`.
23. **priority**: `P2`.
24. **recommended_PR_phase**: post-S11.

### chain

1. **cog_module**: `disbot/cogs/chain_cog.py`
2. **subsystem**: `chain`
3. **current_commands**: `!chain` (group with subcommands `create`, `delete`,
   `setlimit`, `removelimit`, `list`), `!chainmenu`.
4. **current_command_groups**: `!chain` (group at `chain_cog.py:66`).
5. **current_command_panel_or_menu**: `chainmenu`.
6. **help_menu_discoverable**: Yes.
7. **dedicated_panel_command**: `none`.
8. **help_menu_direct_navigation_hook**: `none`.
9. **existing_SettingSpec_declarations**: none.
10. **existing_settings_keys**: none.
11. **existing_BindingSpec_entries**: none.
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: `visibility_tier=user`; capabilities
    `chain.game.play`, `chain.game.configure`.
14. **hardcoded_or_env_only_behavior**: chain-channel discovery, limit
    defaults.
15. **missing_customization_commands**: `chain_channel` selector.
16. **missing_settings_pages**: Settings Manager chain page (`P2`).
17. **missing_menu_buttons_selects_modals**: chain_channel BindingSelectView.
18. **setting_class_per_value**: chain_channel → binding;
    word-list overrides → list.
19. **target_Settings_Manager_page**: `!settings subsystem chain` (P2).
20. **target_mutation_path**: `SettingsMutationPipeline`;
    `BindingMutationPipeline` + `ResourceProvisioningPipeline` for
    chain_channel.
21. **target_help_or_menu_route**: Help direct-nav.
22. **provisionable_resources** (proposed for S10):
    `(chain_channel, CHANNEL, OPTIONAL, word-chain, Games, public-text)`.
23. **priority**: `P2`.
24. **recommended_PR_phase**: post-S11.

### leaderboard

1. **cog_module**: `disbot/cogs/leaderboard_cog.py`
2. **subsystem**: `leaderboard`
3. **current_commands**: `!leaderboard`/`!lb`.
4. **current_command_groups**: none.
5. **current_command_panel_or_menu**: `leaderboard`.
6. **help_menu_discoverable**: Yes.
7. **dedicated_panel_command**: `none`.
8. **help_menu_direct_navigation_hook**: `none`.
9. **existing_SettingSpec_declarations**: none.
10. **existing_settings_keys**: none.
11. **existing_BindingSpec_entries**: none.
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: `visibility_tier=user`; capabilities
    `leaderboard.xp.view`, `leaderboard.economy.view`.
14. **hardcoded_or_env_only_behavior**: page size, default sort axis.
15. **missing_customization_commands**: page-size / default-axis selector.
16. **missing_settings_pages**: Settings Manager leaderboard page (`P2`).
17. **missing_menu_buttons_selects_modals**: page-size scalar editor.
18. **setting_class_per_value**: page_size → scalar.
19. **target_Settings_Manager_page**: `!settings subsystem leaderboard` (P2).
20. **target_mutation_path**: `SettingsMutationPipeline`.
21. **target_help_or_menu_route**: Help direct-nav.
22. **provisionable_resources**: none.
23. **priority**: `P2`.
24. **recommended_PR_phase**: post-S11.

### proof_channel

1. **cog_module**: `disbot/cogs/proof_channel_cog.py`
2. **subsystem**: `proof_channel`
3. **current_commands**: `!+prize`, `!-prize`, `!prizestatus`, `!prizemenu`,
   `!timedprize`.
4. **current_command_groups**: none.
5. **current_command_panel_or_menu**: `prizemenu`.
6. **help_menu_discoverable**: Yes.
7. **dedicated_panel_command**: `none`.
8. **help_menu_direct_navigation_hook**: `none`.
9. **existing_SettingSpec_declarations**: none yet (timed-prize default
   duration pending promotion).
10. **existing_settings_keys**: none.
11. **existing_BindingSpec_entries**: none yet (`proof_channel` binding
    pending promotion in S10 — currently resolved by hardcoded name
    `"proof"` at `proof_channel_cog.py:30`).
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: `visibility_tier=staff`; capabilities
    `proof_channel.access.grant`, `proof_channel.access.revoke`,
    `proof_channel.access.timed`.
14. **hardcoded_or_env_only_behavior**: hardcoded channel name `"proof"`,
    default approval role, default timed-prize duration.
15. **missing_customization_commands**: `!settings proof channel ...`,
    approval-role selector, default-duration editor.
16. **missing_settings_pages**: Settings Manager proof_channel page.
17. **missing_menu_buttons_selects_modals**: proof_channel BindingSelectView,
    approval_role RoleSelectView, default-duration scalar editor.
18. **setting_class_per_value**: proof_channel → binding;
    approval_role → binding; default_duration → scalar.
19. **target_Settings_Manager_page**: `!settings subsystem proof`.
20. **target_mutation_path**: `BindingMutationPipeline` (channel + role
    bindings); `ResourceProvisioningPipeline` (create flows);
    `SettingsMutationPipeline` (duration scalar).
21. **target_help_or_menu_route**: Help direct-nav, Admin button, Settings tab.
22. **provisionable_resources** (proposed for S10):
    `(proof_channel, CHANNEL, REQUIRED, proof, Staff, staff-only-text)`,
    `(approval_role, ROLE, REQUIRED, Proof Approver, n/a, public-mention)`.
23. **priority**: `P0` — hardcoded name `"proof"` is a current footgun.
24. **recommended_PR_phase**: S10.

### utility

1. **cog_module**: `disbot/cogs/utility_cog.py`
2. **subsystem**: `utility`
3. **current_commands**: `!utilitymenu`, `!clear`/`!purge`, `!info`,
   `!serverinfo`, `!userinfo`, `!avatar`, `!remind`, `!invite`, `!poll`.
4. **current_command_groups**: none.
5. **current_command_panel_or_menu**: `utilitymenu`.
6. **help_menu_discoverable**: Yes.
7. **dedicated_panel_command**: `none`.
8. **help_menu_direct_navigation_hook**: `none`.
9. **existing_SettingSpec_declarations**: none.
10. **existing_settings_keys**: none.
11. **existing_BindingSpec_entries**: none.
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: `visibility_tier=user`; capabilities
    `utility.info.server`, `utility.info.user`, `utility.tool.ping`.
14. **hardcoded_or_env_only_behavior**: reminder limits, poll constraints.
15. **missing_customization_commands**: reminder-limit / poll-constraint
    editor.
16. **missing_settings_pages**: Settings Manager utility page (`P2`).
17. **missing_menu_buttons_selects_modals**: scalar editors for limits.
18. **setting_class_per_value**: reminder_limit → scalar; poll_options → list.
19. **target_Settings_Manager_page**: `!settings subsystem utility` (P2).
20. **target_mutation_path**: `SettingsMutationPipeline`.
21. **target_help_or_menu_route**: Help direct-nav.
22. **provisionable_resources**: none.
23. **priority**: `P2`.
24. **recommended_PR_phase**: post-S11.

### general

1. **cog_module**: `disbot/cogs/general_cog.py`
2. **subsystem**: `general`
3. **current_commands**: `!generalmenu`, `!fact`, `!joke`, `!quote`,
   `!trivia`, `!motivate`, `!eightball`, `!greet`.
4. **current_command_groups**: none.
5. **current_command_panel_or_menu**: `generalmenu`.
6. **help_menu_discoverable**: Yes.
7. **dedicated_panel_command**: `none`.
8. **help_menu_direct_navigation_hook**: `none`.
9. **existing_SettingSpec_declarations**: none.
10. **existing_settings_keys**: none.
11. **existing_BindingSpec_entries**: none.
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: `visibility_tier=user`; capabilities
    `general.info.view`, `general.community.interact`.
14. **hardcoded_or_env_only_behavior**: fact / joke / quote pools loaded from
    JSON files.
15. **missing_customization_commands**: per-guild pool overrides
    (out of scope until v2).
16. **missing_settings_pages**: Settings Manager general page (`P2`).
17. **missing_menu_buttons_selects_modals**: pool toggle editor.
18. **setting_class_per_value**: enabled_pools → list.
19. **target_Settings_Manager_page**: `!settings subsystem general` (P2).
20. **target_mutation_path**: `SettingsMutationPipeline`.
21. **target_help_or_menu_route**: Help direct-nav.
22. **provisionable_resources**: none.
23. **priority**: `P2`.
24. **recommended_PR_phase**: post-S11.

### four_twenty

1. **cog_module**: `disbot/cogs/four_twenty_cog.py`
2. **subsystem**: `four_twenty`
3. **current_commands**: `!420` (aliases `!fourtwenty`, `!fourtwenty420`).
4. **current_command_groups**: none.
5. **current_command_panel_or_menu**: `420`.
6. **help_menu_discoverable**: Yes (Utility hub child; `build_help_menu_view`).
7. **dedicated_panel_command**: `420`.
8. **help_menu_direct_navigation_hook**: `build_help_menu_view`.
9. **existing_SettingSpec_declarations**: none.
10. **existing_settings_keys**: none.
11. **existing_BindingSpec_entries**: none.
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: `visibility_tier=user`; capability
    `four_twenty.panel.view`. Passive `FourTwentyStage` (message-pipeline,
    observe-only, per-channel cooldown) 🍃-reacts to `420` mentions.
14. **hardcoded_or_env_only_behavior**: wisdom / fact pools loaded from
    `data/json/four_twenty_content.json`.
15. **missing_customization_commands**: per-guild egg toggle (out of scope).
16. **missing_settings_pages**: none planned (intentionally a fixed easter egg).
17. **missing_menu_buttons_selects_modals**: none.
18. **setting_class_per_value**: none.
19. **target_Settings_Manager_page**: none (no configurable surface by design).
20. **target_mutation_path**: none (read-only; no state mutation).
21. **target_help_or_menu_route**: Help direct-nav.
22. **provisionable_resources**: none.
23. **priority**: `P3`.
24. **recommended_PR_phase**: PR #420.

### help

1. **cog_module**: `disbot/cogs/help_cog.py`
2. **subsystem**: `help`
3. **current_commands**: `!help`/`!hilfe`.
4. **current_command_groups**: none.
5. **current_command_panel_or_menu**: `help`; UI implemented as
   `HelpPanelView` (`disbot/cogs/help_cog.py:248-327`).
6. **help_menu_discoverable**: itself — surfaces SUBSYSTEMS through
   `HelpPanelView` iteration.
7. **dedicated_panel_command**: `none` formally; the `!help` command is the
   panel.
8. **help_menu_direct_navigation_hook**: `HelpPanelView` is the hook
   provider — other cogs target it via their own implementations once added.
9. **existing_SettingSpec_declarations**: none.
10. **existing_settings_keys**: none.
11. **existing_BindingSpec_entries**: none.
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: `visibility_tier=user`; capabilities
    `help.menu.view`.
14. **hardcoded_or_env_only_behavior**: page layout constants.
15. **missing_customization_commands**: none — Help is itself the discovery
    surface; S11 wires every cog into it.
16. **missing_settings_pages**: none (Help is the menu, not a settings page).
17. **missing_menu_buttons_selects_modals**: direct-nav buttons to Settings,
    Platform, Admin (added in S11).
18. **setting_class_per_value**: n/a.
19. **target_Settings_Manager_page**: n/a; Help routes _into_ Settings, not
    the reverse.
20. **target_mutation_path**: n/a.
21. **target_help_or_menu_route**: itself.
22. **provisionable_resources**: none.
23. **priority**: `P0` — the discoverability hub for S11.
24. **recommended_PR_phase**: S11.

### diagnostic

1. **cog_module**: `disbot/cogs/diagnostic_cog.py`
2. **subsystem**: `diagnostic`
3. **current_commands**: `!diagnostics`/`!diag`, `!list_commands_detailed`,
   `!find_command`, `!validate_json_files`, `!check_database`,
   `!diagnostic_bot_status`, `!latency`/`!ping`, `!system_info`,
   `!query_logs`, `!recent_errors`, `!test_notification`, `!platform` group
   with subcommands (`status`, `anchors`, `identity`, `runtime`, `caches`,
   `locks`, `tasks`, `views`, `slow`, `sessions`, `schemas`, `bindings`,
   `resources`).
4. **current_command_groups**: `!platform` (group at
   `diagnostic_cog.py:179`).
5. **current_command_panel_or_menu**: `!diagnostics` is the panel command;
   no `*menu`.
6. **help_menu_discoverable**: Yes via SUBSYSTEMS — but no
   `build_help_menu_view` hook implemented yet.
7. **dedicated_panel_command**: `none` formally; `!diagnostics` is the panel.
8. **help_menu_direct_navigation_hook**: `none`.
9. **existing_SettingSpec_declarations**: none.
10. **existing_settings_keys**: none.
11. **existing_BindingSpec_entries**: none.
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: `visibility_tier=administrator`;
    capabilities `diagnostic.health.view`, `diagnostic.latency.check`.
14. **hardcoded_or_env_only_behavior**: probe thresholds inline.
15. **missing_customization_commands**: `!platform customization`
    (S2), `!platform resources` (S2.5).
16. **missing_settings_pages**: none for diagnostic itself; diagnostic
    _surfaces_ the catalogues.
17. **missing_menu_buttons_selects_modals**: none (read-only diagnostic).
18. **setting_class_per_value**: runtime diagnostic.
19. **target_Settings_Manager_page**: n/a (read-only mirror in
    `!platform`).
20. **target_mutation_path**: none (read-only).
21. **target_help_or_menu_route**: existing.
22. **provisionable_resources**: none.
23. **priority**: `P0` — hosts the registries that S2 / S2.5 surface.
24. **recommended_PR_phase**: S2 (`!platform customization`) + S2.5
    (`!platform resources`).

### ai

1. **cog_module**: `disbot/cogs/ai_cog.py`
2. **subsystem**: `ai`
3. **current_commands**: `!ai` (group), `!ai status`, `!ai diagnostics`,
   `!ai providers`, `!ai routing`, `!ai settings`, `!aimenu`. Slash
   equivalents (`/ai status`, `/ai diagnostics`, `/ai providers`,
   `/ai routing`, `/ai settings`, `/aimenu`) mirror the prefix surface.
4. **current_command_groups**: `!ai` group (administrator-only).
5. **current_command_panel_or_menu**: `!aimenu` (alias of `!ai`) opens the
   persistent panel `AIPanelView`; `!ai settings` opens the
   auto-dispatched `SubsystemSettingsView` for the AI subsystem.
6. **help_menu_discoverable**: Yes — `AICog.build_help_menu_view`
   returns the panel embed + view.
7. **dedicated_panel_command**: `!aimenu`.
8. **help_menu_direct_navigation_hook**: `build_help_menu_view` →
   `AIPanelView` (read-only).
9. **existing_SettingSpec_declarations**: M1 of the BTD6-top-level +
   AI-central-policy initiative shipped the AI subsystem's scalar
   surface in `disbot/cogs/ai/schemas.py` — ten SettingSpecs:
   `ai_enabled`, `ai_natural_language_enabled`, `ai_default_provider`,
   `ai_default_model`, `ai_minimum_level_default`,
   `ai_cooldown_seconds`, `ai_fresh_user_mention_allowance`,
   `ai_guild_instruction_profile`, `ai_memory_window_minutes`, and
   `ai_memory_channel_scan_enabled`. Each spec maps to the matching
   `AI_*` constant in `disbot/utils/settings_keys/ai.py`. The
   `audit_log_channel` BindingSpec is the single source of truth
   for the AI audit channel across later milestones.
10. **existing_settings_keys**: `AI_ENABLED`, `AI_NATURAL_LANGUAGE_ENABLED`,
    `AI_DEFAULT_PROVIDER`, `AI_DEFAULT_MODEL`,
    `AI_MINIMUM_LEVEL_DEFAULT`, `AI_COOLDOWN_SECONDS`,
    `AI_FRESH_USER_MENTION_ALLOWANCE`, `AI_GUILD_INSTRUCTION_PROFILE`,
    `AI_MEMORY_WINDOW_MINUTES`, `AI_MEMORY_CHANNEL_SCAN_ENABLED`
    (all in `disbot/utils/settings_keys/ai.py`).
11. **existing_BindingSpec_entries**: `audit_log_channel` (channel,
    optional, capability `ai.settings.configure`) — routed through
    `BindingMutationPipeline`. Remains the canonical owner of the
    AI audit channel; M2 does NOT duplicate this into the typed
    `ai_guild_policy` table.
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: `visibility_tier=administrator`;
    capabilities `ai.platform.view`, `ai.diagnostics.view`,
    `ai.provider.view`, `ai.routing.view` (all read-only).
14. **hardcoded_or_env_only_behavior**: provider/model resolution lives
    in `core.runtime.ai.routing` (env-overridable via
    `AI_ROUTING_<TASK>=<provider>:<model>`); request budgets and
    timeouts default in `core.runtime.ai.routing`/`safety`.
15. **missing_customization_commands**: per-task enable/disable surface
    (currently env-only via `AI_TASK_<NAME>_ENABLED`).
16. **missing_settings_pages**: none for the read-only MVP.
17. **missing_menu_buttons_selects_modals**: none (panel is read-only).
18. **setting_class_per_value**: n/a (process-level platform settings).
19. **target_Settings_Manager_page**: `!settings subsystem ai` plus
    the dedicated `!ai settings` / `/ai settings` entry points that
    open the auto-dispatched `SubsystemSettingsView` directly.
20. **target_mutation_path**: `SettingsMutationPipeline` (eight M1
    scalars); `BindingMutationPipeline` (`audit_log_channel`). M2
    adds `ai_policy_mutation` / `ai_instruction_mutation` for the
    typed policy tables; both write through the same audit/event
    plumbing.
21. **target_help_or_menu_route**: existing; AI Platform reachable via
    Admin / Diagnostics hubs (`related_subsystems`).
22. **provisionable_resources**: none.
23. **priority**: `P1` — surfaces platform AI state for operators.
24. **recommended_PR_phase**: lands with Module 2 of the AI/BTD6
    plan.

### btd6

1. **cog_module**: `disbot/cogs/btd6_cog.py`
2. **subsystem**: `btd6`
3. **current_commands**: `!btd6` (group), `!btd6 status`,
   `!btd6 diagnostics`, `!btd6 ask <question>`, `!btd6 test-intent <text>`,
   `!btd6 ctteam`, `!btd6menu`. Slash equivalents (`/btd6 ...`, `/btd6menu`)
   mirror the prefix surface. The reference / events / strategy command
   groups now live in sibling cogs (see `btd6_reference`, `btd6_events`,
   `btd6_strategy` below) so `btd6_cog.py` stays under the 800-LOC ceiling;
   the mother cog keeps the panel, core diagnostics, and the schema +
   ingestion-supervisor lifecycle.
4. **current_command_groups**: `!btd6` group (user-tier).
5. **current_command_panel_or_menu**: `!btd6menu` (alias for `!btd6`)
   opens the persistent panel `BTD6PanelView`.
6. **help_menu_discoverable**: Yes — `BTD6Cog.build_help_menu_view`
   returns the panel embed + view.
7. **dedicated_panel_command**: `!btd6menu`.
8. **help_menu_direct_navigation_hook**: `build_help_menu_view` →
   `BTD6PanelView`.
9. **existing_SettingSpec_declarations**: M3B of the BTD6
   top-level + AI-central-policy initiative landed BTD6's source-
   cache scalars under `disbot/utils/settings_keys/btd6_cache.py`
   (BTD6-owned cadence, NOT AI policy): per-source overrides live in
   `btd6_source_registry.cache_policy_key`; the three guild-level
   defaults are the named constants below. Module 6 / M4 add
   strategy-submission channel binding + AI augmentation toggle.
10. **existing_settings_keys**: `BTD6_CACHE_DEFAULT_INTERVAL_SECONDS`,
    `BTD6_CACHE_CIRCUIT_BREAKER_THRESHOLD`,
    `BTD6_CACHE_FRESHNESS_WARNING_HOURS`
    (in `disbot/utils/settings_keys/btd6_cache.py`);
    `BTD6_STRATEGY_SUBMISSION_CHANNEL` (M4),
    `BTD6_CT_GROUP_ID` (the per-guild Contested Territory bracket id pasted
    via `!btd6 ctteam`, read/written through
    `services.btd6_ct_team_service`; a runtime pointer, no SettingSpec), and
    `BTD6_VERSION_ANNOUNCEMENT_CHANNEL` (the per-guild channel where new BTD6
    version announcements are posted, set via `!btd6ops announcechannel`,
    read/written through `services.btd6_version_announce`; a runtime pointer,
    no SettingSpec), all
    in `disbot/utils/settings_keys/btd6.py`.
11. **existing_BindingSpec_entries**: `btd6.strategy_submission_channel`
    (M4) routes natural-language submissions in bound channels into
    the strategy review pipeline; declared in
    `disbot/cogs/btd6/schemas.py` with capability
    `btd6.settings.configure`. Writes flow through
    `BindingMutationPipeline`.
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: `visibility_tier=user`;
    capabilities `btd6.query.ask`, `btd6.strategy.view`,
    `btd6.diagnostics.view`.
14. **hardcoded_or_env_only_behavior**: game-data fixtures pinned in
    `disbot/data/btd6/*.json` (version metadata in each file).
15. **missing_customization_commands**: `!btd6 settings` lands with
    Module 6 once channels/mention behaviour are persisted.
16. **missing_settings_pages**: per-guild BTD6 settings page —
    deferred to Module 6.
17. **missing_menu_buttons_selects_modals**: AI-augmentation toggle
    button (Module 5/6).
18. **setting_class_per_value**: n/a in Module 4 (no settings yet).
19. **target_Settings_Manager_page**: Module 6.
20. **target_mutation_path**: `SettingsMutationPipeline` (BTD6
    cache scalars + future per-guild scalars);
    `BindingMutationPipeline` (`btd6.strategy_submission_channel`,
    M4); `services.btd6_strategy_mutation` (audited strategy
    state transitions); `services.btd6_source_mutation` (audited
    source registry edits).
21. **target_help_or_menu_route**: existing; BTD6 reachable via Games
    hub (`parent_hub="games"`).
22. **provisionable_resources**: none.
23. **priority**: `P1` — Module 4 of the AI/BTD6 plan.
24. **recommended_PR_phase**: lands with Module 4; settings expand in
    Module 6.

### btd6_reference

1. **cog_module**: `disbot/cogs/btd6_reference_cog.py`
2. **subsystem**: `btd6` (sibling cog — static game-data lookups split out so
   `btd6_cog.py` stays under the 800-LOC ceiling; class name maps to no
   SUBSYSTEMS key, so it shares the `btd6` subsystem like `btd6_ops`).
3. **current_commands**: `!btd6ref tower <name>`, `!btd6ref hero <name>`,
   `!btd6ref round <N>`, `!btd6ref relic <name>`, `!btd6ref ct`. Slash twins
   under `/btd6ref`. Also reachable from `BTD6PanelView` (`!btd6`).
4. **current_command_groups**: `btd6ref` (prefix) / `/btd6ref` (app group).
5. **current_command_panel_or_menu**: none of its own — surfaced via the
   shared `BTD6PanelView`.
6. **help_menu_discoverable**: via the BTD6 panel (the `btd6` subsystem owns
   `build_help_menu_view`).
7-22. inherit the `btd6` subsystem's settings / access / mutation posture
   (deterministic reference reads; no settings, no mutations).
23. **priority**: `P1` — BTD6 cog-split foundation.
24. **recommended_PR_phase**: ships with the BTD6 cog split.

### btd6_events

1. **cog_module**: `disbot/cogs/btd6_events_cog.py`
2. **subsystem**: `btd6` (sibling cog — live Ninja Kiwi events / leaderboards /
   source diagnostics / grounding, split out of `btd6_cog`).
3. **current_commands**: `!btd6events live`, `!btd6events event`,
   `!btd6events leaderboard`, `!btd6events sources`,
   `!btd6events source-health`, `!btd6events latest-data`,
   `!btd6events refresh-source <key>` (manage-guild), `!btd6events grounding`.
   Slash twins under `/btd6events`.
4. **current_command_groups**: `btd6events` (prefix) / `/btd6events` (app group).
5. **current_command_panel_or_menu**: none of its own — surfaced via
   `BTD6PanelView`.
6. **help_menu_discoverable**: via the BTD6 panel.
7-22. inherit the `btd6` subsystem posture; `refresh-source` writes flow
   through `services.btd6_source_mutation` (audited), never the cog directly.
23. **priority**: `P1` — BTD6 cog-split foundation.
24. **recommended_PR_phase**: ships with the BTD6 cog split.

### btd6_strategy

1. **cog_module**: `disbot/cogs/btd6_strategy_cog.py`
2. **subsystem**: `btd6` (sibling cog — strategy memory browse/submit/review +
   `why-no-response`, split out of `btd6_cog`).
3. **current_commands**: `!btd6strat browse`, `!btd6strat mine`,
   `!btd6strat strategy <id>`, `!btd6strat strategy-audit <id>`,
   `!btd6strat submit` (slash opens a modal), `!btd6strat pending`
   (manage-guild), `!btd6strat strategies`, `!btd6strat why-no-response`.
   Slash twins under `/btd6strat`.
4. **current_command_groups**: `btd6strat` (prefix) / `/btd6strat` (app group).
5. **current_command_panel_or_menu**: none of its own — surfaced via
   `BTD6PanelView`.
6. **help_menu_discoverable**: via the BTD6 panel.
7-22. inherit the `btd6` subsystem posture; submissions + review transitions
   flow through `services.btd6_strategy_mutation` (audited).
23. **priority**: `P1` — BTD6 cog-split foundation.
24. **recommended_PR_phase**: ships with the BTD6 cog split.

### paragon

1. **cog_module**: `disbot/cogs/paragon_cog.py`
2. **subsystem**: `btd6` (Paragon degree calculator — a BTD6 feature given a
   thin command surface of its own so `btd6_cog.py` stays under the 800-LOC
   ceiling).
3. **current_commands**: `!paragon` opens the Paragon degree calculator.
   Also reachable from the 🔮 Paragon button on `BTD6PanelView` (`!btd6`).
4. **current_command_groups**: none (single prefix command).
5. **current_command_panel_or_menu**: `!paragon` opens
   `ParagonCalculatorView` (ephemeral) — selects for paragon / players /
   difficulty / extra-T5, plus modals for the numbers and the target degree.
6. **help_menu_discoverable**: Yes — prefix command plus the BTD6 panel button.
7. **dedicated_panel_command**: `!paragon`.
8. **help_menu_direct_navigation_hook**: `views.btd6.paragon_view.open_paragon_calculator`.
9. **existing_SettingSpec_declarations**: none.
10. **existing_settings_keys**: none.
11. **existing_BindingSpec_entries**: none.
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: `visibility_tier=user` (read-only
    calculator; no mutations).
14. **hardcoded_or_env_only_behavior**: `PARAGON_API_BASE_URL` /
    `PARAGON_API_KEY` (env, optional); committed medium base prices in
    `disbot/utils/btd6/paragon_math.py`.
15. **missing_customization_commands**: none planned.
16. **missing_settings_pages**: none planned.
17. **missing_menu_buttons_selects_modals**: none.
18. **setting_class_per_value**: n/a (no settings).
19. **target_Settings_Manager_page**: n/a.
20. **target_mutation_path**: n/a (read-only; external API + local math via
    `services.paragon_service`).
21. **target_help_or_menu_route**: existing; reachable from the BTD6 hub panel
    button and `!paragon`.
22. **provisionable_resources**: none.
23. **priority**: `P2` — BTD6 Paragon calculator.
24. **recommended_PR_phase**: ships with the Paragon calculator feature.

### btd6_ops

1. **cog_module**: `disbot/cogs/btd6_ops_cog.py`
2. **subsystem**: `btd6` (operator surface for BTD6 ingestion — given its own
   thin cog so `btd6_cog.py` stays under the 800-LOC ceiling).
3. **current_commands**: `!btd6ops readiness` (ingestion readiness verdict),
   `!btd6ops runs` (recent ingestion runs), `!btd6ops source_enable <key>` /
   `!btd6ops source_disable <key>` (toggle a source). Slash twins under
   `/btd6ops`. Also reachable from the 🛠️ Admin sub-panel on `!btd6`.
4. **current_command_groups**: `btd6ops` (prefix group) / `/btd6ops` (app group).
5. **current_command_panel_or_menu**: the BTD6 Admin panel
   (`views.btd6.admin_panel.BTD6AdminView`) exposes Readiness, Recent Runs, and
   a source enable/disable select + buttons.
6. **help_menu_discoverable**: Yes — prefix + slash commands and the admin panel.
7. **dedicated_panel_command**: opened via the 🛠️ Admin button on `!btd6`.
8. **help_menu_direct_navigation_hook**: `views.btd6.admin_panel.BTD6AdminView.create`.
9. **existing_SettingSpec_declarations**: none.
10. **existing_settings_keys**: none.
11. **existing_BindingSpec_entries**: none.
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: mixed — readiness/runs require staff
    (`is_staff_member`); source enable/disable require administrator
    (`is_administrator_member`), matching `btd6_source_mutation._check_admin`.
14. **hardcoded_or_env_only_behavior**: `BTD6_INGESTION_ENABLED` (env gate; the
    readiness verdict reports the env-off state distinctly).
15. **missing_customization_commands**: none planned.
16. **missing_settings_pages**: none planned.
17. **missing_menu_buttons_selects_modals**: none.
18. **setting_class_per_value**: n/a (no settings).
19. **target_Settings_Manager_page**: n/a.
20. **target_mutation_path**: source toggles write through
    `services.btd6_source_mutation.set_enabled` (audited); reads via
    `services.btd6_ops_readiness_service` + `utils.db.btd6_sources`.
21. **target_help_or_menu_route**: existing; the BTD6 hub Admin panel and
    `!btd6ops` / `/btd6ops`.
22. **provisionable_resources**: none.
23. **priority**: `P2` — BTD6 ingestion operations.
24. **recommended_PR_phase**: ships with the BTD6 operator-visibility feature.

### settings

1. **cog_module**: `disbot/cogs/settings_cog.py` (added in S5).
2. **subsystem**: `settings`
3. **current_commands**: `!settings` (group root that opens the Settings
   Manager hub).
4. **current_command_groups**: `!settings` (administrator-tier; entry
   point declared in `SUBSYSTEMS["settings"].entry_points`).
5. **current_command_panel_or_menu**: `!settings` IS the panel command;
   no `*menu` alias.
6. **help_menu_discoverable**: Yes via SUBSYSTEMS — registered in
   `utils.subsystem_registry.SUBSYSTEMS` at admin tier with
   `entry_points=["settings"]`.
7. **dedicated_panel_command**: `!settings` (the cog's only command).
8. **help_menu_direct_navigation_hook**: Yes — `SettingsCog.build_help_menu_view`
   returns the same `(embed, view)` the `!settings` command produces, so
   the help dropdown navigates straight into the hub.
9. **existing_SettingSpec_declarations**: none. The cog itself does not
   declare scalar settings; it is a read-only browser over the *other*
   subsystems' schemas.  A future PR may add cog-local preferences
   (e.g. `hub_page_size`) if needed.
10. **existing_settings_keys**: none.
11. **existing_BindingSpec_entries**: none.
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: `visibility_tier=administrator`;
    capabilities `settings.manager.view`.  Runtime behaviour gated on
    the `settings.manager_cog.enabled` feature flag (default OFF) —
    when OFF, invocations return a clearly-worded disabled embed.
14. **hardcoded_or_env_only_behavior**: none.  The S5 view module
    composes S1 (`SettingsRegistry`), S2 (`CustomizationCatalogue`),
    S3 (`SettingsResolution`), S4 (`settings_mutation_audit`), and
    `core.runtime.bindings.get_binding` for read-only rendering.
15. **missing_customization_commands**: none.  The hub already
    surfaces every subsystem's settings/bindings/resources page.
16. **missing_settings_pages**: edit / reset flows (S6); logging
    create-or-select flow (S7); cleanup expansion (S8); access policy
    manager (S9); per-subsystem setup packs (S10).
17. **missing_menu_buttons_selects_modals**: scalar-edit modals (S6);
    binding-select views (S7+); reset buttons (S6); setup-pack
    confirmation modals (S10).
18. **setting_class_per_value**: n/a — this subsystem is the
    *management surface* for every other subsystem's settings, not a
    settings consumer itself.
19. **target_Settings_Manager_page**: `!settings` (this cog hosts the
    hub).
20. **target_mutation_path**: read-only in S5; consumes
    `SettingsMutationPipeline` (S4) for S6+, `BindingMutationPipeline`
    + `ResourceProvisioningPipeline` (S4.5) for S7+,
    `GovernanceMutationPipeline` for S9.
21. **target_help_or_menu_route**: Help direct-nav (already wired);
    `!adminmenu` and `!platform` deep-links land in S11.
22. **provisionable_resources**: none.  The Settings Manager UI runs
    in any text channel; it does not require dedicated channels or
    roles.
23. **priority**: `P0` — gates discoverability for every other
    subsystem's settings page.
24. **recommended_PR_phase**: S5 (this cog) + S6 (edit/reset) + S7+
    (per-subsystem write surfaces).

### logging

1. **cog_module**: `disbot/cogs/logging/schemas.py` (S7a) — schema-only;
   the `!logging` group still lives in `disbot/cogs/admin_cog.py:211`
   until S7d extracts a dedicated `LoggingCog`.
2. **subsystem**: `logging`
3. **current_commands**: `!logging status`, `!logging test` (admin tier).
4. **current_command_groups**: `!logging` (group at `admin_cog.py:211`).
5. **current_command_panel_or_menu**: none yet — S7d adds the panel.
   Discoverability passes today via `KNOWN_PANEL_COMMANDS`
   (`("logging", "logging")`).
6. **help_menu_discoverable**: Yes via SUBSYSTEMS — registered at
   administrator tier with `entry_points=["logging"]`.  Help-menu
   direct-nav routes through `AdminCog.build_help_menu_view` until
   S7d ships the logging-specific panel.
7. **dedicated_panel_command**: deferred to S7d.
8. **help_menu_direct_navigation_hook**: indirect (`AdminCog` owns
   `!logging`).  S7d adds a logging-specific
   `build_help_menu_view`.
9. **existing_SettingSpec_declarations**: `enabled` (bool, default
   False), `auto_create_channels` (bool, default False).  Both point
   at the existing legacy keys via `settings_key=` so the S6
   edit/reset flows mutate them through `SettingsMutationPipeline`
   today.
10. **existing_settings_keys**: `LOGGING_ENABLED`,
    `LOGGING_AUTO_CREATE_CHANNELS` from `utils.settings_keys.logging`.
    The two channel-id keys (`LOGGING_MOD_CHANNEL`,
    `LOGGING_CLEANUP_CHANNEL`) are legacy and are migrating to
    bindings in S7b.
11. **existing_BindingSpec_entries**: `mod_channel`, `cleanup_channel`
    — both `BindingKind.CHANNEL`, optional.  Declared in S7a; S7b
    wires the mutation path through `BindingMutationPipeline`.
    Phase 9a (schema v2) adds five severity/source slots, all
    `BindingKind.CHANNEL`, all optional, all falling back to
    `mod_channel` when unset: `debug_channel`, `info_channel`,
    `warning_channel`, `error_channel`, `audit_channel`. No subscriber
    publishes into these yet — publisher callsites land in Phase 9c.
12. **existing_ResourceRequirement_entries**: `mod_log` channel
    (`bot-mod-log`, RECOMMENDED), `cleanup_log` channel
    (`bot-cleanup-log`, RECOMMENDED).  Both link to the declared
    bindings via `binding_name=`.  Phase 9a adds five matching
    RECOMMENDED requirements with `bot-debug-log` / `bot-info-log` /
    `bot-warning-log` / `bot-error-log` / `bot-audit-log` suggested
    names. Auto-create stays OFF by default.
13. **current_access_policy_behavior**: `visibility_tier=administrator`;
    capabilities `logging.settings.configure`, `logging.channel.bind`,
    `logging.channel.create`.  Master switch `logging.enabled`
    defaults to OFF; the service in `services/server_logging.py`
    stays inert until an operator opts in.
14. **hardcoded_or_env_only_behavior**: `DEFAULT_MOD_CHANNEL_NAME` /
    `DEFAULT_CLEANUP_CHANNEL_NAME` are module-level constants in
    `utils.settings_keys.logging`; the create-channel flow (S7c)
    uses the schema's `suggested_name` instead, so these constants
    become a legacy fallback once S7c lands.
15. **missing_customization_commands**: existing-channel selection
    (S7b), create-new-channel flow (S7c), per-event-class routing
    (deferred — not in S7 scope).
16. **missing_settings_pages**: bind-existing-channel flow (S7b),
    create-channel preview/confirm flow (S7c), logging admin panel
    (S7d).
17. **missing_menu_buttons_selects_modals**: `LogChannelSelectView`
    (S7b), `LogChannelProvisionView` + confirmation modal (S7c),
    logging admin panel buttons (S7d).
18. **setting_class_per_value**: scalar (`enabled`,
    `auto_create_channels`); binding (`mod_channel`,
    `cleanup_channel`); provisionable resource (`mod_log`,
    `cleanup_log`).
19. **target_Settings_Manager_page**: `!settings → logging` — the
    page renders from the registered `LOGGING_CONFIG_SCHEMA` already.
20. **target_mutation_path**: scalar edits via
    `SettingsMutationPipeline` (S6 — works today); channel binding
    via `BindingMutationPipeline` (S7b); channel creation via
    `ResourceProvisioningPipeline` (S7c).
21. **target_help_or_menu_route**: Help direct-nav routes via
    `KNOWN_PANEL_COMMANDS` today; dedicated logging panel via
    `build_help_menu_view` in S7d.
22. **provisionable_resources**: `mod_log` channel,
    `cleanup_log` channel — both RECOMMENDED priority, both consumed
    by S7c.
23. **priority**: `P1` — first real binding/provisioning consumer in
    the Settings Manager.
24. **recommended_PR_phase**: S7a (schema, this PR) + S7b
    (binding-select) + S7c (provisioning preview/confirm) + S7d
    (panel + Help / Admin integration).

## Setting class summary

Cross-cut by class, this is the work distribution implied by the per-cog
inventory above.

- **scalar setting** — moderation (`warn_threshold`, `warn_timeout_minutes`),
  xp (`xp_min`, `xp_max`, `xp_cooldown`), economy
  (`_DAILY_COOLDOWN`/`_WORK_COOLDOWN` to be promoted), mining (ore weights,
  cooldown — to be promoted), proof_channel (default duration — to be
  promoted), logging (`logging.enabled`, `logging.auto_create_channels`).
- **binding** — economy (`log_channel`), xp (`announce_channel`), moderation
  (`mod_log` — to be promoted in S10), proof_channel (`proof_channel`,
  `approval_role` — to be promoted), role (`default_role`,
  `role_menu_channel` — to be promoted), logging (`mod_channel`,
  `cleanup_channel`).
- **access policy** — every subsystem declares a `visibility_tier` in
  `SUBSYSTEMS` and capabilities; S9 lands the manager-cog editor.
- **list setting** — role (`SKIP_ROLES`), cleanup (`ignored_channels` CSV
  pending v2 typed promotion, `prohibited_words` pending v3),
  counting (`skip_numbers`), mining (`ORE_WEIGHTS` weighted list).
- **channel-scoped policy** — cleanup v2 typed policies; admin uses
  `governance/cleanup_policies` table today.
- **per-user preference** — none in v1 of this roadmap.
- **runtime diagnostic** — diagnostic cog read-only views.

## Setup-readiness blocker references

The following blocker tags from `services.platform_consistency.SETUP_READINESS_BLOCKERS`
gate the roadmap; the doc test asserts every one is referenced here.

- `command_surface_ledger` — closed by PR #90; backs S2 catalogue lookups.
- `panel_registry` — partial via panel detection in S2; full registry deferred.
- `settings_registry` — opens with S1 read-only registry.
- `settings_mutation_pipeline` — opens with S4 (canonical scalar writer).
- `governance_trusted_role_schema` — used by S9 access-policy editor.
- `role_service_extraction` — backs role bindings in S10.
- `cleanup_policy_extraction` — backs S8 cleanup ownership.
- `logging_settings_integration` — backs S7 (settings + binding +
  resource_provisioning split).
- `slash_panel_entrypoints` — backs S11 discoverability pass.
- `setup_wizard_readiness_bridge` — backs S12 planning doc.
- `setup_wizard` — long-term consumer; never owner of any pipeline.

## Cross-cutting settings keys (not subsystem-owned)

Some keys exposed by `disbot/utils/settings_keys/__init__.py:__all__` are not
owned by any single cog and instead serve cross-cutting concerns. They are
documented here so the inventory remains complete.

- **Logging** keys (currently surfaced via the `admin` cog's `!logging`
  subgroup; promoted to a dedicated `settings_cog` in S5 / S7):
  - `LOGGING_ENABLED` — scalar setting (`SettingsMutationPipeline` after S4).
  - `LOGGING_AUTO_CREATE_CHANNELS` — scalar setting; flips the implicit
    confirmation rule for `ResourceProvisioningPipeline` channel creation
    (see [`docs/setup-platform/resource-provisioning-overview.md`](resource-provisioning-overview.md)).
  - `LOGGING_MOD_CHANNEL` — legacy KV mirror of the `logging.mod_channel`
    binding; long-term storage is the `subsystem_bindings` row written by
    `BindingMutationPipeline` (called by `ResourceProvisioningPipeline`
    step 8).
  - `LOGGING_CLEANUP_CHANNEL` — legacy KV mirror of the
    `logging.cleanup_channel` binding; same storage discipline.
  - `DEFAULT_MOD_CHANNEL_NAME`, `DEFAULT_CLEANUP_CHANNEL_NAME` — string
    defaults used by `ResourceProvisioningPipeline` when no
    `ProvisioningHint.suggested_name` overrides apply.
- **Governance** keys (owned by the `governance/` package, not a cog):
  - `GOVERNANCE_VERSION` — version of the governance subscriptions /
    visibility schema; bumped when shape changes.
  - `TRUSTED_TIER_ROLE_ID` — role ID for the `TRUSTED` permission tier
    (see `disbot/governance/permission_tiers.py`); editable through the
    Access Policy Manager in S9.

Each key above is intentionally referenced here so the S0 doc test
(`test_existing_settings_keys_constants_referenced`) can verify the
inventory stays in sync with `settings_keys.__all__` without depending on
runtime imports.

## Cross-references

- `disbot/utils/subsystem_registry.py:SUBSYSTEMS` — 21 subsystem manifest.
- `disbot/config.py:INITIAL_EXTENSIONS` — 20 cog loader list.
- `disbot/core/runtime/subsystem_schema.py` — `register(...)` helper for
  `SettingSpec` / `BindingSpec` / `ResourceRequirement`.
- `disbot/core/runtime/resource_specs.py` — `ResourceKind`,
  `ProvisioningPriority`, `ProvisioningHint`, `ResourceRequirement` data
  classes.
- `disbot/core/runtime/command_surface_ledger.py` — runtime ledger walked by
  S2 / S2.5 catalogues.
- `disbot/services/platform_consistency.py:SETUP_READINESS_BLOCKERS` — gates
  the roadmap.
- `disbot/services/governance_service.py` — runtime access-policy resolution.
- `disbot/utils/settings_keys/` — per-subsystem `SettingKey` constants.
- `disbot/cogs/xp/schemas.py`, `disbot/cogs/moderation/schemas.py`,
  `disbot/cogs/economy/schemas.py` — the three schema modules registered
  today; S5-S10 adds more.
