# Settings / bindings / provisioning subsystem — folio

> **Status:** `living-ledger` (area index). Source + binding contracts win.
> **Last updated:** 2026-06-06.

## What & where

This area has three distinct mutation lanes: scalar/enum **settings**, Discord
resource-pointer **bindings**, and confirmed **resource provisioning**. Start in
`disbot/core/runtime/settings_registry.py`, `disbot/core/runtime/bindings.py`,
`disbot/services/settings_mutation.py`, `disbot/services/binding_mutation.py`,
`disbot/services/resource_provisioning.py`, `disbot/core/resources/`,
`disbot/services/governance_service.py`, `disbot/core/runtime/subsystem_capabilities.py`,
`disbot/views/settings/`, and `disbot/views/setup/provisioning/`.

## Rules & approved structures (binding — link, don't restate)

- `docs/settings-customization-roadmap.md` owns the three-lane model and ownership
  invariants; `docs/settings-customization-command-map.md` records live surfaces.
- A Discord resource ID is a binding, not a setting. Provisioning creates/reuses a
  resource only through preview + confirmation + audit; it is not an implicit
  binding mutation.
- `docs/capability-authority.md` owns the capability resolver and operator
  kill-switch rules. Every panel callback must re-check authority/capability at
  execution time; opening a panel is not authorization for later callbacks.
- Use `docs/platform-consistency-ledger.md` before adding another surface or write
  path. Ownership and allowed write paths remain in `docs/ownership.md` and
  `docs/runtime_contracts.md`.

## Current state

- Settings registry/resolution/mutation, binding mutation/backfill, resource
  provisioning catalogue/pipeline, setup flows, governance/capability resolution,
  audits, and operator preset documentation are present.
- Settings UI includes typed editors, invalid-setting and missing-binding surfaces;
  setup includes scan/draft/review/provisioning flows. Source remains authoritative
  on which entries are actually registered and exposed.
- Platform consistency is an active drift ledger, not proof that every possible
  configuration surface has converged.

## Plans / pending approval

`docs/settings-customization-roadmap.md` and its command map are the starting plans
for coverage work. Future changes must identify the lane and owner first, then state
migration/backfill needs, cache invalidation, audit behavior, tests, and rollback or
safe-disable behavior before implementation.

## Ideas (not approved)

Do not create a generic "configuration" write path that collapses the three lanes.
New preset or setup conveniences are candidates only when they reuse the canonical
mutation/provisioning services and preserve operator confirmation.

## Next candidates

1. Select an inconsistency from `docs/platform-consistency-ledger.md`; verify the
   live registry, command/panel surface, and canonical mutation path before fixing it.
2. For a new setting/binding, plan additive migration/backfill (if needed), cache
   invalidation, audit, callback re-check, tests, and rollback together.
3. Extend provisioning only through catalogue → preview → confirmed apply → audit,
   with partial-failure and retry behavior documented.

## Related docs

`docs/settings-customization-roadmap.md`, `docs/settings-customization-command-map.md`,
`docs/resource-provisioning-overview.md`, `docs/capability-authority.md`,
`docs/platform-consistency-ledger.md`, `docs/operator-settings-presets.md`,
`docs/ownership.md`, `docs/runtime_contracts.md`.
