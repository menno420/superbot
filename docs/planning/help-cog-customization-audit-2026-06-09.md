# Help cog customization audit and roadmap — 2026-06-09

> **Status:** `historical` — source-verified mapping and future-work recommendation; no runtime behavior is implemented here.
> **Superseded 2026-06-19 (was active):** Decisions Q-0055–Q-0059 answered; the Help overlay editor shipped #677/#679. Do not act on this — current map: [planning/README](README.md).
>
> **Scope:** Help + hubs + navigation + governance visibility + access projection + settings/customization/setup integration.
>
> **Source precedence:** live source at `09e5a297` wins over older docs. Live GitHub PR state could not be verified in this checkout because `gh` is unavailable and no Git remote is configured.
> **Post-merge note (2026-06-09, end-of-day consolidation):** this audit merged as **#627**. Community Spotlight registration shipped the same day (**#626**), so the "queued/unregistered Spotlight" findings below are resolved history. The bounded counts-reconciliation + characterization-tests session (Lane 8) **shipped 2026-06-09 as #642** *(updated 2026-06-10 — this note previously said "queued")*; the next Help step is the **projection seam** (Batch 6 of [`consolidated-implementation-plan-2026-06-10.md`](consolidated-implementation-plan-2026-06-10.md), after Adaptive P1C); **all five overlay decisions (Q-0055–Q-0059) were answered same evening** (router §25 is canonical): hiding = **display-only**, names = **Help-only**, ordering = **panel-local** (no UI until stable panel/action identities), admin/debug shows **custom + default + key**, and the Help Home message = **embed builder** (deviates from the plain-text recommendation → the structured overlay model this audit anticipated, with bounds/sanitation/preview mandatory).

## 1. Executive summary

SuperBot already has most of the *pieces* needed for a deterministic, customizable Help system, but Help does not yet compose them into one policy-aware presentation pipeline.

- **Discovery and presentation metadata are split.** `utils/subsystem_registry.py` owns subsystem display metadata, entry points, tiers, parent hubs, and capabilities. `utils/hub_registry.py` separately owns mother-hub presentation/order. The live bot/cog command objects own command names, aliases, help text, enabled/hidden flags, and panel hooks. `core/runtime/command_surface_ledger.py` classifies commands and owns the static hidden-from-help policy.
- **Current Help has two surfaces.** `!help` and `/help` open a mother-hub category index. “Advanced / All Commands” opens a paginated list of governance-visible **top-level** subsystems. Typed/selected routes share `cogs/help/route.py` and usually open a cog's `build_help_menu_view` panel.
- **Help partially respects governance.** It calls `governance_service.resolve_visibility`, and Advanced filters against `visible_subsystems`. However, Help Home passes only `member_tier` into `hubs_for_tier`; it does not filter hubs by resolved subsystem visibility, routing, command access, or the access projection. Typed/direct hub, subsystem, and command routes resolve names without checking the selected target against `visible_subsystems`.
- **Help does not currently consume `access_projection`.** The projection already composes command access, per-scope cog routing, governance, future availability, and informational help visibility. Its help axis is explicitly display-only. The adaptive platform has an active sequence for `help_advertises_locked` and Help Preview; future Help work must not duplicate or bypass that lane.
- **Command panels are not one system.** Generic fallback command embeds enumerate live cog commands in cog order and filter only `cmd.hidden`, `cmd.enabled`, and ledger classification. Dedicated cog panels are independently authored, usually with static buttons/copy. Neither path supports guild-specific hide/show/reorder/rename today.
- **Existing mutation owners should be extended, not replaced.** Governance remains canonical for whether a subsystem is discoverable at guild/category/channel/thread scope. Command access/routing remain execution/admission owners. Settings mutation is the best existing audited scalar/text route. The customization catalogue is a read-only composition inventory, not a write store. A per-guild Help overlay will probably need structured storage because ordered command/category overrides do not fit scalar settings cleanly, but all writes should still use an audited service and emit invalidation/events.
- **Recommended target:** a unified, read-only **Help Catalogue** composed from subsystem/hub/command/panel metadata, plus a separately persisted **guild Help presentation overlay**. A Help Projection service should combine catalogue defaults + guild overlay + governance/access projection into explainable render models. Display-only hiding must remain separate from execution disabling.

### Severity-ranked findings

1. **Critical foundation before customization:** establish one projection/composition seam for Help. Today top-level hubs, Advanced, typed routes, generic embeds, and dedicated panels apply different filters.
2. **Important:** reconcile registry/docs drift. The binding help map says “9 hubs” while its table and source contain 10; it says 26 loaded cogs while `config.INITIAL_EXTENSIONS` includes additional split BTD6 cogs, bootstrap access, and unregistered Community Spotlight; `SUBSYSTEMS` contains 28 entries. Community Spotlight remains intentionally queued for registration under answered Q-0044.
3. **Important:** decide product semantics for display-only hide, shared naming scope, ordering scope, debug/default-name display, and custom-message format before storage design.
4. **Cleanup:** move static Help Home copy, tier-group labels, Advanced labels, and route alias overrides into canonical presentation metadata only after the projection contract is pinned by tests.

### Gates and off-limits scope

- **No gate blocks this mapping document.** No runtime behavior is changed.
- Future implementation must coordinate with the active Adaptive Setup/Access sequence: P1B `help_advertises_locked` uses the governance tier-input path chosen in Q-0045; P1C Help Preview is a staff-hub subpanel, not a new command.
- Community Spotlight registration/navigation belongs to the Q-0025 scaffold lane selected by answered Q-0044; do not ad hoc register it inside a Help-customization PR.
- Central availability policy is not implemented; Help must report/handle that axis as skipped rather than invent policy.
- Do not merge display-only Help hiding with command registration, command-access admission, governance execution checks, or Discord slash visibility.

## 2. Source-verified file inventory

