# Maintainer Question Router

> **Status:** `reference` — owner-facing guidance and question router.
>
> **Audience:** maintainer first, agents second.
>
> **Purpose:** collect agent questions, preserve maintainer answers, and route
> answered owner intent to the correct documentation home.
>
> **Not a roadmap:** unanswered questions are not approval. Answered questions that
> affect code, architecture, priorities, or product behavior still need the normal
> decision/planning/promotion path before implementation.

## 1. What this file is for

Use this file when an agent needs the maintainer's intent to avoid guessing. Questions
may cover product vision, priority, user experience, architecture, safety, workflow,
or clarification of an earlier answer.

It gives the maintainer one place to answer at their own pace. It also supports a
dedicated Claude/Opus-style session that prepares a small batch of plain-language,
multiple-choice questions for quick answers.

Maintainer answers are **leading owner intent by default**. Agents must preserve the
original answer, use it faithfully, and route durable conclusions to their proper
home.

## 2. What this file is not

This file is not:

- an implementation plan, roadmap, active queue, or approval to change code;
- an ADR, architecture contract, ownership map, runtime contract, or current-state
  ledger;
- a replacement for `.claude/CLAUDE.md`, `.session-journal.md`, subsystem folios,
  `docs/planning/`, `docs/decisions/`, or `docs/ideas/`;
- a bypass around server-management sequencing, AI/BTD6 gates, privacy review,
  security review, or any other binding decision;
- a place to silently convert unanswered questions into assumed approval.

Source code and merged PRs win where they describe shipped behavior. Binding docs and
active trackers keep their existing authority. This router preserves and routes owner
intent; it does not override those sources by itself.

## 3. Maintainer preferences

- Prefer clear explanations before coding jargon.
- Preserve the maintainer's product vision, not only a technically convenient
  implementation.
- Ask when owner intent is genuinely unclear instead of guessing at product intent.
- Continue safe, reversible, source-verified work when possible, but do not decide
  unresolved product, safety, privacy, or architecture questions on the maintainer's
  behalf.
- Agents may challenge an answer that is impossible, unsafe, inefficient, too costly,
  or conflicts with architecture or binding decisions, but must explain why in plain
  language and offer a safer alternative.
- Prefer safe, modular, observable, service-owned changes over broad rewrites or
  duplicate systems.
- Keep AI, automation, BTD6 expansion, privacy-sensitive features, and
  server-management changes behind their documented gates.

## 4. How agents should use this file

1. Check authoritative source and the correct existing documentation home before
   asking; do not ask the maintainer to resolve a question the repo already answers.
2. Add a focused question only when the answer materially affects product intent,
   safety, architecture, priority, or an irreversible/expensive choice.
3. Write in plain language, explain why the answer matters, and give a safe default.
4. Do not bundle unrelated decisions or steer the maintainer toward a preferred answer
   without saying why it is preferred.
5. Preserve the maintainer's original answer block exactly. Agents may add a concise
   interpretation below it, but must not silently ignore, rewrite, or reinterpret it.
6. Route or copy the durable conclusion to the correct home, then record the routing
   result here. Do not dump whole conversations into multiple docs.
7. If the answer cannot safely be followed, use the reproposal rule in §8.

Unanswered questions are **not approval**. Their safe defaults describe what agents
should do while waiting; they do not promote work into an active plan.

## 5. How the maintainer can answer

The maintainer may:

- answer directly inside the preserved answer block;
- choose an option and add a short reason;
- say “defer” or “not sure yet” without approving anything;
- identify something agents keep misunderstanding;
- ask for a clearer explanation or safer alternative;
- answer several small questions in a dedicated multiple-choice session.

Short answers are valid. Agents are responsible for making the question understandable
and routing the conclusion, not for making the maintainer write technical documents.

## 6. Question lifecycle

Use one of these statuses:

| Status | Meaning |
|---|---|
| **Inbox** | Captured but not yet prepared for the maintainer. |
| **Awaiting maintainer answer** | Ready for the maintainer; no answer yet. |
| **Answered in chat — needs repo update** | The maintainer answered outside this file; preserve the answer here before routing. |
| **Answered — needs routing** | Answer is preserved here but its durable conclusion has not reached the correct home. |
| **Routed** | The concise conclusion is linked/copied to the correct authoritative or reference home. |
| **Kept here as general guidance** | The answer is reusable owner intent and has no better home. |
| **Needs follow-up** | The answer exposes another material question or unresolved conflict. |
| **Superseded** | A later maintainer answer or authoritative decision replaced it; link the replacement. |

Optional priority values are **Low**, **Medium**, **High**, and **Blocking**. “Blocking”
means a specific decision cannot safely continue; it does not make the question an
approved implementation priority.

## 7. Routing destinations

After an answer, copy or link only the concise durable conclusion to the correct home:

