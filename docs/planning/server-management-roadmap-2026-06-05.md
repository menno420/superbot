# Server Management Roadmap

> **Status:** `plan` — source-grounded planning document; no production behavior is changed by this document.
> **Audit date:** 2026-06-05
> **Intended direction:** evolve SuperBot into a coherent, service-owned, button-first Guild OS without duplicating existing setup, governance, resource, or mutation systems.
>
> ---
>
> **⚠️ PR ordering superseded after #523 (2026-06-05).** This roadmap remains the
> **target architecture** and its seven maintainer decisions still stand, but the
> "Proposed PR Sequence" (Phase 0–5) below is **no longer the execution order**. The
> implementation plan (#521) re-sequenced the work to lead with moderation
> convergence, and that sequence is what shipped (#521–#523). For *what is actually
> done and what is next*, read **`docs/planning/server-management-status-2026-06-05.md`**
> (the live status tracker); for per-PR scope detail read
> **`docs/planning/server-management-implementation-plan-2026-06-05.md`**.

## Audit Base

- **Branch:** `work`
- **Commit:** `23b0f365058fd574c5e736ec15378e7444be1b76`
- **Date:** 2026-06-05
- **Recent merge context:** PRs #517–#519 landed capability-native authority, target-guild panel authorization, and related documentation immediately before this audit.
- **Scope:** channel/category management, roles and role automation, moderation, cleanup policy and manual cleanup, setup, logging/audit, governance/visibility, guild resources, selectors, diagnostics, and help/menu discovery.
- **Non-goals:** no production implementation, migration, unrelated game/economy/AI expansion, or claim that an aspirational document is shipped behavior.

### Evidence policy

This roadmap treats source code and migrations as authoritative. Existing docs were used to discover contracts and intended direction, then checked against source. Binding architecture contracts include `docs/architecture.md`, `docs/ownership.md`, `docs/runtime_contracts.md`, and `docs/helper-policy.md`. In particular:

- moderation actions are owned by `services/moderation_service.py` (`docs/ownership.md:36`);
- cleanup-policy writes are owned by `GovernanceMutationPipeline` (`docs/ownership.md:40,90`);
- cogs are adapters and cross-subsystem orchestration belongs in services/pipelines;
- persistent views must obey the restoration and interaction contracts in `docs/runtime_contracts.md`;
- reusable selector behavior belongs in shared view primitives, while domain mutation behavior belongs in services.

## Maintainer Decisions Incorporated

The following decisions are settled for this roadmap:

1. Time-based and XP roles remain together in one **Role Automation** management section, while their mutation semantics must not destructively interfere with each other.
2. Threads do not store cleanup overrides. A thread inherits cleanup policy from its parent channel, then category, guild, and platform default.
3. Role templates are optional. SuperBot should offer deterministic built-in templates and an on-request AI role-template generator with explicit accept/reject/edit/preview/apply gates.
4. Resource provisioning remains focused on create-or-reuse plus binding. Channel and role lifecycle mutations are separate coordinated domain services rather than an oversized provisioning pipeline.
5. The Server Management Hub has two delivery modes over one shared builder: a persistent prefix-command panel and an ephemeral slash-command panel.
6. Discord mutations do not claim transactional rollback. SuperBot snapshots relevant prior state, classifies reversibility, audits every step, automatically compensates only narrow low-risk operations, and otherwise offers a confirmed **Revert Safe Changes** or repair plan.
7. Moderation remains a lightweight append-only action log initially. The design must leave room for future numbered cases, evidence, review, and appeals without making a case-system migration a prerequisite.

## Executive Summary

SuperBot already has much of the platform foundation required for a Guild OS:

- centralized channel and role resource lookup services;
- guild snapshots, resource health, recommendations, and audited provisioning;
- setup sessions, drafts, deterministic operations, recommendations, final review, and readiness checks;
- governance-owned visibility and inherited cleanup policy;
- reusable selectors, multi-select primitives, hubs, persistent panels, and navigation;
- a central moderation service and role-automation service;
- audit events and server logging primitives.

The remaining problem is primarily **convergence and ownership**, not absence of features. Channel and role managers still contain direct Discord mutations; reusable selectors are fragmented and capped at the first 25 resources; time roles use role names and hardcoded defaults; the moderation cog bypasses the central moderation service; cleanup policy is inherited but too coarse; and setup does not yet provide first-class role, moderation, governance, and repair sections.

The recommended sequence is foundations first:

1. establish shared dynamic resource selection and manageability diagnostics;
2. establish channel/category and role lifecycle mutation services;
3. route existing surfaces through canonical owners;
4. add movement, role-template, cleanup-policy, and moderation-policy capabilities;
5. make setup the guided control plane over those primitives;
6. add one Server Management Hub over the specialized managers.

The first implementation phase must not be a new hub or a new move button. It must make resource selection, safety evaluation, preview/apply, audit, and partial-failure behavior reusable and dependable.

## Shipped, Aspirational, and Stale Claims

### Confirmed shipped foundations

- `ResourceProvisioningPipeline` has typed requests, preview, explicit confirmation for creates, result records, audit, and binding behavior (`disbot/services/resource_provisioning.py:145-153,187-230,238-247`).
- Setup sections are registry-driven and own domain-specific `SetupOperation` batches rather than requiring a giant hardcoded hub (`disbot/services/setup_sections.py:1-24,40-97`).
- Setup has server scan, recommendations, draft replacement, final review, readiness, and provisioning views under `disbot/views/setup/` and `disbot/services/setup_*`.
- Cleanup setup supports guild/category/channel policies and named batch profiles (`disbot/views/setup/sections/cleanup.py:1-13,385-400`; `disbot/services/cleanup_profiles.py`).
- Governance cleanup resolves channel, category, and guild policy with fallback (`disbot/governance/cleanup.py:22-57`).
- Channel delete and restriction panels already use a shared multi-select primitive (`disbot/views/channels/delete_panel.py:57-61`; `disbot/views/channels/restrict_panel.py:54-58`).
- Role exemptions already use a native multi-role select with up to 25 roles (`disbot/views/roles/exemptions_panel.py:22-29`).
- Moderation has a central service that writes an append-only log and emits `moderation.action_taken` (`disbot/services/moderation_service.py:1-12,56-58`).
- Help/menu hooks and specialized hubs exist for channel, role, moderation, and cleanup surfaces.

### Confirmed gaps or stale assumptions

- A channel move operation does exist, but only as a single-channel typed command that changes category; it is not a move/reorder panel or lifecycle pipeline (`disbot/cogs/channel_cog.py:325-335`).
- Cleanup inheritance is more mature than “not configurable at all,” but its policy vocabulary is narrow and thread persistence is intentionally absent (`disbot/governance/cleanup.py:29-42`; `disbot/migrations/004_governance_tables.sql:24-32`).
- Setup is not a giant hardcoded cog; its registry/draft design is already the correct convergence point. The gap is missing domain sections and shared primitives, not a need to replace setup.
- Resource provisioning is not a general lifecycle mutation owner. It handles declared resource creation/reuse and binding, not arbitrary rename, move, reorder, overwrite, assignment, or deletion.

## Current Architecture Map

| Area | Main shipped owners | UI/command surfaces | Important tests |
|---|---|---|---|
| Channel/category management | `cogs/channel_cog.py`, `views/channels/**`, `core/resources/channel_service.py`, `utils/channels.py` | `!channelmenu`, typed create/delete/list/move/rename/lock/permissions/bulk commands | `tests/unit/cogs/test_channel_list_paginate.py`, `tests/unit/resources/test_channel_service.py` |
| Role management and automation | `cogs/role_cog.py`, `views/roles/**`, `core/resources/role_service.py`, `services/role_automation.py`, `services/role_exemption_service.py` | role hub, management, time roles, XP roles, exemptions, diagnostics, reaction roles | `tests/unit/services/test_role_automation.py`, `test_role_exemption_service.py`, role view/cog tests |
| Moderation | `cogs/moderation_cog.py`, `views/moderation/**`, `services/moderation_service.py`, `utils/db/moderation.py` | `!modmenu`, `/moderation`, warn/timeout/kick/ban/unban/clearwarnings/modlogs | `tests/unit/services/test_moderation_service.py`, `tests/unit/db/test_moderation_db.py` |
| Cleanup | `cogs/cleanup_cog.py`, `cogs/cleanup/panel.py`, `governance/cleanup.py`, `services/cleanup_levels.py`, `cleanup_profiles.py`, `history_cleanup.py` | cleanup panel, typed cleanup history, setup cleanup section | cleanup cog, governance scope, profiles, runtime cleanup tests |
| Setup | `cogs/setup_cog.py`, `views/setup/**`, `services/setup_*`, setup DB helpers | setup wizard, registered sections, scan, AI review, final review | extensive setup service/view/invariant tests |
| Governance/access | `governance/**`, command access services/runtime, visibility panel | channel visibility, settings/setup/governance surfaces | governance and schema tests |
| Resource runtime/provisioning | `core/runtime/guild_resources.py`, `core/resources/**`, `services/resource_health.py`, `resource_provisioning.py`, catalogue | setup provisioning and diagnostics consumers | resource, health, provisioning, invariant tests |
| Shared UI/selectors | `views/base.py`, `views/navigation.py`, `views/selectors/**`, panel/session/navigation runtime | reused unevenly across managers | selector owner and view tests |
| Logging/audit/diagnostics | `services/server_logging.py`, domain audit tables/events, diagnostic views | logging hub, specialized diagnostics | server logging, audit alignment, resource health tests |

## Capability Matrix

| Capability | Exists? | Current owner | UI surface | Dynamic per guild? | Multi-select ready? | Configurable? | Main gaps |
|---|---:|---|---|---:|---:|---:|---|
| List channels/categories | Yes | channel cog/resource service | typed list | Yes | N/A | No | management panel lacks full inventory/health view |
| Create channels | Yes | cog/view direct Discord API; provisioning for declared resources | typed + panel + setup provisioning | Yes | panel supports multiple names | Partial | duplicate mutation paths; categories not first-class |
| Delete channels | Yes | cog/view direct Discord API | typed + panel | Yes | Yes in panel | No | no canonical lifecycle audit/compensation |
| Rename/edit channels | Yes, typed | channel cog | typed only | Yes | No | Partial | direct mutation; incomplete panel discovery |
| Move channel to category | Minimal | channel cog | typed only | Yes | No | No | no reorder/category move/preview/partial-failure handling |
| Category lifecycle | Partial | channel cog/helpers/provisioning | creation helper/setup | Yes | No | Partial | no coherent category manager |
| Channel restrictions/overwrites | Yes | cog/view direct Discord API | typed + panel | Yes | Yes in panel | Partial | no shared preview, overwrite diff, or audit owner |
| Role create/edit/delete | Yes | role cog/views direct Discord API | role management panel | Yes | Mostly no | Partial | no canonical role lifecycle owner |
| Role assignment/removal | Yes | role cog/views/automation | commands/panels/automation | Yes | Fragmented | Partial | hierarchy/manageability logic is not one shared contract |
| Time and XP automation | Yes | role cog, DB helpers, automation service | combined role hub sections | Partly | No | Yes | role-name identity; coupled row deletion; hardcoded defaults |
| Role templates | Hardcoded defaults only | role helper | reset defaults | No | No | No | must become optional, previewable templates |
| Moderation actions | Yes | service intended; cog still bypasses it | moderation hub + hidden typed commands | Yes | No | Partial | two mutation paths; limited policy/configuration |
| Moderation logs | Yes, append-only actions | moderation DB/service | `modlogs` | Yes | N/A | Limited | not a full case workflow; log channel/config gaps |
| Cleanup inheritance | Yes | governance cleanup/writes | setup cleanup section | Yes | Scope picks are single | Coarse | narrow policy vocabulary; explainability/preview gaps |
| Cleanup profiles | Yes | cleanup profiles/setup draft | setup profile picker | Yes | batch by generated operations | Yes, fixed profiles | no advanced policy builder |
| Manual history cleanup | Yes | cleanup cog/history service | typed command; panel gap documented | Yes | Filter/batch scan | Partial | incomplete hub discoverability and shared audit model |
| Setup scan/recommend/draft/apply | Yes | setup services/views | setup wizard | Yes | Batch operations | Yes | missing role/moderation/governance/repair sections |
| Resource diagnostics/repair | Partial | resource health/readiness/diagnostics | fragmented | Yes | N/A | Partial | no unified server-management diagnostic report |
| Unified management hub | No | — | — | — | — | — | specialized hubs are disconnected |

## Confirmed Problems

### P0 — Direct Discord mutations bypass intended service ownership

Channel cogs and views directly create, edit, delete, move, and change overwrites. Examples include channel creation/deletion and movement in `disbot/cogs/channel_cog.py:173-180,208,248,270,330-335,403-408,424-433,462`, creation in `disbot/views/channels/create_panel.py:198-219`, deletion in `disbot/views/channels/delete_panel.py:239`, and overwrite changes in `disbot/views/channels/restrict_panel.py:179`.

Role cogs/views similarly perform lifecycle mutations without one canonical role mutation owner. This prevents consistent preview, audit, partial-failure, compensation, and diagnostics.

### P0 — Moderation cog bypasses the shipped moderation service

The service is documented as the single audited path (`disbot/services/moderation_service.py:1-12`), but the cog directly calls warning DB helpers and Discord timeout/kick/ban/unban operations (`disbot/cogs/moderation_cog.py:126-142,145-226`). This produces inconsistent event and audit behavior.

### P0 — Resource selectors are fragmented and do not scale past 25 choices

The shared `RoleSelector` and `ChannelSelector` truncate to 25 and force a single value (`disbot/views/selectors/role.py:24-68`; `disbot/views/selectors/channel.py:20-66`). Feature views independently use custom selects, native selects, or `MultiSelect`. Filtering, hierarchy safety, stale validation, paging, search, and selected-result handling therefore vary by surface.

### P1 — Time-role configuration is name-based and seeded from hardcoded names

The time-role modal accepts a free-text role name and persists it even if no Discord role resolves (`disbot/views/roles/time_roles_panel.py:114-148`). Defaults are hardcoded names such as `Neu`, `Iron`, and `Beacon` (`disbot/views/roles/_helpers.py:26-34`). Renames and deletions create stale configuration risk.

### P1 — Time and XP role row semantics can interfere

Both automation types use `role_thresholds`; removing a time threshold deletes the whole row and explicitly invalidates XP cache because XP fields may also disappear (`disbot/views/roles/time_roles_panel.py:167-172`; `disbot/utils/db/roles.py:3-5,37-40`). They should remain one UI section but have independent field-level mutation semantics.

### P1 — Channel/category movement is not a management capability

`!move` only changes one channel's category (`disbot/cogs/channel_cog.py:325-335`). There is no category reorder, relative placement, multi-select batch, preview, or audited partial-failure plan. The channel hub only exposes create, delete, restrictions, and visibility (`disbot/views/channels/main_panel.py:49-136`).

### P1 — Cleanup is inherited but not expressive enough

The resolver effectively produces invalid-command deletion, delay, and feedback behavior (`disbot/governance/cleanup.py:38-57`). It does not express stale panels, successful command clutter, bot messages, links, invites, spam, repeated messages, caps/emojis, old-message retention, staff/pinned exemptions, or per-subsystem controls.

### P1 — Setup lacks complete server-management sections

Setup correctly uses registered sections and draft operations, but the current registered surface does not provide complete role automation/templates, moderation policy, governance/access, or unified diagnostics/repair sections. Setup should consume shared domain primitives rather than add direct mutations.

### P2 — Moderation is configurable only at a basic level

The moderation schema exposes warning threshold, warning timeout minutes, and a recommended mod-log channel (`disbot/cogs/moderation/schemas.py:33-77`). Moderator/trusted roles, reason rules, user DMs, evidence, escalation, delete-message behavior, and review policy are not first-class configuration.

### P2 — Help and hub discovery remain incomplete

Specialized hubs exist, but typed-only high-value operations remain. `docs/audits/cog-hub-coverage-audit.md` identifies `cleanuphistory` as a cleanup hub gap and defers a focused audit of the broader channel command set (`docs/audits/cog-hub-coverage-audit.md:65-81,163-177`).

## Target Architecture

### One control plane, multiple focused owners

```text
Persistent !servermanagement ─┐
                              ├─> shared Server Management Hub builder
Ephemeral /server-management ─┘
                                      │
           ┌──────────────────────────┼───────────────────────────┐
           ▼                          ▼                           ▼
    Setup guided flow         Specialized managers        Diagnostics/repair
           │                          │                           │
           └──────────────────────────┼───────────────────────────┘
                                      ▼
                         Shared schemas and selectors
                                      ▼
                    Domain mutation plans / preview / apply
            ┌─────────────────────────┼──────────────────────────┐
            ▼                         ▼                          ▼
 ResourceProvisioningPipeline  ChannelLifecycleService   RoleLifecycleService
 create/reuse + bind           channel/category ops      role/member-role ops
            │                         │                          │
            └─────────────────────────┼──────────────────────────┘
                                      ▼
                      audit events, results, diagnostics,
                    snapshots, safe compensation, repair plans
```

### Ownership rules

- **Cogs are adapters:** authorize, parse, defer, call a service, render a result.
- **Views compose primitives:** selectors, previews, confirmation, navigation, and result rendering; no direct Discord mutation.
- **Provisioning stays focused:** declared create/reuse plus binding.
- **Lifecycle services own Discord resource changes:** channel/category and role/member-role operations remain separate because their safety and failure semantics differ.
- **Setup orchestrates:** it stages plans and invokes owners; it never becomes the mutation owner.
- **Governance owns cleanup and visibility writes.**
- **Moderation service owns all moderation actions.**
- **AI proposes only:** AI output is validated, reviewed, and converted to ordinary staged operations before any apply.

## Shared Platform Primitives Needed

### 1. Dynamic guild resource selector framework

Create one configurable shared selector family for channels, categories, roles, threads, members, and mixed resource sets.

Required capabilities:

- live guild-state input and stable IDs;
- single- and multi-select modes;
- paging/search beyond Discord's 25-option limit;
- filters for kind, hierarchy, manageability, permissions, binding compatibility, scope, and deleted/stale state;
- structured exclusion reasons and counts;
- stale-selection revalidation before preview and apply;
- consistent owner/capability gating and error rendering;
- reusable selection summaries.

Consumers: time/XP roles, role templates, bulk assignment/removal, exemptions, channel movement, cleanup scopes, setup bindings, governance mappings, logging destinations, and repair flows.

### 2. Resource feasibility and diagnostics model

Define structured diagnostic findings rather than feature-specific strings:

- severity, code, resource kind/ID/name, explanation, remediation, and whether repair can be staged;
- bot lacks Manage Channels/Roles/Messages;
- bot role is below target role;
- managed/default/system role is unsafe;
- channel overwrite blocks the bot;
- category children are unsynced;
- stored binding/policy references a deleted resource;
- setup draft references stale state;
- moderation log destination is missing;
- move plan partially failed.

`resource_health`, setup readiness, specialized manager diagnostics, and the Server Management Hub should consume this shared model.

### 3. Mutation plan, preview, apply, and result contract

Every high-impact management operation should expose:

- typed request and normalized plan;
- side-effect-free preview;
- explicit warnings and required confirmation;
- ordered apply steps;
- per-step result and failure classification;
- mutation ID and audit event;
- snapshot references and safe-compensation classification;
- repair/revert-safe-changes suggestions.

Reversibility classes:

- **reversible:** restoring a prior name/color when permissions remain;
- **compensatable:** moving a channel back or restoring snapshotted overwrites, but without transaction guarantees;
- **irreversible:** deleting channels/roles/messages or kicking members.

Complex batches should stop according to an explicit policy and offer a confirmed **Revert Safe Changes** plan rather than silently attempting broad rollback.

### 4. Audit event standard

Each lifecycle service should emit a catalogued event with:

- mutation ID, guild ID, actor ID/type, resource IDs/kinds;
- operation type and normalized plan summary;
- outcome: success, partial, blocked, declined, Discord failure, or audit failure;
- before/after snapshot references where appropriate;
- failed step details and repair-plan availability.

Logging destinations and diagnostic dashboards consume these events; feature surfaces do not implement their own audit delivery.

## Channel / Category Management Roadmap

### Current state

- Typed commands cover create, bulk create/delete, delete, clone, move-to-category, list, info, rename, lock/unlock, and permission changes.
- The panel covers create, multi-delete, multi-restrict, and subsystem visibility.
- Categories are resolvable and usable during creation/movement but are not a first-class management surface.
- Channel listing is paginated, but selectors and mutation behavior are not consistently centralized.

### Target capabilities

1. **Unified channel/category inventory:** list text, voice, forum, stage, categories, and relevant threads with health, position, category, bindings, cleanup policy, visibility, and bot feasibility.
2. **Lifecycle operations:** create, rename, edit, clone, delete, permission changes, sync/unsync category permissions, move, and reorder through `ChannelLifecycleService`.
3. **Move / Reorder Channels panel button:**
   - select one or more channels or categories;
   - choose destination category or top-level area;
   - choose before, after, top, bottom, or preserve-batch-order strategy;
   - preview final ordering and permission/category-sync effects;
   - explicitly confirm apply;
   - log partial failures and offer safe repair/revert plans.
4. **First-class categories:** category creation, rename, delete, overwrite templates, child sync diagnostics, movement, and repair.
5. **Integration:** channel inventory shows setup bindings, cleanup inheritance, visibility, logging routes, provisioning ownership, and diagnostics without owning those domains' writes.

### Discord-safe movement rules

- Snapshot current positions and categories before preview.
- Revalidate target resources and permissions immediately before apply.
- Preserve selected batch order deterministically.
- Reject invalid mixed operations or normalize them explicitly.
- Warn when changing category may alter effective permissions or sync state.
- Never claim atomic reordering across Discord API calls.
- On partial failure, record the actual final state, then offer a safe compensation plan when feasible.

### Sequencing

1. shared selectors and diagnostics;
2. `ChannelLifecycleService` contracts and audit;
3. route legacy commands/views through service;
4. category-first inventory and lifecycle;
5. move/reorder planner and panel;
6. setup/cleanup/visibility integration and repair.

## Role Management Roadmap

### Current state

- The role hub contains management, time roles, XP roles, reaction roles, diagnostics, and exemptions.
- Time-role thresholds are name-based and can persist nonexistent names.
- Hardcoded time-role defaults seed static names.
- Role selectors and safety filters differ by surface.
- Role automation has a service, but lifecycle and member-role mutations are not one canonical owner.

### Combined Role Automation section

Keep time and XP automation in one section with focused subsections:

- Time / tenure roles
- XP / level roles
- Stacking behavior
- Automation exemptions
- Role templates
- Diagnostics

Persistence may remain in a shared table, but mutations must be field-specific:

- removing time configuration clears time fields only;
- removing XP configuration clears XP fields only;
- delete the shared row only when no active automation fields remain;
- move toward stable role IDs plus display-name snapshots;
- diagnose renamed, deleted, managed, or newly unmanageable roles.

### Dynamic role selector

The canonical selector must:

- load current guild roles;
- exclude `@everyone`, managed/integration roles, unsafe system roles, and roles the bot cannot manage;
- optionally enforce actor hierarchy for manual staff actions;
- show why roles are excluded;
- support search/pagination and multi-select;
- be reused by automation, assignments, exemptions, governance, setup, cleanup exemptions, and templates.

### Optional deterministic role templates

Built-in templates are opt-in suggestions, never automatic creation. Examples:

- basic community hierarchy;
- moderation team;
- gaming/event community;
- time-role progression;
- XP-role progression;
- support server.

Operators can bind matching existing roles, edit the suggestion, or stage previewed creation.

### AI-generated per-guild role templates

Add **Generate with AI** to the role-template manager. Example request:

> “Bloons/monkey-themed time roles, about 10.”

Flow:

```text
admin description + approximate count + intended use
→ existing AI gateway/advisor boundary
→ strict structured role-template output
→ deterministic validation and safety filtering
→ suggestion preview
→ accept all / reject all / review each / edit / reorder
→ choose bind existing or create new
→ stage ordinary role lifecycle + automation operations
→ final preview and explicit apply
```

AI must never directly call Discord, write role configuration, grant privileged permissions, or bypass lifecycle services. The structured suggestion should include role name, purpose, color, hoist/mentionable defaults, optional time/XP threshold, and no permissions unless a separately constrained future policy explicitly supports them.

Audit the original request, model/source metadata, validation changes, operator edits, accepted plan, and final apply result. Provide a deterministic fallback when AI is unavailable.

### Role lifecycle safety

`RoleLifecycleService` should own create, edit, reorder, delete, assign, and remove. It must centralize:

- bot and actor hierarchy checks;
- managed/default/integration role exclusion;
- stable-ID revalidation;
- batch member-role partial failures;
- before/after snapshots and compensation plans;
- audit events and repair diagnostics.

## Moderation Roadmap

### Current state

- Warn, timeout, kick, ban, unban, clear warnings, and log lookup exist.
- `moderation_service` is the intended central audited path, but the cog still performs direct mutations.
- Configuration covers warning threshold, timeout minutes, and a recommended mod-log resource.
- `mod_logs` is an append-only action log, while warnings are a mutable aggregate counter.

### Immediate convergence

- Route every cog/view moderation action through `moderation_service`.
- Centralize target safety, hierarchy, reason normalization, duration parsing, and policy evaluation.
- Emit one canonical event and append one canonical action record per successful moderation action.
- Keep cleanup separate: moderation owns staff discipline; cleanup owns message hygiene. A moderation action may request an explicit cleanup operation, but it must not duplicate cleanup policy logic.

### First-class moderation configuration

Add schema/policy-backed configuration for:

- moderator and trusted roles/capabilities;
- mod-log and optional public-log destinations;
- required or optional reasons;
- default and maximum durations;
- user-DM toggle and DM templates;
- warning escalation rules;
- ban delete-message behavior;
- evidence links/attachments when supported;
- post-action cleanup behavior;
- permissions and hierarchy diagnostics.

### Logs versus future cases

Near term, keep append-only moderation actions. Do not require a full case migration to improve moderation.

Design future-compatible identifiers and event metadata so a later case workflow can add:

- stable case numbers;
- evidence and staff notes;
- amendments without erasing original history;
- review/appeal/overturned status;
- related/escalated actions.

A future case design should use current case state plus append-only case events. It is a later product decision, not a blocker for service convergence or moderation configuration.

## Cleanup Roadmap

### Current state

- Governance owns cleanup-policy writes and scope resolution.
- Setup supports guild, category, and channel levels plus named profiles.
- Manual cleanup/history tools and prohibited-word management exist.
- Policy behavior is currently focused on invalid-command deletion/delay and feedback.

### Inheritance contract

```text
message in normal channel: channel → category → guild → platform default
message in thread/forum post: parent channel → category → guild → platform default
```

Do not persist thread cleanup rows. Diagnostics should still explain the parent channel and inherited source.

### Cleanup policy builder

Evolve coarse levels into versioned expressive policy while preserving existing behavior during migration.

Policy dimensions:

- failed commands;
- successful command prompts and bot command clutter;
- stale bot panels;
- bot-message retention;
- links and invites;
- spam, repeated messages, caps, and emoji flooding;
- old-message cleanup where Discord limitations permit;
- per-subsystem behavior;
- staff/member/role exemptions;
- pinned-message exemption;
- whitelist/blacklist behavior;
- delay, feedback, and log behavior.

Presets remain deterministic bundles: Minimal, Normal, Strict, Staff-heavy, Community, Game/Event, Bot Channel, and Moderation Evidence Safe.

### Explainability and safety

- Dry-run a policy against sample/recent messages without deleting.
- Explain “why deleted” and “why retained,” including inherited scope.
- Treat message deletion as irreversible.
- Log policy/rule/source and target message metadata within privacy/retention constraints.
- Distinguish automated policy actions from staff-initiated purge/history cleanup.
- Surface missing permissions and inaccessible channels in diagnostics.

## Setup Wizard Roadmap

### Role of setup

Setup becomes the **guided control plane**, not the owner of domain mutations and not a mega-cog. It composes:

- subsystem schemas;
- guild snapshots and recommendations;
- shared selectors;
- diagnostics and readiness;
- resource provisioning and lifecycle plans;
- setup drafts, preview, final review, apply, and repair.

### Required new/expanded sections

1. **Channels & categories:** bind existing, preview provisioning, inspect category/layout health, and link to advanced movement.
2. **Role automation & templates:** configure time/XP automation together, bind existing roles, choose optional deterministic templates, or request an AI-generated template.
3. **Moderation:** configure roles/capabilities, log destinations, escalation, DMs, reasons, and hierarchy readiness.
4. **Cleanup:** advanced policy/preset builder with inherited-scope visualization and dry-run.
5. **Governance & visibility:** role/capability mapping, command visibility, and routing through existing governance owners.
6. **Diagnostics & repair:** stage safe repairs for stale bindings, missing resources, invalid roles, and permission blockers.

### Re-run and repair behavior

- Setup is safe to rerun after onboarding.
- It distinguishes recommended rows from explicit operator customizations.
- It never overwrites custom choices silently.
- Repairs are staged and reviewed like other setup operations.
- Missing resources offer use-existing, previewed-create, skip, or link-to-manager choices.
- Final review groups operations by domain owner, risk, reversibility, and dependency.

## Server Management Hub

### Shared logical hub

The hub links to:

- Channel & Category Manager
- Role Automation & Templates
- Moderation Manager
- Cleanup Policy Builder
- Setup Wizard
- Logging & Audit Manager
- Governance & Visibility Manager
- Diagnostics & Repair

It shows compact health badges from resource health, setup readiness, stale-reference diagnostics, and bot permission feasibility.

### Delivery modes

#### Persistent prefix command

Primary command: `!servermanagement` with sensible aliases such as `!servermanage` and `!servermanager`.

- renders or refreshes a persistent admin panel in an appropriate/configured channel;
- restores after restart through existing persistent panel contracts;
- rechecks capability and target guild on every interaction;
- contains no domain business logic.

#### Ephemeral slash command

Primary command: `/server-management`.

- returns the same logical hub ephemerally;
- uses the same builders, services, capability gates, and health data;
- supports one-off administration without publishing/refreshing a persistent panel.

The two commands differ only in delivery and persistence, never in ownership or feature behavior.

## Proposed PR Sequence

> **Superseded as an execution order (2026-06-05).** The phases below capture the
> intended *grouping* of work, but the actual shipped sequence leads with moderation
> convergence per the implementation plan. Shipped so far: Phase 0 (PR 0 = #520);
> moderation convergence (PR 2A = #521); selectors partial (PR 1A = #522, model +
> `MultiRoleSelector` only); lifecycle contract + channel rename/move/delete
> (PR 1B + PR 2B = #523, partial). See
> `docs/planning/server-management-status-2026-06-05.md` for the live state and the
> remaining queue (starts at PR5).

### Phase 0 — Roadmap and contracts

**PR 0: Server-management roadmap only**

- Land this source-grounded roadmap.
- Ratify lifecycle-service boundaries, selector contract, reversibility vocabulary, and event naming before production code.

### Phase 1 — Shared resource safety foundation

**PR 1A: Dynamic selectors and manageability diagnostics**

- Add shared role/channel/category selector framework with paging/search and multi-select modes.
- Add structured feasibility/exclusion diagnostics.
- Adopt in one low-risk surface first, then expand.

**PR 1B: Mutation-plan and audit primitives**

- Add shared request/preview/result/step/failure/reversibility types.
- Add event catalogue entries and rendering helpers.
- Add invariants preventing new direct lifecycle mutations in cogs/views after migration begins.

### Phase 2 — Canonical domain owners

**PR 2A: Moderation convergence**

- Route moderation cog/views through `moderation_service`.
- Centralize target safety and duration/reason handling.
- Preserve current user-visible behavior while making event/audit behavior canonical.

**PR 2B: Channel/category lifecycle service**

- Own rename, overwrite changes, delete, clone, move, and reorder planning.
- Route existing channel commands/panels through it.
- Coordinate declared creation with provisioning rather than duplicating it.

**PR 2C: Role lifecycle service and role-ID automation groundwork**

- Own role create/edit/delete/reorder/member assignment.
- Centralize hierarchy safety.
- Add field-specific time/XP threshold mutations and stable-ID migration design.

### Phase 3 — High-value management capabilities

**PR 3A: Dynamic time/XP role configuration**

- Replace free-text role-name selection.
- Diagnose stale roles and make defaults optional templates.
- Keep one combined automation section.

**PR 3B: Channel/category move and reorder manager**

- Add panel button, multi-select, target/strategy choice, preview/apply, audit, and repair.

**PR 3C: Optional deterministic and AI role templates**

- Add template schema, validation, review/edit UI, built-in templates, AI generation through existing gateway, and staged operations.

### Phase 4 — Policy depth

**PR 4A: Cleanup policy schema/versioning**

- Define expressive policy model and migration preserving current behavior.
- Enforce parent-channel inheritance for threads.

**PR 4B: Cleanup builder, dry-run, and diagnostics**

- Add presets, scoped bulk assignment, explainability, and audit.

**PR 4C: Moderation configuration**

- Add roles/capabilities, destinations, reasons, DMs, escalation, delete-message policy, and diagnostics.

### Phase 5 — Setup convergence and hub

**PR 5A: Setup role/moderation/governance sections**

- Compose shared schemas, selectors, diagnostics, and operations.

**PR 5B: Setup diagnostics and repair**

- Stage safe repairs; improve readiness and stale-reference handling.

**PR 5C: Server Management Hub**

- Add shared hub builder, persistent prefix entry, ephemeral slash entry, health badges, and specialized-manager navigation.

## Risks and Migration Notes

### Discord permission and hierarchy races

Permissions, hierarchy, and resource existence may change between selection, preview, and apply. Every mutation must revalidate immediately before execution and report stale plans clearly.

### Role-ID migration

Moving automation from names to IDs requires conservative matching. Ambiguous or missing names become diagnostic findings requiring operator resolution; they must not silently bind to a guessed role.

### Cleanup migration

Existing cleanup levels must map to equivalent versioned policies so rollout does not change behavior. Thread inheritance requires no thread-row migration because rows should never be stored.

### Partial Discord failure

Discord-side batches are not transactions. Record actual completed steps, classify failed/unattempted steps, and offer safe compensation or repair. Never describe recreated deleted resources as rollback because IDs and external references change.

### Cache invalidation

Role rename/delete, channel/category movement/delete, binding changes, cleanup-policy changes, and setup apply must invalidate or refresh all relevant resource, governance, selector, and readiness caches.

### AI safety and availability

AI role templates are suggestions only. Enforce strict structured output, count/name/color constraints, duplicate detection, permission prohibition, hierarchy feasibility, rate limits, audit metadata, and deterministic fallback. AI failure must not block normal role management.

### Persistent panel authorization

The persistent hub and specialized panels must gate every callback using current capability and target-guild checks; permission at render time is insufficient.

### Privacy and retention

Moderation evidence, cleanup message metadata, and AI prompts may contain sensitive content. Define retention, visibility, redaction, and audit-channel policy before storing richer evidence or message samples.

## Verification Plan for Future Implementation

### Unit and invariant tests

- shared selectors: >25 resources, search/paging, multi-select, filters, exclusion reasons, stale selections;
- role feasibility: default/managed/integration roles, actor hierarchy, bot hierarchy, missing permissions;
- channel feasibility: Manage Channels, overwrite blockers, category sync, stale resources;
- lifecycle plans: deterministic ordering, preview purity, confirmation, per-step results, audit event shape;
- invariants: migrated cogs/views cannot directly perform owned Discord mutations;
- moderation: every action uses service, logs once, emits once, and handles Discord failures consistently;
- role automation: time and XP field mutations do not erase each other; role rename/delete diagnostics;
- cleanup: channel/category/guild inheritance, thread parent inheritance, presets, exemptions, dry-run explanations;
- setup: recommendation replacement, custom-choice preservation, stale drafts, repair staging, partial apply;
- AI templates: structured validation, unsafe output rejection, accept/reject/edit, no direct writes, gateway failure fallback.

### Integration/manual Discord checks

- bot role below/above target roles;
- large guild with >25 roles/channels/categories;
- channel/category movement with unsynced permissions;
- permission removed between preview and apply;
- partial batch failure and **Revert Safe Changes** preview;
- deleted binding/policy resource diagnostics;
- thread/forum post cleanup inheritance explanation;
- persistent `!servermanagement` restoration after restart;
- ephemeral `/server-management` parity and privacy;
- AI-generated themed time-role template review, edit, reject, and confirmed apply.

### Observability checks

- every mutation has a mutation ID and catalogued event;
- partial failures expose completed/failed/unattempted steps;
- audit destinations receive canonical summaries without duplicate feature-local logging;
- diagnostic findings include remediation and repair availability;
- metrics exist for blocked, failed, partial, compensated, and stale-plan outcomes.

## Completion Criteria

The server-management platform is coherent when:

1. cogs and views no longer own deep Discord resource or moderation mutations;
2. every manager and setup section uses the same dynamic selectors and feasibility rules;
3. channel/category and role operations support preview, audit, partial-failure reporting, and safe repair;
4. time/XP automation remains one section without destructive persistence coupling;
5. cleanup is expressive, inherited, explainable, and thread-parent based;
6. setup can scan, recommend, configure, rerun, and repair through shared domain primitives;
7. the persistent prefix hub and ephemeral slash hub expose the same specialized managers and health data;
8. AI role templates remain optional, reviewable suggestions that use ordinary staged mutation paths;
9. implementation tests and diagnostics make permission, hierarchy, stale-resource, and partial-failure behavior explicit.

## Open Questions

No unresolved maintainer decision blocks the proposed PR sequence. Future product decisions—such as whether moderation eventually becomes a numbered case workflow or which additional built-in role templates ship—can be made when their implementation phase begins without changing the foundational architecture above.
