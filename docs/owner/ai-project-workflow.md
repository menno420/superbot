# AI-assisted project workflow

> **Status:** `reference` — how SuperBot's multi-agent planning/execution pipeline works.
>
> **Audience:** every agent (Claude/Opus, the ChatGPT projects, Codex) and the maintainer.
>
> **Purpose:** the durable, low-drift contract for *how work flows* across AI projects —
> the pipeline, each project's role, the clean handoff between stages, the shared
> idea-state vocabulary, and the failure modes to prevent. The maintainer's personal
> profile is in [`maintainer-working-profile.md`](./maintainer-working-profile.md); owner
> answers live in [`maintainer-question-router.md`](./maintainer-question-router.md).
>
> **Scope — process, not approval.** This does not approve any feature, and it does not
> restate rules that already bind — it links them. The planning→execute lifecycle and
> act-vs-ask live in [`../collaboration-model.md`](../collaboration-model.md) and
> `.claude/CLAUDE.md`; idea promotion lives in [`../ideas/README.md`](../ideas/README.md).

## 1. The pipeline

Work moves through stages; each stage knows its role and does not try to own the others.

```text
SuperBot Ideas project
  → SuperBot Decisions project
    → Opus planning / question batch
      → ChatGPT Revision project
        → Codex or Opus execution
          → PR review / routing / merge
```

This is the maintainer's normal high-confidence flow. A given task may skip stages (a
small, clear fix can go straight to execution), but the **roles** below do not change.

## 2. Per-stage roles

| Stage | Job | Explicitly not its job |
|---|---|---|
| **Ideas** | Expand a rough idea; name related systems, hidden dependencies, risks; preserve product vision; suggest the next state. | Approve work, write the final plan, or tell Codex to build. |
| **Decisions** | Compare options; define safe defaults and non-goals; pick a direction, or defer/reject. | Implement; skip repo verification when current state matters. |
| **Opus planning** | Read the repo in layers; inspect open PRs; use the question router when owner intent is unclear; use `scripts/context_map.py` for file-impact context; produce the real structured plan and any question batch; execute **only after acceptance**. | Execute before the maintainer accepts the plan. |
| **Revision** | Independent grounded sanity check: verify against source, docs, open PRs, architecture, owner intent, and tests; list required changes, optional improvements, user decisions, live-verification needs, and unverified assumptions. | Redesign unless explicitly asked. |
| **Codex / Opus execution** | Execute an accepted, narrow scope: verify the relevant files/docs, make the change, run the checks, open a PR. | Widen scope, or proceed when owner intent or repo state conflicts — stop and ask. |

Opus is especially valuable for broad context consolidation, documentation architecture,
final revision, and large-but-coherent refactors. Codex usually receives **narrower**,
already-accepted scopes.

## 3. Handoff templates

A handoff is clean when the receiving stage can act without re-reading the whole
conversation. Fill this envelope when moving work between stages:

```text
Handoff
- From → To:        <stage> → <stage>
- Idea / question:  <one line>
- State:            <raw | captured | needs-owner-answer | needs-decision |
                     needs-repo-verification | ready-for-planning | accepted-plan |
                     in-implementation>   (see §5)
- Inputs attached:  <links: source files, docs, open PRs, prior owner answers>
- Decided:          <what is settled>
- Open:             <what the next stage must resolve>
- Boundary:         <what the next stage must NOT do>
- Owner answers:    <router question refs, or "none needed">
```

Per stage, what each one should hand the next:

| Stage hands off | Contents |
|---|---|
| Ideas → Decisions | expanded idea + related systems + risks + suggested next state |
| Decisions → Opus | chosen direction (or defer/reject) + non-goals + safe defaults |
| Opus → Revision | structured implementation plan + open question batch + the files it touches |
| Revision → execution | required changes, optional improvements, user decisions, live-verify needs, unverified assumptions |
| execution → merge | a PR with code + tests + green checks + a description that links the plan |

## 4. Random-order idea intake

The maintainer may introduce ideas in **any order**. A new idea is **not** automatically a
priority change and does not interrupt active implementation — unless the maintainer says
so, or the idea reveals a blocker, safety issue, architectural conflict, or a serious
misunderstanding.

Default handling for any new idea:

```text
new idea → classify → capture or ask a question → route to the right home
         → promote only after decision / planning / verification
         → implement only after acceptance
```

