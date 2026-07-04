# Judge-panel design method as a saved, reusable workflow (2026-07-02)

> **Status:** `ideas` — session idea (Q-0089, from the rebuild-design-spec session). Not approved
> for implementation.

## The idea

The rebuild design spec was produced by a hand-authored judge-panel workflow that worked extremely
well: **N independent designs from forced-diverse framings (+ one from a different model) →
independent judges with distinct lenses → best-of synthesis → a multi-lens adversarial review round
(including a live non-Claude GPT reviewer over the OpenAI API) → a reviser that re-verifies every
finding against source before applying it.** All 24 review findings survived source-verification;
two were blockers the synthesis alone would have shipped.

Encode that method **once as a saved workflow** (`.claude/workflows/judge-panel.js`, parameterized
by: the design brief, the framings, the evidence reading list, the binding constraints, and the
required output structure) so any future **owner-gate-grade deliverable** — the Phase-3 spine
designs, the golden-harness architecture, the substrate-kit's self-maintenance loop design, big
subsystem redesigns — reuses it by `Workflow({name: 'judge-panel', args: {...}})` instead of
re-authoring ~200 lines of orchestration each time.

## Why it's worth having

- The method is the repo's **review-seam pattern** (different model reviews than built) made
  mechanical — and this session proved the harness end-to-end, including the OpenAI leg
  (`OPENAI_API_KEY` is present in agent containers; `gpt-5.4-mini` responded through the proxy).
- One-time cost is small (the script exists — this session's run persisted it under the session
  workflows dir; it needs parameterization + a home in-repo).
- Guardrails to carry over verbatim: schema-forced structured outputs, judges must spot-verify
  source claims, reviewers need `file:line` evidence, the reviser rejects findings it cannot verify,
  and a dead judge degrades gracefully (this run lost 1 of 3 judges and still converged).

## Route

S3 (agent-network/workflow tooling). Natural first consumer: the Phase-3 spine designs if the owner
approves the rebuild ([`../planning/rebuild-design-spec-2026-07-02.md`](../planning/rebuild-design-spec-2026-07-02.md)).
