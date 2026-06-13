# Session — Independent revision report for the portable substrate-kit plan

> **Status:** `complete` — produced an independent revision/complement of the (then-"Plan v5")
> portable agent-substrate extraction plan and shipped it as **PR #788 (merged via auto-merge)**:
> `docs/planning/portable-agent-substrate-revision-2026-06-13.md`. Closing discovery: the plan has
> since **graduated to an approved, executing kit** (`substrate-kit/`, PRs #789/#793) and this
> report's recommendations **landed in it** — so the close is a log, not new artifacts.

## What this session did

The maintainer asked for: a thorough GitHub + web prior-art sweep (own repo + public), personal
analysis of the plan, an explicit check for missing "skills/modes" (question/analysis/etc.), an
AI-weakness audit, forgotten steps — packaged as a report that **complements (not fights)** the plan,
with testable assumptions grouped separately. Delivered exactly that (PR #788, merged).

Headline finding: the plan had **three control axes (pace · promotion-rights · stage) but no
task-stance axis** — recommended a first-class, **tool-scoped** "mode/stance" layer (Roo-style schema:
`roleDefinition` + `whenToUse` + scoped tool `groups` + `fileRegex`), flagged the in-plan "mode" word
overload, and surfaced a name collision (`agent-os` ↔ `buildermethods/agent-os` & others). Grounded in:
Roo/Cline/Claude-Code mode mechanics; spec-kit (`constitution.md` + `/clarify`), Agent OS, GSD
(spec-driven neighbors); claude-mem/atomicmemory/gitagent/letta `.af` (memory neighbors); the
fork-and-fill template; 12-factor-agents; the 2026 AI-agent failure handbook (context rot ~25% fill,
instruction centrifugation, tool-selection 43%→14%, sub-agent isolation 90.2%).

## 🔎 Closing discovery — the recommendations already landed (no orphan)

Mid-"continue", synced `main` and found the idea **graduated to an approved plan**
(`docs/planning/portable-substrate-kit-extraction-2026-06-13.md`, #789) with **PR 1a already built**
(`substrate-kit/src/engine/{cli,lib/{config,state,atomicio,guardrail}}.py` + tests, green; #793). The
executing plan **already incorporates this report's core asks**:

- §3b **"Task-stance modes — the fourth axis"** (Round 7, owner-decided) — `engine/stances/`
  (`stances.py` + `stances.yml`), a `stance` CLI, `state.json.stance`, scoped tools + reading-route
  per stance, a PreToolUse out-of-stance warning; lands PR 2, stubbed PR 1. Extended into a full
  **stance · skill · persona** capability layer with a precedence model.
- The **rename** off `agent-os` → `substrate-kit/` (my §3.1) and the **"stance" vocabulary** that
  resolves the "mode" overload (my §2.2) — both adopted.

So my offered next steps (capture Plan v5; draft a modes spec) were **already done, better** — I
deliberately created **no duplicate docs**. The revision report stays the durable companion.

## 📌 For the executor — report contributions NOT yet named in the kit's plan

These are the parts of the revision report the executing plan does not yet appear to cover; surface
them when the kit reaches PR 2/3:

- **Memory integrity (the report's one 🔴):** the substrate forward-injects grown memory and ingests
  external text (issues / PR comments / web). Treat ingested external content as **data, not
  instructions**; quarantine it before anything can enter the orientation chain. (Forward-injected
  memory is a poisoning vector — the field itself under-addresses it.)
- **Substrate context budget:** it injects orientation + memory + reflections + stance every session;
  budget it (≤ ~15% of window) and load by reading-route — else the thing built to fight context rot
  becomes its source (rot measurable from ~25% fill).
- **A4 golden-task A/B:** prove substrate-on beats substrate-off. The sim harness proves *mechanics*
  (slots fill, graduation fires); it does not prove the *thesis*. This is the experiment that
  justifies the project.

## 💡 Session idea (Q-0089)

**Stance-conformance assertion in the kit's `simulate.py`.** Turn revision-report assumption A5
("tool-scoped stances reduce scope creep") into a standing test: drive a scripted session in each
stance and assert **zero out-of-stance writes** (no file edit while `stance == review`/`ask`),
emitting an "out-of-stance action rate" KPI. It makes the fourth axis *measurably* safety-bearing from
PR 2 — not just declared — and is the cheapest proof that stances earn their place. Small, additive,
sits in the harness that already exists.

## ⟲ Previous-session review (Q-0102)

Reviewing the **substrate-kit graduation + PR-1a line (#789/#793)**: it did the hard thing well — took
an idea to an **owner-approved plan via ~10 review rounds** and shipped a **green, contract-locked
skeleton** (atomic-write state, a kit-root guardrail, bootstrap build + tests) instead of a sprawling
first PR; and it genuinely **absorbed cross-line input** (the task-stance axis, the rename, the
vocabulary) rather than plowing its own furrow. **What was risky:** that absorption happened while a
*separate* line (this one) was independently writing a revision of the same plan — the two converged
only because the owner routed between them, not because the system signalled the overlap.
**System improvement:** a planning doc under active execution should carry a **standardized, visible
`EXECUTING — entry PRs #x; route additions as PR-N inputs` banner** at the top, so a parallel
agent/reviewer instantly sees it's live and pushes contributions *forward* instead of risking a
duplicate or a late collision. (The kit's own §3b gives *projects* this kind of live-state signal for
tasks; the *workflow* deserves the same for plans.)

## Doc audit (Q-0104)

- Revision report reachable (linked from `docs/ideas/portable-agent-memory-package-2026-06-12.md`,
  which now also carries the "GRADUATED" banner to the approved plan); `check_docs --strict` green.
- **No duplicate plan/modes docs created** (superseded by #789/#793) — drift avoided by *not* writing.
- Idea-backlog health on this thread: the portable-substrate idea graduated to an executing plan; the
  one new ASK still open from the report is the memory-integrity patch (above), routed to the executor.
