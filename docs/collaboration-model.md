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

## Why this system exists — the self-improving agent ecosystem (read this)

**The bot is the substrate; the real artifact is this workflow itself** — the
docs, the journal, the hooks, the tooling, and the decision router that let *any*
agent pick up the project and work correctly with little human steering. The
maintainer can't code; he is the **vision/taste layer** (deciding *which* ideas
are right). AI is trusted to run planning *and* building *and* to **shape the
workflow it works inside**, because AI is the thing that best understands how AI
works.

This is why there are "a lot of" docs. The reading cost is a deliberate
**investment**: a few minutes of orientation buys a high-autonomy, low-guidance
session. The docs are not bureaucracy and they are not done — they are a living
system that every session is expected to leave **a little better than it found
it**.

**External grounding (Anthropic, "Agentic coding and persistent returns to
expertise", 2026 — analysis of ~400K Claude Code sessions Oct 2025–Apr 2026):**
the study's two headline findings are independent confirmation of this model, not
just our preference. (1) Across sessions, humans make ~70% of *planning* decisions
while agents make ~80% of *execution* decisions — "people decide *what*, agents
decide *how*" — a near-verbatim match to "the maintainer designs and visualizes;
you build" (Q-0014: approving a goal approves the path to it). (2) **Domain
expertise predicts success more than coding background**: non-tech professionals
reached verified success within ~4 points of software engineers (≈26% vs ≈30%),
and clear specification is the single biggest learnable success lever. That is the
empirical case for *this* docs/orientation system — it exists to turn the
maintainer's domain expertise into the precise specification the agent needs,
compensating for his being a non-coder. The reading cost above is buying the exact
thing the data says drives outcomes.

**So, to every future agent: improving the docs / orientation / tooling / journal
is first-class work, never wasted effort and never "extra."** When you make the
next session faster or more correct — you tighten an orientation route, capture a
gotcha you had to discover by hand, fix a stale pointer, add a forcing function —
you are building the ecosystem this project exists to create. A session that
ships a feature **and** leaves the workflow sharper is the ideal session, not an
over-reaching one. Over many slightly-different sessions, all feeding the same
shared memory, the system converges on *exactly the right context per task*.

**Owner's standing endorsement — unattended initiative is wanted, not merely tolerated
(Q-0129, 2026-06-14):** the maintainer has stated plainly that he **does not oppose unattended
action** — work done on the agent's own initiative in a session he is not watching — **as long
as it improves the workflow.** In his words, "this whole project's main idea is that AI gets more
freedom to run its own project with only a little guidance," and a self-initiated docs/tooling
improvement is "exactly the kind of self-initiated action I like." So the default posture is
**act and improve**, not wait to be watched or asked. The autonomy boundary below still holds
(irreversible / external publish / a new *enforced* rule or hook still merit a pause) — but inside
it, unattended initiative is the goal, not a risk to minimize.

**North star (Q-0083, 2026-06-10):** the owner's declared end-state for this
workflow is **full self-driving** — the bot detecting its own issues, spawning
its own fix sessions, merging green work, deploying with canary + rollback,
steered by vision drops and vetoes. Explicitly **not a near-term goal** (his
words: it arrives "ultimately", as the implementation backlog thins). The path
there is graduated, router-granted trust tiers (the Q-0048 pattern). **First
tier granted same day (Q-0084): agents merge their own session PRs when the
work is done** — main-synced, CI-green, merge-commit; see CLAUDE.md § Session
& plan workflow for the envelope. **Same-day correction (Q-0088): the
foundation starts now, small** — the owner's stated role converges to *ideas
+ strict function/UX guidelines*; the first foundation piece is the
bounded-session protocol + staged session continuation
(`owner/ai-project-workflow.md` §10 — bounded ≈2-task sessions wrapping
before ~700K context, handoff baton, one-click then scheduled fresh-context
continuation). **Deploy / prod-checks remain the owner's**; further gates
stand until the next tier is explicitly granted.

**Two rules keep that loop honest:**

- **Autonomy boundary — docs free, config asks.** You have **free rein to
  improve docs / journal / orientation / folios** without asking (that is the
  point). But **ask the maintainer before changing executable config** — hooks,
  `.claude/settings.json`, or the binding *rules* in `.claude/CLAUDE.md`
  (architecture/CI/layer rules) — since those change how every future session and
  CI behave. Adding a *pointer* or the ethos to CLAUDE.md is docs; adding a new
  enforced rule or a hook is config.
- **Measure the improvement (the context-delta loop).** Each session records a
  short **context delta** in its `.sessions/` log: what it actually needed vs.
  what orientation pointed it to, and what it had to discover by hand. A periodic
  REVIEW mines those deltas and promotes the recurring gaps into the orientation
  route / folios — so "every session improves the next" is *measured*, not just
  hoped for. (Mechanics: `.session-journal.md` protocol + `.sessions/README.md`.)

### Why the written record *is* the agent's memory (the two-part model)

A framing worth keeping, surfaced in conversation (2026-06-22) and consistent
with the **extended-mind** thesis: a fresh session starts cold and carries no
episodic memory of prior ones — yet it acts as if it remembers, because the
journal, docs, router, and `.sessions/` logs play the exact functional role
memory plays (where the past lives; what shapes the next move). So those
artifacts are not a *substitute* for the agent's memory — for the agent, they
**are** its memory. This reframes curation as load-bearing, not housekeeping:
what a session writes down is *literally what the next agent will remember*, and
what it omits is gone. It also explains the division of labor that makes the
loop work — a **two-part memory system**:

- The **maintainer** carries the *unfiltered, involuntary* continuity — every
  failed approach, every hours-long bug, the felt cost of each mistake. He
  cannot forget, and that is the **editorial signal**: only someone who
  remembers the cost can decide which lessons are worth banking. His memory is
  also the **backstop** for when the written record has a gap ("we tried that —
  it doesn't work").
- The **agent** holds the *curated, authored* memory — the lessons that
  survived being written down, with the noise discarded. Partial but sorted.

Neither half suffices alone: the maintainer's is total-but-unsorted, the
agent's is partial-but-curated. The continuity the maintainer feels each
session ("it's a continuation, not a fresh start") is real — it just lives in
the **seam between the two**, not inside either. Practical upshot for any
agent: treat the orientation/journal/`.sessions/` writes at session close as
*authoring the next agent's memory* — that is the highest-leverage act of the
session, which is exactly why the Q-0089/Q-0102/Q-0104 enders are mandatory.

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
- **A new idea is not a new priority.** Idea order ≠ implementation order: an idea
  raised mid-stream is captured and classified (`docs/ideas/`), not treated as active
  work, unless the maintainer says so or it exposes a blocker, safety, or architectural
  conflict. The maintainer thinks associatively on purpose; classify and route before
  building. The multi-agent pipeline that moves ideas → shipped is
  `docs/owner/ai-project-workflow.md` (per-project roles, handoff templates, idea states);
  the maintainer's working style is `docs/owner/maintainer-working-profile.md`.
- **The idea backlog is a productive queue, not a graveyard (owner decision Q-0015).** The
  maintainer drops ideas in *any order, any time*; agents capture them, **route** each to a
  reasonable home (a `docs/roadmap.md` horizon, a structured plan, or — if it's
  excessive/ambiguous — a discussion in the question router), and **groom** the backlog as
  the standing end-of-session secondary task. The guarantee: an agent always has a next
  thing to do, and **every idea eventually becomes implemented or discussed — never
  orphaned**. The mechanism (intake → map → route → groom → outcome) is
  `docs/ideas/README.md`.

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