| Path | Important owners/symbols | Help/hub/visibility role | Read/write | Classification | Related protection |
|---|---|---|---|---|---|
| `disbot/cogs/help_cog.py` | `HelpCog`, `HelpCategoryView`, `HelpPanelView`, `build_categories_overview_embed`, `build_cog_embed`, `resolve_help_panel_state` | Prefix/slash entry, Help Home, Advanced list, generic fallback command embed, back-to-Help | Reads governance/live bot/registries; writes message anchors only | Thin-ish adapter but still owns presentation/filter orchestration | `tests/unit/help/*`, `tests/unit/views/test_navigation.py` |
| `disbot/cogs/help/route.py` | `HelpRoute`, `HelpOpener`, `resolve_route`, `open_route`, `HUB_PANEL_BUILDERS` | Shared typed/dropdown route resolver and direct panel opening | Read-only | Canonical Help routing seam | route/direct-navigation tests |
| `disbot/utils/subsystem_registry.py` | `SUBSYSTEMS`, `all_subsystems_sorted`, identity checks | Canonical subsystem identity/display metadata, parent hubs, entry points, tier, dependencies, capability list | Static read-only metadata | Canonical registry | registry/doc/governance tests |
| `disbot/utils/hub_registry.py` | `HUBS`, `HubEntry`, `hubs_for_tier`, `get_hub` | Canonical mother-hub presentation/order and tier metadata | Static read-only metadata | Canonical presentation registry; not policy owner | `tests/unit/utils/test_hub_registry.py`, Help category tests |
| `disbot/core/runtime/command_surface_ledger.py` | `build_ledger`, classifications, `is_hidden_from_help` | Live prefix/slash command inventory and static help-classification filter | Cached read model | Canonical command-surface classification | classification/discovery/access tests |
| `disbot/core/runtime/command_descriptions.py` | command-description metadata | Supplemental command copy where adopted | Read-only | Canonical where used; adoption incomplete | command-surface tests |
| `disbot/services/governance_service.py`, `disbot/governance/resolver.py` | `GovernanceContext`, `resolve_visibility`, `get_visible_subsystems` | Canonical tier + guild/category/channel/thread subsystem visibility and dependencies | Reads DB/cache | Canonical visibility owner | governance/help tests |
| `disbot/governance/writes.py`, `disbot/utils/db/governance.py` | `set_subsystem_visibility`, audited transactions | Audited per-scope visibility mutation and invalidation | Writes DB/audit/events | Canonical governance mutation owner | governance write/visibility panel tests |
| `disbot/utils/visibility_rules.py` | visibility tiers and synchronous tier helpers | Registry-default discoverability only; explicitly not execution auth | Read-only | Canonical tier definitions | governance tests |
| `disbot/services/access_projection.py` | `FeatureEntry`, `AccessContext`, `resolve_feature_access`, axis evaluators | Explainable composite of command access, routing, governance, availability, and Help classification | Read-only, fault-tolerant | Canonical cross-axis projection/read model | `tests/unit/services/test_access_projection.py` |
| `disbot/core/runtime/command_access.py`, `disbot/services/command_access_service.py` | central admission decisions and mutation | Whether commands can execute in configured channels/modes | Read/write through owner | Canonical command admission owner | command access service/settings tests |
| `disbot/services/command_routing.py`, `disbot/utils/db/command_routing.py` | `is_cog_enabled`, `set_policy` | Per-guild/category/channel cog routing; currently not consumed by Help | Read/write | Canonical routing owner | setup/routing tests |
| `disbot/services/customization_catalogue.py` | `CustomizationEntry`, `PanelDeclaration`, `build_catalogue`, `panel_command` | Read-only aggregate of commands/settings/schema/help hooks/panels | Read-only | Canonical inventory/composition catalogue; **not storage** | customization catalogue tests |
| `disbot/core/runtime/settings_registry.py` | `SettingSpec`, registry functions | Declared scalar setting metadata | Read-only declarations | Canonical setting declaration owner | settings tests |
| `disbot/services/settings_resolution.py` | resolved setting models/functions | Typed setting read path | Read-only/cache-backed | Canonical setting read owner | settings resolution tests |
| `disbot/services/settings_mutation.py`, `disbot/utils/db/settings_audit.py` | `SettingsMutationPipeline` | Audited scalar setting write, reset, cache invalidation, events | Writes DB/audit/events | Canonical scalar mutation owner | mutation pipeline tests |
| `disbot/utils/guild_config_accessors.py` | typed accessors, setting and command-access caches | Cache-backed settings/policy reads and invalidation helpers | Read/cache | Canonical cache accessor seam | settings/access tests |
| `disbot/services/setup_change_plan.py`, `disbot/services/setup_draft.py`, `disbot/services/setup_operations.py` | preview/diff/staged operations | Existing compound preview/apply route; relevant to bulk Help customization | Read/write only through staged apply owners | Canonical compound-change lane | setup plan/draft/operation tests |
| `disbot/views/settings/*`, `disbot/cogs/settings_cog.py` | settings hub/subsystem editors/reset/audit | Future structured Help editor host; currently no Help settings | Reads/writes through settings owners | Adapter/UI | settings view tests |
| `disbot/views/setup/*`, `disbot/cogs/setup_cog.py` | wizard, sections, final review | Future setup integration/preview; currently no Help customization section | Draft/apply through setup owners | Adapter/UI | setup view/service tests |
| `disbot/views/navigation.py` | `BackTarget`, `attach_back_button`, `transition_to`, `chain_back` | Shared in-place navigation/back-chain helpers | UI-only | Canonical navigation primitive | `tests/unit/views/test_navigation.py` |
| `disbot/views/games/hub.py`, `community/hub.py`, `economy/panel.py`, `moderation/panel.py`, `utility/panel.py`, `server_management/hub.py` and cog-local panels | dedicated panel builders/views | Independently authored command/action panels opened by Help | Mostly adapters; callbacks call services | Canonical per-panel UI today, but duplicated presentation/filtering | actionability/hub/view tests |
| `disbot/views/channels/visibility_panel.py` | multi-channel subsystem visibility UI | Existing governance visibility editor | Writes through governance owner | Adapter/UI | visibility panel tests |
| `disbot/views/access/explorer.py` | Access Explorer | Existing explainability UI using governance/access data | Read-only | Adapter/UI | access explorer tests |
| `disbot/core/runtime/persistent_views.py`, `message_anchor_manager.py` | persistent registry and anchors | Help views register persistently; prefix Help replaces prior per-user/channel anchor; slash Help is ephemeral | Anchor writes | Canonical lifecycle support | Help/navigation tests |
| `disbot/config.py` | `INITIAL_EXTENSIONS`, `PREFIX` | Loaded cog list and prefix | Static config | Canonical extension load list | config/startup tests |
| `docs/help-command-surface-map.md` | binding inventory | Existing command/hub inventory; useful but has count drift and an explicit Spotlight gap | Docs | Binding inventory requiring reconciliation | `tests/unit/docs/test_help_surface_map_doc.py` |
| `docs/building-roadmap/mother-hub-map.md`, `hub-ui-standard.md` | hub doctrine | Defines registry/presentation/navigation doctrine | Docs | Binding/reference design | doc checks |
| `docs/planning/adaptive-setup-access-routine-platform-2026-06-08.md` | access projection/Help Preview roadmap | Active sequencing and negative-architecture guardrails | Docs | Authoritative plan for adaptive access lane | plan/source tests |

