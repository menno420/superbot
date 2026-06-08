# UX, Discoverability, Mobile-First, and Product Copy — roadmap draft

> **Status:** `plan` — planning/routing draft; not implementation approval.
> **Horizon:** Later; bounded slices may be selected through existing interface plans.

## Planning contract

- **Status:** roadmap draft; routing only, not approval and not an active implementation lane.
- Source code, merged PRs, binding contracts, subsystem folios, and `docs/current-state.md` outrank this draft.
- Preserve domain-service mutation ownership, direct-vs-draft lane rules, deterministic event flow, auditability, rollback safety, observability, cache invalidation, and testability.
- Before implementation, re-verify source, live PRs, the relevant folio, and every named gate.

## Context and objective

Group rich help categories/search, changelog/what's-new and balance notices, mobile-first embeds/buttons/forms, bot personality/copy, panel language/action vocabulary, profile/discovery entry points, and command-access explanations. The objective is consistent composition over existing panels, not a new UI framework.

## Scope

A mobile-first audit rubric; help/search/category and locked-reason routes; consistent action-language/personality copy; release/balance notice concepts; and slash front doors that open existing hubs only.

## Out of scope

A second router/panel framework, one slash command per sub-action, hidden-achievement spoilers, large copy sweeps without owner review, or an operator changelog without a canonical release manifest.

## Current state and seams to reuse

The mother-hub map, interface-completion roadmap, command-expansion backlog, hub UI standard, command-integration standard, config-input standard, Help routes, access projection, existing panels/views, and adaptive setup/access plan already own most mechanics.

Likely roots: `disbot/cogs/help_cog.py`, `disbot/cogs/help/`, `disbot/services/access_projection.py`, `disbot/core/runtime/interaction_helpers.py`, `disbot/views/`, and existing hub/panel renderers.

## Proposed phases

1. **Audit/rubric:** inventory representative mobile embeds/forms/buttons and define measurable limits; route findings to existing interface plans.
2. **Vocabulary and personality:** owner-reviewed action labels, denial copy, and funny/sarcastic tone boundaries; accessibility and moderation review.
3. **Discovery:** help categories/search and access explanations using existing command/access metadata; slash commands remain wrappers/front doors.
4. **What's new:** define canonical release/balance manifest ownership, then render Discord-native notices/changelog.
5. **Continuous conformance:** add focused checks/tests to existing UI standards rather than creating a new framework.

## Dependencies, risks, and mechanics

Existing interface sequencing; Q-0036 for locked-reason copy; release-manifest ownership; privacy-safe profile/discovery semantics; and owner approval for tone. Main risks are duplication, copy drift, mobile regressions, and over-notification. No new data migration is expected until a release manifest is approved; cache/audit/rollback needs follow the reused owner.

## Migration, cache, audit, rollback, and test implications

Most slices should require no schema; a release manifest needs an explicit additive owner and retention policy. Reuse existing metadata/cache owners and invalidate when commands/access/releases change. Audit only actions that already require audit; do not log private help/profile content. Rollback is copy/render/front-door reversion or feature disable. Tests should cover mobile rendering limits, accessibility, route/authority parity, locked reasons, search, and notification deduplication.

## Open questions and next session

- Q-0036 owns locked-reason copy. Release-manifest ownership and personality boundaries need owner review during revision, not silent decisions.
- **Recommended next model/session:** Opus UX/release-manifest revision; Sonnet can take a bounded mobile audit or existing-help routing slice only after selection in the authoritative interface lane.
