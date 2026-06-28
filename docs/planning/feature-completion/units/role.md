# Roles — completion certificate

> **Status:** `living-ledger` — per-unit completion certificate; updated as the unit is assessed /
> certified. Source + merged PRs win. System: [`../README.md`](../README.md).

> **Unit:** `role` · **Type:** server-fn · **Family:** management
> **State:** ◐ assessed · **Assessed:** 2026-06-28 · **Certified:** —
> Source: `disbot/cogs/role_cog.py` (`RoleHubPanelView` + commands + Help hook) ·
> `disbot/views/roles/` (`reaction_panel.py` · `role_menu_view.py` · `role_menu_builder.py` ·
> `_role_pack_flow.py` · `exemptions_panel.py`) ·
> `disbot/services/role_automation.py` (audited member-assignment seam) ·
> `disbot/services/role_lifecycle_service.py` (audited role create/edit/delete) ·
> `disbot/services/reaction_role_service.py` · `disbot/services/role_grants_service.py` (temp-roles) ·
> `disbot/services/role_exemption_service.py` · `disbot/cogs/role/schemas.py` ·
> `disbot/utils/settings_keys/role.py` · `disbot/utils/role_packs.py`

> Assessed during the completion-first arc (Q-0209). Roles is a **broad, mature** unit (the Carl-bot-
> mature reaction-roles arc #1234…#1279 plus admin role ops + temp-roles): self-assign via emoji
> reactions **and** button/dropdown menus (normal/unique/verify modes), admin create/grant/revoke, temp
> roles with expiry sweep, colour + gradient presets, and role packs. It is **architecturally clean** —
> every member mutation routes through the audited `role_automation` seam (perm + hierarchy preflight,
> classified per-member failures, dead-binding self-heal) and every role-object op through
> `role_lifecycle_service`, both pinned by AST invariants. The honest gaps are **best-in-class breadth**
> (the gated web builder, exclusive role groups / per-menu limits, emoji-triggered *temp* roles, bulk
> member grants) — feature scope, not defects.

## Rubric (server function)

### A. Functional completeness — "does its job, in every case"
- [x] **Core promise delivered** — emoji reaction-role bindings (`reaction_role_service.py`) +
      button/dropdown role menus (`role_menu_view.py`, restart-durable) with normal/unique/verify modes;
      admin role create/grant/revoke (`role_lifecycle_service` + `role_automation.apply`); temp-roles
      with expiry sweep (`role_grants_service.py`); time/XP auto-role thresholds.
- [ ] **Every best-in-class sub-option exists** — ❌ **partial.** Has: multi-emote per message,
      channel/message pickers, colour + gradient presets, role packs, verify/unique modes, exemptions.
      **Missing vs Carl-bot:** web builder (gated — Surface A) · mutually-exclusive role *groups* /
      per-menu max-N enforcement (the `max_roles` field exists; no group constraint) · emoji-triggered
      *temporary* role · in-place menu-message edit (Save posts a new message) · bulk multi-member grant ·
      menu-option reorder. → punch-list #2.
- [x] **Failure modes honest** — hierarchy/permission preflight via `check_preflight` +
      `_blocking_verdict`; classified per-member `ApplyError` codes surfaced via `summarize_failures`;
      dead reaction-role bindings self-heal (dropped + audited as `system`); per-member isolation (one
      failure never aborts the batch).
- [x] **Idempotent** — already-held roles are skipped (no-op emits nothing, `role_automation.apply`);
      unresolved tiers dropped rather than dangling.

### B. Reachability & UI — "the most convenient way"
- [x] **Command panel(s) exist** — `RoleHubPanelView` (persistent, 7 buttons: Create · Manage · Time ·
      XP · Reaction · Diagnostics · Exemptions), each rendering a sub-panel in place; the reaction
      builder (`reaction_panel.py`) and role-menu builder (`role_menu_builder.py`) are full CRUD flows.
- [x] **Reachable every natural way** — `!rolemenu` entry point + Help hook (`build_help_menu_view`) +
      Community-hub child (`parent_hub: community`); admin commands `!rolesettings`/`!rolecreator`.
- [x] **Integrated into the Setup wizard** — role-templates section (`views/setup/sections/`) +
      time/XP auto-role staging.
- [x] **Return navigation** — sub-panels use `.edit_message()` + `attach_back_button` to the parent; no
      dead-ends.
- [x] **In-place, not spammy** — panels edit in place; ephemeral pickers for the builder steps.

### C. Convenience
- [x] **Multi-emote + pickers** — multiple emotes per message (PK is per-emoji, #1234); channel +
      most-recent/pick/new/by-ID message pickers (#1243); bulk role-pack create (`_role_pack_flow.py`,
      #1300/#1302).
- [x] **Presets** — colour presets (`_helpers.py`), gradient presets (gated on
      `supports_role_gradients`), curated role packs (`utils/role_packs.py`).
- [x] **Clear feedback** — operator results show succeeded/failed + a classified failure summary
      (`role_cog.py` `_format_role_check_result`); member-facing menus show per-mode hints.

### D. Authority & safety
- [x] **Authority re-checked at callback** — cog decorators (`has_permissions(administrator/manage_roles)`)
      **and** per-button re-checks (`manage_roles`/`administrator`) **and** panel-level `_can_manage`
      re-checks at callback; settings specs require `role.settings.configure`.
- [x] **All mutations through audited seams** — member grants via `role_automation.apply` (perm +
      hierarchy preflight, `actor_type` threaded, `audit.action_recorded` per change); role-object ops
      via `role_lifecycle_service` (`role.lifecycle_changed` + audit). Pinned by
      `test_no_direct_role_mutations.py` (no direct create/edit/delete in the role surfaces) +
      `test_no_direct_role_threshold_writes.py`.
- [x] **Resource creation safe** — auto-created colour roles go through the audited
      `RoleLifecycleService.apply` (`ensure_role`), not raw `guild.create_role`.
- [x] **Reuses governance** — capability floor; exemptions via `role_exemption_service`; no second
      allowlist.

### E. Configuration
- [x] **Bindings + settings through the proper seam** — reaction-role binds/unbinds through the audited
      `reaction_role_service` (`_emit`); settings (`REACTION_ROLES_ENABLED`, `TIME_ROLES_STACK`,
      `XP_ROLES_STACK`) via `SettingSpec`s with `capability_required`; threshold writes through the
      audited `role_automation.set_{time,xp}_threshold`.
- [x] **`settings_keys` constants** — `utils/settings_keys/role.py` (no raw strings in the views).
- [x] **Typed widgets** — builder uses selects/pickers; settings are typed specs.

### F. Wiring & discoverability
- [x] **Registry** — key `role`, `category: management`, `visibility_tier: administrator`,
      `entry_points: [rolemenu]`, `parent_hub: community`, related `[xp]`, 4 capabilities
      (`subsystem_registry.py`).
- [x] **Discoverable in Help** — `build_help_menu_view` hook; Community-hub child.
- [x] **Homed in `ownership.md`** — role create/edit/delete via `role_lifecycle_service`; thresholds via
      `role_automation`; reads + `reaction_roles` via `utils/db/roles.py`.

### G. Tests & evidence (required for ✔)
- [x] **Behavior tests** — `test_role_automation.py` (compute_assignments / preflight / apply isolation /
      error classification), `test_role_automation_thresholds.py`, `test_role_lifecycle_service.py`,
      `test_role_grants_service.py` (grant + expiry sweep), `test_role_exemption_service.py`,
      `test_reaction_role_service.py`, `test_reaction_roles_refinement.py` (multi-emote / picker /
      self-heal), `test_role_menu_view.py`.
- [x] **Authority/seam tests** — `test_no_direct_role_mutations.py` +
      `test_no_direct_role_threshold_writes.py` (AST fences); callback re-checks in view tests.
- [x] **Mutation-seam tests** — audit emission asserted on grants/threshold writes.
- [ ] **Live walkthrough recorded** — pending. → punch-list #3.
- [ ] **Owner ✔** — pending. → punch-list #4.

## Punch-list (clear these to certify)

1. **Web builder (Surface A)** *(owner-paced / gated)* — the hosted reaction-role builder, the one
   remaining piece of the overhaul plan ([plan](../../reaction-roles-overhaul-plan-2026-06-21.md)).
2. **Best-in-class breadth (rubric A)** *(owner-paced, deepening)* — mutually-exclusive role *groups* /
   enforced per-menu max-N · emoji-triggered temp-roles · in-place menu-message edit · bulk multi-member
   grant · menu-option reorder.
3. **Live walkthrough** *(owner / live-bot)* — `/verify-bot` boot + scripted click-through (reaction
   builder → bind multi-emote → self-assign → temp-role grant + expiry → admin create/revoke), with
   screenshots.
4. **Owner sign-off** — maintainer uses it and confirms "it does its job the most convenient way."

## Evidence
- **Tests:** `tests/unit/services/test_role_automation*.py` · `…/test_role_lifecycle_service.py` ·
  `…/test_role_grants_service.py` · `…/test_role_exemption_service.py` ·
  `tests/unit/.../test_reaction_role*.py` · `tests/unit/invariants/test_no_direct_role_mutations.py` ·
  `…/test_no_direct_role_threshold_writes.py`
- **Walkthrough:** pending (punch-list #3)
- **Owner sign-off:** pending (punch-list #4)

## Verdict
Roles is **broad and architecturally clean** — Carl-bot-mature reaction roles + role menus + admin ops +
temp-roles, every mutation through an audited seam (two AST invariants), classified failure handling,
dead-binding self-heal, presets and packs. It is **not yet `✔ certified`**: the gaps are the **gated web
builder** (#1) and **best-in-class breadth** (exclusive groups, emoji temp-roles, bulk grant, in-place
edit — #2), plus the owner walkthrough/sign-off (#3/#4). No safety/audit/dead-end issues found.
