# Idea — full setup-wizard server-onboarding planner (target scope)

> **Status:** `ideas` — preserved target-scope spec, **not approval**. Captured 2026-06-13 from
> GitHub issue **#232** (owner-authored 2026-05-21) so the vision lives in the repo, then the
> issue was closed. **Much of this is now the active setup-platform lane** — read those docs for
> *current* state; this file preserves the original full vision + the enumerated requirements that
> aren't yet shipped. Living homes:
> [`setup-platform/setup_wizard_finalization_plan.md`](../setup-platform/setup_wizard_finalization_plan.md)
> (current wizard; PR1–3 shipped #435, PR4–6 roadmap) ·
> [`setup-platform/roadmap_setup_platform.md`](../setup-platform/roadmap_setup_platform.md) ·
> [`setup-platform/operator-settings-presets.md`](../setup-platform/operator-settings-presets.md) ·
> [`planning/adaptive-setup-access-routine-platform-2026-06-08.md`](../planning/adaptive-setup-access-routine-platform-2026-06-08.md).

## Intent

The complete Setup Wizard should be a **guided server-onboarding planner**, not just a settings
form: scan the current server, then propose a concrete, reviewable setup plan.

## Spec (owner's original target scope)

- **Server scan (read-only, deterministic):** categories · text/voice channels · roles ·
  member counts · current bot permissions · likely admin/mod/staff channels · likely existing
  bot/log/mod/proof/counting/mining/game channels · role-hierarchy constraints · missing
  permissions that would block setup.
- **Channel/category planning:** after scan, offer (1) bind existing, (2) create only missing
  bot channels, (3) load a preset structure, (4) manual customize → Final Review. Key outputs:
  log · bot/command · admin/setup · mod-log · cleanup targets · optional game/economy/proof/
  counting/mining channels per loaded cogs.
- **Presets → `SetupOperation` drafts (never apply immediately):** Minimal · Community · Gaming ·
  Moderation-heavy · Existing-server safe mode.
- **Command/channel routing:** server-default cog enable/disable → category override → channel
  override; command-channel allowlist / bot-channel binding; per-cog routing where supported.
  Simple default (all loaded cogs on/off), optional overrides.
- **Cleanup levels (per server/category/channel):** Off · Light · Standard · Strict · Custom →
  produce reviewable setting/binding/policy operations.
- **Role suggestions:** bot-admin/setup-admin · moderator · trusted · muted/quarantined ·
  time/progression · event/game roles — respecting hierarchy/permissions; new roles previewed +
  applied only via Final Review.
- **Other questions (ask only what's needed):** prefix/help preference · warn threshold · log
  routing · economy/game defaults · automation templates (created disabled) · public vs
  admin-only panels.

## Architecture constraints (these match the shipped platform)

Scan is read-only/deterministic · suggestions become `SetupOperation` draft records · no setup
section mutates DB/Discord directly · **Final Review is the only apply point** · mutations route
through the canonical pipelines (`SettingsMutationPipeline` / `BindingMutationPipeline` /
`ResourceProvisioningPipeline` / `AutomationMutationPipeline`) · Setup Wizard + Settings Manager
share reusable controls.

## The open tail (enumerated #232 enhancements not yet shipped — preserve as design targets)

- **Confidence/explanation field** on every proposed binding/resource (*why* this channel/role
  fits).
- **Conflict detection** (proposed bot channel already exists · role hierarchy too low · missing
  Manage Channels).
- **No-surprises mode** (never create resources unless explicitly confirmed).
- **Rollback/cleanup note** per resource-creation op.
- **Setup completeness scoring** (required vs optional).
- **Post-setup summary** (created / bound / skipped / still-needs-attention).

## Routing

Settings/setup lane — folio [`subsystems/settings-bindings-provisioning.md`](../subsystems/settings-bindings-provisioning.md).
**Priority (owner, #232):** high *after* Settings Manager contract reconciliation + setup
draft-operation storage (both now in place). Promote the open-tail enhancements into the
finalization plan's future roadmap (or a dedicated planner plan) when the onboarding-planner is
scheduled; the draft-operation/Final-Review substrate they need already exists.
