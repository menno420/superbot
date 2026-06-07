# Maintainer working profile and random-order idea intake

> **Status:** `owner-guidance` — maintainer-facing capture for planning workflow and owner intent.
>
> **Purpose:** capture the maintainer's working style, strengths, friction points, and preferred AI-assisted planning flow so future Opus / ChatGPT / Codex sessions can preserve intent instead of reconstructing it from scattered chat history.
>
> **Not a roadmap:** this document explains how ideas should be captured, clarified, routed, and promoted. It does not approve implementation work by itself.

## 1. Why this document exists

The maintainer often explains the real shape of an idea through conversation. Useful context can be spread across many messages: one message may explain the product feeling, another the workflow problem, another the technical concern, and another the owner preference. Taken separately, those messages can look unrelated; together, they describe the actual system being designed.

This document exists to preserve that context in one owner-facing place.

It should help agents understand that the maintainer may introduce ideas in a random order, not because the project direction is chaotic, but because the maintainer is actively exploring relationships between product vision, agent workflow, documentation, tooling, and implementation risk.

Agents should not treat idea order as implementation order.

## 2. Maintainer working profile

The maintainer's strongest contribution is product vision, honest feedback, and the ability to describe intent through conversation. The maintainer is good at:

- visualizing what SuperBot should become;
- seeing how separate systems could connect into a better workflow;
- identifying when the bot or the agent process feels wrong;
- explaining personal intent honestly instead of hiding uncertainty;
- generating many useful ideas quickly;
- recognizing when a tool, document, or workflow would reduce repeated friction;
- using Opus as a high-context final revision and consolidation pass;
- using Codex for focused execution after scope is clear;
- using ChatGPT projects for idea shaping, decision framing, and revision reports.

The maintainer may find it harder to:

- keep ideas in strict implementation order;
- decide multiple technical tradeoffs under pressure;
- track where every answer should live in the repo;
- understand all coding jargon immediately;
- notice which decisions are architectural, workflow, product, or implementation-specific;
- keep long planning conversations from scattering useful context across many messages;
- prevent agents from interpreting a raw idea as active implementation priority.

Agents should treat these not as weaknesses to correct, but as design constraints for the workflow. The project should support free idea generation while enforcing deterministic routing before implementation.

## 3. Core operating insight

The maintainer's idea flow is intentionally broad and associative:

```text
feature idea
→ documentation issue
→ agent workflow concern
→ owner decision
→ tooling idea
→ product direction
→ repo hygiene
→ implementation strategy
```

This is valuable. It reveals hidden dependencies that a narrower implementation-only session might miss.

The process should therefore separate three different orders:

```text
idea order           = the order ideas appear in conversation
decision order       = the order unresolved choices should be answered
implementation order = the order accepted work should actually be built
```

Agents must not collapse these into one sequence.

## 4. Random-order idea intake rule

The maintainer may introduce ideas in any order. A new idea is not automatically a priority change and does not interrupt active implementation unless the maintainer explicitly says so or the idea reveals a blocker, safety issue, architectural conflict, or serious misunderstanding.

Default handling:

```text
new idea
→ classify
→ capture or ask a question
→ route to the right home
→ promote only after decision / planning / verification
→ implement only after acceptance
```

Agents should respond to random-order ideas by classifying them, not by immediately turning them into implementation work.

## 5. Idea states

Use these states when processing new ideas:

| State | Meaning |
|---|---|
| `raw` | Mentioned in chat; not structured yet. |
| `captured` | Written down as an idea; not approved. |
| `needs-owner-answer` | Requires maintainer preference or clarification. |
| `needs-decision` | Requires tradeoff, priority, or scope selection. |
| `needs-repo-verification` | Cannot be judged without checking source, docs, or PRs. |
| `ready-for-planning` | Direction is clear enough for Opus planning. |
| `accepted-plan` | Maintainer accepted the plan. |
| `in-implementation` | Active implementation session or PR. |
| `shipped` | Merged and reflected in the correct docs. |
| `deferred` | Intentionally later. |
| `rejected` | Should not be re-proposed unless the governing decision changes. |
| `superseded` | Replaced by a newer idea, answer, or decision. |

## 6. Project pipeline

The maintainer's preferred AI-assisted pipeline is stage-based. Each project should know its role and should not try to own every stage.

```text
SuperBot Ideas project
→ SuperBot Decisions project
→ Opus planning / question batch
→ ChatGPT Revision project
→ Codex or Opus execution
→ PR review / routing / merge
```

### SuperBot Ideas project

