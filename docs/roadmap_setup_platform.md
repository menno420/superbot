# SuperBot — Setup + Configuration Wizard Platform Roadmap

## Context

SuperBot has just completed a major stabilization run: a centralized message pipeline (`disbot/core/runtime/message_pipeline.py`), the `GovernanceMutationPipeline` orchestrator (`disbot/governance/writes.py`), a 5-surface identity contract validator (`disbot/utils/subsystem_registry.py:validate_identity_contract`), a unified guild resource resolver (`disbot/core/runtime/guild_resources.py`), version-stamped guild config caching (`disbot/core/runtime/guild_config.py`) with typed accessors (`disbot/utils/guild_config_accessors.py`), a diagnostics provider registry (`disbot/services/diagnostics_service.py`), 14 enforced runtime invariants, and 20 subsystems with rich metadata. The platform is in shape; what is missing is the **declarative layer that lets subsystems be configured at runtime**.

Today, guild operators have no coherent way to set up a subsystem. Channel/role IDs are stored as raw strings in `guild_settings` KV; the `has_onboarding` flag in `SUBSYSTEMS` is declared but unconsumed; `disbot/utils/onboarding_profiles.py` is dead code with one stub entry; there is no setup command, no completeness check, no preview-before-apply, no preset system. A naïve fix would be to ship a "settings cog" that reads each subsystem's config directly. That is the wrong shape: it would inflate one cog with knowledge of every subsystem, bypass `GovernanceMutationPipeline` (INV-E), and add a configuration surface that future subsystems would have to manually integrate into.

The right shape is to make the wizard **a platform layer**, not a feature. Subsystems declare their configuration schema; the platform reads it; the wizard renders against the schema with zero per-subsystem UI code. Drafts, previews, bindings, diagnostics, and templates become platform primitives that any future subsystem (moderation auto-rules, AI tooling, tournament configurator, cross-guild presets) can opt into by declaring a schema — without writing a single line of wizard code.

This roadmap sequences that transition phase-by-phase, **inside-out**: ownership protocols and binding storage first, draft/preview primitives next, diagnostics in parallel, declarative UI fifth, identity-contract guardrail sixth, the wizard cog seventh, and extensibility validation eighth. Each phase is independently shippable with CI-visible exit criteria. The end state is a wizard that is one of the **central governing platform layers** of SuperBot — peer to the governance, message pipeline, and identity systems — not a feature attached to the side.

### Expanded Direction (Refinement Pass)

The original roadmap framed the wizard as **guild configuration infrastructure**. After further architectural work it must be reframed as a **full participation + platform runtime layer**. Three first-class concerns now sit inside the same effort:

1. **Dual-scope state.** The platform must serve a 3-tier hierarchy — `Global Defaults → Guild Configuration → Per-User Guild Participation State` — not a single "settings" layer. Guild config and per-user participation are *separate runtimes* with separate persistence, caching, ownership boundaries, and diagnostics. They share schema primitives but never share storage or mutation pipelines.
2. **Unified Guild Resources.** Today's channel system (`disbot/cogs/channel_cog.py` + `disbot/views/channels/`, ~1500 LOC) and role system (`disbot/cogs/role_cog.py` + `disbot/views/roles/`, ~1500 LOC) are early provisioning groundwork. They must generalize into a `core/resources/` runtime over `GuildResource` / `ChannelResource` / `RoleResource` / `CategoryResource` / `ThreadResource` — a single resource taxonomy that bindings, selectors, provisioning, diagnostics, repair, and discovery all share. **This runtime is foundational** — bindings, participation, governance role-mapping, and diagnostics all consume it, so it must complete before any of them.
3. **Platform Navigation Framework.** The help menu (`disbot/cogs/help_cog.py`, 506 LOC), setup panels, dashboards, and selector widgets are presently three nascent UI tracks. They must converge into a single navigation framework with shared component registries — no separate help/setup/dashboard systems. The wizard's `Screen` primitive becomes the engine for all platform-level UI.

The long-term direction this serves: SuperBot is evolving from **a traditional Discord bot** toward a **Guild Operating System** — a runtime that hosts subsystems, manages their per-guild and per-user lifecycle, routes notifications, provisions resources, validates state, and surfaces an integrated control plane. Every architectural choice in this roadmap is sequenced toward that direction. The wizard is the inhabited surface of that OS; the platform layers built underneath it are what make the surface possible.

### Inside-Out Implementation Strategy (Hard Constraint)

The strongest discipline in this roadmap is **inside-out**: foundational runtime primitives complete before higher-level surfaces depend on them. The implementation order MUST follow this tier sequence; any phase that breaks it is a re-design, not a re-order.

```
Tier 1: Foundational Runtime Primitives        (P0, P1, P2)
   ↓
Tier 2: Governance + Resource Infrastructure   (P1d, P2a, P2d, P4.5)
   ↓
Tier 3: Typed Runtime State + Participation    (P2b, P2c, P3)
   ↓
Tier 4: Diagnostics + Routing + Policies       (P4, P6, P6.5)
   ↓
Tier 5: Platform UI Framework                  (P5a, P5b, P5c)
   ↓
Tier 6: Inhabited Surfaces                     (P7: Wizard / Dashboard / Participation Hub)
   ↓
Tier 7: Provisioning + Cross-Guild + OS        (P7.5, P8)
```

UI surfaces (P5c, P7, P7.5) are the **last consumers**, never early architectural drivers. The Component Registry (P5b) lands **before** any wizard surface so wizard code composes primitives instead of inventing them. The Resource Runtime (P2a — moved earlier than the original ordering had it) lands **before** bindings, participation, diagnostics, provisioning, or governance role-mapping because all of them depend on it.

---

## Executive Summary

- **What it is.** A schema-driven **dual-scope** runtime that subsumes onboarding, channel/role binding, diagnostics, presets, participation, subscription, notification routing, and resource provisioning into a single platform layer. Surfaces guild operator UX (Setup Wizard) and per-user UX (Participation Hub) over shared primitives.
- **What stays.** Every existing platform primitive — message pipeline, governance pipeline, identity contract, guild_config cache, session manager, diagnostics, persistent views, navigation stack, scope locks, services layer. The wizard composes them; it does not duplicate them.
- **What's new (foundation tier).** Subsystem-owned schemas split across **two ownership protocols** (Phase 1): guild config schemas + user participation schemas. Typed bindings + per-user participation state + unified resource taxonomy (Phase 2). `ConfigDraft` primitive over `runtime_session_state` (Phase 3). Setup + participation + resource diagnostics (Phase 4).
- **What's new (UI tier).** Platform Navigation Framework with shared component registry that subsumes help/setup/dashboard (Phase 5). `NotificationIntent` + `VisibilityIntent` routing service with central suppression and digest (Phase 6.5).
- **What's new (surface tier).** Identity contract 6th surface (Phase 6), the `!setup` cog with Experience Modes (Phase 7), Resource Provisioning Runtime for auto-generated channels and setup packs (Phase 7.5), and extensibility hooks toward the Guild Operating System direction (Phase 8).
- **Critical architectural choice.** The wizard **never mutates state directly**. Every commit flows through `GovernanceMutationPipeline`, the new `BindingMutationPipeline`, or the new `ParticipationMutationPipeline` — all shaped identically. Enforced by AST invariant in Phase 3.
- **Critical ownership choice.** Subsystems own their schemas (both config and participation). The wizard reads schemas; it never writes them. Identity contract in Phase 6 enforces this.
- **Critical scope choice.** Guild config and per-user participation are **never combined** into one settings object. Same goes for participation, permissions, visibility, notifications, preferences — these are separate runtimes that share schema primitives but have distinct storage, caching, and pipelines.

---

## Core Platform Runtime Boundaries

The roadmap formalizes the following platform runtime domains. Each domain has a single owner package, a clear mutation authority, a clear cache authority, and a clear event authority. Cross-domain access is read-only via documented helpers; cross-domain writes flow through domain-owned mutation pipelines.

| Domain | Package | Mutation authority | Cache authority | Event authority | Phase introduced |
|---|---|---|---|---|---|
| **Resources** (channels, roles, categories, threads as first-class) | `core/resources/` | `ResourceMutationPipeline` | `resource_validation_cache` | `EVT_RESOURCE_*` | P2a (moved earlier) |
| **Bindings** (subsystem → resource intent) | `core/runtime/bindings.py` | `BindingMutationPipeline` | `guild_config` (binding namespace) | `EVT_BINDING_*` | P2b |
| **Participation** (per-user opt-in, subscriptions, preferences, visibility) | `core/runtime/participation_state.py` | `ParticipationMutationPipeline` | `user_config` (sibling cache) | `EVT_PARTICIPATION_*`, `EVT_SUBSCRIPTION_*`, `EVT_USER_PREFERENCE_*`, `EVT_USER_VISIBILITY_*` | P2c |
| **Governance** (visibility, cleanup, capabilities, role-tier mapping, access control) | `governance/` (existing) | `GovernanceMutationPipeline` | `governance/cache.py` | `EVT_VISIBILITY_CHANGED`, `EVT_CLEANUP_CHANGED`, `EVT_CACHE_INVALIDATED` | P4.5 formalization |
| **Feature Flags / Environments / Rollout** | `core/runtime/feature_flags.py` | `RolloutMutationPipeline` | `feature_flag_cache` | `EVT_FEATURE_FLAG_CHANGED`, `EVT_ROLLOUT_ADVANCED` | P2d (NEW) |
| **Configuration (typed)** | `utils/guild_config_accessors.py` + `utils/user_config_accessors.py` | (none — read-only views over the above) | inherits `guild_config` / `user_config` | (none — passthrough) | P0 + P2 |
| **Notifications / Visibility** | `core/runtime/notification_router.py` + `core/runtime/visibility_filter.py` | `notification_service.notify` | (none — stateless router) | `EVT_NOTIFICATION_*`, `EVT_VISIBILITY_FILTERED` | P6.5 |
| **Diagnostics** | `services/diagnostics_service.py` + `services/*_health_service.py` | (none — read-only providers) | (none — on-demand snapshots) | (none — observation only) | P4 |
| **Drafts / Sessions** | `core/runtime/config_drafts.py` over `core/runtime/session_manager.py` | `ConfigDraft.commit` (delegates to per-domain pipelines) | inherits `runtime_session_state` | inherits domain events | P3 |
| **UI Framework** | `core/runtime/screens.py` + `core/runtime/components/` + `core/runtime/screen_navigator.py` | (none — UI is stateless) | (none — UI is stateless) | (none) | P5 |

**Ownership rules (binding):**
1. A domain's data is mutated **only** through its mutation pipeline. Direct DB writes from any other domain or from cogs are forbidden (AST-enforced).
2. A domain's cache is invalidated **only** by its own pipeline. Other domains read; they never invalidate.
3. A domain's events are emitted **only** by its own pipeline. Cogs may listen, but never emit a domain event directly.
4. UI never holds runtime state. UI reads from domain accessors; UI writes go through `ConfigDraft.commit`, which dispatches to the right mutation pipeline.
5. New domains require an ADR (`docs/decisions/`) and an update to this table. The table is the canonical contract.

This taxonomy converges on a `core/` directory structure that, by end-of-Phase-7.5, looks like:

```
disbot/core/
  config/           — typed accessors (existing, extended in P2)
  resources/        — unified resource runtime (P2a, NEW)
  runtime/          — sessions, drafts, navigation, scope locks (existing + extended)
    bindings.py     — guild bindings (P2b)
    participation_state.py — per-user state (P2c)
    feature_flags.py — environments + rollout (P2d)
    notification_router.py + suppression + digest + visibility_filter (P6.5)
    components/     — UI primitives (P5b)
    screens.py + screen_navigator.py (P5a)
  events.py         — EventBus (existing)
  events_catalogue.py — KNOWN_EVENTS (existing, extended)
governance/         — policy engine + role templates + permission tiers (existing + P4.5)
services/           — audited cross-subsystem mutations (existing + new health/notification/notification services)
```

---

## Phase Dependency Graph

The refined roadmap is organized into **seven tiers**, executed inside-out. Each tier completes before the next consumes its primitives. Within a tier, sub-phases parallelize.

```
═══ Tier 1 — Foundational Runtime ═════════════════════════════════════════
  P0   Pre-flight Refactor (settings_keys, accessors, dead-code removal,
       resource helper extraction)
   │
   ▼
  P1   Ownership Protocols (schema declarations, no runtime yet)
       ├─ P1a Guild Config Schemas
       ├─ P1b Participation Schemas
       ├─ P1c Resource Capability Declarations
       └─ P1d Governance / Rollout Schemas (PlatformRole, PermissionTier,
              FeatureFlag, EnvironmentTier, RolloutPolicy, RoleTemplate) ← NEW
   │
   ▼
═══ Tier 2 — Resource + Governance Substrate ══════════════════════════════
  P2   Typed State Storage (REORDERED — resources are foundational)
       ├─ P2a Unified Resource Runtime (core/resources/)            ← MOVED EARLIER
       │       Required by: bindings, participation, diagnostics,
       │       governance role-mapping, provisioning.
       ├─ P2b Guild Bindings (subsystem_bindings, consumes P2a)
       ├─ P2c Per-User Participation State (4 sibling tables)
       └─ P2d Feature Flags + Environment Tiers + Rollout Policy    ← NEW
               (feature_flags, environment_tiers, rollout_state)
   │
   ▼
═══ Tier 3 — Cross-cutting Primitives ═════════════════════════════════════
  P3   Draft / Preview / Commit Session Pattern  (single primitive, used by
       guild config, participation, resource provisioning, governance)
   │
   ▼
═══ Tier 4 — Diagnostics + Governance + Routing ═══════════════════════════
  P4   Diagnostics + Health (parallel to P3)
       ├─ P4a Setup Health
       ├─ P4b Participation Health
       └─ P4c Resource Diagnostics
   │
   ▼
  P4.5 Governance / Access Control Runtime    ← NEW
       (Role templates, permission tiers, governance role provisioning,
        smart role detection, recommended mappings, permission diagnostics,
        delegated administration, subsystem ownership scopes)
   │
   ▼
  P6   Identity Contract 6th Surface (formalize schema-registry as a
       surface; lands after foundations stabilize)
   │
   ▼
  P6.5 Notification + Visibility Intent Routing
       (notification_router, suppression, digest, visibility_filter)
   │
   ▼
═══ Tier 5 — Platform UI Framework ════════════════════════════════════════
  P5   Platform Navigation Framework
       ├─ P5a Screen Primitive
       ├─ P5b Component Registry (selectors, panels, toggles, progress)
       └─ P5c Help / Setup / Dashboard / Diagnostics / Governance
              UI unification
   │
   ▼
═══ Tier 6 — Inhabited Surfaces ═══════════════════════════════════════════
  P7   Setup Wizard + Participation Hub + Experience Modes
       (operator surface !setup, user surface /myprofile, Minimal /
        Recommended / Full / Custom modes)
   │
   ▼
═══ Tier 7 — Provisioning + Extensibility ═════════════════════════════════
  P7.5 Resource Provisioning Runtime
       (setup packs, repair flows, regeneration, environment-aware
        provisioning, role provisioning integration with P4.5)
   │
   ▼
  P8   Cross-guild + AI/Automation + Domain Event Reservation +
       Guild OS direction
```

User-visible deliverables: **P4** (diagnostics), **P4.5** (role provisioning admin commands), **P7** (setup + participation), and **P7.5** (provisioning). All other phases are platform foundation.

**Sequencing notes (binding).**
- The P2 sub-phase reorder (resources → bindings → participation → feature flags) reflects dependency reality. Bindings reference resources; participation references bindings (for guild-scope) and subscriptions (which reference resources via notification routing); feature flags gate everything from Tier 4 onward.
- P4.5 lands **between diagnostics and routing** because it requires diagnostics to be observable (P4) but routing (P6.5) depends on it for "which roles can suppress notifications for a guild" type queries.
- P5 (UI framework) cannot start before P4.5 because the component registry's `RoleSelector` and `PermissionPicker` need the governance taxonomy to be real.
- P7 cannot start before P5 — the wizard is a UI surface, and UI surfaces consume the framework.
- P7.5 lands after P7 because resource provisioning is exposed through wizard flows; the runtime is reusable, but its first inhabited surface is the wizard.

**Track ownership.** Three logical tracks weave through these tiers:
- **Track A — Guild Configuration Runtime** extends existing governance/settings primitives. Lives in P1a/P2b.
- **Track B — User Participation Runtime** is genuinely new. Lives in P1b/P2c/P4b/P6.5/P7.
- **Track C — Unified Resource Infrastructure** generalizes ~3000 LOC of existing channel/role infrastructure. Lives in P1c/P2a/P4c/P7.5.
- All three tracks share P0, P3, P4.5, P5, and converge fully at P7.

