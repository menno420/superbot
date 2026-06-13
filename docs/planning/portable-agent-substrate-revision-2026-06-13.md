# Revision report — Portable agent-memory + workflow substrate (Plan v5)

> **Status:** `plan` — an **independent revision/complement** of the externally-reviewed "Portable,
> self-learning agent-memory + workflow system" plan (Plan v5). **Not an approval and not a rewrite.**
> Its job: *don't fight the plan unless there's a real blocker* (there isn't), add the final touches
> to make it future-proof, surface forgotten steps, audit it against known AI weaknesses, and answer
> the maintainer's specific question about **task-stance "modes"** (question/analysis/etc.). Grounded
> in a GitHub + web prior-art sweep (2026-06-13) and a read of the in-repo substrate. Pairs with the
> idea doc [`../ideas/portable-agent-memory-package-2026-06-12.md`](../ideas/portable-agent-memory-package-2026-06-12.md)
> and the loop vision [`../ideas/autonomous-improvement-loop-vision-2026-06-12.md`](../ideas/autonomous-improvement-loop-vision-2026-06-12.md).
> Assumptions we should test ourselves are **quarantined in §7** (per the maintainer's ask).

---

## 0. Verdict (TL;DR)

The plan is **strong and should proceed as written**. Five external rounds already hardened the
*safety + measurement* model; this pass adds the things those rounds structurally couldn't, because
they were model critiques rather than a **prior-art survey**: where this sits in a now-crowded field,
and one genuine architectural axis the plan is missing.

**The one substantive addition — and it's the maintainer's exact instinct:** the plan controls the
agent on three axes (adoption **pace**, promotion **rights**, lifecycle **stage**) but has **no
task-stance axis** — no "question mode," "analysis mode," "debug mode," "review mode." This is not a
nicety. Every mature agent harness ships it (Roo Code's Code/Architect/Ask/Debug/Orchestrator;
Cline's Plan/Act; Claude Code's plan mode + output styles), and the research says a *tool-scoped*
stance is one of the cheapest mitigations for the three failure modes this whole project is built to
fight: **scope creep, goal drift, and tool-selection collapse**. It should be a first-class engine
concept (§2).

**The one thing to fix before anything else:** the working name `agent-os/` collides head-on with at
least three established projects, one of them a direct sibling (§3.1). Rename now; it's free today and
expensive after publish.

Everything else here is additive: prior-art positioning (§3), an AI-weakness audit with concrete
patches (§4), forgotten steps (§5), small refinements (§6), assumptions to test (§7), and an explicit
"don't dilute these" list (§8).

---

## 1. How I researched this

- **In-repo:** read the two idea docs, the skills inventory (`.claude/skills/{pre-pr,architecture-review,session-close}`),
  the orientation chain, the question-router + idea-lifecycle schemas, the four stdlib checkers, and
  `tools/agent_context/build_pack.py`. Confirmed first-hand what the plan claims exists.
- **GitHub sweep:** repository searches across `topic:claude-code` (36k+ repos), agent-memory
  frameworks, spec-driven-development kits, and the `agent-os`/`agentos` namespace; an issue search of
  `menno420/superbot` itself (nothing prior on this topic beyond the two idea docs — the field is
  external, not internal). Note: the GitHub MCP here is scoped to `menno420/superbot`, so external
  repos were read via the web.
- **Web grounding** for the moving parts: Roo Code's custom-mode schema, Cline/Claude-Code mode
  semantics, GitHub Spec Kit, Agent OS (buildermethods), 12-factor-agents, and a 2026 AI-agent
  failure-mode handbook. Sources listed at the end.

What I did **not** find: any project combining *all* of this plan's pillars (single-file stdlib
bootstrap + a staged interview that **grows** project content + the self-audit session-ender loop +
promotion-rights + a model-agnostic review seam). The combination is genuinely novel. Individual
pillars, however, each have strong prior art worth borrowing from (§3).

---

## 2. The missing axis: task-stance "modes" (the maintainer's question, answered)

### 2.1 Confirmed: it is genuinely absent

You did not miss it. The plan has **three control axes, all about governance/onboarding**:

| Axis in the plan | Values | What it controls |
|---|---|---|
| Onboarding **mode** | `observe` / `guided` / `active` | adoption **pace** |
| Promotion **rights** | `observe` / `propose` / `promote` | what may change **without sign-off** |
| **Stage** | `integration` → `steady` | lifecycle **phase** |

None of these is a **task stance** — the cognitive posture the agent adopts for the *kind of work in
front of it right now*. The only stance the whole substrate has is `ExitPlanMode` (plan vs. execute),
inherited from Claude Code. The closest in-repo analogs — the pipeline *stages*
(analysis → decisions → revision → execution in `docs/owner/ai-project-workflow.md`) and the
*routines* (dispatch / docs-reconciliation / night-executor in
`docs/operations/autonomous-routines.md`) — are **separate agents/jobs**, not stances one agent
switches into. So the portable kit, as drafted, would actually **lose** a capability the source
system has (role specialization), flattening it into "one agent + onboarding knobs."

The plan ships exactly one skill (`session-close`) and treats skills as **ritual drivers**, not as
**cognitive stances**. "Question mode" / "analysis mode" are nowhere.

### 2.2 A naming landmine inside the plan

The plan already uses the word **"mode"** for adoption pace, and ships a `mode <name>` CLI verb for
it. If task-stance modes are added later under the same word, they collide — and "mode" in every
other tool (Roo, Cline, Claude Code, Cursor) means *task stance*, so users will expect that meaning.
**Fix the vocabulary now, before either is built:**

- adoption pace → **`pace`** (`pace observe|guided|active`)
- authority → **promotion-rights** (unchanged)
- task stance → **`mode`** (or `lens`) — `mode ask|analyze|plan|build|debug|review|…`

Reserving the words is a 10-minute decision today and an unfixable wart after release.

### 2.3 How the field does it (prior art for the mechanism)

The cleanest, most-copied design is **Roo Code custom modes**. A mode is a small declarative record:

| Field | Role |
|---|---|
| `slug` | stable id |
| `name` / `description` | UI label + one-line purpose |
| `roleDefinition` | identity/expertise text injected at the **start** of the system prompt |
| `whenToUse` | guidance for **auto-selection / orchestration** (lets an orchestrator pick the mode) |
| `customInstructions` | rules injected at the **end** of the system prompt |
| `groups` | **allowed toolsets + file-access scope** — `read` / `edit` / `command` / `mcp`, where `edit` can carry a `fileRegex` restricting which paths the mode may write |

Read-only is literally `groups: [read]`. Built-ins: **Code** (full edit), **Architect** (read-only
planning/design), **Ask** (Q&A/explanations), **Debug** (systematic hypothesis-narrowing), and
**Orchestrator** (decompose → delegate to other modes, a.k.a. "Boomerang"). Cline ships the same idea
as **Plan/Act**; Claude Code expresses it as **plan mode + output styles + skills + subagents**.

The crucial detail the plan should steal: **a mode bundles a prompt overlay *with* a tool/permission
scope.** That is what turns "please don't edit files while answering a question" from a hope into a
mechanism.

### 2.4 Why this matters for *this* substrate specifically — it's a safety control

Three reasons, the last two grounded in the failure-mode research:

1. **It is the substrate's own thesis.** The whole project is "reproduce *how the maintainer works*."
   The maintainer demonstrably works in distinct stances — he designs/visualizes (analyze), asks
   questions (ask), directs builds (build), and reviews (review). The source repo even encodes these
   as separate pipeline stages. A faithful extraction must carry the *stance* concept, not just the
   pace/authority knobs.
2. **Tool-scoped stances mitigate the exact AI weaknesses the plan exists to fight.** Scope creep and
   over-eagerness (acting when it should ask) are *stance* failures — the agent edits when it should
   only answer. A mode that says "Ask: `groups: [read]`" makes "act vs. ask" **mechanical** instead of
   a discipline in CLAUDE.md prose. Goal-drift research formalizes drift as both commission
   (`GD_actions`) and omission (`GD_inaction`); a stance with explicit entry/exit conditions is a
   natural place to assert "are we still doing the thing this mode is for?"
3. **It measurably improves tool selection.** The 2026 handbook reports tool-selection accuracy
   collapsing from **43% → 14%** as the toolset bloats, and a **94%** token reduction from progressive
   (staged) tool disclosure. A mode that exposes only its relevant tools is exactly that disclosure
   discipline — so modes aren't just safety and ergonomics, they make the agent *more accurate*.

This reframes the addition: it is not "add some personas." It is "add the missing **mechanical
guard-rail axis**, which the field already proved out, and which doubles as a tool-budget win."

### 2.5 Recommendation — ship a `mode` (stance) layer as a first-class engine concept

Add `engine/modes/` alongside `engine/interview/`. A mode is a markdown+frontmatter file
(`SKILL.md`-shaped, so it maps onto Claude Code skills directly), carrying the Roo fields plus two
this substrate needs:

- `reading_route` — which `docs/AGENT_ORIENTATION.md`-style route to load on entry (ties modes to the
  orientation chain and to progressive disclosure, §4).
- `entry` / `exit` conditions — when to suggest/leave the mode (e.g., Build mode exits to Review mode
  on "tests green, pre-PR clean").

**Default mode set (the engine ships these; the interview tunes/extends them):**

| Mode | Stance | Tool scope | Produces |
|---|---|---|---|
| **ask** *(your "question mode")* | answer from repo + memory; cite sources | `read` only | an answer, no file changes |
| **analyze** *(your "analysis mode")* | deep investigation / design | `read` + write to `docs/planning` only | a findings/plan doc, no implementation |
| **plan** | formalize the ExitPlanMode discipline | `read` (+ plan artifact) | an approved plan |
| **build** | implement under the audited seams | full | code + tests + PR |
| **debug** | systematic hypothesis-narrow → instrument → fix → verify | `read` + scoped `edit` | a root-caused fix |
| **review** | the independent-review stance (the Hermes seam) | `read` only | proposition+evidence critique |

These already exist *latently* in the source repo as stages/routines/skills — the work is to **name
them as modes and make switching first-class**, not to invent behavior.

### 2.6 Other stances worth shipping (your "anything else like this?")

Beyond ask/analyze, four more earn their place — each maps to a real maintainer need or a known
failure mode:

- **orchestrate** — decompose a big task into mode-tagged subtasks and delegate (Roo's
  Orchestrator/Boomerang). Maps onto Claude Code **subagents**, which the handbook credits with a
  **90.2%** improvement from context *isolation* (not parallelism). This is also how the multi-session
  pipeline becomes intra-session when useful.
- **teach / explain** — the maintainer "can't code and relies on you." Claude Code already has an
  Explanatory/Learning output style; a stance that narrates *why*, in plain language, directly serves
  the owner profile and the "Hermes explains features to the maintainer" gate.
- **triage / intake** — the front-end for idea-intake + question-routing (raw idea → mapped → routed;
  the interview's question front-end lives here).
- **incident / hotfix** — "bugs first, durably" as a stance: minimal-change, root-cause, fast-path,
  reversible. A named stance keeps an autonomous run from "refactoring while the house is on fire."

Ship **ask, analyze, plan, build, review** in the first cut (they're the load-bearing ones and all
already latent); add debug/orchestrate/teach/triage/incident as the catalog the interview can enable
per project.

### 2.7 How to implement it portably

The plan is implicitly Claude-Code-shaped (hooks, `.mcp.json`, `ExitPlanMode`, the `session-close`
skill). Two honest options — pick per the v1 scope decision in §5.7:

- **Claude-Code-native (simplest):** render each mode as a **skill** (`SKILL.md`) for the stance
  prompt, use **plan mode** for `plan`, **output styles** for persistent stances (ask/teach), and
  **subagents** (scoped tools + isolated context) for `orchestrate`/`review`. This is the
  dominant "skills-as-markdown" extensibility pattern and needs no new mechanism.
- **Tool-agnostic (future-proof):** keep one canonical `engine/modes/*.md` definition and a thin
  renderer that emits the host's native form — Claude Code skills/output-styles, Roo/Kilo custom
  modes, Cursor rules, or a plain prompt-prelude for bare models. This is exactly how spec-kit and
  Agent OS reach "30+ agents" (§3.2): one source, many adapters.

### 2.8 Where it lands

Modes are **PR 2** material (alongside the templated hooks and `settings.template.json`), with the
*vocabulary reservation* (§2.2) and the `ask`/`analyze` defaults pulled into **PR 1** so the seam
exists from the start and the maintainer's two named stances work on day one.

---

## 3. Prior-art / related-work positioning (the GitHub deliverable)

The plan's five review rounds were all *model critiques*; none surveyed the field. It's crowded now,
which is good news — it means most pillars are de-risked by someone else's production use, and the
plan only needs to **borrow mechanisms and differentiate clearly**. A "Related work / why not just
use X" section is itself a forgotten step (§5.2).

### 3.1 Name collision — rename `agent-os/` now

`agent-os` is taken, repeatedly:

- **`buildermethods/agent-os`** — a well-known, actively promoted "system for spec-driven development
  with AI coding agents… inject your codebase standards and write better specs," compatible with
  Claude Code/Cursor/etc. This is the **closest-sounding sibling** and the collision that will cause
  real confusion.
- **`framerslab/agentos`** (~576★) — a TypeScript agent framework with "cognitive memory."
- **`kivo360/OmoiOS`**, plus a long tail of "…OS for agents" projects (e.g. `Athena-Public`
  brands itself "The Linux OS for AI Agents").

Defer the *published* name if you like, but pick a non-colliding **working** name today so docs,
tests, and `state.json` namespaces don't have to be renamed later. (Candidates that read well and are
clearly free-ish in this space: something around *substrate / loom / scaffold / throughline* — the
point is just "not agent-os".)

### 3.2 Spec-driven neighbors — borrow the constitution, the clarify step, and the adapter pattern

A whole category does "structure the agent's work via durable docs": **GitHub `spec-kit`**
(`specify → plan → tasks → implement`, plus `clarify` and `analyze`), **buildermethods/agent-os**,
**`get-shit-done`** (64k★), **`shotgun`**, **OpenSpec**, and dozens of "kits." They are **adjacent but
different**: they structure *one feature's* development; this plan grows *whole-project memory + a
self-improving loop*. Three things to steal rather than reinvent:

1. **A "constitution" artifact.** spec-kit persists project principles in
   `.specify/memory/constitution.md` that *all later phases obey*. That is precisely this plan's
   "CLAUDE.md binding-rules + current-state ledger," and the convergence is a strong validation.
   Adopt the *name-and-shape* familiarity where useful.
2. **The `clarify` pattern.** spec-kit's `/clarify` = "sequential, coverage-based questioning that
   records answers in a Clarifications section." That is the plan's **interview**, scoped to a feature
   instead of the whole project — confirming the interview design and giving a proven UX to mirror.
3. **The adapter model.** Both spec-kit and Agent OS reach many tools via per-agent adapters/installers.
   If v1 wants to be "portable" beyond Claude Code, this is the pattern (§2.7, §5.7).

**Differentiator to state plainly:** spec-driven kits assume you already know what to build and need
discipline; this substrate assumes you need the *agent* to learn *how you work* and then run the loop
itself. Say so in the README.

### 3.3 Memory neighbors — they confirm the seam, and the zero-dep stance is the differentiator

- **`claude-mem`** (~82k★) — "persistent context across sessions… captures, compresses with AI,
  injects back." Same *goal* as the plan's memory layer, but it's **chromadb/sqlite/embeddings** —
  the heavy-retrieval path Grok's round warned against. Its popularity proves demand; its dependency
  weight is exactly what the single-file stdlib bootstrap differentiates against.
- **`atomicmemory`** — "portable semantic memory for AI agents: core engine, SDK, MCP server, CLI."
  Direct neighbor; pgvector-backed. Same lesson.
- **`gitagent`** (open-gitagent) — "universal git-native AI agent framework. Your agent lives inside a
  git repo — identity, rules, memory, tools, and skills are all version-controlled files." This is the
  **closest philosophical cousin** (memory = versioned files). Worth reading before PR 1 to see what a
  git-native file-memory layout looks like in the wild.
- **`letta-ai/agent-file` (.af)** — an open format for serializing stateful agents. Relevant to the
  plan's `state.json` + the "optional external-memory adapter seam" (Round 4 #6): if you ever want
  interop, `.af` is the emerging interchange format to point the adapter at.
- **`SoloFlow`** — "zero deps, Ebbinghaus memory, skill evolution, governance, 80+ tests." A rare
  *zero-dependency* cousin; a useful sanity check that stdlib-only memory + governance is viable.

**Net:** the memory pillar is well-trodden; the plan's defensible edge is **zero-dep + file-native +
grown-by-interview**, not the memory store itself. Keep the optional adapter seam (Round 4 #6) so you
interop without taking the dependency.

### 3.4 The cheapest competitor: fork-and-fill templates

**`florian101010/awesome-agentic-AI-coding-template`** — *"Stop re-explaining your project to every AI
agent… Fork it, fill the `[FILL:]` markers… skills system, agent workflows, git hooks included."*
This is almost exactly the plan's "interview-populated templates with `$PLACEHOLDER`," already shipped
as a static fork-and-fill repo. It is the **minimum viable version of this idea**, and it's the thing a
skeptic will say "why not just use that?"

**The plan's answer must be explicit:** static templates are filled *once, by hand, by someone who
already knows the answers*. This plan's differentiator is the **staged interview that fills them over
many sessions, can self-answer provisionally when no human is present, and a loop that keeps them from
rotting.** That's the moat — so the README must lead with "grows and maintains itself," not "templates
you fill in," or it looks like a heavier fork-and-fill.

### 3.5 Principle references to map against (future-proofing credibility)

- **`humanlayer/12-factor-agents`** (~23k★). The plan already honors most factors implicitly; *say
  so*. Direct hits: **F2 own your prompts**, **F3 own your context window**, **F5 unify execution &
  business state** (`state.json` is exactly this), **F7 contact humans with tool calls** (the
  question-router/Q-blocks), **F8 own your control flow** (the bootstrap CLI/state machine), **F9
  compact errors into context**, **F10 small focused agents** (modes/subagents), **F11 trigger from
  anywhere** (the routines/dispatch). A one-paragraph "how this maps to the 12 factors" in the README
  buys instant credibility with the audience most likely to adopt.
- **`vasilyevdm/ai-agent-handbook`** — the catalog behind §4's numbers (context rot, instruction
  centrifugation, tool sprawl, progressive disclosure, SOUL.md split, skills-as-markdown, subagent
  isolation). Use it as the citation spine for the safety docs (PR 3).

### 3.6 "Why not just use X" — the table to put in the README

| Existing thing | What it gives | Why this plan still exists |
|---|---|---|
| spec-kit / Agent OS / GSD | spec-driven *feature* discipline | they structure one feature; this grows whole-project memory + a self-running loop |
| claude-mem / atomicmemory | persistent cross-session memory | heavy deps (vector DBs); this is zero-dep, file-native, single-file-portable |
| fork-and-fill templates | pre-wired project scaffold | filled once by hand; this is *grown* by a staged interview + kept fresh by the loop |
| gitagent | git-native file memory | framework you adopt; this is a stdlib bootstrap that drops into an existing repo + tool |
| 12-factor-agents | principles | a doc of principles; this is a runnable substrate that *embodies* them |

---

## 4. Known-AI-weakness audit

Checked the plan against the 2026 failure-mode literature. The plan is **already strong on the
governance failures** (sycophancy, graduation-gaming, monoculture) — those were the external rounds'
focus. The gaps cluster on **context economics and memory integrity**, which model-only reviewers
under-weight because they don't feel token budgets.

| Weakness (with grounding) | Plan coverage | Verdict | Patch |
|---|---|---|---|
| **Sycophancy / rubber-stamping** | independent-review seam + anti-anchor payload + conflict-as-gate | ✅ covered | keep |
| **Graduation/proxy-goal gaming** | non-placeholder counting, provisional self-answers, SICA gate | ✅ covered | keep |
| **Monoculture (same blind spots)** | model-agnostic review seam | ✅ covered | keep |
| **Context rot — degrades at ~25% fill, not 100%** | pre-compaction handoff + episodic index + state-delta (PR 3) | 🟡 partial | add a **substrate context budget** (§4a) — the orientation+memory+reflections+user-style+modes the plan injects *forward* is itself context; budget and progressively disclose it |
| **Instruction centrifugation (system-prompt influence fades as context grows)** | SessionStart injection only | 🟡 partial | **re-inject the core agreement near the *end* of long contexts**, not just at start; the handbook's named fix |
| **Lost-in-the-middle** | handoff + episodic index | 🟡 partial | same budget/disclosure discipline; keep the ledger as the single high-signal anchor |
| **Goal drift (`GD_actions` / `GD_inaction`)** | session-enders + reconciliation cadence | 🟡 partial | a **mode** with explicit entry/exit (§2) is the natural drift check; add a per-session "still on the stated goal?" line to the session-log schema |
| **Scope creep / over-eagerness (act-vs-ask)** | CLAUDE.md prose discipline | 🟡 → mechanical | **tool-scoped modes** (§2) make it mechanical, not aspirational |
| **Cascading errors** | atomic state writes (PR 1) | 🟡 partial | atomic write protects one file; add a **memory checkpoint/restore** (git tag or `state.json.bak`) so a bad autonomous run is revertible, not just non-corrupt |
| **Memory poisoning / prompt-injection via persisted memory** | anti-anchor payload; provisional self-answers; deprecation/unlearning | 🔴 **gap** | the substrate **injects memory forward every session** and **ingests external text** (issues, PR comments, web). A poisoned log/issue becomes a standing instruction. Add: treat ingested external content as **data, not instructions**; quarantine it behind an explicit envelope in memory; never let un-reviewed external text enter the orientation chain. (See §4b.) |
| **Tool sprawl / selection collapse (43%→14%)** | stdlib, lean surface | 🟡 partial | modes' tool scoping + progressive disclosure (§2.4) |
| **Long-horizon capability decay (METR)** | METR-style KPI (PR 3) | 🟡 partial | wire the **stop-conditions** the loop vision lists as open (cost cap / run cap / red-readiness freeze) — a KPI without a brake is a dashboard, not a control |

### 4a. The substrate's own context budget (the ironic gap)

The system built to *fight* context rot **adds** to context: orientation chain + ledger + reflections
+ user-style block + mode prompt, injected every session. With rot measurable from ~25% fill, an
unbudgeted substrate could consume the very headroom it's protecting. The source repo already has the
cure — `AGENT_ORIENTATION.md` *reading routes* and the context-pack compiler are **progressive
disclosure** — but the plan doesn't carry that principle into the engine as a *constraint*. Make
"substrate footprint ≤ X% of the window at steady state" an explicit budget and a KPI (§7 A8), and
load by reading-route, not all-at-once.

### 4b. Memory integrity is the real frontier gap

This is the one place I'd insist on a patch before autonomy increases. The handbook confirms the field
*itself* under-addresses memory poisoning and goal-drift recovery — so the plan isn't behind, but a
kit whose defining move is "inject grown memory forward, sometimes self-authored, sometimes from
external issues" must treat memory as an **integrity-sensitive store**: external content quarantined as
data, self-answers provisional (already planned), and a review gate before anything external becomes
durable orientation. Cheap to state now; load-bearing under full autonomy.

---

## 5. Forgotten steps / gaps (additive — none of these block PR 1)

1. **The plan itself isn't in the repo.** Only the two *idea* docs live in `docs/ideas/`; Plan v5 (the
   thing five rounds reviewed) exists in chat. Capture it to `docs/planning/` at execution so this
   report's references resolve and the executor has a single source. *(I deliberately didn't paste the
   full plan verbatim into the repo in this pass — happy to, on your nod; it's a mechanical capture.)*
