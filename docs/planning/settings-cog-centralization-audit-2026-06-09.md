# Settings cog centralization audit and refactor roadmap — 2026-06-09

> **Status:** `plan` — source-verified mapping and implementation roadmap; no runtime changes in this session.
> **Truth rule:** source code wins over this document. Re-run the verification plan before implementation because schemas are registered at cog load and active subsystem work can move concurrently.
> **Live concurrency check:** GitHub API showed one open PR on 2026-06-09: [#624](https://github.com/menno420/superbot/pull/624), the mining Workshop/durability lane. It does not touch the settings stack, but mining product/config conclusions remain concurrency-sensitive. AI UI expansion remains per-exposure gated; governance setup remains deferred pending a scope decision.
> **Post-merge note (2026-06-09, end-of-day consolidation):** this audit merged as **#625**; #624 and **#626** (Community Spotlight registration) merged the same day, so Spotlight rows below are resolved history. The §11 phasing is queued: Phases 0+1 = scoreboard **Lane 7** via [`consolidated-productive-session-plan-2026-06-09.md`](consolidated-productive-session-plan-2026-06-09.md); the Phase 2/3 directions were **decided same evening** — **Q-0063: converge gradually** (seven-key projection kept + diagnosed, projected-key set frozen, typed-panel convergence planned at Phase 3) and **Q-0064: announcement → binding, CT group → guided advanced flow** (lands with Phase 2's BTD6 rows). Router §27 is canonical.

## 1. Executive summary

SuperBot already has a strong central **scalar-settings** architecture. `SettingSpec` declarations in subsystem schemas feed a read-only `SettingsRegistry`; `SettingsMutationPipeline` is the canonical typed, capability-checked, audited, cache-invalidating scalar writer; `settings_resolution` is the canonical typed scalar reader; and the Settings Manager automatically dispatches boolean, enum, numeric-preset, channel, role, number, text, and reset editors from schema metadata.

The high-value refactor is therefore **not to invent centralization**. It is to finish and clarify the existing platform:

1. **Discovery/display is currently wrong for the owner's desired UX.** The Settings hub deliberately lists every non-internal `SUBSYSTEMS` entry, not only configurable groups. There are 28 registered subsystem identities but the Discord select is capped at 25, so some entries are silently unreachable from the dropdown. Many listed pages have no scalar settings, bindings, or resources. The registry is used for counts, but not as the hub's discovery source.
2. **Central scalar definitions are complete only for 9 settings-bearing schemas (36 settings).** A tenth registered schema, BTD6, has bindings but no scalar settings. Eighteen manifest subsystems have no schema at all. This is sometimes correct (router/hub/read-only cogs), sometimes a separate-policy domain, and sometimes incomplete coverage.
3. **There are multiple legitimate configuration domains.** Scalar settings, bindings, provisioning, governance/visibility/cleanup policy, command access/routing, role thresholds/exemptions, AI policy/orchestration, feature flags, participation/preferences, and game/runtime state have separate canonical owners. They must not be collapsed into one generic settings writer. The Settings Manager should become a common **discovery and navigation surface**, not a god-object mutation service.
4. **AI already has an intentional but complex compatibility projection.** The generic page exposes ten legacy-KV `SettingSpec`s. Seven guild-policy scalars are projected after each scalar mutation through `ai_policy_mutation.project_from_legacy_settings` into the typed `ai_guild_policy` row consumed by the live natural-language resolver. Memory settings remain scalar-owned and are read by `ai_memory_service`; the free-text guild-instruction scalar is explicitly not projected to typed instruction profiles. Projection failure is best-effort, so the KV mutation can succeed while typed policy projection fails and emits diagnostics. This is not missing centralization, but it is a high-risk dual-write/partial-projection seam that should be clarified before broad AI Settings work.
5. **Structured editing is already good but incomplete.** Booleans toggle; enums select; channel/role pointers use native selectors; most numbers have preset buttons plus an optional override modal; every scalar can reset. Avoidable text remains in dedicated XP modals, free-form numeric fallbacks, BTD6 command-only channel/group configuration, and several command/panel-only policy surfaces. Truly free-form AI/moderation instruction/template text remains justified.
6. **Direct scalar DB writes are fenced but not eliminated.** The AST invariant allowlists governance version writes and typed BTD6/runtime-pointer services. These are documented exceptions, but BTD6 version-announcement channel and CT team ID are operator configuration hidden from the Settings Manager and bypass scalar mutation audit/cache/event semantics by design.
7. **Setup convergence is partial and architecturally sound where implemented.** Setup's `set_setting` draft operation ultimately calls `SettingsMutationPipeline`; moderation setup shares central scalar definitions by name. Cleanup, routing, bindings, provisioning, and role thresholds correctly use their own domain operations. The remaining work is shared discovery/metadata and UI projection—not forcing every domain through `set_setting`.

**Recommendation:** make a richer, typed `settings_registry`/configuration catalogue the single discovery surface for the Settings Manager; include only groups with at least one actionable/configurable surface the actor can use; preserve domain-specific mutation services; document and harden the AI projection seam; then progressively add declarative editor/navigation metadata and remove duplicate command-only routes.

## 2. Source-verified file inventory

### 2.1 Canonical scalar-settings stack

| Path | Owner / important surface | Reads / writes | Families | Classification |
|---|---|---|---|---|
| `disbot/core/runtime/subsystem_schema.py` | `SettingSpec`, `BindingSpec`, `SubsystemSchema`, `register`, `all_schemas` | In-memory declarations only | All declared subsystem config | **Canonical definition protocol** |
| `disbot/core/runtime/settings_registry.py` | `build_registry`, `SettingsRegistry`, duplicate/missing-key/capability findings | Reads loaded schemas; cached in memory | Scalar settings only | **Canonical scalar discovery snapshot**, currently too lossy for full UI discovery |
| `disbot/services/settings_resolution.py` | `resolve_setting`, `resolve_all`, `resolve_value`, coercion/validation/provenance | Reads `guild_settings` through typed cache; default fallback | Declared scalar settings | **Canonical scalar read path** |
| `disbot/services/settings_mutation.py` | `SettingsMutationPipeline.set_value`; authority, validation, kill-switch, serialization, audit, invalidation, event | Reads previous resolved value; writes KV + audit; invalidates key cache | Declared scalar settings | **Canonical scalar write path** |
| `disbot/utils/db/settings.py` | `get_setting`, `set_setting` | Direct `guild_settings` KV primitive | Legacy scalar/pointer/runtime keys | **Persistence primitive; not an operator-facing seam** |
| `disbot/utils/db/settings_audit.py` | settings audit insert/read helpers | Writes/reads `settings_mutation_audit` | Scalar settings | **Canonical scalar audit persistence** |
| `disbot/migrations/029_settings_mutation_audit.sql` | Audit table/indexes and actor/action contract | Creates `settings_mutation_audit` | Scalar settings | **Canonical audit schema** |
| `disbot/core/runtime/guild_config.py` | Per-key TTL cache | Cached KV reads/invalidation | Legacy KV | **Canonical cache primitive** |
| `disbot/utils/guild_config_accessors.py` | Typed accessors and `invalidate_setting_value` | Reads cache/DB; invalidates per key | XP, generic settings, command access | **Canonical adapter layer; some legacy direct reads remain** |

### 2.2 Definitions and registration

| Path(s) | Purpose / families | Classification |
|---|---|---|
| `disbot/cogs/{ai,blackjack,deathmatch,economy,logging,moderation,role,rps_tournament,xp}/schemas.py` | 36 scalar `SettingSpec`s plus bindings/resources/capabilities | **Canonical subsystem declarations** |
| `disbot/cogs/btd6/schemas.py` | BTD6 binding only; no scalar setting | **Canonical binding declaration, not scalar coverage** |
| `disbot/utils/settings_keys/__init__.py` and `ai.py`, `btd6.py`, `btd6_cache.py`, `economy.py`, `games.py`, `governance.py`, `logging.py`, `moderation.py`, `role.py`, `xp.py` | Stable KV key constants grouped by owner | **Canonical key names**, but key existence does not imply a `SettingSpec` or Settings UI coverage |
| Cog `cog_load()` registration in the ten schema-bearing cogs | Registers schemas before startup builds registry | Inherently load-order dependent; **canonical registration route** |
| `disbot/bot1.py` | Calls `settings_registry.build_registry()` after cogs load | **Canonical startup build point** |

Notable key-only exceptions: BTD6 cache keys have no live `SettingSpec`; `SKIP_ROLES` is retained but no longer read; `ACTIVE_TOURNAMENT` is runtime state; governance version is internal state; BTD6 CT group/version-announcement pointers are typed service-owned command configuration.

### 2.3 Settings Manager and editors

| Path | Purpose | Mutation/read behavior | Classification |
|---|---|---|---|
| `disbot/cogs/settings_cog.py` | `!settings`, `/settings`, Help hook, `!settings access`; manager feature gate | Opens views; no scalar write itself | **Canonical front door** |
| `disbot/views/settings/hub.py` | Top-level inventory, subsystem select, diagnostics, command-access shortcut | Uses registry for count but `SUBSYSTEMS` for discovery | **Canonical UI hub with discovery defect** |
| `disbot/views/settings/subsystem_view.py` | Renders schema settings/bindings/resources/commands; dispatches editors/reset | Reads schemas/resolver; routes mutations to editor widgets | **Canonical scalar detail/editor dispatcher** |
| `edit_boolean.py` | Immediate boolean inversion | `SettingsMutationPipeline` | **Canonical typed editor** |
| `edit_enum.py` | Allowed-values select | `SettingsMutationPipeline` | **Canonical typed editor** |
| `edit_number_presets.py`, `edit_number.py` | Preset buttons plus text override; generic numeric modal | `SettingsMutationPipeline` | **Canonical numeric editors; text fallback remains** |
| `edit_channel.py`, `edit_role.py` | Native Discord channel/role select + clear | `SettingsMutationPipeline` | **Canonical structured pointer editors for legacy scalar pointers** |
| `edit_text.py` | Free-form string modal | `SettingsMutationPipeline` | **Canonical fallback; use only where text is semantically required** |
| `reset_button.py` | Reset select calls pipeline with declared default; audit action remains `set_value` | `SettingsMutationPipeline` | **Canonical reset UI; explicit-default write and audit-action semantics need correction** |
| `invalid_settings.py`, `needs_setup.py`, `missing_bindings.py`, `audit_view.py` | Cross-cutting diagnostics | Read-only | **Canonical diagnostics, though missing-resources and policy coverage are incomplete** |
| `edit_command_access.py` | Structured command-access mode buttons + channel multi-select | `command_access_service`, not scalar pipeline | **Correct domain-specific settings-adjacent editor** |

### 2.4 Setup/platform and separate canonical configuration domains

| Path(s) | Domain and behavior | Classification |
|---|---|---|
| `disbot/services/setup_operations.py`, `setup_draft.py`, `setup_change_plan.py` | Draft/preview/apply; `set_setting` dispatches to scalar pipeline; bindings/cleanup/routing/roles use domain operations | **Canonical compound/draft adapter** |
| `disbot/views/setup/sections/{identity,moderation}.py` | Stages scalar moderation operations | **Shared scalar mutation route; good convergence** |
| `disbot/views/setup/sections/{channels,logging_presets,cleanup,cog_routing,roles,role_templates}.py` | Stages binding/provisioning/policy/routing/role operations | **Correct separate-domain setup routes** |
| `disbot/services/ai_policy_mutation.py`, `ai_orchestration_mutation.py`; `disbot/utils/db/ai.py`; `disbot/views/ai/policy/`, `views/ai/tools/` | First-class AI policy/orchestration tables, caches, structured editors | **Canonical AI typed-policy stack; generic scalar UI projects seven keys into it** |
| `disbot/services/moderation_config.py` | Reads moderation behavior through `settings_resolution.resolve_value` | **Canonical scalar consumer** |
| `disbot/governance/writes.py`, `utils/db/governance.py`, governance resolvers/views | Visibility and cleanup policies; governance audit/cache invalidation; governance-version direct KV write | **Canonical separate policy domain** |
| `disbot/services/command_access_service.py`, `command_routing.py`, corresponding DB modules | Command admission/routing configuration and audit | **Canonical separate policy domains** |
| `disbot/services/role_automation.py`, `role_exemption_service.py` | Role thresholds and exemptions | **Canonical separate role-config domains** |
| `disbot/services/binding_mutation.py`, `resource_provisioning.py`, `core/runtime/bindings.py` | Discord resource pointers and confirmed resource creation | **Canonical binding/provisioning domains** |
| `disbot/services/participation_mutation.py`, user config accessors | Per-user participation/subscription/preference/visibility | **Canonical per-user domain; not guild Settings Manager scalar data** |
| `disbot/services/rollout_mutation.py`, `core/runtime/feature_flags.py` | Platform/feature flags | **Canonical rollout domain; not scalar settings** |

### 2.5 Legacy, duplicate, command-only, or unclear surfaces

| Path / surface | Finding | Classification |
|---|---|---|
| `disbot/views/xp/config_panel.py` + `views/xp/modals.py` | Dedicated XP config still uses text modals; writes now route through scalar pipeline, but reads include direct KV/accessor paths | **Duplicate UI adapter; avoidable text entry** |
| `disbot/cogs/economy_cog.py` economy log-channel command | Routes through scalar pipeline, while generic Settings uses a native channel selector | **Command-only duplicate route; safe but redundant** |
| `disbot/services/btd6_ct_team_service.py` | Command-only typed direct-KV CT group pointer, no scalar audit/cache invalidation | **Intentional allowlisted exception; operator-config classification unclear** |
| `disbot/services/btd6_version_announce.py` | Command-only typed direct-KV channel pointer despite channel semantics | **Important centralization gap / likely binding candidate** |
| `disbot/governance/writes.py` | Direct KV governance-version marker is allowlisted; actual visibility/cleanup writes correctly use governance tables | **Internal exception, not a user setting** |
| `disbot/services/server_logging.py` | Reads logging booleans directly from KV and resolves binding-first with legacy scalar fallback for channels | **Compatibility adapter; scalar reads should converge on resolver/accessor** |
| `disbot/core/runtime/guild_resources.py`, `config_arbitration.py`, `binding_backfill.py` | Legacy-KV pointer fallback/arbitration | **Migration/compatibility adapters** |
| `disbot/cogs/cleanup/panel.py`, `cogs/logging/panel.py`, channel/role management panels | Rich management UI adjacent to Settings but domain-specific | **Canonical domain panels; should be discoverable, not absorbed** |

### 2.6 Documentation and test ownership

Canonical area docs are `docs/subsystems/settings-bindings-provisioning.md`, `docs/setup-platform/settings-customization-roadmap.md`, `docs/setup-platform/settings-customization-command-map.md`, `docs/building-roadmap/config-input-standard.md`, `docs/ownership.md`, and `docs/runtime_contracts.md`. `operator-settings-presets.md` and `roadmap_setup_platform.md` are broad reference/aspirational documents and contain expectations beyond live source.

The strongest live guards are:

- `tests/unit/runtime/test_settings_registry.py`
- `tests/unit/services/test_settings_resolution.py` and `test_settings_mutation_pipeline.py`
- `tests/unit/invariants/test_no_direct_settings_keys_writes.py`
- `tests/unit/invariants/test_settings_mutation_audit_alignment.py`
- `tests/unit/invariants/test_settings_keys_package_structure.py`
- `tests/unit/invariants/test_reserved_settings_keys.py`
- `tests/unit/views/test_settings_*` and `test_subsystem_settings_view.py`
- setup operation/draft tests and docs pinning tests.

## 3. Settings architecture map

```text
cog load
  -> cogs/<subsystem>/schemas.py register_schemas()
  -> core.runtime.subsystem_schema (live typed declarations)
  -> bot1 startup builds core.runtime.settings_registry (frozen scalar snapshot)

read scalar
  -> services.settings_resolution.resolve_setting/resolve_value
  -> utils.guild_config_accessors / core.runtime.guild_config TTL cache
  -> utils.db.settings.get_setting -> guild_settings
  -> coerce + validate -> declared default on absent/invalid row

write scalar
  -> Settings UI / setup set_setting adapter / migrated command
  -> services.settings_mutation.SettingsMutationPipeline.set_value
  -> resolve spec + capability check + operator kill-switch + coerce/validate
  -> utils.db.settings.set_setting + utils.db.settings_audit insert
  -> invalidate one cached key + emit settings.changed

compound setup
  -> stage SetupOperation(s) -> preview/change plan -> confirm/apply
  -> dispatch each operation to its owning scalar/binding/governance/routing/role service

separate domains
  -> bindings, provisioning, governance, command access/routing, AI policy,
     feature flags, participation, and role thresholds retain their own stores/services/audits
```

### Ownership details

- **Registry/discovery owner:** `subsystem_schema` owns live declarations; `settings_registry` owns the frozen scalar catalogue. The Settings hub does **not** use either as its actual group inclusion rule.
- **Key definitions:** `utils/settings_keys/*` owns legacy KV strings. Schema modules bind user-editable scalar names to those strings.
- **Persistence:** `guild_settings` is the legacy scalar KV store. Specialized domains have typed tables.
- **Audit:** scalar writes use `settings_mutation_audit`; specialized domains use their own audit/event contracts. Reset stores the default explicitly and is currently audited as ordinary `set_value`, despite the reset module documenting a future/distinct `reset_value` action.
- **Cache/invalidation:** scalar mutation invalidates one guild/key cache entry. AI policy uses an `ai_guild_policy.generation` cache plus explicit invalidation. Governance and other domains have separate invalidation.
- **Permissions/capabilities:** each `SettingSpec` declares a capability; the scalar pipeline checks it at mutation time. Hub discovery and editor visibility are not capability-filtered. Domain-specific command-access callbacks explicitly check admin at callback time.
- **Defaults/invalid values:** resolver returns the declared default for absent or invalid scalar rows and marks provenance/validity. Invalid rows remain persisted until corrected/reset.
- **Help/menu/panel integration:** SettingsCog has prefix, slash, and Help front doors. Per-subsystem pages link to a related cog panel when available. Several dedicated panels link back to Settings, but coverage is inconsistent.

## 4. Cog/subsystem settings availability

Legend: **scalar** = central `SettingSpec`; **domain** = real config with another canonical owner; **setup** = setup-only/draft surface; **command** = command-only config; **none** = should not be shown as a settings group unless it gains a real configurable surface.

| Subsystem | Current classification | Current UI / source truth | Recommendation |
|---|---|---|---|
| AI | **Scalar + typed domains; partial compatibility projection** | 10 generic scalar settings; seven guild-policy keys project to `ai_guild_policy`; memory reads scalar KV; free-text guild instruction is explicitly unprojected; dedicated scoped-policy/orchestration UIs also exist. | Keep one discoverable AI group, make projection/effective-source status explicit, and decide whether the hybrid remains intentional. UI expansion remains gated. |
| BTD6 | **Binding + command-only pointers** | Schema has strategy-submission binding, no scalar settings. CT group and version-announcement channel are command-only direct-KV typed services; cache keys are key-only. | Show only real BTD6 configurable surfaces. Promote announcement channel to binding/structured selector; owner decision for CT group. Do not expose internal cache knobs casually. |
| XP | **Scalar + domain/user preference + duplicate panel** | 4 scalar settings; dedicated XP panel uses text modals; participation/preference schema is separate per-user domain. | Keep scalar group; replace dedicated avoidable text inputs with shared structured editors or shared metadata-driven panel. Keep participation separate. |
| Economy | **Scalar + binding** | One channel-valued scalar plus matching `log_channel` binding/resource and command mutation route. | Resolve scalar-pointer vs binding duplication; prefer binding as long-term channel source, one structured UI. |
| Games hub | **None (router only)** | Explicitly zero game logic/config; children own config. | Exclude from Settings menu. |
| Blackjack | **Scalar** | Default entry fee, numeric presets. | Keep. |
| RPS tournament | **Scalar + runtime state** | Default entry fee scalar; active tournament is runtime state. | Keep scalar; never expose runtime state as setting. |
| Deathmatch | **Scalar** | Turn timeout, numeric presets. | Keep. |
| Mining | **None currently; active PR #624** | No schema/settings; gameplay constants and economy balancing are code/data. | Exclude now. Any future guild balance knobs require owner decision and must not be inferred during active lane. |
| Counting | **Implied/command config, no schema** | Command/channel activity behavior and documented skip-number idea; no central settings declaration. | Audit product intent before promotion; exclude until real configurable contract exists. |
| Chain | **Implied/command config, no schema** | Activity behavior; no central settings declaration. | Same as counting. |
| Roles | **Scalar + separate role domains + setup** | Two stacking booleans; thresholds/exemptions/reaction roles/default resources live elsewhere. | Keep scalar group plus navigation to role manager; do not force thresholds/exemptions into scalar KV. |
| Logging | **Scalar + bindings/provisioning + dedicated panel** | Two booleans; seven channel bindings; legacy mod/cleanup pointer fallback; presets/provisioning. | Keep one grouped Logging configuration page with scalar toggles and binding/provisioning navigation. |
| Moderation | **Scalar + setup + management panel** | 14 scalar policies, structured role/channel/enum/preset editors; setup stages a subset. | Keep; use as reference implementation for setup/settings convergence. Improve threshold numeric presets. |
| Cleanup | **Domain policy + command/panel, no scalar schema** | Governance cleanup policy tables, prohibited words, history, dedicated structured panel; Settings page is empty. | Include as a **domain configuration group** linked to canonical panel, not an empty scalar page. Governance setup section remains deferred/off-limits until scope decision. |
| Channels | **Management/provisioning, no settings** | Structured channel manager; setup binding/provisioning. | Exclude from scalar Settings; optionally expose a “Resources & bindings” configuration group if the product scope includes management navigation. |
| Help | **No guild scalar settings; visibility is governance-derived** | Router/read projection; visibility/access handled elsewhere. | Exclude. Never invent Help-local visibility settings. |
| Setup wizard/platform | **Orchestrator, not owner** | Draft/preview/apply across canonical services. | Exclude as a setting group; keep Setup shortcut and shared catalogue consumption. |
| Governance/subsystem visibility | **Separate domain config** | Canonical governance tables/writes/read resolvers; Access Explorer is partly read-only; setup governance section deferred. | Include only through a dedicated structured access/governance page. Do not map to scalar settings. |
| Command access/routing | **Separate domain config** | Settings hub already has structured command-access editor; setup routing drafts use separate service. | Keep top-level structured shortcut; consider catalogue registration as a domain group. |
| Server management | **Hub/orchestrator** | Setup/diagnostics/role templates; no scalar schema. | Exclude as a scalar group; link as a management destination where relevant. |
| Inventory | **None** | Gameplay/storage surface, no config schema. | Exclude. |
| Leaderboard | **None / XP-adjacent** | No config schema; visibility/preference belongs to other domains. | Exclude. |
| Proof channel | **Setup/binding candidate; command-managed** | Resource pointers documented for promotion but no schema. | Add binding/resource declarations before exposing. |
| Community / Community Spotlight | **No settings currently** | Community is hub; Spotlight registration is decided but not yet shipped *(shipped **#626** same day, post-audit)*. | Exclude until a real configuration contract exists; re-audit after registration lane. |
| Admin / General / Utility / Four-twenty / Diagnostic / Settings | **No configurable subsystem settings** | Commands, diagnostics, or front doors. | Exclude from subsystem Settings dropdown. Diagnostic/platform controls remain separate. |

## 5. Current settings map

The loaded source route declares **36 scalar settings across 9 settings-bearing subsystems**. Registry findings are clean: no missing keys, missing capabilities, duplicate qualified names, or duplicate keys.

| Group | Settings | Current editor |
|---|---|---|
| AI (10) | enabled, natural-language enabled, provider, model, minimum level, cooldown, fresh-user allowance, guild instruction body, memory window, memory channel scan | 3 toggles; provider select; 4 numeric-preset flows; model + instruction free text; seven guild-policy fields project to typed policy; memory remains scalar; instruction body is unprojected |
| Moderation (14) | warn threshold/timeout/action; DM behavior/template; reason requirement; ban purge days; max timeout; post-action cleanup/limit; public-log actions/channel; moderator/trusted role | 2 toggles; 3 enums; 3 native selectors; 3 numeric presets; 2 generic number modals; 1 text template |
| XP (4) | min, max, cooldown, announce channel | min/max generic number modals; cooldown presets; native channel selector |
| Logging (2) | enabled, auto-create channels | toggles |
| Role (2) | time stack, XP stack | toggles |
| Economy (1) | economy log channel | native channel selector; overlaps binding |
| Blackjack (1) | default entry fee | numeric presets |
| RPS tournament (1) | default entry fee | numeric presets |
| Deathmatch (1) | turn timeout | numeric presets |

Settings-adjacent but outside the scalar registry include bindings/resources, cleanup policies, subsystem visibility, command access/routing, role thresholds/exemptions, AI typed policy/orchestration, feature flags, participation/preferences, proof-channel pointers, and BTD6 pointers.

## 6. Settings UI display audit

| Question | Verified answer | Severity |
|---|---|---|
| Does the UI use the settings registry? | **Only for header count.** It does not use registry entries to choose dropdown groups. | **Critical blocker for desired display correctness** |
| Does it scan cogs? | No. It iterates static `SUBSYSTEMS`; schemas are consulted only to sort schema-bearing entries first. | Important |
| Does it use static lists? | Yes: `SUBSYSTEMS` is the identity manifest; first 25 candidates become Discord select options. | Important |
| Does it display cogs/subsystems without settings? | Yes, intentionally. Tests pin that behavior. Empty pages may still show commands or no-panel text. | **Critical UX defect** |
| Does it display bindings-only groups? | Yes if they are in the first 25; BTD6 has a schema/binding but no scalar setting. | Cleanup/owner-scope question |
| Does it hide disabled/gated/unavailable settings? | It gates the entire manager with `settings.manager_cog.enabled`, but does not filter groups/settings by feature availability, governance visibility, capability, or setup readiness. | Important |
| Does it respect permissions/capability/governance? | Mutation pipeline checks declared capability at write time. The hub and edit/reset controls remain visible; they do not pre-filter. Command-access callbacks separately re-check admin. | Important; callback enforcement is safe, discovery is noisy |
| Invalid / needs-setup handling? | Invalid scalar and missing-binding diagnostics exist; needs-setup lists declared required bindings/resources, not a per-actor/actionable group state. | Improvement |
| Can it stale after mutation/setup? | Scalar values refresh after edits and key cache is invalidated. Registry/schema discovery is frozen at startup and will not see dynamically registered/reloaded schemas until rebuilt. Domain-panel changes rely on their own refresh/invalidation. | Important |
| New-cog automatic support? | A new `SUBSYSTEMS` entry appears even with no schema; a new schema's scalar editors work automatically if registered before registry build. The 25-option cap can make entries unreachable. | **Critical discoverability defect** |

**Immediate target inclusion rule:** a Settings/configuration group should appear only if the catalogue declares at least one actor-visible actionable surface: editable scalar setting, binding editor, provisionable resource flow, or registered domain-policy panel. Router-only, read-only, internal, unavailable, and empty groups should not appear. Pagination/category selects must replace silent first-25 truncation.

## 7. Editability and no-text-entry audit

### Keep as-is

- Boolean `SettingSpec`s → immediate toggle.
- String settings with `allowed_values` → enum select.
- Channel/role hints → native Discord selectors with clear action.
- Numeric settings with curated presets → preset buttons plus an advanced custom override.
- Reset select → keep, but later distinguish “clear override/inherit” from “write explicit default.”
- Truly authored text: AI guild instructions, moderation DM template, model identifier when a provider catalogue cannot enumerate it.

### Avoidable text entry / conversion targets

| Current surface | Current mechanism | Target UX | Priority |
|---|---|---|---|
| XP min/max in generic Settings | Number modal | Curated numeric presets or a guided range editor validating min ≤ max | Important |
| XP dedicated config panel | Text modals for range, cooldown, channel | Reuse shared numeric presets and native channel selector | Important |
| Moderation warn threshold / timeout | Generic number modal | Numeric presets with advanced override | Improvement |
| AI default model | Free text | Provider-dependent model select where a safe catalogue exists; retain advanced custom text | Future / gated UI |
| AI guild instruction body | Text modal | Keep text, but move to typed instruction-profile flow if the hybrid AI ownership model is retained/reconciled | Critical architecture first |
| Moderation DM template | Text modal | Keep text; add preview/placeholders guidance | Improvement |
| BTD6 version announcement channel command | Typed/pasted command argument | Native binding/channel selector | Important |
| BTD6 CT group | Pasted group ID/URL command | Guided modal with parser + preview, or advanced-only command if intentionally operational | Owner decision |
| Economy log channel command | Command argument | Prefer one native selector/binding page; retain command only as documented shortcut if desired | Cleanup |
| Setup moderation role selection | Structured setup flow already exists | Keep; share declaration/navigation metadata | Keep |
| Cleanup/governance/access | Dedicated structured panels or setup flows | Keep separate service, register as discoverable domain editors | Keep / improve discovery |

The generic dispatcher has no native user/member selector or multi-select metadata in `SettingSpec`, despite the config-input standard naming those strategies. Add them only when a real setting requires them; bindings/policy domains may already own the better abstraction.

## 8. Centralization consistency gap analysis

| Severity | Gap / exception | Evidence and impact | Target |
|---|---|---|---|
| **Important** | AI uses a best-effort partial projection from legacy scalar writes to typed guild policy. | Seven keys project through `ai_policy_mutation`; memory remains scalar; instruction text is unprojected. Projection failure does not roll back the committed KV write. | Decide whether the hybrid is durable; surface projection/effective-source diagnostics and test failure/recovery behavior. |
| **Critical blocker** | Hub discovery lists all non-internal subsystems and silently truncates at 25. | Empty/non-configurable groups appear; some identities are unreachable. Tests currently pin this behavior. | Catalogue-driven actionable groups + pagination/category navigation. |
| **Important** | Registry is scalar-only and snapshots lossy string metadata. | It cannot drive typed editors, bindings, domain panels, actor filtering, groups, or setup reuse by itself. UI goes back to live schemas. | Evolve registry entries/catalogue metadata while keeping schema as declaration owner. |
| **Important** | Capability/governance is enforced on write but not reflected in discovery/editor availability. | Users can see controls that later reject; gated/unavailable systems appear. | Compute actor-aware availability/readiness and still re-check at callback. |
| **Important** | Channel-valued scalar settings overlap bindings. | Economy and legacy logging/XP pointer flows split source/read paths. | Finish binding promotion/arbitration; keep compatibility reads until migrated. |
| **Important** | Command-only BTD6 pointers bypass scalar audit/cache/events and UI. | Allowlisted direct writes are safe from accidental expansion but hidden/inconsistent. | Classify and promote to binding or declared advanced config. |
| **Important** | Reset writes an explicit default, does not clear an override, and is audited as `set_value`. | Effective value is correct, but inheritance/absence semantics, operator intent, and rollback are obscured. | Add metadata-supported “clear override/inherit” and a truthful reset audit action; retain explicit reset where required. |
| **Important** | Setup shares mutation services but not one declarative rendering catalogue. | Some settings are manually named/staged; drift is possible. | Setup and Settings consume shared definitions, with setup-specific grouping/compound plans. |
| **Important** | Direct scalar reads remain in compatibility/dedicated panels. | Server logging, XP config, readiness/preflight use raw reads for various reasons; provenance/validation can diverge. | Migrate user-facing effective reads to canonical resolver; document intentional raw reads for diff/backfill. |
| **Cleanup** | Dedicated XP/economy command surfaces duplicate generic Settings. | Safe writes, inconsistent/no-text UX. | Reuse shared editors or make commands shortcuts to canonical panels. |
| **Cleanup** | Docs overstate “all subsystems” as a menu expectation and contain historical milestone language. | Matches current implementation but conflicts with owner's desired only-real-settings UX. | Reconcile after owner confirms group scope. |
| **Future opportunity** | Automatic editor metadata lacks sections/order/dependencies/advanced visibility. | Flat edit select becomes unwieldy; conditional settings are not expressed. | Add group/order/visibility/editor metadata, not a second registry. |

### Principle-by-principle result

- **Central definition:** strong for declared scalar settings; incomplete across settings-adjacent domains.
- **Typed metadata/validation:** strong for scalar types and basic editor hints; weak for grouping, dependency/availability, and separate-domain discovery.
- **Permission/capability gate:** strong at scalar mutation; inconsistent at UI discovery and across domain panels.
- **Mutation/persistence/audit/cache:** strong for scalar pipeline; intentionally separate but unevenly discoverable elsewhere; allowlisted direct-KV exceptions remain.
- **UI rendering:** automatic for scalar editor shape; not automatic for group inclusion/domain panels; 25-item truncation is unsafe.
- **Setup compatibility:** correct service reuse where implemented; incomplete metadata reuse.
- **Docs/tests:** extensive and valuable, but some tests pin the undesired all-subsystems behavior and docs mix live/aspirational coverage.

## 9. Setup/platform/governance overlap audit

| Surface | Overlap / drift | Required posture |
|---|---|---|
| Settings cog vs setup wizard | Both can mutate moderation scalars; setup correctly stages and applies via scalar pipeline. Setup also owns compound changes. | Share definitions and validation; preserve direct-vs-draft lane based on change shape. |
| Operator presets vs live source | Preset docs describe many future settings/packs not represented by schemas or live editors. | Treat as reference; do not infer implementation coverage. Convert only approved presets into typed operations. |
| Settings vs management panels | Cleanup/logging/XP/AI/role/channel panels contain richer flows than generic Settings. | Settings should navigate to canonical domain panels or reuse common editors; avoid duplicate mutation logic. |
| Subsystem visibility/governance | Visibility is a separate policy domain; Settings has an Access Explorer but no full unified policy editor. | Register/navigation only; governance writes remain canonical. Deferred governance setup scope is off-limits. |
| Channel/role managers | Manage Discord objects and permissions, not scalar values. Setup uses provisioning/binding/role services. | Do not reclassify management actions as scalar settings. Surface contextual links. |
| Cleanup policies | Cleanup page in Settings is empty; real policies live in governance cleanup tables/panel/setup operation. | Make Cleanup a registered domain config group linked to the policy panel. |
| AI policy/tools/workflows | Generic scalar AI page, dedicated live AI policy UI, and orchestration UI overlap. | Treat the existing projection as a first-class compatibility seam; avoid adding more projected keys or UI until ownership is reviewed. AI UI changes require per-exposure gate lift. |
| Help menu visibility | Help is a projection of subsystem/governance/availability, not a settings owner. | No Help-local config; share access projection/catalogue. |
| Old slash/prefix commands | Economy/XP/BTD6 and various domain commands remain alternate mutation routes. | Keep only where they call canonical services and add unique operational value; otherwise redirect/deprecate after UI parity. |

## 10. Target architecture recommendation

### 10.1 One discovery surface, multiple mutation owners

Use the current `settings_registry` stack as the seed for a **Configuration Catalogue** projection, not a duplicate persistence/mutation system. `SubsystemSchema` remains the declaration owner. The catalogue should compose:

- scalar `SettingSpec`s;
- binding/resource declarations;
- explicitly registered domain-panel destinations (cleanup, command access, AI policy, role thresholds, etc.);
- availability/readiness/capability metadata;
- setup compatibility and direct-vs-draft lane metadata.

The Settings Manager consumes this catalogue for group inclusion and rendering. Every edit still dispatches to the domain's canonical mutation owner.

### 10.2 Repeatable declaration pattern for new cogs

A new subsystem should:

1. register identity/capabilities in the subsystem registry;
2. declare only real configurable scalar settings in `cogs/<subsystem>/schemas.py`, with canonical key, type, default, validator, capability, editor hint, group/order, and optional availability rule;
3. declare bindings/resources in the same schema;
4. register any separate canonical config panel/service as a catalogue destination rather than pretending it is scalar;
5. register schemas in `cog_load()` before registry build;
6. add resolver/mutation/audit/editor/setup/docs/tests as applicable;
7. appear in Settings only when at least one actionable declaration exists.

Router/hub/read-only cogs should declare no settings and should not appear.

### 10.3 Grouping and editor selection

Extend metadata conservatively with fields such as `section`, `order`, `editor_kind`, `advanced`, `depends_on`, `availability_provider`, and `reset_semantics`. Derive editor automatically:

- bool → toggle;
- allowed values → select;
- numeric presets → buttons/select + advanced custom;
- channel/role/user/member → native Discord selectors;
- collections → multi-select where bounded;
- compound/cross-domain → guided setup flow;
- free-form authored content → text modal;
- separate domain → canonical panel link.

### 10.4 Defaults, reset, rollback

- Keep declared defaults in one definition.
- Distinguish **reset to explicit default** from **clear override / inherit**.
- Continue recording before/after raw values, action, actor, and mutation ID.
- Use audit history to offer a future “revert to previous valid value” flow through the same mutation service; never directly replay DB rows.
- Setup rollback remains operation/domain-aware; do not promise atomic rollback across Discord side effects without a dedicated design.

### 10.5 Setup convergence

Settings and Setup should share definitions, validation, editor hints, and effective-value rendering. Settings remains suitable for focused reversible direct edits; Setup remains suitable for compound/generated/high-risk changes with draft, preview, confirmation, and apply. A common catalogue should tell each surface what exists; it should not erase their different workflows.

## 11. Phased implementation roadmap

> **Phases 0+1 shipped 2026-06-09 in PR #640** (execution-plan Lane 7): the hub's
> discovery rule is `services/customization_catalogue.actionable_settings_groups()`
> (the §6 inclusion rule — editable scalar / binding / resource / declared domain
> panel; live taxonomy = **11 groups**, exactly §4/§5), with select pagination past
> the 25-option cap and per-guild routing availability markers. Domain-config
> inclusion is the declared `DOMAIN_CONFIG_SUBSYSTEMS = {"cleanup"}` table — a
> Phase 1 seam that **Phase 2 replaces with real registrations**. Phases 2/3
> directions are decided (Q-0063 converge-gradually · Q-0064 binding+guided flow).

| Phase | Goal / expected files | Dependencies and blocked/off-limits scope | Risk | Verification | Recommended next agent |
|---|---|---|---|---|---|
| **0 — reconciliation and test targets** | Confirm owner answers; document live group taxonomy; add failing/target tests for actionable-only discovery, no truncation, AI source alignment. Expected: this plan, router, `tests/unit/views/test_settings_hub_view.py`, registry/catalogue tests. | Review the existing partial-projection contract; no runtime behavior change yet. | Low | Docs strict; source inventory script; target-test review. | **Opus planning/revision**, then GPT/manual review |
| **1 — discovery/display correctness** | Replace all-`SUBSYSTEMS` dropdown with catalogue/actionable groups; add pagination/categories; actor-aware availability labels; preserve callback re-check. Expected: `settings_registry` or `customization_catalogue`, `views/settings/hub.py`, subsystem view, tests. | Do not absorb domain mutation services. Governance setup section remains deferred. | Medium | Hub tests for empty exclusion, >25 reachability, unavailable/gated/capability cases, reload behavior. | **Sonnet implementation** |
| **2 — complete declaration/coverage map** | Add missing schemas/bindings/domain-panel registrations only for verified real config; classify BTD6/proof/logging/economy pointer migrations; remove dead key presentation. | Mining active lane; no speculative mining settings. AI policy UI remains gated. | Medium/high by subsystem | Registry findings, reserved-key/direct-write invariants, per-subsystem tests, manual inventory diff. | **Codex mapping** per subsystem + **Sonnet implementation** |
| **3 — eliminate duplicate/hardcoded/command-only paths** | Harden or simplify AI projection; migrate safe direct/duplicate routes; make old commands call/redirect to canonical owners; converge effective reads. Expected: AI policy stack, BTD6 services/bindings, XP/economy panels, server logging adapters, invariants. | Any AI UI change requires Q-0063 and a gate lift for exposure. Preserve runtime state exceptions. | High | Mutation/audit/cache tests; behavior parity; no-direct-write invariant shrinks; live smoke for affected commands. | **Opus revision** for AI; **Sonnet implementation** |
| **4 — structured editors / less text** | Add group/order/advanced/reset metadata; XP guided range; numeric presets; model selector where safe; user/member/multi-select only for real needs. **Owner posture Q-0070 (2026-06-10):** wherever feasible every editor offers defined presets + preset-then-edit + always-available manual entry — upgrades §7's "keep as plain text" rows (templates/instruction bodies get curated starting presets, not blank modals). | Do not add AI UI without gate lift. Discord component limits. | Medium | Editor dispatch, validation, callback authority, no-text UX tests/manual smoke. | **Sonnet implementation** + GPT/manual UX review |
| **5 — Setup/Settings convergence** | Shared catalogue/definition projection; Setup consumes definitions and effective renderers; domain panels registered; preserve draft/direct lane. | Governance setup scope deferred; provisioning confirmation contract immutable. | High | Setup draft/preflight/apply parity, domain-service dispatch tests, audit checks, manual compound-flow smoke. | **Opus planning/revision**, then **Sonnet implementation** |
| **6 — docs/current-state/test hardening** | Reconcile command map/presets/current-state; remove stale milestone claims; add architecture/invariant tests and operator smoke checklist. | Update `current-state` only for shipped truth. | Low | `check_docs --strict`, full relevant tests, architecture/quality gates, live menu walkthrough. | **Codex mapping** + GPT/manual review |

## 12. Open questions / owner decisions

Two decisions are routed as Q-0063 and Q-0064 in `docs/owner/maintainer-question-router.md`:

1. **AI hybrid ownership:** should the existing seven-key scalar-to-policy projection remain the durable contract, or should AI converge on typed policy panels while memory remains a separate scalar family?
2. **BTD6 operator pointers:** should version-announcement channel and CT team group become first-class discoverable configuration, and if so which domain owns each?

Safe defaults until answered: preserve the existing tested seven-key projection, do not add more projected keys or AI UI, and label the hybrid seam in implementation planning; keep BTD6 typed services/commands unchanged; exclude empty groups from the target design while preserving domain panel navigation.

## 13. Verification plan

### Completed in this mapping session

- Verified every required reading/source path exists (except CodeGraph service availability; no MCP resources/templates were exposed).
- Queried live GitHub open PRs and inspected #624's file list.
- Ran `scripts/context_map.py` with available `python` for every deeply inspected `disbot/*.py` file after the requested `python3.10` executable proved unavailable.
- Imported and registered all ten schema modules in an isolated process: 36 scalar settings across 10 schemas, clean registry findings.
- Enumerated all 28 `SUBSYSTEMS` entries and verified the hub's 25-option cap/all-subsystems inclusion behavior from source and tests.
- Traced direct `get_setting`/`set_setting` callers and the AST allowlist.

### Required before and during implementation

1. Re-run live PR/gate check, especially AI UI, adaptive setup/governance, mining, and Community Spotlight registration.
2. Add a machine-readable inventory test asserting every actionable group has a destination and every shown group has a real action.
3. Add hub tests proving zero empty groups and reachability beyond 25.
4. Add an AI end-to-end test proving an edit changes the live resolver's effective decision before exposing it.
5. Add direct-write audit tests as allowlist entries are removed.
6. Run targeted settings/setup/governance tests, then `python scripts/check_docs.py --strict`, architecture checks, and full quality suite for runtime phases.
7. Perform a live Discord walkthrough for Settings → each group → edit/reset/inherit → audit → Setup parity.

## 14. Recommended next session

**Next: Opus planning/revision for Phase 0, focused on the actionable-group catalogue contract and review of the AI partial-projection seam.** It should consume this audit plus owner answers Q-0063/Q-0064, produce a reviewed data model and exact target tests, and explicitly preserve the separate mutation-domain boundaries. After that review, a Sonnet implementation session can safely execute Phase 1 discovery/display correctness without touching live mutation semantics.