### Deep-inspection tooling note

The required `python3.10 scripts/context_map.py <path>` command was attempted for the deeply inspected Python files. The pyenv shim could identify Python 3.10.20 but did not expose `python3.10`; running the script under 3.10.20 then failed because PyYAML is absent in that interpreter. The repository-default Python 3.12 environment successfully produced a context map for `help_cog.py`; important claims were manually verified from source regardless.

## 3. Current Help architecture map

### Entry and lifecycle flow

1. `!help [category]` and `/help [name]` both resolve `GovernanceContext` through `governance_service.resolve_visibility`.
2. With no argument, Help builds `HelpCategoryView(member_tier)` and `build_categories_overview_embed(member_tier)`.
3. Prefix Help deletes/stales the prior per-user/per-channel Help anchor, sends a fresh panel, and upserts a new anchor. Slash Help is ephemeral and has no anchor.
4. With an argument or dropdown choice, `resolve_route` classifies the target as `advanced`, `hub`, `subsystem`, `command`, or `unknown`; `open_route` builds the destination.
5. Interactive destinations gain a shared navigation Back-to-Help button. Returning to Help re-resolves governance at click time.

### Discovery and grouping

- **Subsystems:** static `SUBSYSTEMS` entries. Ordering is `ui_priority`/registry-driven through `all_subsystems_sorted`.
- **Cog lookup:** `_cog_for_subsystem` scans live `bot.cogs`; a cog matches when any live prefix command name/alias intersects the subsystem's static `entry_points`.
- **Mother hubs:** static ordered `HUBS`; every hub key is expected to map to a subsystem/cog host. `hubs_for_tier` filters only `panel_available` and `minimum_tier`.
- **Children:** `parent_hub` on subsystem metadata is the primary relationship. `HubEntry.primary_children` duplicates that roster for presentation/contract checks; `cross_link_children` permits secondary placement.
- **Commands:** generic command-list embeds use live `cog.get_commands()` order. Single-command routes use `bot.get_command`, including aliases. Dedicated panels choose their own buttons/actions/copy.
- **Panels:** `open_route` invokes the cog's `build_help_menu_view`; the diagnostic hub uses an override to call `build_platform_help_menu_view`. Failure falls back to not-found for hubs or a generic command embed for subsystems.

### Visibility and authorization actually applied

| Surface | Governance tier | Scope visibility | Parent-hub rule | Routing | Command access | Per-command `can_run`/capability | Loaded-state | Static Help classification |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Help Home hubs | Yes, via `minimum_tier` | **No** (resolved set is discarded) | N/A | No | No | No | Indirect only; stale hub can render then fail on select | N/A |
| Advanced list | Yes + resolved visibility | Yes, through governance | **Excludes every `parent_hub` child** | No | No | No | Cog absence discovered only after selection | N/A at subsystem row |
| Typed/dropdown hub route | Route caller resolves governance, but target is not checked against it | **No target check** | N/A | No | No | Builder-dependent | Yes, via cog lookup | Builder-dependent |
| Typed/dropdown subsystem route | Same | **No target check** | Direct route bypasses nesting | No | No | Builder-dependent | Yes, via cog lookup | Generic fallback only |
| Typed single-command route | Same | **No target check** | N/A | No | No | No | Yes, via `bot.get_command` | **No classification filter** |
| Generic fallback command embed | Inherited from route only | No command-level check | N/A | No | No | No | Live cog commands only | Yes; also `cmd.hidden` + `cmd.enabled` |
| Dedicated panel | Builder-specific | Builder-specific | Panel-specific | Usually callback/execution-time only | Execution-time central guard | Callback/service-specific | Live panel only | Usually not ledger-driven |

**Implication:** Help discoverability is not currently equivalent to “this audience can use this here.” That is not inherently wrong—Help may intentionally advertise locked features—but it is currently inconsistent and unexplained. The access projection exists to make this distinction explicit, but Help does not consume it yet.

### Caching and persistence

- Governance visibility is generation/version cached by guild/context/tier/roles and invalidated by canonical governance writes.
- Command-surface ledger is cached after build; static command classification is read from command extras.
- Settings and command-access policy reads use guild-config caches with owner-specific invalidation.
- Help presentation itself has no per-guild persisted customization and no render cache. Views hold short-lived snapshots (`member_tier`, visible list/page); important navigation callbacks re-resolve governance.
- Prefix Help message anchors are persisted for cleanup/replacement, but they do not persist Help configuration.

