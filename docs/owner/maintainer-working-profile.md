# Maintainer working profile

> **Status:** `owner-guidance` — maintainer-facing capture of working style and intent.
>
> **Purpose:** preserve *how the maintainer works* — strengths, friction points, and the
> shape of his idea flow — so agents keep his intent instead of reconstructing it from
> scattered chat. The reusable *multi-agent pipeline* (project roles, handoffs, idea
> states, failure modes) lives in [`ai-project-workflow.md`](./ai-project-workflow.md);
> this doc is only the person.
>
> **Not a roadmap, not binding behavior.** It explains intent; it does not approve work.
> The agent-behavior rules it implies are stated where agents actually read them — see §4.

## 1. Why this exists

The maintainer often explains the real shape of an idea through conversation, and the
useful context is spread across many messages: one gives the product feeling, another the
workflow problem, another a technical worry, another an owner preference. Apart they look
unrelated; together they describe the system being designed. This doc keeps that intent in
one owner-facing place so a future session does not have to re-derive it.

The practical upshot for agents is in §3–§4: **idea order is not implementation order.**

## 2. Working profile

The maintainer's strongest contribution is **product vision, honest feedback, and the
ability to describe intent through conversation.** He is good at:

- visualizing what SuperBot should become, and seeing how separate systems connect;
- noticing when the bot — or the agent process itself — feels wrong;
- explaining intent honestly instead of hiding uncertainty;
- generating many useful ideas quickly;
- recognizing when a tool, doc, or workflow would remove repeated friction;
- using the right agent for the job: Opus for high-context consolidation and final
  revision, Codex for focused execution once scope is clear, ChatGPT projects for idea
  shaping and decision framing.

It is harder for him to:

- keep ideas in strict implementation order;
- weigh several technical trade-offs at once, under pressure;
- track where every answer should live in the repo;
- read coding jargon quickly;
- tell at a glance whether a decision is architectural, workflow, product, or
  implementation-specific.

**Treat these as workflow design constraints, not weaknesses to correct.** The project
should support free idea generation *and* enforce deterministic routing before anything
becomes implementation work. That routing is the job of
[`ai-project-workflow.md`](./ai-project-workflow.md) and
[`maintainer-question-router.md`](./maintainer-question-router.md), so the maintainer does
not have to carry it.

**How he runs it day-to-day (observed 2026-06-08).** The maintainer runs **several chats in
parallel by default** — typically a Claude Code *implementation* chat, plus ChatGPT *projects*
per pipeline stage (`SuperBot Prompts` = Prompt Forge, `SuperBot Decisions`, `SuperBot
Revisions`), plus Discord for the live bot — and spins a **fresh chat per item/issue**. The
"AI does all the work" read is wrong: he spends the day planning and routing across these
chats; the agents execute. A chat often ends with a short Q&A like this one whose purpose is
to **turn session learnings into permanent memory** (route durable answers to the router +
their home doc). Practical consequence for agents: when you edit a binding/owner doc, assume
**another chat may be editing it concurrently** — prefer append-only / section-scoped edits,
take the next free `Q-00NN` number, and don't be surprised when `main` moved mid-session.

## 3. How ideas arrive: three different orders

The maintainer's idea flow is intentionally broad and associative — a feature idea leads
to a documentation gap, which surfaces an agent-workflow concern, which needs an owner
decision, which suggests a tooling idea, and so on. This is valuable: it exposes hidden
dependencies a narrow implementation-only session would miss.

So three orders must stay separate:

```text
idea order           = the order ideas appear in conversation
decision order       = the order unresolved choices should be answered
implementation order = the order accepted work is actually built
```

Agents must not collapse these into one sequence. The binding consequence — *a new idea is
not a new priority* — is stated where every agent reads it (see §4).

## 4. What this means for agents

This doc is intent, not enforcement. The rules it implies live in their proper homes:

- **New idea ≠ new priority; idea order ≠ implementation order** → binding in
  `.claude/CLAUDE.md` (Working agreement) and `docs/collaboration-model.md`.
- **How work flows across AI projects** (pipeline, handoffs, idea states, failure modes)
  → [`ai-project-workflow.md`](./ai-project-workflow.md).
- **When owner intent is unclear / preserving owner answers** →
  [`maintainer-question-router.md`](./maintainer-question-router.md).
- **The planning→execute lifecycle, act-vs-ask, bugs-first** → `docs/collaboration-model.md`
  and `.claude/CLAUDE.md` (don't restate them; follow them).

Two standing expectations the maintainer has stated:

- His answers are **leading owner intent** unless impossible, unsafe, inefficient, too
  costly, or in conflict with a binding decision — in which case explain, cite, propose a
  safer alternative, and confirm (the reproposal rule in the router).
- Agents should **think critically and infer related dependencies, risks, and missing
  questions** rather than follow a request mechanically when the surrounding context asks
  for a better adjacent change.

## 5. Non-goals

This doc should **not**:

- approve bot features, or turn raw idea order into implementation priority;
- become a second `current-state.md`, collaboration model, or question router;
- replace project-specific ChatGPT instructions;
- require every implementation agent to read a long personal profile by default.

Its only job is to preserve intent and point at the right homes.
