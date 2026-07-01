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

The 50 extensions loaded at startup come from
`disbot/config.py:INITIAL_EXTENSIONS`. The 37 subsystems live in
`disbot/utils/subsystem_registry.py:SUBSYSTEMS`; each has exactly one owning
cog. The 14 loaded extensions that are **not** one-to-one subsystems are
`bootstrap_access_cog` (command-admission guard), `hermes_cog` (the
Hermes→Claude dispatch bridge — admin-only slash commands with no subsystem
row), `media_maintenance_cog` (the YouTube cache-retention task owner — no
commands, no subsystem row), `health_maintenance_cog` (the health-findings
retention task owner — no commands, no subsystem row), `role_grants_cog` (the
temporary-role expiry sweep loop + the `!temprole` grant command — backs the
role product, no subsystem row), `creature_battle_cog` (the creature PvP
`!cbattle` command — part of the Creatures subsystem, surfaced via
`creature_cog`'s hook, no subsystem row), `starboard_cog` (the Starboard /
Hall-of-Fame raw-reaction listener + the `!starboard` config command — no
subsystem row), `ai_review_cog` (the AI answer review log — a 👎 / correction-reply
listener (the `ai_correction` message-pipeline stage) plus the `!aireview` staff
command that sets the `AI_REVIEW_CHANNEL` channel pointer — no subsystem row),
`setup_cog` (the advanced setup wizard surface — `!setupadvanced` /
`/setup-advanced`), `quicksetup_cog`
(the Essential Setup front door — the primary `!setup` / `/setup`, no
subsystem row), and the
five split BTD6 cogs (`btd6_reference_cog`, `btd6_events_cog`,
`btd6_strategy_cog`, `paragon_cog`, `btd6_ops_cog`), which all surface under
the single `btd6` subsystem. (Counts re-verified against source 2026-06-21;
`starboard_cog` added 2026-06-21.)

Cogs (53): `admin_cog`, `ai_cog`, `automod_cog`, `blackjack_cog`, `casino_cog`,
`bootstrap_access_cog`, `btd6_cog`, `btd6_events_cog`, `btd6_ops_cog`,
`btd6_reference_cog`, `btd6_strategy_cog`, `chain_cog`, `channel_cog`,
`cleanup_cog`, `community_cog`, `community_spotlight_cog`, `counters_cog`,
`counting_cog`, `creature_battle_cog`, `creature_cog`, `deathmatch_cog`,
`diagnostic_cog`, `economy_cog`, `fishing_cog`, `four_twenty_cog`,
`games_cog`, `general_cog`, `health_maintenance_cog`, `help_cog`,
`hermes_cog`, `image_moderation_cog`, `inventory_cog`, `karma_cog`, `leaderboard_cog`,
`logging_cog`, `media_maintenance_cog`, `mining_cog`, `moderation_cog`,
`paragon_cog`, `proof_channel_cog`, `role_cog`, `role_grants_cog`,
`rps_tournament_cog`, `security_cog`, `server_management_cog`, `settings_cog`,
`setup_cog`, `starboard_cog`, `treasury_cog`, `utility_cog`, `ux_lab_cog`,
`welcome_cog`, `xp_cog`.

Subsystems (40): `admin`, `ai`, `automod`, `blackjack`, `casino`, `btd6`, `chain`,
`channel`, `cleanup`, `community`, `community_spotlight`, `counters`,
`counting`, `creature`, `deathmatch`, `diagnostic`, `economy`, `fishing`,
`four_twenty`, `games`, `general`, `help`, `image_moderation`, `inventory`,
`karma`, `leaderboard`, `logging`, `mining`, `moderation`, `proof_channel`, `role`,
`rps_tournament`, `security`, `server_management`, `settings`, `treasury`,
`utility`, `ux_lab`, `welcome`, `xp`.

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
   `dm_actions`, `dm_template`, `require_reason`, `ban_delete_message_days`,
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
    `MOD_WARN_ESCALATION_ACTION`, `MOD_DM_ON_ACTION`, `MOD_DM_ACTIONS`,
    `MOD_DM_TEMPLATE`,
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
    (`dm_on_action` / `dm_template`; `dm_actions` later added the per-action
    allow-list gating the DM master switch — Q-0147), the ban message-purge window
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
    `dm_actions` free-text (csv subset of warn/timeout/kick/ban — the per-action
    DM allow-list gating `dm_on_action`), `dm_template` free-text,
    `require_reason` bool toggle,
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

### automod

automod v1 (owner decision Q-0108) — the automated message-filter layer beneath
manual moderation; the twin of `cleanup` (auto-mod pipeline tier, parented to the
moderation hub). Detection lives in `services/automod_service.py`; actions route
through `moderation_service` (no parallel audit path).

1. **cog_module**: `disbot/cogs/automod_cog.py` (+ `disbot/cogs/automod/`
   subpackage with `schemas.py` + `listener.py`).
2. **subsystem**: `automod`
3. **current_commands**: `!automod` (read-only policy summary).
4. **current_command_groups**: none.
5. **current_command_panel_or_menu**: none (config via `!settings` → Automod).
6. **help_menu_discoverable**: Yes — `SUBSYSTEMS["automod"]` lists `automod`.
7. **dedicated_panel_command**: `none`.
8. **help_menu_direct_navigation_hook**: `build_help_menu_view` (policy summary).
9. **existing_SettingSpec_declarations**: `enabled`, `spam_enabled`,
   `invites_enabled`, `caps_enabled`, `mentions_enabled`, `spam_count`,
   `spam_window_seconds`, `caps_percent`, `mentions_count`, `exempt_roles`,
   `exempt_channels` (`disbot/cogs/automod/schemas.py`). All flags default OFF;
   defaults + bounds are the single source of truth in
   `disbot/services/automod_config.py`.
10. **existing_settings_keys**: `AUTOMOD_ENABLED`, `AUTOMOD_SPAM_ENABLED`,
    `AUTOMOD_INVITES_ENABLED`, `AUTOMOD_CAPS_ENABLED`, `AUTOMOD_MENTIONS_ENABLED`,
    `AUTOMOD_SPAM_COUNT`, `AUTOMOD_SPAM_WINDOW_SECONDS`, `AUTOMOD_CAPS_PERCENT`,
    `AUTOMOD_MENTIONS_COUNT`, `AUTOMOD_EXEMPT_ROLES`, `AUTOMOD_EXEMPT_CHANNELS`
    (`disbot/utils/settings_keys/automod.py`). Stored as scalar guild settings —
    **no migration**.