---

## Phase 0 — Pre-flight Refactor Cut-line

**Objective.** Normalize the three pre-existing structural mismatches that would otherwise inflate Phase 1.

**Architectural purpose.** Every later phase reads from or extends `subsystem_registry.py`, `settings_keys.py`, and `guild_config_accessors.py`. If these are still in their current shape when Phase 1 lands, Phase 1 will either bloat them past their natural responsibility or create a parallel structure that fragments ownership.

**Refactors (no behavior change):**
- **`disbot/utils/settings_keys.py`** → split into `disbot/utils/settings_keys/` package with per-subsystem modules (`xp.py`, `economy.py`, `moderation.py`, `governance.py`, …) and a `__init__.py` re-exporting for back-compat. Add a new AST invariant test in `tests/unit/invariants/` blocking new imports from the flat path (same shape as INV-F).
- **`disbot/utils/guild_config_accessors.py`** → extract a `TypedAccessor[T]` helper encapsulating the loader + invalidator + key + dataclass pattern. The existing AST invariant `test_guild_config_typed_accessors.py` stays intact. The same helper will be reused by Phase 2b for per-user participation accessors and Phase 2c for resource accessors.
- **`disbot/utils/onboarding_profiles.py`** → delete (dead code, no consumers). Remove `has_onboarding` field from `SUBSYSTEMS` entries in the same PR. The flag returns in Phase 1 as a derived property: "subsystem has registered schema → has onboarding."
- **Resource helper extraction** (NEW, prep for Track C): pull `_build_channel_options` from `disbot/views/channels/_helpers.py` and `_find_role_normalized` from `disbot/views/roles/_helpers.py` into a new shared `disbot/views/selectors/_resource_helpers.py`. No behavior change; sets the stage for Phase 2c generalization. Existing call-sites updated to import from the new location. The current `views/selectors/channel.py` and `views/selectors/role.py` already exist and stay as the high-level component surface.

**Dependencies.** None.

**Migration impact.** Zero DB migrations. Identity surfaces unchanged. Settings KV unchanged.

**Risks & mitigations.**
- Import-path cascade across ~30 callsites → mitigated by back-compat re-exports from the new `__init__.py`.
- Deleting `onboarding_profiles.py` strands the `has_onboarding` flag → bundle deletion with field removal in the same PR.

**Entry criteria.** `main` is green.
**Exit criteria.** All tests pass; new AST invariant blocks regressions; no production caller imports from legacy flat `settings_keys` paths.

**User value.** None (foundation).

---

## Phase 1 — Subsystem-owned Ownership Protocols

**Objective.** Subsystems declare three kinds of shape — guild config, user participation, and required resources — and the platform reads them. Ownership flows from cog → platform, never the reverse.

**Architectural purpose.** Without this phase, the wizard becomes a god-object that knows every subsystem's config, every subsystem's participation rules, and every subsystem's resource requirements. With it, every later phase (bindings, participation state, resources, diagnostics, wizard, templates, routing) iterates over typed declarations without coupling to specific cogs. **This is the most load-bearing phase in the roadmap.** It is now structured into three sibling sub-phases that share the same registry + decorator infrastructure.

---

### Phase 1a — Guild Configuration Schema Protocol

**Systems introduced.**
- `disbot/core/runtime/subsystem_schema.py` — `SubsystemSchema` dataclass:
  - `subsystem: str` (matches registry key)
  - `bindings: list[BindingSpec]` — name, kind (`channel | role | member | category | thread`), required, hint, `capability_required`
  - `settings: list[SettingSpec]` — name, type, default, validator, `capability_required`, linked `settings_key`
  - `version: int` — schema version for migration support
  - `completeness_rule: Callable[[guild_id], CompletenessReport]`
- `disbot/core/runtime/subsystem_capabilities.py` — `@capability("subsystem.resource.action")` decorator that (a) verifies the capability is declared in the registry, (b) registers a reverse map for diagnostics. Replaces the current pattern where capabilities live only as strings.
- `SubsystemSchemaRegistry` — name-keyed registry, same shape as `diagnostics_service._PROVIDERS` and `persistent_views._REGISTRY`. Each cog registers in `cog_load`.

### Phase 1b — User Participation Schema Protocol (NEW)

**Systems introduced.**
- `disbot/core/runtime/participation_schema.py` — `ParticipationSchema` dataclass declaring per-user shape the subsystem supports:
  - `subsystem: str`
  - `subscriptions: list[SubscriptionSpec]` — name (e.g. `"xp"`, `"xp.levelup_notifications"`), `default_enabled: bool`, `eligibility_rule: Callable[[member], bool] | None`, `requires_optin: bool`, capability required to toggle
  - `visibility_intents: list[VisibilityIntent]` — `"tournaments.feed"`, `"xp.leaderboard.public"` — what surfaces this subsystem can show or hide per-user
  - `notification_intents: list[NotificationIntent]` — `"xp.levelup"`, `"economy.daily.reminder"` — what kinds of messages this subsystem can send per-user
  - `preference_specs: list[PreferenceSpec]` — UI/UX prefs (digest frequency, embed style, language hints)
  - `version: int`
- **Decoupling rule** (enforced in code review + docstring contract): a `ParticipationSchema` MUST split `subscription`, `visibility`, `notification`, and `preference` into separate field lists. Cogs MUST NOT collapse these into a single "user settings" object.
- `ParticipationSchemaRegistry` — name-keyed; mirrors `SubsystemSchemaRegistry`.
- `disbot/core/runtime/participation_capabilities.py` — `@user_capability("subsystem.user.toggle_xp")` decorator for per-user mutations (separate capability namespace from guild-level governance capabilities).

**Why this is separated from 1a.** Guild config is **operator state** mutated by moderators+ via `GovernanceMutationPipeline`. Participation is **user state** mutated by the user themselves via the new `ParticipationMutationPipeline` (Phase 2b). They have different authority models, different audit semantics, different cache lifecycles. Mixing them would re-introduce the god-object trap at a different layer.

### Phase 1c — Resource Capability Declarations (NEW)

**Systems introduced.**
- `disbot/core/runtime/resource_specs.py` — `ResourceRequirement` dataclass declaring what platform resources a subsystem needs at runtime:
  - `kind: ResourceKind` (`CHANNEL | ROLE | CATEGORY | THREAD`)
  - `intent: str` — what the subsystem uses the resource for (`"log_destination"`, `"announcement_target"`, `"role_threshold_anchor"`)
  - `provisioning: ProvisioningHint` — `recommended | required | optional` + suggested name/category/permissions (for Phase 7.5 auto-provisioning)
  - `binding_name: str` — links to a `BindingSpec` in the 1a schema (so resources and bindings are not double-declared)
- Extension to `SubsystemSchema` from 1a: optional `resource_requirements: list[ResourceRequirement]`. Most subsystems will declare resources here; the field is structurally part of the guild config schema but conceptually owned by Track C.

**Why this is separated from 1a.** Resources are the **platform substrate** subsystems run on; bindings are **named slots** the operator fills. The same `mod-logs` channel might satisfy multiple subsystems' `log_destination` requirements; resource declarations let the Phase 4c diagnostics surface "this channel is referenced by 3 subsystems" and let Phase 7.5 auto-provisioning decide "should we create one channel per subsystem or one shared channel?"

### Phase 1d — Governance & Rollout Schemas (NEW)

**Systems introduced.**
- `disbot/governance/role_templates.py` — `RoleTemplate` and `RoleCollection` declarations. A `RoleTemplate` describes a recommended governance role (`name`, `permissions`, `color`, `mentionable`, `governance_scope`, `permission_tier`, `provisioning_hint`). `RoleCollection` groups templates into bundles (e.g. `MODERATION_ROLES`, `TRUSTED_USER_TIERS`).
- `disbot/governance/permission_tiers.py` — `PermissionTier` enum + metadata extending the existing `visibility_tier` strings. Adds explicit `tier_index`, `inherits_from`, `description`, and `recommended_roles`. Backward-compatible with current `visibility_tier` strings.
- `disbot/governance/scopes.py` — formalize `GovernanceScope` as a typed enum (`GUILD | CATEGORY | CHANNEL | THREAD | ROLE | USER`). The existing scope strings in `governance/writes.py:_VALID_SCOPE_TYPES` become aliases for this enum.
- `disbot/core/runtime/feature_flags.py` — `FeatureFlag`, `EnvironmentTier`, `RolloutPolicy` dataclasses:
  - `EnvironmentTier`: `DEVELOPMENT | CANARY | BETA | PRODUCTION | OWNER_GUILD_ONLY`
  - `FeatureFlag`: `name`, `description`, `default_value`, `environment_overrides: dict[EnvironmentTier, bool]`, `rollout_policy: RolloutPolicy | None`
  - `RolloutPolicy`: `staged_guilds: list[int]`, `percentage_rollout: int`, `tier_gate: EnvironmentTier`
- `FeatureFlagRegistry` — name-keyed registry; subsystems declare flags in `cog_load`.

**Why a separate sub-phase.** These are **declarations** (schema-level) the way 1a/1b/1c are declarations — they describe shape, not runtime. The runtime that consumes them lands in P2d (state storage) and P4.5 (governance runtime services). Splitting declaration from runtime keeps the schema invariant validators uniform across all four sub-phases.

**Why governance/rollout is its own sub-phase rather than absorbed into 1a.** Guild config schemas describe **operator-settable values**; governance schemas describe **platform-administrative shape** (who can do what, where, under which environment, at which rollout stage). Conflating them would re-introduce the god-object trap: a subsystem's `SubsystemSchema` would balloon to include both "what an operator can configure" and "what permission tier can configure it" — which are different ownership concerns (subsystem owner vs. platform owner).

**Existing primitives reused / extended.**
- `disbot/utils/visibility_rules.py:get_member_visibility_tier` — extended in P4.5 to consume `PermissionTier`; backward-compat shim retained for one release.
- `disbot/governance/templates.py` — reused as the template payload carrier; `RoleTemplate` becomes a new payload kind.

**Existing primitives reused / extended.**
- `disbot/utils/subsystem_registry.py:SUBSYSTEMS` — stays as platform metadata. All three schema kinds are sibling structures, not replacements.
- `disbot/services/diagnostics_service.py` — three registries self-register snapshot providers (`!platform schemas`, `!platform participation-schemas`, `!platform resource-requirements`).
- `disbot/core/runtime/persistent_views.py:register` — pattern template for all three registries.

**Dependencies.** Phase 0.

**Migration impact.** No DB migrations. No new identity surface yet (waits for Phase 6, intentionally). Settings KV untouched.

**Risks & mitigations.**
- Schemas drift from `SUBSYSTEMS.capabilities` → startup validator asserts every `*.capability_required` exists in the registry's `capabilities` list; failure raises during `validate_registry()`. Sibling of `validate_identity_contract`.
- Cogs collapse participation/visibility/notification/preference into one object → docstring contract + code review + a structural unit test in `tests/unit/schema/test_participation_separation.py` asserting that no `ParticipationSchema` has a single field of type `dict[str, Any]` masquerading as everything.
- Cogs over-declare (e.g. game cogs declaring user game state) → guild config schema covers **guild-level operator configuration only**; participation schema covers **per-user runtime state only**; game state stays in `game_state_service`. Document on `BindingSpec` / `SubscriptionSpec` / `PreferenceSpec` docstrings; enforce in review.
- Resource requirements duplicated across subsystems → resource diagnostics in Phase 4c surfaces shared usage; cogs see the same `mod-logs` channel cited by multiple subsystems as a feature, not a problem.
- Capability decorators slow test cog loading → decorators are no-ops outside `cog_load`; registration runs once.

**Implementation considerations.**
- All three schema kinds must be reachable **without instantiating the cog** (so the wizard can render setup for subsystems whose cogs failed to load — INV-J interaction). Declare as module-level constants; register them in `cog_load`; import directly when needed.
- Migrate 2 reference subsystems (xp, economy) with complete schemas (1a + 1b + 1c) plus 1 stub (admin, 1a only) first to validate all three protocols before sweeping the rest.
- The `ParticipationSchema` for `xp` is a reference test: it must declare `subscriptions=["levelups"]`, `notification_intents=["xp.levelup"]`, `visibility_intents=["xp.public_rank"]`, `preference_specs=["digest_frequency"]` — and these MUST be separate, not collapsed.

**Entry criteria.** Phase 0 complete.
**Exit criteria.**
- All three schema protocols (1a, 1b, 1c) exist and are documented.
- ≥3 subsystems have config schemas; ≥2 have participation schemas; ≥6 have resource requirements.
- Startup validator asserts schema↔registry capability consistency for both guild-level and user-level capability namespaces.
- `!platform schemas`, `!platform participation-schemas`, `!platform resource-requirements` admin commands work.
- New AST invariants scaffolded (warn-only): any panel-bearing cog should register a config schema; any cog supporting per-user opt-in should register a participation schema; any cog with `bindings` should declare `resource_requirements`. All promote to error in Phase 6.

**User value.** Admin-only (`!platform *` commands).

---

## Phase 2 — Typed State Storage Layer

**Objective.** Stand up three sibling state runtimes — guild bindings, per-user participation state, and a unified resource layer — each typed, each cached, each behind its own mutation pipeline.

**Architectural purpose.** Today XP's announce channel, Economy's log channel, and ~6 other settings store raw `str(channel.id)` directly in `guild_settings`. There is no per-user participation storage at all. Channel and role lookups happen through ad-hoc resolution in helper modules. The wizard, the participation hub, and resource diagnostics each need typed primitives. This phase splits into three sibling sub-phases that share the **same 6-step mutation contract** shape (`validate → authority → read-old → write → invalidate → emit`) inherited from `GovernanceMutationPipeline`.

---

### Phase 2a — Unified Guild Resource Runtime (REORDERED — now first)

**Why first.** Resources are the platform substrate. Bindings reference resources; participation references subscriptions that reference resources via notification routing; diagnostics inspect resources; governance role-mapping maps to resources; provisioning creates resources. Every Track-2 sub-phase and every Tier 4+ phase depends on this layer. It must complete before bindings (P2b) and before participation state (P2c).

**Systems introduced.**
- `disbot/core/resources/` — a new top-level package mirroring `core/runtime/` layering, governing channels, roles, categories, threads as first-class resource types.
- `disbot/core/resources/types.py` — `GuildResource` base + `ChannelResource` / `RoleResource` / `CategoryResource` / `ThreadResource` subclasses. Each carries `id`, `name`, `kind`, `metadata`, `last_validated_at`, and resource-specific fields.
- `disbot/core/resources/discovery.py` — generalized resource enumeration; absorbs `_build_channel_options` (channels) and `_find_role_normalized` (roles) from Phase 0's extracted helpers. Adds `list_resources(guild, kind, filter)`, `resolve_resource(guild, kind, id)`, `validate_resource(resource) → ResourceStatus`.
- `disbot/core/resources/role_service.py` — formal role service: `list_roles()`, `filter_roles(predicate)`, `resolve_scope(role) → GovernanceScope` (from P1d), `validate_role_permissions(role, capability)`, `match_role_template(role) → RoleTemplate | None` (consumes templates declared in P1d). Generalizes today's `_helpers.py` patterns.
- `disbot/core/resources/channel_service.py` — formal channel service: `list_channels()`, `filter_channels(predicate)`, `resolve_intent(channel, intent)`, `validate_channel_permissions(channel, intent)`. Generalizes today's channel helpers.
- `disbot/core/resources/__init__.py` — exposes a unified `resources` namespace: `from core import resources; resources.channel_service.list_channels(...)`.
- `disbot/core/resources/mutation.py` — `ResourceMutationPipeline` shell. Actual resource creation/deletion lands in P7.5; this phase introduces the **pipeline contract** so bindings and participation pipelines can wire to it.
- `disbot/utils/db/resource_cache.py` — `resource_validation_cache` table writer (status of channels/roles/categories without re-resolving on each query). Bounded TTL.

**Why a sibling package vs `core/runtime/`.** Resources are the substrate runtime primitives operate on (channels, roles, categories), not the runtime primitives themselves. Layered correctly, `core/resources/` sits beneath `core/runtime/` and is imported by both runtime modules and view selectors. Adding it as a sibling package keeps the dependency graph crisp.

### Phase 2b — Guild Bindings (REORDERED — now after resources)