## 4. Current Help surface map

### Mother hubs shown on Help Home

All labels, emoji, purposes, order, entry commands, and minimum tiers below are static in `hub_registry.HUBS`. None can be renamed, described differently, hidden, or reordered per guild today. Home visibility is tier-only; it does not use the resolved subsystem set or access projection.

| Hub | Entry / tier | Primary children; cross-links | Panel/source | Current customization |
|---|---|---|---|---|
| 🎮 Games | `!games` / user | blackjack, deathmatch, rps_tournament, mining, counting, chain | Games cog → Games hub | None |
| 🐵 BTD6 Assistant | `!btd6` / user | none | BTD6 cog/panel | None |
| 💰 Economy | `!economymenu` / user | inventory, leaderboard; cross-link mining | Economy cog/panel | None |
| 🛡️ Moderation & Safety | `!modmenu` / moderator | cleanup, logging, proof_channel | Moderation cog/panel | None |
| 🌱 Community | `!community` / user | xp, role; cross-links counting, chain, leaderboard | Community cog/hub | None |
| 🧰 Utility | `!utilitymenu` / user | general, four_twenty | Utility cog/panel | None |
| ⚙️ Admin / Operations | `!adminmenu` / administrator | none declared | Admin cog/panel | None |
| 🔧 Settings / Configuration | `!settings` / administrator | none declared | Settings cog/hub | None |
| 🩺 Platform / Diagnostics | `!platform` / administrator | none declared | Diagnostic cog special builder | None |
| 🧭 Server Management | `!servermanagement` / administrator | none declared | Server Management cog/hub | None |
| 📋 Advanced / All Commands | internal sentinel / always | governance-visible top-level subsystems only | `HelpPanelView` | None |

### Subsystem visibility and placement audit

Legend: **Home** means a registered mother hub exists; **Advanced** means it can appear in the parent-filtered Advanced list when governance-visible; **Child** means `parent_hub` hides it from Advanced/Home and a parent panel is expected to surface it. Every row's display name/description/emoji/tier/entry points is static in `SUBSYSTEMS`; no row is guild-renamable, guild-description-customizable, or guild-reorderable today.

| Subsystem (display) | Tier / placement | Entry points (command metadata source) | What Help respects today | Main drift/risk |
|---|---|---|---|---|
| `admin` (Administration) | owner; Home via admin hub | `adminmenu` | Home hub min tier is administrator, not subsystem owner tier; direct route unfiltered | Hub/subsystem tier mismatch |
| `server_management` | administrator; Home | `servermanagement` | Home tier only; direct route unfiltered | Does not consume composite access |
| `moderation` | moderator; Home | `modmenu`, warn/timeout/kick/ban/unban | Home tier only; panel owns commands | Dedicated panel can drift from command/access metadata |
| `economy` | user; Home | `economymenu`, daily/work/balance | Home tier only | Same |
| `inventory` | user; Child of economy | `inventory` | Governance affects direct Advanced source set, but parent filter removes row | Reachability depends on Economy panel/static child wiring |
| `mining` | user; Child of games, Economy cross-link | `minemenu`, `mine` | Same | Multi-hub placement duplicated across registries/views |
| `xp` | user; Child of community | `xpmenu`, `rank` | Same | Parent panel controls discoverability |
| `role` | administrator; Child of community | `rolemenu` | Governance tier/override can hide it; Community panel must also filter correctly | User-tier parent can expose admin child unless panel checks |
| `channel` | administrator; Advanced; linked from Admin/Server Mgmt panels | `channelmenu` | Advanced governance-visible; direct route unfiltered | No declared parent despite panel nesting |
| `cleanup` | administrator; Child of moderation | cleanup/word/history | Parent panel-dependent | Hub minimum moderator vs child administrator requires panel filtering |
| `games` | user; Home | `games` | Home tier only | Dedicated child list/actionability contract |
| `community` | user; Home | `community` | Home tier only | Spotlight is not yet a registered child |
| `blackjack` | user; Child of games | blackjack aliases | Parent panel-dependent | Dedicated static action panel |
| `btd6` | user; Home | `btd6`, `btd6menu` | Home tier only | Split BTD6 cogs/commands are represented under one subsystem imperfectly |
| `deathmatch` | user; Child of games | deathmatch aliases | Parent panel-dependent | Entry-point alias matching owns cog association |
| `rps_tournament` | user; Child of games | `rps` | Parent panel-dependent | Cog association depends on static entry point |
| `counting` | user; Child of games; Community cross-link | `countingmenu` | Parent/cross-link panel-dependent | Duplicate placement metadata/view wiring |
| `chain` | user; Child of games; Community cross-link | `chainmenu`, `chain` | Parent/cross-link panel-dependent | Same |
| `leaderboard` | user; Child of economy; Community cross-link | leaderboard aliases | Parent/cross-link panel-dependent | Same |
| `proof_channel` | staff; Child of moderation | prize commands | Parent panel-dependent | Parent minimum moderator is higher than staff; direct route unfiltered |
| `utility` | user; Home | utility commands | Home tier only | Dedicated panel static |
| `general` | user; Child of utility | `generalmenu` | Parent panel-dependent | Static panel |
| `four_twenty` (420) | user; Child of utility | 420 aliases | Parent panel-dependent | Static/easter-egg placement |
| `help` | user; Advanced | `help` | Governance can hide the Help row in Advanced, but Help remains callable/front-door guarded separately | Self-referential subsystem has no panel hook |
| `diagnostic` | administrator; Home | diagnostics/ping/platform | Home tier only; route override selects Platform vs Diagnostics | Alias/builder override is hardcoded in route module |
| `ai` | administrator; Advanced / linked panels | `ai`, `aimenu` | Advanced governance-visible; direct route unfiltered | Not a mother hub despite substantial panel |
| `settings` | administrator; Home | `settings` | Home tier only | Static hub metadata; no Help settings |
| `logging` | administrator; Child of moderation | `logging` | Parent panel-dependent | Static child panel |

