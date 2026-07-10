# Owner-facing documentation

> **Status:** `reference` — maintainer-facing guidance, not an implementation plan.

Use [`maintainer-question-router.md`](./maintainer-question-router.md) as the main
entry point for unresolved agent questions, maintainer explanations, reusable owner
intent, and routing answered conclusions to their correct long-term documentation
home.

Three companion docs capture the pipeline in increasing depth:

- [`maintainer-working-profile.md`](./maintainer-working-profile.md) — the maintainer's
  working style, strengths, friction points, and idea-flow shape (`owner-guidance`).
- [`ai-project-workflow.md`](./ai-project-workflow.md) — the multi-agent pipeline:
  per-project roles, handoff templates, idea-state vocabulary, and failure modes
  (`reference`).
- [`agent-workflow-spec.md`](./agent-workflow-spec.md) — the operational spec for each
  stage (Analysis, Decisions, Revision, Prompt Forge, Executor): what to do, what not to
  do, and what the output should look like (`reference`).
- [`gpt-5-6-sol-codex-eval-2026-07-10.md`](./gpt-5-6-sol-codex-eval-2026-07-10.md) —
  GPT-5.6 Sol launch-week research brief + the copy-paste Codex eval-prompt suite for
  deciding what role it earns in the cross-agent pipeline; §8 records the scored
  2026-07-10 run (`reference`).
- [`cross-agent-trust-ledger.md`](./cross-agent-trust-ledger.md) — per-model
  capability/trust scores from eval runs; trust decides the lane (`living-ledger`).

`docs/owner/` does **not** replace active plans, `docs/current-state.md`, binding
contracts or decisions, subsystem folios, the session journal, or brainstorms.
Unanswered questions are not approval. Owner questions become ideas only when they
are explicitly captured in `docs/ideas/` through its normal capture path.