Purpose: raw idea shaping and early feasibility.

This stage should:

- expand rough ideas;
- identify related systems;
- flag hidden dependencies and risks;
- preserve product vision;
- classify the idea's state;
- suggest whether the next stage is capture, decision, Opus planning, or defer.

This stage should not approve work, write final implementation plans, or tell Codex to implement.

### SuperBot Decisions project

Purpose: turn promising ideas into owner decisions and accepted direction.

This stage should:

- compare options;
- ask short multiple-choice questions;
- define safe defaults;
- identify non-goals;
- decide whether the idea should be deferred, captured, rejected, or sent to Opus planning.

This stage should not implement and should not skip repo verification when current implementation matters.

### Opus planning session

Purpose: high-context repo verification, planning, question batching, and optionally execution after acceptance.

This stage should:

- read the repo in layers;
- inspect open PRs;
- use the maintainer-question router when owner intent is unclear;
- use `scripts/context_map.py` for file-impact context when planning concrete file changes;
- ask multiple-choice questions when many owner decisions are needed;
- create the real structured implementation plan;
- execute in the same session only after maintainer acceptance.

Opus is especially valuable for broad context consolidation, documentation architecture, final revision, and large-but-coherent refactors.

### ChatGPT Revision project

Purpose: independent sanity check and risk review.

This stage should:

- verify grounding first;
- review plans or PRs against source, docs, open PRs, architecture, owner intent, and tests;
- identify required changes, optional improvements, user decisions, live verification needs, and unverified assumptions;
- avoid redesign unless explicitly asked.

The Revision project is the consistency / risk filter, not the idea generator.

### Codex execution

Purpose: focused implementation of accepted scope.

This stage should:

- execute a clear accepted plan;
- keep scope narrow;
- verify relevant files/docs first;
- run checks;
- open a PR;
- stop and ask if owner intent or repo state conflicts with the task.

## 7. Planning-to-execution rule

Planning remains planning until the maintainer accepts the plan.

After acceptance, Opus may execute the approved scope in the same session while the planning context is still loaded. This is the maintainer's preferred workflow for high-context work because it avoids losing the reasoning that produced the plan.

Before acceptance, agents may perform read-only research and safe prototyping where appropriate, but should not commit implementation changes or treat the plan as approved.

For risky, unclear, or broad runtime behavior changes, the agent should ask whether to split execution into a separate session.

## 8. Maintainer-question router relationship

The maintainer-question router is the durable intake and preservation layer for owner answers.

Use it when:

- an agent is unsure what the maintainer wants;
- an answer affects workflow, product direction, safety, privacy, architecture, or major implementation sequencing;
- a conversation produced a meaningful owner answer that could otherwise be lost;
- multiple-choice answers need to be preserved and routed.

The router should not become a planning system. It preserves original owner answers and routes concise conclusions to the correct home.

A useful answer flow is:

```text
question asked in Opus / ChatGPT
→ maintainer answers, often by multiple choice
→ original answer preserved in router
→ concise conclusion routed to CLAUDE.md / collaboration-model / folio / decisions / ideas / planning as appropriate
```

## 9. Multiple-choice question workflow

The maintainer prefers short multiple-choice questions when many small decisions are needed. This works because it reduces pressure and makes decisions easier to answer quickly.

Good multiple-choice questions:

- avoid jargon;
- explain why the answer matters;
- provide two to four real options;
- include a safe default;
- include a recommended direction only when the agent explains why;
- avoid bundling unrelated decisions;
- do not treat unanswered options as approval.

This is especially useful for:

- workflow preferences;
- PR size / session size;
- doc routing and archiving;
- whether a tool should be custom or third-party;
- whether a concept is future-only or ready for planning;
- AI action boundaries;
- Discord-first versus web-ready direction.

## 10. Documentation scale strategy

The repo may continue to grow, but the solution is not to remove useful docs. The solution is better routing, authority, and hygiene.

The preferred strategy is:

```text
stable truth lives in docs
current truth is routed by current-state
area truth starts at subsystem folios
owner intent starts at the maintainer-question router
file-impact context comes from context_map.py
old plans are marked historical or archived
new ideas are captured without interrupting active implementation
```

Agents should load context in layers, not read the entire docs tree by default.

The maintainer values documentation because it prevents repeated re-explanation, but wants the docs to remain navigable enough that agents do not lose confidence.

## 11. Context-map tooling intent

The context-map tool exists because agents need to answer:

```text
If I touch this file, what else is connected?
What docs should I read?
What tests should I run?
What ownership/risk rules apply?
```

