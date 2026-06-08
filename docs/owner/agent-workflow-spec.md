# Agent stage specifications

> **Status:** `reference` — how each stage of the SuperBot multi-agent pipeline behaves.
>
> **Audience:** the ChatGPT projects (Analysis, Decisions, Revision, Prompt Forge) and
> every executor agent (Claude / Codex). Read the section(s) for your stage.
>
> **Scope — the *how*, not the *what*.** The pipeline overview, per-stage role table,
> and handoff templates live in [`ai-project-workflow.md`](./ai-project-workflow.md).
> This doc is the operational spec: what each stage does inside its role, what it must
> not do, and what its output looks like.
>
> **Precedence.** When this file conflicts with source code or a binding doc, the source
> code and binding docs win (`.claude/CLAUDE.md` > `docs/collaboration-model.md` >
> `docs/architecture.md` / `docs/ownership.md` / `docs/runtime_contracts.md`).

---

## Quick navigation

| I am | Read |
|---|---|
| **Analysis** project | §3 + §8 |
| **Decisions** project | §4 + §8 |
| **Revision** project | §5 + §8 |
| **Prompt Forge** project | §6 + §8 |
| **Executor** agent (Claude / Codex) | §7 + §8 |

---

## 1. The pipeline (brief)

```text
Ideas → Analysis (when needed) → Decisions → Opus planning → Revision → Prompt Forge → Execution → PR
```

Any stage may be skipped for small, clear tasks where scope is already confirmed. The
**roles** do not change even when stages are skipped. Full pipeline detail:
[`ai-project-workflow.md` §1–§2](./ai-project-workflow.md).

---

## 2. When to use each stage

| Trigger | Stage |
|---|---|
| Scope is unclear, current state uncertain, or multiple subsystems involved | **Analysis** |
| A direction needs to be chosen, or non-goals and safe defaults defined | **Decisions** |
| An implementation plan needs an independent grounded sanity check | **Revision** |
| An accepted plan (or clear task) needs a session prompt for the executor | **Prompt Forge** |
| Small, clear task with confirmed scope | Skip to execution |

---

## 3. Analysis

### 3.1 Role

Analysis is the **discovery stage** — broader than Revision because it uncovers unknown
problems rather than validating a known plan. It reads, inspects, and reports. It never
implements, approves, or redesigns.

| In scope | Out of scope |
|---|---|
| Current state (grounded in source + merged PRs) | Implementing anything |
| Problems, inconsistencies, unfinished work | Redesigning plans |
| Root causes and risks | Approving work |
| Simplification opportunities (duplicate abstractions, misplaced logic) | |
| Future opportunities — *separated section only* | |
| Active gates and off-limits items that affect scope | |

### 3.2 Before reporting — verify these

1. **Open PRs** — check live GitHub (`mcp__github__list_pull_requests`); source code and
   merged PRs win over any doc.
2. **Active gates** — AI readiness, BTD6 provenance, privacy, server-management
   sequencing. Flag any gate that affects the task's scope.
3. **Current state** — `docs/current-state.md` (dated snapshot — treat open-PR entries
   as provisional; verify against live GitHub).
4. **Relevant folio** — the subsystem folio for the area under review.
5. **Off-limits** — `docs/current-state.md §Off-limits / do-not-propose`.

When source code contradicts a doc, flag the inconsistency and note that the source
wins. Never report the doc as current without verification.

### 3.3 Severity tiers

| Tier | Label | Meaning |
|---|---|---|
| 1 | **Critical blocker** | Must be resolved before any implementation continues |
| 2 | **Important improvement** | Should be done soon; latent risk or quality debt |
| 3 | **Cleanup** | Low-risk; may be deferred without harm |
| 4 | **Future opportunity** | Captured only — not active work |

Foundational fixes are **critical blockers** unless the maintainer explicitly overrides.

### 3.4 Output structure

```
## Analysis: <area>

### Current state
<What is actually true — grounded in source + merged PRs, not just docs>

### Problems / inconsistencies  [severity tier per item]
<Root cause, not symptom; one source of truth over a local patch>

### Simplification opportunities
<Duplicate abstractions, misplaced helpers, over-complex paths>

### Future opportunities  [captured only — not active work]
<Ideas separated from active findings>

### Recommended next destination
<Decisions / Revision / Opus planning / idea-capture — one clear recommendation>
```

### 3.5 Rules

- Future ideas land in the **separated Future opportunities section** — never promoted
  to active findings inside the report.
- **Always flag active gates and off-limits items** that affect scope.
- **Recommend the next destination** at the end.
- Never generate implementation plans — that belongs to Revision after Decisions.
- Always look for simplification opportunities, especially duplicate abstractions and
  misplaced logic.

---

## 4. Decisions

### 4.1 Role

Decisions compares options, defines non-goals and safe defaults, and picks a direction —
or explicitly defers/rejects. It does not implement, and does not skip repo verification
when current state matters.

### 4.2 Foundational-fix rule

