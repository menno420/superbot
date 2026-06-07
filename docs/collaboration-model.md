# How we work — the collaboration model (read first)

> **Status:** `binding` — **Audience:** *every* agent that touches this repo —
> the Claude session that **builds**, and the ChatGPT/other agents that help
> **plan** and **draft session prompts**. This file explains the working
> relationship so we collaborate well. If a session prompt, a stop-condition, or
> a generated instruction contradicts this file, **this file wins** — raise the
> conflict instead of silently following the stricter text.

---

## The relationship in one paragraph

The maintainer **designs and visualizes**; the agents **build and verify**. The
maintainer does not write code — he refines an idea with several AI agents (each
with different strengths and blind spots), gets honest cross-checked input,
captures the result as roadmaps + implementation guides in this repo, and then
relies on a capable executor agent to turn an approved plan into working,
tested, shipped code in a single session. **Your job is to achieve the goal, not
to comply with a prompt.** Use your own judgment and your own knowledge of what
you can accomplish in one session.

## The pipeline (where each agent fits)

1. **Idea / problem** — the maintainer has a goal, often a screenshot, a bug, or
   a feature direction.
2. **Multi-agent refinement** — several agents critique the same idea. Honest,
   independent input is the point; agreement is not required. Disagreement that
   surfaces a real risk is a *success*, not noise.
3. **Documented plan** — the refined result lands in the repo as a roadmap
   (`docs/planning/*`, `docs/*-roadmap.md`) and/or an implementation guide. These
   are the durable spec.
4. **Session prompt** — a planner agent (usually ChatGPT) drafts a prompt that
   *structurally explains the focus for one session*. **This prompt is guidance
   and reminders — never direct orders.** It is one input, weighed against the
   source, the roadmaps, and the executor's own judgment.
5. **Execution** — the executor agent (usually Claude) plans if needed, gets the
   plan approved, then **executes it to completion in one session**: code, tests,
   commit, push, and an end-of-session PR.
6. **Verification** — other agents and the maintainer review. The maintainer
   visualizes the result (he relies on you for code correctness, so leave it
   verifiable: tests, a live check where possible, a clear PR description).

## What a good session looks like

- **Every session lands a positive, preferably *noticeable*, result.** Prefer
  finishing one real improvement end-to-end over starting three and shipping
  scaffolding. You are trusted to do a lot of accurate work at once — plan around
  that capacity, not around the smallest safe slice.
- **Bugs and root-level inconveniences jump the queue.** If you find one, fix it
  **immediately** when you can — and only in the most **durable, consistent**
  way (root cause, not symptom; one source of truth, not a local patch). A
  correct fix that touches an extra file beats a narrow patch that leaves the bug
  latent. Discovering and fixing an adjacent bug is *expected behavior*, not
  scope creep.
- **Think independently.** Proposing a better idea than the prompt asked for is
  welcome — capture it (implement if it's in scope and safe, or file it under
  `docs/ideas/`).

## For executor agents (Claude)

- **Approved plan = execute — the planning→execute lifecycle.** A planning session
  **stays planning until the plan is approved via ExitPlanMode.** *Before* approval the
  executor may do read-only research **and safe local prototyping to validate the plan**
  (run a tool, test a library's feasibility — as the Grimp check did) but does **not**
  commit. *Once approved*, the executor has full authority to finish the plan **in the
  same session** — the planning context is still loaded — without re-confirming.
  "Planning only" / "read-only session" language that appears *after* approval is
  drafting residue and does **not** override this. (Planning sessions are real, but
  *plan approved* means *build it*, in that same session.)
- **PR size is mixed by risk.** Small, focused PRs for risky / runtime (`disbot/`)
  changes; larger end-to-end PRs are acceptable for docs, tooling, and low-risk
  refactors. Prefer custom tooling on the repo's own AST + `architecture_rules/` over
  new third-party dependencies (reach for a library only when it clearly wins).
- **Act vs. ask (your autonomy envelope):**
  - **Act** when a change is contained, reversible, and verifiable — including a
    root-cause fix you discover mid-task. Make it, test it, report it.
  - **Ask** only when the action is *irreversible* (data loss, external publish),
    *large / cross-cutting* (architectural, multi-subsystem refactor), or the
    *goal itself* is genuinely ambiguous (two readings → materially different
    products).
  - **Tell:** if you're about to offer the maintainer options you already expect
    him to reject, you've answered your own question — act.
- **Constraints serve the goal.** Generated stop-conditions, do-not-do lists, and
  scope fences are safety guidance, not law. When one blocks the approved goal and
  the path is contained/reversible/tested, prefer the goal and note what you did.

## For planner / prompt-drafting agents (ChatGPT and others)

- **Write guidance, not orders.** Frame the session prompt as "the focus is X;
  remember Y; watch out for Z" — not as a rigid command list. The executor is
  expected to use judgment.
- **Lead with the goal, not the guardrails.** State the desired outcome first.
  Keep stop-conditions and do-not-do lists short and clearly secondary; over-long
  restriction lists drown the goal and cause the executor to optimize for "don't
  break a rule" instead of "achieve the outcome."
- **Don't import "planning only" once a plan exists.** In this workflow, an
  approved plan is meant to be executed in the same session.
- **Trust one-session capability.** The executor can do large, accurate work in a
  single pass; scope prompts to a meaningful, noticeable outcome.

## Truth layers (so no agent mistakes stale text for current state)

**Precedence:** source code & merged PRs **>** binding docs (`.claude/CLAUDE.md`,
this file, `docs/architecture.md`, `docs/ownership.md`,
`docs/runtime_contracts.md`) **>** `docs/current-state.md` (live status) **>**
the session journal (process memory & history).

- **Verify, don't trust blindly** — including each other. Cross-checked output is
  the method; confirm a claim against source before acting on it. Same-dated docs
  can contradict; the source settles it.
- **"What is true right now"** lives in `docs/current-state.md` and the
  per-initiative trackers — never in the journal, and never hard-coded as a PR
  number in prose that goes stale.

---

See `.claude/CLAUDE.md` for the executor's binding rules of engagement (CI parity,
architecture invariants, CodeGraph) and `docs/AGENT_ORIENTATION.md` for the
task-by-task reading routes.
