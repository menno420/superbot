# Setup / settings / provisioning — planning & reference cluster

> **Status:** `reference` — index for the setup-wizard, settings-customization, and
> resource-provisioning docs. Area entry point lives in the folio:
> [`../subsystems/settings-bindings-provisioning.md`](../subsystems/settings-bindings-provisioning.md).
> Source code and merged PRs win over any plan here.

Consolidated out of the top-level `docs/` pile (owner decision Q-0010) so the
setup/settings/provisioning material sits together behind the folio. Read the folio
first; reach for these on demand.

| Doc | What it is |
|---|---|
| [`settings-customization-roadmap.md`](settings-customization-roadmap.md) | The three lanes (settings / binding / provisioning) and which pipeline owns which (`reference`). |
| [`settings-customization-command-map.md`](settings-customization-command-map.md) | Per-setting customization command surface (`living-ledger`). |
| [`operator-settings-presets.md`](operator-settings-presets.md) | Operator settings presets inventory (`living-ledger`). |
| [`quiet-hours-design.md`](quiet-hours-design.md) | Minimal design for per-guild quiet hours using the existing settings mutation/audit seams (`plan`). |
| [`resource-provisioning-overview.md`](resource-provisioning-overview.md) | The resource-provisioning (RPM) lane and confirmation rules (`reference`). |
| [`roadmap_setup_platform.md`](roadmap_setup_platform.md) | Setup-platform target roadmap (`plan`, read for context). |
| [`setup_wizard_finalization_plan.md`](setup_wizard_finalization_plan.md) | Setup-wizard finalization plan (`plan`, read for context). |

Related binding/reference docs that stay top-level: the config-input UI rules
([`../building-roadmap/config-input-standard.md`](../building-roadmap/config-input-standard.md))
and capability authorization ([`../capability-authority.md`](../capability-authority.md)).