11. **existing_BindingSpec_entries**: none.
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: `visibility_tier=administrator`;
    capability `automod.settings.configure`; spec edits gated on
    `moderation.settings.configure` (automod *is* moderation's automated layer).
14. **hardcoded_or_env_only_behavior**: none — every rule + threshold + exempt
    list is operator config; a fresh guild is unaffected (all flags default OFF).
15. **current_resource_dependencies**: none (no channels/roles required).
16. **target_settings_fields**: the four rule toggles + thresholds + the two
    exempt lists (`mock_automod_rules` is the reviewed UX target).
17. **target_bindings**: none in v1.
18. **target_access_controls**: administrator floor for config; runtime actions
    are system-actor via `moderation_service` (warn → escalation).
19. **acceptance_or_validation_rules**: thresholds bounded by the
    `MIN_*`/`MAX_*` constants in `automod_config`; exempt lists must be numeric
    ids (CSV).
20. **target_mutation_path**: `SettingsMutationPipeline` (scalars). Actions are
    not a settings mutation — they route through `moderation_service`.
21. **target_help_or_menu_route**: Help direct-nav (policy summary), Settings
    → Automod group.

### karma

Karma (thanks/upvote reputation, 2026-06-22) — members grant each other peer
reputation; per-user totals + a leaderboard category on an audited mutation seam
(`services/karma_service.py`), modelled on economy/XP.

1. **cog_module**: `disbot/cogs/karma_cog.py` (+ `disbot/cogs/karma/` subpackage
   with `schemas.py`).
2. **subsystem**: `karma` (homed under the Community hub).
3. **current_commands**: `!thanks @user [reason]` (aliases `!rep`/`!thank`),
   `!karma [member]` (group; `!karma give @user`), `/karma [member]`.
4. **current_command_groups**: `!karma` (with the `give` subcommand).
5. **current_command_panel_or_menu**: the karma card embed (via the Community hub
   button / `build_help_menu_view`).
6. **help_menu_discoverable**: Yes — `SUBSYSTEMS["karma"]` + `build_help_menu_view`.
7. **dedicated_panel_command**: `none` (card-style embed, no interactive hub yet).
8. **help_menu_direct_navigation_hook**: `build_help_menu_view` (the viewer's card).
9. **existing_SettingSpec_declarations**: `enabled`, `cooldown_seconds`,
   `daily_cap`, `reaction_emoji` (`disbot/cogs/karma/schemas.py`). Defaults + bounds
   are the single source of truth in `disbot/services/karma_config.py`. The
   `reaction_emoji` trigger (empty = off) drives the react-to-thank listener in
   `karma_cog` — reacting with it grants karma through the same audited seam.
10. **existing_settings_keys**: `KARMA_ENABLED`, `KARMA_COOLDOWN`,
    `KARMA_DAILY_CAP`, `KARMA_REACTION_EMOJI` (`disbot/utils/settings_keys/karma.py`).
    Stored as scalar guild settings — schema-declared, with the two karma tables in
    migration 093.
11. **existing_BindingSpec_entries**: none.
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: `visibility_tier=user`; grant/card are
    user-tier; config edits gated on `karma.settings.configure`.
14. **hardcoded_or_env_only_behavior**: none — cooldown, daily cap, and the master
    switch are all operator config (with code-level defaults).
15. **current_resource_dependencies**: none (no channels/roles required).
16. **target_settings_fields**: the master switch + cooldown + daily cap.
17. **target_bindings**: none in v1 (an optional announcement channel is a
    deferred PR-3 follow-up).
18. **target_access_controls**: user-tier grants (anti-abuse enforced in the
    service); administrator floor for config.
19. **acceptance_or_validation_rules**: cooldown/cap bounded by the `MIN_*`/`MAX_*`
    constants in `karma_config`; grants are positive-only, no self/bot, and rate-
    limited by the per-(giver→receiver) cooldown + per-giver daily cap.
20. **target_mutation_path**: `SettingsMutationPipeline` (scalars). Grants route
    through `karma_service.give` (audited, INV-K), never a settings mutation.
21. **target_help_or_menu_route**: Community hub button, Settings → Karma group.

### image_moderation

image moderation v1 (owner decision Q-0108) — the automated **image**-filter
layer beneath manual moderation; the image twin of `automod` (auto-mod pipeline
tier, parented to the moderation hub). Pure detection lives in
`services/image_moderation_service.py`; the OpenAI `omni-moderation-latest` call
lives in `core/runtime/ai/providers/openai_moderation.py` (the invariant SDK
chokepoint); actions route through `moderation_service` (no parallel audit path).

1. **cog_module**: `disbot/cogs/image_moderation_cog.py` (+
   `disbot/cogs/image_moderation/` subpackage with `schemas.py` + `listener.py`).
2. **subsystem**: `image_moderation`
3. **current_commands**: `!imagemod` (read-only policy summary).
4. **current_command_groups**: none.
5. **current_command_panel_or_menu**: none (config via `!settings` → Image moderation).
6. **help_menu_discoverable**: Yes — `SUBSYSTEMS["image_moderation"]` lists `imagemod`.
7. **dedicated_panel_command**: `none`.
8. **help_menu_direct_navigation_hook**: `build_help_menu_view` (policy summary).
9. **existing_SettingSpec_declarations**: `enabled`, `sexual_enabled`,
   `violence_enabled`, `harassment_enabled`, `hate_enabled`, `threshold_percent`,
   `exempt_roles`, `exempt_channels` (`disbot/cogs/image_moderation/schemas.py`).
   All flags default OFF; defaults + bounds are the single source of truth in
   `disbot/services/image_moderation_config.py`.
10. **existing_settings_keys**: `IMAGE_MODERATION_ENABLED`,
    `IMAGE_MODERATION_SEXUAL_ENABLED`, `IMAGE_MODERATION_VIOLENCE_ENABLED`,
    `IMAGE_MODERATION_HARASSMENT_ENABLED`, `IMAGE_MODERATION_HATE_ENABLED`,
    `IMAGE_MODERATION_THRESHOLD_PERCENT`, `IMAGE_MODERATION_EXEMPT_ROLES`,
    `IMAGE_MODERATION_EXEMPT_CHANNELS`
    (`disbot/utils/settings_keys/image_moderation.py`). Stored as scalar guild
    settings — **no migration**.
11. **existing_BindingSpec_entries**: none.
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: `visibility_tier=administrator`;
    capability `image_moderation.settings.configure`; spec edits gated on
    `moderation.settings.configure` (image moderation *is* moderation's automated
    image layer).
14. **hardcoded_or_env_only_behavior**: the OpenAI key is read from
    `OPENAI_API_KEY` (shared with the AI cog); when absent the stage fails open
    (no image is acted on). Every category + threshold + exempt list is operator
    config; a fresh guild is unaffected (all flags default OFF).
15. **current_resource_dependencies**: none (no channels/roles required); the
    external OpenAI moderation endpoint is the only runtime dependency.
16. **target_settings_fields**: the four category toggles + the threshold + the
    two exempt lists (reuses the automod panel shape — `mock_automod_rules`).
17. **target_bindings**: none in v1.
18. **target_access_controls**: administrator floor for config; runtime actions
    are system-actor via `moderation_service` (warn → escalation).
19. **acceptance_or_validation_rules**: threshold bounded by the
    `MIN_/MAX_THRESHOLD_PERCENT` constants in `image_moderation_config`; exempt
    lists must be numeric ids (CSV).
20. **target_mutation_path**: `SettingsMutationPipeline` (scalars). Actions are
    not a settings mutation — they route through `moderation_service`.
21. **target_help_or_menu_route**: Help direct-nav (policy summary), Settings
    → Image moderation group.
22. **privacy_disclosure**: when on, the image **URL** (only) is sent to OpenAI's
    free moderation endpoint — disclosed in the master-switch setting hint;
    operators should surface external image analysis in their server rules.
22. **provisionable_resources**: none.
23. **priority**: `P1` — first slice of the safety/community lane (band slot 4).
24. **recommended_PR_phase**: safety-lane PR1 (this PR).

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
9. **existing_SettingSpec_declarations**: _none_.  The `economy_log_channel`
   scalar was **retired in P0-3 arc PR 2 (#794)** — the log channel is a
   Discord-resource pointer and now lives solely in the `log_channel`
   BindingSpec (item 11).  The three write sites (``on_ready``,
   ``on_guild_join``, ``!setlogchannel``) route through
   ``BindingMutationPipeline`` (`actor_type='system'` for the two listener
   paths); reads go through the arbitration ladder
   (``get_economy_log_channel``, binding-first regardless of the
   `bindings.primary` flag).  Daily/work cooldowns pending promotion.
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

### fishing

1. **cog_module**: `disbot/cogs/fishing_cog.py`.
2. **subsystem**: `fishing`
3. **current_commands**: `!fish`, `!fishlog`/`!fishdex`, `!fishtop`/`!topfishers`.
4. **current_command_groups**: none.
5. **current_command_panel_or_menu**: `none` (hub-less; the open-world Explore
   panel that folds in `🎣 Fishing` is a later plan slice).
6. **help_menu_discoverable**: Yes (static overview via `build_help_menu_view`).
7. **dedicated_panel_command**: `none`.
8. **help_menu_direct_navigation_hook**: `build_help_menu_view` (static embed).
9. **existing_SettingSpec_declarations**: none.
10. **existing_settings_keys**: none.
11. **existing_BindingSpec_entries**: none.
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: `visibility_tier=user`; capabilities
    `fishing.catch.fish`, `fishing.collection.view`.
14. **hardcoded_or_env_only_behavior**: the 21-fish dataset (`data/fishing/fish.json`)
    + the 7×3 level/size bands are committed data/code (owner design Q-0175). v1 has
    **no coins** — fish value/use is an explicitly OPEN owner question.
15. **missing_customization_commands**: `!fishing level award set ...` (xp pace),
    fish-value setters (future, once the owner decides the value/cook/sell question).
16. **missing_settings_pages**: Settings Manager fishing page (future).
17. **missing_menu_buttons_selects_modals**: xp-pace scalar editor,
    optional `fishing_channel` BindingSelectView (future).
18. **setting_class_per_value**: xp pace → scalar; optional fishing_channel → binding.
19. **target_Settings_Manager_page**: `!settings subsystem fishing` (future).
20. **target_mutation_path**: `SettingsMutationPipeline` (scalars + list) if
    payouts/weights are ever made configurable.
21. **target_help_or_menu_route**: Help direct-nav (static); Settings tab (future).
22. **provisionable_resources**:
    `(fishing_channel, CHANNEL, OPTIONAL, fishing-panel, Games, public-text)`
    (proposed for a later slice — not declared yet).
23. **priority**: `P2`.
24. **recommended_PR_phase**: S10.

### creature

1. **cog_module**: `disbot/cogs/creature_cog.py`.
2. **subsystem**: `creature`
3. **current_commands**: `!catch`/`!hunt`, `!dex`/`!collection`/`!creatures`,
   `!dextop`/`!topcatchers`.
4. **current_command_groups**: none.
5. **current_command_panel_or_menu**: `none` (hub-less; the open-world Explore
   panel that folds in `🐾 Creatures` is a later plan slice).
6. **help_menu_discoverable**: Yes (static overview via `build_help_menu_view`).
7. **dedicated_panel_command**: `none`.
8. **help_menu_direct_navigation_hook**: `build_help_menu_view` (static embed).
9. **existing_SettingSpec_declarations**: none.
10. **existing_settings_keys**: none.
11. **existing_BindingSpec_entries**: none.
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: `visibility_tier=user`; capabilities
    `creature.catch.creature`, `creature.collection.view`.
14. **hardcoded_or_env_only_behavior**: the 36-creature dataset
    (`data/creatures/creatures.json`) + the rarity encounter/catch weights are
    committed data/code (owner design Q-0186/Q-0187, no Pokémon IP). v1 has **no
    coins** — the reward is progression (`game_xp`) + the collection dex. The
    level-normalized PvP battle is a later substantial-runtime slice.
15. **missing_customization_commands**: `!creature level award set ...` (xp pace),
    catch-rate setters (future, only if balance is ever made configurable).
16. **missing_settings_pages**: Settings Manager creature page (future).
17. **missing_menu_buttons_selects_modals**: xp-pace scalar editor,
    optional `creature_channel` BindingSelectView (future).
18. **setting_class_per_value**: xp pace → scalar; optional creature_channel → binding.
19. **target_Settings_Manager_page**: `!settings subsystem creature` (future).
20. **target_mutation_path**: `SettingsMutationPipeline` (scalars + list) if
    catch/encounter weights are ever made configurable.
21. **target_help_or_menu_route**: Help direct-nav (static); Settings tab (future).
22. **provisionable_resources**:
    `(creature_channel, CHANNEL, OPTIONAL, creature-panel, Games, public-text)`
    (proposed for a later slice — not declared yet).
23. **priority**: `P2`.
24. **recommended_PR_phase**: S10.

### treasury

1. **cog_module**: `disbot/cogs/treasury_cog.py`.
2. **subsystem**: `treasury`
3. **current_commands**: `!treasury`/`!bank`/`!pool`, `!treasury contribute <amount>`,
   `!treasury grant @member <amount>`.
4. **current_command_groups**: `treasury` (group; subcommands `contribute`, `grant`).
5. **current_command_panel_or_menu**: `TreasuryView` (Contribute · Refresh) —
   `disbot/views/treasury/`; Contribute opens a one-field amount modal.
6. **help_menu_discoverable**: Yes (actionable panel via `build_help_menu_view`).
7. **dedicated_panel_command**: `!treasury`.
8. **help_menu_direct_navigation_hook**: `build_help_menu_view` (live `TreasuryView`).
9. **existing_SettingSpec_declarations**: none.
10. **existing_settings_keys**: none.
11. **existing_BindingSpec_entries**: none.
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: `visibility_tier=user`; capabilities
    `treasury.pool.view`, `treasury.pool.contribute`, `treasury.pool.disburse`.
    Disburse (`!treasury grant`) is additionally gated on Discord `manage_guild`.
14. **hardcoded_or_env_only_behavior**: none — the treasury holds no tunables. It is
    the bot's first **server-owned** (collective) coin pool: members contribute their
    own coins into the guild pool (a sink) and server managers disburse from it (a
    `manage_guild`-gated grant), through the audited `services/treasury_service.py`
    seam (one txn per op; user coin legs via `economy_service.*_in_txn`). The seam
    between the economy (where coins come from) and governance (who may spend them).
15. **missing_customization_commands**: per-guild contribution caps / a configurable
    auto-tithe from game winnings (future).
16. **missing_settings_pages**: Settings Manager treasury page (future — e.g. who may
    disburse, beyond the `manage_guild` default).
17. **missing_menu_buttons_selects_modals**: an in-panel manager Disburse control
    (future; today disburse is command-only by design).
18. **setting_class_per_value**: contribution cap → scalar; disburse-authority role →
    role setting (future).
19. **target_Settings_Manager_page**: `!settings subsystem treasury` (future).

### ticket

1. **cog_module**: `disbot/cogs/ticket_cog.py`.
2. **subsystem**: `ticket`
3. **current_commands**: `!ticket` (hub), `!ticket new <subject>`, `!ticket close [reason]`,
   `!ticket claim`, `!ticket add @user`, `!ticket remove @user`, `!ticketpanel`,
   `!ticketsetup @StaffRole [#log]`, `!ticketlimit <n>`, `!ticketblacklist add|remove @user`.
4. **current_command_groups**: `ticket` (group; subcommands `new`/`close`/`claim`/`add`/`remove`),
   `ticketblacklist` (group; `add`/`remove`).
5. **current_command_panel_or_menu**: `TicketHubView` (Open · My tickets · Post panel) —
   `disbot/views/tickets/`; the public `TicketLauncherView` (persistent "Open a ticket" button)
   and the in-channel `TicketControlView` (Claim · Close); the `TicketOpenModal` collects the subject.
6. **help_menu_discoverable**: Yes (actionable hub via `build_help_menu_view`).
7. **dedicated_panel_command**: `!ticket`.
8. **help_menu_direct_navigation_hook**: `build_help_menu_view` (live `TicketHubView`).
9. **existing_SettingSpec_declarations**: none (config lives in the `ticket_config` table, not the
   KV settings store).
10. **existing_settings_keys**: none.
11. **existing_BindingSpec_entries**: none.
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: `visibility_tier=user`; capabilities `ticket.ticket.open`,
    `ticket.ticket.manage`, `ticket.config.update`. Opening is gated by the per-user open cap +
    blacklist; claim/close/add/remove require the configured staff role or `manage_guild`/admin;
    setup commands require `manage_guild`.
14. **hardcoded_or_env_only_behavior**: none — per-guild config (staff role, ticket category,
    transcript log channel, max-open-per-user, ping-on-open) lives in `ticket_config` (migration 098)
    and is written through the audited `services/ticket_mutation.py` seam. Opening creates a private
    channel through `ChannelLifecycleService` and emits `ticket.opened`; the AI `open_support_ticket`
    tool shares the same audited open path.
15. **missing_customization_commands**: multiple ticket categories/panels with per-category staff
    teams; pre-ticket question forms; auto-close-on-inactivity; feedback ratings (future).
16. **missing_settings_pages**: Settings Manager ticket page (future — staff roles, category, log,
    limits as settings rows).
17. **missing_menu_buttons_selects_modals**: an in-hub setup wizard + a category dropdown on the
    launcher (future; today setup is command-only).
18. **setting_class_per_value**: staff role → role setting; category/log → channel settings;
    max-open → scalar; ping-on-open → boolean (future Settings rows).
19. **target_Settings_Manager_page**: `!settings subsystem ticket` (future).

### farm

1. **cog_module**: `disbot/cogs/farm_cog.py`.
2. **subsystem**: `farm`
3. **current_commands**: `!farm`/`!chickenfarm`/`!coop`.
4. **current_command_groups**: none.
5. **current_command_panel_or_menu**: `FarmMenuView` (Collect · Shop · Refresh) +
   `FarmShopView` (Buy hen · Upgrade coop · Back) — `disbot/views/farm/`.
6. **help_menu_discoverable**: Yes (actionable panel via `build_help_menu_view`).
7. **dedicated_panel_command**: `!farm`.
8. **help_menu_direct_navigation_hook**: `build_help_menu_view` (live `FarmMenuView`).
9. **existing_SettingSpec_declarations**: none.
10. **existing_settings_keys**: none.
11. **existing_BindingSpec_entries**: none.
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: `visibility_tier=user`; capabilities
    `farm.egg.collect`, `farm.coop.manage`.
14. **hardcoded_or_env_only_behavior**: the idle-farm tunables — lay interval, egg
    value, capacity ladder, hen/coop price curves — are committed code
    (`utils/farm/farm.py`). The bot's first **idle** game: eggs accrue over time
    via pure `settle()` (a stored value + a timestamp, no ticker — ADR-001/002),
    are collected for coins (modest faucet) + `game_xp`, and coins buy hens
    (faster lay rate) / coop upgrades (bigger egg cap) through the audited
    `services/farm_workflow.py` seam (one txn per op).
15. **missing_customization_commands**: per-guild faucet-rate setters (future, only
    if egg value / lay rate is ever made configurable).
16. **missing_settings_pages**: Settings Manager farm page (future).
17. **missing_menu_buttons_selects_modals**: faucet-rate scalar editor (future).
18. **setting_class_per_value**: egg value / lay rate → scalar (future).
19. **target_Settings_Manager_page**: `!settings subsystem farm` (future).
20. **target_mutation_path**: `SettingsMutationPipeline` (scalars) if tunables are
    ever made configurable.
21. **target_help_or_menu_route**: Help direct-nav (live panel); Settings tab (future).
22. **provisionable_resources**: none (no channel binding; the farm is per-player).
23. **priority**: `P2`.
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
9. **existing_SettingSpec_declarations**: `xp_min`, `xp_max`, `xp_cooldown`
    (`disbot/cogs/xp/schemas.py`). The `xp_announce_channel` scalar was
    **retired in P0-3 arc PR 2 (#794)** — the announce channel lives solely
    in the `announce_channel` BindingSpec (item 11) now. The range/cooldown
    modals still write scalars through `SettingsMutationPipeline`; the
    channel modal writes the binding via `BindingMutationPipeline`, and
    reads go through the arbitration ladder (`get_xp_announce_channel`,
    binding-first regardless of the `bindings.primary` flag).
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
   `xp_roles_stack`, `reaction_roles_enabled` (`disbot/cogs/role/schemas.py`).
10. **existing_settings_keys**: `SKIP_ROLES` (legacy — no longer read at
    runtime), `TIME_ROLES_STACK`, `XP_ROLES_STACK`, `REACTION_ROLES_ENABLED`
    (`disbot/utils/settings_keys/role.py`).
11. **existing_BindingSpec_entries**: none.
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: `visibility_tier=administrator`;
    capabilities `role.settings.configure`, `role.threshold.configure`,
    `role.assignment.manage`, `role.reaction.manage`.
14. **hardcoded_or_env_only_behavior**: time-based role thresholds. Per-role
    XP/time exemptions are stored in the `role_automation_exemptions` table
    (migration 052), edited via the Roles → Exemptions panel. Temporary roles
    are granted via `!temprole` (`role_grants_cog`) and swept on expiry.
15. **missing_customization_commands**: `!settings role thresholds set ...`.
    (Reaction-role manager UI **shipped** — the Reaction Roles panel is now an
    interactive add/remove/mode editor, overhaul PR 3.)
16. **missing_settings_pages**: thresholds editor page (stacking toggles +
    exemptions + the `reaction_roles_enabled` toggle shipped).
17. **missing_menu_buttons_selects_modals**: time/XP threshold editor
    parity. (Reaction-role manager shipped — overhaul PR 3.)
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
    (e.g. category/name seeds hardcoded in `disbot/config.py` and similar).
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
9. **existing_SettingSpec_declarations**: `spam_window_seconds` — the
    `!cleanuphistory` spam-duplicate detection window, a scalar with a
    `numeric_presets` config-input widget (completion-cert punch #4,
    `disbot/cogs/cleanup/schemas.py`; default 15s, bounds 1..300, capability
    `cleanup.policy.configure`). Governance still owns cleanup_policies; the
    deeper cleanup-level scalars stay roadmap work in S8 v2/v3.
10. **existing_settings_keys**: `CLEANUP_SPAM_WINDOW_SECONDS`
    (`disbot/utils/settings_keys/cleanup.py`) — a scalar guild setting, **no
    migration**. The legacy `CLEANUP_WHITELIST_CHANNELS` env list was removed
    (channel exemption is now a per-channel cleanup policy set to `Off`); only
    the ignored-channel CSV in legacy KV remains to be migrated.
11. **existing_BindingSpec_entries**: none. **Cleanup must not own a
    duplicate `cleanup_log_channel` binding** — the logging subsystem owns
    `cleanup_channel`; cleanup deep-links to it.
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: `visibility_tier=administrator`;
    capabilities `cleanup.word.add`, `cleanup.word.remove`,
    `cleanup.history.scan`, `cleanup.policy.configure`.
14. **hardcoded_or_env_only_behavior**: ignored-channels CSV,
    prohibited-words seed list. (The `CLEANUP_WHITELIST_CHANNELS` env list
    was removed — exemption is a per-channel cleanup policy set to `Off`.)
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

### community_spotlight

1. **cog_module**: `disbot/cogs/community_spotlight_cog.py`.
2. **subsystem**: none (standalone dashboard, no settings subsystem).
3. **current_commands**: `!spotlight` (alias: `!activity` — the greedy
   `!hub`/`!server` aliases were dropped 2026-06-09, Q-0044).
4. **current_command_groups**: none.
5. **current_command_panel_or_menu**: opens `SpotlightView` — live embed
   with server stats, XP/coin leaders, level-up feed, and a Games sub-panel.
6. **help_menu_discoverable**: Yes — registered in `subsystem_registry.py` as a
   `community`-hub child (Q-0025 scaffold lane, 2026-06-09).
7. **dedicated_panel_command**: `!spotlight`.
8. **help_menu_direct_navigation_hook**: `build_help_menu_view` on the cog.
9. **existing_SettingSpec_declarations**: none.
10. **existing_settings_keys**: none.
11. **existing_BindingSpec_entries**: none.
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: `visibility_tier=user`; no
    permission gate — any server member can run `!spotlight`.
14. **hardcoded_or_env_only_behavior**: data sources are hard-coded to
    the `xp` table and `rank_providers` registry; no per-server config.
15. **missing_customization_commands**: no settings surface yet.
16. **missing_settings_pages**: future work — allow admins to pin a
    spotlight channel and configure which panels are shown.
17. **missing_menu_buttons_selects_modals**: none blocking — hook + hub child
    routing in place.
18. **setting_class_per_value**: n/a (no configurable state today).
19. **target_Settings_Manager_page**: future — Spotlight section under
    Community settings.
20. **target_mutation_path**: n/a; read-only dashboard.
21. **target_help_or_menu_route**: DONE — community hub child
    (`parent_hub="community"`).
22. **provisionable_resources**: none.
23. **priority**: `P2` — functional as-is; settings surface is future work.
24. **recommended_PR_phase**: future community-settings PR.

### welcome

welcome v1 (owner decision Q-0110) — the member-greeting layer of the
safety/community platform (band slot 6). Greets members on join, optionally
bids farewell on leave, and optionally grants an entry role the moment a member
joins. Embed-only (the Q-0110 PIL card is phase 2). Deliberately hub-less:
surfaced via its Help hook + `!settings` → Welcome + the `!welcome` summary, so
it does not clutter the user-tier Community hub with operator config. Embeds +
orchestration live in `services/welcome_service.py`; the entry-role grant routes
through `services/role_automation.py` (audited — no parallel role/audit path).

1. **cog_module**: `disbot/cogs/welcome_cog.py` (+ `disbot/cogs/welcome/`
   subpackage with `schemas.py`).
2. **subsystem**: `welcome`
3. **current_commands**: `!welcome` (read-only policy summary).
4. **current_command_groups**: none.
5. **current_command_panel_or_menu**: none (config via `!settings` → Welcome).
6. **help_menu_discoverable**: Yes — `SUBSYSTEMS["welcome"]` lists `welcome`;
   discoverable via the `build_help_menu_view` hook (administrator tier).
7. **dedicated_panel_command**: `none`.
8. **help_menu_direct_navigation_hook**: `build_help_menu_view` (policy summary).
9. **existing_SettingSpec_declarations**: `enabled`, `join_enabled`,
   `leave_enabled`, `channel`, `join_message`, `leave_message`, `entry_role`,
   `card_enabled`, `dm_enabled`, `dm_message`, `min_account_age_days`,
   `delete_after_seconds` (`disbot/cogs/welcome/schemas.py`).
   The master flag defaults OFF; defaults are the single source of truth in
   `disbot/services/welcome_config.py`. `card_enabled` is the welcome **phase 2**
   (Q-0110) toggle — attaches a rendered PIL greeting card to the join embed,
   off by default, degrading to embed-only when Pillow is unavailable. The
   `join_message`/`leave_message`/`dm_message` templates accept multiple
   `---`-separated **random variants** (one picked per greeting); `dm_enabled`
   also DMs the joiner the greeting (off by default, silently skipped when DMs
   are closed). `min_account_age_days` is the **join-delay age gate** (anti-raid:
   skip greeting/DM/entry-role for accounts younger than N days, `0` = off) and
   `delete_after_seconds` is **ping-then-delete** (auto-delete the channel
   greeting/farewell after N seconds, `0` = keep) — both default-off `int`
   settings with `numeric_presets` hints.
10. **existing_settings_keys**: `WELCOME_ENABLED`, `WELCOME_JOIN_ENABLED`,
    `WELCOME_LEAVE_ENABLED`, `WELCOME_CHANNEL`, `WELCOME_JOIN_MESSAGE`,
    `WELCOME_LEAVE_MESSAGE`, `WELCOME_ENTRY_ROLE`, `WELCOME_CARD_ENABLED`,
    `WELCOME_DM_ENABLED`, `WELCOME_DM_MESSAGE`, `WELCOME_MIN_ACCOUNT_AGE_DAYS`,
    `WELCOME_DELETE_AFTER_SECONDS`
    (`disbot/utils/settings_keys/welcome.py`). Stored as scalar guild settings —
    **no migration**. The `channel`/`entry_role` settings carry
    `input_hint="channel"`/`"role"` (channel-id-as-str duality).
11. **existing_BindingSpec_entries**: none (channel/role are scalar settings
    with a picker `input_hint`, not `subsystem_bindings` rows in v1).
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: `visibility_tier=administrator`;
    capability `welcome.settings.configure`; the `!welcome` summary is
    `manage_guild`-gated.
14. **hardcoded_or_env_only_behavior**: none — every flag/channel/template is
    operator config; a fresh guild is unaffected (master flag defaults OFF).
15. **current_resource_dependencies**: the greeting channel + optional entry
    role are operator-supplied ids (no auto-provisioning in v1).
16. **target_settings_fields**: the two per-event toggles + channel + the two
    templates + the entry role (`mock_welcome_ab` is the reviewed UX target;
    embed-first, PIL card phase 2).
17. **target_bindings**: none in v1 (a channel/role BindingSpec is a phase-2
    option once the binding read path generalises).
18. **target_access_controls**: administrator floor for config; the entry-role
    grant is system-actor via `role_automation` (audited).
19. **acceptance_or_validation_rules**: channel/role ids must be numeric (or
    empty); message templates are non-empty and bounded by `MAX_MESSAGE_LENGTH`;
    placeholders render injection-safe via `welcome_config.render_template`.
20. **target_mutation_path**: `SettingsMutationPipeline` (scalars). The greeting
    is a channel send, not a settings mutation; the entry role routes through
    `role_automation`.
21. **target_help_or_menu_route**: Help direct-nav (policy summary), Settings
    → Welcome group.
22. **provisionable_resources**: none.
23. **priority**: `P1` — band slot 6 of the safety/community lane.
24. **recommended_PR_phase**: safety-lane slot 6 (this PR).

### counters

server counters v1 (owner decision Q-0110) — the slot-6 quick-win paired with
welcome. Keeps designated channel names showing a live server stat (total
members / humans / bots — the statdock pattern). Deliberately hub-less (same
rationale as welcome). The renames are driven by a slow periodic loop in
`cogs/counters_cog.py` — **never per join** — because Discord caps channel
renames at ~2/10 min per channel; change-detection keeps it under the cap.
Compute/rename logic lives in `services/counter_service.py` (no DB writes).

1. **cog_module**: `disbot/cogs/counters_cog.py` (+ `disbot/cogs/counters/`
   subpackage with `schemas.py`).
2. **subsystem**: `counters`
3. **current_commands**: `!counters` (read-only bindings + live-count summary).
4. **current_command_groups**: none.
5. **current_command_panel_or_menu**: none (config via `!settings` → Counters).
6. **help_menu_discoverable**: Yes — `SUBSYSTEMS["counters"]` lists `counters`;
   discoverable via the `build_help_menu_view` hook (administrator tier).
7. **dedicated_panel_command**: `none`.
8. **help_menu_direct_navigation_hook**: `build_help_menu_view` (policy summary).
9. **existing_SettingSpec_declarations**: `enabled`, `total_channel`,
   `humans_channel`, `bots_channel`, `total_template`, `humans_template`,
   `bots_template` (`disbot/cogs/counters/schemas.py`). The master flag defaults
   OFF; defaults are the single source of truth in
   `disbot/services/counter_config.py`.
10. **existing_settings_keys**: `COUNTERS_ENABLED`, `COUNTERS_TOTAL_CHANNEL`,
    `COUNTERS_HUMANS_CHANNEL`, `COUNTERS_BOTS_CHANNEL`, `COUNTERS_TOTAL_TEMPLATE`,
    `COUNTERS_HUMANS_TEMPLATE`, `COUNTERS_BOTS_TEMPLATE`
    (`disbot/utils/settings_keys/counters.py`). Stored as scalar guild settings —
    **no migration**. The three channel settings carry `input_hint="channel"`.
11. **existing_BindingSpec_entries**: none (the counter channels are scalar
    settings with a picker `input_hint`, not `subsystem_bindings` rows in v1).
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: `visibility_tier=administrator`;
    capability `counters.settings.configure`; the `!counters` summary is
    `manage_guild`-gated.
14. **hardcoded_or_env_only_behavior**: the loop cadence (~10 min) is a
    constant (`_COUNTER_LOOP_MINUTES`), chosen to respect Discord's rename
    rate limit; everything else is operator config (master flag defaults OFF).
15. **current_resource_dependencies**: the bound counter channels are
    operator-supplied ids; the bot needs Manage Channels to rename them.
16. **target_settings_fields**: the master flag + the three channel bindings +
    the three name templates (`mock_counters` is the reviewed UX target).
17. **target_bindings**: none in v1 (a channel BindingSpec is a phase-2 option
    once the binding read path generalises).
18. **target_access_controls**: administrator floor for config; the rename loop
    is system-driven (no per-user authority).
19. **acceptance_or_validation_rules**: channel ids must be numeric (or empty);
    templates are non-empty and bounded by `MAX_TEMPLATE_LENGTH`; the rendered
    name is `{count}`-expanded injection-safe and capped at 100 chars.
20. **target_mutation_path**: `SettingsMutationPipeline` (scalars). The rename
    itself is a channel edit, not a settings mutation.
21. **target_help_or_menu_route**: Help direct-nav (policy summary), Settings
    → Counters group.
22. **provisionable_resources**: none.
23. **priority**: `P1` — band slot 6 of the safety/community lane (the
    welcome-paired quick-win).
24. **recommended_PR_phase**: safety-lane slot 6 (this PR).

### security

security tiers 1+2 (owner decision Q-0111) — the automated join-screening layer
beneath manual moderation: **raid detection** (join-rate lockdown + staff alert)
and an **account-age filter** (alert/kick on too-young accounts). Detection lives
in `services/security_service.py` (a pure `RaidTracker` + account-age helpers);
the one consequential action (a kick) routes through `moderation_service` — no
parallel audit path. Deliberately hub-less (same rationale as welcome/counters).
The two DECLINED tiers (alt-detection / VPN blocking) own no settings and are
deliberately absent — no external calls, no PII stored.

1. **cog_module**: `disbot/cogs/security_cog.py` (+ `disbot/cogs/security/`
   subpackage with `schemas.py`).
2. **subsystem**: `security`
3. **current_commands**: `!security` (read-only policy summary).
4. **current_command_groups**: none.
5. **current_command_panel_or_menu**: none (config via `!settings` → Security).
6. **help_menu_discoverable**: Yes — `SUBSYSTEMS["security"]` lists `security`;
   discoverable via the `build_help_menu_view` hook (administrator tier).
7. **dedicated_panel_command**: `none`.
8. **help_menu_direct_navigation_hook**: `build_help_menu_view` (policy summary).
9. **existing_SettingSpec_declarations**: `enabled`, `alert_channel`,
   `raid_enabled`, `raid_join_count`, `raid_window_seconds`,
   `raid_slowmode_channel`, `raid_slowmode_seconds`, `raid_lockdown_seconds`,
   `age_enabled`, `age_min_days`, `age_action`
   (`disbot/cogs/security/schemas.py`). The master flag + both tier flags default
   OFF; defaults + bounds are the single source of truth in
   `disbot/services/security_config.py`.
10. **existing_settings_keys**: `SECURITY_ENABLED`, `SECURITY_ALERT_CHANNEL`,
    `SECURITY_RAID_ENABLED`, `SECURITY_RAID_JOIN_COUNT`,
    `SECURITY_RAID_WINDOW_SECONDS`, `SECURITY_RAID_SLOWMODE_CHANNEL`,
    `SECURITY_RAID_SLOWMODE_SECONDS`, `SECURITY_RAID_LOCKDOWN_SECONDS`,
    `SECURITY_AGE_ENABLED`, `SECURITY_AGE_MIN_DAYS`, `SECURITY_AGE_ACTION`
    (`disbot/utils/settings_keys/security.py`). Stored as scalar guild settings —
    **no migration**. The two channel settings carry `input_hint="channel"`.
11. **existing_BindingSpec_entries**: none.
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: `visibility_tier=administrator`;
    capability `security.settings.configure`; the `!security` summary is
    `manage_guild`-gated.
14. **hardcoded_or_env_only_behavior**: none — every threshold/action is operator
    config (the numeric values are clamped to guardrail ranges in
    `security_config`); a fresh guild is unaffected (master + both tiers OFF).
15. **current_resource_dependencies**: the alert/slowmode channels are
    operator-supplied ids; a raid lockdown needs Manage Channels (slowmode) and a
    kick needs Kick Members — both fail open if missing.
16. **target_settings_fields**: the master flag + the two tier flags + their
    thresholds + the action enum + two channel pointers (`mock_security_alerts`
    is the reviewed UX target).
17. **target_bindings**: none in v1.
18. **target_access_controls**: administrator floor for config; runtime actions
    route through moderation's authority (kick) / channel edits (slowmode).
19. **acceptance_or_validation_rules**: numeric thresholds are bounded
    (`raid_join_count` 2-100, `raid_window_seconds` 5-3600, `age_min_days`
    1-365, slowmode 0-21600); `age_action` ∈ {`alert`, `kick`}; channel ids must
    be numeric or empty.
20. **target_mutation_path**: `SettingsMutationPipeline` (scalars). Actions
    (kick / slowmode) are not settings mutations.
21. **target_help_or_menu_route**: Help direct-nav (policy summary), Settings →
    Security group.
22. **provisionable_resources**: none.
23. **priority**: `P1` — band slot 9 of the safety/community lane.
24. **recommended_PR_phase**: safety-lane slot 9 (this PR).

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

### casino

1. **cog_module**: `disbot/cogs/casino_cog.py` (+ `disbot/views/casino/`,
   `disbot/utils/cards/`, `disbot/utils/poker/`).
2. **subsystem**: `casino`
3. **current_commands**: `!casino`, `!poker`/`!holdem`.
4. **current_command_groups**: none.
5. **current_command_panel_or_menu**: Casino hub + multiplayer poker table.
6. **help_menu_discoverable**: Yes (Games-hub child).
7. **dedicated_panel_command**: `!casino`.
8. **help_menu_direct_navigation_hook**: `build_help_menu_view` (Casino hub).
9. **existing_SettingSpec_declarations**: none (v1 play-chips; tuning is module
   constants in `disbot/views/casino/poker_table.py`).
10. **existing_settings_keys**: none.
11. **existing_BindingSpec_entries**: none.
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: `visibility_tier=user`; capabilities
    `casino.game.play`.
14. **hardcoded_or_env_only_behavior**: start stack, blinds, seat cap, turn
    timeout (play-chip constants).
15. **missing_customization_commands**: blinds/buy-in editor (gated on real-coin
    buy-in — N-party escrow follow-up).
16. **missing_settings_pages**: Settings Manager casino page (future).
17. **missing_menu_buttons_selects_modals**: custom raise-amount modal.
18. **setting_class_per_value**: blinds/stack → scalar.
19. **target_Settings_Manager_page**: `!settings subsystem casino` (future).
20. **target_mutation_path**: `SettingsMutationPipeline`.
21. **target_help_or_menu_route**: Games hub → Casino.
22. **provisionable_resources**: none.
23. **priority**: `P3`.
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

### ux_lab

1. **cog_module**: `disbot/cogs/ux_lab_cog.py`.
2. **subsystem**: `ux_lab` (admin-tier design workbench).
3. **current_commands**: `!uxlab` (alias: `!interfacelab`), `/uxlab`.
4. **current_command_groups**: none.
5. **current_command_panel_or_menu**: opens `UxLabHomeView`
   (`disbot/views/ux_lab/home.py`) — wing buttons into the exhibit browsers
   + the limit probe bench.
6. **help_menu_discoverable**: Yes — `subsystem_registry.py` entry,
   `visibility_tier=administrator` (admins only).
7. **dedicated_panel_command**: `!uxlab`.
8. **help_menu_direct_navigation_hook**: `build_help_menu_view` on the cog.
9. **existing_SettingSpec_declarations**: none — **by design, permanently**:
   the lab is a zero-write workbench (no settings, no DB, no mutations;
   CI-fenced by `tests/unit/invariants/test_ux_lab_zero_write.py`).
10. **existing_settings_keys**: none (see 9).
11. **existing_BindingSpec_entries**: none (see 9).
12. **existing_ResourceRequirement_entries**: none (see 9).
13. **current_access_policy_behavior**: `visibility_tier=administrator`;
    `has_permissions(administrator=True)` on both entry commands; views are
    author-locked (`BaseView` default).
14. **hardcoded_or_env_only_behavior**: exhibit content is code-defined
    sample data — intentionally static (it is the demo corpus).
15. **missing_customization_commands**: none — the lab must not grow a
    settings surface (zero-write fence).
16. **missing_settings_pages**: none (see 15).
17. **missing_menu_buttons_selects_modals**: plan PRs B/C add the
    Components-V2, PIL, mockup, and compare wings
    (`docs/planning/ux-lab-interface-gallery-plan-2026-06-12.md` §8).
18. **setting_class_per_value**: n/a (no configurable state, see 9).
19. **target_Settings_Manager_page**: none — exempt by design.
20. **target_mutation_path**: none — zero-write fence.
21. **target_help_or_menu_route**: DONE — Help direct-nav (admin tier).
22. **provisionable_resources**: none.
23. **priority**: `P3` — workbench, not a member feature.
24. **recommended_PR_phase**: UX Lab plan PR A (this entry); B/C follow.

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

### project_moon

1. **cog_module**: `disbot/cogs/project_moon_cog.py`
2. **subsystem**: `project_moon`
3. **current_commands**: `!pm` (aliases `!limbus`, `!projectmoon`) with
   subcommands `sinner`/`sin`/`status`/`ego`/`damage`/`lookup`/`list`; slash `/pm`.
4. **current_command_groups**: `pm` (prefix group, `invoke_without_command` opens the panel).
5. **current_command_panel_or_menu**: `pm`.
6. **help_menu_discoverable**: Yes (its own top-level Project Moon hub, like BTD6; `build_help_menu_view`).
7. **dedicated_panel_command**: `pm`.
8. **help_menu_direct_navigation_hook**: `build_help_menu_view`.
9. **existing_SettingSpec_declarations**: none.
10. **existing_settings_keys**: none.
11. **existing_BindingSpec_entries**: none.
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: `visibility_tier=user`; capability
    `project_moon.lookup.view`. Read-only, deterministic — no writes, no DB, no
    AI gateway (like `btd6_reference`).
14. **hardcoded_or_env_only_behavior**: structural/lore facts loaded from
    `data/projmoon/limbus/*.json` (committed, provenance-tagged).
15. **missing_customization_commands**: none (read-only reference by design).
16. **missing_settings_pages**: none planned.
17. **missing_menu_buttons_selects_modals**: none.
18. **setting_class_per_value**: none.
19. **target_Settings_Manager_page**: none (no configurable surface by design).
20. **target_mutation_path**: none (read-only; no state mutation).
21. **target_help_or_menu_route**: top-level Project Moon hub; Help direct-nav.
22. **provisionable_resources**: none.
23. **priority**: `P2`.
24. **recommended_PR_phase**: Project Moon knowledge domain PR 1 (Q-0192).

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
3. **current_commands**: the whole BTD6 surface is now **one unified `/btd6`
   (`!btd6`) tree** (owner request, 2026-06-24): everyday lookups flat
   (`/btd6 income`, `/btd6 round`, `/btd6 rbe`, `/btd6 tower`, `/btd6 hero`,
   `/btd6 relic`, `/btd6 ct`, `/btd6 ask`, `/btd6 status`, `/btd6 diagnostics`,
   `/btd6 test-intent`; `!btd6 ctteam` is prefix-only) and the bigger buckets
   nested (`/btd6 strat …`, `/btd6 ops …`, `/btd6 events …`). The tree is
   module-level in `disbot/cogs/btd6/_unified.py` (cogs can't cleanly share one
   `app_commands.Group`); the mother `btd6_cog` registers it and keeps the panel
   (`!btd6menu`) + the schema / ingestion-supervisor lifecycle. The old
   `btd6_reference` / `btd6_events` / `btd6_strategy` / `btd6_ops` cogs (below)
   remain only as **hidden prefix aliases** (`!btd6ref …` etc.) so existing
   muscle-memory keeps working.
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
    `BTD6_CT_GROUP_ID` (the per-guild Contested Territory bracket id —
    set via the **guided flow** since Settings Phase 2/Q-0064:
    `!btd6 ctteam <url-or-id>` parses → previews → confirms before
    `services.btd6_ct_team_service` commits; never a raw scalar field), and
    `BTD6_VERSION_ANNOUNCEMENT_CHANNEL` (the **legacy fallback lane** for the
    version-announcement channel since Settings Phase 2/Q-0064 — the
    `btd6.version_announce_channel` binding takes precedence when bound;
    `!btd6 ops announcechannel` still writes this KV pointer and warns when a
    binding shadows it; read through `services.btd6_version_announce`), all
    in `disbot/utils/settings_keys/btd6.py`.
11. **existing_BindingSpec_entries**: `btd6.strategy_submission_channel`
    (M4) routes natural-language submissions in bound channels into
    the strategy review pipeline; `btd6.version_announce_channel`
    (Settings Phase 2, Q-0064) is the first-class version-announcement
    channel (binding-first read; legacy KV fallback). Both declared in
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
2. **subsystem**: `btd6` (now a **hidden prefix alias** — static game-data
   lookups. The canonical surface is the unified `/btd6` tree
   (`cogs/btd6/_unified.py`); this cog keeps `!btd6ref …` so old muscle-memory
   keeps working).
3. **current_commands** (canonical): `!btd6 tower <name>`, `!btd6 hero <name>`,
   `!btd6 round <N>`, `!btd6 rbe <N>`, `!btd6 income <N>`, `!btd6 relic <name>`,
   `!btd6 ct` (+ slash `/btd6 tower …`). The legacy `!btd6ref tower …` prefix
   still works (hidden alias). Also reachable from `BTD6PanelView` (`!btd6`).
4. **current_command_groups**: flat lookups under the unified `/btd6` (`!btd6`)
   tree; `btd6ref` survives as a hidden **prefix-only** alias (no slash twin).
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
2. **subsystem**: `btd6` (now a **hidden prefix alias** — live Ninja Kiwi
   events / leaderboards / source diagnostics / grounding. Canonical surface:
   the unified `/btd6 events …` subgroup in `cogs/btd6/_unified.py`).
3. **current_commands** (canonical): `!btd6 events live`, `!btd6 events event`,
   `!btd6 events leaderboard`, `!btd6 events sources`,
   `!btd6 events source-health`, `!btd6 events latest-data`,
   `!btd6 events refresh-source <key>` (manage-guild), `!btd6 events grounding`
   (+ slash `/btd6 events …`). The legacy `!btd6events …` prefix still works
   (hidden alias).
4. **current_command_groups**: `/btd6 events …` (nested under the unified tree);
   `btd6events` survives as a hidden **prefix-only** alias (no slash twin).
5. **current_command_panel_or_menu**: none of its own — surfaced via
   `BTD6PanelView`.
6. **help_menu_discoverable**: via the BTD6 panel.
7-22. inherit the `btd6` subsystem posture; `refresh-source` writes flow
   through `services.btd6_source_mutation` (audited), never the cog directly.
23. **priority**: `P1` — BTD6 cog-split foundation.
24. **recommended_PR_phase**: ships with the BTD6 cog split.

### btd6_strategy

1. **cog_module**: `disbot/cogs/btd6_strategy_cog.py`
2. **subsystem**: `btd6` (now a **hidden prefix alias** — strategy memory
   browse/submit/review + `why-no-response`. Canonical surface: the unified
   `/btd6 strat …` subgroup in `cogs/btd6/_unified.py`).
3. **current_commands** (canonical): `!btd6 strat browse`, `!btd6 strat mine`,
   `!btd6 strat strategy <id>`, `!btd6 strat strategy-audit <id>`,
   `!btd6 strat submit` (slash opens a modal), `!btd6 strat pending`
   (manage-guild), `!btd6 strat strategies`, `!btd6 strat why-no-response`
   (+ slash `/btd6 strat …`). The legacy `!btd6strat …` prefix still works
   (hidden alias).
4. **current_command_groups**: `/btd6 strat …` (nested under the unified tree);
   `btd6strat` survives as a hidden **prefix-only** alias (no slash twin).
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
2. **subsystem**: `btd6` (now a **hidden prefix alias** — operator surface for
   BTD6 ingestion. Canonical surface: the unified `/btd6 ops …` subgroup in
   `cogs/btd6/_unified.py`; shared formatters in `cogs/btd6/_ops_helpers.py`).
3. **current_commands** (canonical): `!btd6 ops readiness` (ingestion readiness
   verdict), `!btd6 ops runs` (recent ingestion runs), `!btd6 ops source_enable
   <key>` / `!btd6 ops source_disable <key>` (toggle a source), `!btd6 ops
   seed-data`, `!btd6 ops announcechannel` (+ slash `/btd6 ops …`). The legacy
   `!btd6ops …` prefix still works (hidden alias). Also reachable from the 🛠️
   Admin sub-panel on `!btd6`.
4. **current_command_groups**: `/btd6 ops …` (nested under the unified tree);
   `btd6ops` survives as a hidden **prefix-only** alias (no slash twin).
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
    `!btd6 ops` / `/btd6 ops` (legacy `!btd6ops` still works, hidden).
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
   today.  **Server event logging v1 (schema v3, Q-0109)** adds four
   more: `messages_enabled` / `members_enabled` / `roles_enabled`
   (bool, default False — per-category gates for the passive
   `LoggingCog` listeners) and `event_routing` (str enum,
   `allowed_values=("combined", "per_category")`, default `combined`)
   selecting one-channel vs per-category routing.  The
   `messages_enabled` hint carries the deleted-message privacy
   disclosure.  **Exclusion lists (schema v4, completion cert punch #1)**
   add `ignored_channels` and `ignored_users` (str, comma-separated id
   CSV, default empty, tolerant `parse_id_csv` read / loud write
   validator) — a passive event whose channel or subject id is listed is
   never logged, for every category.
   **Server event logging v2 (schema v5, audit-log integration)** adds four
   more category gates: `moderation_enabled` / `channels_enabled` /
   `server_enabled` (bool, default False — audit-log-sourced groups sharing
   the combined `events_channel` route, requiring the bot's View-Audit-Log
   permission) and `voice_enabled` (bool, default False — passive
   `on_voice_state_update` join/leave/move logging, bots excluded).  The
   `roles` category is repurposed to the audit-log path so it names the actor.
10. **existing_settings_keys**: `LOGGING_ENABLED`,
    `LOGGING_AUTO_CREATE_CHANNELS` from `utils.settings_keys.logging`.
    The two channel-id keys (`LOGGING_MOD_CHANNEL`,
    `LOGGING_CLEANUP_CHANNEL`) are legacy and are migrating to
    bindings in S7b.  Server event logging v1 adds
    `LOGGING_MESSAGES_ENABLED`, `LOGGING_MEMBERS_ENABLED`,
    `LOGGING_ROLES_ENABLED`, and `LOGGING_EVENT_ROUTING` (all legacy
    KV keys, no migration).  Schema v4 adds `LOGGING_IGNORED_CHANNELS`
    and `LOGGING_IGNORED_USERS` (legacy KV, no migration) for the
    exclusion lists.  Schema v5 (audit-log v2) adds
    `LOGGING_MODERATION_ENABLED`, `LOGGING_CHANNELS_ENABLED`,
    `LOGGING_SERVER_ENABLED`, and `LOGGING_VOICE_ENABLED` (legacy KV, no
    migration) for the new audit-log-sourced + voice categories.
11. **existing_BindingSpec_entries**: `mod_channel`, `cleanup_channel`
    — both `BindingKind.CHANNEL`, optional.  Declared in S7a; S7b
    wires the mutation path through `BindingMutationPipeline`.
    Phase 9a (schema v2) adds five severity/source slots, all
    `BindingKind.CHANNEL`, all optional, all falling back to
    `mod_channel` when unset: `debug_channel`, `info_channel`,
    `warning_channel`, `error_channel`, `audit_channel`.  Server
    event logging v1 (schema v3) adds four more event-route slots:
    `events_channel` (the combined "everything" destination) plus the
    per-category `message_channel`, `member_channel`, `role_channel`
    — these fall back to `events_channel` (NOT `mod_channel`) so event
    noise never lands in the moderation-action log.
12. **existing_ResourceRequirement_entries**: `mod_log` channel
    (`bot-mod-log`, RECOMMENDED), `cleanup_log` channel
    (`bot-cleanup-log`, RECOMMENDED).  Both link to the declared
    bindings via `binding_name=`.  Phase 9a adds five matching
    RECOMMENDED requirements with `bot-debug-log` / `bot-info-log` /
    `bot-warning-log` / `bot-error-log` / `bot-audit-log` suggested
    names. Server event logging v1 adds four RECOMMENDED requirements
    (`events_log`, `message_log`, `member_log`, `role_log`) with
    `bot-event-log` / `bot-message-log` / `bot-member-log` /
    `bot-role-log` suggested names. Auto-create stays OFF by default.
13. **current_access_policy_behavior**: `visibility_tier=administrator`;
    capabilities `logging.settings.configure`, `logging.channel.bind`,
    `logging.channel.create`.  Master switch `logging.enabled`
    defaults to OFF; the service in `services/server_logging.py`
    stays inert until an operator opts in.  The passive event
    listeners (added to `cogs/logging_cog.py`) read the master switch
    plus each per-category flag, so a fresh guild — and a guild that
    already logs moderation actions — sees no new behaviour.
14. **hardcoded_or_env_only_behavior**: `DEFAULT_MOD_CHANNEL_NAME` /
    `DEFAULT_CLEANUP_CHANNEL_NAME` are module-level constants in
    `utils.settings_keys.logging`; the create-channel flow (S7c)
    uses the schema's `suggested_name` instead, so these constants
    become a legacy fallback once S7c lands.  The event routes add
    `DEFAULT_EVENTS_CHANNEL_NAME`, `DEFAULT_MESSAGE_LOG_CHANNEL_NAME`,
    `DEFAULT_MEMBER_LOG_CHANNEL_NAME`, and
    `DEFAULT_ROLE_LOG_CHANNEL_NAME` as the matching auto-create
    fallback names.
15. **missing_customization_commands**: existing-channel selection
    (S7b — shipped), create-new-channel flow (S7c — shipped).
    Per-event-class routing **shipped in server event logging v1
    (Q-0109)**: message edits/deletions · member joins/leaves · role
    grants/revocations, with the owner-configurable combined-vs-
    per-category routing.  A multi-select exempt-roles/channels picker
    remains a phase-2 UX polish.
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

### server_management

The unified Server Management mother hub (PR14). A **routing-only** operator
surface: it composes the moderation / channels / roles / cleanup / setup
managers behind read-only health badges and owns **no** settings, bindings,
resources, or mutations of its own.

1. **cog_module**: `disbot/cogs/server_management_cog.py`.
2. **subsystem**: `server_management` (snake_case key per Q-0026; the
   `!servermanagement` command keeps its name).
3. **current_commands**: `!servermanagement` (aliases `!servermenu`,
   `!guildmenu`), `/server-management`.
4. **current_command_groups**: none.
5. **current_command_panel_or_menu**: `server_management` (panel-anchor key) →
   `views/server_management/hub.py:ServerManagementHubView`.
6. **help_menu_discoverable**: Yes (mother hub, administrator tier).
7. **dedicated_panel_command**: `none`.
8. **help_menu_direct_navigation_hook**: `none` (the cog hosts the command).
9. **existing_SettingSpec_declarations**: none — routing-only hub.
10. **existing_settings_keys**: none.
11. **existing_BindingSpec_entries**: none.
12. **existing_ResourceRequirement_entries**: none.
13. **current_access_policy_behavior**: `visibility_tier=administrator`; no
    capabilities (authority is the administrator floor on the command plus the
    view's `interaction_check`; per-manager authority is re-checked when routing
    in — ADR-005).
14. **hardcoded_or_env_only_behavior**: none — composes existing managers.
15. **missing_customization_commands**: none (it owns no settings).
16. **missing_settings_pages**: none.
17. **missing_menu_buttons_selects_modals**: none planned.
18. **setting_class_per_value**: n/a.
19. **target_Settings_Manager_page**: n/a — not a settings-owning subsystem.
20. **target_mutation_path**: none — every action routes into an existing
    manager's panel; the hub introduces no op-kind, migration, or pipeline.
21. **target_help_or_menu_route**: Help mother hub → manager panels.
22. **provisionable_resources**: none.
23. **priority**: shipped (server-management PR14).
24. **recommended_PR_phase**: shipped 2026-06-08.

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
