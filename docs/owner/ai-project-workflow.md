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

**Where answers live (Q-0210, 2026-06-28).** The router is the **single canonical, append-only Q-block
ledger** — a decision keeps its `Q-0NNN` block here forever; numbers are never moved. That is what keeps
the **~9,000 plain-text `Q-0XXX` references across the repo** resolvable, so we do **not** physically
re-home answers to scattered docs (that would orphan the anchor). Instead: (1) the **`Home:` line** (§7)
routes each durable *conclusion* to its real home — the plan / folio / `CLAUDE.md` is where agents *read*
the decision, the Q-block is the *provenance*; and (2) **size** is managed by **archiving** old, fully
answered + routed Q-blocks to **`docs/owner/maintainer-question-router-archive.md`** (newest kept here,
oldest archived, with a pointer) — mirroring the proven `current-state.md` → `current-state-archive.md`
split. Because references are plain text, an archived `Q-0XXX` stays grep-resolvable (the lone
`#q-0017` anchor link is the only thing to fix if Q-0017 is ever archived). **Archiving is a
reconciliation-pass (Q-0107) job**, not ad hoc — the same pass that already trims `current-state`.

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
- **Merge your own PR when done — yourself (owner grant Q-0084, 2026-06-10).** Don't
  leave a finished PR open for the owner: sync main, get CI green on the final head,
  merge (merge-commit), and the *next* agent starts from your work instead of
  conflicting with it. Stale open PRs are the conflict window this whole section
  exists to fight; prompt merges are what let the owner run more agents in parallel.
- **Skip the standing backlog-grooming secondary task in a parallel session** — two agents
  grooming `docs/ideas/` simultaneously is an avoidable collision on a shared tracker;
  the next solo session picks it back up.