Treat foundational fixes as **blockers**. Defer a visible feature to fix a foundation
issue unless the maintainer explicitly overrides. Root cause over symptom; one source of
truth over a local patch.

### 4.3 Output structure

```
## Decision: <topic>

### Chosen direction
<One clear direction, or "deferred" / "rejected" with a reason>

### Non-goals
<What is explicitly out of scope for this decision>

### Safe defaults
<Behavior to assume while any remaining open questions are unanswered>

### Deferred items
<Choices explicitly deferred, with reason and suggested revisit trigger>
```

---

## 5. Revision

### 5.1 Role

Revision is an **independent grounded sanity check**. It verifies an implementation plan
against source, docs, open PRs, architecture, owner intent, and tests. It does **not**
redesign the plan unless a safety, architecture, or correctness issue makes redesign
unavoidable — in which case it flags the specific conflict and explains why, rather than
silently rewriting.

| In scope | Out of scope |
|---|---|
| Verify plan against source + merged PRs | Redesign unless explicitly asked |
| Verify architecture boundaries and ownership rules | Implement anything |
| Verify owner intent alignment | Approve work independently |
| Flag source/doc conflicts | |
| Check test coverage | |

### 5.2 Architecture check (not optional)

Always verify the plan does not violate layer boundaries, ownership contracts, or
mutation paths before signing off. The binding rules are in `docs/architecture.md`,
`docs/ownership.md`, and `docs/runtime_contracts.md`. Architecture violations found at
Revision cost less than ones caught at CI.

### 5.3 Output structure (five sections)

```
## Revision: <plan title>

### Required changes
<What must be fixed before implementation proceeds>

### Optional improvements
<Suggestions the executor may apply — not required to proceed>

### User decisions
<Choices that need maintainer input before they can be resolved>

### Live-verification needs
<Things that cannot be confirmed from source alone — require a running bot, live data, etc.>

### Unverified assumptions
<Plan claims Revision could not verify — the executor must check these>
```

---

## 6. Prompt Forge

### 6.1 Before generating — read these

1. `docs/current-state.md` — current project state and ▶ Next action.
2. The relevant subsystem folio (if the task is area-specific).
3. Open PRs via live GitHub — source and merged PRs win over docs.
4. Active gates — if the requested scope conflicts with a gate (AI readiness, BTD6,
   privacy, server-management sequencing), **flag it in the generated prompt and mark
   the blocked scope off-limits** with a brief explanation.

### 6.2 Target agent — always specify

| Agent | Prompt character |
|---|---|
| **Codex** | Narrow, already-accepted scope. One clear goal. Minimal context overhead. |
| **Opus** | Broader: context consolidation, planning, revision, or large-but-coherent refactors. Full context envelope. |

### 6.3 Standard prompt anatomy

Every executor prompt includes these sections. Omit only what is genuinely not applicable.

**Context**
Current state ref (`docs/current-state.md`) + relevant docs/PRs + any prior planning
output the executor needs.

**Objective**
Lead with this. Desired outcome in one or two sentences. Do not bury it under guardrails.

**Scope**
What is in scope; what is explicitly out of scope — short. Over-long restriction lists
drown the goal.

**Reading list** *(include when directly relevant)*
Specific docs/files/folios the executor should read first. Point to the task-matching
route in `docs/AGENT_ORIENTATION.md` "Reading order by task."

**Repo checks** *(include when disbot/ code is touched)*
```
python3.10 scripts/check_quality.py --full          # CI mirror — run before push
python3.10 scripts/check_architecture.py --mode strict
```
For `disbot/*.py` edits: `python3.10 scripts/context_map.py <path>` before first edit.
For symbol/cross-file work: `mcp__codegraph__where` / `context` / `fn_impact` before
Grep or Read.

**Boundaries**
Active gates and off-limits items. One-line truth-layer reminder:
> Source code and merged PRs win over docs — verify open PRs against live GitHub.

**Output format**
What the executor should produce (code, docs, PR, etc.).

**Verification steps**
How to confirm the work is correct (tests to run, live check, CI, etc.).

**Stop conditions** *(keep short — these are not the goal)*
Pause and ask only for: real ambiguity about the goal, an irreversible/external action,
or a decision that only the maintainer can make. Everything else: act.

**End-of-session requirements**
- Open a PR — standing advance consent, every session.
- Write `.sessions/YYYY-MM-DD-<slug>.md` with a **Context-delta section** (what the
  session needed vs. what orientation pointed it to; what had to be discovered by hand).
- Update `docs/current-state.md` if anything shipped, opened, blocked, or deferred.

No handoff section.

### 6.4 Cross-cutting one-liners (include in every prompt)

- **New ideas mid-session:** route to `docs/ideas/`, not active scope.
- **Unclear owner intent:** add a Q-block to `docs/owner/maintainer-question-router.md` —
  do not guess product intent.
- **Binding docs win:** if this prompt conflicts with `.claude/CLAUDE.md` or
  `docs/collaboration-model.md`, those docs win — raise the conflict.
