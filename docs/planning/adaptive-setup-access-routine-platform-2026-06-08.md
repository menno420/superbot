# Adaptive Setup, Access, Profile, and Routine Platform — source map and roadmap

> **Status:** `plan` · **Phase 0 complete; Phase 1 in progress** — P0A (Q-0026 identity repair), P0B (direct-vs-draft + access read-model contracts), and **P0C (role-threshold writer normalization)** all done 2026-06-08; **P1A (Access Map projection service)** done; **P1B/P1C next** · **Source-verified 2026-06-08**
> **Owner decisions:** applies [Q-0017 through Q-0027](../owner/maintainer-question-router.md#q-0017--adaptive-setupaccessroutine-platform-planning-document-structure-2026-06-08).
> **Authority:** source + binding architecture/ownership/runtime contracts win over this plan. This is the one comprehensive planning home required by Q-0017.
> **Live-repo check:** PRs [#584](https://github.com/menno420/superbot/pull/584) and [#585](https://github.com/menno420/superbot/pull/585) are merged; the GitHub API reported no open PRs during this source-mapping session.

## 1. Executive summary

The Adaptive Setup, Access, Profile, and Routine Platform should be an **orchestration and explanation layer over existing primitives**, not a new configuration, permission, help, or scheduler stack. Its central product promise is one owner/staff-facing answer to:

> What should the bot do here; who can use and see it; where and when does it work; what is unhealthy; and what would change if this draft were approved?

SuperBot already has most of the required write seams and several read seams: setup drafts and Final Review, typed settings mutation, binding/resource pipelines, command-access resolution, cog-routing resolution, governance visibility/capabilities, the command-surface ledger, setup diagnostics, server-management health badges, and an audited automation scheduler/executor. The missing foundation is a **composed, side-effect-free access/setup read model** plus consistent locked reasons and drift findings. Product mutation must wait until that read model is trustworthy.

**Ready now:** reconcile subsystem identity debt; specify/build the read-only Access Map projection; extend deterministic diagnostics; add staff-only Help Preview using the live help resolver; catalogue the panel consistency gaps.

**Later:** Guild Feature Profiles can generate previewable setup drafts once the read model and profile catalogue are settled. Access Map editing, profile application, and configuration routines must route through setup drafts/Final Review and audited canonical services. Personal Setup is Phase 5. AI assistance is Phase 6 and remains gated; it may explain or draft, never mutate.

## 2. Binding decisions and terminology

| Decision | Applied consequence |
|---|---|
| Q-0017 | This document is the single comprehensive plan; no parallel concept docs. |
| Q-0018 | Starter Guild Feature Profiles are derived from real registry/routing/setup support, not the prompt's six examples. |
| Q-0019 | Routine actions use progressive risk: low risk may auto-apply; medium/high risk queue approval/Final Review; every run is auditable. |
| Q-0020 | Personal Setup stays Phase 5 but is fully specified here. |
| Q-0021 | Routines extend `automation_scheduler`, `automation_executor`, `automation_registry`, templates, and mutation pipeline. |
| Q-0022 | **Guild Feature Profile** is the server configuration bundle. **Automation Preset / `ServerPreset`** remains an automation rule template. |
| Q-0023 | Help Preview is staff/admin-only. Normal users receive clear denial/locked-reason messages instead. |
| Q-0024 | Access Map is read-only before Phase 3. |
| Q-0025 | `scripts/new_subsystem.py` is decided backlog, not part of this plan's product implementation. |
| Q-0026 | Fix CamelCase → snake_case subsystem conversion and rename `servermanagement` → `server_management` before building multi-word-profile identity assumptions. |
| Q-0027 | Binding repo docs override prompt/template wording. |

### Concept glossary

- **Guild Feature Profile:** named, versioned server-configuration intent that compiles into previewable setup operations. Never call it a preset.
- **Automation Preset / `ServerPreset`:** existing template that installs one automation rule through `AutomationMutationPipeline`.
- **Setup draft:** persisted, provenance-bearing list of `SetupOperation` rows for a guild.
- **Final Review:** authority-rechecked, ordered, audited apply/recovery gate for setup operations.
- **Access Map:** composed read model explaining who can use/see what, where, and why.
- **Help Preview:** staff-only rendering of live help for a selected audience context.
- **Routine:** automation rule plus optional conditions, risk classification, and an action.
- **Condition:** deterministic predicate evaluated before an action; false/failed evaluations are observable.
- **Action:** canonical executor dispatch target; config actions either use an approved canonical mutation or queue a draft.
- **Availability policy:** central policy layer for time/event/stage/user-age availability, composed after hard safety and guild policy.
- **Quiet mode:** a time-window or manually-triggered state that suppresses non-essential bot commands and bot-initiated outbound posts for a configured duration or until lifted. Non-essential commands return a quiet-mode denial with a locked reason and end time. Commands stay visible in help, labelled "currently quiet" — not hidden. Staff/admin/essential commands (moderation, diagnostics, help, management) are exempt. Triggered by routine (`enable_quiet_mode(until=)`) or manual staff action; lifted by time expiry, manual lift, or `disable_quiet_mode()`. Availability policy layer owns the per-command check; the routine engine sets/clears a guild-scoped quiet state flag (a reversible settings key or DB column, risk: low).
- **Locked reason:** structured, safely renderable explanation of a denial and, where appropriate, the unlock requirement.

## 3. Current-state source map

### 3.1 Canonical services, registries, and runtime paths

| File/module | Current responsibility | Reuse candidate | Risk / missing piece |
|---|---|---|---|
| `disbot/services/setup_draft.py` + `utils/db/setup_draft.py` | Persists ordered operations with section/staging/group provenance, risk, reason, source, and rollback note. | Profile previews, Access Map edits, routine approval drafts. | Public staging kinds are fixed; profile/routine provenance may need additive kinds or metadata conventions. |
| `disbot/services/setup_operations.py` + `views/setup/final_review.py` | Typed operation dispatcher; ordered, locked, authority-rechecked apply with partial recovery. | Only controlled mutation seam for compound profile/access/routine changes. | New op kinds are a dispatcher + DB gate + SQL CHECK contract. Do not bypass it. |
| `disbot/services/settings_mutation.py`, `binding_mutation.py`, provisioning/lifecycle services | Canonical audited writers for settings, bindings, resources, roles/channels. | Underlying operation executors and direct single-setting manager edits. | Not all panels use the same writer or preview model. |
| `disbot/core/runtime/command_access.py` + `services/command_access_service.py` | Resolves guild channel-access mode, bootstrap/operator exceptions, decision reason/source; canonical audited writer. | Access Map command-access axis and locked reason seed. | Current model is command-entry channel admission, not full capability/time availability. |
| `disbot/services/command_routing.py` + `cog_routing_profiles.py` | Resolves channel → category → guild → default-true cog routing; existing routing profiles compile to setup operations. | Access Map routing axis and Feature Profile compiler building blocks. | Routing profiles are channel-name heuristics for three cogs, not full Guild Feature Profiles. |
| `disbot/governance/` (`resolve_visibility`, capability resolvers, snapshots) | Canonical subsystem visibility and capability/authority decisions. | Access Map role/capability/help visibility axes. | Must compose, not duplicate; legacy `governance_service` is only a re-export shim. |
| `disbot/core/runtime/command_surface_ledger.py` | Runtime command/subsystem identity, classification, help-hidden policy, diagnostics. | Feature inventory, help/access consistency checks. | **Q-0026 resolved 2026-06-08:** `cog_name_to_subsystem` now CamelCase → snake_cases (also repaired the latent `proof_channel`/`four_twenty` collapse). |
| `disbot/utils/subsystem_registry.py` | `SUBSYSTEMS`, `HUBS`, visibility/capability/entry-point metadata and identity validation. | Profile catalogue vocabulary and Access Map feature index. | Registry metadata describes identity/discovery, not per-guild desired enablement. Key is now `server_management` (snake_cased per Q-0026). |
| `disbot/cogs/help_cog.py`, `cogs/help/route.py`, help views | Governance-aware live help, registry/category routes, command classification filtering. | Help Preview must invoke the same visibility and render paths with an explicit audience context. | No single composed help+command-access+routing+availability explanation object today. |
| `disbot/services/setup_diagnostics.py` | Read-only setup findings; suggested repairs are setup operations, never direct writes. | Setup health/drift detector core. | Needs access/help/routing/routine/identity consistency providers. |
| `disbot/services/server_management_hub.py` + `views/server_management/hub.py` | Read-only badges and handoffs to moderation/channels/roles/cleanup/setup managers. | Owner landing point for Access Map, health, Help Preview. | It deliberately owns no mutation and should stay that way. |
| `disbot/services/automation_registry.py` | Typed trigger/action metadata aligned with migration 032. | Extend with conditions and config-oriented action metadata/risk. | Registry ↔ SQL CHECK lockstep makes additions migration-bearing. |
| `disbot/services/automation_templates.py` | `ServerPreset` catalogue and installability filtering. | Keep as Automation Presets; possibly add safe routine templates. | Must not be renamed/reused as Guild Feature Profiles. |
| `disbot/services/automation_scheduler.py`, `automation_executor.py`, `automation_mutation.py`, `utils/db/automation.py` | Claim/run lifecycle, dispatch, owner-gated rule writes, run/error/audit state. | Routine Engine foundation. | No general condition model; several triggers/actions exist but installability and execution support differ. |

### 3.2 Existing setup and management surfaces

| Surface | Current behavior and reusable seam | Planning conclusion |
|---|---|---|
| Setup launcher/wizard/hub/depth (`views/setup/launcher.py`, `wizard.py`, `hub.py`, `depth_panel.py`) | Shared `BaseView`; depth/progress/session model; depth panel explicitly stages no operations. | Reuse for guided first-run flow; do not overload it with the entire Access Map/routine platform. |
| Setup sections (`views/setup/sections/`) | Channels, moderation, roles, cleanup, cog routing, presets, diagnostics, role templates, AI review, etc. stage recommended/custom/preset/repair operations. | Strongest shared controlled-mutation pattern; Feature Profile compiler should produce the same operations. |
| Final Review/recovery (`views/setup/final_review.py`, `recovery.py`) | Preview, authority recheck, ordered apply, audit outcome, partial recovery. | Mandatory for profile apply and medium/high-risk routine/config changes. |
| Server Management Hub | Persistent/ephemeral read-only router with health badges. | Keep as composition/navigation; add links/cards, not write logic. |
| Settings Hub/editors (`views/settings/`) | `HubView`; typed editors write directly through `SettingsMutationPipeline`; command access writes through `command_access_service`; audit/invalid/missing views are read-only. | Canonical direct-edit lane, but not setup-draft/Final Review. Appropriate for isolated reversible settings; compound edits need draft mode. |
| Moderation manager (`views/moderation/`) | Runtime moderation actions through `ModerationService`; persistent panel; capability checks. Setup moderation section stages config separately. | Runtime actions should remain direct/audited and outside Final Review; moderation configuration should converge on canonical setting writers/drafts. |
| Role manager (`views/roles/`) | Mix of `RoleLifecycleService`, `role_exemption_service`, and direct DB threshold writers. | Largest consistency drift: lifecycle operations are audited but destructive/direct; threshold panels bypass setup draft and some canonical service seams. Normalize before routine/profile role mutations. |
| Channel manager (`views/channels/`) | Mix of direct Discord creation, audited `ChannelLifecycleService` deletion, direct channel edits, and governance visibility writer. | Mixed lane. Keep deliberate confirmed runtime management, but profiles/routines must never call panels/direct Discord methods. Centralize create/edit lifecycle/audit before automation. |
| Cleanup manager (`cogs/cleanup/panel.py`, `views/cleanup/policy_panel.py`) | Router is read-only; policy panel previews and confirms canonical policy changes; setup cleanup stages operations. | Good confirmation model, but separate from setup Final Review. Reuse diagnostics/policy service and preserve direct focused workflow. |
| Setup diagnostics/repair | Findings are read-only; repair proposals stage `SetupOperation` rows. | Model for all future drift repair. |
| Help/admin/operator surfaces | Help uses registry/governance/classification; operator/server-management surfaces compose health and handoffs. | Help Preview and Access Map should be diagnostics on the same resolvers, not alternate policy. |

### 3.3 Tests and contracts to preserve

Key existing guards include `tests/unit/services/test_setup_operations*.py`, `test_setup_draft.py`, `test_preset_to_setup_operations.py`, `test_command_access_service.py`, `test_command_routing.py`, `test_cog_routing_profiles.py`, `test_setup_diagnostics.py`, automation registry/executor/scheduler/template/mutation tests, command-surface ledger and subsystem-registry tests, plus setup/settings/server-management view tests. Binding boundaries remain [architecture](../architecture.md), [ownership](../ownership.md), [runtime contracts](../runtime_contracts.md), [capability authority](../capability-authority.md), and the [settings customization roadmap](../setup-platform/settings-customization-roadmap.md).

## 4. Foundation first

### 4.1 Target boundaries

Create a read-oriented service family, not a god service:

1. **Feature inventory adapter** — reads subsystem registry + command-surface ledger.
2. **Access context** — explicit guild/channel/category/member/role/time/event/setup-stage inputs.
3. **Access projection resolver** — composes command access, cog routing, governance visibility/capabilities, bootstrap exceptions, AI gates, and later availability policies into structured decisions.
4. **Explanation renderer** — converts structured reasons into Access Map rows, Help Preview annotations, and user-safe denial messages.
5. **Drift providers** — compare projections, configured resources, help exposure, routine references, and identity contracts without writing.
6. **Draft compiler(s)** — only after read projection stabilizes; convert profile/access edits or risky routine actions into `SetupOperation` drafts.

The projection should return decisions with source, precedence, allow/deny/unknown state, locked reason code, safe explanation, and optional remediation pointer. It should not persist initially. Caching is optional only after invalidation owners are explicit.

### 4.2 Required prerequisites

1. **Q-0026 identity fix — DONE (2026-06-08).** `cog_name_to_subsystem` now does a two-pass CamelCase → snake_case conversion and the registry key is `server_management`; the same fix repaired the latent `ProofChannelCog → proof_channel` / `FourTwentyCog → four_twenty` collapse, and regression tests pin the snake_case output contract. The user-facing `!servermanagement` command name is unchanged (command names are not subsystem keys). Profile identifiers may now safely assume snake_case multi-word keys.
2. **Pin the mutation boundary:** profiles, Access Map editing, and risky routines compile to setup drafts; Final Review applies. Focused manager/runtime actions may remain direct through their canonical audited services.
3. **Build the composed read model before UI/editing:** Access Map, Help Preview, denial explanations, and drift checks must consume one resolver.
4. **Normalize high-risk drift before automating it:** especially direct role-threshold DB writes and direct channel creation/edit paths.
5. **Extend automation, never fork it:** add conditions/actions/risk/approval behavior around the existing registry, scheduler, executor, mutation pipeline, and runs.

> **Do not build on top of drift:** no profile catalogue that hard-codes stale subsystem keys; no Help Preview with copied visibility logic; no Access Map editor before the read model; no routine action that calls Discord APIs or manager-panel callbacks directly.

## 5. Settings/manage-panel consistency map

The panels **do not all follow the same edit rules or base**. They share UI foundations (`BaseView`, `HubView`, `PersistentView`) and often use canonical services, but there are intentionally different lanes and several real drifts.

| Surface | Read/write | Draft + Final Review? | Gate / audit / rollback | Shared base / canonical seam | Classification and follow-up |
|---|---|---|---|---|---|
| Setup hub/depth/progress | Read/session write | No config mutation in depth; sections draft | Setup access; session audit/progress | `BaseView`, setup session/progress | Keep as setup orchestration. |
| Setup sections | Draft mutation | **Yes** | Apply-time authority; operation metadata, apply outcome, partial recovery | `BaseView`, `setup_draft`, `SetupOperation` | Canonical compound-change model. |
| Final Review/recovery | Applies drafts | **Yes** | Rechecks `can_apply_setup`; apply lock; audit/recovery | `BaseView`, canonical operation dispatcher | Mandatory controlled-mutation gate. |
| Server Management Hub | Read-only/router | N/A | Administrator/capability gating; no mutation | `PersistentView`, badge composer | Keep direct read-only. |
| Settings typed editors/reset | Direct setting write | No | Callback authority; `SettingsMutationPipeline` audit; previous/new values | `HubView`/editor views | Valid focused direct lane; add optional “add to draft” only when compound workflows need it. |
| Settings command access | Direct access-policy write | No | Canonical service invalidation + audit; bootstrap warning | `HubView`, `command_access_service` | Read model can consume now; editing moves behind draft in Access Map Phase 3, while focused editor may remain direct. |
| Settings audit/invalid/missing/needs-setup | Read-only | N/A | Redaction/authority by parent route | `HubView` | Keep read-only. |
| Cog-routing setup section/profiles | Draft write | **Yes** | Final Review; operation risk currently medium | `BaseView`, `cog_routing_profiles`, `command_routing` apply seam | Reuse for Feature Profiles. |
| Setup diagnostics/repair | Read + repair draft | **Yes for repair** | Findings are read-only; repairs reviewed | `BaseView`, `setup_diagnostics` | Ideal drift pattern. |
| Moderation action panel | Runtime mutation | No | Per-action capability; `ModerationService` audited writer | `PersistentView` + service | Keep direct: these are runtime moderation actions, not configuration. |
| Moderation setup section | Config draft | **Yes** | Final Review | setup section + `set_setting` ops | Keep and expand via canonical settings metadata. |
| Role create/edit/delete | Direct resource mutation | No | Confirmation varies; `RoleLifecycleService` audit/result | `BaseView`, lifecycle service | Keep operator workflow, but require snapshots/strong confirmation for destructive flows; never routine-direct. |
| Role thresholds | Direct DB write | No | Capability at route; audit consistency varies | `BaseView`, role DB helpers | **Drift:** centralize behind audited role-automation service before profiles/routines. |
| Role exemptions | Direct service write | No | Audited/cache-invalidated service | `BaseView`, `role_exemption_service` | Valid focused direct lane. |
| Channel create/edit/move/restrict/visibility/delete | Direct Discord/service/governance mix | No | Confirmation strongest for delete; audit varies | `HubView`/`BaseView`; lifecycle/governance services | **Drift:** centralize create/edit/move/restrict lifecycle and audit before automation; runtime direct manager can remain. |
| Cleanup hub/policy | Read-only router + confirmed policy write | No | Preview/confirm; governance/canonical cleanup services | `HubView`, `BaseView` | Good focused workflow; setup/profile changes should still draft. |
| Help | Read-only | N/A | Live visibility resolver/classification | Help views + registry/governance | Preview must use same resolver; do not fork. |

**Centralize before future work:** structured access decisions/reasons; role-threshold writer; channel lifecycle/audit coverage; draft provenance for profile/routine origins; setup-operation risk policy; read-model drift providers. **Remain direct:** runtime moderation actions, diagnostic/read-only panels, focused reversible typed setting edits, and deliberate resource-manager actions through canonical audited lifecycle services.

## 6. Product concept specifications

### 6.1 Guild Feature Profiles

A profile is declarative intent compiled against the current guild into grouped setup operations. It has a stable slug/version, display text, intended audience, supported subsystem keys, assumptions, setup depth, operations/builders, risk summary, and compatibility findings. Preview shows no-op/already-matching/blocked/proposed rows and never mutates.

**Source-grounded starter recommendation (owner confirmation required):**

1. **Essential Utility** — setup/health/settings/help/server-management foundations; avoids claiming domain cogs are configured.
2. **Community Core** — moderation, roles, cleanup, logging/bindings, sensible command access; only where setup sections and canonical writers exist.
3. **Games Community** — Games hub plus existing game/economy routing heuristics; uses detected channels and reports missing prerequisites.
4. **Moderation Focused** — moderation/roles/cleanup/logging with stricter access intent; broad permission changes stay draft-only/high risk.
5. **BTD6 Community (experimental/gated)** — only after BTD6 readiness and setup coverage are verified; not an initial generally available promise.

**Phase 2 design note (Q-0028):** Essential Utility and Community Core may consolidate during the Phase 2 profile catalogue design session into one Foundation profile plus an optional Community add-on (moderation, roles, cleanup, logging). Do not implement two overlapping profiles without reviewing this first. The distinction should be settled before the profile compiler is built.

Do not start with “Private/Friends” until its policy differences are explicit, or “Game Server” as a blanket profile when registry readiness varies by game. Profiles should use registry metadata to enumerate features but require explicit profile-owned intent; registry presence alone must not enable a feature.

**Open gap for Phase 2:** the compiler spec must decide what a profile does when it would logically require removing a resource (e.g. a channel belonging to a disabled feature). The current plan forbids auto-delete but does not specify whether profiles should surface this as a "manual action required" finding, a no-op with a warning, or a separate cleanup suggestion. Resolve in the Phase 2 design session before implementing the profile compiler.

### 6.2 Unified Access Map

Phase 1/2 read-only rows should cover feature/subsystem/cog, command group/entry point, channel/category routing, command-access mode, capability/role authority, help visibility, setup visibility, AI visibility/gates, bootstrap/recovery exceptions, and later availability locks. Each row includes effective result, source chain, reason, safe remediation, and inconsistencies. It creates no second permission system: it is a projection over existing owners.

Phase 3 editing changes intent into grouped setup operations and opens Final Review. Direct editing is forbidden from the read-only surface.

### 6.3 Help Preview and locked reasons

Staff/admin Help Preview supplies an explicit simulated audience (normal member, trusted user, moderator, admin, owner/operator where meaningful) to the same live help visibility/rendering path. It must label simulation limits and never imply Discord permissions it cannot accurately model. Normal users do not receive audience simulation; they receive a structured denial message from the live access/availability decision, with unlock guidance only where safe.

**Locked reason structure (minimum fields for Phase 1B):** `code` (stable string identifier, e.g. `quiet_mode`, `command_access_deny`, `availability_window`, `setup_stage_required`), `safe_text` (user-renderable string, never leaks sensitive policy details), `source` (which policy layer produced it: `command_access` | `routing` | `availability` | `capability` | `bootstrap`), `unlock_hint` (optional — only included when the unlock path is safe to show, e.g. "unlocks after 24h membership"). The renderer must never expose role names, channel IDs, or policy internals in `safe_text`.

### 6.4 Setup health and drift detection

Extend `setup_diagnostics` with providers for: incomplete/skipped advanced setup; deleted configured channels/roles; command access that blocks all non-admin users; help exposure of disabled/unavailable features; routing/access conflicts; routine references to missing resources; bootstrap/recovery path availability; and subsystem/ledger/help identity mismatch. Findings remain side-effect-free. Repairable findings produce setup-operation drafts. Non-repairable findings link to the owning panel or explanation.

### 6.5 Automation Presets and Routine Engine extension

Existing triggers are `scheduled_time`, `interval`, `member_join`, `setup_readiness_below`, `binding_missing`, `channel_inactive`, and `manual`; `scheduled_time` is currently blocked for new installs until cron support. Existing actions include messaging, role assignment/removal, readiness/leaderboard summaries, binding/channel actions, and owner notification (verify executor support before exposing any template). Existing `ServerPreset` remains an Automation Preset.

Add a typed **condition model** to rules or an associated table/JSON envelope, evaluated by the executor before dispatch: `role_present`, `setup_stage_completed`, `event_active`, `cooldown_state`, `account_age`, `join_age`, and channel/category state. Add configuration-oriented actions only via canonical seams: `apply_feature_profile` should normally mean “compile/queue draft,” `switch_cog_routing_profile`, `enable_quiet_mode`, `hide_show_help_category`, `queue_final_review_draft`, post/update panel, notify staff, and start setup checklist.

| Risk | Default behavior | Examples |
|---|---|---|
| Low | May auto-apply through audited canonical service | Send/update a bounded message/panel; staff notification; start checklist; reversible narrow quiet-mode/help-display change if owner classifies it low. |
| Medium | Queue approval draft / Final Review | Routing profile switch, multi-setting profile subset, binding change, role threshold, channel creation. |
| High | Queue approval draft; stronger summary/snapshot | Broad access/capability change, role creation, full Guild Feature Profile application. |
| Forbidden automatic | Never auto-apply | Role deletion, permission-overwrite mutation without preview, mass channel changes, physical cog load/unload, AI-generated direct mutation. |

Every execution records trigger, condition outcomes, action risk, actor/rule/profile version, proposed/applied operation IDs, result/error, notifications, and rollback/snapshot references.

### 6.6 Central availability policy and time-based unlocks

Add one policy resolver after global safety → guild → channel → role/capability and before user preferences. Rules may reference member tenure, account age, setup stage, accepted-rules/event state, quiet hours, or domain event windows. Commands and help both consume the same decision. No command-specific time checks. Locked reasons identify the policy source and safe unlock condition; sensitive policies may return a generic reason.

### 6.7 Personal Setup Wizard (Phase 5 full spec)

Commands: `/my-setup` for guided onboarding/checklist and `/my-preferences` for ongoing controls. Likely preferences: guild-scoped timezone override, notification subscriptions, DM permission/preference, help ordering, favorite/hidden features, onboarding steps, and optional account links.

Invariant:

```text
global safety policy → guild policy → channel policy → role/capability policy → user preference
```

Preferences can hide, sort, personalize, or subscribe; they never grant access. Data must distinguish global vs guild scope, default/explicit/unknown values, consent timestamp/source, retention/deletion/export, and visibility. Account links should wait for Q-0033 because generic cross-domain links materially change privacy and ownership.

### 6.8 AI-assisted setup suggestions (Phase 6)

Behind existing AI expansion/readiness gates, AI may suggest profiles/routines, explain deterministic health findings, draft role/channel/settings operations, and summarize an owner-facing change plan. AI output is untrusted proposal data: deterministic schema validation, canonical compiler, preview, risk classification, and owner Final Review are mandatory. AI never directly calls a mutation service.

## 7. Readiness matrix

| Capability | Readiness | Why / prerequisite |
|---|---|---|
| Setup wizard improvements | Ready now, selectively | Mature session/draft/review paths; avoid adding advanced controls to first-run flow. |
| Settings/manage-panel consistency baseline | Ready now | Source map exists; normalize role thresholds/channel lifecycle before automation. |
| Unified Access Map (read-only) | Needs foundation | Requires Q-0026 and composed resolver/reason model. |
| Help Preview | Needs foundation | Same resolver as live help + explicit staff simulation context. |
| Setup health/drift detection | Ready now / iterative | Existing diagnostics pattern; new cross-axis providers depend on Access Map projection. |
| Guild Feature Profile preview | Needs foundation + owner decision | Needs profile catalogue decision, Q-0026, compiler contract, compatibility report. |
| Profile apply / Access Map editing | Needs foundation | Phase 3 only; draft/Final Review, snapshots, audit. |
| Automation/routines | Needs foundation + owner decisions | Existing substrate; requires condition/risk/approval design and SQL migrations. |
| Time/event unlocks | Needs foundation | Central availability resolver and locked reasons first. |
| Personal Setup Wizard | Future only + privacy decisions | Phase 5 migrations, privacy/retention/export design. |
| AI-assisted setup suggestions | Gated | Existing AI expansion/readiness gates plus deterministic drafts. |
| `scripts/new_subsystem.py` | Ready backlog, separate | Q-0025 decided; useful after Q-0026 naming fix. |

## 8. Phased roadmap

### Phase 0 — foundation and reconciliation

- ✅ **Implement Q-0026 identity fix/rename** (2026-06-08) — `cog_name_to_subsystem` snake_cases; key `server_management`; latent `proof_channel`/`four_twenty` collapse also fixed; regression tests added (P0A).
- ✅ **Turn this panel consistency map into explicit canonical direct-vs-draft rules** (2026-06-08) — now binding in [`docs/ownership.md` § "Direct vs. draft mutation lanes"](../ownership.md) (P0B).
- ✅ **Specify structured access decision, locked reason, simulated audience, and drift-provider interfaces** (2026-06-08) — see §16 below (P0B). Reuses the existing `command_access` decision/reason model rather than forking it.
- ✅ **Normalize/audit role-threshold writes** (2026-06-08, P0C) — all six time/XP threshold write sites now route through the audited `role_automation.set_{time,xp}_threshold` seam; the drift fence's allowlist is empty (absolute rule in force). Channel-lifecycle normalization is the deferred secondary gap (assess, don't rewrite — §16.5).
- ⏳ Confirm first Guild Feature Profile catalogue and risk/snapshot owner decisions (Q-0028 / Q-0030 / Q-0031 — open; safe defaults hold, no committed catalogue built).
- No product expansion or new mutation surface.

### Phase 1 — read-only orchestration foundation

- Build Access Map projection service and tests.
- Add read-only Access Map operator surface, likely linked from Server Management/Settings.
- Add deterministic access/setup drift providers.
- Add staff/admin-only Help Preview using live help resolver.
- Add clear user-safe locked reasons to denial paths.
- No Access Map editing.

### Phase 2 — Guild Feature Profile preview

- Add versioned profile catalogue based on supported registry/setup/routing capabilities.
- Compile profile intent to in-memory operations and compatibility findings.
- Render dry-run/no-op/blocked/risk/grouped preview.
- No direct apply and no profile mutation UI.

### Phase 3 — controlled mutation

- Persist profile and Access Map edits as grouped setup drafts.
- Open Final Review with provenance, staff-facing summary, risk grouping, and snapshot/rollback references.
- Expand operation kinds only through dispatcher/DB/CHECK parity.
- Preserve focused direct manager lanes where appropriate.

### Phase 4 — Routine Engine extension

- Extend existing automation schema/registry/executor with conditions, action risk, and approval-draft outcomes.
- Add safe configuration action adapters that call canonical compilers/services.
- Auto-apply only owner-approved low-risk actions; queue medium/high-risk drafts.
- Add run/condition/draft/audit/operator-notification observability.

### Phase 5 — Personal Setup Wizard

- Add privacy-reviewed global/guild user-preference model, `/my-setup`, `/my-preferences`, onboarding, timezone, notification/DM preferences, personalized help ordering, favorites/hiding, and later account links.
- Prove preferences cannot elevate access.

### Phase 6 — AI-assisted setup drafts

- Only after AI gates clear.
- Add suggestion/explanation/draft-generation adapters; validate deterministically and require preview/approval.
- No AI mutation tool.

## 9. Future session batch plan

| Batch / target agent | Goal and scope | Likely files | Out of scope | Verification | Risk / stop conditions |
|---|---|---|---|---|---|
| **P0A — Codex/Sonnet:** Q-0026 identity repair | ✅ **DONE 2026-06-08.** Snake-case conversion, `server_management` rename, references/tests/docs. | `command_surface_ledger.py`, `subsystem_registry.py`, help/router/hub tests/docs | Product features | Full quality + strict architecture + live identity check | Medium; stop if key migration affects persisted external contracts unexpectedly. |
| **P0B — Opus:** access/read-model contract | ✅ **DONE 2026-06-08** (docs). Precedence, decision/reason schema (reuses `command_access`), audience simulation, owners, invalidation, direct-vs-draft rule — §16 + `docs/ownership.md`. | Planning/ADR/ownership/runtime docs | Runtime code | Docs/architecture checks | High architecture; stop on unresolved second-permission-system risk. |
| **P0C — Sonnet:** panel writer normalization | ✅ **DONE 2026-06-08.** All six role-threshold write sites converted to the audited `role_automation.set_{time,xp}_threshold` seam; drift-fence allowlist emptied (absolute rule). Seam relaxed to `role_id: int \| None` for the legacy `!setrole` free-text path; the created-role XP companion now threads the real id (rename-safe). Channel lifecycle remains the deferred secondary gap. | role services/views/tests | New automation actions; channel-lifecycle rewrite | Focused unit/view tests + full quality (8094 passed) | Medium/high; stopped before any behavior-changing destructive flow. |
| **P1A — Sonnet:** Access Map projection | ✅ **DONE 2026-06-08.** Side-effect-free composed service + 19 tests, no UI — `services/access_projection.py`. | new service module; governance/access/routing/ledger adapters; tests | Editing/persistence | Unit/service/identity tests + strict architecture | High; stop if owner of any axis cannot be identified. |
| **P1B — Sonnet:** drift + locked reasons | **Re-scoped (§16.8 items 5–7); partially shipped.** ✅ `routing_access_conflict` built (`setup_diagnostics._diagnose_routing_access_conflict`, member-independent, 7 tests). **Remaining:** `help_advertises_locked` (needs the item-3 audience decision first). **Skipped `configured_resource_missing`** — already covered by the four existing collectors. The denial-message UX integration is a **confirm-with-maintainer** step, separable from the read-only providers. | `setup_diagnostics.py` (new `_diagnose_*` collectors), tests | Editing; `configured_resource_missing`; silent denial-message changes | Diagnostics/access tests + quality | Medium; stop if explanation leaks sensitive policy or a provider needs audience sim that isn't built. |
| **P1C — Sonnet:** Access Map + Help Preview UI | Staff-only read-only panels using P1A; Server Management link. | server-management/help/views/cogs/tests | Mutation | View/authority/help tests + live smoke | Medium. |
| **P2 — Opus then Sonnet:** Feature Profile preview | Decide starter set/schema, implement catalogue/compiler/dry-run preview. | new profile service, setup operations/read model/views/tests | Apply | Compiler/view tests; no DB writes in preview | High; stop on unresolved profile/risk questions. |
| **P3 — Opus then Sonnet:** controlled profile/access mutation | Draft generation, provenance, snapshots, Final Review summaries. | setup draft/operations/final review/migrations/views/tests | Routines/AI | Migration, apply/recovery/audit/capability tests | High; stop if any path bypasses Final Review. |
| **P4A — Opus:** Routine schema/safety design | Conditions, action risk, approval outcomes, observability contract. | plan/ADR/ownership/runtime docs | Implementation | Docs/architecture checks | High; blocked by Q-0029–Q-0031. |
| **P4B — Sonnet:** Routine Engine extension | Schema/registry/executor/mutation/UI batches after approved design. | automation services/DB/migrations/tests | AI-generated routines | Registry parity, scheduler/executor/migration/audit tests | High; stop on destructive/direct mutation. |
| **P5 — Opus then Sonnet:** Personal Setup | Privacy/data design, then preferences and commands. | new DB/service/views/cogs/help/tests | Access grants, cross-guild admin data | Privacy invariants, migration, permission, deletion/export tests | High; blocked by Q-0033. |
| **P6 — Opus then Sonnet:** AI drafts | Gate review, deterministic draft adapters and summaries. | AI gateway/orchestration, profile/routine compiler adapters, tests | Direct mutation | AI gate, redaction, schema, deterministic approval tests | High/gated; stop until AI readiness gates clear. |

Each implementation batch is independently reviewable. Opus owns cross-cutting contract/final-plan sessions; Sonnet owns coherent implementation batches after approval; Codex is a good fit for source mapping, bounded debt, drift guards, and docs/tooling.

## 10. Architecture boundaries

- Do not create a second permission system; compose command access, routing, governance, Discord permissions, and availability.
- Do not physically unload/load cogs for guild customization; routing/visibility are policy.
- Do not let AI mutate settings directly.
- Do not add one-off command-specific time checks.
- Do not build routines as ad-hoc background tasks; use scheduler/executor/run lifecycle.
- Do not overload first-run setup with every advanced control.
- Do not duplicate help visibility, command access, cog routing, or role/capability logic.
- Do not call view callbacks from compilers/routines; call canonical services or queue operations.
- Do not auto-apply destructive or broad permission/resource changes.
- Do not persist a read model merely because a UI needs it; compute first, cache only with explicit invalidation.

## 11. Data model and migration considerations

| Concern | Compute first? | Likely persistence / migration later |
|---|---|---|
| Access Map projection | **Yes** from registry/ledger/policies/resources | Optional cache only after invalidation contract; no source-of-truth table. |
| Guild Feature Profile catalogue | Built-ins can be source-owned/versioned | Guild-selected/default profile and applied-version/history only if product needs it; profile draft provenance may fit metadata first. |
| Profile preview | **Yes**, in memory | Draft rows only on explicit “add to Final Review.” |
| Routine conditions | No, rules need durable config | Add normalized condition JSON/schema/version or child table; registry/SQL parity and validation required. |
| Routine action risk/approval outcome | Derived default + explicit versioned policy | Store risk/policy version and queued-draft/result linkage in rules/runs. |
| Routine audit entries | No | Extend automation runs/audit payload with condition results, proposal/draft/apply IDs, snapshot reference. |
| Rollback snapshots | N/A | Add snapshot entity or immutable serialized before-state references if Q-0030 requires them. Avoid pretending free-text rollback notes are executable rollback. |
| Availability rules/locked reasons | Resolver can start with source-owned rules | Guild-configurable rules need versioned table/JSON, scope, precedence, safe explanation, activation window, audit. |
| User preferences | No | Global/guild-scoped preference tables with consent/source/timestamps, privacy scope, deletion/export, nullable/default semantics. |
| Account links | No | Separate privacy-reviewed ownership/domain table; never bury credentials/secrets in preferences. |

All schema additions are additive, versioned, cache-aware, auditable, and tested for migration parity. Cross-guild user data requires explicit privacy decisions before implementation.

## 12. Observability and audit

Required events/records:

- Access projection/locked-reason metrics by reason code without sensitive identifiers.
- Setup/profile change summary: compiler/profile version, grouped operations, actor, risk, before/snapshot reference, Final Review outcome, partial recovery.
- Routine run: trigger, every condition outcome, dispatch/approval decision, canonical action result, error class, retry/disable behavior, draft/apply linkage.
- Drift findings: stable code, severity, owner, first/last seen where health framework supports it, safe repair/link.
- Operator/staff notification for queued approval, repeated failure, auto-disable, high-risk proposal, or partial apply.
- Rollback traceability from applied operation/run back to immutable before-state or explicit manual rollback instructions.

Reuse audit events, settings mutation audit, lifecycle results, automation runs, diagnostics providers, and health surfaces. Do not add a parallel generic log table until a concrete gap is proven.

## 13. Testing strategy

- **Unit:** decision precedence, reason safety, audience simulation, profile compiler, condition predicates, risk classifier.
- **Service:** composed Access Map against command access/routing/governance/ledger; diagnostic providers; canonical writer adapters.
- **View:** staff-only Help Preview, read-only Access Map, profile dry run, Final Review summaries, callback authority rechecks.
- **Migration/parity:** automation condition/action constraints, setup operation kinds, snapshot/preferences/availability schemas.
- **Drift guards:** registry ↔ ledger/help/hubs/router keys; automation registry ↔ SQL; operation dispatcher ↔ DB gate ↔ SQL CHECK.
- **Identity contracts:** multi-word subsystem snake-case behavior and `server_management` discovery.
- **Permission/capability:** bootstrap/recovery, moderator/admin/owner tiers, simulated vs actual contexts, user preferences never grant access.
- **Draft/Final Review:** grouping, provenance, replace conflicts, no-op/blocked rows, apply lock, partial recovery, snapshot linkage.
- **Automation:** claim-once, conditions false/error, progressive apply vs queue, audit/error/notification/auto-disable.
- **Locked reasons/help agreement:** every denial maps to safe text; help never advertises a command as available when the shared projection says locked, unless deliberately shown as locked with reason.
- **Negative architecture tests:** previews are side-effect-free; AI/routines cannot import direct mutation/Discord resource APIs where prohibited.

## 14. Open owner questions

This session added Q-0028–Q-0033 to the [maintainer question router](../owner/maintainer-question-router.md). They do not repeat Q-0017–Q-0027:

- Q-0028: approve/revise the source-grounded first Guild Feature Profile catalogue.
- Q-0029: classify quiet mode as availability policy, routine action, or both with one owner.
- Q-0030: define required rollback snapshot coverage.
- Q-0031: approve the initial routine/profile action risk matrix.
- Q-0032: choose Discord UI command/entry-point names for Access Map and Help Preview.
- Q-0033: decide whether Personal Setup account links start generic or domain-specific later.

**Q-0028–Q-0033 + Q-0036 ANSWERED (2026-06-09, gate-lifting interview — verbatim in the router):**
the proposed profile catalogue is **committed** (Essential Utility / Community Core / Games
Community / Moderation Focused + BTD6 experimental, Q-0028); **availability policy is quiet
mode's sole owner** (routines request through it, Q-0029); snapshots are **mandatory for
compound profile/routine + high-risk applies** (Q-0030); the **risk policy is approved as
written** (Q-0031); Access Map / Help Preview are **staff-hub subpanels only — no new command
names reserved** (Q-0032); **account links deferred entirely** (Q-0033); denial copy is
**Claude-drafted, maintainer-reviewed in PR** (Q-0036). Profiles stay preview-only until the
apply pipeline is separately approved.

## 15. Recommended next destination

1. ✅ **First technical debt — DONE (2026-06-08):** Q-0026 implemented (`cog_name_to_subsystem` snake_case + `server_management` rename + the latent `proof_channel`/`four_twenty` repair). The decided `scripts/new_subsystem.py` (Q-0025) can now safely assume canonical snake_case multi-word keys.
2. ✅ **Phase 0 access/read-model contract — DOCUMENTED (2026-06-08):** precedence, reason schema (reusing the `command_access` decision model — no second permission system), drift-provider ownership, simulation limits, and the direct-vs-draft rule are in §16 below + [`docs/ownership.md`](../ownership.md). Q-0028–Q-0032 stay at safe defaults (not blockers for read-only work).
3. ✅ **P1A — DONE (2026-06-08):** the side-effect-free Access Map projection service (`services/access_projection.py`) + 19 tests per §16 (no UI, no persistence). ✅ **P0C — DONE (2026-06-08, #592):** all six role-threshold write sites route through the audited `role_automation.set_{time,xp}_threshold` seam; drift-fence allowlist emptied (§16.5). ✅ **P1B `routing_access_conflict` — DONE (#592)**; **skipped** `configured_resource_missing` (already covered by the four existing collectors — §9 row). **UNBLOCKED 2026-06-09 — next:** P1B's `help_advertises_locked` (audience sim decided: governance tier-input path, **Q-0045**) + the denial-copy integration (**Q-0036**: Claude drafts, maintainer reviews in PR); then **P1C** (read-only Access Map + Help Preview, as **staff-hub subpanels only — no new command names**, Q-0032). Read §16.8 before P1B/P1C.
4. **Blocked/gated:** controlled profile/access mutation waits for the read model and rollback/risk decisions; Routine Engine waits for condition/safety design; Personal Setup waits for privacy decisions; AI drafts wait for current AI expansion gates.

## 16. Phase 0 access read-model contract (P0B)

> **Status:** contract documented 2026-06-08 (P0B); **P1A service implemented 2026-06-08** —
> `services/access_projection.py` (+ `tests/unit/services/test_access_projection.py`) realizes
> this contract (read-only composed projection; no UI, no persistence). The governance axis
> **reuses** `governance.get_visible_subsystems` — the same read the existing
> `views/access/explorer.py::AccessExplorerView` (governance-axis-only diagnostic) uses — so a
> future read-only Access Map panel (P1C) can compose the multi-axis projection without a second
> visibility resolver. This section is the spec that service realizes. It is *read-only*: it defines
> how to **compose existing owners**, never a new policy. **Reuse the existing
> decision/reason vocabulary** (`core.runtime.command_access.DecisionReason` /
> `DecisionSource`) — do **not** fork a parallel enum. Source types win over this
> section; verify signatures before coding.

### 16.1 Service family (side-effect-free)

Five read-only collaborators (no god service, no persistence):

1. **Feature inventory adapter** — enumerates features from
   `utils.subsystem_registry.SUBSYSTEMS` + `core.runtime.command_surface_ledger`
   (the now-snake_case keys from Q-0026). Yields `(subsystem, command/entry_point,
   owning cog, visibility_tier)`.
2. **Access context** — one explicit, fully-specified input record (no implicit
   globals). Superset of the existing `command_access.CommandAccessContext`
   (`guild_id`, `channel_id`, `user_id`, `command_name`, `invocation_type`,
   `is_guild_operator`, `is_bot_owner`, `is_dm`) plus `category_id`,
   `member_role_ids`, `member_tier`, and an optional `now`/`event_state` for the
   future availability axis. Building a context performs **no** I/O beyond what the
   wrapped resolvers already do.
3. **Projection resolver** — composes the axes below into one structured
   `AccessDecision` per (feature, context). Pure composition; calls each owner's
   existing async resolver and records its native decision.
4. **Explanation renderer** — turns an `AccessDecision` into (a) an Access Map row,
   (b) a Help Preview annotation, or (c) a user-safe denial string. The renderer is
   the **only** place a `LockedReason.safe_text` is produced for users.
5. **Drift providers** — compare two owners' projections and emit read-only findings
   (§16.5). They never write; repairable findings become `SetupOperation` *proposals*
   per the `setup_diagnostics` pattern.

The **draft compiler(s)** of §4.1 item 6 are **out of scope** until the projection
stabilises (Phase 3).

### 16.2 Composition precedence (the axis order)

The projection evaluates axes in this fixed order and **short-circuits on the first
`deny`/`unavailable`** — matching the order the runtime actually gates so the read
model can never claim "allow" where the runtime denies (the core
help-advertises-locked guard). Each axis delegates to its existing owner:

| # | Axis | Owner (existing) | Produces |
|---|---|---|---|
| 1 | Hard safety / lifecycle / bootstrap | `command_access.resolve_command_access` (lifecycle-drain, bootstrap-bypass branches) | `deny`(silent) / bypass-`allow` |
| 2 | Command access (channel admission) | `command_access.resolve_command_access` (`DB_POLICY` / `DEFAULT_UNCONFIGURED`) | `allow` / `deny` + `DecisionReason` |
| 3 | Cog routing (feature enabled here) | `services.command_routing.is_cog_enabled` | `allow` / `deny` |
| 4 | Governance visibility + capability/tier | `governance.resolver.resolve_visibility` / `get_visible_subsystems` + capability resolver | `visible+permitted` / `hidden` / `tier-insufficient` |
| 5 | Availability policy (time/tenure/event) | **future** central resolver (§6.6) — absent today ⇒ axis returns `allow`/`unknown` | `allow` / `deny`(window) |
| 6 | Help classification (help axis only) | `command_surface_ledger.is_hidden_from_help` | `shown` / `hidden` (does **not** affect execution) |
| 7 | User preference (Phase 5) | **future** — can hide/sort, **never grant** | re-order / hide only |

Axis 6 is informational for the *help-visibility* column only; it must never turn an
executable `allow` into a denied execution result. Axis 7 is Phase 5 and likewise
cannot elevate.

### 16.3 Decision & reason schema

```text
AccessDecision (frozen):
    feature:      str            # subsystem key (snake_case) or command name
    effective:    "allow" | "deny" | "unknown"
    deciding_axis: AccessAxis    # which numbered axis produced `effective`
    source:       DecisionSource # REUSE command_access.DecisionSource where the
                                 # axis is command-access; each other axis maps its
                                 # native source into a small shared AccessAxisSource
    reason:       LockedReason | None
    source_chain: tuple[AxisOutcome, ...]   # every axis evaluated, in order, for "why"
    remediation:  str | None     # safe pointer to the owning panel/setting, never a write

LockedReason (frozen) — minimum fields (per §6.3):
    code:        str             # stable id, drawn from the union of DecisionReason
                                 # values + {routing_disabled, capability_insufficient,
                                 # subsystem_hidden, availability_window, quiet_mode,
                                 # setup_stage_required}
    safe_text:   str             # user-renderable; NEVER leaks role names / channel ids /
                                 # policy internals
    source:      str             # command_access | routing | governance | availability |
                                 # bootstrap | help
    unlock_hint: str | None      # only when safe to show (e.g. "unlocks after 24h")
```

Reason `code`s reuse `command_access.DecisionReason` verbatim for axes 1–2
(`allowed`, `bootstrap_bypass`, `lifecycle_draining`, `dm_not_supported`,
`channel_not_allowed`, `commands_disabled`); axes 3–5 add the small stable set listed
above. **Do not invent per-feature codes.**

### 16.4 Simulation limits (Help Preview)

Help Preview (staff/admin only — Q-0023) supplies a **simulated** audience context
(member tier + role set) to the *same* axes. It must label that it cannot model
live Discord channel-permission overrides it has not been given, must never imply a
permission it cannot accurately resolve, and renders axis-6 (`hidden`) honestly
("shown as locked, with reason"). Normal users get no simulator — only the live
axis-1→5 denial string from the renderer.

### 16.5 Drift providers and the P0C drift selection

Phase 0/1 drift providers (read-only findings; extend `setup_diagnostics`):

- **`identity_mismatch`** — a subsystem key disagrees across registry / ledger / hub /
  view / anchor surfaces (the Q-0026 *class* of bug; now guarded by the
  command-surface-ledger identity tests).
- **`help_advertises_locked`** — help shows a command the projection says is `deny`
  for the baseline audience (and not deliberately shown-as-locked).
- **`routing_access_conflict`** — cog routing enables a cog whose commands command-
  access denies in every channel (or vice-versa).
- **`configured_resource_missing`** — a bound channel/role referenced by config no
  longer exists.

**P0C drift selected for normalization (the answer to §4.2 item 4):** the
**role-threshold writer**. The role panels/cog wrote time/XP thresholds via a *direct
DB write* (`utils.db.roles.set_role_threshold` / `set_role_xp_threshold`) rather than
the audited `role_automation` seam, so there was no single canonical seam for a future
profile/routine draft to compile into.

> ✅ **P0C DONE (2026-06-08).** All six sites below now route through
> `role_automation.set_{time,xp}_threshold`; the drift-fence allowlist is empty (the
> invariant is now the absolute rule). Two implementation notes for the next agent:
> (1) the seam's `role_id` was relaxed to `int | None` so the legacy free-text
> `!setrole` path (role may not exist) keeps a name-only write, audited, with the
> audit `target` falling back to the role name; (2) the created-role XP companion
> (`creation_panel`) now threads the freshly-created role id through, closing the old
> name-only write that would orphan the tier on a rename. The recipe below is retained
> as the record of what was converted.

*Turn-key recipe (as executed; line numbers drift — find by symbol):*

- **The audited seam already exists** in `services/role_automation.py`:
  `set_time_threshold(*, guild_id, role_id, role_name, days, actor_id, actor_type="user")`
  and `set_xp_threshold(*, guild_id, role_id, role_name, level, actor_id,
  actor_type="user", auto_assign=True)`. Each does the **identical**
  `utils.db.roles.set_role_threshold*` write **plus** `emit_audit_action(...)` (and
  `set_xp_threshold` also invalidates the XP-threshold cache); both return a
  `mutation_id`. So each swap is **behavior-preserving for the write + additive (audit)**.
- **The 6 direct-write call sites (the punch list):**
  1. `views/roles/time_roles_panel.py` ~:139 — *Seed Defaults* button (time) → `actor_id=interaction.user.id`.
  2. `views/roles/time_roles_panel.py` ~:226 — `TimeDaysModal.on_submit` (time) → `actor_id=interaction.user.id`. *(Keep the existing surrounding cache-invalidation call.)*
  3. `views/roles/_helpers.py` ~:67 — `_ensure_defaults(guild)` system-seed (time, **no interaction**) → `actor_id=None, actor_type="system"`.
  4. `views/roles/creation_panel.py` ~:168 — (xp) → `actor_id=interaction.user.id`.
  5. `views/roles/xp_roles_panel.py` ~:183 — (xp) → `actor_id=interaction.user.id`.
  6. `cogs/role_cog.py` ~:454 — prefix-command path (time) → `actor_id=ctx.author.id`.
- **Drift fence / progress tracker:** `tests/unit/invariants/test_no_direct_role_threshold_writes.py`
  pinned exactly these 5 files; `_ALLOWED_DIRECT_THRESHOLD_FILES` is now **empty**, so
  the invariant is the absolute rule — any direct `utils.db.roles.set_role_threshold*`
  call in the scanned role surface fails CI.
- **Tests to update:** the role-panel/selector tests that currently assert
  `db.set_role_threshold*` is called (e.g. `tests/unit/views/test_role_threshold_selectors.py`)
  → assert the `role_automation.set_{time,xp}_threshold` call instead.
- **Out of scope for P0C:** channel create/edit lifecycle (mixed direct-Discord +
  `ChannelLifecycleService`) is the secondary, larger gap — assess but do **not** rewrite
  wholesale here.

See the binding rule + drift note in [`docs/ownership.md` § "Direct vs. draft mutation lanes"](../ownership.md).

### 16.6 Invalidation / caching

Compute on demand; **do not persist** the projection (a read model is not a source of
truth — see §10 and §11). Cache **only** with an explicit invalidation owner: the
projection cache (if any) must be invalidated on a `command_access_service` write, a
routing write, a governance/capability write, a settings write, and process restart
(registry change). Absent an explicit owner for every one of those, do not cache.

### 16.7 Negative-architecture guardrails (P1A tests must assert)

- The projection module performs **no** writes and imports **no** mutation service or
  Discord resource API (AST/negative test).
- It defines **no** new permission/visibility *policy* — every `allow`/`deny` traces
  to an existing owner in the §16.2 table (the source_chain makes this auditable).
- `LockedReason.safe_text` never contains a role name, channel id, or raw policy field
  (redaction test over a fixture with sensitive values).
- Help-visibility (axis 6) can never flip an execution `allow` to a denied result.

### 16.8 Notes for the next agent (refinements learned building P1A, 2026-06-08)

The P1A service (`services/access_projection.py`) is built and tested. Four refinements
surfaced during the build that change how P1B/P1C should be scoped — read these before
starting them:

1. **Drop `identity_mismatch` from P1B — it's already covered.** Subsystem-key agreement
   across registry/ledger/view/router/anchor is enforced by
   `governance`-side `validate_identity_contract` **and** the command-surface-ledger
   identity tests (added in the Q-0026 PR). Building a fourth identity checker would
   duplicate. The real P1B drift work is the other three providers
   (`help_advertises_locked`, `routing_access_conflict`, `configured_resource_missing`).

2. **The P1B drift providers are RUNTIME (per-guild), not static.** They compare
   *effective* projections, and the projection's command-access / routing / governance
   axes all read **live per-guild DB policy** — there is no meaningful static answer
   without a guild + member. So these providers belong in `setup_diagnostics` as
   per-guild findings (each runs `resolve_feature_access` against the live guild), not as
   import-time/static checks. Test them with patched resolvers (as the P1A tests do).

3. **Audience simulation — DECIDED 2026-06-09 (Q-0045): option (b), the governance tier-input path.** ✅ **IMPLEMENTED (PR #632, 2026-06-09):** `GovernanceContext.member_tier` is the declared-tier input; `resolver._resolve_member_tier` prefers it verbatim (member derivation + role grants skipped — the caller declares the *effective* standing; invalid values ignored with a warning, never escalating), and the projection's governance axis consumes `AccessContext.member_tier` (member-less + declared tier now evaluates instead of `unknown`, with the §16.4 limit label on the chain detail). The visibility cache keys on the resolved tier, so declared-`user` and a real user-tier member share one cache entry and one answer. P1C Help Preview builds on this as-is. (Original trade-off kept below for context.)
   The governance axis calls `governance.get_visible_subsystems(GovernanceContext)`, which
   needs a **real `discord.Member`** (it derives the tier + roles from the member object).
   Help Preview (Q-0023) and the drift "baseline audience" want to simulate an audience **by
   tier/role set**, not a real member. `AccessContext.member_tier` exists as a forward hook
   but **is not consumed yet**. Before P1C, pick one: (a) synthesize a member-like object
   from the simulated tier/roles and pass it through, or (b) add a tier-input read path to
   governance and have the governance axis prefer `ctx.member_tier` when set. Option (b) is
   cleaner but touches governance; option (a) keeps the change in the projection. Either way
   the simulation must still **label its limits** (it can't model live channel-permission
   overrides it wasn't given — §16.4).

4. **`project_access_map(ctx)` is the batch surface for the P1C table.** It maps
   `resolve_feature_access` over `feature_inventory()`; a read-only Access Map panel renders
   its rows. The per-feature `AccessDecision.source_chain` is the "why" the row's detail
   view shows. There is **no** diagnostics provider / boot import wired yet (the projection
   is per-request) — P1C wires the first consumer.

#### Further P1B refinements (source-verified during the P0C session, 2026-06-08)

Reading `services/setup_diagnostics.py` + `services/access_projection.py` end-to-end to
scope P1B surfaced three things that **re-scope the P1B drift batch** — read these before
starting it (they're the same "verify against source before building" lesson as items 1–4):

5. **`configured_resource_missing` is ALREADY covered — do not build a fourth detector.**
   `setup_diagnostics` already flags "a bound channel/role referenced by config no longer
   exists" across **all four** existing collectors: `_diagnose_bindings`
   (`stale_binding` / `missing_required_binding`, via `resource_health.inspect`),
   `_diagnose_role_thresholds` (`stale_role_threshold`), `_diagnose_moderation_roles`
   (`stale_moderation_role`), and `_diagnose_cleanup` (`stale_cleanup_policy`). A general
   `configured_resource_missing` provider would duplicate this — exactly the situation item
   1 found for `identity_mismatch`. **So the genuinely-new P1B drift work is just the
   remaining TWO providers** (`routing_access_conflict`, `help_advertises_locked`).

6. **Of those two, `routing_access_conflict` is built ✅ (2026-06-08); `help_advertises_locked`
   still depends on the item-3 audience decision.** ✅ **`routing_access_conflict` shipped** as
   `setup_diagnostics._diagnose_routing_access_conflict` — a read-only, **member-independent**
   collector that composes the two *policy owners directly* (the command-access
   `CommandAccessPolicySnapshot` + `command_routing.list_for_guild`), not `resolve_feature_access`
   (the projection short-circuits on the first deny, so it can't expose the routing↔access
   *disagreement*; the policy-level read does). Conflict semantics: command access in
   `selected_channels` mode + a channel-scoped `enabled` routing row for a non-allowed channel
   = "enabled-but-unusable" (warning); `disabled_except_bootstrap` mode + any `enabled` routing
   toggle = a guild-level advisory. ✅ **`help_advertises_locked` shipped too (PR #632,
   2026-06-09, on the item-3 tier path)** as `setup_diagnostics._diagnose_help_advertises_locked`.
   Semantic learned building it (source-verified): help menus + typed routes already filter
   through `resolve_visibility` per member, so *"advertised to the baseline audience"* =
   **ledger-shown ∧ governance-visible at tier `user`** (one up-front `get_visible_subsystems`
   call on the Q-0045 path — needed because the projection short-circuits on a routing deny
   *before* its governance axis runs). A governance/tier lock is therefore the "deliberately
   shown-as-locked" exclusion realized through the canonical owner — **the per-feature drift
   that remains is the routing axis** (advertised but routed off), plus one guild-level finding
   per guild-wide command-access lock (disabled-except-bootstrap advisory / empty-selected-
   channels warning). `unknown` never produces a finding; selected-channels scans evaluate in
   the lowest allowed channel id so a channel-scoped deny can't masquerade as a guild lock;
   every finding carries the §16.4 simulation-limit note verbatim.

7. **The "locked-reason denial integration" changes user-facing denial messages — confirm the
   wording with the maintainer first (it's his UX domain).** Wiring `LockedReason.safe_text`
   into the live command-access / availability denial paths changes what *every* denied user
   sees. The maintainer designs/visualizes UX (he audits by clicking and saying "X should be
   Y"), so the `_SAFE_TEXT` copy table in `access_projection.py` is a **draft to confirm**,
   not a silent swap. The read-only drift providers (items 5–6) don't touch this and can land
   independently of it.
   📝 **Draft complete (PR #632, 2026-06-09, per Q-0036):** `_SAFE_TEXT` now covers the full
   §16.3 code union (added `capability_insufficient`, `quiet_mode`, `setup_stage_required`;
   refined `routing_disabled` to scope-neutral wording) and the full table is presented in the
   PR #632 body for the maintainer's read-through. **Still NOT wired into any live denial
   path** — the live command-access feedback strings are unchanged; wiring is a follow-up
   commit after his markup.
