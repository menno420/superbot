# ADR-005: Capability-native authority for settings/bindings + platform-flag semantics

**Status:** Accepted (2026-06-05)
**Supersedes:** none
**Superseded by:** none

> **Accepted.** This ADR is ratified; the implementing change (capability resolver +
> kill-switch wiring) lands in the same session. The capability-native settings UI
> remains gated as a follow-on (the RC-4 gate covers the UI, not the core swap).

## Context

Two coupled questions, both raised by RC-4 (audit consolidation) and the
platform-consistency ledger:

1. **Authority model.** `SettingsMutationPipeline` / `BindingMutationPipeline`
   gate mutations behind a placeholder *administrator-tier floor* rather than the
   declared, typed capability a given setting/binding actually requires
   (`SettingSpec.capability_required`). This conflates "is an admin" with "is
   allowed to change THIS setting", and blocks a capability-native settings UI.
2. **Flag semantics.** Two platform flags — `SETTINGS_MUTATION_PRIMARY` and
   `RESOURCE_PROVISIONING_PRIMARY` — are declared but not consulted as real
   kill-switches. They are either (a) intended kill-switches never wired, or
   (b) dead declarations to remove.

## Options

**Authority model:**
- **A1 (recommended):** Replace the tier floor with typed capability resolution —
  each mutation checks `SettingSpec.capability_required` / the binding's declared
  capability via the governance capability map; preserve the `system`/`backfill`
  bypass; keep audit + cache-invalidation firing.
- **A2:** Keep the tier floor, document it as intentional. (Not recommended — it
  permanently blocks the capability-native settings UI that RC-4 exists to
  unblock.)

**Flag semantics:**
- **F1:** Wire `*_PRIMARY` as real kill-switches consulted at the mutation /
  provisioning pipeline entry points via the feature-flag evaluator. *(The original
  draft named `core/runtime/config_arbitration.py`; that is a read-only config seam
  and the wrong place — corrected at ratification.)*
- **F2:** Remove the unconsulted flags as dead declarations.
- (Both are internally consistent: F1 if an incident-response kill-switch is
  genuinely wanted; F2 if not.)

## Decision

**ACCEPTED — A1 + F1** (maintainer-ratified 2026-06-05).

- **A1:** authority for settings/bindings is resolved from the declared
  `SettingSpec.capability_required` / `BindingSpec.capability_required` via a
  governance capability resolver, replacing the placeholder administrator-tier
  floor. The `system`/`backfill` bypass, audit emission, and cache invalidation are
  preserved. A spec with an **empty** `capability_required` resolves to the
  administrator floor (matching existing pipeline behaviour — *not* "no auth").
- **F1:** `SETTINGS_MUTATION_PRIMARY` and `RESOURCE_PROVISIONING_PRIMARY` become real
  operator kill-switches, consulted at the **mutation / provisioning pipeline entry
  points** (`SettingsMutationPipeline.set_value`,
  `ResourceProvisioningPipeline.provision`) via the feature-flag evaluator — *not*
  via `core/runtime/config_arbitration.py` (read-only). They default to **ALLOW**
  (block only on an explicit operator OFF) and **fail OPEN** (a flag-store outage
  must not brick writes).

The capability-native settings/bindings **UI** remains a follow-on (out of this
session's scope). The core authority swap + kill-switches land in the ratifying
session (contained: the three mutation pipelines + a governance resolver, no public
signature changes).

## Consequences (of A1 + F1)

- Mutations are authorized by the specific declared capability, not a broad tier.
- Unblocks a capability-native settings/bindings UI as a *follow-on* (not part of
  the implementing change).
- The core authority swap is contained (the three mutation pipelines + one
  governance resolver, no public-signature changes), so it lands in the ratifying
  session; only the broader settings UI is deferred.
- Two operator kill-switches exist for incident response (default ALLOW, fail OPEN).

## Re-evaluation criteria

Revisit if a per-capability authorization matrix (capability → required tier) is
introduced (v1 keeps a single administrator floor keyed on the declared capability,
plus a revoke-only guild overlay), or if the kill-switch fail-OPEN posture proves
wrong in an incident.
