# Implementation Readiness Review — 2026-06-06

> **Status:** `audit` — verified audit snapshot. This review classifies the current plans and
> status documents; it does not replace binding contracts, subsystem folios, or the
> server-management status tracker. Source code and merged commits win.
>
> **Verified at:** `4d2224b` on branch `work` before this review's edits.

## Summary

SuperBot is not waiting for another broad stabilization programme. The accepted
operational baseline remains valid, the bot-awareness PR1–PR6 programme is complete,
and the server-management foundations through PR9 are present. The clearest approved
implementation lane is the server-management tracker's **PR10: moderation first-class
configuration**. Bounded game UX follow-ups and verified settings-consistency fixes are
also safe candidates, but they are lower priority and must start from source, not old
phase plans.

The largest implementation-readiness problem found is documentation drift rather than
missing runtime foundations. `docs/health/platform-consistency-ledger.md` and
`docs/archive/phase-2-completion-readiness.md` still contain pre-ship Phase-2 cells/next-work
language. Their contract shapes and historical rationale remain useful, but their
status cells are not current implementation authority. The settings roadmap also
contains a milestone sequence whose planned/landed labels must be source-verified
before use.

AI and BTD6 expansion remain gated. The repository has substantial provider, tool-loop,
source-registry, fact-store, and cache infrastructure, but that does not clear the
maintainer-live-tool-call, orchestration-approval, ADR-006 provenance-schema,
provider-parity, caching/source-health, or behavior/config gates.

## Docs inspected

- Startup and binding route: `.claude/CLAUDE.md`, `docs/collaboration-model.md`,
  `docs/current-state.md`, `.session-journal.md`, `docs/AGENT_ORIENTATION.md`,
  `docs/repo-navigation-map.md`, `docs/architecture.md`, `docs/ownership.md`,
  `docs/runtime_contracts.md`, and `docs/helper-policy.md`.
- Every canonical folio under `docs/subsystems/`.
- All files under `docs/planning/`, `docs/ideas/`, `docs/decisions/`, and
  `docs/audits/`; the repository has no `docs/roadmaps/` or `docs/status/` directories.
- Health: `docs/health/bot-awareness-implementation-plan.md`,
  `docs/health/bot-awareness-diagnostics-plan.md`, `docs/health/platform-consistency-ledger.md`, and
  `docs/smoke-test-checklist.md`.
- Server management: the status tracker, roadmap, implementation plan,
  `docs/setup-platform/resource-provisioning-overview.md`, `docs/capability-authority.md`, and
  `docs/server-logging.md`.
- AI/BTD6: AI ownership/readiness/integration/orchestration/tool-roadmap docs, the AI
  ideas backlog, ADR-006, all `docs/btd6/btd6-*.md`, and the superseded Agent-D audit.
- Settings/games/inventories: settings roadmap/command map/presets,
  `docs/archive/phase-2-completion-readiness.md`, `docs/archive/games-actionability-roadmap.md`,
  `docs/audits/helper-debt-inventory.md`, and `docs/audits/ui-view-adoption-audit.md`.

## Source areas inspected

- Health contracts, snapshot/findings/diagnostics/consistency services, DiagnosticCog
  and diagnostic views, health-findings DB helper, migration `057`, and DB/doc tests.
- Channel/role lifecycle and views, role automation, moderation service/views, cleanup
  profiles/diagnostics/panel, setup cog/views, and related invariant/service/view tests.
- AI runtime contracts, natural-language stage, providers/tool calling, AI cog/config
  mutation/settings keys, `services/ai_tools.py`, and AI runtime/service/view tests.
- BTD6 cogs/services/views/DB helpers/settings/data, BTD6 migrations `040`–`055`, and
  BTD6 service/grounding/provider tests.
- Settings manager views/cog, settings/binding/provisioning services and tests, game
  views/cogs/actionability tests, and the Git history for shipped programme commits.

## Workstream status table

