# 2026-06-08 — Tooling reliability, EventBus wiring map, and owner-memory capture

Continuation of the PR12 session (`2026-06-08-server-management-pr12-diagnostics.md`).
After PR12 merged (#571), the maintainer's end-of-chat Q&A turned into a meta/tooling
thread that shipped four more PRs and captured durable owner decisions.

## Shipped (all merged)

- **#572 — CLAUDE.md reliability tiers.** Replaced the blanket "CodeGraph caller edges
  are hints, ~half invisible" with three *verified* tiers (tested against grep/Read
  ground truth): trust CodeGraph for definition/signature/`list_functions`/complexity;
  trust **Grimp** (`context_map.py`) for imports incl. lazy; grep-verify caller edges
  (the **bare-token rule** — `module.foo()` / indirect / decorator calls are missed);
  read source for the both-tools-blind class (EventBus/registry/decorator).
- **#573 — `scripts/wiring_map.py`.** Resolves the EventBus emit↔subscribe edges blind
  to both CodeGraph and Grimp (joins by event-name string). `--check` gates only on
  catalogue drift (zero FP). Demoted "dead subscriber" to advisory after finding the
  governance `_emit_governance_event(event_name, …)` forwarder makes it FP-prone.
- **#574 — CodeGraph pin 3.10.0 → 3.11.2.** Validated a 3.11.2 build (31505 nodes,
  +25 receiver/inheritance edges) and **re-ran the reliability battery on a throwaway
  3.11.2 index** — `apply_operations`/`collect_setup_diagnostics` still `dead-unresolved`
  with module-qualified callers missed → the tiers hold byte-identical. (Runtime MCP
  version is env-managed; the repo only documents the pin.)
- **#575 — owner-memory capture (this).** Router **Q-0014** + CLAUDE.md + working-profile.

## Owner decisions captured (Q-0014)

- **Branch identity is not significant** — ship in logical modular batches. The strict
  "develop only on branch X" rule is **session-prompt-template residue, not in the repo**
  (grep-confirmed). → CLAUDE.md session-workflow.
- **Tooling latitude + provenance** — download/try/adopt any *verifiable* package without
  asking, carrying why + date + "unverified: confirm a few times before trusting." Keep
  dev-deps lazy+`importorskip`, pin runtime-deps. → CLAUDE.md Tooling bullet (relaxed the
  old "custom over deps / ask first," which the new rule contradicted).
- **Goal-approval = path-approval** — execute an unstated prerequisite to an approved goal
  (don't refuse on a missing-step technicality); take a better path than stated and say
  why; bound by output staying structured + matching intent. → CLAUDE.md Working agreement.

## Gates

- #572/#574/#575 docs-only (CI fast-green); #573 dev tooling — `check_quality --full`
  green, `check_architecture` exit 0.

## Context delta

- **Needed but not pointed to:** that the *strict branch rule isn't in the repo* — it
  comes from the session-prompt template. It cost a branch-tangle (#573 first carried a
  duplicate CLAUDE.md commit; rebuilt as main + the wiring commit and force-pushed). Now
  documented in CLAUDE.md + working-profile so the next session doesn't treat it as binding.
- **Pointed to but didn't need:** nothing major this arc.
- **Discovered by hand:** (1) the **bare-token rule** — CodeGraph resolves a call edge
  only for bare-name `foo()`, not `module.foo()`/indirect; this is the real predictor of
  its ~20% caller coverage, sharper than "~half invisible." (2) Multi-chat **doc collision
  is live** — a parallel chat shipped `agent-workflow-spec.md` + router Q-0013 + moved
  `main` mid-session; CLAUDE.md already has `<!-- READ_FIRST/SESSION_WORKFLOW/CODEGRAPH/
  ARCH_RULES -->` section markers that look like the right primitive for section-scoped
  ownership if made deliberate.

## Next

The reliability tiers + `wiring_map.py` are new tools — per Q-0014 they start **unverified**;
confirm their output across a few sessions before fully trusting. PR13 (role templates)
remains the next server-management implementation step.