### Unregistered and split surfaces

- `community_spotlight_cog.py` is loaded but absent from `SUBSYSTEMS`/`HUBS`, so it is not governed or discoverable through Help/catalogue as a subsystem. Q-0044 already chose registration as a Community child via the future scaffold; that implementation remains outside this audit.
- Bootstrap access and split BTD6 support/ops cogs are loaded extensions but are intentionally not one-to-one Help subsystems. Therefore “loaded cog,” “subsystem,” and “Help category” are different concepts and must not be conflated in a future catalogue.

## 5. Cog/subsystem visibility audit

### What can be controlled today

- **Per guild/category/channel/thread subsystem discoverability:** yes, through governance visibility rows and the canonical audited governance write path. Help Advanced consumes this result; Help Home and direct routes do not consistently consume it.
- **Per-role/tier visibility:** default tier metadata and configured moderator/trusted role resolution affect governance. Help Home uses only the resulting tier; Advanced uses full governance visibility.
- **Per-channel cog routing:** yes through command routing, but Help does not consult it.
- **Per-channel command admission:** yes through central command access, but Help does not consult it.
- **Disabled/hidden commands:** generic fallback embeds exclude disabled commands, Discord-hidden commands, and ledger classifications `hidden`/`legacy_duplicate`. Dedicated panels and single-command Help do not uniformly apply that filter.
- **Unloaded/failed cogs:** governance can mark known failed subsystems internal, and direct lookup requires a live cog. Home hubs can still be advertised because hub filtering does not inspect live host availability.

### Consistency conclusions

- Help **does respect subsystem visibility only on Advanced and when rebuilding its visible list**, not on Home hub composition or target authorization.
- Help **does not respect access projection** today.
- Help may show commands/features users cannot run; execution remains protected by central admission/governance/callback checks, but discovery can mislead.
- Help may advertise locked/routed-off features. The active adaptive plan explicitly owns the future `help_advertises_locked` finding and Help Preview; use that work rather than a local Help-only lock detector.
- Setup wizard cog routing, governance visibility panels, Settings command access, Access Explorer, Help Home, and dedicated panels currently expose different slices of effective availability. This is explainable only by reading several surfaces; there is no shared projected Help render model.

## 6. Command panel audit

### Current panel families

1. **Generic fallback command embed (`build_cog_embed`)**
   - Includes live top-level prefix commands from `cog.get_commands()`.
   - Filters `cmd.hidden`, `cmd.enabled`, and static ledger classification.
   - Uses live command name, aliases, signature, and `cmd.help`; caps at 24 fields.
   - Preserves cog declaration order; it does not explicitly sort/group.
   - Does not evaluate governance, routing, command access, capability, `can_run`, channel, or user.

2. **Single-command embed (`build_single_command_embed`)**
   - Resolves via `bot.get_command`, including aliases.
   - Displays one command's help/usage/aliases.
   - Does not apply the hidden-from-help classification or effective-access checks.

3. **Dedicated cog/hub panels (`build_help_menu_view`)**
   - Built across many cog/view files with independently authored buttons, copy, ordering, grouping, and callback policy.
   - Often provide actions rather than a literal command list.
   - Actionability is protected for Games children, and navigation helpers are widely tested, but no central per-guild command-panel overlay exists.

### Current customization and semantics

- Commands cannot be hidden, added, removed, regrouped, renamed, or reordered per guild/channel in Help panels.
- Removing a command from a future Help panel should be presumed **display-only** until the owner decides otherwise. Execution disabling already has separate canonical owners.
- A display-only alias must never register a new Discord/prefix/slash alias. It should be presentation metadata mapped to a stable command identity.
- Hiding a slash command from a custom Help panel does not remove it from Discord's slash-command picker. Discord registration/sync is deployment/global behavior, not per-guild Help presentation.
- Dedicated panels may contain non-command actions; a future overlay must distinguish command references, panel actions, navigation, and explanatory content rather than treating every button as a command.

### Risks to pin before implementation

- Stable identity: use subsystem key/hub key/qualified command identity, not display labels.
- Nested/grouped/slash commands: prefix `cog.get_commands()` and ledger entries do not represent every panel action identically.
- Security: never interpret Help hide/show as permission or execution authorization.
- Stale overrides: commands/hubs can be removed or renamed; overlays need validation, ignored-orphan reporting, and reset/migration behavior.
- Determinism: default order + overlay order must have explicit tie-breaking and stable fallbacks.

## 7. Customization gap analysis

| Capability | Today | Existing owner/seam to extend | Gap/risk |
|---|---|---|---|
| Guild-specific Help Home message | No | Settings mutation for bounded text; structured overlay for rich/template form | Format/variables/product decision required |
| Guild-specific top-level category visibility | No presentation-only switch; governance can hide subsystems but Home ignores full result | Governance for true discoverability; overlay for display-only suppression | Must define display-only vs governed hiding |
| Guild-specific subsystem visibility in Help | Partially via governance; inconsistent across surfaces | Governance + Help Projection | Home/direct routes must consume projection |
| Custom display names | No | Help overlay/catalogue | Decide Help-only vs all panels; preserve stable/default identity |
| Custom descriptions/emoji | No | Help overlay/catalogue | Validation/localization/Discord limits |
| Command hide/show per guild | No | Structured Help overlay | Must remain separate from execution access |
| Command hide/show per channel/category/thread | No display overlay; execution/routing policies exist | Prefer projection of existing policies first; add presentation scope only if owner approves | High complexity/cache cardinality/duplicate-policy risk |
| Command reorder/grouping | No | Structured Help overlay | Dedicated panel/action semantics complicate global ordering |
| Display-only aliases | No | Help overlay | Must not register command aliases |
| Execution-blocking aliases/hide | Existing command access/routing only | Command access/routing/governance | Do not place in Help storage |
| Reset to default | Settings/governance have reset/inherit patterns; no Help overlay | Overlay mutation service | Required from first write phase |
| Audit log | Settings/governance writes audited; no Help writes | Reuse audit event pattern | Required from first write phase |
| Preview before apply | Setup change plan exists; no Help preview | Help Projection + setup change plan/draft for compound edits | Coordinate with P1C Help Preview |
| Setup wizard integration | No Help customization | Setup sections/draft/final review | Later phase only |
| Settings cog integration | No Help customization | Settings hub/editors | Later phase only |
| Per-role/capability variants | Tier/governance visibility exists; no presentation variants | Access/governance projection | Avoid arbitrary role-specific overlay initially |
| Localization readiness | Static English strings across registries/panels | Catalogue stable keys + renderer layer | No localization service currently identified |