**Systems introduced.**
- `disbot/core/runtime/bindings.py` — `BindingStore` over a new `subsystem_bindings` table: `(guild_id, subsystem, binding_name, kind, target_id, status, last_validated_at, version)`. Status enum: `bound | unresolved | missing | invalid`.
- `disbot/utils/db/bindings.py` — CRUD; all writes routed through a new `BindingMutationPipeline` (validate → resolve via `core/resources/discovery` → upsert → invalidate guild_config → emit event). **Shape identical to `GovernanceMutationPipeline`.** Now consumes resources from P2a rather than inlining channel/role lookups.
- New event names in `core/events_catalogue.KNOWN_EVENTS`: `EVT_BINDING_CHANGED`, `EVT_BINDING_INVALIDATED`.
- `disbot/utils/guild_config_accessors.py` — `get_binding(guild_id, subsystem, name) → BindingValue` via the version-stamped cache (uses the `TypedAccessor[T]` helper from Phase 0).

### Phase 2c — Per-User Participation State + Feature Subscriptions (REORDERED — now after bindings)

**Systems introduced.**
- `disbot/core/runtime/participation_state.py` — `ParticipationStore` over a new `user_participation` table: `(guild_id, user_id, subsystem, status, last_updated, version)` with status enum `opted_in | opted_out | not_set`. Default is **`not_set`** — explicit opt-in required for subsystems with `requires_optin=True`.
- A separate `user_subscriptions` table: `(guild_id, user_id, subsystem, subscription_name, enabled, version)` for fine-grained subscriptions (`FeatureSubscription(feature="xp.levelup_notifications", enabled=True)`). Separate from the top-level `user_participation` table so a user can be "participating in XP" but suppress "XP levelup notifications" — these are distinct decisions.
- A `user_preferences` table: `(guild_id, user_id, namespace, key, value, version)` for UX prefs (digest frequency, embed style). Separate again — preferences are not subscriptions, not visibility, not participation.
- A `user_visibility_overrides` table: `(guild_id, user_id, intent, enabled, version)` for `VisibilityIntent` toggles (e.g. "hide me from leaderboard"). Separate again. **Four tables, four concerns, never combined.**
- `disbot/utils/db/participation.py` — CRUD; writes routed through new `ParticipationMutationPipeline` (validate → user-authority → read-old → write → invalidate → emit). The authority check is "is this the same user, or a moderator+ on this guild?" — a different authority model than governance writes.
- New event names: `EVT_PARTICIPATION_CHANGED`, `EVT_SUBSCRIPTION_CHANGED`, `EVT_USER_PREFERENCE_CHANGED`, `EVT_USER_VISIBILITY_CHANGED`.
- `disbot/utils/user_config_accessors.py` — sibling to `guild_config_accessors`, using the same `TypedAccessor[T]` helper. `get_participation(guild_id, user_id, subsystem)`, `get_subscription(...)`, `get_preference(...)`, `get_user_visibility(...)`.
- Per-user version-stamped cache (`disbot/core/runtime/user_config.py`) — separate from `guild_config`. Same shape; **separate keyspace and separate TTL** because user cache eviction patterns differ (more entries, hotter for active users, colder for inactive).

### Phase 2d — Feature Flags + Environment Tiers + Rollout Policy (NEW)

**Why this lands in Tier 1 alongside resources/bindings/participation.** Every subsequent phase (P3 drafts, P4 diagnostics, P4.5 governance runtime, P6.5 notification routing, P7 wizard, P7.5 provisioning) wants to ship behind a gate. Today the codebase relies on ad-hoc env vars (`STRICT_DISABLED`, `IDENTITY_CONTRACT_STRICT`, etc.) — workable for binary toggles, insufficient for staged rollouts. Standing up `FeatureFlag` + `EnvironmentTier` + `RolloutPolicy` infrastructure here means every later phase can ship with a typed gate from day one. Doing it later would require backfilling gates across nine phases of code.

**Systems introduced.**
- `disbot/core/runtime/feature_flags.py` — runtime over the P1d declarations:
  - `is_enabled(flag: str, guild_id: int | None = None) → bool` — primary read API
  - `evaluate_rollout(flag: str, guild_id: int) → RolloutDecision` — staged rollout evaluation
  - In-process cache version-stamped via EventBus invalidation
