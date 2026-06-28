# Settings — completion certificate

> **Status:** `living-ledger` — per-unit completion certificate; updated as the unit is assessed /
> certified. Source + merged PRs win. System: [`../README.md`](../README.md).

> **Unit:** `settings` · **Type:** server-fn · **Family:** platform
> **State:** ◐ assessed · **Assessed:** 2026-06-28 · **Certified:** —
> Source: `disbot/cogs/settings_cog.py` (`!settings` hub + Help hook) ·
> `disbot/views/settings/` (`hub.py` · `subsystem_view.py` · the typed edit widgets
> `edit_boolean`/`edit_text`/`edit_number`/`edit_enum`/`edit_channel`/`edit_role`/`edit_number_presets` ·
> `reset_button` · `audit_view`) · `disbot/services/settings_mutation.py` (the 11-step audited
> pipeline) · `disbot/services/binding_mutation.py` · `disbot/core/runtime/subsystem_schema.py` (the
> schema registry + `SettingSpec`) · `disbot/utils/settings_keys/` · folio
> `docs/subsystems/settings-bindings-provisioning.md`

> Assessed during the completion-first arc (Q-0209). Settings is the **platform-grade configuration
> spine** every other subsystem routes through: a `!settings` hub that surfaces each subsystem's group,
> typed edit widgets (bool/int/enum/channel/role/presets), and a strict mutation discipline — every
> scalar write goes through the audited `SettingsMutationPipeline` (capability re-check → coercion →
> validation → DB+audit transaction → cache invalidation → event) and every resource pointer through
> `BindingMutationPipeline`, both protected by CI invariants (a read-only-cog allowlist + a no-raw-KV
> fence). The honest gaps are **operator-convenience breadth** (no settings search, no export/import or
> config templates, no draft/Final-Review lane for compound edits, no change-history/rollback view) and
> the gated **web dashboard** — UX ceiling, not safety/correctness.

## Rubric (server function)

### A. Functional completeness — "does its job, in every case"
- [x] **Core promise delivered** — the hub surfaces every subsystem's actionable settings group
      (`hub.py` `actionable_settings_groups()`); typed widgets cover bool/text/number/enum/channel/role +
      numeric presets (`views/settings/edit_*.py`); per-spec validators + coercion-error + disabled-state
      messaging (`settings_mutation.py`, feature-flag gate in `settings_cog.py`).
- [ ] **Every best-in-class sub-option exists** — ❌ **partial.** **Missing:** a **draft / Final-Review
      lane** for compound multi-setting edits (all writes are immediate) · a **message**-kind binding
      widget · inline (pre-submit) validation feedback. → punch-list #2.
- [x] **Failure modes honest** — invalid value → `SettingsValidationError`; uncoercible →
      `SettingsCoercionError`; capability denied → a human-reason `CapabilityDecision`; disabled flag →
      a clear "how to re-enable" embed.
- [x] **Idempotent** — KV sets are reapply-safe; the audit records prev+new so a repeat is visible.

### B. Reachability & UI — "the most convenient way"
- [x] **A command panel exists** — `!settings` → `SettingsHubView` (domains grouped; header shows
      settings/bindings/resources/findings counts); drill into a subsystem → per-setting edit widgets.
- [x] **Reachable every natural way** — `!settings` entry point + Help hook (`build_help_menu_view`);
      Admin-hub child (`parent_hub: admin`).
- [ ] **Integrated into the Setup wizard** — ⚠️ **partial.** The Q-0098 `setup_delegate` lane exists and
      individual subsystems' settings are configured via their own setup sections, but the full Settings
      surface is not itself a wizard step (by design — onboarding routes through per-subsystem sections).
      Acceptable waiver. → note.
- [x] **Return navigation** — every subsystem drill + diagnostic sub-panel (Needs Setup / Invalid /
      Missing Bindings / Recent Changes) has a Back-to-Hub button; no dead-ends.
- [x] **In-place, not spammy** — edits are an ephemeral confirmation + a parent-embed refresh
      (`edit_boolean.py` etc., `interaction.response.edit_message`).

### C. Convenience
- [x] **Domain grouping** — subsystems grouped by `parent_hub`/`hub_group` (registry).
- [ ] **Search / jump** — ❌ no search across settings by name and no jump-to-setting; navigation is
      hub → subsystem → setting. → punch-list #2.
- [x] **Presets + clear feedback** — numeric presets (`SettingSpec.presets`, e.g. XP cooldown
      0/15/30/60/120/300); every edit confirms "X → Y (was …)"; a read-only audit panel shows recent
      `settings_mutation_audit` rows.

### D. Authority & safety
- [x] **Authority re-checked at callback** — every edit widget routes through
      `SettingsMutationPipeline.set_value()`, which re-checks `actor_holds_capability` at the write
      (`settings_mutation.py`), independent of who opened the panel.
