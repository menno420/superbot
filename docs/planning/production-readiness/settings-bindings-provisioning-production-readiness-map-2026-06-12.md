# Settings / Bindings / Provisioning production-readiness map — 2026-06-12

> **Status:** `audit` — source-verified production-readiness review; docs-only; no fixes implemented.
> **Scope:** settings, bindings, resource provisioning, Settings UI, Setup relations, and directly required governance/authority seams.
> **Verdict:** **Partial**. The three canonical lanes and their audited service boundaries exist and are well tested, but production readiness is blocked by pointer-lane duplication, incomplete binding/provisioning UI coverage, delegated-setup authority mismatch, and insufficient live verification.

## Current verified state

Source code and merged PRs win over roadmap language in this review. The review inspected the required reading route, the live source routes named in the request, related setup/catalogue/backfill code, and relevant unit/invariant tests.

As of **2026-06-12**, the GitHub API reports one live open PR, [#704](https://github.com/menno420/superbot/pull/704), containing live-test screenshots only. It does not modify Settings / Bindings / Provisioning source. Recent merged PRs that materially affect this map are [#640](https://github.com/menno420/superbot/pull/640) (actionable Settings groups and pagination), [#650](https://github.com/menno420/superbot/pull/650) (binding/runtime truth clarification), [#654](https://github.com/menno420/superbot/pull/654) (Phase-2 declarations and BTD6 binding), [#672](https://github.com/menno420/superbot/pull/672) (proof-channel binding/resource declaration), and [#682](https://github.com/menno420/superbot/pull/682) (domain-panel destination rendering). No open PR changes the claims below.

### Verified headline inventory

| Inventory | Verified count/state | Readiness |
|---|---:|---|
| Registered `SettingSpec` declarations | **36** across 9 settings-bearing schemas | **Partial** — all are editable through the generic scalar pipeline and runtime-consumed or intentionally transitional; five are legacy Discord resource pointers in the wrong lane. |
| Registered `BindingSpec` declarations | **13**, all channel bindings | **Partial** — canonical read/write primitives exist, but generic Settings pages render bindings read-only and several consumers retain legacy fallbacks/dual lanes. |
| Registered provisionable resource requirements | **11**, all channels | **Partial** — preview/confirmation/audit pipeline exists; generic provisioning UI is not reachable from every Settings subsystem page. |
| Registered domain-panel destinations | **2** (`cleanup`, `help`) | **Partial** — discoverable and rendered, but opening/routing remains destination-specific. |
| Settings UI files | 16 files under `disbot/views/settings/` | **Partial** — scalar edit/reset and diagnostics are strong; generic binding/resource actions remain intentionally absent. |
| Setup UI files | 38 files under `disbot/views/setup/` | **Partial** — draft/final-review composition is broad, but authority semantics and some duplicate/legacy entry points remain unresolved. |
| Canonical mutation owners | settings, binding, provisioning pipelines present | **Done** for declared-lane primitives; **Partial** end-to-end because legacy/domain writers remain. |
| Open PR collision check | #704 only; screenshots, no source overlap | **Done** for this review snapshot. |

## Scope inventory table

### Registries, catalogues, resolution, mutation, and storage seams

| Item | Path | Type | Status | Reason | Evidence |
|---|---|---|---|---|---|
| Subsystem schema registry | `disbot/core/runtime/subsystem_schema.py` | registry | **Done** | Declares typed settings, bindings, resource requirements, and domain-panel destinations; registered schemas are the common discovery source. | `SubsystemSchema`, `register`, `all_schemas`; declaration invariants. |
| Settings registry | `disbot/core/runtime/settings_registry.py` | registry/read model | **Done** | Frozen registry finds duplicate/missing keys and capabilities and exposes diagnostic snapshot. | `build_registry()`, `RegistryFindings`, settings-registry tests. |
| Customization catalogue | `disbot/services/customization_catalogue.py` | registry/read model | **Done** | `actionable_settings_groups()` is the single inclusion rule and paginated hub consumer; source-backed after #640/#654. | `ActionableGroup`, `actionable_settings_groups()`, hub tests. |
| Provisioning catalogue | `disbot/services/resource_provisioning_catalogue.py` | registry/read model | **Done** | Builds typed options only from resource requirements that name a declared binding and reports findings. | `build_provisioning_catalogue()`, catalogue tests. |
| Capability usage registry | `disbot/core/runtime/subsystem_capabilities.py` | governance registry | **Partial** | Capability decorators and diagnostics exist, but declared capabilities still resolve through one administrator floor rather than per-capability policy. | `capability()`, `declared_capabilities()`, `governance/capability.py`. |
| Settings resolution | `disbot/services/settings_resolution.py` | read path | **Done** | Typed declared-setting resolution, arbitration, diagnostics, batch reads, and value helper exist. | `resolve_setting()`, `resolve_batch()`, `resolve_value()`, resolution tests. |
| Settings mutation | `disbot/services/settings_mutation.py` | canonical write path | **Done** for declared scalars | Re-resolves spec, re-checks capability, honors kill switch, validates/coerces, atomically writes KV + audit, invalidates cache, and emits events. | `SettingsMutationPipeline.set_value()`, mutation tests and audit-alignment invariant. |
| Settings DB + audit | `disbot/utils/db/settings.py`; `disbot/utils/db/settings_audit.py` | storage owner | **Partial** | Canonical audited writer exists for declared settings, but allowlisted domain/runtime writers still call the raw KV primitive. | `set_value_with_audit()`; `test_no_direct_settings_keys_writes.py` allowlist. |
| Binding read/validation | `disbot/core/runtime/bindings.py` | canonical read path | **Done** | Typed `BindingValue`, target validation, live status resolution, and diagnostics exist; reads intentionally hit DB each time. | `get_binding()`, `validate_binding_target()`, binding tests; #650. |
| Binding mutation | `disbot/services/binding_mutation.py` | canonical write path | **Done** | Re-resolves declaration, validates capability and target kind/status, writes with audit, and emits event. | `set_binding()`, `clear_binding()`, binding pipeline tests. |
| Binding DB + audit | `disbot/utils/db/bindings.py` | storage owner | **Done** | Upsert/clear and audit are transactionally paired; cogs/views are fenced from direct primary-branch writes. | `upsert_with_audit()`, `clear_with_audit()`, direct-write invariant. |
| Legacy-pointer binding backfill | `disbot/services/binding_backfill.py` | migration/governance seam | **Partial** | Dry-run, classification, lock, and apply exist, but registry covers only XP announce channel, economy log channel, and trusted role; some are still concurrently declared as scalar settings, and `governance.trusted_role` has no current binding declaration. | `MIGRATED_KEYS`, `dry_run()`, `apply_backfill()`. |
| Resource provisioning | `disbot/services/resource_provisioning.py` | canonical create/reuse path | **Done** at service boundary | Create requires confirmation; calls binding pipeline; writes provisioning audit for success/failure; capability and kill-switch checks happen at execution. | `preview()`, `provision()`, pipeline and audit-alignment tests. |
| Resource primitive package | `disbot/core/resources/` | Discord resource helpers/read model | **Partial** | Discovery/status/types plus channel/role ensure helpers exist; package truth was clarified in #650, but lifecycle/provisioning concepts remain easy to confuse and category coverage lives through service composition rather than a symmetric module. | `channel_service.py`, `role_service.py`, `discovery.py`, `status.py`, `types.py`. |
| Provisioning audit store | `disbot/utils/db/resource_provisioning_audit.py` | storage owner | **Done** | Append-only outcome audit and operator read methods exist. | `insert_audit()`, count/list methods, audit-alignment invariant. |
| Setup draft store | `disbot/services/setup_draft.py`; `disbot/utils/db/setup_draft.py` | compound-change staging | **Done** | Setup operations stage before apply; replacement/delete/clear/list APIs exist. | `append()`, `replace_recommended_for_section()`, draft tests. |
| Setup dispatcher | `disbot/services/setup_operations.py` | canonical compound apply adapter | **Partial** | Correctly routes settings, bindings, and resource creates through their pipelines and isolates failures, but it does not independently enforce the setup owner/delegate authority policy; it relies on view gating plus per-lane pipeline checks. | `_apply_set_setting()`, `_apply_binding()`, `_apply_resource_create()`, `apply_operations()`. |
| Governance service façade | `disbot/services/governance_service.py` | governance seam | **Partial** | Provides stable governance read/write façade, but is not the authority resolver used by the three mutation pipelines and retains broad legacy exports. | Re-exports from `governance`; no local mutation classes/functions. |
| Capability resolver | `disbot/governance/capability.py` | execution authority | **Partial** | Target-guild membership, administrator-floor, revoke-only overlay, and system/backfill bypass are implemented. Per-capability tiers and delegated-setup semantics are not. | `actor_holds_capability()`, governance tests, `docs/capability-authority.md`. |
| Kill switches | `disbot/core/runtime/feature_flags.py`; settings/provisioning pipelines | operator safety | **Partial** | Settings and provisioning have explicit fail-open operator-disable checks; binding mutation has capability enforcement but no sibling mutation kill switch. | `SETTINGS_MUTATION_PRIMARY`, `RESOURCE_PROVISIONING_PRIMARY`; pipeline tests. |
| Direct-write fences | `tests/unit/invariants/test_no_direct_settings_keys_writes.py`; `test_no_direct_bindings_primary_branch.py` | architecture guard | **Partial** | New cogs/views cannot casually bypass canonical writers, but raw settings writes remain allowlisted for governance and typed runtime-state services; the setting invariant is not an absolute no-direct-write guarantee. | Allowlist and AST scan comments. |

### Declared settings and setting-key paths

Every registered scalar below is editable through `SettingsMutationPipeline`; status measures end-to-end production usefulness and lane correctness, not whether the declaration parses.

| Item | Path | Type | Status | Reason / runtime evidence |
|---|---|---|---|---|
| `ai.ai_enabled` → `ai_enabled` | `disbot/cogs/ai/schemas.py`; `disbot/utils/settings_keys/ai.py` | setting | **Partial** | Projected into typed AI policy and consumed, but projection is best-effort after the KV commit. |
| `ai.ai_natural_language_enabled` → `ai_natural_language_enabled` | same | setting | **Partial** | Projectable typed-policy scalar; dual-store projection can diverge. |
| `ai.ai_default_provider` → `ai_default_provider` | same | setting | **Partial** | Projectable typed-policy scalar; configuration/default-provider reads also exist outside the generic resolver. |
| `ai.ai_default_model` → `ai_default_model` | same | setting | **Partial** | Declared/projectable but no direct runtime consumer was found outside schema/tests; typed projection is the intended consumer seam. |
| `ai.ai_minimum_level_default` → `ai_minimum_level_default` | same | setting | **Partial** | Projectable typed-policy scalar; dual-store risk. |
| `ai.ai_cooldown_seconds` → `ai_cooldown_seconds` | same | setting | **Partial** | Projectable typed-policy scalar; dual-store risk. |
| `ai.ai_fresh_user_mention_allowance` → `ai_fresh_user_mention_allowance` | same | setting | **Partial** | Projectable typed-policy scalar; dual-store risk. |
| `ai.ai_guild_instruction_profile` → `ai_guild_instruction_profile` | same | setting | **Partial** | Transitional/backcompat scalar; typed instruction-profile tables are the intended authority and this scalar is not projected. |
| `ai.ai_memory_window_minutes` → `ai_memory_window_minutes` | same | setting | **Done** | Scalar-owned and consumed by `disbot/services/ai_memory_service.py`. |
| `ai.ai_memory_channel_scan_enabled` → `ai_memory_channel_scan_enabled` | same | setting | **Done** | Scalar-owned and consumed by `disbot/services/ai_memory_service.py`. |
| `blackjack.default_entry_fee` → `blackjack_default_entry_fee` | `disbot/cogs/blackjack/schemas.py`; `disbot/utils/settings_keys/games.py` | setting | **Done** | Runtime consumed through `resolve_value()` in `disbot/cogs/blackjack_cog.py`. |
| `deathmatch.turn_timeout` → `deathmatch_turn_timeout` | `disbot/cogs/deathmatch/schemas.py`; `disbot/utils/settings_keys/games.py` | setting | **Done** | Runtime consumed through `resolve_value()` in `disbot/cogs/deathmatch_cog.py`. |
| `economy.economy_log_channel` → `economy_log_channel` | `disbot/cogs/economy/schemas.py`; `disbot/utils/settings_keys/economy.py` | legacy pointer setting | **Not Done** | Discord channel pointer is in the wrong lane; `economy.log_channel` binding exists and backfill knows this key, but the scalar remains declared/editable and the cog still resolves the settings pointer. |
| `logging.enabled` → `logging_enabled` | `disbot/cogs/logging/schemas.py`; `disbot/utils/settings_keys/logging.py` | setting | **Done** | Runtime consumed by `services/server_logging.py`. |
| `logging.auto_create_channels` → `logging_auto_create_channels` | same | setting | **Partial** | Runtime consumed, but “auto create” intent must remain subordinate to explicit provisioning confirmation/no-silent-create rules. |
| `moderation.warn_threshold` → `warn_threshold` | `disbot/cogs/moderation/schemas.py`; `disbot/utils/settings_keys/moderation.py` | setting | **Done** | Runtime consumed through the central `disbot/services/moderation_config.py` resolver. |
| `moderation.warn_timeout_minutes` → `warn_timeout_minutes` | same | setting | **Done** | Runtime consumed through `moderation_config.py`. |
| `moderation.warn_escalation_action` → `moderation_warn_escalation_action` | same | setting | **Done** | Runtime consumed through `moderation_config.py`. |
| `moderation.dm_on_action` → `moderation_dm_on_action` | same | setting | **Done** | Runtime consumed through `moderation_config.py`. |
| `moderation.dm_template` → `moderation_dm_template` | same | setting | **Done** | Runtime consumed through `moderation_config.py`. |
| `moderation.require_reason` → `moderation_require_reason` | same | setting | **Done** | Runtime consumed through `moderation_config.py`. |
| `moderation.ban_delete_message_days` → `moderation_ban_delete_message_days` | same | setting | **Done** | Runtime consumed through `moderation_config.py`. |
| `moderation.max_timeout_minutes` → `moderation_max_timeout_minutes` | same | setting | **Done** | Runtime consumed through `moderation_config.py`. |
| `moderation.post_action_cleanup` → `moderation_post_action_cleanup` | same | setting | **Done** | Runtime consumed through `moderation_config.py`. |
| `moderation.post_action_cleanup_limit` → `moderation_post_action_cleanup_limit` | same | setting | **Done** | Runtime consumed through `moderation_config.py`. |
| `moderation.public_log_actions` → `moderation_public_log_actions` | same | setting | **Done** | Runtime consumed through `moderation_config.py`. |
| `moderation.public_log_channel` → `moderation_public_log_channel` | same | legacy pointer setting | **Not Done** | Discord channel pointer is a binding by rule; no corresponding moderation binding is declared. |
| `moderation.moderator_role` → `moderator_tier_role_id` | `disbot/cogs/moderation/schemas.py`; `disbot/utils/settings_keys/governance.py` | legacy pointer setting | **Partial** | Runtime-consumed governance role pointer, but Discord role pointers belong in bindings; Setup reads the scalar directly. |
| `moderation.trusted_role` → `trusted_tier_role_id` | same | legacy pointer setting | **Partial** | Runtime-consumed and present in backfill registry as `governance.trusted_role`, but no matching binding declaration is registered. |
| `role.time_roles_stack` → `time_roles_stack` | `disbot/cogs/role/schemas.py`; `disbot/utils/settings_keys/role.py` | setting | **Done** | Runtime consumed by `disbot/services/role_exemption_service.py`. |
| `role.xp_roles_stack` → `xp_roles_stack` | same | setting | **Done** | Runtime consumed by `role_exemption_service.py`. |
| `rps_tournament.default_entry_fee` → `rps_default_entry_fee` | `disbot/cogs/rps_tournament/schemas.py`; `disbot/utils/settings_keys/games.py` | setting | **Done** | Runtime resolver exists in the schema module. |
| `xp.xp_min` → `xp_min` | `disbot/cogs/xp/schemas.py`; `disbot/utils/settings_keys/xp.py` | setting | **Done** | Runtime consumed through typed guild-config accessors. |
| `xp.xp_max` → `xp_max` | same | setting | **Done** | Runtime consumed through typed guild-config accessors. |
| `xp.xp_cooldown` → `xp_cooldown` | same | setting | **Done** | Runtime consumed through typed guild-config accessors. |
| `xp.xp_announce_channel` → `xp_announce_channel` | same | legacy pointer setting | **Not Done** | Discord channel pointer is in the wrong lane; `xp.announce_channel` binding and backfill mapping exist, but the scalar remains editable and the XP config panel still references it. |

#### Reserved/non-Settings keys that must not be mistaken for editable settings

| Item | Path | Type | Status | Reason |
|---|---|---|---|---|
| `BTD6_STRATEGY_SUBMISSION_CHANNEL` | `disbot/utils/settings_keys/btd6.py` | reserved key | **Not Done** | Reserved and intentionally unwired; the actual schema now declares `btd6.strategy_submission_channel` binding. |
| BTD6 cache cadence keys (3) | `disbot/utils/settings_keys/btd6_cache.py` | reserved keys | **Not Done** | Reserved only; no `SettingSpec` or runtime consumer. |
| `SKIP_ROLES` | `disbot/utils/settings_keys/role.py` | orphan key | **Not Done** | No production or unit-test consumer found outside key declaration/export. |
| `ACTIVE_TOURNAMENT`, `BTD6_CT_GROUP_ID`, `GOVERNANCE_VERSION` | games/BTD6/governance key modules | domain/runtime state | **Done** as non-Settings classification | Correctly owned by typed domain/runtime services rather than generic Settings mutation. |
| `BTD6_VERSION_ANNOUNCEMENT_CHANNEL` | `disbot/utils/settings_keys/btd6.py`; `disbot/services/btd6_version_announce.py` | legacy pointer/runtime seam | **Partial** | Binding-first read exists for `btd6.version_announce_channel`, but legacy KV write/read fallback remains. |
| `LOGGING_MOD_CHANNEL`, `LOGGING_CLEANUP_CHANNEL` | `disbot/utils/settings_keys/logging.py`; `disbot/services/server_logging.py` | legacy pointer fallback | **Partial** | Seven logging bindings are canonical, but two legacy scalar fallback keys remain until convergence. |

### Binding and resource-provisioning paths

| Item | Path | Type | Status | Reason / evidence |
|---|---|---|---|---|
| `ai.audit_log_channel` | `disbot/cogs/ai/schemas.py` | channel binding | **Partial** | Declared single source of truth, but generic Settings page is read-only for bindings and no dedicated mutation surface was verified. |
| `btd6.strategy_submission_channel` | `disbot/cogs/btd6/schemas.py` | channel binding | **Partial** | Correct lane; strategy intake feature remains future/unwired. |
| `btd6.version_announce_channel` | same; `disbot/services/btd6_version_announce.py` | channel binding | **Partial** | Binding-first runtime read shipped, but legacy KV fallback/write lane remains. |
| `economy.log_channel` + provision `economy.log_channel` | `disbot/cogs/economy/schemas.py` | binding + recommended channel resource | **Partial** | Correct typed lane exists, but legacy scalar remains declared/consumed. |
| `logging.{mod,cleanup,debug,info,warning,error,audit}_channel` + seven provision options | `disbot/cogs/logging/schemas.py`; `disbot/cogs/logging/` | 7 bindings + 7 recommended resources | **Partial** | Best operator-complete slice: dedicated set/create/status/routes UI, binding-first runtime routes, preview/confirmation/audit. Legacy mod/cleanup scalar fallbacks and unproven event publishers keep it Partial. |
| `proof_channel.proof_channel` + provision `proof_channel.proof` | `disbot/cogs/proof_channel/schemas.py`; `disbot/cogs/proof_channel_cog.py` | binding + optional channel resource | **Partial** | Binding-first with name fallback and real-Postgres smoke recorded in #672; generic mutation/provisioning reachability remains limited. |
| `xp.announce_channel` + provision `xp.announce_channel` | `disbot/cogs/xp/schemas.py` | binding + optional channel resource | **Partial** | Correct typed lane exists; legacy scalar and XP config path remain. |
| `moderation.mod_log` | `disbot/cogs/moderation/schemas.py` | recommended resource without binding | **Not Done** | Provisioning catalogue requires a binding name to form an actionable option; this requirement is not a complete provision-and-bind path. |
| `governance.trusted_role` backfill target | `disbot/services/binding_backfill.py` | role binding target | **Not Done** | Backfill registry references it, but no registered `BindingSpec` exists, so classification blocks on missing schema. |
| Role/category generic provisioning | `disbot/core/resources/role_service.py`; provisioning service supports kinds | resource capability | **Partial** | Pipeline supports declared resource kinds, but current catalogue contains channel requirements only; no registered role/category option exercises the generic path. |

### Settings panels/views, setup relation, and operator-facing functions

| Item | Path | Type | Status | Reason / evidence |
|---|---|---|---|---|
| `!settings`, `/settings`, `!settings access`, Help-menu hook | `disbot/cogs/settings_cog.py` | operator front doors | **Done** | Admin-gated hub/slash, actionable-group discovery, feature-flag disabled state, read-only access explorer, and Help hook exist. |
| Settings hub | `disbot/views/settings/hub.py` | navigation view | **Done** | Actionable-only discovery and >25 pagination shipped; links diagnostics and command access. |
| Subsystem page | `disbot/views/settings/subsystem_view.py` | settings/detail view | **Partial** | Edits/resets scalar settings and renders bindings/resources/domain panels; binding/resource rows remain read-only, so “actionable” does not always mean actionable from the page. |
| Scalar editors | `edit_boolean.py`, `edit_enum.py`, `edit_number.py`, `edit_number_presets.py`, `edit_text.py`, `edit_channel.py`, `edit_role.py`, `reset_button.py` | mutation views | **Done** for declared settings | All writes route through `SettingsMutationPipeline`, which re-checks capability at execution. Channel/role editors are nevertheless legacy pointer-setting editors, not binding editors. |
| Command access editor | `disbot/views/settings/edit_command_access.py` | separate-domain mutation view | **Done** | Uses its own canonical service and explicitly rejects non-admin callbacks. Correctly not forced through settings pipeline. |
| Settings diagnostics | `invalid_settings.py`, `missing_bindings.py`, `needs_setup.py`, `audit_view.py` | read-only views | **Partial** | Useful cross-cutting read models exist; “needs setup” and missing-resource/policy coverage are not complete enough to be a production checklist. |
| Domain-panel destinations | `cleanup` and `help` schemas + subsystem page | navigation relation | **Partial** | Destinations are declared/rendered after #654/#682, but routing/opening remains domain-specific and is not a universal Settings action. |
| `/setup`, `!setup`, `/setup-hub`, `/setup-depth`, `/setup-skip`, `/setup-unskip`, `/setup-reset`, `/setup-delegate`, `/setup-undelegate`, `/setup-status` | `disbot/cogs/setup_cog.py` | operator front doors | **Partial** | Broad setup controls exist, but prefix `!setup` and slash/hub compatibility surfaces have differing entry semantics; delegated authority does not align with pipeline authority at apply. |
| Setup wizard/launcher/hub | `disbot/views/setup/{launcher,wizard,hub}.py` | setup navigation/views | **Partial** | Owner/delegate write gates and section routing exist; legacy hub remains and increases surface area. |
| Setup sections | `disbot/views/setup/sections/` | draft producers | **Partial** | Correctly stage compound config rather than directly writing settings/bindings/resources; section-specific metadata and authority patterns are uneven. |
| Final Review | `disbot/views/setup/final_review.py` | preview/confirm/apply view | **Partial** | Re-checks owner/delegated authority, orders operations, preserves failed drafts, and routes through services. Delegated users can pass Final Review gate but still fail administrator-floor settings/binding/provisioning pipeline checks. |
| Provisioning preview/confirm panels | `disbot/views/setup/provisioning/` | resource provisioning UI | **Done** | Preview is side-effect free; Apply runs `provision(..., confirmed=True)` and pipeline re-checks capability/audits. |
| Logging operator suite | `disbot/cogs/logging_cog.py`; `disbot/cogs/logging/` | binding/provisioning UI | **Partial** | `!logging status/set/create/routes/test` is the most complete dedicated operator flow; retains duplicated route-specific UI and legacy fallback lane. |
| Setup summary/recovery | `disbot/views/setup/{summary,recovery}.py` | operator recovery | **Partial** | Partial-apply recovery exists, but “finish anyway” can intentionally drop failed operations and should be live-tested with audit/recovery expectations. |

## Required before production-ready

1. **Finish pointer-lane convergence.** Replace or retire editable scalar Discord pointers (`economy_log_channel`, `xp_announce_channel`, moderation public-log/role pointers, BTD6/logging fallbacks as applicable) only after binding-first reads, migration/backfill, operator reconciliation, and rollback are proven. A Discord resource pointer must have one canonical binding owner.
2. **Resolve the broken backfill declaration.** Either declare the intended `governance.trusted_role` binding and its capability/schema owner or remove/reframe the mapping. A permanently `BLOCKED_NO_SCHEMA` registry entry is not production-ready migration machinery.
3. **Keep declaration-to-runtime-consumer parity machine-checkable.** This review verified consumers for the current declared settings, but no invariant prevents a future editable declaration from becoming a no-op. Add a generated disposition/consumer check rather than relying on manual source search.
4. **Align Setup delegation with mutation authority.** Decide whether delegated setup admins are supposed to apply settings/bindings/provisioning. If yes, capability policy needs a non-escalating delegated setup route; if no, Setup copy/gates must stop promising apply authority. Preserve execution-time re-checks in either design.
5. **Make binding/resource actions consistently reachable.** Either add capability-native binding/provisioning actions from generic subsystem pages or clearly route every binding/resource row to its canonical dedicated/setup flow. Read-only rows inside an “actionable” group are insufficient operator UX.
6. **Close provisioning catalogue gaps.** Every declared resource requirement must resolve to a valid binding-backed option, or be explicitly classified as lifecycle-only/non-provisionable. `moderation.mod_log` currently has no complete provision-and-bind target.
7. **Decide the binding kill-switch posture.** Settings and provisioning writes have operator kill switches; binding mutation does not. Either add an equivalent governed control or document/test why bindings intentionally remain available when adjacent mutation lanes are disabled.
8. **Complete a real-guild production smoke.** Exercise generic Settings edits/resets, binding set/clear, create and use-existing provisioning, Setup Final Review, partial recovery, kill switches, revoked capabilities, deleted targets, and audit inspection.

## Bugs, inconsistencies, and risks

| Finding | Severity | Status | Why it matters |
|---|---|---|---|
| Legacy Discord pointers remain registered as scalar settings while equivalent bindings exist. | High | **Not Done** | Violates lane rule, creates two operator-visible truths, and permits generic scalar editors to bypass binding target validation/status semantics. |
| `binding_backfill.MIGRATED_KEYS` references undeclared `governance.trusted_role`. | High | **Not Done** | Backfill cannot apply that mapping because `_schema_declares()` will reject it. |
| Delegated Setup apply gate and mutation-pipeline administrator floor disagree. | High | **Not Done** | A delegated operator can stage and pass Final Review authority but fail canonical settings/binding/provisioning writes per operation. |
| Declaration-to-runtime-consumer parity is manually verified, not invariant-backed. | Medium | **Partial** | Current consumers exist, but a future editable no-op setting could ship without a generated parity check. |
| `moderation.mod_log` resource has no binding name. | Medium | **Not Done** | It cannot become a normal provisioning catalogue option that creates/reuses then binds. |
| Generic Settings subsystem pages show bindings/resources but do not mutate them. | Medium | **Partial** | Discovery is better than before #640, but operators still need undocumented destination knowledge for many rows. |
| AI scalar → typed-policy projection happens after successful KV commit and is best-effort. | Medium | **Partial** | Audit says the setting changed even if live typed policy did not; diagnostics/repair must remain prominent until convergence. |
| Binding reads are intentionally uncached while settings reads cache. | Low | **Done / watch** | Correctly documented after #650, but load/latency should be observed in production rather than “fixed” based on stale docs. |
| Roadmap milestone status is stale. | Medium | **Partial** | `settings-customization-roadmap.md` still labels several already-shipped flows planned/in-progress; source and this map must win during execution planning. |
| Core resource provisioning vs lifecycle services are adjacent concepts. | Medium | **Partial** | New callers can accidentally choose create/edit lifecycle APIs rather than the preview/confirmation/audit provisioning lane. |

## Settings vs bindings vs provisioning lane correctness

| Lane | Correct current uses | Incorrect/partial current uses | Verdict |
|---|---|---|---|
| **Settings** | Scalar booleans/enums/numbers/text; typed coercion/validation; direct focused edits through audited settings pipeline. | Legacy channel/role IDs still appear as settings; AI uses transitional/dual-store projection. | **Partial** |
| **Bindings** | Declared Discord resource pointers, target validation/status, audited set/clear, binding-first reads for logging/BTD6/proof and other consumers. | Generic Settings UI is read-only; legacy fallback/scalar lanes remain; trusted-role backfill target lacks schema. | **Partial** |
| **Provisioning** | Declared create/reuse option, side-effect-free preview, explicit create confirmation, capability/kill-switch check, binding pipeline composition, outcome audit. | Not all resource declarations form catalogue options; not all Settings groups expose the action; no registered role/category options prove those generic kinds. | **Partial** |
| **Setup draft/final review** | Compound and generated changes stage, preview, re-check at apply, dispatch through canonical lane services, and preserve partial failures. | Delegated setup authority conflicts with per-lane capability floor; multiple setup entry/navigation surfaces remain. | **Partial** |

## Authority/capability callback re-check gaps

- **Done:** every scalar editor/reset ultimately calls `SettingsMutationPipeline.set_value()`, which re-checks the declared capability at callback execution time.
- **Done:** binding selectors that use `BindingMutationPipeline` and provisioning confirmations that use `ResourceProvisioningPipeline` re-check capability at the mutation seam. Logging’s dedicated views also have explicit `interaction_check` guards.
- **Done:** command-access callbacks explicitly re-check administrator authority before domain-service writes.
- **Done:** Setup Final Review and recovery apply actions call `_gate_apply()` again before dispatch.
- **Partial:** many Setup section callbacks mutate the **draft store** after owner/delegate view gates rather than capability-specific checks. This is acceptable only if draft mutation is explicitly governed by Setup authority and apply remains the sole effectful gate; that contract should be pinned consistently for every section.
- **Not Done:** delegated Setup authority is not represented in `actor_holds_capability()`. Final Review’s owner/delegate re-check therefore does not guarantee that the called canonical pipelines will authorize the same actor.
- **Gap:** there is no single invariant that enumerates every mutating panel callback and proves it either performs an explicit authority check or reaches a mutation service that does. Existing tests cover selected panels/services, not total callback coverage.

## Simplification opportunities

1. Retire legacy pointer-setting editors as bindings converge; this removes `input_hint="channel"` / `input_hint="role"` as a misleading generic substitute for binding management.
2. Generate the declaration inventory and no-runtime-consumer report from schemas + key usage in CI, rather than maintaining manual counts in multiple docs.
3. Give every actionable binding/resource row one destination descriptor so the generic subsystem page can render “Set”, “Create/reuse”, or “Open canonical panel” without bespoke subsystem logic.
4. Consolidate Setup front doors after the linear wizard is proven; keep one primary operator path and mark compatibility paths with removal criteria.
5. Make the authority contract compositional: Setup gate decides who may apply a draft, while each operation carries a capability decision compatible with that Setup role. Avoid parallel “delegate” and “administrator floor” models that disagree at runtime.
6. Classify resource requirements explicitly as `provision_and_bind` versus lifecycle-only; do not infer completeness from a nullable `binding_name`.
7. Replace stale milestone/status prose in historical roadmaps with links to the living folio/current source map rather than repeatedly reconciling old status tables.

## Tests and live-verification gaps

### Strong automated coverage already present

- Settings registry, resolution, mutation authorization/validation/kill switch/audit, edit/reset round trips, hub pagination/discovery, diagnostics, and no-new-direct-write guards.
- Binding value/target validation, mutation authorization/audit, DB behavior, constraints, and no-direct-primary-branch guard.
- Provisioning catalogue import discipline, pipeline authority/confirmation/kill switch/outcomes/audit, and preview/confirm panel behavior.
- Setup operation dispatch, draft/final-review ordering, recovery, wizard gates, and section-specific behavior.
- Capability target-guild/admin-floor/revoke semantics.

### Missing or insufficient verification

- No single generated test proves **every registered setting has a production runtime reader**; current parity was verified manually in this review.
- No single generated test proves **every legacy Discord pointer has exactly one canonical binding migration target and no editable scalar declaration**.
- No test pins `MIGRATED_KEYS` targets to registered `BindingSpec`s; the undeclared trusted-role target demonstrates the gap.
- No total callback-authority inventory proves every mutating Settings/Setup/logging callback re-checks authority/capability at execution.
- No test demonstrates a delegated setup admin successfully applying each settings/binding/provisioning op class, or intentionally being rejected with accurate UX.
- No registered role/category provisioning option exercises those generic pipeline branches end to end.
- Real-Postgres/live Discord verification is sparse. #672 records a proof-channel binding smoke, but there is no current full production smoke covering all three lanes and Setup recovery.
- The open screenshot PR #704 should be reviewed for relevant operator UX evidence, but it is not source or automated verification.

## Recommended next session

Run a **docs + tests planning session for pointer-lane convergence and Setup authority alignment**, without immediately changing production behavior:

1. Generate a machine-readable matrix of all `SettingSpec`, `BindingSpec`, resource requirements, backfill mappings, runtime readers, writers, UI destinations, and capabilities.
2. Add/plan invariants for: backfill-target declaration parity; no dual declared pointer setting + binding; and declared-setting runtime-consumer disposition.
3. Decide and document the delegated Setup apply contract against `actor_holds_capability()` before implementing any UI expansion.
4. Produce a migration order for the four highest-risk pointer families: XP announce, economy log, governance role pointers, then BTD6/logging legacy fallbacks.
5. Define a real-guild smoke checklist covering preview, confirmation, audit, revoke, kill switch, deleted target, and partial recovery; use #704 only as supplementary visual evidence.