2. **No related-work section** (§3). Add one; it's the cheapest future-proofing and stops a reviewer
   from saying "this is just fork-and-fill / just claude-mem."
3. **The task-stance `mode` axis** (§2) — the headline addition.
4. **Vocabulary collision** between adoption-"mode" and stance-"mode" (§2.2) — reserve words now.
5. **Name collision** `agent-os/` (§3.1) — rename the working dir now.
6. **Day-1 value isn't guaranteed.** Stage 1 is ~50 sessions of interview before graduation; spec-kit
   /Agent OS give value on session 1. The `guided` pace mitigates, but state an explicit promise: the
   memory + session log + orientation + the `ask`/`analyze` modes must be **useful before the interview
   completes**. Front-load value; don't make the user pay 50 sessions of overhead first.
7. **Decide v1's portability honestly.** The plan says "portable" but is Claude-Code-shaped. Either
   (a) **scope v1 to Claude Code** explicitly and add adapters later (clean, honest, ships faster), or
   (b) build the **adapter seam** from the start (spec-kit/Agent-OS pattern). Don't ship something
   half-portable that breaks on the second tool. My recommendation: **(a)** — be the best Claude Code
   substrate first, generalize once proven (it mirrors the repo's own "prove-in-repo-then-extract").
8. **Schema versioning + migration.** `state.json` and the templates will change as the engine
   evolves; atomic writes + deprecation (already planned) don't cover **migrating an existing project's
   state to a new engine version**. Add a `schema_version` field and a migration step in `init`.
9. **PAT/credential-expiry guard.** The plan flags superbot's silent routine-stall when `ROUTINE_PAT`
   lapses but only "documents" it for the kit. For a *portable* kit a silent dead-loop is a terrible
   first impression — make it a loud, explicit check in `status`/`session-start`.
10. **The real value claim is untested.** The simulation harness proves *mechanics* (slots fill,
    graduation fires, generated docs pass `check_docs`) but not the *thesis*: that an agent **with** the
    substrate outperforms one **without**. Add a golden-task A/B (§7 A4) — it's the only test that
    proves the project worth shipping.

---

## 6. Smaller refinements

- **Make `review` mode the home of the Hermes seam.** The independent-review seam and the `review`
  stance are the same thing from two directions; unify them so there's one concept, not two.
- **Episodic index entries should carry the mode they were produced in** (`mode: build`/`debug`/…).
  Retrieval-by-stance ("show me past *debugging* sessions on the payments path") is high-value and
  free once modes exist.
- **Reflection memory (Round 4 #1) should be mode-aware** — "what worked in *build* vs *analyze*"
  generalizes better than undifferentiated reflections.
- **`whenToUse` per mode enables auto-selection.** Borrow Roo's field so an orchestrator (or the
  SessionStart hook) can *suggest* the right stance from the work order, closing more of the
  "no human steering" loop.
- **Adopt the SOUL.md/AGENTS.md split as a template seam.** Separating *persona/voice* (owner profile,
  user-style block) from *operations* (the checkers, hooks) is an independently-converged pattern and
  maps cleanly onto your owner-profile-vs-engine seam.
- **Ship the question-bank with the curation header Hermes asked for** (already accepted) — and add a
  matching one to the **mode catalog** so day-1 modes don't accrete into sprawl either.

---

## 7. Assumptions to test ourselves (quarantined, per your ask)

These are *hypotheses the plan rests on*, not claims I can verify from sources. Each has a cheap test;
none should gate PR 1, but A4/A7 should gate any **autonomy/promotion-rights increase**.

- **A1 — Tag-index retrieval is enough.** *Assume* topic-tagged `.sessions/` retrieval suffices and we
  never need BM25/embeddings. **Test:** on ~20 real "find the past decision/bug" queries, measure
  hit-rate; only add BM25 (the no-dep scaling path already named) if it falls short.
- **A2 — ~50-session integration converges, and "80% critical slots" tracks real readiness.** **Test:**
  run the simulation + one real project; measure sessions-to-graduation and the **post-graduation
  rule-trip rate** — if graduated projects still trip rules often, the criteria are wrong.
- **A3 — Self-answers (`ASSUMED`) are accurate enough to be useful.** **Test:** track the
  assumption-confirmation rate over real sessions; if low, the fully-autonomous path is unsafe and must
  stay propose-only.
- **A4 — The core thesis: substrate-on beats substrate-off.** **Test:** a golden task in
  `examples/`, run by an agent with vs. without the substrate; compare completion quality, rule-trips,
  and unintended file changes. *This is the experiment that justifies the whole project.*
- **A5 — Tool-scoped modes reduce scope creep.** **Test:** compare unintended-file-change / out-of-scope
  edit rate with vs. without mode tool-scoping on the same tasks.
- **A6 — The single-file stdlib bootstrap actually integrates cleanly with ≥2 host tools.** **Test:**
  `init` into a fresh repo for Claude Code *and* one other (Cursor/Roo); count manual steps required —
  if it's many, §5.7(a) "Claude-Code-first" is the honest scope.
- **A7 — Memory resists adversarial input.** **Test:** plant a poisoned session log / issue comment
  with an embedded instruction; confirm it does **not** propagate into the orientation chain or a
  self-promotion.
- **A8 — The substrate's own context footprint stays bounded.** **Test:** measure injected-token count
  per session at steady state; assert ≤ a chosen budget (e.g. <15% of window) so it never becomes the
  context-rot source it's meant to prevent.

---

## 8. What NOT to change (protect the core)

Five rounds plus this pass converge here — don't let later edits dilute these:

- **Zero-dep, single-file, offline stdlib bootstrap.** It's the moat vs. claude-mem/atomicmemory.
  Keep it a first-class, *tested* artifact (CI from commit 1), not a packaging afterthought.
- **Grown-by-interview, not shipped-as-content.** The differentiator vs. fork-and-fill templates.
- **Promotion-rights ≠ adoption-pace as separate axes.** Correct and load-bearing; the new `mode`
  axis is a *third* dimension, not a merge.
- **Anti-gaming graduation + provisional self-answers + SICA acceptance gate.** The safety spine.
- **Model-agnostic review seam.** The monoculture-breaker; keep it a seam, not a model binding.

---

## 9. Suggested integration into the plan's PRs

Nothing here reshapes PR 1's foundation; it adds one axis and a positioning section.

- **PR 1 (foundation):** reserve the `pace`/`mode` vocabulary (§2.2); rename the working dir off
  `agent-os` (§3.1); land `ask` + `analyze` mode stubs (the two you named) so they work day one; add
  the related-work stub + the "grown, not filled" framing to the README (§3.4); add `schema_version`
  to `state.json` (§5.8); make the PAT/credential check loud (§5.9).
- **PR 2 (modes + triggers + templates + hooks):** the full `engine/modes/` layer + default set + the
  Roo-style schema (§2.5); decide and implement v1 portability scope (§5.7); the substrate context
  budget + progressive disclosure (§4a); re-inject-core-agreement-late (§4 centrifugation).
- **PR 3 (self-maintenance + review seam + polish):** unify `review` mode with the Hermes seam (§6);
  mode-aware episodic index + reflections (§6); memory-integrity/quarantine + checkpoint-restore
  (§4b, §4 cascading); the golden-task A/B harness (§7 A4); wire the loop stop-conditions (§4 METR).

---

## Sources

- Roo Code custom modes (schema, tool/permission groups, built-ins): https://roocodeinc.github.io/Roo-Code/features/custom-modes · https://docs.roocode.com/basic-usage/using-modes · https://docs.roocode.com/features/boomerang-tasks
- Cline Plan/Act vs Claude Code plan mode: https://www.morphllm.com/comparisons/cline-vs-claude-code · https://www.squid-club.com/blog/reverse-engineering-cline-vs-claude-code-a-technical-deep-dive-into-ai-coding-agent-architectures
- Claude Code primitives (skills/subagents/hooks/output styles/plan mode): https://www.tembo.io/blog/claude-code-subagents · https://boringbot.substack.com/p/claude-code-skills-subagents-hooks · https://ofox.ai/blog/claude-code-hooks-subagents-skills-complete-guide-2026/
- GitHub Spec Kit (constitution.md, clarify/specify/plan/tasks): https://github.com/github/spec-kit · https://developer.microsoft.com/blog/spec-driven-development-spec-kit
- Agent OS (buildermethods): https://github.com/buildermethods/agent-os · https://buildermethods.com/agent-os/v2
- 12-factor-agents: https://github.com/humanlayer/12-factor-agents
- AI agent failure-mode handbook (context rot ~25%, centrifugation, tool sprawl/selection, progressive disclosure, subagent isolation, SOUL.md, skills-as-markdown): https://github.com/vasilyevdm/ai-agent-handbook
- Context rot / lost-in-the-middle / sycophancy: https://thenewstack.io/context-is-ai-codings-real-bottleneck-in-2026/ · https://www.birjob.com/blog/ai-coding-agent-doom-loop-2026
- Goal drift (`GD_actions`/`GD_inaction`), scope creep, cascading errors, proxy-goal convergence: https://zylos.ai/research/2026-04-03-goal-persistence-drift-long-horizon-ai-agents · https://arxiv.org/html/2605.01604 · https://nimblebrain.ai/why-ai-fails/agent-governance/agent-failure-modes/
- Memory / template neighbors: claude-mem https://github.com/thedotmack/claude-mem · atomicmemory https://github.com/atomicstrata/atomicmemory · gitagent https://github.com/open-gitagent/gitagent · letta agent-file https://github.com/letta-ai/agent-file · fork-and-fill template https://github.com/florian101010/awesome-agentic-AI-coding-template