| Workstream | Status | Evidence | Remaining work | Risk | Next action |
|---|---|---|---|---|---|
| Health / diagnostics / bot awareness | **Implemented; Needs verification** | Health contracts/snapshot/findings services, owner-gated `diagnostics_health_snapshot`, migration `057`, integration/static SQL pins, and bot-awareness PR1–PR6 commits are present. | Maintainer live-test production AI tool selection and grouped Discord findings render. Dense platform-view pagination is ideas-only UX follow-up. | Low for read-only verification; high if changed into remediation. | Live-test only. Require a new approved plan for write-capable diagnostics. |
| Server management foundations through PR9 | **Implemented** | Moderation convergence, role feasibility/lifecycle/automation, channel lifecycle/reorder, and cleanup versioning/builder/diagnostics are present and test-covered; tracker records the same. | Tracker queue begins at PR10; bounded UX follow-ups remain. | Moderate because mutations must preserve service/audit/capability boundaries. | Implement tracker PR10 next, after a fresh source read. |
| Server management PR10 | **Ready for implementation** | It is the first remaining item in the authoritative tracker and its dependencies are shipped. | First-class moderation config: mod roles, log destinations, escalation, DMs. | Moderate; settings/binding ownership and callback authority must remain consistent. | Use the implementation plan for scope and binding docs for contracts. |
| Server management PR11–PR14 | **Partially implemented / Deferred by dependency order** | Existing setup, repair, role, and hub primitives cover parts of the target, but the tracker sequences these after PR10 and other dependencies. | Setup role/mod/governance sections, setup diagnostics/repair integration, role templates, unified hub. | Moderate-to-high if started out of order or rewritten broadly. | Keep in tracker order; do not rewrite setup or the hub now. |
| Server-management UX follow-ups | **Ready for implementation** (bounded, lower priority) | Moderation still uses member text inputs; time/XP panels use role selectors but have no bulk “Clear missing”; Edit Role remains a bespoke selection path. | Member quicksearch, bulk clear-missing, selector-ize Edit Role. | Low-to-moderate when isolated and test-pinned. | Take one bounded follow-up only if PR10 is not the session goal. |
| AI owner diagnostics tool | **Implemented; Needs verification** | `PLATFORM_OWNER` derivation, tool registry/handler, provider tool-call loops, and tests are present. | Maintainer production live tool-call verification. | Provider/environment dependent. | Live-test; do not infer production success from sandbox unit tests. |
| Reusable AI orchestration foundation | **Partially implemented; Pending approval** | Provider-neutral contracts and bounded tool loops already exist; the orchestration plan proposes reusable toolsets, policy, budgets, and evidence behavior beyond the current seams. | Reconcile/approve the foundation before net-new tools. | High risk of parallel orchestration or policy drift. | Dedicated approval/reconciliation session, no new capability implementation yet. |
| AI extra-tool backlog | **Ideas only / not approved; Blocked** | The ideas README and AI ideas file explicitly deny implementation authority; global expansion gate remains. | Approval plus cleared provider/provenance/source-health/config gates. | High. | Do not implement. |
| BTD6 existing runtime/data surfaces | **Implemented, with verification gaps** | Cogs, views, source registry, ingestion runs, facts, blobs, caches, grounding, strategies, events, and tests exist. | Provider parity/freshness/source-health and rendered degraded-source behavior still need reconciliation/live checks. | Moderate. | Stabilization/verification only. |
| BTD6 new extraction/mappings | **Blocked / Deferred** | ADR-006 requires a follow-on provenance schema/ownership implementation; no post-`058` migration clears that gate. Existing `btd6_facts.source_id`/`fact_type` is not the full ADR-006 contract. | Implement and verify ADR-006 schema/owner-per-fact-type contract before extraction. | High migration/ownership risk. | Do not resume extraction or add mappings. |
| Settings / bindings / provisioning substrate | **Implemented** | Registries, typed resolution/mutation, binding backfill/mutation, provisioning catalogue/preview/confirmed apply, capability authority, and editable settings surfaces exist. | Per-subsystem adoption and UX/consistency gaps remain. | Moderate if old phase cells are trusted. | Use source + folio; select a verified inconsistency, not a stale ledger cell. |
| Settings roadmap status sequence | **Stale/conflicting** | Its S7–S12 planned/in-progress labels do not reliably describe all shipped access/setup/cleanup surfaces now present. | Reconcile milestone labels if the roadmap is reused as a programme tracker. | Medium documentation-driven duplication risk. | Treat as architectural context until reconciled. |
| Platform consistency ledger status cells | **Stale/conflicting; Needs verification** | It still marks shipped feature flags, arbitration, participation, diagnostics, teardown, and setup work as future/in-flight Phase-2 PRs. | Source-backed row-by-row refresh. | High if used as an implementation queue. | Preserve contract shapes; do not implement from a cell until verified. |
| Phase-2 completion-readiness doc | **Superseded / Historical** | It still calls PR-10 current next work although unified consistency diagnostics and later setup work shipped. | None as a live queue; retain blocker-name/reference history. | Medium if treated as current. | Use current-state, folios, and active trackers instead. |
| Games actionability baseline | **Implemented** | Roadmap marks the sweep complete; game folio and actionability/view tests pin terminal disabling/history behavior. | Bounded deferred UX follow-ups and live smoke checks only. | Low if ADR-002 is preserved. | Do not reopen restart-safe state; take only testable UX fixes. |
| Game restart safety | **Deferred by accepted decision** | ADR-002 explicitly accepts non-restart-safe in-flight game state while protecting money. | No work approved. | High architectural scope. | Do not implement Redis/external state or restart-safe games. |
| Helper/UI adoption inventories | **Stale snapshot / reference only** | Their own banners direct readers to newer audits/source and warn that old backlogs shipped or drifted. | Re-run only when a focused helper/UI cleanup is approved. | Low if treated as snapshots. | Do not use as an automatic queue. |
| Raw 2026-06-05 audits and old superbot planning routers | **Superseded / Historical** | Their banners point to the consolidation/current-state/folios; later merges shipped many findings. | None as current implementation authority. | Medium if agents skip banners. | Keep for rationale only. |
| Ideas documents | **Ideas only / not approved** | `docs/ideas/README.md` defines the promotion path and denies implementation authority. | Promotion to an approved plan. | High if mistaken for backlog approval. | Do not implement directly. |

