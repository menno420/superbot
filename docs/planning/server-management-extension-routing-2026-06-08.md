# Server Management, Setup, Access, and Routine Extensions — routing draft

> **Status:** `plan` — planning/routing draft; not implementation approval.
> **Horizon:** Existing authoritative plans; this doc is a routing addendum, not a competing server-management tracker.

## Planning contract

- **Status:** roadmap draft; routing only, not approval and not an active implementation lane.
- Source code, merged PRs, binding contracts, subsystem folios, and `docs/current-state.md` outrank this draft.
- Preserve domain-service mutation ownership, direct-vs-draft lane rules, deterministic event flow, auditability, rollback safety, observability, cache invalidation, and testability.
- Before implementation, re-verify source, live PRs, the relevant folio, and every named gate.

## Context and objective

Route owner ideas for scheduled announcements, anti-spam/abuse detection, quiet/availability policy, access explanations, setup guidance, owner analytics, and future automation into the existing server-management and adaptive setup/access/routine authorities.

## Scope and destination

- Adaptive setup, access explanations, Help Preview, locked reasons, central availability/quiet policy, setup guidance, profiles, and routine-engine extension: already covered by `adaptive-setup-access-routine-platform-2026-06-08.md`.
- Moderation configuration and safe deterministic anti-spam controls: route to the server-management roadmap/status tracker; AI-based detection stays AI-gated.
- Scheduled announcements/reminders: route as a curated Routine Engine action only after its authority/audit decision.
- Owner/admin analytics: read-only reviewed concept after privacy/retention/aggregation decisions; reuse diagnostics/audit reads, not a new dashboard.

## Out of scope

A second server-management tracker, arbitrary automation scripts, direct Discord mutations, AI moderation actions, or analytics collection before privacy review.

## Existing seams and likely roots

Reuse `setup_diagnostics`, `setup_operations`, `command_access_service`, `access_projection`, capability/governance resolution, moderation services/config, settings/bindings/provisioning lanes, existing managers/hub, readiness/audit/event reads, and the future Routine Engine seam named by the adaptive plan. Likely roots include `disbot/services/setup_*`, `disbot/services/command_access_service.py`, `disbot/services/access_projection.py`, `disbot/services/moderation_*`, `disbot/services/governance_service.py`, and server-management/setup views.

## Proposed slices

1. Continue only the authoritative active server-management/status sequence.
2. Revise adaptive-plan read-only access/explanation and availability-policy slices after its existing owner questions clear.
3. Produce a deterministic scheduled-announcement action contract as part of Routine Engine planning: curated action, preview, confirmation, audit, disable, retry/degraded behavior.
4. Extend moderation policy/readiness explanations before considering AI detection.
5. Define privacy-bounded analytics requirements and reuse existing audit/diagnostics reads.

## Dependencies, risks, and mechanics

The server-management tracker remains authoritative. New setup op-kinds require dispatcher + DB gate + migration. Direct-vs-draft choice follows mutation shape. Announcement delivery needs permission checks, rate limits, retry/degraded behavior, audit, and safe disable. Analytics and anti-spam require privacy/moderation/retention review. AI detection is blocked by the AI expansion/action gates.

## Migration, cache, audit, rollback, and test implications

Follow the authoritative plans: additive migrations and the three-place setup-op-kind contract where applicable; canonical settings/binding/capability invalidation; audit previews/applies/delivery/moderation decisions; safe disable and staged-draft rollback; tests for authority re-checks, retries, Discord partial failure, rate limits, privacy, and deterministic scheduling.

## Open questions and next session

Use existing adaptive-platform/router questions; do not add a parallel ownership decision here. **Recommended next model/session:** Opus revises Routine Engine/announcement authority after the active lane and existing questions; Sonnet may take only an explicitly approved deterministic read-only explanation slice.
