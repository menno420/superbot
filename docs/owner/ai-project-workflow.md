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

**Operational specs** (what each stage does, output formats, cross-cutting rules):
[`agent-workflow-spec.md`](./agent-workflow-spec.md).

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

The full **idea lifecycle** (intake → map → route → groom → *implemented | discussed |
rejected*) and the end-of-session **grooming** secondary task — what an agent does with
leftover capacity so the backlog keeps draining — live in
[`../ideas/README.md`](../ideas/README.md). This section is the pipeline-level view of the
same loop; that README owns the mechanics (owner decision Q-0015).

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

The **Opus planning** stage uses `scripts/context_map.py` to answer "if I touch this file,
what else is connected, and what should I read/test before editing?" — the file-impact
context CodeGraph can't resolve. It's the **custom-wrapper-over-a-useful-engine** philosophy
in practice (the repo's architecture rules + an override YAML + Grimp), matching the
"custom-tooling-over-new-deps" rule in `.claude/CLAUDE.md`.

Full usage, the trust matrix, and the override-file contract live in
[`../context-map-tooling.md`](../context-map-tooling.md) — this section does not restate them.

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

## 9. Concurrent-editing safety (multiple chats at once)

The maintainer runs several chats in parallel, and `main` can move under you mid-session.
To keep that productive instead of collision-prone, the shared, frequently-co-edited files
have **per-section / per-file ownership** so two chats touching different parts never
conflict:

| Shared file | Collision-safe pattern |
|---|---|
| `.claude/CLAUDE.md` | **Section ownership** via `<!-- SECTION_START/END -->` markers (`READ_FIRST` · `SESSION_WORKFLOW` · `CI_PARITY` · `CODEGRAPH` · `ARCH_RULES`). Edit **one** block; two chats in different blocks auto-merge. |
| `docs/owner/maintainer-question-router.md` | **Append-only.** Add the next free `Q-00NN` block at the end; never renumber or reflow existing ones. **Accept-and-reconcile is the decided policy for concurrent sessions (Q-0060)** — no session ledger, no hotspot locks; collisions resolve at merge. **Merge collision** (two sessions appended concurrently — it happened 2026-06-09): the *merged/answered* entries keep their numbers; an unmerged entry that duplicates an answered question is **dropped**, not double-recorded; still-open unmerged entries **renumber to the new tail** and the renumbering session fixes its own cross-references. **Answer scope:** when recording an answer next to adjacent mechanics, add one line on what it does *not* decide (the Q-0050 "craft-once" wording forced a re-ask, Q-0054). |
| `.sessions/` | **Per-file.** One `YYYY-MM-DD-<slug>.md` per session — no shared anchor, so no structural conflict. |
| `.session-journal.md` (guidebook) · `docs/current-state.md` | Edit the **smallest** relevant block; on conflict resolve by **UNION** (keep both additions — it's docs, no CI risk). |

Practical rules when several chats are live:

- **Expect `main` to move.** Re-fetch before you push; prefer additive, section-scoped edits
  over rewrites of a whole shared file.
- **Ship in logical modular batches** (owner decision Q-0014) — small, self-contained PRs
  merge around each other cleanly; a sprawling PR that touches every shared file is the one
  that collides.
- **One fact, one home.** Route a durable conclusion to its owning doc and link from the rest
  — restatement across files is exactly what turns a clean merge into a conflict.

### Parallel execution lanes (two agents on the same plan, simultaneously)

First deliberate run: 2026-06-09, Lanes 2 (#632) + 3 (#634) of the multi-lane plan,
one agent each. Empirical result: **zero code conflicts, one mechanical docs conflict**
— the model works. What made it work, and the rules it earned:

- **Partition by subsystem, and put an explicit "do not touch" list in each prompt.**
  Lane 2 (governance/access/diagnostics) and Lane 3 (AI orchestration) share no files,
  so the build phases never interacted. The exclusion list meant no guessing about the
  boundary. Two agents inside the *same* subsystem would need file-level partition —
  don't run that variant without one.
- **The entire collision surface is the cross-cutting ledgers** (`docs/current-state.md`
  lane list, the execution plan's scoreboard). Lane-owned docs — plan section banners,
  folios, `capability-authority.md` — partition naturally and merged clean. Budget your
  caution accordingly: free rein on lane-owned docs, surgical edits on ledgers.
- **Edit only your own lane's paragraph/card; never reflow neighbours.** The scoreboard's
  per-lane cards auto-merged (separate list items). The current-state lane list ¶2/¶3
  conflicted *only because the paragraphs are adjacent lines* — and resolution was
  mechanical UNION (keep both) precisely because each agent had stayed inside its own ¶.
- **Leave the shared "▶ Next action" header pointer alone during a parallel burst.** It
  says "first unchecked lane", which self-corrects through the scoreboard; rewriting it
  from two sessions is a guaranteed same-line conflict for zero information gain.
- **Re-fetch + merge `origin/main` right before the END-protocol docs push.** The 2026-06-09
  conflict landed because the other lane merged between this lane's code push and docs
  push. A last-moment sync usually absorbs it; when the other PR merges *after* your final
  push anyway, the **second-to-merge agent owns the reconciliation** — a ~2-minute UNION
  resolve. That is the designed cost: accept-and-reconcile (Q-0060), no locks.
- **Skip the standing backlog-grooming secondary task in a parallel session** — two agents
  grooming `docs/ideas/` simultaneously is an avoidable collision on a shared tracker;
  the next solo session picks it back up.
- **Name the parallel partner in the PR body** ("Agent N is concurrently working on
  Lane M; this PR avoids …") so the reviewer knows two PRs are siblings, not rivals.
- **Do not add coordination machinery.** The observed total overhead was one mechanical
  merge; any session-ledger / lock protocol would cost more than it saves. The
  per-section ownership table above + the rules here are sufficient.