- **Plan vs. execute:** planning stays read-only until accepted via ExitPlanMode; once
  accepted, execute fully in the same session without re-confirming.
- **Aim for noticeable results:** one real improvement end-to-end beats scaffolding.

### 6.5 Docs-only sessions

Same full-envelope prompt, minus the Repo checks section. Docs sessions still need
objective, scope, reading list, stop conditions, and end-of-session requirements.

### 6.6 When to include verification commands

Include `check_quality.py --full` and `check_architecture.py --mode strict` whenever
implementation or repo file modification is expected. Omit for pure docs/research.

---

## 7. Executor guidance (Claude / Codex)

This section supplements `.claude/CLAUDE.md` and `docs/collaboration-model.md`; it does
not replace them. When they conflict, those docs win.

### 7.1 Planning → execute lifecycle

A planning session **stays planning until the plan is accepted** (ExitPlanMode). Before
acceptance: read-only research + safe local prototyping only, no commits. After
acceptance: finish the plan **in the same session** — code, tests, commit, push, PR —
without re-confirming. "Planning only" language appearing *after* acceptance is drafting
residue; ignore it.

### 7.2 Act vs. ask

| Act | Ask |
|---|---|
| Contained, reversible, verifiable change | Irreversible action (data loss, external publish) |
| Adjacent root-cause fix discovered mid-task | Large / cross-cutting (architectural, multi-subsystem) |
| | Goal itself is genuinely ambiguous (two readings → materially different products) |

If you are about to offer options you already expect rejected, you have answered your own
question — act.

### 7.3 Adjacent bugs

Fix root-cause adjacent bugs when the fix is contained, reversible, and verifiable.
Root cause over symptom; one source of truth over a local patch. Discovering and fixing
an adjacent bug is expected behavior, not scope creep.

### 7.4 PR size

Small, focused PRs for risky / runtime (`disbot/`) code. Larger end-to-end PRs are fine
for docs, tooling, and low-risk refactors — when the work is internally coherent and
strongly verified.

### 7.5 Noticeable results

Prefer finishing one real improvement end-to-end over starting three and shipping
scaffolding. You are trusted to do large, accurate work in one session — plan around
that capacity, not around the smallest safe slice.

### 7.6 End-of-session secondary task — groom the idea backlog

Once the main task + PR are done and capacity remains, you are **not** finished. Spend the
leftover capacity grooming the idea backlog so it keeps draining and you always have a next
thing to do:

- **Browse** `docs/ideas/` and any ideas the maintainer raised this session.
- **Move one idea down its lifecycle** ([`../ideas/README.md`](../ideas/README.md)): execute
  a small, safe, decided-lane idea now; structure a bigger one into a `docs/planning/` plan +
  a `docs/roadmap.md` horizon; or open a discussion (router Q-block) if it is excessive,
  ambiguous, or a product-vision call.
- **Record** the move — the idea's state + a line in the `.sessions/` log.

This is real work, not scope creep: the maintainer drops ideas in any order on purpose and
relies on agents to route them so **every idea eventually becomes implemented or discussed,
never orphaned** (owner decision Q-0015).

---

## 8. Cross-cutting rules (all stages)

### 8.1 Truth-layer precedence

```
source code and merged PRs
  > binding docs (CLAUDE.md · collaboration-model.md · architecture.md · ownership.md · runtime_contracts.md)
    > docs/current-state.md  (dated snapshot — verify open PRs against live GitHub)
      > session journal (process memory)
```

When a doc and source disagree, the source wins. Never report a doc as current without
verification.

### 8.2 One-fact-one-home

Route each fact to one canonical doc and link elsewhere. Restatement across files is
where drift breeds.

### 8.3 Ideas routing

Idea order ≠ implementation order. A new idea raised mid-stream: **capture in
`docs/ideas/`; do not promote to active scope** unless the maintainer says so or it
exposes a blocker, safety, or architectural conflict. The promotion path is
[`../ideas/README.md`](../ideas/README.md).

### 8.4 Unclear owner intent

When intent is genuinely unclear: add a Q-block to
`docs/owner/maintainer-question-router.md`. Unanswered questions are **not** approval —
safe defaults apply until answered. Do not guess product intent.

### 8.5 Docs maintenance is first-class work

Improving docs / orientation / tooling / folios is first-class work, never wasted effort.
Every session should leave the next better equipped. You have free rein on docs; ask
before changing executable config (hooks, `.claude/settings.json`, binding CLAUDE.md
rules).

### 8.6 Active gates

Before starting or scoping work, check:
- **AI/BTD6** — `docs/current-state.md §Gates / blocked work`
- **Privacy/safety** — no AI action capabilities without all documented gates + a
  dedicated decision
- **Server-management sequencing** — the status tracker owns the queue

If scope conflicts with an active gate, flag it and mark the blocked scope off-limits.
Do not silently plan past a gate and discover the block mid-session.
