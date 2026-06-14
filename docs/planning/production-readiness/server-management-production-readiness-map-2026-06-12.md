# Server Management — Production-Readiness Map (2026-06-12)

> **Status:** `audit` — source-verified production-readiness snapshot, not a replacement for the living server-management status tracker.
>
> **Scope:** setup, channel management, role management, moderation, cleanup, and the unified Server Management Hub. Source code and merged PRs win over this document.
>
> **Verdict:** **Partial / not yet production-ready as one end-to-end subsystem.** The unified composition, setup draft/apply lane, moderation convergence, role lifecycle service, cleanup policy controls, diagnostics composer, and most targeted unit/invariant coverage are Done. The main readiness blocker is the still-mixed channel mutation surface: direct channel creation, permission-overwrite, clone, and category paths remain outside one canonical audited lifecycle/provisioning seam. Production live verification and failure-path integration evidence are also incomplete.

## Current verified state

- Verified against the required docs, the scoped source paths, relevant unit/invariant tests, local git history, and the live GitHub pull-request API on **2026-06-12**.
- The only live open PR was **#704, “Screenshots from live testing the bot”**; it does not change setup or server-management source. No live open PR conflicts with this map.
- Relevant merged source history includes moderation convergence (#521), role feasibility (#522), channel lifecycle convergence (#523), cleanup versioning/presets/diagnostics (#549), setup moderation/roles (#570), the unified hub (#584), service-boundary fixes including role-threshold ownership (#652), Access Map + Help Preview (#656), and Help Preview projection correction (#671).
- Server management is **structurally complete** in the initiative tracker: PR10, PR11's approved moderation/roles scope, PR12, PR13's deterministic role-template slice, and PR14 are shipped. The PR13 AI-generation layer remains gated.
- Setup uses the sanctioned **draft → Final Review** lane. The setup operation contract currently has 18 op kinds, and parity is pinned across `services/setup_operations.py`, `utils/db/setup_draft.py`, and migration `059`'s `CHECK` constraint.
- No second role-threshold mutation path was found: setup applies thresholds through `services.role_automation.set_time_threshold` / `set_xp_threshold`; diagnostics remain advisory.
- Existing AST invariants pin no direct moderation writes, no direct role-object lifecycle mutations, no direct role-threshold writes, setup diagnostics/preflight read-only behavior, and the currently-owned channel `.edit()` / `.delete()` operations. The channel invariant explicitly does **not** yet cover `.set_permissions()`, `.clone()`, or creation.
- This review did **not** establish a new full production boot/live-walk baseline. “Done” below means implemented and source/test-backed, not independently live-verified in production during this review.

### Status meaning

| Status | Meaning |
|---|---|
| **Done** | Implemented through the intended ownership seam and backed by relevant automated evidence. Live-only behavior may still need a production walk. |
| **Partial** | Useful shipped behavior exists, but the area has a known ownership, UX, failure-path, integration, or live-verification gap. |
| **Not Done** | Required production behavior is absent, deliberately deferred, or gated. |

## Scope inventory table

### Composition, cogs, and entry points

| Item | Path | Type | Status | Reason | Evidence |
|---|---|---|---|---|---|
| Unified Server Management cog | `disbot/cogs/server_management_cog.py` | Cog / entry point | **Done** | Provides persistent prefix and ephemeral slash entry points and composes the canonical hub. | `tests/unit/services/test_server_management_hub.py`; `tests/unit/views/test_server_management_hub_view.py`; merged #584. |
| Unified Server Management Hub | `disbot/views/server_management/hub.py` | Panel / composition | **Done** | Composes moderation, channels, roles, cleanup, setup, Access Map, Help Preview, Help editor, and refresh behind an administrator interaction check and read-only badges. | Hub view tests; merged #584, #656. |
| Server-management health/read model | `disbot/services/server_management_hub.py` | Read service | **Done** | Central read-only badge composer; keeps health reads out of the hub view. | `tests/unit/services/test_server_management_hub.py`. |
| Access Map | `disbot/views/server_management/access_map.py` | Read-only panel | **Done** | Uses the access projection seam and is display-only. | Hub/access-map tests and display-only invariant coverage; merged #656. |
| Help Preview | `disbot/views/server_management/access_map.py` | Read-only panel | **Done** | Uses `project_help_with_execution`, including governance/overlay behavior and orphan reporting after the #671 correction. | Merged #671; projection tests outside this subsystem map. |
| Channel cog | `disbot/cogs/channel_cog.py` | Cog | **Partial** | Rich command surface and lifecycle routing for owned operations, but creation, clone, and overwrite mutations remain mixed/direct. | `tests/unit/invariants/test_no_direct_channel_mutations.py` explicitly excludes these remaining operations. |
| Role cog | `disbot/cogs/role_cog.py`; `disbot/cogs/role/` | Cog / schema | **Done** | Canonical role hub, automation listeners, reaction-role commands, hidden panel-action routes, and schemas are wired; role-object lifecycle writes route through the lifecycle service. | Role routing/lifecycle/threshold invariant tests. |
| Moderation cog | `disbot/cogs/moderation_cog.py`; `disbot/cogs/moderation/` | Cog / schema / helpers | **Done** | Prefix/slash/manual moderation surfaces converge on `moderation_service`; capability/permission OR-gate is pinned. | `test_no_direct_moderation_writes.py`; `test_moderation_role_authority.py`; merged #521. |
| Cleanup cog | `disbot/cogs/cleanup_cog.py`; `disbot/cogs/cleanup/` | Cog / panel / schema | **Done** | Exposes cleanup configuration, history scan, word controls, staged policy application, and the reusable cleanup panel. | Cleanup cog/panel/stage/history tests; merged #549. |
| Setup cog | `disbot/cogs/setup_cog.py`; `disbot/cogs/setup/` | Cog / entry flow | **Done** | Supports status, launcher/wizard entry, resume/recovery, delegation, final review, and setup lifecycle commands. | `tests/unit/cogs/test_setup_cog.py`; setup session/progress tests. |

### Setup flow, diagnostics, and operations

| Item | Path | Type | Status | Reason | Evidence |
|---|---|---|---|---|---|
| Setup launcher and workspace | `disbot/views/setup/launcher.py`; `disbot/views/setup/wizard.py`; `disbot/views/setup/hub.py` | Setup flow | **Done** | Provides launcher placement, linear wizard, section workspace, navigation, and authority-aware staging. | Setup cog/session/progress/view tests. |
| Draft rendering and Final Review | `disbot/views/setup/draft_render.py`; `disbot/views/setup/final_review.py`; `disbot/views/setup/provisioning/` | Apply gate | **Done** | Compound changes are previewed, confirmed, authority-rechecked, and applied through the sanctioned draft lane. | Setup operation/draft/final-review tests and ownership contract. |
| Setup operation dispatcher | `disbot/services/setup_operations.py` | Mutation orchestrator | **Done** | Validates, preflights, applies, audits, and reports typed setup operations through domain owners. | Setup operation, invariant, role-threshold, managed-role, cleanup/routing tests. |
| Setup op-kind three-place contract | `disbot/services/setup_operations.py`; `disbot/utils/db/setup_draft.py`; `disbot/migrations/059_setup_draft_op_kinds_role_templates.sql` | Persistence contract | **Done** | Dispatcher, DB gate, and migration `CHECK` are parity-pinned after the PR11 regression. | `tests/unit/db/test_setup_draft_op_kind_parity.py`. |
| Setup preflight diff | `disbot/services/setup_operations.py` | Read-only safety check | **Partial** | Default-on and read-only, but several known op kinds still report `no_adapter` instead of a real current/proposed diff. | `_preflight_*` dispatch and `tests/unit/invariants/test_setup_preflight_readonly.py`. |
| Setup diagnostics composer | `disbot/services/setup_diagnostics.py` | Diagnostic service | **Done** | Canonically composes isolated read-only collectors into typed findings and stages only safe repairs. | `tests/unit/services/test_setup_diagnostics.py`; read-only invariant; PR12. |
| Binding diagnostics and stale-binding repair | `disbot/services/setup_diagnostics.py` | Diagnostic / repair plan | **Done** | Detects stale, wrong-type, missing, unbound, permission, hierarchy, and unknown binding states; dead bindings can stage `clear_binding`. | Setup diagnostics tests. |
| Role-threshold diagnostics | `disbot/services/setup_diagnostics.py` | Diagnostic | **Done** | Detects stale/unassignable thresholds and intentionally stays advisory, avoiding a second threshold mutation path. | Setup diagnostics tests; no-direct-threshold invariant. |
| Moderation-role diagnostics | `disbot/services/setup_diagnostics.py` | Diagnostic | **Done** | Detects stale moderator/trusted role configuration and remains advisory. | Setup diagnostics tests. |
| Cleanup diagnostics | `disbot/services/setup_diagnostics.py`; `disbot/services/cleanup_diagnostics.py` | Diagnostic | **Done** | Detects ineffective and stale cleanup policy state without writing. | `tests/unit/services/test_cleanup_diagnostics.py`; setup diagnostics tests. |
| Routing/access and Help drift diagnostics | `disbot/services/setup_diagnostics.py` | Diagnostic | **Done** | Reports routing/access conflicts and Help-advertises-locked drift with simulation-limit labeling. | Setup diagnostics/read-only tests; #671 projection correction. |
| Setup recovery and summary | `disbot/views/setup/recovery.py`; `disbot/views/setup/summary.py` | Recovery / outcome UI | **Done** | Supports partial-apply recovery, per-operation outcomes, and explicit setup-channel deletion confirmation. | Setup completion/defer and recovery-related setup operation tests. |
| Server scan and readiness | `disbot/views/setup/scan_panel.py`; `disbot/views/setup/sections/server_scan.py`; `disbot/views/setup/sections/readiness.py` | Read-only setup flow | **Done** | Scans current guild resources/permissions and exposes readiness results without mutation. | Setup advisor/diagnostic read-only invariants and setup section tests. |
| Setup channel bindings section | `disbot/views/setup/sections/channels.py` | Setup section | **Done** | Selector-driven binding staging and recommendations route through setup operations. | `tests/unit/views/setup/sections/test_channels_section.py`; `test_setup_channel.py`. |
| Setup roles section | `disbot/views/setup/sections/roles.py` | Setup section | **Done** | Stages selector-driven time/XP thresholds through `set_role_threshold`; the historical DB-gate regression is fixed. | Roles-section, threshold-operation, and parity tests; merged #570/#584-era fix. |
| Setup moderation section | `disbot/views/setup/sections/moderation.py` | Setup section | **Done** | Stages moderation settings and moderator-role selection through `set_setting`. | `tests/unit/views/setup/sections/test_moderation_section.py`; merged #570. |
| Setup cleanup section | `disbot/views/setup/sections/cleanup.py` | Setup section | **Done** | Stages hierarchical cleanup policies and presets through the setup apply lane. | Cleanup-section and cleanup/routing operation tests. |
| Setup role templates | `disbot/services/setup_role_templates.py`; `disbot/views/setup/sections/role_templates.py` | Deterministic planner / setup section | **Done** | Built-in permission-free templates use pure planning and audited `create_managed_role`, optionally with one threshold companion. | Role-template service/view/operation tests; PR13 deterministic slice. |
| AI-generated role templates | Future PR13 AI layer | AI-assisted setup | **Not Done** | Explicitly gated by the AI-expansion gate; no implementation should be treated as missing production work until that gate is lifted. | `docs/current-state.md`; server-management tracker. |
| Setup governance section | Deferred PR11 scope | Setup section | **Not Done** | Deliberately deferred by owner decision Q-0008; not part of the approved shipped setup scope. | Server-management status tracker. |
| Other setup sections | `disbot/views/setup/sections/{identity,purpose,preset_select,logging_presets,cog_routing,ai_setup,btd6,suggestions}.py` | Setup sections | **Done** | Present and wired into the setup workspace; mutations stage through setup operations or the relevant owned surface. | Setup sections/operations tests and source registration. |

### Channel management

| Item | Path | Type | Status | Reason | Evidence |
|---|---|---|---|---|---|
| Channel manager main panel | `disbot/views/channels/main_panel.py` | Panel | **Done** | Canonical panel routes operators to create, move/reorder, delete, restrict, and visibility subviews. | Channel view source and hub composition. |
| Rename / move / reorder / delete service | `disbot/services/channel_lifecycle_service.py` | Lifecycle service | **Done** | Owns confirmed operator lifecycle operations, feasibility, audit companion, and lifecycle event emission. | `tests/unit/services/test_channel_lifecycle_service.py`; merged #523. |
| Delete panel | `disbot/views/channels/delete_panel.py` | Panel | **Done** | Requires explicit confirmation and routes deletion through `ChannelLifecycleService`. | Channel mutation invariant. |
| Move/reorder panel | `disbot/views/channels/move_panel.py` | Panel | **Done** | Selector-driven move/top/bottom operations route through the lifecycle service. | `tests/unit/views/test_channel_move_panel.py`; lifecycle tests. |
| Channel creation panel | `disbot/views/channels/create_panel.py` | Panel / provisioning consumer | **Done** | Uses the resource-provisioning lane rather than silently creating from a detector/read model. | Resource-provisioning contract and channel service tests. |
| Legacy/prefix channel creation | `ChannelCog.manage_event`; `create_channel_with_role`; `bulk_create_channels` | Management functions | **Partial** | These functions still call Discord channel/category creation directly, so channel creation does not have one canonical audited writer across all surfaces. | Source inspection; `docs/ownership.md` marks channel create/edit lifecycle mixed. |
| Channel permission overwrites | `ChannelCog.set_access`; `lock_channel`; `unlock_channel`; `modify_permissions`; `disbot/views/channels/restrict_panel.py` | Management functions / panels | **Done** | P0-4 (Q-0100): every overwrite routes through `ChannelLifecycleService.set_overwrite` (audit + `channel.lifecycle_changed` event + typed result); the invariant now pins `.set_permissions()`. `visibility_panel.py` was already audited via `governance_service`. | `test_no_direct_channel_mutations.py` (pins `.set_permissions`); `test_channel_lifecycle_service.py`; `test_restrict_panel_multi.py`. |
| Channel clone | `ChannelCog.clone_channel` | Management function | **Done** | P0-4 (Q-0100): clone routes through `ChannelLifecycleService.clone` (compensatable, audited); the invariant pins `.clone()`. | `test_no_direct_channel_mutations.py`; `test_channel_lifecycle_service.py`. |
| Category lifecycle / event category creation | `ChannelCog.manage_event`; channel create helpers | Management function | **Partial** | Category creation/lifecycle is not fully converged behind one audited service. | Source inspection; server-management folio current-state note. |
| Bulk delete and single delete commands | `ChannelCog.bulk_delete_channels`; `delete_channel`; `manage_event(delete)` | Management functions | **Done** | Route through `ChannelLifecycleService` and return typed outcome errors. | Channel invariant and service tests. |
| Channel list/info/pagination | `ChannelCog.list_channels`; `channel_info`; `_ChannelListPaginatorView` | Read-only management functions | **Done** | Read-only inventory and pagination are implemented. | `tests/unit/cogs/test_channel_list_paginate.py`. |

### Role management

| Item | Path | Type | Status | Reason | Evidence |
|---|---|---|---|---|---|
| Role hub and panels | `disbot/cogs/role_cog.py`; `disbot/views/roles/main_panel.py` | Hub / panel | **Done** | Composes create, manage, time, XP, reaction, diagnostics, and exemptions surfaces. | Role routing and panel compatibility tests. |
| Role create/edit/delete lifecycle | `disbot/services/role_lifecycle_service.py`; `disbot/views/roles/{creation_panel,management_panel}.py` | Lifecycle service / panels | **Done** | Role-object mutations route through the canonical audited lifecycle service. | Role lifecycle service test and no-direct-role-mutations invariant. |
| Time and XP role thresholds | `disbot/views/roles/{time_roles_panel,xp_roles_panel}.py`; `disbot/services/role_automation.py` | Automation management | **Done** | ID-first selectors and canonical threshold setters/clearers are used; no second write path is allowed. | Threshold selector/service/invariant tests; merged #652 for clear ownership. |
| Role automation worker/listeners | `RoleCog.role_check`; `on_member_join`; `disbot/services/role_automation.py` | Lifecycle automation | **Done** | Daily and join-time application paths exist with centralized automation logic. | `tests/unit/services/test_role_automation.py`; XP listener tests. |
| Reaction roles | `RoleCog` reaction listeners/commands; `disbot/views/roles/reaction_panel.py` | Role assignment feature | **Done** | Add/remove/list/setup paths and event listeners are present. | Role routing/source inspection. |
| Role exemptions | `disbot/views/roles/exemptions_panel.py`; `disbot/services/role_exemption_service.py` | Management panel / service | **Done** | Uses a dedicated service and tested panel behavior. | `tests/unit/views/test_role_exemptions_panel.py`. |
| Role diagnostics | `disbot/views/roles/diagnostics_panel.py`; `disbot/utils/role_feasibility.py` | Diagnostic panel | **Done** | Read-only feasibility diagnostics are implemented and tested. | `tests/unit/views/test_role_diagnostics_panel.py`; role feasibility tests. |
| Role-management UX follow-ups | Time/XP and edit-role panels | UX | **Partial** | Bulk “Clear missing” and selector-based Edit Role remain known follow-ups. | Server-management folio. |

### Moderation

| Item | Path | Type | Status | Reason | Evidence |
|---|---|---|---|---|---|
| Manual moderation service | `disbot/services/moderation_service.py` | Domain mutation service | **Done** | Owns warn, timeout, kick, ban, unban, clear-warnings, auto-delete recording, audit companion, and domain events. | `tests/unit/services/test_moderation_service.py`; no-direct-write invariant; merged #521. |
| Moderation command surface | `disbot/cogs/moderation_cog.py` | Management functions | **Done** | Prefix/slash actions route through the service and use capability/Discord-permission authority. | Moderation authority and service tests. |
| Moderation panel and modals | `disbot/views/moderation/main_panel.py`; `modals.py` | Panel / action UI | **Done** | Seven action/read modals are wired; mutating callbacks defer and dispatch through the service. | Moderation modal defer test and no-direct-write invariant. |
| Moderation configuration | `disbot/services/moderation_config.py`; moderation schemas/settings/setup section | Config/read model | **Done** | DM-on-action, purge/timeout/reason/escalation/post-action cleanup/public-log and moderator/trusted roles are config-backed. | Moderation config tests; server-management tracker PR10 completion. |
| Moderator/trusted role authority | Governance resolver + moderation cog/panel | Authority | **Done** | Configured roles grant governance tiers while preserving Discord permission holders via OR-gating. | `tests/unit/governance/test_role_tier_grants.py`; `test_moderation_role_authority.py`; ADR-008. |
| Moderation history and logging | `moderation_service._record_action`; `mod_logs`; server logging | Audit/history | **Done** | Authoritative append-only history plus best-effort audit/domain companions are implemented. | Moderation service tests and ownership contract. |
| Moderation quick-search/unban UX | Moderation panel/modals | UX | **Partial** | Member quick-search via `UserSelect` remains a known follow-up; unban is still ID-based. | Server-management folio. |

### Cleanup

| Item | Path | Type | Status | Reason | Evidence |
|---|---|---|---|---|---|
| Cleanup profiles | `disbot/services/cleanup_profiles.py` | Preset service | **Done** | Known immutable presets compile to policy mutations through the canonical governance pipeline. | `tests/unit/services/test_cleanup_profiles.py`; merged #549. |
| Hierarchical cleanup policy mutation | Cleanup cog/setup section + governance mutation pipeline | Mutation path | **Done** | Guild/category/channel policy changes route through the canonical pipeline; direct DB writes are blocked. | Cleanup stage/governance tests and ownership blocklist. |
| Cleanup panel diagnostics and dry-run | `disbot/cogs/cleanup/panel.py`; cleanup diagnostics | Panel / diagnostic | **Done** | Builder, dry-run, effective-policy display, and diagnostics shipped. | Cleanup panel/diagnostic tests; merged #549. |
| Cleanup history scan and words | `disbot/cogs/cleanup_cog.py` | Management functions | **Done** | History scan modal and add/remove/refresh word controls are implemented. | Cleanup history/panel tests. |
| Post-action moderation cleanup | `disbot/services/moderation_service.py`; `disbot/services/history_cleanup.py` | Cross-subsystem lifecycle request | **Done** | Optional post-kick/ban sweep is requested from the cleanup owner rather than duplicated in moderation. | Moderation service tests and PR10 tracker record. |
| Cleanup policy persistence/versioning | Cleanup DB/policy services | Persistence | **Done** | Policy version marker, dedupe/retention integration coverage, and guild-default no-op fix shipped. | Cleanup DB integration/migration tests; merged #549. |

## Required before production-ready

1. **Converge the remaining channel mutation paths.** **Clone + permission-overwrite are DONE** (P0-4 PR 1, Q-0100 — routed through `ChannelLifecycleService`). **Remaining: direct creation + category lifecycle** (`ChannelCog.manage_event` create, `create_channel_with_role`, `bulk_create_channels`, `views/channels/create_panel.py`) need to converge under `ResourceProvisioningPipeline` (preserve its confirmation rule), since ad-hoc operator creation has no declared binding — design that fit explicitly.
2. **Expand the channel mutation invariant after each convergence.** `.set_permissions()` and `.clone()` are now pinned (P0-4 PR 1). Still to pin: the creation/category calls, once their canonical provisioning path exists.
3. **Run a production-like live walk.** Exercise both prefix and slash entry points, hub navigation/back paths, setup stage → preview → apply → recovery, authority denials, Discord hierarchy failures, audit/log delivery, and cleanup scans on a real guild.
4. **Verify persistence and partial-failure behavior on real PostgreSQL.** In particular: setup draft/op-kind parity against the deployed schema, lock contention, partial apply/recovery, cleanup policy writes, moderation history, and event/audit companion failure behavior.
5. **Decide whether preflight adapters are required for every setup op before launch.** Today several known op kinds intentionally render `preflight unavailable`; this is safe but weakens operator confidence for compound changes.
6. **Close or explicitly accept the known UX gaps.** The highest-value ones are moderation member quick-search/unban selection, bulk clear-missing for thresholds, and selector-based Edit Role.

## Bugs, inconsistencies, and risks

- **Mixed channel ownership is the principal architectural risk.** Some channel paths are audited lifecycle operations while others call Discord directly. Similar operator actions therefore have different audit, confirmation, failure-reporting, and event behavior.
- **The channel invariant can give a false sense of completeness.** It guarantees only `.edit()` / `.delete()` convergence and documents that overwrites/clone are outside its scope.
- **Setup preflight coverage is incomplete.** Known operations without adapters are valid and apply correctly, but Final Review cannot always show a true current-versus-proposed diff.
- **Best-effort companions are not durable history.** Channel/role lifecycle audit companions and domain events may fail after Discord mutation succeeds; this is by contract, but operators need live evidence that logging failures are visible enough operationally.
- **Lifecycle services do not own every adjacent operation.** Role member assignment remains on automation/reaction-role paths by design; channel creation belongs to resource provisioning. Future work must preserve these boundaries rather than creating “one giant lifecycle service.”
- **Setup diagnostics intentionally cannot repair most findings.** This avoids unauthorized side channels and duplicate mutation paths, but operators may interpret “Diagnose & repair” as broader auto-repair than it is.
- **Docs describe structural completion, not production proof.** The tracker is accurate about shipped scope; it should not be read as evidence of a fresh boot/live walk.
- **The PR13 AI layer is gated, not a defect.** Do not implement or count it as an ungated readiness requirement while the AI-expansion gate remains in force.

## Setup/channel/role/moderation/cleanup readiness by area

| Area | Readiness | Summary |
|---|---|---|
| **Setup** | **Partial** | Strong draft/apply/recovery architecture, canonical diagnostics, deterministic templates, and broad unit coverage. Needs live/Postgres/failure-path verification and a decision on incomplete preflight adapters. |
| **Channels** | **Partial** | Rename/move/reorder/delete and their panels are converged. Direct creation, clone, overwrites, and category paths prevent full production readiness. |
| **Roles** | **Partial** | Core lifecycle and automation ownership are strong and invariant-pinned. Remaining gaps are primarily live verification and known UX follow-ups. |
| **Moderation** | **Partial** | Service convergence, config, authority, history, and logging contracts are strong. Remaining gaps are live verification and member/unban UX. |
| **Cleanup** | **Partial** | Policy hierarchy, presets, diagnostics, dry-run, versioning, and moderation integration are implemented. Production persistence/large-history/live behavior still needs verification. |
| **Hub composition** | **Partial** | Canonical first-class composition and read-only staff subpanels are Done. Overall status inherits the incomplete channel lane and live-verification gap. |

## Gated or blocked work

- **PR13 AI-generated role templates:** blocked by the AI-expansion gate in `docs/current-state.md`; deterministic templates are already shipped.
- **Setup governance section:** deferred by owner decision Q-0008; not approved production scope.
- **Per-severity `logging_routes`:** reserved future model, explicitly outside v1.
- **Broader channel lifecycle convergence:** not externally blocked, but must preserve the ownership split between resource provisioning (creation) and lifecycle change operations; it needs an explicit contained design before implementation.

## Simplification opportunities

- Route legacy/prefix channel mutation commands through the same panel/domain adapters used by the canonical channel manager, reducing duplicate Discord mutation/error-copy paths.
- Extract a shared channel-overwrite mutation seam rather than keeping separate lock/unlock/set/restrict/visibility implementations.
- Reuse one canonical role hub implementation: `RoleHubPanelView` in the cog and `RoleHubView` under `views/roles/` should be reviewed for overlap before either evolves further.
- Generate/setup-register section metadata from one declaration source where practical; the large setup view tree currently makes reachability auditing laborious.
- Add a small machine-readable readiness/inventory check for scoped managers and setup sections so future maps can detect newly added but unclassified surfaces.
- Keep diagnostics read-only and stage repairs as operations; do not simplify by letting diagnostics call mutation services directly.

## Tests and live-verification gaps

### Existing evidence

- Targeted unit tests cover the hub, channel/role lifecycle services, moderation service/authority, cleanup profiles/diagnostics/panels, setup operations/diagnostics/sections/templates, and setup views.
- AST invariants enforce the most important current ownership rules: no direct moderation writes, no direct role-object mutations, no direct role-threshold writes, setup advisor/diagnostics/preflight read-only behavior, and channel `.edit()` / `.delete()` convergence.
- DB parity coverage pins the setup operation dispatcher, Python DB gate, and migration `059` constraint.

### Remaining gaps

- No fresh real-guild end-to-end walk was performed for this audit.
- No fresh real-PostgreSQL apply/recovery/lock-contention run was performed for this audit.
- No automated invariant yet forbids direct channel create/clone/overwrite/category mutations because those paths have not converged.
- Lifecycle companion-event/audit delivery failure behavior is mostly unit-tested rather than production-observed.
- Discord-specific hierarchy, stale selector, missing permission, interaction timeout, and back-navigation behavior needs a deliberate live matrix across all five managers.
- Large-guild behavior needs explicit live checks: channel list pagination, role selectors, cleanup history scans, setup scan latency, and hub badge refresh.

## Recommended next session

**Run a channel-ownership convergence planning/review session, not an implementation-by-default session.** Produce a source-grounded decision for each remaining direct channel mutation (`create_*`, category creation, clone, and permission overwrites): canonical owner, confirmation requirement, audit/event contract, and migration/invariant implications. Cross-check the resource-provisioning contract before assigning creation ownership. End with a bounded implementation sequence and a live-verification matrix for the entire Server Management Hub. Do not add a setup op-kind, create a role-threshold writer, or permit direct cog/view DB writes as part of that work.