- [x] **All writes through the audited pipeline** — scalars via `SettingsMutationPipeline`, pointers via
      `BindingMutationPipeline`; each emits `audit.action_recorded` + a `settings_mutation_audit` row.
      Pinned by `test_settings_cog_read_only.py` (only the 8 allowlisted edit files may import the
      mutation pipeline) + `test_no_direct_settings_keys_writes.py` (no raw `db.set_setting` on declared
      keys).
- [x] **Nothing security-sensitive editable below floor** — every `SettingSpec` carries a
      `capability_required` floor (default administrator); per-capability overrides are revoke-only (no
      escalation).
- [x] **Reuses governance** — the capability layer **is** the authority model; no second allowlist.

### E. Configuration
- [x] **Pipeline contract** — the 11-step `SettingsMutationPipeline` (input → authority → coercion →
      validation → read-prev → DB+audit txn → cache invalidate → event → typed result), with a fail-open
      `SETTINGS_MUTATION_PRIMARY` kill-switch + guild/global scope.
- [x] **`settings_keys` constants** — all keys in `utils/settings_keys/` (one submodule per subsystem),
      pinned by reserved-key + package-structure invariants.
- [x] **config-input-standard widgets** — widgets dispatched by `input_hint`/`value_type`
      (`subsystem_view.py`); native channel/role selects; numeric presets + override modal.

### F. Wiring & discoverability
- [x] **Registry** — key `settings`, `category: platform`, `visibility_tier: administrator`,
      `entry_points: [settings]`, `parent_hub: admin`, cap `settings.manager.view` (the hub is a
      *browse* surface; mutation is the allowlisted edit-widget seam).
- [x] **Discoverable in Help** — `build_help_menu_view` hook (flag-gated; shows the disabled embed when
      off).
- [x] **Schema registry** — `core/runtime/subsystem_schema.py` (`register`/`get_schema`/`all_schemas`);
      every subsystem declares its `SubsystemSchema` at cog load.

### G. Tests & evidence (required for ✔)
- [x] **Behavior tests** — `test_settings_mutation_pipeline.py` (11-step contract, every error class),
      `test_settings_resolution.py`/`…_global.py`, `test_settings_hub_view.py`,
      `test_subsystem_settings_view.py`, `test_settings_edit_round_trip.py`,
      `test_settings_reset_round_trip.py`, `test_settings_input_hint_dispatch.py`,
      `test_settings_diagnostic_subviews.py`.
- [x] **Authority tests** — `test_settings_edit_safety.py` (callback re-check);
      `test_settings_command_access.py`.
- [x] **Mutation-seam tests** — `test_settings_cog_read_only.py`, `test_no_direct_settings_keys_writes.py`,
      `test_settings_mutation_audit_alignment.py`, `test_settings_declared_vs_consumed_parity.py`,
      `test_settings_reachability.py`.
- [ ] **Live walkthrough recorded** — pending. → punch-list #3.
- [ ] **Owner ✔** — pending. → punch-list #4.

## Punch-list (clear these to certify)

1. **Per-setting visibility / reset breadth** *(offline, minor)* — reset exists per-setting via a button;
   consider a guarded bulk reset-to-default and a clearer "added/deprecated" schema-version surface.
2. **Operator-convenience breadth (rubric A/C)** *(owner-paced, deepening)* — settings **search/jump** ·
   a **draft / Final-Review lane** for compound edits · **export/import or config templates** · a
   **change-history / rollback** view over the audit table · a **message**-kind binding widget · inline
   pre-submit validation.
3. **Live walkthrough** *(owner / live-bot)* — `/verify-bot` boot + scripted click-through (hub → a
   subsystem → toggle a bool → set a channel/role → reset → audit panel), with screenshots.
4. **Owner sign-off** — maintainer uses it and confirms "it does its job the most convenient way."

## Evidence
- **Tests:** `tests/unit/services/test_settings_mutation_pipeline.py` · `…/test_settings_resolution*.py` ·
  `tests/unit/views/test_settings_*` · `tests/unit/invariants/test_settings_cog_read_only.py` ·
  `…/test_no_direct_settings_keys_writes.py` · `…/test_settings_mutation_audit_alignment.py`
- **Walkthrough:** pending (punch-list #3)
- **Owner sign-off:** pending (punch-list #4)

## Verdict
Settings is a **production-grade configuration spine** — a domain-grouped hub, typed widgets, and a
strict audited pipeline (capability re-check + audit + cache + event) protected by CI invariants
(read-only-cog allowlist, no-raw-KV fence). It is **not yet `✔ certified`**: the gaps are **operator-
convenience breadth** (search, draft/Final-Review lane, export/templates, change-history — #2), minor
reset/version surfacing (#1), and the owner walkthrough/sign-off (#3/#4). No safety/audit/dead-end
issues found.