## Ready for implementation now

1. **Server-management PR10** is the highest-value approved lane. It is first in the
   authoritative tracker and its moderation convergence dependency is shipped.
2. A **single bounded server-management UX follow-up** is safe when isolated and
   regression-tested: moderation member quicksearch, time/XP bulk clear-missing, or
   selector-driven Edit Role.
3. **Source-verified settings/platform consistency corrections** are safe when they
   repair an already-defined contract and include tests. The stale ledger itself is
   not a queue.
4. **Bounded game interaction UX fixes** are safe if a specific regression is first
   reproduced and ADR-002 remains untouched. No unresolved terminal-state regression
   was proven by this review.
5. Documentation/status reconciliation and stale doc-test corrections are safe now.

## Needs stabilization first

- The platform-consistency ledger needs a row-by-row source-backed refresh before it
  can again serve as a reliable adoption punch list.
- The settings roadmap's milestone status needs reconciliation before its S7–S12
  sequence is used as current work ordering.
- AI production tool calling needs maintainer live verification; the reusable
  orchestration plan needs approval/reconciliation before expansion.
- BTD6 needs ADR-006 schema/ownership implementation plus provider parity,
  cache/freshness/source-health, and behavior/config verification before extraction.
- Server-management PR11–PR14 should stay behind the tracker's dependency order.

## Deferred / gated work

- New BTD6 extraction or mappings.
- New AI tool capabilities.
- Write-capable health remediation.
- Broad setup-wizard or server-management-hub rewrites.
- Redis/external state and restart-safe game state.
- Any ideas backlog item that has not passed the ideas-to-plan promotion path.

## Superseded or stale docs found

- `docs/archive/phase-2-completion-readiness.md`: superseded as a live next-work queue.
- `docs/health/platform-consistency-ledger.md`: contract/reference shape remains useful, but
  implementation-status cells are stale and conflict with source.
- `docs/setup-platform/settings-customization-roadmap.md`: architectural lanes remain useful; milestone
  status sequence needs source reconciliation.
- `docs/planning/server-management-implementation-plan-2026-06-05.md`: shipped banner
  lagged PR8+PR9 and incorrectly said the remaining queue began at PR8.
- `docs/planning/server-management-status-2026-06-05.md`: PR7 heading still said “this
  PR” after later work shipped.
- Raw 2026-06-05 audits and old superbot planning routers are already bannered
  superseded/historical and remain context only.

## Immediate fixes applied

- Added this source-grounded readiness audit without creating a competing tracker.
- Corrected current-state/read-path wording so agents route to the server-management
  tracker and do not treat stale Phase-2 ledgers as current queues.
- Reclassified the Phase-2 completion snapshot and platform-consistency status cells.
- Corrected stale server-management plan/tracker shipped/remaining wording.
- Replaced the stale doc-test assertion that required PR-10 to be “current next work”
  with a guard that requires the Phase-2 document to identify itself as historical.

## CI / verification

- Ran the required broad and area-specific `rg` searches; the result sets contained
  6,712 and 13,907 matches respectively and were used as discovery inputs, not as
  authority.
- Inspected `.github/workflows/code-quality.yml` and `scripts/check_quality.py --help`.
- `python3.10 -m pytest tests/unit/docs -q --tb=short`: **54 passed**.
- `python3.10 scripts/check_architecture.py --mode strict`: **0 errors**, 87 known
  warnings.
- `python3.10 scripts/check_quality.py --full`: **passed** (black, isort, ruff,
  mypy, and **7646 passed / 16 skipped** pytest suite).

## Recommended next session

Implement **server-management PR10: moderation first-class configuration** from the
status tracker. Start at the server-management folio and tracker, then verify the
existing moderation/settings/binding/capability seams. Keep the change service-owned,
callback-authorized, audited, and test-covered; do not begin PR11–PR14 or a hub/setup
rewrite in the same session unless PR10's approved scope directly requires it.
