# Settings / bindings / provisioning subsystem — folio

> **Status:** `living-ledger` (area index). Source + binding contracts win.
> **Last updated:** 2026-06-10 (Phase 2 #654 + Help-overlay shipped-state corrections).

## What & where

This area has three distinct mutation lanes: scalar/enum **settings**, Discord
resource-pointer **bindings**, and confirmed **resource provisioning**. Start in
`disbot/core/runtime/settings_registry.py`, `disbot/core/runtime/bindings.py`,
`disbot/services/settings_mutation.py`, `disbot/services/binding_mutation.py`,
`disbot/services/resource_provisioning.py`, `disbot/core/resources/`,
`disbot/services/governance_service.py`, `disbot/core/runtime/subsystem_capabilities.py`,
`disbot/views/settings/`, and `disbot/views/setup/provisioning/`.

## Rules & approved structures (binding — link, don't restate)

- `docs/setup-platform/settings-customization-roadmap.md` owns the three-lane model and ownership
  invariants; `docs/setup-platform/settings-customization-command-map.md` records live surfaces.
- A Discord resource ID is a binding, not a setting. Provisioning creates/reuses a
  resource only through preview + confirmation + audit; it is not an implicit
  binding mutation.
- `docs/capability-authority.md` owns the capability resolver and operator
  kill-switch rules. Every panel callback must re-check authority/capability at
  execution time; opening a panel is not authorization for later callbacks.
- Use `docs/health/platform-consistency-ledger.md` before adding another surface or write
  path. Ownership and allowed write paths remain in `docs/ownership.md` and
  `docs/runtime_contracts.md`.
- **Direct vs. draft lane choice** is canonical in `docs/ownership.md` §
  "Direct vs. draft mutation lanes": focused/reversible single-domain edits write
  directly through their audited service; compound/multi-setting/generated changes
  stage `SetupOperation` rows and apply through Final Review. Pick the lane by the
  *shape* of the change, not the panel you're in.

## Current state

- Settings registry/resolution/mutation, binding mutation/backfill, resource
  provisioning catalogue/pipeline, setup flows, governance/capability resolution,
  audits, and operator preset documentation are present.
- Settings UI includes typed editors, invalid-setting and missing-binding surfaces;
  setup includes scan/draft/review/provisioning flows. Source remains authoritative
  on which entries are actually registered and exposed.
- **Hub discovery is actionable-groups-only (audit Phases 0+1, shipped #640,
  2026-06-09):** `services/customization_catalogue.actionable_settings_groups()` is
  the one inclusion rule (editable scalar · binding · provisionable resource ·
  declared domain panel — real `DomainPanelSpec` registrations since **Phase 2,
  #654 2026-06-10**; the Phase 1 `DOMAIN_CONFIG_SUBSYSTEMS` frozenset is retired,
  pinned gone by `test_domain_panel_declarations.py`); the hub select paginates past Discord's 25-option cap and
  `SettingsHubView.create(author, guild_id)` marks routed-off groups via per-guild
  cog routing while keeping them reachable. Audit + phase queue:
  [settings audit §11](../planning/settings-cog-centralization-audit-2026-06-09.md).
- Platform consistency remains a useful contract/reference inventory, but its
  Phase-2 implementation-status cells are stale as of the 2026-06-06 readiness review.
  Verify a cell against source before treating it as pending work. The settings
  roadmap's S7–S12 milestone labels likewise need reconciliation before use as current
  sequencing.

## Plans / pending approval

`docs/setup-platform/settings-customization-roadmap.md` and its command map are the starting plans
for coverage work. The comprehensive [Adaptive Setup, Access, Profile, and Routine Platform plan](../planning/adaptive-setup-access-routine-platform-2026-06-08.md) maps the longer-lived read-model, profile, routine, and Personal Setup sequence; it is planning, not implemented. Future changes must identify the lane and owner first, then state
migration/backfill needs, cache invalidation, audit behavior, tests, and rollback or
safe-disable behavior before implementation.

- **`docs/planning/ai-btd6-answerability-roadmap-2026-06-09.md`** (`plan`) — conditionally plans one AI-settings vertical slice after a centralized effective-settings introspection read model exists; it does not approve a broad Settings Manager rewrite.
- **[`docs/planning/settings-cog-centralization-audit-2026-06-09.md`](../planning/settings-cog-centralization-audit-2026-06-09.md)** (`plan`) — source-verified audit of scalar settings, settings-adjacent domains, UI discovery/editability gaps, and the phased convergence roadmap.

- **[Help cog customization audit and roadmap](../planning/help-cog-customization-audit-2026-06-09.md)** (`plan`) — maps Help/hub/access/customization ownership; its catalogue + projection + audited presentation-overlay sequence **shipped 2026-06-10** (Q-0055–Q-0059 answered; seam #657, overlay store #659) — the overlay **editor UI** (audit Phase 5) is the open tail.

## Ideas (not approved)

Do not create a generic "configuration" write path that collapses the three lanes.
New preset or setup conveniences are candidates only when they reuse the canonical
mutation/provisioning services and preserve operator confirmation.

- [`docs/ideas/settings-presets-and-ai-template-advisor.md`](../ideas/settings-presets-and-ai-template-advisor.md) —
  the AI template/preset advisor (captured only, gated). Note: its §1 — the
  **presets + preset-then-edit + manual-entry everywhere** posture — is a
  *decided* owner posture (**Q-0070**, 2026-06-10), routed into the settings
  audit's Phase 4 row; only the advisor itself is an idea.

## Next candidates

1. Select an inconsistency from `docs/health/platform-consistency-ledger.md`; verify the
   live registry, command/panel surface, and canonical mutation path before fixing it.
2. For a new setting/binding, plan additive migration/backfill (if needed), cache
   invalidation, audit, callback re-check, tests, and rollback together.
3. Extend provisioning only through catalogue → preview → confirmed apply → audit,
   with partial-failure and retry behavior documented.

## Production-readiness reviews

- [`docs/planning/production-readiness/settings-bindings-provisioning-production-readiness-map-2026-06-12.md`](../planning/production-readiness/settings-bindings-provisioning-production-readiness-map-2026-06-12.md) — source-verified Done / Partial / Not Done inventory and production blockers (2026-06-12).

## Related docs

`docs/setup-platform/settings-customization-roadmap.md`, `docs/setup-platform/settings-customization-command-map.md`,
`docs/planning/adaptive-setup-access-routine-platform-2026-06-08.md`,
`docs/setup-platform/resource-provisioning-overview.md`, `docs/capability-authority.md`,
`docs/health/platform-consistency-ledger.md`, `docs/setup-platform/operator-settings-presets.md`,
`docs/ownership.md`, `docs/runtime_contracts.md`.

## Cross-area extension routing (not approved)

The [server-management/setup/access/routine extension routing draft](../planning/server-management-extension-routing-2026-06-08.md) preserves this folio's three mutation lanes while routing announcement/routine and guidance ideas. The [UX/mobile-first roadmap draft](../planning/ux-discoverability-mobile-roadmap-2026-06-08.md) routes presentation work through existing panels and standards rather than a new UI framework.