- `disbot/utils/db/feature_flags.py` — `feature_flag_state` table: `(flag_name, environment_tier, guild_id, enabled, rollout_metadata, version)`. Composite PK on `(flag_name, guild_id NULLS FIRST)`.
- `disbot/utils/db/environment_tiers.py` — `environment_tier` table: maps guild IDs to tiers (owner guild → `OWNER_GUILD_ONLY`, designated test guilds → `BETA`, etc.).
- `RolloutMutationPipeline` — flips flags and advances rollouts through the same 6-step contract (validate → authority → read-old → write → invalidate → emit). Authority: platform-owner only (a new tier above `moderator`, defined in P1d's `PermissionTier`).
- `disbot/services/feature_flag_service.py` — service-layer entry: `service.set_flag(name, guild_id, enabled, actor)`, `service.advance_rollout(flag, target_percentage, actor)`.
- New events: `EVT_FEATURE_FLAG_CHANGED`, `EVT_ROLLOUT_ADVANCED`, `EVT_ENVIRONMENT_TIER_CHANGED`.

**Existing primitives reused / extended.**
- All existing `STRICT_DISABLED`, `IDENTITY_CONTRACT_STRICT`, `BINDINGS_PRIMARY`, etc. env-var gates are **migrated to feature flags** behind back-compat shims (env var read if no flag, flag read if present). One AST invariant tracks remaining env-var gates over time; new gates must be flags.
- `governance/cache.py` — provides the version-stamping idiom; `feature_flag_cache` mirrors it.

**Migration impact.**
- DB migration `020d_feature_flags.sql` — `feature_flag_state` + `environment_tier` tables.
- Owner guild and designated test guilds inserted as seed data via the migration.
- All existing env-var gates declared as feature flags during migration; runtime falls back to env vars for one release, then flips to flag-primary in the following release.

**Existing primitives reused / extended.**
- `disbot/governance/writes.py:GovernanceMutationPipeline` — all four new pipelines (`ResourceMutationPipeline` shell from P2a, `BindingMutationPipeline` from P2b, `ParticipationMutationPipeline` from P2c, `RolloutMutationPipeline` from P2d) mirror this 6-step contract exactly. Audit semantics shared.
- `disbot/core/runtime/guild_resources.py:resolve_settings_channel` — generalize to `resolve_binding(guild, subsystem, binding_name)`; the function moves to `core/resources/discovery.py` as part of 2a, with a back-compat shim retained for one release.
- `disbot/core/runtime/guild_config.py` — bindings cache through this primitive, version-stamped per guild as today. **A sibling `disbot/core/runtime/user_config.py` is added in 2c for per-user state.** A third sibling `feature_flag_cache` lands in 2d.
- `disbot/views/selectors/` (`ChannelSelector`, `RoleSelector`, `ScopeSelector`, `SubsystemSelector`) — refactored in 2a (selectors consume `core/resources/role_service` and `core/resources/channel_service` instead of inlining selector logic). Public API stable.
- `disbot/services/governance_service.py:get_member_visibility_tier` — reused by `ParticipationMutationPipeline.authority` to validate moderator-overrides of user state.
- `disbot/core/runtime/scope_locks.py:lock_for` — four mutation pipelines acquire scope locks scoped differently: resources on `(guild, resource_id)`, bindings on `(guild, subsystem)`, participation on `(guild, user, subsystem)`, rollouts on `(flag_name)` globally.

**Dependencies.** Phase 1 (need `BindingSpec`, `SubscriptionSpec`, `ResourceRequirement`, and P1d governance/rollout declarations to know what to migrate / instantiate).

**Sub-phase ordering (binding).** 2a → 2b → 2c → 2d. Each consumes primitives from the prior. Concretely:
- 2a publishes `core/resources/` (resources are the substrate).
- 2b consumes `core/resources/discovery` to resolve binding targets.
- 2c references resources indirectly via binding-shaped subscription targets (e.g. a subscription's notification channel is bound through P2b which resolves via P2a).
- 2d gates everything from Tier 4 onward; lands at the end of P2 so all of Phase 2's exit checks themselves run behind a flag.

**Migration impact.**
- **DB migration `020a_resource_registry.sql`** (was `020c`, renamed) — resource cache table.
- **DB migration `020b_subsystem_bindings.sql`** (was `020`, renamed) — bindings table.
- **DB migration `020c_user_participation.sql`** (was `020b`, renamed) — four sibling participation tables. All audited via `governance_audit_log` with a new `actor_type='user'` discriminator.
- **DB migration `020d_feature_flags.sql`** (NEW) — `feature_flag_state` + `environment_tier` tables; seed data for owner guild + test guilds.
- **Settings KV backfill** — same shape as before. Tracked via a `BINDING_MIGRATION_VERSION` flag in the KV.
- **Participation backfill** — none; default `not_set` for every user means no backfill needed.
- **Env-var migration** (NEW, 2d) — existing env-var gates declared as feature flags; back-compat shim reads env var if flag absent, flag if present.
- **Feature flags** — `RESOURCES_UNIFIED=true` for 2a (default false at first); `BINDINGS_PRIMARY=true` for 2b; `PARTICIPATION_ENABLED=true` for 2c; `FEATURE_FLAG_PRIMARY=true` for 2d (the meta-flag — bootstrapped via env var). Each flag flipped after its sub-phase verifies in production canary.
- Identity surfaces: still none added (waits for Phase 6).

**Risks & mitigations.**
- Backfill inflates the audit log → backfill writes bypass `BindingMutationPipeline.audit` with `actor_id=0`, action `backfill_v1`; documented exception in the pipeline docstring; regression test ensures no other code path emits audit-less binding writes.
- Per-user cache cardinality explodes → `user_config` cache uses LRU eviction (max N entries, e.g. 50k) on top of TTL. Hot users stay; cold users fall out. Sized per active-user-count metrics.
- Per-user writes burst on subscription-toggle storms → `ParticipationMutationPipeline` enforces a per-user rate limit (e.g. 30 ops/min via existing `scope_locks` primitive); excess returns `RateLimited` finding to the UI.
- Settings KV mid-write during backfill → backfill runs under `pg_advisory_lock` per guild (INV-I primitive).
- Dual sources of truth during migration → feature-flag cutover; old paths keep working either way.
- Governance gate fires twice → cogs migrate one at a time; after all migrated, ban raw `set_setting` on binding-typed keys via new AST invariant.
- Resource unification disrupts existing channel/role panels → selectors are refactored to consume `core/resources/` but keep their public API; existing panel cogs do NOT need to change. The refactor is internal.
- Default participation defaults wrong (everyone auto-opted-in) → 2b ships with **opt-in defaults across the board** for subsystems declaring `requires_optin=True`. Tournaments, automations, and AI-facing subsystems MUST set `requires_optin=True`; XP / Economy / general can default `requires_optin=False` but `notification_intent` defaults stay suppressed until explicit opt-in (see Phase 6.5).

**Implementation considerations.**
- The four sub-phases ship sequentially. 2a ships first (resources foundational); 2b second (bindings consume resources); 2c third (participation references binding-shaped targets); 2d last (feature flag infrastructure is the meta-gate for everything Tier 4+).
- `status` column on `subsystem_bindings` unlocks Phase 4a diagnostics. The new `user_participation.status` column unlocks Phase 4b diagnostics ("only 12% of guild users have opted into XP — is this expected?"). Resource cache unlocks Phase 4c. Feature flag audit unlocks Phase 4-level rollout observability.
- PK on `subsystem_bindings` is `(guild_id, subsystem, binding_name)` — bindings are scope-aware from day one. Same channel can be a different binding in different subsystems.
- `EVT_BINDING_CHANGED` integrates with `session_manager.invalidate_subsystem_sessions` so binding changes invalidate stale sessions, mirroring the existing visibility-change → session-purge pattern. `EVT_PARTICIPATION_CHANGED` triggers a narrower invalidation: only the affected `(guild, user)` cache key.
- Resource cache TTLs differ from validation cache TTLs: the resource itself is cached at the `guild_resources` layer (Discord-object-lifetime); the **status** ("does this channel still exist?", "does it still match its binding?") is cached separately with a shorter TTL.

**Entry criteria.** Phase 1 complete; ≥3 reference subsystems have schemas (1a + 1b + 1c + 1d declarations).
**Exit criteria.**
- Migrations 020a, 020b, 020c, 020d applied; backfill completed on all production guilds.
- Feature flags `RESOURCES_UNIFIED=true`, `BINDINGS_PRIMARY=true`, `PARTICIPATION_ENABLED=true`, `FEATURE_FLAG_PRIMARY=true` in production.
- ≥6 raw-id settings migrated (XP_ANNOUNCE_CHANNEL, ECONOMY_LOG_CHANNEL, TRUSTED_TIER_ROLE_ID, etc.).
- ≥2 subsystems have working participation state (xp opt-out, economy daily-reminder subscription).
- `core/resources/` is the single source of channel/role enumeration; existing selectors thinly wrap it.
- ≥3 env-var gates migrated to feature flags; new gates required to be flags (AST tracks).

**User value.** None directly. Transitively unlocks every later phase: Phase 4 diagnostics, P4.5 governance runtime, P6.5 routing, and the staged-rollout infrastructure that lets P7+ ship safely.

---

## Phase 3 — Draft / Preview / Commit Session Pattern

**Objective.** A typed pattern for multi-step state flows: build a **draft** in session state, run **validation**, render a **preview**, and only **commit** through the relevant Mutation Pipelines on confirmation. Used by **all three tracks** — guild config drafts (Track A), participation onboarding flows (Track B), and resource provisioning flows (Track C).

**Architectural purpose.** A wizard without drafts is a series of disconnected commands. Drafts must NOT be a wizard-cog concept — they're a platform primitive any future subsystem can use (automation rule builders, tournament configurators, multi-guild template editors, per-user onboarding wizards). Building this before the wizard cog prevents entanglement. **One primitive, three commit targets.**

**Systems introduced.**
- `disbot/core/runtime/config_drafts.py` — `ConfigDraft` over `runtime_session_state` (the existing 2h TTL table; no migration needed). Operations: `create`, `set`, `validate → ValidationReport`, `preview → PreviewReport`, `commit → CommitResult`, `discard`.
- `ValidationReport` and `PreviewReport` are typed dataclasses with `findings: list[Finding]` and `severity` per finding. Modeled on `summarize_findings` shape from `subsystem_registry.py` (lines 824–841).
- `CommitResult` records every mutation pipeline invoked and the `mutation_id` returned — full audit traceability across all pipelines (`GovernanceMutationPipeline`, `BindingMutationPipeline`, `ParticipationMutationPipeline`, `ResourceMutationPipeline`).
- `DraftScope` enum: `GUILD_CONFIG | PARTICIPATION | RESOURCE_PROVISIONING` — the same `ConfigDraft` primitive carries the discriminator that selects which pipelines `commit()` invokes. A single draft never spans scopes; a user-flow that touches both guild config and participation creates two draft sessions.

**Existing primitives reused / extended.**
- `disbot/core/runtime/session_manager.py` — reused as-is; drafts live in `runtime_session_state` keyed `draft:{subsystem}`.
- `disbot/core/runtime/state_store.py:set_many` — atomic multi-key upsert is the basis for `ConfigDraft.set`.
- `disbot/core/runtime/scope_locks.py:lock_for` — per-draft scope lock (`config_draft:{session_id}:{subsystem}`) prevents racy concurrent edits.
- `disbot/governance/writes.py:GovernanceMutationPipeline` + new `BindingMutationPipeline` (Phase 2) — `commit` calls both. **The wizard MUST NOT mutate anything directly.** This is the single most important architectural rule of the roadmap.
- `disbot/core/runtime/session_gc.py` — drafts inherit the 2h TTL automatically.

**Dependencies.** Phase 2 (need `BindingMutationPipeline` to commit into).

**Migration impact.** No new DB migration. Identity surfaces untouched. Settings KV untouched.

**Risks & mitigations.**
- Partial commit (governance set, binding fails) → introduce a `commit_plan` that pre-validates every step; commit phase rolls forward only; `CommitResult` surfaces "retry from failed step." **No cross-pipeline transactional rollback** — known design constraint; pipelines commit independently today.
- Contributors bypass `commit` and call mutation pipelines directly → **AST invariant**: any call to `BindingMutationPipeline.*` or `GovernanceMutationPipeline.*` from a file under `disbot/cogs/setup/` is a build failure. (The directory exists from Phase 7 onward; the invariant lands here in advance.)
- Drafts survive past intended life → piggyback on `session_gc._run_gc_loop`; drafts expire with the parent session.

**Implementation considerations.**
- Validation runs in the **Validate** phase of the existing scope-lock V/M/A pattern (`docs/architecture.md` §Realtime / event-driven systems); Discord I/O (rendering preview) happens outside the lock.
- A `Finding` reuses the tier classification (`fatal | auto_healable | warn_only`) from `subsystem_registry.IDENTITY_FINDING_TIER` (line 816) so admin UIs share rendering logic between identity diagnostics and setup diagnostics.

**Entry criteria.** Phase 2 complete; `BINDINGS_PRIMARY=true`.
**Exit criteria.**
- `ConfigDraft` primitive with full unit-test coverage.
- One reference flow (XP setup) works end-to-end as a test fixture; no production cog uses it yet.
- AST invariant blocks direct mutation pipeline calls from `cogs/setup/`.

**User value.** None (foundation).

---

## Phase 4 — Diagnostics + Health (runs in parallel with P3)

**Objective.** Surface configuration completeness, participation drift, and resource issues **before the wizard exists**. The wizard later consumes these reports.

**Architectural purpose.** "You can't fix what you can't see." Diagnostics give operators an actionable view of what needs setup; the wizard becomes a remediation UI on top of the same data. Building first because (a) standalone operator value, (b) forces `SubsystemSchema.completeness_rule` (Phase 1) to be real, (c) shakes out edge cases in the binding/participation/resource migrations (Phase 2) before they hit a multi-step UI. Diagnostics fans out across all three tracks.

---

### Phase 4a — Setup Health (existing scope)

**Systems introduced.**
- `disbot/services/setup_health_service.py` — provider-registry pattern; producer of `SetupHealthReport` per guild: missing bindings, missing channels, invalid roles, capability/governance mismatches, schema-version drift, governance-version drift.
- Admin commands via diagnostics_service: `!platform setup`, `!platform setup <subsystem>`, `!platform setup --json`.
- Prometheus metrics: `setup_health_bindings_missing_total{subsystem}`, `setup_health_completeness_ratio{subsystem}`, `setup_health_schema_drift_total{subsystem}`.

### Phase 4b — Participation Health (NEW)

**Systems introduced.**
- `disbot/services/participation_health_service.py` — producer of `ParticipationHealthReport` per guild: subscription drift, opt-in adoption rates, notification-suppression coverage, eligibility-rule failure counts, default-vs-explicit subscription ratio.
- Admin commands: `!platform participation`, `!platform participation <subsystem>`, `!platform participation <user_id>` (per-user inspection for moderators+).
- Prometheus metrics: `participation_optin_ratio{subsystem}`, `subscription_active_total{subsystem,subscription}`, `notification_suppressed_total{intent}`, `participation_eligibility_failure_total{subsystem,rule}`.
- **Per-user diagnostic surface** for the user themselves: `/myprofile health` (Phase 7 exposes this in UI) shows their own subscription state across subsystems, but never another user's state without moderator authority.

### Phase 4c — Resource Diagnostics (NEW)

**Systems introduced.**
- `disbot/services/resource_health_service.py` — producer of `ResourceHealthReport` per guild: orphan resources (channel referenced by no subsystem), starvation (subsystem requires channel that doesn't exist), permission gaps (bot can't post to bound channel), category drift (channels not under expected category), thread expiration patterns.
- Admin commands: `!platform resources`, `!platform resources <kind>`, `!platform resources --missing`.
- Prometheus metrics: `resource_orphan_total{kind}`, `resource_missing_total{kind}`, `resource_permission_gap_total{kind,capability}`.
- **Cross-subsystem resource graph**: surfaces which channels/roles are bound by multiple subsystems — informs Phase 7.5 auto-provisioning decisions ("merge into one channel" vs "split into per-subsystem channels").

**Existing primitives reused / extended.**
- `disbot/services/diagnostics_service.py:register` — all three new health services self-register snapshot providers (sibling providers, named separately).
- `disbot/core/runtime/bindings.py` (Phase 2a) — drives binding-missing checks via `status` column.
- `disbot/core/runtime/participation_state.py` (Phase 2b) — drives subscription-drift and opt-in-rate checks.
- `disbot/core/resources/discovery.py` (Phase 2c) — drives resource-orphan and resource-missing checks.
- `disbot/governance/health.py` — extend the pattern; add `setup_completeness_check`, `participation_completeness_check`, `resource_completeness_check` (or refactor to a unified `health_check_for(scope)` dispatch).
- `disbot/services/webhook_reporter.py` — alerts on high-severity regressions in any of the three reports.

**Dependencies.** Phase 1 (schemas) + Phase 2 (statuses across all three sub-storages). Runs **in parallel** with Phase 3.

**Migration impact.** None. All reads.

**Risks & mitigations.**
- Per-guild completeness expensive across all guilds → on-demand reads only; the periodic Prometheus-emitting job samples one guild per minute round-robin (same rate as existing governance-version checks).
- Participation health surfacing per-user data is a privacy boundary → `participation_health_service` exposes **aggregate** metrics (counts, ratios) at the guild scope; per-user inspection requires moderator+ authority and is logged via `governance_audit_log` with a `participation_inspection` action.
- False-positive "missing binding" findings during backfill → reports gated on the per-track feature flags (`BINDINGS_PRIMARY`, `PARTICIPATION_ENABLED`, `RESOURCES_UNIFIED`); before flip, completeness computed from legacy sources as a transitional fallback.

**Implementation considerations.**
- Reuse the `summarize_findings` finding-tier model so the wizard can render with shared code in Phase 7. All three health services produce findings with the same `(severity, kind, message, suggested_action)` shape.
- Resource diagnostics should categorize findings by remediability: `auto_repairable` (bot has permissions to fix), `operator_required` (needs server admin), `unknown` (probe failed). Phase 7.5 consumes the `auto_repairable` set.

**Entry criteria.** Phases 1 + 2 complete.
**Exit criteria.**
- `!platform setup`, `!platform participation`, `!platform resources` work for any guild.
- Prometheus dashboards show per-subsystem completeness, opt-in ratios, and resource health.
- Webhook alerts trigger on completeness ratio < 0.5, opt-in ratio crashing > 50% in 24h, or resource missing-rate spiking.

**User value.** **First user-visible deliverable.** Operators see what is misconfigured (4a), what user adoption looks like (4b), and what resource state needs attention (4c).

---

## Phase 4.5 — Governance / Access Control Runtime (NEW)

**Objective.** Promote governance from a visibility-policy engine into a full access-control runtime that owns: role templates, permission tier mapping, governance role provisioning, smart role detection, recommended mappings, delegated subsystem administration, and access scopes for setup/diagnostics/participation surfaces.

**Architectural purpose.** Governance is already a first-class layer in SuperBot (`disbot/governance/`, ~12 modules), but its current scope is narrow: per-scope visibility + cleanup overrides + a capability namespace. The wizard and the platform UI framework need more: **delegated authority** ("a guild-appointed Setup Captain can run !setup but not modify governance"), **environment-aware permissions** ("beta features are visible only to platform-owner-flagged users"), **smart role mapping** ("you have a role called Moderator that looks like the Moderator template — bind it to the `moderator` tier?"), and **role provisioning** ("create the recommended governance roles for this guild"). Standing this up **between diagnostics and UI** means the diagnostics surface from P4 can drive governance findings (P4.5 consumes), and the UI framework from P5 can render role-aware components (P5 consumes).

**Systems introduced.**
- `disbot/governance/role_provisioning.py` — service over the `RoleTemplate` declarations from P1d. Operations:
  - `detect_existing_roles(guild) → list[RoleMatch]` — fuzzy-match guild roles against templates (name, permissions, color)
  - `recommend_mappings(guild) → list[RoleRecommendation]` — recommended template → existing-role bindings
  - `provision_role(guild, template) → ProvisioningResult` — create a new role from a template via `ResourceMutationPipeline` (the P2a shell)
  - `bind_role_to_tier(role, tier, actor) → BindingResult` — record a role → `PermissionTier` mapping
- `disbot/governance/role_diagnostics.py` — produces `RoleHealthReport`: missing recommended roles, role-permission gaps, redundant role mappings, tier-coverage gaps.
- `disbot/governance/access_scopes.py` — typed access scopes for platform surfaces: `SETUP_SCOPE`, `DIAGNOSTICS_SCOPE`, `PARTICIPATION_SCOPE`, `GOVERNANCE_SCOPE`, `ROLLOUT_SCOPE`. Each scope has a `required_tier`, `delegatable_to: list[PermissionTier]`, and `audit_action_prefix`.
- `disbot/governance/delegation.py` — `Delegation` model: a guild-admin grants a tier-scoped capability to a specific user or role for a bounded period. Stored in a new `governance_delegations` table; audited via the governance audit log.
- New service: `disbot/services/access_control_service.py` — single entry point for "can this member do this thing?" queries that overlays Discord permissions + governance tier + delegation + feature flag (from P2d) into one resolution result.
- New admin commands routed through diagnostics_service:
  - `!platform governance` — current governance state for the guild
  - `!platform governance roles` — `RoleHealthReport`
  - `!platform governance delegate <user> <scope> <duration>` — operator-level delegation
  - `!platform governance recommend` — runs `recommend_mappings` and shows recommendations

**Existing primitives reused / extended.**
- `disbot/governance/__init__.py` + `governance/resolver.py` — the resolution path already exists; this phase adds access-scope resolution as a new entry point alongside `resolve_visibility` and `resolve_execution`.
- `disbot/governance/writes.py:GovernanceMutationPipeline` — delegations and role mappings flow through it.
- `disbot/core/resources/role_service.py` (P2a) — drives role detection.
- `disbot/services/governance_service.py:get_member_visibility_tier` — extended to consider delegations.
- `disbot/governance/templates.py` — `apply_template` extended to optionally include role provisioning instructions (cross-guild template application can now offer "and create these governance roles?").
- `disbot/services/diagnostics_service.py:register` — `role_diagnostics` self-registers a snapshot provider.

**Dependencies.** Phase 4 (diagnostics shape for findings); Phase 1d (RoleTemplate declarations); Phase 2a (resource runtime for role lookups); Phase 2d (feature flags for environment-aware access).

**Migration impact.**
- DB migration `024a_governance_delegations.sql` — `governance_delegations` table.
- DB migration `024b_role_template_bindings.sql` — `role_template_bindings` table: `(guild_id, role_id, template_name, bound_by, bound_at)`.
- Identity surfaces: unchanged.
- Access-scope strings declared in code; new schema invariant validates that every admin command corresponds to a declared access scope.

**Risks & mitigations.**
- Smart role detection produces false matches → all detection results are **suggestions**; binding is always explicit (operator-confirmed). The wizard renders recommendations with confidence scores; auto-bind is disabled by default.
- Delegation creates an authority back-channel that bypasses normal governance → delegations are time-bounded (max 30 days; default 7), tier-bounded (can only delegate equal-or-lower tier), and audited at grant + revoke + use. A `!platform governance audit` command shows recent delegated actions.
- Role provisioning creates roles the bot can't manage → provisioner verifies bot's `Manage Roles` permission and the bot's highest role position before attempting; surfaces "you need to move the bot's role above X" findings instead of failing mid-provision.
- Environment-aware permissions create surprise denials → feature flag changes that affect access scopes are surfaced in `EVT_FEATURE_FLAG_CHANGED` consumers (notification routing alerts the affected user via the suppression-aware notification path).

**Implementation considerations.**
- P4.5 is the right home for the **role-mapping wizard flow** that lands in P7 — but the runtime that flow uses lives here, fully tested before any UI exists.
- This phase is the moment to formalize what "platform-owner" means as a tier (above `administrator`/`moderator` in the existing taxonomy). The platform-owner tier is restricted to: feature flag mutations (P2d), environment tier assignments (P2d), and cross-guild template publishing (P8). Codified in `PermissionTier` from P1d.

**Entry criteria.** Phases 4 complete.
**Exit criteria.**
- `RoleHealthReport` produced for any guild.
- Smart role detection demonstrated against ≥3 test guilds (high-recall, no false-bind).
- ≥1 governance role provisioned via the runtime (in a test guild).
- Delegation grant/use/revoke audited end-to-end.
- `access_control_service.can(member, scope) → AccessDecision` returns a unified yes/no with reason across Discord permissions + tier + delegation + feature flag.

**User value.** Indirect for the moment; operator-facing once P5/P7 expose role provisioning flows.

---

## Phase 5 — Platform Navigation Framework

**Objective.** A unified UI runtime for the bot's entire control plane — setup, help, dashboards, participation hub, diagnostics, role/channel management — composed from declarative `Screen` primitives and a shared component registry. Eliminates hand-built `BaseView` subclasses for every config flow AND replaces the current standalone help/dashboard architectures.

**Architectural purpose.** Today each panel is hand-coded; the help cog (`disbot/cogs/help_cog.py`, 506 LOC) is its own UI track; the channel/role panels (~2300 LOC) are separate from each other; the wizard would multiply this fragmentation. A unified framework collapses these into one set of primitives. Future subsystems opt into wizard / help / dashboard / governance support by declaring a schema (Phase 1) — no UI code required. **There is no separate help system. There is no separate dashboard system. There is no separate setup system. There is no separate governance UI. There is one navigation framework, and these are flows inside it.**

This phase is structured into three sub-phases. **Sub-phase ordering is binding**: P5a (Screen primitive) before P5b (component registry) before P5c (flow unification). Inverting this would create either screens that can't render components or components that have no compose target.

---

### Phase 5a — Screen Primitive (existing scope)

**Systems introduced.**
- `disbot/core/runtime/screens.py` — `Screen` Protocol: `render(draft, schema_slice) → (Embed, View)`, `on_submit(interaction, draft) → NextScreen | Commit | Cancel`.
- Built-in screen kinds: `BindingScreen`, `SettingScreen`, `ConfirmScreen`, `PreviewScreen`, `ProgressOverviewScreen`, `BreadcrumbScreen`, `SubscriptionScreen` (NEW — toggles participation subscriptions), `PreferenceScreen` (NEW — toggles user preferences), `VisibilityScreen` (NEW — toggles `VisibilityIntent`s).
- `disbot/core/runtime/screen_navigator.py` — orchestrator using the existing `navigation_stack` for back/forward; supports linear, branching, and modal-nested flows.

### Phase 5b — Component Registry Foundation (NEW)

**Why 5b lands before any wizard / dashboard / participation surface.** Components are the **vocabulary** the surfaces speak. Building surfaces first would lock in ad-hoc widgets that later have to be back-ported into the registry — a cost paid once per surface. Building the registry first means the wizard cog in P7 is **assembled** from registered components, not invented.

**Systems introduced.**
- `disbot/core/runtime/components/` — package of reusable, declarative platform components, each a typed primitive:
  - `ChannelSelector` (extracted from `views/selectors/channel.py`, generalized over `core/resources/channel_service` from P2a)
  - `RoleSelector` (extracted from `views/selectors/role.py`, generalized over `core/resources/role_service` from P2a)
  - `CategorySelector`, `ThreadSelector` (NEW)
  - `MemberSelector` (NEW — for participation flows where moderator+ inspects a specific user)
  - `PermissionPicker` (NEW — for P4.5 role-tier mapping flows; renders the `PermissionTier` taxonomy from P1d)
  - `BindingPanel` — renders a `BindingSpec` with selector + clear/validate buttons
  - `DiagnosticsPanel` — renders a `Findings` list with severity color-coding (consumed by P4a/4b/4c and P4.5 reports)
  - `FeatureTogglePanel` — renders a `SubscriptionSpec` or `VisibilityIntent` toggle
  - `FeatureFlagPanel` (NEW — for P2d-flagged surfaces and P4.5 admin views; renders `RolloutDecision` per flag)
  - `RoleProvisioningPanel` (NEW — for P4.5/P7.5 role-template provisioning flows; renders `RoleRecommendation` + provision button)
  - `ProgressPanel` — renders a `ProgressSnapshot` (used by setup, onboarding, leveling — same widget)
  - `BreadcrumbBar` — renders the `navigation_stack` trail
  - `ExperienceModePicker` — renders the Phase 7 mode chooser (Minimal/Recommended/Full/Custom)
  - `DelegationPanel` (NEW — for P4.5 delegation grant/revoke flows)
- `disbot/core/runtime/components/registry.py` — name-keyed registry, same shape as `diagnostics_service`. Components self-register; screens compose them by name. Hot-swappable for tests.

### Phase 5c — Help / Setup / Dashboard / Diagnostics / Governance Unification (NEW)

**Systems introduced.**
- `disbot/cogs/help_cog.py` is **refactored to consume `Screen` + components** instead of carrying its own UI code. The cog shrinks to a thin command dispatcher; ~80% of the file moves into screens registered under `core/runtime/screens.py`.
- `disbot/views/help/` is created (currently absent — there is no `views/help/`). Help becomes a flow class in the navigation framework: `HelpFlow` (a sequence of `Screen` instances driven by `flow_orchestrator`).
- `disbot/views/dashboard/` is created — the user-facing "what's happening in this guild for me?" landing page. It's a flow over the same `Screen` infrastructure. Used by Phase 7's participation hub.
- `disbot/views/diagnostics/` is created — admin-facing diagnostics dashboard composing `DiagnosticsPanel` instances from P4a/4b/4c.
- `disbot/views/governance/` is created — admin-facing governance dashboard composing `RoleProvisioningPanel`, `DelegationPanel`, `FeatureFlagPanel` from P4.5/P2d. **No separate governance cog or one-off panels** — all of it composed from the registry.
- The channel/role panels (`disbot/views/channels/`, `disbot/views/roles/`) are NOT refactored in this phase — they remain ~2300 LOC of hand-built panels until Phase 7.5 generalizes them into resource-provisioning flows. The Phase 5c refactor focuses on help + dashboard + diagnostics + governance + selectors; channel/role panel migration is deferred to avoid over-loading this phase.

**Existing primitives reused / extended.**
- `disbot/views/selectors/{channel,role,scope,subsystem}.py` — refactored in 5b to consume `core/resources/`; public API stable. They become thin wrappers over the new component registry.
- `disbot/core/runtime/navigation_stack.py` — already DB-backed via `state_store`; reused as-is.
- `disbot/core/runtime/component_registry.py` — existing module is extended in 5b with the full set of platform components listed above. Today it has progress/stats/action primitives; we add selectors and panels here.
- `disbot/views/base.py:HubView` / `BaseView` — `Screen` views inherit `HubView` (ephemeral 180s timeout). Persistent variants (the setup entry-point anchor, the dashboard pinned panel) use `PersistentView`.
- `disbot/core/runtime/interaction_router.py` — register prefixes `setup`, `help`, `dashboard`, `participation` for the navigation framework. Each prefix routes through the same `screen_navigator` dispatcher; the prefix differentiates flow ownership for telemetry.
- `disbot/core/runtime/ui_permissions.py:require_execution` — every screen submission checks the capability declared in the corresponding spec (`SettingSpec.capability_required`, `BindingSpec.capability_required`, or `SubscriptionSpec`'s user-capability for self-mutation).
- `disbot/cogs/help_cog.py` — 5c rewrite consumes the new infrastructure.

**Dependencies.** Phase 3.

**Migration impact.**
- No DB migrations.
- **One new subsystem registry entry**: `"setup"` with `visibility_mode: "internal"`, `visibility_tier: "administrator"`, `has_cleanup_rules: True`. This is the canonical home for the wizard's identity strings — anchors, router prefix, sessions all use `"setup"`.
- Identity surfaces: the `setup` router prefix lands here; passes the existing 5-surface contract because `"setup"` is declared in `SUBSYSTEMS`. The 6th surface (schemas) is added in Phase 6.

**Risks & mitigations.**
- Over-engineering trap (generality without users) → build screens **only for the patterns the wizard cog (P7) + help cog rewrite (5c) will need**; defer "arbitrary form builder" to Phase 8.
- `PersistentView` restoration trying to restore in-flight setup panels → setup screens are **ephemeral** `HubView`-style timeouts; drafts persist via `runtime_session_state`, the UI does not. Persistent surfaces are limited to the entry-point anchors (setup, dashboard).
- Capability checks at every screen multiply governance queries → `governance/cache.py` already version-stamps; one read per draft commit is fine. Profile and add a guild_config_accessor for "current setup author's capabilities" only if needed.
- Help cog rewrite breaks existing usage → 5c ships with a feature flag `HELP_FRAMEWORK_V2`; canary on a single guild before broad rollout. The old `help_cog.py` is renamed `help_cog_legacy.py` and conditionally loaded for one release.
- Component registry becomes a junk drawer → enforce naming convention `{kind}_{purpose}` (e.g. `ChannelSelector` not `ChannelDropdown`); component types limited to the listed taxonomy; new components require ADR approval (a new `docs/decisions/` entry).

**Implementation considerations.**
- Screen interaction custom_ids follow the `{prefix}:{action}` convention (`disbot/core/runtime/interaction_router.py`). Prefix is always `setup`; action encodes `{flow}:{step}:{field}` so one handler routes everything.

**Entry criteria.** Phase 3 complete.
**Exit criteria.**
- `Screen` primitive exists.
- Reference flow: a 4-step XP setup (announce channel binding → cooldown → min/max → preview → commit) works end-to-end through `Screen` infrastructure, committing through existing pipelines.
- AST invariant: any new `discord.ui.View` subclass under `cogs/setup/` is a build failure (force everything through Screens).

**User value.** None directly; visible only via the internal reference flow.

---

## Phase 6 — Identity Contract 6th Surface: Schema

**Objective.** Add `SubsystemSchemaRegistry` as the 6th identity surface; `validate_identity_contract` ensures the schema registry, `SUBSYSTEMS`, and `persistent_views._REGISTRY` agree.

**Architectural purpose.** Now that schemas exist (Phase 1), are non-trivial (Phase 5 uses them for rendering), and have stable identity, the identity contract can constrain them without thrashing on early-iteration changes. Timing matters — adding a 6th surface in Phase 1 would mean every Phase 1–5 PR fights the validator.

**Systems introduced.**
- Extension to `disbot/utils/subsystem_registry.py:validate_identity_contract` — adds `schema_subsystem_unknown` finding kind.
- New tier in `IDENTITY_FINDING_TIER` (line 816): `schema_subsystem_unknown: auto_healable` (orphan schemas can be safely unregistered).
- Auto-heal extension in `apply_self_heal` (line 986): `unregister_schema_for_subsystem`.

**Existing primitives reused / extended.**
- `validate_identity_contract` — the validator is already shaped for 5 surfaces; adding a 6th is a ~30-line extension.
- `tests/unit/registry/test_identity_contract.py` — extend to assert that every non-internal subsystem with `panel`-like entry_points has a registered schema (or explicit `has_setup: False`).

**Dependencies.** Phase 5 (so that violating schemas — those with no rendering target — are catchable).

**Migration impact.** None.

**Risks & mitigations.**
- Turning on schema invariants while production has subsystems without schemas → introduce as `warn_only` for one release; promote to `auto_healable` after all production subsystems have a schema or explicit `has_setup: False` opt-out.
- Cog fails to load (INV-J) and schema registry won't have it (false positive) → identity validator already handles INV-J for entry_points; mirror the same handling for schemas (treat INV-J-marked-internal cogs as not requiring a schema for the contract).

**Implementation considerations.**
- Update `docs/architecture.md` to upgrade the identity contract from "five places" to "six places" (currently line 94 in the doc).

**Entry criteria.** Phase 5 complete; reference flow uses real schemas.
**Exit criteria.**
- STRICT-default test green: every non-internal panel subsystem has a config schema (or `has_setup: False`); every cog declaring user-facing commands has a participation schema (or `has_participation: False`); every panel-bearing subsystem declares its resource requirements.
- `IDENTITY_FINDING_TIER` extended with `participation_schema_missing`, `resource_requirement_missing` kinds; auto-heal extensions registered.
- The identity contract is now formally a **6-place** contract: registry, commands, views, router, DB anchors, **schema registries** (the three sibling registries from Phase 1 collectively count as the 6th surface, since they share a self-registration pattern and a single validation path).

**User value.** None directly; protects all later work.

---

## Phase 6.5 — Notification + Visibility Intent Routing (NEW)

**Objective.** Centralize the routing layer for notifications and visibility surfaces. Subsystems declare *intents* (`NotificationIntent("xp.levelup")`, `VisibilityIntent("tournaments.feed")`); a platform router resolves eligibility, suppression, digesting, and delivery. Subsystems **never** push notifications directly.

**Architectural purpose.** Today every cog that wants to notify a user calls `channel.send(...)` or `member.send(...)` directly. The result: no central place to enforce per-user suppression, no digesting, no eligibility filtering, no rate limiting, no audit trail of what was sent. The wizard needs all of these to work; the participation runtime requires them by design (Phase 2b created `user_visibility_overrides`, `user_subscriptions`, and `notification_intents` — but until this phase, nothing consumes them at delivery time). Adding this routing layer **before** Phase 7 ensures the wizard rolls out into a world where its own subscription-toggles actually affect notification behavior. Sequencing it after Phase 6 ensures the identity contract is in place to validate that every declared `NotificationIntent` corresponds to a real `ParticipationSchema` intent.

**Systems introduced.**
- `disbot/core/runtime/notification_router.py` — central dispatch:
  - `route(intent: NotificationIntent, recipients: list[Member], payload: NotificationPayload, **routing_hints) → DispatchResult`
  - Resolution pipeline: **eligibility check → suppression check → digest decision → delivery channel selection → rate-limit gate → audit log → emit**.
  - `DispatchResult` records why each recipient was filtered (or delivered).
- `disbot/services/notification_service.py` — service-layer entry point for cogs. Subsystems call `notification_service.notify(intent="xp.levelup", member=..., payload=...)` and never touch `member.send` or `channel.send` for user-targeted notifications.
- `disbot/core/runtime/visibility_filter.py` — central filter for visibility intents. Used by leaderboard views, public ranks, social feeds. `filter_for_viewer(intent, members, viewer) → list[Member]` removes anyone with a `user_visibility_overrides` row toggling that intent off.
- `disbot/core/runtime/notification_digest.py` — bucketed delivery for intents marked `digestable=True` in their `NotificationIntent` declaration. Daily/weekly digest assembly; emits via the same router but with batched payloads.
- `disbot/core/runtime/notification_suppression.py` — central suppression engine. Respects:
  - User opt-outs (`user_subscriptions.enabled=False`)
  - `requires_optin` defaults (suppress until user opts in)
  - Guild-wide suppression overrides (operator-set via the wizard)
  - Time-window suppression (quiet hours per-user preference)
  - Storm protection (>N messages from one intent in M minutes → digest forced)
- New event names: `EVT_NOTIFICATION_ROUTED`, `EVT_NOTIFICATION_SUPPRESSED`, `EVT_NOTIFICATION_DIGESTED`, `EVT_VISIBILITY_FILTERED`.

**Existing primitives reused / extended.**
- `disbot/core/runtime/participation_state.py` (Phase 2b) — drives subscription + visibility lookups.
- `disbot/services/webhook_reporter.py` — pattern template for the new notification_service.
- `disbot/core/runtime/scope_locks.py:lock_for` — rate-limit gates use per-user scope locks.
- `disbot/core/events.py:bus` — all dispatch events flow through the EventBus.
- `disbot/services/metrics.py` — instrumented at every step.
- `disbot/governance/cache.py` — version-stamped reads for intent visibility.

**Dependencies.** Phase 6 (identity contract must validate that declared intents exist) + Phase 2b (participation state).

**Migration impact.**
- DB migration `024_notification_audit.sql` — `notification_audit` table (`mutation_id`, `intent`, `recipient`, `delivered`, `suppressed_reason`, `digest_batch_id`, `at`). Append-only audit, like `governance_audit_log`.
- Existing direct-send call-sites in cogs (`member.send(...)`, channel-targeted user notifications) are migrated to `notification_service.notify(...)`. AST invariant added: no `member.send` / `user.send` calls outside `disbot/services/notification_service.py` (allowlist exceptions for OOB error reporting).
- Identity surfaces unchanged.

**Risks & mitigations.**
- Subsystems bypass the router via direct `channel.send` → AST invariant blocks user-targeted direct sends; channel-targeted ones (panels, embeds in shared channels) are fine and stay outside the router.
- Suppression engine misfires (legitimate notifications dropped) → router emits `EVT_NOTIFICATION_SUPPRESSED` with reason for every drop; webhook reporter alerts on spikes. A "force-deliver" mode (`bypass_suppression=True`) for moderation+critical-ops intents.
- Digest assembly slow under load → digests run on a separate scheduled task (`core.runtime.tasks.spawn`), not in the delivery hot path.
- Cross-guild notification leakage → intents always carry `guild_id`; router refuses to deliver if `recipient.guild.id != intent.guild_id`.

**Implementation considerations.**
- Subsystems migrate to the router one at a time. XP first (levelup notifications), then Economy (daily reminders), then Moderation (warn DMs).
- The router has its own diagnostics: `!platform notifications` shows recent dispatch volume, suppression rates, digest backlog.

**Entry criteria.** Phase 6 complete.
**Exit criteria.**
- ≥3 subsystems route notifications via `notification_service.notify`.
- AST invariant blocks direct user-sends outside the service.
- `notification_audit` table populated; `!platform notifications` works.
- Wizard's subscription-toggle changes have observable effect on notification delivery within one cache TTL.

**User value.** Indirect but significant: opt-outs actually work; quiet hours work; digests reduce noise; visibility toggles ("hide me from leaderboard") become honored by every consumer automatically.

---

## Phase 7 — Setup Wizard + Participation Hub + Experience Modes

**Objective.** Ship the user-facing surface: `!setup` for operators (guild config), `/myprofile` for users (participation), Experience Modes for both. The wizard is no longer just an operator tool — it's the inhabited surface of both Track A (guild config) and Track B (participation).

**Architectural purpose.** Everything before this made these surfaces implementable as **thin** cogs. This phase wires the existing pieces (Schemas + Bindings + Participation + Drafts + Screens + Components + Diagnostics + Notification Routing + identity-validated subsystem registry) into coherent UX flows.

**Systems introduced.**

**Operator surface (Track A):**
- `disbot/cogs/setup_cog.py` (with `disbot/cogs/setup/` decomposition per the 400 LOC rule). Entry points:
  - `!setup` — top-level wizard
  - `!setup <subsystem>` — focused flow
  - `!setup repair` — guided fix for every `setup_health` finding
  - `!setup template <name>` — apply a named preset
- `disbot/cogs/setup/flow_orchestrator.py` — knows subsystem walk order via `_COMPILED_DEPENDENCY_ORDER` (line 546 of `subsystem_registry.py`) so e.g. economy is set up before mining.
- `disbot/cogs/setup/templates/` — starter presets: `community_default`, `gaming_minimal`, `moderation_focused`. Applied through the existing `governance/templates.py` AND `BindingMutationPipeline`.
- `disbot/views/setup/` — only **Screen specializations**, no new `BaseView` subclasses. Includes preset-picker, subsystem-grid landing, completeness overview, repair flow.
- One persistent anchor: `setup` resume affordance — survives restart, replays into the wizard via `panel_recovery.py`.

**User surface (Track B, NEW):**
- `disbot/cogs/participation_cog.py` (with `disbot/cogs/participation/` decomposition).
  - `/myprofile` — top-level participation hub for the invoking user
  - `/myprofile subscriptions` — focused subscription management
  - `/myprofile preferences` — focused preference editor
  - `/myprofile visibility` — focused visibility-intent toggles
  - `/myprofile reset` — opt out of all subsystems (one-button safety net)
- `disbot/cogs/participation/onboarding_orchestrator.py` — walks new users through opt-in choices on first interaction with the bot (or when invoked manually).
- `disbot/views/participation/` — Screen specializations for the user surface (subscription toggles, preference editors, visibility hub).
- One persistent anchor per active user: `participation` resume affordance — survives restart, scoped to `(guild, user)`.

**Experience Modes (cross-cutting, NEW):**
- `disbot/cogs/setup/experience_modes.py` — defines four canonical modes:
  - `MINIMAL` — opt-in only the smallest viable subsystem set; suppress all non-critical notifications; no advanced features visible.
  - `RECOMMENDED` — opt-in the curated default set; sensible notification defaults; standard UI density.
  - `FULL_EXPERIENCE` — opt-in everything available; full notification surface; all features visible.
  - `CUSTOM` — user-by-user / setting-by-setting selection.
- Each mode is a **preset over the participation schema** (Track B) and **a preset over the guild config schema** for guild-level modes. Same `apply_template`/`apply_preset` engine, different scope.
- Modes are surfaced in both flows: `!setup` lets operators set a guild-wide mode that becomes the default for new users; `/myprofile` lets users override.
- Modes are stored as a participation preference (`user_preferences.experience_mode`) and as a guild config setting (`setup.default_experience_mode`).

**Existing primitives reused / extended.**
- Everything from Phases 1–6.5.
- `disbot/governance/templates.py:apply_template` — extended (not duplicated) to accept setup-template payloads carrying governance overrides + binding values + participation defaults. Payload versioning: `v1` = governance-only (current), `v2` = + bindings, `v3` = + participation defaults. Existing pipeline-routing contract preserved.
- `disbot/core/runtime/panel_manager.py:get_or_render_panel` — used for the persistent `!setup` and `/myprofile` entry-point anchors.
- `disbot/core/runtime/message_anchor_manager.py:restore_anchors` — restores both anchors at startup (no special handling needed; the existing pattern works for both).
- `disbot/core/runtime/notification_router` (Phase 6.5) — `/myprofile reset` triggers a `bypass_suppression` notification confirmation.

**Dependencies.** Phases 1–6.

**Migration impact.**
- **DB migration `021_setup_templates.sql`** — extends `governance_templates.payload` schema to support `payload.version: "v2"` and `v3`. INV-I (idempotent migrations under advisory lock) covers this.
- **DB migration `021b_participation_indexes.sql`** — adds covering indexes on `user_participation`, `user_subscriptions`, `user_preferences` for the per-user dashboard query path.
- Identity surfaces: the `setup` and `participation` subsystem entries (added in Phase 5) are populated with entry_points + persistent_view + anchor surfaces. All 6 surfaces agree for both subsystems.

**Risks & mitigations.**
- Wizard performs writes outside the mutation pipelines (the trap) → AST invariant from Phase 3 blocks at CI for all three pipelines.
- Wizard/participation cog accumulates state → both cogs have **zero new tables**. All draft state in `runtime_session_state`; all committed state in tables owned by other subsystems or by the four participation tables from Phase 2b.
- Preset application partially fails → preset apply is a series of `ConfigDraft.commit`s; `CommitResult` retry-from-failed-step applies uniformly.
- Templates contain raw IDs from source guild → templates only contain **binding-shaped placeholders** ("a moderator role", "a logs channel"); the wizard prompts the operator to bind each placeholder. Cross-guild viability.
- Experience Modes drift apart between operator and user definitions → modes are defined in **one canonical file** (`disbot/cogs/setup/experience_modes.py`); both setup and participation flows consume the same definitions.
- User changes Experience Mode and loses prior custom prefs → `CUSTOM` mode is the only mode that does not overwrite existing user choices; switching to `MINIMAL`/`RECOMMENDED`/`FULL` warns and offers a "preserve my customizations" toggle before applying.
- New-user onboarding is overwhelming → `onboarding_orchestrator` ships defaulting to `MINIMAL` mode + a single "want more?" follow-up. No multi-step onboarding modal blocks first-time interaction.

**Implementation considerations.**
- `!setup` and `/myprofile` must run in partially-loaded state: if cog X failed to load (INV-J), both surfaces skip it but surface it in diagnostics as `unavailable`.
- Resumable drafts: persistent anchors keyed `(user, channel, "setup")` and `(user, channel, "participation")`. Pressing restores the most recent unfinished draft via `state_store.get_all`.
- `/myprofile` is intentionally **slash-command** (not prefix-command) — it's a per-user surface that benefits from Discord's slash-command UX (ephemeral by default, autocomplete, scoped to the invoking user).

**Entry criteria.** Phases 1–6.5 complete.
**Exit criteria.**
- `!setup` works end-to-end for ≥6 subsystems.
- `/myprofile` works end-to-end for ≥3 subsystems with participation schemas.
- ≥3 presets exist and apply successfully (one per Experience Mode + one community preset).
- All mutations traceable to `mutation_id`s in `governance_audit_log` + binding audit + participation audit.
- E2E tests in `tests/unit/cogs/test_setup_flow.py` and `tests/unit/cogs/test_participation_flow.py`.

**User value.** **Primary deliverable.** Admins use `!setup`; users use `/myprofile`; the platform's inhabited surface is live.

---

## Phase 7.5 — Resource Provisioning Runtime (NEW)

**Objective.** Promote channel/role management from hand-built panels to a declarative provisioning system. Setup packs become first-class: the wizard offers "create the channels and roles I need" as a one-button action backed by typed resource provisioning.

**Architectural purpose.** The existing channel/role panels (`disbot/views/channels/`, `disbot/views/roles/`, ~2300 LOC) are early provisioning groundwork. They show that the bot already creates and manages guild resources — but each panel is hand-coded against discord.py primitives. With Phase 1c's `ResourceRequirement` declarations, Phase 2c's `core/resources/` runtime, and Phase 4c's resource diagnostics, the platform has the typed substrate to make provisioning declarative. The wizard becomes the entry point: "this server is missing the recommended channels for moderation; create them?" — and the provisioning runtime executes against the schema.

**Systems introduced.**
- `disbot/core/resources/provisioning.py` — `ResourceProvisioner` orchestrator: takes a `ProvisioningPlan` (list of `ResourceRequirement` to fulfill) → builds a preview → on confirmation, creates channels/roles/categories via the `ResourceMutationPipeline` whose shell was introduced in P2a. This phase fills the pipeline with actual creation logic.
- `disbot/utils/db/resource_provisioning.py` — audit table for provisioned resources, so "undo last provisioning" is possible.
- `disbot/core/resources/setup_packs.py` — declarative bundles: "moderation pack" creates `mod-logs`, `mod-actions`, `appeals` channels under a `Moderation` category + binds them to the moderation subsystem in one atomic plan. **Setup packs integrate with P4.5 role provisioning**: a moderation pack creates the channels AND offers to provision the recommended `Moderator` / `Helper` roles via `role_provisioning.provision_role`. Packs are versioned and idempotent.
- `disbot/core/resources/repair_flows.py` — auto-repair runtime consuming `auto_repairable` findings from Phase 4c AND P4.5 `RoleHealthReport`. Repairs include: recreate-missing-channel, restore-bot-permissions, rebind-orphan-channel, reseed-default-role, provision-missing-governance-role.
- `disbot/core/resources/regeneration.py` — destructive companion: tear down and recreate a subsystem's resources from its declared requirements. Behind heavy confirmation; audited; reversible within one release.
- `disbot/core/resources/environment_aware_provisioning.py` — **environment-tier-aware** provisioning: a CANARY-tier guild may opt into beta setup packs; PRODUCTION guilds use only stable packs. Consumes feature flags from P2d.
- Channel/role panels are **refactored** to consume `provisioning.py` for create/delete operations. The visible UI stays similar; the underlying flow is now audited, typed, and undo-able.

**Existing primitives reused / extended.**
- `disbot/cogs/channel_cog.py` + `disbot/views/channels/` — refactored to consume `core/resources/provisioning`. The cog shrinks; views become Screen specializations consuming `ChannelSelector` and `BindingPanel`.
- `disbot/cogs/role_cog.py` + `disbot/views/roles/` — same refactor; `RoleSelector` becomes the primary primitive.
- `disbot/core/resources/discovery.py` (Phase 2c) — drives the provisioning preview.
- `disbot/services/resource_health_service.py` (Phase 4c) — surfaces `auto_repairable` findings consumed by `repair_flows`.
- `disbot/governance/templates.py` — extended in Phase 7 with `payload.v3`; this phase introduces `payload.v4` adding `resource_provisioning_plan` so cross-guild templates can carry "create these channels" instructions (with bot-permission probing on apply).

**Dependencies.** Phase 7.

**Migration impact.**
- DB migration `023_resource_provisioning_audit.sql` — audit and rollback table.
- AST invariant: channel/role creation outside `core/resources/provisioning.py` is a build failure. Existing direct `guild.create_text_channel(...)` calls in `channel_cog.py` are migrated; new code goes through the provisioner.
- Identity surfaces: unchanged.

**Risks & mitigations.**
- Bot tries to create resources it lacks permission to create → provisioner runs a permission probe before every plan; surfaces "you need to grant me X" findings instead of attempting and failing mid-plan.
- Provisioning duplicates existing channels → setup packs use idempotent matching by `(category, name, intent)`; existing matches are bound, not recreated.
- Mass-provisioning storms a guild's audit log → provisioning batches under `pg_advisory_lock` per guild + Discord rate-limit awareness via existing `live_update_scheduler` patterns.
- Cross-guild template apply creates channels in the wrong category → packs always require an operator confirmation step showing the **exact channels that will be created**; no silent provisioning.

**Implementation considerations.**
- Setup packs are the bridge between Phase 8 cross-guild templates and Phase 7 in-guild setup — the wizard offers "apply the X pack" as a one-button preset, but the underlying flow is the same `ConfigDraft + ResourceMutationPipeline` orchestration.
- Repair flows must be runnable headlessly from `!setup repair --auto` for finding tiers `auto_repairable` only; operator-required findings always require confirmation.

**Entry criteria.** Phase 7 complete.
**Exit criteria.**
- Channel/role panels refactored onto `core/resources/provisioning`.
- ≥2 setup packs (`moderation_essentials`, `economy_starter`) ship and apply successfully.
- `!setup repair --auto` resolves at least 80% of `auto_repairable` findings on a misconfigured test guild.
- `regeneration` flow demonstrably tears down and rebuilds a subsystem's resources in a sandbox guild.

**User value.** **Major user-visible deliverable.** "I joined the bot to a new server, what now?" gets a one-button answer. Existing servers get one-button repair. Setup packs replace 30-minute manual configuration with a 30-second confirmation.

---

## Phase 8 — Cross-guild, AI/Automation, and the Guild Operating System Direction

**Objective.** Validate that the abstractions from Phases 1–7.5 are actually general by extending them — without modifying core primitives — for future subsystem categories. Explicitly orient toward the **Guild Operating System** direction.

**Architectural purpose.** **Deliberate stress test.** If Phase 8 requires changes to `SubsystemSchema`, `ParticipationSchema`, `Screen`, `core/resources/`, or the notification router, the abstractions were wrong; if it's purely declarative addition, they're right.

**Systems introduced.**
- `BindingKind` extensions: `webhook`, `external_provider`, `composite` (multi-binding-as-one). Used for AI subsystem onboarding ("AI listens to channel X + summoned by role Y + fallback admin role Z").
- Cross-guild template registry — extension of `governance_templates` with a `share_scope` field (`private | unlisted | public`). Templates carry **all four payload kinds**: governance overrides, binding placeholders, participation defaults, resource-provisioning plans (Phase 7.5 `payload.v4`).
- `BindingSpec.derived` — a binding whose value is computed from others (e.g. "automation log channel defaults to moderation log channel"). Composable across subsystems.
- A second persistent panel under the `setup` subsystem: the **automation onboarding hub** — same `Screen` infrastructure, different `flow_orchestrator`.
- **Cross-guild participation patterns** (NEW): future-facing primitive. A user opts into a *pattern* (e.g. "I want XP notifications on all my servers") that propagates via a federation event to compatible guilds the user is on. Stays opt-in per guild; never forces participation.
- **Guild OS surface area** (NEW): explicit articulation in `docs/architecture.md` that SuperBot is now structured as a host for subsystems, with documented expectations for what "being a subsystem" means in this architecture (schema declarations, ownership boundaries, identity contract surfaces, etc.). The doc becomes the contributor onboarding manual for the OS direction.
- **Domain event + policy engine reservation** (NEW, architectural-space only): the roadmap reserves namespaces and contracts for future event-driven orchestration without implementing it now. Specifically:
  - `core/events_catalogue.py` is extended with **placeholder domain event categories** (`DomainEvent.ConfigChanged`, `DomainEvent.ParticipationUpdated`, `DomainEvent.BindingUpdated`, `DomainEvent.FeatureFlagChanged`, `DomainEvent.RoleProvisioned`) — none of these have publishers yet, but the catalogue claims the namespace so future orchestration can subscribe without re-cataloguing.
  - `docs/decisions/` gets an ADR explicitly **deferring** a full policy engine, stating: "Future workflow / automation / cross-subsystem orchestration will subscribe to domain events listed above. This phase does not build a policy engine; it claims the architectural space."
  - No `PolicyRule` runtime, no DSL, no rule store ships in P8. The reservation exists so a later phase can build it without re-litigating naming or ownership.

**Existing primitives reused.** Everything from Phases 1–7.5. **Zero new infrastructure modules.**

**Dependencies.** Phase 7.5.

**Migration impact.** Small DB migration `022_template_share_scope.sql`. Identity surfaces unchanged.

**Risks & mitigations.**
- Cross-guild template sharing creates a privacy surface → `share_scope` controls visibility; ID-shaped values always replaced by placeholders during export; resource-provisioning plans always show a confirmation preview on apply.
- Composite bindings explode in complexity → limit to 2 levels of derivation; AST invariant prevents recursive bindings.
- Cross-guild participation creates surveillance-pattern risks → patterns are user-initiated only; the user can revoke per-guild; the bot never auto-propagates participation across guilds without explicit per-guild confirmation.
- "Guild OS" framing creates scope creep → the OS direction is **architectural**, not a product positioning. Cog authors don't need to learn new terminology; only platform contributors do.

**Implementation considerations.**
- Treat Phase 8 as the **abstraction audit** moment. Before shipping it, review every primitive added in Phases 1–7.5 and ask: "Does this primitive bend, or does it generalize?" If anything bends to fit Phase 8, fix it before shipping Phase 8.

**Entry criteria.** Phase 7.5 in production.
**Exit criteria.**
- An automation cog can be added with **only** a schema + presets, no UI code.
- One AI tooling preset works end-to-end.
- Cross-guild preset sharing operational.
- Cross-guild participation pattern demo works (e.g. "XP notifications everywhere I am") via federation events.
- `docs/architecture.md` includes a "Guild OS direction" section codifying the platform's evolved framing.

**User value.** Long-tail: enables future feature velocity. Limited immediate visibility. Validates the entire roadmap.

---

## Architectural Traps Avoided

1. **Wizard mutating config directly (INV-E violation).** Phase 3 makes `ConfigDraft.commit` the ONLY commit surface. Phase 7 ships with AST invariant blocking direct pipeline calls from `cogs/setup/` and `cogs/participation/`.
2. **Setup state in cogs (layering violation).** Drafts live in `runtime_session_state` (platform-owned). Cogs never carry session-scoped state.
3. **Wizard owning subsystem schemas (ownership inversion).** Schemas registered by subsystem cogs in `cog_load`; Phase 6 invariant enforces. The wizard reads schemas; it never writes them.
4. **Raw-ID settings migrated without backfill plan.** Phase 2 includes explicit backfill with feature-flag cutover under `pg_advisory_lock`.
5. **6th identity surface added too early.** Phase 6 is gated on Phases 1–5 to avoid validator thrash during early iteration.
6. **Schema drift from registry capabilities.** Phase 1 startup validator catches; failure raises during `validate_registry()`.
7. **Templates carrying source-guild IDs (cross-guild leak).** Phase 8 placeholder model required from day one; never store raw IDs in shareable templates.
8. **Persistent setup views surviving an unfinished flow.** Setup screens ephemeral by design (Phase 5); only the entry-point anchor is persistent.
9. **PersistentView restoration trying to restore wizard screens.** Phase 5 makes screens ephemeral; drafts persist via `runtime_session_state`, UI does not.
10. **Adding a "settings cog" style command.** Out of scope. The wizard IS the configuration runtime.
11. **Collapsing participation, permissions, visibility, notifications, and preferences into one "user settings" object.** Phase 1b mandates separate `subscriptions / visibility_intents / notification_intents / preference_specs` fields; Phase 2b mandates four separate tables. AST + structural test in Phase 1b enforces.
12. **Mixing per-user state into the guild config cache.** Phase 2b adds a sibling `user_config` cache with its own keyspace and TTL. Cross-write between the two caches is forbidden; AST invariant prevents.
13. **Subsystems sending notifications directly via `member.send`.** Phase 6.5 introduces `notification_service.notify`; AST invariant in Phase 6.5 blocks direct user-targeted sends outside the service.
14. **Default opt-in for participation (especially for AI / automation / tournaments).** Phase 1b requires `requires_optin=True` for these categories; the participation schema validator at startup rejects subsystems that violate the rule. Notifications default suppressed until explicit opt-in via `subscriptions`.
15. **Channel/role creation outside the resource provisioning runtime.** Phase 7.5 introduces `ResourceMutationPipeline`; AST invariant blocks direct `guild.create_*` calls outside `core/resources/provisioning.py`.
16. **Help / dashboard / setup becoming three separate UI systems.** Phase 5c collapses them into one navigation framework with one component registry; ADR requirement for new top-level UI tracks.
17. **Cross-guild participation auto-propagation (surveillance pattern).** Phase 8 patterns require explicit per-guild user confirmation; never silently propagate.
18. **Experience Modes becoming two separate definitions (operator vs user).** Phase 7 mandates a single `experience_modes.py` consumed by both surfaces.
19. **Resource Unification breaking existing channel/role panels.** Phase 2c keeps selector public APIs stable; Phase 7.5 refactors panels to consume the new runtime without changing UI behavior.
20. **Migration to bindings/participation/resources running concurrently and stepping on each other.** Phase 2 sub-phases ship in strict sequence (2a Resources → 2b Bindings → 2c Participation → 2d Feature Flags) with independent feature flags; one cog migrates one sub-phase at a time.
21. **UI surfaces built before runtime primitives.** Tier ordering is binding. P5 cannot start before P4.5; P7 cannot start before P5; P7.5 cannot start before P7. AST + review enforce; any PR introducing UI under `cogs/setup/` or `cogs/participation/` while the corresponding primitives are absent fails review.
22. **Feature flags becoming a junk drawer.** New flags require an ADR entry; flags must declare a removal date or a permanent rationale; periodic audit removes resolved flags.
23. **Delegation back-channels bypassing governance audit.** P4.5 delegations are always time-bounded, tier-bounded, and audited at grant + use + revoke. AST invariant verifies delegation creation goes through `governance/delegation.py`.
24. **Role provisioning creating roles the bot can't manage.** P4.5/P7.5 provisioner runs permission probes before plan execution; never attempts to create roles above the bot's highest role position.
25. **Cross-domain cache writes.** Each domain owns its cache exclusively (per the Core Platform Runtime Boundaries table). AST invariant blocks cache writes outside the owning module.
26. **Domain events implemented prematurely.** P8 reserves the catalogue namespace but explicitly does NOT build a policy engine. Future workflow systems subscribe to placeholder events; building the engine itself is out of scope for this roadmap.
27. **Governance growing into a god-object.** P4.5 splits governance into clear modules (`role_provisioning`, `role_diagnostics`, `access_scopes`, `delegation`) rather than expanding `governance/__init__.py`. ADR required for any new top-level governance module.

---

## Cross-cutting Concerns

| Concern | Where addressed |
|---|---|
| **Audit logging** | Every commit flows through `GovernanceMutationPipeline`, `BindingMutationPipeline`, `ParticipationMutationPipeline`, `ResourceMutationPipeline`, or `notification_router`; all write to audit tables with `mutation_id`. `CommitResult` aggregates across pipelines for multi-pipeline drafts. |
| **Metrics** | Prometheus families: `setup_health_*`, `binding_resolution_*`, `participation_*`, `subscription_*`, `notification_*`, `visibility_filtered_*`, `resource_orphan_*`, `setup_flow_completion_total{flow,outcome}`, `experience_mode_distribution_total{mode}`. All via `services/metrics.py`. |
| **Governance** | All mutation paths run through existing pipelines + the three new ones. Phase 3's AST invariant prevents bypass. The three new pipelines share the 6-step contract from `GovernanceMutationPipeline` (`validate → authority → read-old → write → invalidate → emit`); authority models differ (governance: moderator+; participation: self-or-moderator+; resources: moderator+; bindings: moderator+). |
| **Caching architecture** | Three sibling caches: `guild_config` (existing), `user_config` (NEW, Phase 2b), `resource_validation_cache` (NEW, Phase 2c). All version-stamped, all TTL'd, all invalidated via EventBus on their respective mutation events. Cardinality controls: `guild_config` unbounded (low guild count); `user_config` LRU-bounded at ~50k entries; `resource_validation_cache` TTL-only (bounded by guild resource count). Cross-cache writes forbidden by AST invariant. |
| **Notification routing** | Phase 6.5 introduces the centralized router. Subsystems never call `member.send` directly; routing handles eligibility, suppression, digesting, rate limiting, audit. AST invariant blocks direct user-targeted sends. |
| **Testing** | Phase 1 → `tests/unit/schema/` (config + participation + resource); Phase 2 → `tests/unit/runtime/test_bindings.py`, `test_participation_state.py`, `tests/unit/resources/`; Phase 4 → `tests/unit/services/test_setup_health.py`, `test_participation_health.py`, `test_resource_health.py`; Phase 6.5 → `tests/unit/runtime/test_notification_router.py`; Phase 7 → `tests/unit/cogs/test_setup_flow.py`, `test_participation_flow.py`; Phase 7.5 → `tests/unit/resources/test_provisioning.py`. Existing AST invariant pattern (INV-F, INV-G shape) extended across all new layers. |
| **Migration safety** | Phase 2 backfills are the only data-touching steps; each runs under `pg_advisory_lock` with independent feature flags (`BINDINGS_PRIMARY`, `PARTICIPATION_ENABLED`, `RESOURCES_UNIFIED`). Sub-phases sequenced 2a → 2c → 2b to minimize concurrent risk. INV-I unchanged. |
| **STRICT mode** | Identity contract extension in Phase 6 lands as `warn_only` first, promoted to `auto_healable` only after production validation. New surfaces (participation schemas, resource requirements) follow the same gradient. |
| **Hot reload** | Diagnostics registry already supports re-registration; schema, capability, participation, resource decorators inherit this behavior. Component registry from Phase 5b is also hot-swappable. |
| **Documentation** | `docs/architecture.md` upgrade from 5→6 surface contract in Phase 6; new "Guild OS direction" section in Phase 8. `docs/ownership.md` adds bindings + drafts + participation + resources + notifications ownership rows across Phases 2/3/6.5/7.5. `docs/decisions/` gets ADR entries for: binding migration (P2a), participation runtime (P2b), unified resources (P2c), notification routing (P6.5), provisioning runtime (P7.5), Guild OS direction (P8). |
| **Privacy** | Participation health metrics (4b) are aggregate-only at the guild scope; per-user inspection requires moderator+ authority and is audited. Cross-guild participation (P8) requires explicit per-guild user confirmation. Visibility intents are user-controlled and respected by every consumer via the central filter. |
| **Discoverability** | All three new admin command surfaces (`!platform participation`, `!platform resources`, `!platform notifications`) registered under the existing `!platform <name>` shape from S2.5. New user surface (`/myprofile`) is one slash command with subcommands. |

---

## Critical Files

### Modified
- `disbot/utils/settings_keys.py` → `disbot/utils/settings_keys/` package (P0)
- `disbot/utils/guild_config_accessors.py` (P0 helper, P2a binding accessors)
- `disbot/utils/subsystem_registry.py` (P1 capability validator, P6 6th surface)
- `disbot/governance/templates.py` (P7 v2/v3 payload, P7.5 v4 payload)
- `disbot/governance/writes.py` (reference shape; not modified)
- `disbot/core/runtime/guild_resources.py` (P2a `resolve_binding` generalization; deprecated in favor of `core/resources/` shim)
- `disbot/core/runtime/interaction_router.py` (P5 `setup`, `participation`, `help`, `dashboard` prefix registration)
- `disbot/core/runtime/message_anchor_manager.py` (P7 setup + participation anchors)
- `disbot/core/runtime/component_registry.py` (P5b expansion with platform components)
- `disbot/cogs/help_cog.py` (P5c rewrite to consume Screen framework)
- `disbot/cogs/channel_cog.py` (P7.5 refactor onto `core/resources/provisioning`)
- `disbot/cogs/role_cog.py` (P7.5 refactor onto `core/resources/provisioning`)
- `disbot/views/channels/` (P7.5 refactor to Screen specializations)
- `disbot/views/roles/` (P7.5 refactor to Screen specializations)
- `disbot/views/selectors/channel.py`, `role.py` (P2c refactored to consume `core/resources/`)
- `docs/architecture.md` (P2/P3 ownership rows; P6 contract upgrade; P8 "Guild OS direction" section)
- `docs/ownership.md` (P2/P3/P6.5/P7.5 layering)

### Deleted
- `disbot/utils/onboarding_profiles.py` (P0 dead code removal)

### Added — Phase 1 (Schema protocols)
- `disbot/core/runtime/subsystem_schema.py` (P1a)
- `disbot/core/runtime/subsystem_capabilities.py` (P1a)
- `disbot/core/runtime/participation_schema.py` (P1b NEW)
- `disbot/core/runtime/participation_capabilities.py` (P1b NEW)
- `disbot/core/runtime/resource_specs.py` (P1c NEW)
- `disbot/governance/role_templates.py` (P1d NEW)
- `disbot/governance/permission_tiers.py` (P1d NEW)
- `disbot/governance/scopes.py` (P1d NEW)
- `disbot/core/runtime/feature_flags.py` (P1d declarations; P2d runtime)

### Added — Phase 2 (State Storage) [Sub-phases reordered: 2a=Resources, 2b=Bindings, 2c=Participation, 2d=Feature Flags]
- `disbot/core/resources/` package (P2a — moved earlier) — `types.py`, `discovery.py`, `role_service.py`, `channel_service.py`, `mutation.py`, `__init__.py`
- `disbot/utils/db/resource_cache.py` (P2a NEW)
- `disbot/core/runtime/bindings.py` (P2b)
- `disbot/utils/db/bindings.py` (P2b)
- `disbot/core/runtime/participation_state.py` (P2c NEW)
- `disbot/utils/db/participation.py` (P2c NEW)
- `disbot/utils/user_config_accessors.py` (P2c NEW)
- `disbot/core/runtime/user_config.py` (P2c NEW)
- `disbot/utils/db/feature_flags.py` (P2d NEW)
- `disbot/utils/db/environment_tiers.py` (P2d NEW)
- `disbot/services/feature_flag_service.py` (P2d NEW)

### Added — Phase 3+ (Drafts, Diagnostics, Governance Runtime, Components)
- `disbot/core/runtime/config_drafts.py` (P3)
- `disbot/services/setup_health_service.py` (P4a)
- `disbot/services/participation_health_service.py` (P4b NEW)
- `disbot/services/resource_health_service.py` (P4c NEW)
- `disbot/governance/role_provisioning.py` (P4.5 NEW)
- `disbot/governance/role_diagnostics.py` (P4.5 NEW)
- `disbot/governance/access_scopes.py` (P4.5 NEW)
- `disbot/governance/delegation.py` (P4.5 NEW)
- `disbot/services/access_control_service.py` (P4.5 NEW)
- `disbot/core/runtime/screens.py` (P5a)
- `disbot/core/runtime/screen_navigator.py` (P5a)
- `disbot/core/runtime/components/` package (P5b NEW)
- `disbot/views/help/`, `disbot/views/dashboard/`, `disbot/views/diagnostics/`, `disbot/views/governance/` (P5c NEW)

### Added — Phase 6.5 (Notification Routing)
- `disbot/core/runtime/notification_router.py` (P6.5 NEW)
- `disbot/services/notification_service.py` (P6.5 NEW)
- `disbot/core/runtime/visibility_filter.py` (P6.5 NEW)
- `disbot/core/runtime/notification_digest.py` (P6.5 NEW)
- `disbot/core/runtime/notification_suppression.py` (P6.5 NEW)

### Added — Phase 7+ (User-facing surfaces)
- `disbot/cogs/setup_cog.py` + `disbot/cogs/setup/` (P7)
- `disbot/views/setup/` (P7)
- `disbot/cogs/participation_cog.py` + `disbot/cogs/participation/` (P7 NEW)
- `disbot/views/participation/` (P7 NEW)
- `disbot/cogs/setup/experience_modes.py` (P7 NEW)
- `disbot/core/resources/provisioning.py` (P7.5 NEW)
- `disbot/core/resources/setup_packs.py` (P7.5 NEW)
- `disbot/core/resources/repair_flows.py` (P7.5 NEW)
- `disbot/core/resources/regeneration.py` (P7.5 NEW)
- `disbot/utils/db/resource_provisioning.py` (P7.5 NEW)

### DB Migrations [renumbered after P2 sub-phase reorder]
- `020a_resource_registry.sql` (P2a — moved earlier) — resource validation cache
- `020b_subsystem_bindings.sql` (P2b)
- `020c_user_participation.sql` (P2c) — 4 sibling tables
- `020d_feature_flags.sql` (P2d NEW) — feature_flag_state + environment_tier tables; seed owner-guild + test-guild tiers
- `021_setup_templates.sql` (P7)
- `021b_participation_indexes.sql` (P7)
- `022_template_share_scope.sql` (P8)
- `023_resource_provisioning_audit.sql` (P7.5)
- `024_notification_audit.sql` (P6.5)
- `024a_governance_delegations.sql` (P4.5 NEW)
- `024b_role_template_bindings.sql` (P4.5 NEW)

---

## Architectural Alignment Validation

A final pre-implementation check. Each of the 10 critical platform rules is mapped to the specific phase(s), invariant(s), and trap entry where it is enforced. If any cell is empty, the plan is not ready.

| # | Rule | Where it lands | AST / runtime enforcement | Trap reference |
|---|---|---|---|---|
| 1 | **UI surfaces are consumers, not owners** | P5 (UI framework) precedes P7 (wizard). P7 cogs described as thin dispatchers composing components from P5b. Architectural Trajectory section affirms. | AST invariant P5: no `discord.ui.View` subclasses under `cogs/setup/` or `cogs/participation/`; new components require ADR. | Traps #1, #2, #21 |
| 2 | **Cross-domain mutations through orchestration/runtime services** | Every domain has a typed mutation pipeline: `GovernanceMutationPipeline`, `BindingMutationPipeline`, `ParticipationMutationPipeline`, `ResourceMutationPipeline`, `RolloutMutationPipeline`, `notification_service.notify`. All share the 6-step contract from `governance/writes.py`. | AST invariant P3: no direct `*MutationPipeline` calls from `cogs/setup/` or `cogs/participation/`. AST invariant P6.5: no direct `member.send`/`user.send` outside `notification_service`. AST invariants for P2b/P2c block raw writes outside services. | Traps #1, #2, #13, #15 |
| 3 | **Roles/channels/categories unified as resource primitives** | P2a introduces `core/resources/` with `GuildResource` base + `ChannelResource`/`RoleResource`/`CategoryResource`/`ThreadResource`. Selectors refactored in P2a to consume `role_service`/`channel_service`. Phase 7.5 provisions all kinds through the same `ResourceMutationPipeline`. | AST invariant P2a → P7.5: no direct `guild.create_*` calls outside `core/resources/provisioning.py` (warn in P2a, error in P7.5). | Trap #15 |
| 4 | **Participation, permissions, notifications, visibility, preferences remain separate** | P2c creates four sibling tables: `user_participation`, `user_subscriptions`, `user_preferences`, `user_visibility_overrides`. P6.5 adds notification routing as its own domain. P4.5 owns permissions/governance. P1b's `ParticipationSchema` enforces separate field lists. | Structural test `tests/unit/schema/test_participation_separation.py` asserts no `ParticipationSchema` field is a single `dict[str, Any]` catch-all. AST invariant P2b/P2c blocks raw writes outside owning pipelines. | Trap #11, #12 |
| 5 | **Governance is platform-level, not Discord-role-level** | P1d declares `PermissionTier`, `GovernanceScope`, `RoleTemplate` at the platform layer. P4.5 introduces `access_control_service.can(member, scope)` overlaying Discord permissions + governance tier + delegation + feature flag. Discord roles map to `PermissionTier` via P4.5 role-template bindings — they don't ARE the tier. | AST invariant P4.5: delegations time-bounded ≤ 30 days; admin commands must declare access scopes; role provisioning only via `governance/role_provisioning.py`. | Trap #23, #24, #27 |
| 6 | **Reusable selectors/panels/navigation completed before wizard assembly** | Tier ordering: P5a (Screen) → P5b (Component Registry) → P5c (Unification) → P7 (Wizard). P5b explicitly states "lands before any wizard / dashboard / participation surface." | AST invariant P5: new `discord.ui.View` in `cogs/setup/`/`cogs/participation/` is a build failure. New components require ADR. | Trap #21 |
| 7 | **Feature rollout/environment isolated from subsystem business logic** | P1d declarations for `FeatureFlag` / `EnvironmentTier` / `RolloutPolicy`. P2d storage + `RolloutMutationPipeline` (authority: platform-owner tier only, defined in P1d). Subsystems DECLARE flags; they don't OWN flag state. Cogs query via `feature_flags.is_enabled(...)` — a read-only interface. | AST invariant P2d: no new env-var-only gates outside an explicit allowlist. New gates must be `FeatureFlag` declarations. ADR required for each flag with removal date or permanent rationale. | Trap #22 |
| 8 | **Diagnostics and provisioning remain first-class platform concerns** | P4 (Diagnostics + Health) is its own Tier-4 phase with three sub-phases (Setup, Participation, Resource). P7.5 (Resource Provisioning Runtime) is its own Tier-7 phase. Both register self-providers; both produce typed reports consumed by repair flows. | Diagnostics findings consumed by P7.5 repair flows via the `auto_repairable` finding-tier classification. Provisioning is core/resources/, not a cog. | Trap #2 |
| 9 | **Avoid cog-local reinvention of runtime infrastructure** | Every primitive (session_manager, scope_locks, navigation_stack, persistent_views, message_anchor_manager, guild_config, user_config, feature_flags, notification_router, screens, components) lives under `core/runtime/` or `core/resources/`. Cogs import them; cogs never own them. AST invariant blocks cog-local re-implementations. | AST invariants for: no naked `asyncio.create_task` (INV-K existing), no raw `defer` (INV-L existing), no raw `set_setting` on binding keys (P2b), no raw user-table writes (P2c), no raw flag mutation (P2d), no raw create_* (P2a→P7.5), no raw user.send (P6.5). | Traps #2, #3, #10, #13, #15, #25 |
| 10 | **Preserve inside-out platform evolution** | Inside-Out Implementation Strategy section flags this as a "Hard Constraint." Tiered dependency graph (Tier 1 Foundations → Tier 7 Provisioning) is binding. Trap #21 explicitly forbids inverting tier order. Architectural Trajectory section affirms wizard as inhabited UI, not runtime. | Tier ordering enforced by phase entry criteria: each phase declares "Phase X complete" as an entry requirement. PR review enforces. AST invariant P5 prevents UI under cogs/setup/cogs/participation/ until P5b lands. | Trap #21 |

### Dependency Ordering Audit

The seven tiers, each line below validated against the phase definitions above:

1. **Tier 1 (P0, P1)** — declarations only, no runtime. Cleanly precedes everything.
2. **Tier 2 (P2)** — **resources before bindings before participation before flags** (P2a → P2b → P2c → P2d). Sub-phase reorder reflects the dependency reality:
   - 2b consumes `core/resources/discovery` from 2a ✓
   - 2c references binding-shaped subscription targets that resolve via 2b → 2a ✓
   - 2d gates Tier 4+ but does not itself depend on 2a/b/c structurally — it lands last to bootstrap rollout for everything that follows ✓
3. **Tier 3 (P3)** — Drafts consume Tier 1 schemas + Tier 2 pipelines. Cleanly follows. ✓
4. **Tier 4 (P4, P4.5, P6, P6.5)** — sequenced internally as Diagnostics → Governance Runtime → Identity Contract → Notification Routing.
   - P4 needs P1 schemas + P2 statuses ✓
   - P4.5 needs P4 (diagnostics for `RoleHealthReport`), P1d (RoleTemplate), P2a (role_service), P2d (feature flags for environment-aware access) ✓
   - P6 needs P5 stability before promoting schema validation to a 6th surface ⚠ — see note below
   - P6.5 needs P6 (identity contract validates declared intents), P2c (participation state for subscription lookups), P4.5 (access_scopes for "force-deliver bypass" authority) ✓
5. **Tier 5 (P5)** — UI framework consumes everything beneath. P5a → P5b → P5c. Cleanly follows. ✓
6. **Tier 6 (P7)** — wizard assembly consumes Tier 5 framework. ✓
7. **Tier 7 (P7.5, P8)** — provisioning runtime fills the `ResourceMutationPipeline` shell from P2a; cross-guild + AI + Guild OS direction validate the abstractions. ✓

**Note on P6 timing (the one place to read carefully).** P6 (Identity Contract 6th Surface) lands inside Tier 4 *between* P4.5 and P6.5 in the dependency graph above, but its **entry criterion** is "Phase 5 complete" because the contract validates that schemas have a rendering target — and the rendering target is P5. This is a forward-reaching dependency: P6 sits at Tier 4 in the conceptual layering (it's a guardrail, not UI) but executes after P5 in calendar order. To resolve the ambiguity: **execution order is P0 → P1 → P2 → P3 → P4 → P4.5 → P5 → P6 → P6.5 → P7 → P7.5 → P8.** P6 promotes from warn-only to enforced after P5 stabilizes; until then, the identity contract operates on the existing 5 surfaces and the 6th surface findings are warn-only.

### Runtime Ownership Boundary Audit

Cross-referenced against the **Core Platform Runtime Boundaries** table (lines 60–104):

| Domain | Owner package | Mutation authority | Cache authority | Cross-domain access |
|---|---|---|---|---|
| Resources | `core/resources/` | `ResourceMutationPipeline` | `resource_validation_cache` | Read-only via `discovery`, `role_service`, `channel_service` |
| Bindings | `core/runtime/bindings.py` | `BindingMutationPipeline` | `guild_config` (binding namespace) | Read via `guild_config_accessors.get_binding` |
| Participation | `core/runtime/participation_state.py` | `ParticipationMutationPipeline` | `user_config` (sibling cache) | Read via `user_config_accessors` |
| Governance | `governance/` + P4.5 modules | `GovernanceMutationPipeline` + `delegation.py` | `governance/cache.py` | Read via `access_control_service.can` |
| Feature Flags | `core/runtime/feature_flags.py` | `RolloutMutationPipeline` | `feature_flag_cache` | Read via `feature_flags.is_enabled` |
| Notifications | `core/runtime/notification_router.py` | `notification_service.notify` | (stateless) | (none — terminal layer) |
| Diagnostics | `services/*_health_service.py` | (read-only providers) | (on-demand snapshots) | Read via `diagnostics_service.snapshot` |
| Drafts | `core/runtime/config_drafts.py` | `ConfigDraft.commit` → domain pipelines | `runtime_session_state` | Terminal commit dispatcher |
| UI | `core/runtime/screens.py` + `components/` | (stateless) | (stateless) | All reads via domain accessors; all writes via `ConfigDraft.commit` |

**Boundary violations to watch for during implementation** (each is also an AST invariant target):
- Resource access outside `core/resources/` (Track C inversion)
- Binding writes outside `BindingMutationPipeline` (governance INV-E parallel)
- Participation writes outside `ParticipationMutationPipeline`
- Flag mutations from anywhere except `feature_flag_service` (platform-owner tier only)
- Notification delivery via `member.send` outside `notification_service`
- Cache writes by any module other than the cache owner

### Reusable Primitive Extraction Audit

Every reusable primitive lands in a Tier-1, Tier-2, or Tier-3 phase — never inside a Tier-5 surface or a Tier-6 cog. Inventory:

| Primitive | Owner phase | Reusing phases |
|---|---|---|
| `TypedAccessor[T]` | P0 | P2b, P2c, P2d (all typed accessor families) |
| Schema registry pattern | P1a | P1b, P1c, P1d, P2d (every schema kind reuses the pattern) |
| `GovernanceMutationPipeline` 6-step contract | governance/writes (existing) | P2a, P2b, P2c, P2d, P4.5, P6.5 |
| `scope_locks.lock_for` | existing | all four new mutation pipelines |
| `core/resources/` runtime | P2a | P2b, P4c, P4.5, P5b, P7, P7.5 |
| `feature_flags.is_enabled` | P2d | P4.5, P6.5, P7, P7.5, P8 |
| `ConfigDraft` primitive | P3 | P7, P7.5 (and any future multi-step flow) |
| `summarize_findings` tier model | existing | P4a, P4b, P4c, P4.5 reports; P5 `DiagnosticsPanel` |
| `Screen` + component registry | P5a + P5b | P5c (help/dashboard/diagnostics/governance), P7, P7.5 |
| `notification_service.notify` | P6.5 | every cog with user-targeted messages |
| Experience Modes | P7 | P7 (operator + user surfaces), preset library |
| Setup packs | P7.5 | P8 cross-guild template applies |

If a phase would otherwise introduce a one-off primitive used only by itself, the plan instead defers that primitive to a foundational phase or marks it as non-reusable in the phase description. No primitive lands inside a Tier-6 or Tier-7 surface for reuse elsewhere.

---

## Architectural Trajectory

The phasing above is not a feature plan — it is the **execution sequence for a platform reorientation**. Read across the tiers and the final shape becomes visible:

- **The wizard is the inhabited UI layer over the platform runtime, not the runtime itself.** By the end of Phase 7, `setup_cog` and `participation_cog` together contain almost no logic — they are thin dispatchers composing screens that compose components that read from typed accessors that resolve through mutation pipelines into domain-owned tables. Every line of new "wizard" code lands in a platform domain, not in a cog.
- **Subsystems are guests of a platform runtime.** A new subsystem joins by declaring four schemas (config, participation, resource requirements, governance/rollout) in `cog_load`. The platform handles bindings, drafts, diagnostics, routing, UI, provisioning, and identity-contract validation. Cogs implement domain logic; everything else is platform-managed.
- **The runtime is dual-scope.** Guild operator state and per-user participation state are peers, not parent-and-child. Both have schemas, mutation pipelines, caches, diagnostics, and surfaces. Neither one is "the configuration"; both are runtime state with separate authority models.
- **Resources are first-class primitives.** Channels and roles are not Discord objects we look up ad-hoc; they are typed `GuildResource` instances with status, discovery, validation, and provisioning paths. The `core/resources/` package is the single point of contact between platform code and Discord's primitives.
- **Governance is access control, not just visibility.** Beyond the existing visibility/cleanup overrides, governance now owns delegated administration, environment-tiered permissions, role-template provisioning, and a unified `access_control_service.can(member, scope)` query. Discord permissions remain the substrate; governance is the layer that maps them to platform-level capabilities and scopes.
- **Feature flags + environment tiers gate every later phase.** Staged rollouts, canary environments, and beta access are infrastructure-level, not feature-level. Every phase from P4 onward ships behind a typed flag; the platform-owner tier controls flag mutations.
- **The UI is a framework, not a collection of cogs.** Help, setup, dashboards, diagnostics, governance admin, participation hub, and provisioning all share the same `Screen` engine, the same component registry, the same navigation stack. Adding a new control plane is a matter of registering a flow, not authoring a new UI track.
- **Domain events reserve future orchestration capacity.** No policy engine ships here; the catalogue space is claimed so future automation can subscribe without re-litigating naming.

The roadmap delivers SuperBot as a **Guild Operating System**: a single-process runtime that hosts subsystems, manages their per-guild and per-user lifecycle, routes notifications through suppression and digest layers, provisions guild resources from declarative packs, validates state through continuous diagnostics, and surfaces all of it through one unified UI framework. The "setup wizard" the user typed at the start of this conversation is the most visible inhabited surface of that OS — but the lasting value is the OS underneath, against which every future subsystem (automation, AI tooling, tournaments, analytics, cross-guild federation) is a straightforward declarative addition.

---

## Verification

Each phase has independent verification gates. End-to-end the roadmap is validated by:

1. **Per-phase exit criteria** — every phase has explicit pass/fail gates listed above.
2. **Identity contract validation at startup** — `validate_identity_contract()` runs every boot (`disbot/bot1.py:main`); STRICT mode (`IDENTITY_CONTRACT_STRICT=1`) aborts on findings. Extended to 6 surfaces in Phase 6.
3. **AST invariants** in `tests/unit/invariants/`:
   - P0: no imports from legacy flat `settings_keys` path
   - P2a: no direct `guild.create_text_channel`/`create_role`/`create_category` calls outside `core/resources/provisioning.py` (lands as warn here; promotes to error in P7.5)
   - P2b: no raw `set_setting` on binding-typed keys
   - P2c: no raw writes to user_participation/user_subscriptions/user_preferences/user_visibility_overrides outside `services/` or `ParticipationMutationPipeline`
   - P2d: no new env-var-only feature gates outside an explicit allowlist; new gates must be declared `FeatureFlag` objects
   - P3: no direct `*MutationPipeline` calls from `cogs/setup/` or `cogs/participation/`
   - P4.5: every admin command corresponds to a declared access scope; delegations time-bounded ≤ 30 days; no role provisioning outside `governance/role_provisioning.py`
   - P5: no `discord.ui.View` subclasses under `cogs/setup/` or `cogs/participation/`; new components require ADR
   - P6: every non-internal panel subsystem has a config schema or `has_setup: False`; every user-facing cog has a participation schema or `has_participation: False`; every panel-bearing subsystem has resource requirements; every subsystem declaring administrative commands has access-scope declarations
   - P6.5: no direct `member.send`/`user.send` calls outside `services/notification_service.py` (allowlist for OOB error reporting)
4. **Structural tests**:
   - `tests/unit/schema/test_participation_separation.py` — no `ParticipationSchema` field is a single `dict[str, Any]` masquerading as everything (P1b)
   - `tests/unit/runtime/test_user_config_isolation.py` — `guild_config` and `user_config` never share keyspace (P2b)
5. **E2E tests**:
   - `tests/unit/resources/test_discovery.py` — resource enumeration, status validation (P2a)
   - `tests/unit/resources/test_role_service.py`, `test_channel_service.py` — formal service APIs (P2a)
   - `tests/unit/runtime/test_bindings.py` — binding lifecycle, backfill safety, status transitions (P2b)
   - `tests/unit/runtime/test_participation_state.py` — participation lifecycle, opt-in defaults, subscription toggle (P2c)
   - `tests/unit/runtime/test_feature_flags.py` — flag evaluation, environment-tier dispatch, rollout staging (P2d)
   - `tests/unit/runtime/test_config_drafts.py` — draft → validate → preview → commit cycle, scope-lock semantics, cross-pipeline commit (P3)
   - `tests/unit/services/test_setup_health.py`, `test_participation_health.py`, `test_resource_health.py` — completeness scoring per track, finding-tier classification (P4)
   - `tests/unit/governance/test_role_provisioning.py`, `test_delegation.py`, `test_access_control.py` — role detection, provisioning, time-bounded delegations, unified can() resolution (P4.5)
   - `tests/unit/runtime/test_notification_router.py` — eligibility, suppression, digest, audit, rate limit (P6.5)
   - `tests/unit/resources/test_provisioning.py` — setup pack apply, repair flows, regeneration (P7.5)
   - `tests/unit/cogs/test_setup_flow.py` — `!setup` end-to-end for XP, repair flow, template application
   - `tests/unit/cogs/test_participation_flow.py` — `/myprofile` end-to-end for XP subscription toggle, visibility, preferences
6. **Operator verification gates** (all flags managed via P2d feature flag service once it lands):
   - P2a: `RESOURCES_UNIFIED=true` flipped only after selector refactor verified on a canary guild.
   - P2b: `BINDINGS_PRIMARY=true` flipped only after audit-log inspection and binding-status sanity check across all production guilds.
   - P2c: `PARTICIPATION_ENABLED=true` flipped only after one release of warn-only `user_*` table reads.
   - P2d: `FEATURE_FLAG_PRIMARY=true` flipped after migration of ≥3 existing env-var gates to feature flags and verification that flag reads match env-var reads.
   - P4.5: `GOVERNANCE_DELEGATION_ENABLED=true` flipped after one full release of delegation grant/use/revoke audit verification on owner guild.
   - P6: `IDENTITY_CONTRACT_STRICT=1` toggled only after `warn_only` release demonstrates clean findings for one full release cycle.
   - P6.5: `NOTIFICATION_ROUTER_PRIMARY=true` flipped after a canary subsystem (XP) routes 100% of notifications via the router for one week.
   - P7: `SETUP_WIZARD_ENABLED` and `PARTICIPATION_HUB_ENABLED` per-guild canary via P2d rollout policies; full enable after canary success.
7. **Prometheus dashboards** (Phase 4 onward):
   - `setup_health_completeness_ratio{subsystem}` per guild
   - `binding_resolution_failures_total{subsystem}` rate
   - `participation_optin_ratio{subsystem}` per guild
   - `subscription_active_total{subsystem,subscription}` distribution
   - `notification_suppressed_total{intent,reason}` rate
   - `resource_orphan_total{kind}` per guild
   - `setup_flow_completion_total{flow,outcome}` and `participation_flow_completion_total{flow,outcome}`
   - `experience_mode_distribution_total{mode}` per guild
8. **Webhook alerts**: high-severity setup-health regressions, binding/participation pipeline failures, schema-registry drift, notification-router error spikes, resource-orphan ramps.

End-state validation: a new subsystem (the Phase 8 automation cog) can be added by writing only `cog_load` registrations of (a) a `SubsystemSchema`, (b) a `ParticipationSchema`, (c) `ResourceRequirement` declarations, (d) `NotificationIntent` declarations, (e) `FeatureFlag` declarations for any gated behavior, (f) optionally `RoleTemplate` declarations for governance-bearing roles the subsystem expects, and (g) optionally a preset/setup-pack entry — with **zero changes** to wizard code, participation hub code, navigation framework code, notification router code, governance runtime code, resource runtime code, or any other platform primitive. If that's true, the platform is the Guild Operating System this roadmap set out to build.
