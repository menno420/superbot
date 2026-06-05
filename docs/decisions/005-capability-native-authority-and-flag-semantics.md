# ADR-005: Capability-native authority for settings/bindings + platform-flag semantics

**Status:** Proposed — awaiting maintainer ratification (drafted 2026-06-05)
**Supersedes:** none
**Superseded by:** none

> **This ADR is a DRAFT.** It records the decision that must be made and the
> recommended option, but it is **not** ratified. No code may rely on it until a
> maintainer changes its status to Accepted. Settings/bindings UI expansion stays
> blocked until then (the RC-4 gate).

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
- **F1:** Wire `*_PRIMARY` as real kill-switches consulted only by
  `core/runtime/config_arbitration.py`.
- **F2:** Remove the unconsulted flags as dead declarations.
- (Both are internally consistent: F1 if an incident-response kill-switch is
  genuinely wanted; F2 if not.)

## Decision

**DEFERRED — the maintainer ratifies A1/A2 and F1/F2.** Recommended: **A1 + (F1 or
F2 per operational need)**. Until ratified, settings/bindings UI expansion stays
blocked, and the implementing PR is kept OUT of the current wave (it touches many
settings/bindings surfaces).

## Consequences (of the recommended A1)

- Mutations authorized by the specific declared capability, not a broad tier.
- Unblocks a capability-native settings/bindings UI as a *follow-on* (not part of
  the implementing PR).
- Broad surface area → the implementing PR is large; deliberately deferred.

## Re-evaluation criteria

Ratify (or amend) when the maintainer decides the flag fate and confirms the
capability-native direction; the implementing PR then proceeds in its own session.