This should reduce wrong assumptions in a growing repo.

Preferred tooling philosophy:

```text
custom SuperBot wrapper over useful existing engines
```

For example:

- Grimp can provide import-graph value;
- SuperBot's existing architecture rules provide ownership/layer meaning;
- override YAML provides curated docs/tests/risk routing;
- `context_map.py` converts those signals into agent-action guidance.

The tool should be practical, not exhaustive. It should make agents faster and safer without pretending to fully map runtime behavior.

## 12. Owner-intent principles established in conversation

These principles should guide future sessions:

- The maintainer's honesty and conversational explanations are a strength; agents should preserve that intent rather than over-technicalizing it.
- The maintainer may forget to mention some important constraints; agents should think critically and infer related dependencies, risks, and missing questions.
- Agents should not merely follow requests mechanically when the surrounding context suggests a better adjacent addition is needed.
- Maintainer answers are leading owner intent unless impossible, unsafe, inefficient, too costly, or conflicting with binding decisions.
- If an answer cannot safely be followed, agents must explain, cite, propose alternatives, and ask for confirmation.
- New ideas should be captured and classified before they affect active implementation.
- Broad Opus sessions are acceptable when they keep context coherent and changes are logically separated.
- Codex should usually receive narrower, accepted implementation scopes.
- The Revision project should remain a grounded sanity-check pass.

## 13. Common failure modes to prevent

Agents should actively prevent these failures:

| Failure mode | Prevention |
|---|---|
| Treating a raw idea as active priority | Classify idea state first. |
| Losing owner intent in technical summaries | Preserve original answer in router. |
| Repeating the same fact across many docs | Route concise conclusion to one home. |
| Reading too many docs by default | Load context in layers. |
| Skipping repo verification when current state matters | Verify source, docs, and open PRs first. |
| Overusing generic tools without repo meaning | Prefer SuperBot-specific wrappers over useful engines. |
| Forcing decisions during coding pressure | Use multiple-choice batches and answer at maintainer pace. |
| Letting planning sessions execute accidentally | Planning requires maintainer acceptance before execution. |
| Starting over after a plan is accepted | Allow same-session execution when context is still loaded. |
| Ignoring technically bad owner answers | Explain conflict, cite, propose, confirm. |

## 14. Suggested Opus mapping session

This document should be reviewed by Opus in a dedicated session.

Suggested Opus task:

```text
Review `docs/owner/maintainer-working-profile-and-idea-intake.md` as an owner-facing capture of the maintainer's working style and random-order idea intake problem.

First verify current repo state, open PRs, `.claude/CLAUDE.md`, `docs/current-state.md`, `docs/AGENT_ORIENTATION.md`, `docs/owner/README.md`, `docs/owner/maintainer-question-router.md`, and any open workflow/doc-hygiene PRs.

Then decide how this content should be mapped into the repo without duplication:
- what should stay in this owner-guidance document;
- what belongs in `docs/owner/ai-project-workflow.md` if that doc should be created;
- what belongs in `.claude/CLAUDE.md` or `docs/collaboration-model.md`;
- what belongs in `docs/AGENT_ORIENTATION.md`;
- what belongs in the maintainer-question router;
- what should remain conversation-only.

Ask the maintainer a short multiple-choice batch for any unresolved workflow choices.

Do not treat this document as an implementation plan. Produce a mapping plan first. Execute only after maintainer acceptance.
```

## 15. Open questions for Opus / maintainer

These questions may be useful in the dedicated mapping session:

1. Should this document remain as a permanent owner profile, or be split into a shorter owner profile plus a separate AI-project workflow doc?
2. Should every ChatGPT project instruction be mirrored in the repo, or should the repo only contain the shared pipeline and handoff templates?
3. Should random-order idea intake be added to the Ideas project instructions only, or also to the collaboration model?
4. Should per-project handoff templates be standardized in one doc?
5. Should the maintainer's personal working profile be treated as owner-guidance only, or as binding agent behavior when it affects collaboration?
6. Should this document be linked from `docs/owner/README.md`, `docs/AGENT_ORIENTATION.md`, or only used as a planning input for Opus?

## 16. Non-goals

This document should not:

- approve new bot features;
- replace the maintainer-question router;
- become a second current-state file;
- become a second collaboration model;
- replace project-specific ChatGPT instructions;
- require every implementation agent to read a long personal profile by default;
- turn the maintainer's raw idea order into implementation priority.

Its value is in preserving intent and giving Opus enough structured material to map the workflow cleanly.