> This is binding agent behavior, stated for agents in `.claude/CLAUDE.md` (Working
> agreement) and [`../collaboration-model.md`](../collaboration-model.md). This section is
> the workflow-level explanation of the same rule; the binding text wins.

## 5. Idea states (shared vocabulary, not a third tracker)

Use these words for an idea's status. They are a **shared vocabulary** that maps onto the
systems that already own state — they do **not** create a new tracker:

| State | Meaning | Owned / recorded by |
|---|---|---|
| `raw` | mentioned in chat, not structured | conversation |
| `captured` | written down as an idea, not approved | [`../ideas/README.md`](../ideas/README.md) promotion path |
| `needs-owner-answer` | needs a maintainer preference | [`maintainer-question-router.md`](./maintainer-question-router.md) |
| `needs-decision` | needs a trade-off / scope choice | router → Decisions stage |
| `needs-repo-verification` | can't be judged without checking source / docs / PRs | Opus planning |
| `ready-for-planning` | direction clear enough to plan | ideas/README promotion gates |
| `accepted-plan` | maintainer accepted the plan | `docs/planning/` + the session |
| `in-implementation` | active session / PR | `docs/current-state.md` |
| `shipped` | merged and reflected in the right docs | `docs/current-state.md` + a `.sessions/` log |
| `deferred` / `rejected` / `superseded` | intentionally later / do-not-repropose / replaced | where the decision was made (router, ideas backlog, or the rejection ledger in `docs/planning/superbot-ideas-lab-2026-06-05.md` §6) |

When you need one status word for an idea, use these. **Do not start a parallel states
list** — the promotion gates in [`../ideas/README.md`](../ideas/README.md) and the question
lifecycle in [`maintainer-question-router.md`](./maintainer-question-router.md) remain the
owners.

## 6. Context-map tooling

`scripts/context_map.py` answers, for any file under `disbot/`: *if I touch this, what else
is connected, what docs should I read, what tests should I run, and what ownership/risk
rules apply?* It complements CodeGraph (which cannot resolve this repo's file/module
edges), computing importers and blast radius with **Grimp** when it is installed and
falling back to a built-in AST scan otherwise. Curated docs/tests/risk routing comes from
`docs/context-map-overrides.yml`.

The philosophy is a **custom SuperBot wrapper over a useful existing engine** — the repo's
own architecture rules supply ownership/layer meaning, the override YAML supplies curated
routing, and Grimp supplies the import graph. It is meant to be practical, not exhaustive:
faster and safer agents, not a full runtime model. (Same "custom-tooling-over-new-deps"
preference recorded in `.claude/CLAUDE.md`; Grimp is dev-only, in `requirements-dev.txt`.)

## 7. Failure modes to prevent

| Failure mode | Prevention |
|---|---|
| Treating a raw idea as active priority | Classify the idea's state first (§4–§5). |
| Losing owner intent inside a technical summary | Preserve the original answer in the router. |
| Repeating the same fact across many docs | Route one concise conclusion to one home. |
| Reading too many docs by default | Load context in layers (see `docs/AGENT_ORIENTATION.md`). |
| Skipping repo verification when current state matters | Verify source, docs, and open PRs first. |
| Overusing generic tools without repo meaning | Prefer SuperBot-specific wrappers over raw engines. |
| Forcing decisions under coding pressure | Use small multiple-choice batches (router §10). |
| A planning session executing by accident | Planning needs maintainer acceptance before execution. |
| Starting over after a plan is accepted | Execute in the same session while context is loaded. |
| Implementing a technically bad owner answer as-is | Explain, cite, propose a safer alternative, confirm. |

## 8. Rules that bind this workflow (don't restate — follow)

- **Planning→execute lifecycle, act-vs-ask, bugs-first** →
  [`../collaboration-model.md`](../collaboration-model.md) and `.claude/CLAUDE.md`.
- **Multiple-choice question format** (how to ask the maintainer) →
  [`maintainer-question-router.md`](./maintainer-question-router.md) §10.
- **Load context in layers / one-fact-one-home** →
  [`../AGENT_ORIENTATION.md`](../AGENT_ORIENTATION.md) and `docs/current-state.md`.
- **Idea → shipped promotion gates** → [`../ideas/README.md`](../ideas/README.md).