| Destination | What belongs there |
|---|---|
| `.claude/CLAUDE.md` | Binding agent workflow or session behavior. |
| `.session-journal.md` | Operational/session gotchas and short-lived working memory. |
| `docs/current-state.md` | Active project status only, when truly current-state relevant. |
| `docs/architecture.md` | Broad system design constraints. |
| `docs/ownership.md` | Ownership boundaries and mutation authority. |
| `docs/runtime_contracts.md` | Runtime guarantees, lifecycle behavior, and failure semantics. |
| `docs/decisions/` | Binding technical decisions or ADR-like outcomes. |
| `docs/planning/` | Approved implementation plans; an answer alone does not create approval. |
| `docs/subsystems/<area>.md` | Area-specific durable guidance and links. |
| `docs/ideas/` | Explicit brainstorms and unapproved future ideas. |
| **Keep here** | General owner intent or reusable clarification with no better home. |

Preserve the original maintainer answer here even after routing. Link to the destination
and record what was copied; do not move the only copy or repeat the full conversation
across the repo.

## 8. Reproposal rule

Maintainer answers are leading owner intent. Agents should follow them unless the
answer is impossible, unsafe, inefficient, too costly, or conflicts with existing
architecture or binding decisions.

If an agent believes a maintainer answer should not be followed, the agent must:

1. summarize the maintainer answer fairly;
2. explain the problem in plain language;
3. name the conflicting source, constraint, or risk;
4. propose at least one safer alternative;
5. ask the maintainer to confirm the revised direction before treating it as settled.

Do not blindly implement the original answer, and do not silently substitute the
agent's alternative.

## 9. Question block template

Copy this block into the Question inbox or the appropriate lifecycle section:

`````markdown
## Q-0001 — <short question title>

**Asked by:** <agent/session if known>
**Date:** YYYY-MM-DD
**Area:** AI / BTD6 / Server management / Docs / Workflow / General
**Type:** Vision / Priority / UX / Architecture / Safety / Workflow / Other
**Priority:** Low / Medium / High / Blocking
**Status:** Awaiting maintainer answer
**Suggested destination after answer:** CLAUDE.md / architecture / current-state / session-journal / planning / decisions / subsystem folio / ideas / keep here

### Question

<Plain-language question>

### Why agents need this

<What this answer affects>

### Options, if useful

A. ...
B. ...
C. ...
D. Defer / not sure yet

### Safe default until answered

<What agents should assume for now>

### Maintainer answer

```text
Answer:

Reason:

Anything agents keep misunderstanding:

Keep open for later:
```

### Agent interpretation, if needed

```text
Do not rewrite the maintainer answer. Add a concise interpretation here only if useful.
```

### Routing result

```text
Destination:
Moved/copied on:
Notes:
```
`````

## 10. Multiple-choice batch format

When many small maintainer decisions are needed, agents may prepare a batch of short
multiple-choice questions.

Each question should:

- avoid jargon;
- explain why it matters in one sentence;
- provide 2–4 clear options;
- include a safe default;
- avoid bundling unrelated decisions together;
- avoid treating unanswered choices as approval.

Keep batches small enough to answer without a long research session. Route each answer
individually when the destinations differ.

### Batch question example

**Q:** Should coding sessions prefer many small PRs or fewer longer PRs?

**Why it matters:** This affects review size, context switching, and how quickly
features land.

**Options:**

A. Prefer small focused PRs.
B. Prefer longer sessions that finish a whole feature.
C. Use small PRs for risky areas and longer PRs for docs/simple work.
D. Decide case by case.

**Safe default:** C.

## 11. Question inbox

The starter questions below are deliberately **unanswered**. Recommended directions
help the maintainer understand the trade-off; they are not approval.

### Q-0001 — Should AI stay explanation-only, or eventually help prepare actions?

**Area:** AI / Server management
**Type:** Vision / Safety
**Priority:** High
**Status:** Awaiting maintainer answer
**Suggested destination after answer:** decisions / AI folio / ideas

**Question:** Should AI permanently stay read-only and explanation-only, or could it
eventually prepare a preview that a human confirms through the normal service-owned
action path?

**Why agents need this:** The answer shapes long-term AI product direction, but cannot
bypass AI-readiness, authority, confirmation, audit, or rollback gates.

**Options:** A. Explanation-only. B. Explanation-only now; maybe prepare previews
later. C. Eventually allow broader actions after dedicated decisions. D. Defer.

**Safe default:** A — AI stays read-only/explanation-only.
**Recommended direction:** A now; reconsider preview → confirm → apply → audit only
after the documented gates and a dedicated decision.

### Q-0002 — Should the owner-facing control center stay Discord-first?

**Area:** Server management / Product
**Type:** Vision / UX
**Priority:** Medium
**Status:** Awaiting maintainer answer
**Suggested destination after answer:** server-management folio / ideas / decisions

**Question:** Should Discord panels remain the primary owner experience even if a web
companion becomes possible later?

**Why agents need this:** The answer affects long-term information architecture and
whether future surfaces must reuse Discord-first services and read models.

**Options:** A. Discord only. B. Discord-first, with a later reusable web companion.
C. Web-first eventually. D. Defer.

**Safe default / recommended direction:** B — Discord remains primary, services stay
reusable, and no web dashboard is started yet.

