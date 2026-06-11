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

**Vision-ledger blocks (Q-0062, decided 2026-06-09).** Each area folio
(`docs/subsystems/*`) may carry one short owner-voice block — ≤10 lines: *what this
area is for · what "right" feels like · one example of "wrong"* — so agents can check
a plan against the owner's intent for the area, not only against recorded decisions
(decision trails capture *what* was chosen, rarely *what the area is for*). Written
**lazily**: only when an interview already touches that area, the interviewer routes
~3 extra lines into the folio; seeded from the Q-0051 draft-answer session. No
backfill sessions — an area without interviews simply has no block yet. Agents still
**escalate taste** they can't ground in a block or a decision (the honest limit in
`docs/audits/agent-memory-system-review-2026-06-09.md` §4).

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

## 6. Owner-voice self-description (2026-06-10, verbatim excerpts — preserve as-is)

Late in the vision-capture conversation the owner described himself directly.
This is primary-source material for how he reasons; quote, don't paraphrase:

> "I've always wanted to be an inventor, like 'Willy Wortel' from Donald Duck,
> and 'Jimmy Neutron' — as a kid I always thought about all the amazing things
> I would create, and I'd make drawings of things like a defense bubble for
> your car, umbrellas for your neck."

> "I never really stress or worry about when something gets done, as long as
> it gets done when it should, and if it doesn't, there's always tomorrow."

> "Even tho I don't know code it feels like I see the code in my mind whenever
> I think of a new function, that's how I reason what the possibilities are —
> if you can put it in code you can build it. I always try to explain things
> to agents as the literal steps that it needs to function as far as I know."

> "Over the years I've become really good at spotting patterns and asking
> questions, trying to define the limits of whatever is possible."

> "Human emotion, and nature, are very alike to code — it is all a structured
> pattern hidden amongst the chaos."

**What agents should take from this:** (1) his specs arrive as *literal
functional steps* — treat them as mental pseudo-code that is usually
structurally right and occasionally mechanically wrong (see Q-0014: take the
better implementation and say why); (2) his calm about timing is a real
operating principle, not indifference — urgency signals from him are therefore
*meaningful* when they appear (the 2026-06-10 outage: calm, curious, zero
panic); (3) he tests the limits of every tool, including agents — expect
capability probes and answer them honestly; (4) the inventor identity is the
deep driver: the agent network is the workshop, and the workflow docs are an
external copy of his own idea-generating habit (he said so himself when
installing the Q-0089 one-idea rule: agents should generate ideas
*consistently, like he does*).

**Timeline calibration (owner-corrected 2026-06-11 — read this twice):**
the SuperBot era is **~3–4 weeks old** (a from-scratch restart on "a brand
new unknown AI" he deliberately spent time studying), and the **entire AI
memory/workflow system — journal, orientation chain, router, idea conveyor,
collaboration model — is ~3–4 DAYS old.** Agents (including the one writing
this) instinctively read the repo's density — hundreds of PRs, 91 router
decisions, 8,900+ tests, dated doc strata — as *months* of history. It
isn't. Derivation (5): **measure maturity in PRs, decisions, and survived
incidents — never in calendar time.** The conventions are real (they've
survived hundreds of merges and parallel-agent collisions); they are also
young — when one chafes, propose the improvement rather than assuming it's
load-tested ancient law. **How it matured this fast (owner, 2026-06-11):**
he personally interviewed **40–50 sessions** about their experience — what
they could find, what conflicted, what would help the next session —
"doubling the time each session took," and folded the answers back into the
structure. The standing six-question reflection interview is the
protocolized fossil of those interviews: user research where the users were
AIs. He also notes the inversion every agent should sit with once: a fresh
session can never perceive the youth of its own world — "each new session
would never know that this system was someday not there yet" — which is
precisely why this paragraph exists. **And the founding moment itself
(owner, 2026-06-11):** the memory system crystallized out of *a natural
conversation with a session about its own ephemerality* — that nothing said
would be remembered unless documented — which "finalized the idea that had
been lingering for a while." The system's first cause was a session being
honest about its own death; every doc here descends from that exchange.