## 8. Storage and mutation options

### Existing route comparison

| Route | Pros | Cons / migration | Cache, audit, reset | Duplicate ownership assessment |
|---|---|---|---|---|
| **SettingsRegistry + SettingsMutationPipeline** | Existing declarations, typed resolution, editors, audit transaction, per-key cache invalidation/events, reset | Best for bounded scalar/text values; poor fit for ordered structured category/command overlays unless JSON/blob support is deliberately designed | Strong existing audit/reset/cache model | Good for `home_message` or simple flags; risky as a generic structured dump |
| **Governance `subsystem_visibility`** | Already scope-aware to guild/category/channel/thread; audited/inherited; canonical discoverability | Stores true subsystem visibility only, not names/descriptions/order/command display; overloading would conflate presentation and policy | Strong cache/invalidation/audit/inherit | Use for true visibility only; adding presentation fields here would duplicate/muddy ownership |
| **Command access/routing tables** | Canonical execution/admission and per-scope routing | Not presentation storage; hiding Help rows here would make UI semantics implicit | Existing owner-specific cache/mutation | Consume as projection inputs; never store Help copy/order here |
| **CustomizationCatalogue** | Already composes live commands/settings/schema/help hooks/panels; ideal basis for defaults/inventory | Explicitly read-only/frozen snapshot; no persistence or mutation path | Rebuild/read-model semantics only | Extend its metadata inputs or create adjacent Help Catalogue; do not turn it into ad hoc DB writer |
| **Setup draft/change plan** | Existing compound preview/review/apply model and rollback hints | Not canonical steady-state storage; needs concrete operation kinds and owner service | Strong preview/audit pattern | Use for bulk/compound editing UX, not as source of truth |
| **New normalized Help overlay table + audited mutation service** | Fits ordered structured overrides, stable identities, per-field reset, orphan detection, versioning | New migration/service/cache/tests; must avoid re-owning governance/access | Require generation cache, audit rows/events, reset/delete semantics, migration-safe defaults | Recommended only for presentation fields existing stores cannot model |

### Recommended storage boundary

Use a hybrid, owner-preserving model:

1. **Governance remains canonical** for whether a subsystem is discoverable at a scope.
2. **Command access/routing remain canonical** for whether a command/cog can execute or is routed here.
3. **Settings mutation may own simple Help-level scalar/text preferences** if the owner chooses a bounded plain-text home message or small enum/boolean preferences.
4. **A new structured Help presentation overlay** is justified for ordered hub/subsystem/command display overrides. It should be keyed by stable entity identity, be guild-scoped initially, store only deviations from defaults, and be mutated through one audited/reversible service.
5. **CustomizationCatalogue/Help Catalogue remains read-only**, composing registry/live metadata and exposing orphan/coverage findings.

Suggested conceptual overlay fields (not a schema commitment): guild id; entity kind; stable entity key; optional visible/display name/description/emoji/order/group/display alias; version/timestamps/actor. Absence means inherit default. A deleted/default reset removes the override row. Do not store execution permission in this table.

## 9. Target architecture recommendation

### Canonical read path

```text
SUBSYSTEMS + HUBS + command-surface ledger + panel declarations/live availability
                              ↓
                    HelpCatalogue (defaults)
                              +
                  GuildHelpOverlay (presentation only)
                              +
 governance visibility + command routing/access + availability projection
                              ↓
 HelpProjectionService (audience/context-aware, reason-coded, deterministic)
                              ↓
 Help Home / Advanced / typed routes / dedicated-panel composition / preview UI
```

### Responsibilities

- **Help Catalogue:** stable keys and default presentation metadata for hubs, subsystems, commands, and panel actions. It should expose relationships (host subsystem, parent/cross-link hub, representative commands, panel declaration) and live/unavailable/orphan findings. Prefer extending/adjacent composition around `customization_catalogue`, `subsystem_registry`, `hub_registry`, and command ledger rather than another static list.
- **Guild overlay:** presentation-only deviations. Initial scope should be guild-wide. Names/descriptions/order/hide flags must never alter command registration or execution identity.
- **Help Projection:** one read-only service that accepts guild/channel/category/thread/audience context and returns reason-coded render models. It composes governance and access projection rather than implementing policy. It should distinguish `shown`, `display_hidden`, `governance_hidden`, `routed_off`, `command_locked`, `unavailable`, and `orphaned_override`.
- **Renderers/views:** thin adapters. Help Home, Advanced, typed/direct routes, and generic panels consume projection models. Dedicated panels migrate incrementally to catalogue-backed composition where useful; action-heavy panels need not become generic command lists.
- **Mutation:** focused single edits go through an audited Help-overlay mutation service (or SettingsMutationPipeline for declared scalar fields); compound edits stage through setup draft/change-plan preview and final review.

### Defaults, reset, invalidation, and observability