### Q-0003 — How should agents handle unclear maintainer vision?

**Area:** Workflow / General
**Type:** Workflow / Safety
**Priority:** High
**Status:** Awaiting maintainer answer
**Suggested destination after answer:** CLAUDE.md / keep here

**Question:** When the desired product outcome is unclear, which work should agents
continue and which decisions should wait for the maintainer?

**Why agents need this:** This balances progress against the risk of guessing the
maintainer's product, safety, privacy, or architecture intent.

**Options:** A. Stop all work. B. Continue safe/reversible work but pause material
product, safety, privacy, and architecture decisions. C. Let agents infer everything.
D. Decide case by case.

**Safe default / recommended direction:** B — continue safe, reversible work; add a
question and block only the material unresolved decision.

### Q-0004 — Should answered maintainer questions be copied or moved?

**Area:** Docs / Workflow
**Type:** Workflow
**Priority:** Medium
**Status:** Awaiting maintainer answer
**Suggested destination after answer:** keep here / CLAUDE.md

**Question:** After an answer belongs in another doc, should the original answer stay
here?

**Why agents need this:** Preserving the original prevents later summaries from
silently changing owner intent while still respecting one-fact-one-home.

**Options:** A. Preserve the original here and copy/link a concise conclusion. B. Move
the original entirely. C. Leave everything here only. D. Defer.

**Safe default / recommended direction:** A.

### Q-0005 — How should agents challenge inefficient or impossible answers?

**Area:** Workflow / General
**Type:** Safety / Workflow
**Priority:** High
**Status:** Awaiting maintainer answer
**Suggested destination after answer:** CLAUDE.md / keep here

**Question:** What should an agent do when the maintainer's requested direction cannot
safely or realistically be followed?

**Why agents need this:** Blind implementation can create safety, cost, architecture,
or reliability problems; silent substitution loses owner control.

**Options:** A. Implement it anyway. B. Silently choose another approach. C. Explain
the conflict plainly, cite it, propose safer alternatives, and ask for confirmation.
D. Defer without explanation.

**Safe default / recommended direction:** C.

## 12. Answered but not yet routed

No entries yet. Preserve answers here before adding an agent interpretation or routing
summary.

## 13. Routed answers

No entries yet. A routed entry should retain the original answer block and link the
concise conclusion's destination.

## 14. General owner intent that should stay here

The maintainer has explicitly established these rules for this router:

- Maintainer answers are leading owner intent by default.
- Agents must preserve original answer blocks and must not silently ignore, rewrite,
  or reinterpret them.
- Unanswered questions are not approval.
- Agents route concise durable conclusions to the correct home while preserving the
  original answer here.
- Agents must explain and re-propose, rather than blindly implement, answers that are
  impossible, unsafe, inefficient, too costly, or conflict with binding decisions.
- This router is owner-facing guidance, not a planning system or gate bypass.

## 15. Related future questions / captures

These are **capture-only future ideas**, not questions answered by the maintainer and
not approved implementation work. If reviewed later, route them through
`docs/ideas/README.md` and preserve existing owners rather than creating parallel
systems.

| Capture | Future question | Existing systems/constraints to preserve |
|---|---|---|
| **Owner-question workflow follow-up** | After real usage, does this router need a smaller index, archive convention, or batch-answer guide? | Keep this docs-only unless a separately approved need proves otherwise; do not create a planning system. |
| **Source confidence field for readiness cards** | Should readiness facts expose owner/source, observed time, freshness, and confidence? | Extend typed health facts and `ReadinessSnapshot`; no second dashboard or monitor. |
| **Decision Preview Contract** | Should policy/config/provisioning previews share a reusable shape? | Reuse owning read models, capability checks, provisioning previews, and service-owned mutation paths. |
| **Read-only AI answer envelope** | Should AI explanations consistently show answer, evidence used, stale/missing facts, risk, manual next actions, and forbidden actions not taken? | Remain read-only and grounded behind AI-readiness/orchestration gates. |
| **Operator incident digest** | Should owners receive a startup/restart digest over existing health and log facts? | Owner-gated, read-only, privacy-safe, and built over existing diagnostics/logging facts. |
| **Fact ownership map before audit timeline** | Which domain owns every fact before a unified audit/event timeline read projection is considered? | Complete the ownership/redaction/retention map first; do not create another event or audit-write pipeline. |

## 16. Plain-language glossary

| Term | Plain-language meaning |
|---|---|
| **Owner intent** | What the maintainer wants the product or working process to achieve. |
| **Leading** | The default direction agents should follow unless a concrete conflict or risk requires reproposal. |
| **Safe default** | Temporary behavior while waiting for an answer; it is not approval. |
| **Route** | Copy or link a concise conclusion to the one doc that should own it. |
| **Binding decision** | A rule or decision agents must not override casually. |
| **Promotion** | The normal review path that turns an idea or answer into approved planned work. |
| **Reproposal** | A fair explanation of why the original answer cannot safely be followed, plus a safer alternative for maintainer confirmation. |
