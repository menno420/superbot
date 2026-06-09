# AI Product Extensions — routing addendum

> **Status:** `plan` — planning/routing draft; not implementation approval.
> **Authority:** `docs/planning/ai-roadmap-2026-06-07.md`; this addendum does not compete with it.
> **Horizon:** Later, fully gated. **Owner decision needed:** Q-0040 for AI dungeon-master posture.

## Planning contract

- **Status:** roadmap draft; routing only, not approval and not an active implementation lane.
- Source code, merged PRs, binding contracts, subsystem folios, and `docs/current-state.md` outrank this draft.
- Preserve domain-service mutation ownership, direct-vs-draft lane rules, deterministic event flow, auditability, rollback safety, observability, cache invalidation, and testability.
- Before implementation, re-verify source, live PRs, the relevant folio, and every named gate.

## Context and objective

Route AI dungeon master, AI-generated game events, wider natural-language intent coverage, and the extra-tool backlog onto the existing AI roadmap. AI remains explanation/orchestration-only until every existing readiness, orchestration, guard, audit, provider, and dedicated action decision clears.

## Scope and routing

- Wider NL intent coverage: route to the central NL-stage/readiness work in the authoritative AI roadmap.
- AI dungeon master and generated narrative/event concepts: product concepts only; mechanics/rewards/difficulty remain deterministic domain-service decisions. Q-0040 owns modes, persistence, cost, moderation, and retention posture.
- Web/vision/file/KB/connectors/scheduler/admin tools: already covered by `ai-extra-tool-capability-ideas.md` and `ai-tool-capability-roadmap.md`; sequence only after orchestration foundation.
- AI-generated setup/moderation/actions: blocked until the dedicated action gates and decisions clear; use drafts/explanations, never direct writes.

## Out of scope

AI write/action tools now, AI-owned game rewards or difficulty authority, raw reasoning/tool-result retention, a second AI roadmap/orchestrator, or bypassing provider/provenance/grounding gates.

## Existing seams and likely roots

Reuse `ai_task_router`, `ai_tools`, orchestration policy/descriptors/budgets, `ai_natural_language_policy`, permission/decision-audit/readiness/diagnostics services, `ai_gateway`, domain-owned read tools, and typed evidence/result contracts. Likely roots are listed in the AI folio and service integration map.

## Proposed sequence

1. Follow the authoritative AI roadmap: readiness and orchestration foundation first.
2. Improve wider intent classification/explanation without action authority.
3. Add only approved read-only tools through descriptors, preflight, scopes, budgets, typed results, faithfulness, and safe traces.
4. Prototype DM/event narrative as text wrapping deterministic domain outputs after Q-0040 and moderation/cost review.
5. Consider any action/dynamic-scaling capability only after a dedicated owner/architecture decision and domain-service draft/confirmation path.

## Dependencies, risks, and mechanics

All AI gates in `docs/current-state.md` and the AI roadmap; Q-0040; provider cost/availability; prompt/content moderation; privacy/retention; deterministic authority; audit and safe-disable. Generated content cannot mutate rewards/state. Cache/source-health and provenance must be observable.

## Migration, cache, audit, rollback, and test implications

Defer schemas until the authoritative AI plan approves them; never persist raw reasoning or private tool results. Cache/source-health behavior follows approved providers/tools. Audit safe decisions/tool metadata and domain drafts, not hidden reasoning. Rollback is tool/provider/feature disable with domain-owned compensation only after confirmed actions are ever approved. Tests require scope/permission denials, budgets, provider failure, prompt/content safety, faithfulness, redaction, deterministic-domain authority, and no-action invariants.

## Open questions and next session

Q-0040 owns dungeon-master scope and operational posture. **Recommended next model/session:** first Opus AI session remains orchestration-foundation revision; Codex remains mapping-only for net-new AI actions, and Sonnet receives no action-tool implementation.