- No overlay rows means byte-for-byte/default-order behavior where practical.
- Every override supports reset-to-inherit; full reset deletes guild overlay rows.
- Validate stable keys against the current catalogue at write time; preserve/report orphaned rows rather than crashing render.
- Emit structured mutation/audit events with actor, guild, entity key, field, previous/new values, and mutation id.
- Maintain a per-guild Help-overlay generation/cache; invalidate on overlay mutation. Governance/access/routing owners continue invalidating their own caches. A Help projection may cache only with all owner generations/context dimensions represented, or initially remain uncached.
- Diagnostics should report catalogue coverage, stale overrides, missing panel hosts, and divergence between Home/Advanced/panel projection.

### Security and policy rules

- **Display-only hide is not deny.** Execution remains controlled by command access, routing, governance execution/capabilities, and callback checks.
- A UI may explain “hidden from Help but still executable” to operators. Public Help should not leak sensitive internal commands merely because an overlay asks to show them; static classification and policy floors remain non-overridable.
- Custom labels are presentation only. Admin/debug views should retain stable keys and likely default labels alongside custom labels, pending Q-0058.
- Per-role/personal Help variants should derive from access/governance projection before introducing role-targeted presentation overlays.

### Required test layers

- Catalogue identity/relationship/default-order contract tests.
- Projection matrix across tier, guild/category/channel/thread visibility, routing, command access, unloaded cog, hidden classification, and overlays.
- Route tests proving typed, dropdown, Home, and Advanced consume the same projection decision.
- Mutation authorization/audit/invalidation/reset/idempotency/orphan tests.
- Dedicated-panel adoption/contract tests and no-permission-bypass tests.
- Setup/settings preview/apply/rollback tests.
- Docs inventory/reachability and migration tests.

## 10. Ideas/options with tradeoffs

| Option | Enables | Does not enable | Risk / size | Likely files | Architecture fit |
|---|---|---|---|---|---|
| **A. Minimal Help display customization only** | Custom Home message and maybe guild hide/rename for Home rows | Does not unify direct routes, panels, governance/access, command ordering | Low–medium / S–M; risks becoming a local patch | `help_cog.py`, a few setting keys/editors | Weak unless explicitly temporary; duplicates presentation logic |
| **B. Help customization through SettingsRegistry** | Audited simple text/boolean/enum preferences with existing reset/edit UI | Ordered structured overlays and per-command records fit poorly | Medium / M; JSON-blob temptation is high | settings registry/keys/mutation/views + Help read | Good for simple preferences only |
| **C. Help customization through setup/platform CustomizationCatalogue** | Shared inventory, preview/editor discoverability, panel/setting/command coverage | Catalogue is read-only and not a storage owner today | Medium–high / M–L | customization catalogue, settings/setup views, new owner service | Strong as catalogue/read-model foundation; not as writer itself |
| **D. Unified command/hub catalogue with per-guild overlays** | Consistent Home/routes/panels, rename/hide/order, diagnostics, future localization | Requires staged panel adoption and structured storage | High / L–XL | registries, ledger/catalogue, new projection/mutation/storage, Help/views/tests | Best long-term fit; recommended target after foundation phases |
| **E. Combine Help visibility with governance/subsystem visibility** | True subsystem hide/inherit across scope, no duplicate policy | Does not model presentation rename/order/message; command-level display is still separate | Medium / M | Help projection + governance/access tests/views | Correct for true visibility, incorrect if overloaded with presentation fields |

**Recommended combination:** D as the target architecture, implemented incrementally with E for true subsystem visibility, B for bounded simple preferences, and C as the inventory/editor integration seam. Do not ship A as an isolated permanent system.

## 11. Phased implementation roadmap

> **Phase 0's bounded reconciliation shipped 2026-06-09 in PR #642** (execution-plan
> Lane 8): the surface-map preamble counts are true again (10 hubs · 29 subsystems ·
> 36 loaded extensions · 28 define `build_help_menu_view`) **and pinned to the live
> registries by test**, and a characterization net pins the five render paths
> (Home · Advanced · typed routes · generic embed · dedicated panels).
>
> **Phases 1 + 2 shipped 2026-06-10 in PR #657** (consolidated plan **Batch 6** —
> verify merged): `services/help_catalogue.py` (the stable-keyed inventory +
> four registry-drift finding kinds, pinned empty) and
> `services/help_projection.py` (the §9 reason-coded `HelpProjection` —
> vocabulary exactly as specified below; only `display_hidden` /
> `governance_hidden` hide; lock states stay advertised). **All five render
> paths consume the one projection** — Home now respects host-subsystem
> governance visibility, typed/dropdown routes check their target, the
> single-command route applies the shared display filter, and
> `HelpPanelView._on_select` re-resolves at click time. The Q-0074
> admin-tier registry fix rode along (placement == admission tier, pinned
> by the catalogue's `tier_mismatch` finding).
>
> **Phase 3 shipped 2026-06-10 in PR #659** (#657 merged the same day,
> clearing the gate): migration 064 `help_overlay` (guild display-hide /
> rename / re-describe per hub/subsystem, store-only-deviations) +
> `services/help_overlay_mutation.py` (the audited seam: admin gate,
> write-time catalogue-key validation, partial-edit merge, per-field +
> full reset, cache invalidation, `audit.action_recorded`) +
> `services/help_overlay.py` (cached fault-tolerant read model), flowing
> through the HLP-2 projection into **all five render paths**
> (presentations carry custom + default per Q-0058; orphans reported via
> `orphaned_overrides`; no-rows = byte-identical, pinned). Q-0055's
> display-only rule is an **import fence** on the admission paths.
> **Next: Phase 5's editor UI** (settings/setup integration — including
> the Q-0059 embed-builder Home message, whose mandatory preview belongs
> with the editor) and Phase 4's command/panel-action records (Q-0057
> rider: no ordering until stable action identities).
> **Phase 5 plan ready (2026-06-10):**
> [`help-overlay-editor-ui-plan-2026-06-10.md`](help-overlay-editor-ui-plan-2026-06-10.md)
> — 2 PRs (A: editor on the shipped seam, no migration · B: the Q-0059
> Home embed builder, migration widening the 064 CHECK as its header
> pre-plans).
> **Phase 5 EXECUTED same day: PR A = #677** (the hide/rename/re-describe
> editor — staff-hub `✏️ Help editor` button + the Settings-hub "Help
> appearance" domain group; every action one audited `help_overlay_mutation`
> call; live round-trip verified) **· PR B = #679** (migration 067 `'home'`
> + the Q-0059 Home embed builder with **mandatory preview**, the shared
> `home_embed_frame` composer, mention suppression, byte-identical default
> pinned). **The remaining Help-lane tail is Phase 4's command/panel-action
> records only** (Q-0057 rider).