- **Name the parallel partner in the PR body** ("Agent N is concurrently working on
  Lane M; this PR avoids …") so the reviewer knows two PRs are siblings, not rivals.
- **Do not add coordination machinery.** The observed total overhead was one mechanical
  merge; any session-ledger / lock protocol would cost more than it saves. The
  per-section ownership table above + the rules here are sufficient.

### Cross-cutting ledger discipline (added 2026-06-10 — the recurring-conflict fix)

Three parallel-merge conflicts in one day (#655×#653, #655×#656, #658×#657) shared
one root cause: **`docs/current-state.md`'s ▶ Next-action was a single mega-line
every session had to edit.** Git merges by line — a shared line is a guaranteed
conflict; a shared *file* with per-lane lines is not. (The journal already solved
its own instance of this class by moving the Session Log to per-session
`.sessions/` files, 2026-06-07; the ledgers were the remaining hotspot.) The
standing rules:

1. **The ▶ Next-action block is per-lane bullets — edit ONLY your lane's bullet.**
   One bullet per lane (consolidated batches · BTD6 · gated · the numbered lane
   list below it). A session that didn't work a lane never touches that lane's
   bullet. Two sessions in different lanes now auto-merge.
2. **Session narrative goes in `.sessions/<date>-<slug>.md` + the PR body — never
   in the ledger.** The ledger bullet is one line of *state* ("X shipped in #NNN;
   next: Y"), not the story. The `.sessions/` file is the agent-owned,
   conflict-free write-ahead record (each agent already writes its own).
3. **Ledger distribution rides the existing REVIEW cadence** (journal protocol,
   every ~3–5 sessions): the reviewing session reconciles the ledger bullets +
   `roadmap.md` rows against live GitHub and the recent `.sessions/` files —
   exactly the "session files get distributed into the right docs every few
   sessions" model, mapped onto a step that already exists. Between reviews, a
   slightly-stale ledger is by design ("verify open PRs against live GitHub" is
   already the doc's own rule).
4. **`docs/roadmap.md`: same discipline** — edit only your area's section/row;
   the at-a-glance table row for another lane is not yours to refresh.
5. **When a conflict still lands** (same-lane parallel work, or both sides edited
   the thin header), resolution stays **UNION, second-to-merge reconciles**
   (Q-0060) — now a one-bullet merge instead of a mega-line rewrite.

## 10. Session lifecycle & continuation — the self-driving foundation (Q-0088)

> **Status:** designed 2026-06-10; **dispatch mechanism re-decided 2026-06-12 (Q-0115):**
> Stage 0's separate GitHub-Action dispatcher is **folded into the #742 Claude Code
> Routine bridge** (`operations/hermes-dispatch-bridge.md`) — the bounded-session
> *protocol* now **activates once the Routine is wired + calibrated** (the runbook's ⬜
> steps), not "when Stage 0 lands". Until then, the context-budget guidance and the
> no-unguided-PRs rule apply as journal guidance.

**Why (owner-stated, Q-0088):** two observed failure modes of unbounded
sessions — (1) *runaway tails*: a session the owner believed finished kept
producing unguided PRs (one built a duplicate function — the #678-class
collision); (2) *long-context degradation*: output quality noticeably drops
past ~700–800K context. The owner's target operating model: he adds ideas and
strict function/UX guidelines; the system handles the rest in **bounded,
chained** sessions.

**The bounded-session protocol (once active):**

1. A session ships **2–3 complete slices** (or one large one) from the
   standing queue (`current-state` ▶ Next action / roadmap session queue /
   its prompt), plus the standing END duties (ledgers, session log, grooming
   pass when capacity remains). Not just one — a finished session often lands
   at only 200–300K context, so there is usually room for more (owner
   observation, Q-0144).
2. **~700K is the ceiling, not 1M (Q-0144).** Work stays good and structured up
   to roughly 700K tokens of the 1M window; that, not 1M, is the practical
   budget. Keep advancing while well under it and quality holds; approaching it
   mid-task, finish the task then hand off — never start the next one.
3. **No unguided PRs past declared scope.** New work discovered late goes
   into the **handoff** (roadmap queue / ▶ Next action / an idea file), not
   into the session. A webhook/babysit loop ends when its PR merges.
4. **The handoff baton is what we already maintain** — `.sessions/` log +
   `current-state` ▶ Next action + the roadmap session queue. The protocol
   adds only the discipline that every session *ends by sharpening the baton*
   (explicit next-2-tasks recommendation), which most sessions already do.

**The continuation mechanism (staged):**

- **Stage 0 — one-click continuation** *(superseded 2026-06-12, Q-0115: folded into the
  Routine bridge — the one-click run is now a Routine fire, no GH Action is built; kept
  for design history)*: a `workflow_dispatch` GitHub Action
  that boots a **fresh** Claude Code session (fresh context — the fix for the
  700K problem) with a fixed prompt: *"Read the orientation chain and the
  newest handoff; execute the recommended next ~2 tasks under the bounded
  protocol."* No schedule, no surprise spend — the owner presses Run.
  Requires (owner-side): the Anthropic API key as a repo Actions secret and a
  per-run budget choice. Build is queued on the roadmap session queue.
  *(Owner-proposed interim variant, 2026-06-11: Samsung Routines touch-macros
  on his phone — scheduled taps pressing send / switching chats hourly.
  Viable as a zero-infra experiment, but two flaws keep it interim: the phone
  is held hostage awake+unlocked all night, and unless the macro opens a NEW
  chat each cycle it extends one conversation's context — recreating the
  exact 700K degradation this protocol exists to avoid. The Action supersedes
  it.)*

## 11. Model allocation — spend intelligence where ambiguity lives (2026-06-11)

> **Why this exists:** the owner ran near-200% of weekly plan limits for
> weeks (2–4 parallel agents, top-tier models on everything) — unsustainable
> by his own numbers. The fix is not "less work"; it's matching model tier to
> task shape. **This repo's whole scaffolding (orientation chain, context
> packs, turn-key plans, context maps, CI mirror, hooks) exists precisely to
> lower the intelligence floor a session needs** — let it pay for itself.

**The split, by task shape (not by lane):**

- **Fable-class (premium, 1M context) — ~1–2 sessions/week, never parallel
  with itself:** vision/posture/decision conversations; writing the *plans*
  other models execute; architecture calls; unknown-cause debugging;
  reviewing/auditing other agents' merged work; genuinely huge-context
  marathons. **Not** for grinding through an already-written plan.
- **Opus — the execution workhorse:** planned `disbot/` PRs (risky runtime
  code with a clear plan), typical root-cause bug fixes, mid-size refactors,
  parallel lane execution. Fast mode for snappier turnaround.
- **Sonnet — the volume tier (underused today):** turn-key recipe execution
  (the P0C precedent: context_map + grep + recipe carried a whole session),
  docs/ledger sessions, test-writing against specs, grooming passes, CI
  babysitting, caretaker/Stage-1 probe duties. The "barely enough context to
  read my documents" objection is solved by **pointing Sonnet at the
  generated context packs** (`docs/agent/generated/`, built for exactly
  this) + one turn-key plan — not by avoiding Sonnet.
- **Haiku — mechanical chores & cheap subagents:** single-file mechanical
  changes, summarization-shaped subtasks.

**Four standing levers (any session, any model):**

1. **Plan→execute flip:** premium models write plans; cheaper models execute
   them. A plan good enough for Sonnet is the *quality bar for plans*.
2. **Bounded sessions are also the cost fix** (§10): the 700K quality cliff
   and the burn rate are the same curve — wrap early, chain fresh.
3. **Subagent model override:** research/search/scout subagents default to
   Sonnet or Haiku (the Agent tool takes a `model` parameter) — a scout's
   report reads the same regardless of which tier fetched the pages.
4. **Parallel discipline:** parallel lanes run on Opus/Sonnet; at most one
   premium session at a time, and only when its distinct value is needed.

**Owner-stated context (2026-06-11, for calibration):** Max x20 plan; ~200%
weekly usage on x5 for 3 weeks (grace refreshes granted); 80% of the x20
week consumed in ~1.5 days after the Fable release with everything pointed
at the top tier. Target: fit inside the weekly limit without shrinking
output — the split above plus the levers is the path.
- **Stage 1 — the scheduled caretaker:** the same workflow on a cron (e.g.
  nightly): smoke probes on the test bot, eval-checklist automatable rows,
  one grooming move, small fixes merged green, morning report. Promotes only
  after Stage 0 has produced several clean runs (router-granted, the Q-0048
  tier pattern).
- **Already true today (no build needed):** Railway auto-deploys every merge
  (`operations/production-deployment.md`), Q-0084 lets agents merge green
  work, and `.sessions/` handoffs exist — Stage 0 is the only missing link in
  a complete loop: *handoff → fresh session → bounded work → green merge →
  auto-deploy → sharpened handoff*.

## 12. The autonomous review/approval loop (Q-0113 / Q-0114, 2026-06-12)

> **Status:** the **seams** are built (this section's tools/skills exist); the
> loop **closes** when the maintainer wires the Routine + `/fire` token
> (`operations/hermes-dispatch-bridge.md`, the ⬜ steps). Until then the same
> seams are usable manually (dispatch degrades to a printed work order; review
> runs on any plan/PR by hand).

**Why:** §10/§11 are the *chaining + cost* half of the self-driving loop. This
section is the *correctness + autonomy-boundary* half: how invented work is
reviewed by a different mind and how far an unattended run may go on its own.
The north-star is `docs/ideas/autonomous-improvement-loop-vision-2026-06-12.md`;
this section is the binding subset that is actually wired.

**The three seams (built 2026-06-12):**

1. **Independent review — `superbot-review` (Hermes skill).** A *non-Claude*
   model critiques a plan or a PR diff. In a Claude-only loop every author and
   reviewer share the same blind spots (a monoculture); a different mind's
   dissent is worth more than another Claude pass. Output includes a
   plain-language **maintainer summary** for the approve/deny hand-off.
2. **Phase gate — `scripts/check_phase_gate.py`.** Machine-readable
   *fix-phase vs. invent-phase*. Invent-phase requires **zero OPEN bugs**
   (bug-book) **and zero `Not Done` rows** (readiness maps). It enforces the
   maintainer's order: bugs/UX/correctness first; agent-*originated* features
   only once everything works.
3. **Dispatch bridge — `superbot-dispatch` (Hermes skill) +
   `operations/hermes-dispatch-bridge.md`.** Hermes assembles a work order and
   fires a Claude Code Routine (read-only: it sends text; Claude Code mutates
   under CI). The routine's **saved prompt** is where the gates below live on
   the build side.

**The two gates (owner decisions):**

- **Merge gate (Q-0113) — full self-merge on green CI.** Routine PRs self-merge
  on green CI exactly as interactive sessions do (Q-0084 extended to unattended
  runs), bounded by: CI required-green on the final head, `claude/`-only pushes,
  and the feature carve-out below. Merge ≠ deploy.
- **Human approve/deny gate (Q-0114) — agent-originated *features* only.** A
  feature an agent invents is built (only in invent-phase), opened as a PR, and
  **held** for the maintainer's approve/deny — Hermes explains it in plain
  language. Bug/UX/docs/correctness work flows freely under the merge gate.

**The closed loop:** *idea/diagnosis → Hermes orients + classifies + checks the
phase gate → dispatch → routine builds + tests → (fix/ux/docs/correctness)
self-merge on green **or** (feature) open + hold for approve/deny → Hermes
reports + `superbot-review` on the diff → maintainer verdict routes back.*

**Calibration discipline (Q-0105):** the reviewer and the dispatch bridge are
**unverified convenience infrastructure** until proven — confirm the reviewer
catches known-planted issues and the dispatch gate behaves on a tiny known fix
before trusting either unattended; tear them down if they prove unreliable over
multiple sessions rather than working around them.