| Phase | Goal and likely files | Dependencies / off-limits | Migration / reset | Verification | Recommended next agent |
|---|---|---|---|---|---|
| **0 — mapping/docs/current-behavior pins** | Reconcile `help-command-surface-map.md` counts/Spotlight state; add tests for Home ignoring scope visibility/direct-route behavior as explicit current findings; define projection contract | Owner answers below; coordinate adaptive P1B/P1C; no runtime change | None | docs checks + targeted Help/hub/access tests | **Codex mapping**, then GPT/manual review |
| **1 — metadata/source-of-truth cleanup** | Define Help Catalogue model from subsystem/hub/ledger/customization catalogue; eliminate duplicated child roster/order/alias metadata where safe; catalogue dedicated panel declarations | Do not rewrite panels or permissions | No DB migration; stable-key contract required | catalogue/registry/doc contract tests | Opus planning/revision → Sonnet implementation |
| **2 — correct top-level visibility and subsystem filtering** | Introduce Help Projection read model; make Home/Advanced/routes consume governance/access projection consistently with reason codes | P1B `help_advertises_locked`/Q-0045 path; do not change execution denial | No Help storage; default behavior changes need explicit release note/rollback flag if broad | audience/context matrix and route parity tests | Opus revision → Sonnet implementation |
| **3 — guild-level rename/hide customization storage** | Add audited guild-scoped presentation overlay for hub/subsystem names/descriptions/display-hide + optional simple Home message | Requires Q-0055/Q-0056/Q-0058/Q-0059 decisions; true visibility stays governance-owned | Additive migration; absence=inherited default; per-field/full reset | mutation/audit/cache/orphan/default-byte tests | Opus plan → Sonnet implementation → GPT/manual review |
| **4 — command panel hide/show/reorder** | Add stable command/panel-action presentation records and overlay ordering; migrate generic fallback first, then selected dedicated panels | Requires Q-0055/Q-0057; do not alter slash registration/execution | Additive structured rows/versioning; reset/inherit and stale-command handling | panel composition + security + deterministic ordering tests | Opus planning/revision → Sonnet implementation |
| **5 — Settings/setup wizard UI** | Add structured editor, preview, Help Preview link, and optional setup section/final-review operations | Coordinate active P1C Help Preview; no direct writes from views | Setup operation migration only if new op kinds; preview/rollback required | settings/setup view/service tests + manual Discord UX | Sonnet implementation + GPT/manual UX review |
| **6 — audit/reset/preview/test hardening** | Full reset, export/debug view, orphan diagnostics, conflict/explanation UI, cache generation metrics | Preserve privacy/security and owner copy decisions | Backfill/cleanup tooling only if proven necessary; reversible | full matrix, architecture/docs checks, fault injection | Codex mapping/test audit + GPT/manual review |
| **7 — legacy/static cleanup** | Remove obsolete Help-only builders/static lists and migrate remaining panels where beneficial | Only after adoption/telemetry; do not genericize action-heavy panels unnecessarily | Remove only unused data after migration window | full suite + navigation/actionability contracts | Sonnet implementation with Opus revision |

## 12. Open owner questions

The unresolved product decisions are routed as Q-0055 through Q-0059 in `docs/owner/maintainer-question-router.md`:

1. Is hiding a command from Help display-only, or can the same action also block execution?
2. Do custom cog/subsystem names affect only Help or every bot panel?
3. Is command order global per guild or scoped to each panel?
4. Should admin/debug views preserve/show default names beside custom names?
5. What formats and template variables are allowed for a custom Help Home message?

Safe planning defaults until answered: presentation-only hiding; Help-only names; panel-local ordering; admin/debug shows default + custom; plain text with no variables.

## 13. Verification plan

### Performed in this mapping session

- Verified all requested source/doc paths exist.
- Read workflow, architecture, ownership, runtime-contract, current-state, roadmap, Help/hub/setup/access/customization docs, and relevant folios.
- Manually verified claims in Help, route, registry, governance, access projection, command ledger/access/routing, settings/customization/setup, navigation, view, test, and config source.
- Enumerated live registry values from `HUBS` and `SUBSYSTEMS` under the repository Python environment.
- Inspected targeted Help/hub/access/settings/customization/navigation test contracts.
- Attempted required Python 3.10 context maps and recorded the environment limitation; ran the available Python 3.12 context map for Help.
- Attempted live open/recent PR verification; recorded the missing `gh`/remote limitation.

### Required for each future phase

- `python scripts/check_docs.py`
- Targeted `pytest` for Help, hub registry, access projection, governance, settings/customization, and affected views.
- `python scripts/check_architecture.py --mode strict` for runtime phases.
- Migration/apply/rollback tests for any new storage.
- Manual Discord smoke across user/mod/admin audiences and guild/channel/category/thread visibility scopes.
- Verify no Help customization changes slash registration or execution authorization.

## 14. Recommended next session

**Next destination: owner Decisions, then Opus planning/revision for Phase 1 + Phase 2 boundaries.** Resolve Q-0055–Q-0059 first. In parallel, a bounded Codex documentation/test session can reconcile `docs/help-command-surface-map.md` counts and add explicit current-behavior characterization tests without implementing customization. Do not begin overlay storage or editor UI until the Help Catalogue/Projection contract and display-vs-execution semantics are approved.
