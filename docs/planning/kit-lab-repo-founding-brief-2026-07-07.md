# Founding brief — the substrate-kit repo + self-improvement lab (dedicated Fable session)

> **Status:** `plan` — the launch brief + paste-ready prompt for **program session 2 of 3**
> (Q-0252): a dedicated **Claude Fable 5, `/effort ultracode`** research-and-plan session whose
> deliverable is the **executable founding plan** for the extracted `substrate-kit` repo and the
> self-improvement lab that runs in it. Launch index:
> [`program-three-sessions-launch-index-2026-07-07.md`](program-three-sessions-launch-index-2026-07-07.md).
> Governance: **Q-0241** (never-wait, decide-and-flag) · **Q-0247** (extraction rides the
> kickoff; this session plans what the repo *becomes* after) · **Q-0248/Q-0249** (model-allocation
> discipline; budget observe-first).

## 1. Reading route (in order)

1. `.claude/CLAUDE.md` → `docs/collaboration-model.md` (§ "Why this system exists" — the lab IS
   this section made literal) → `docs/current-state.md` S3 row → `.session-journal.md` ⚡.
2. **The program frame:** [`../ideas/multi-repo-program-kit-lab-trading-2026-07-07.md`](../ideas/multi-repo-program-kit-lab-trading-2026-07-07.md)
   Part 2 (the lab, strengthened + owner-ratified) — this brief's §2 restates its mandate rows.
3. **The kit itself:** `substrate-kit/` in full (engine, `dist/bootstrap.py`, the 432-test suite,
   its own docs) — you are planning this code's future home and curriculum.
4. **The honest evidence base:** [`phase-2.5-cold-start-report-2026-07-07.md`](phase-2.5-cold-start-report-2026-07-07.md)
   (+ [companion D](rebuild-phase-2.5-procedure-2026-07-06.md)) — the unproven cold-start benefit
   is the lab's founding challenge; do not plan around it, plan *at* it.
5. **The vision lineage:** [`../ideas/autonomous-improvement-loop-vision-2026-06-12.md`](../ideas/autonomous-improvement-loop-vision-2026-06-12.md)
   + [`../ideas/portable-substrate-kit-idea (README index entry)`](../ideas/README.md) — what the
   owner has consistently wanted this to be.
6. **Coordination surfaces:** the [kickoff brief](rebuild-kickoff-steps-6-8-brief-2026-07-07.md)
   (the extraction + the program-governance-home fork it decides) · router **Q-0245…Q-0249**.

## 2. The mandate — research deeply, then produce ONE executable founding plan

Research lanes (fan out; source wins over every doc, Q-0120):

1. **Kit internals audit** — what exists, what is silently superbot-coupled (paths, assumptions,
   vocabulary) and must generalize before consumers #2/#3 adopt; what the adopt/upgrade path
   guarantees today vs what a *versioned multi-consumer release discipline* needs (semver? pinned
   dist? changelog contract? rollback path?).
2. **The benchmark suite** — the lab's fitness functions, specified to runnable depth:
   (a) the companion-D cold-start A/B as a standing, repeatable routine (paired sessions on
   throwaway repos; judge rubric; artifact home); (b) the **Q-0248 model-allocation paired A/Bs**
   per task class (agent plane) — the lab owns this program-wide dataset; (c) guard-fire /
   false-positive telemetry; (d) the **ideas-that-ship-and-survive** acceptance metric wired to
   the idea lifecycle. Define each metric's exact computation, its data source, and where results
   live.
3. **The lab loop** — the routine architecture: what fires on what cadence, what each firing
   reads (friction-report inbox from consumer repos, benchmark trends, its own backlog), what it
   may build freely vs flag (Q-0241 shape: reversible + budgeted + scoped credentials +
   cold-session self-measurement — a warm session never grades its own substrate).
4. **Work surfaces** — specify the provisioning: its own test bot token (Galaxy-Bot pattern),
   its own Railway project (telemetry per Q-0249, no caps yet), its first deployable website —
   **recommended first site: the program console** (the owner's one-glance page: run reports,
   ⚑ flags, spend/model telemetry, kit A/B trends, the port-progress dashboard when gate 5
   exists, trading state later — merges the A-6 dashboard fork). Decide and flag the first
   surface if you disagree.
5. **The governance home** — per the kickoff brief's fork: the kit repo carries the
   program-level canon (collaboration model, decision-authority, program-wide rulings
   Q-0240/41/47/48/49 class) as templates + canonical copies; per-repo routers stay local.
   Specify the file layout and the sync/citation rule so program law is never duplicated-and-
   drifted.
6. **The friction-report protocol** — the consumer→lab inbound contract (what a consumer files,
   where, in what shape) and the lab→consumer outbound contract (release notes, upgrade PRs,
   adoption diffs). Make both mechanical enough that a routine can run them.

**Output artifacts:** (1) `docs/planning/kit-lab-founding-plan-<date>.md` — the executable plan
(PR-arc structure, definition of done for lab v1, the benchmark specs, the routine definitions,
the provisioning checklist with owner-input items marked); (2) a decisions log (Q-0240 style,
every call ⚑-flagged); (3) router Q-blocks only for genuine product forks. The plan lives in THIS
repo until the kit repo exists (the kickoff creates it), then travels.

## 3. What NOT to do

- Don't perform the extraction or create repos (the kickoff session owns that, Q-0247).
- Don't re-run the Phase-2.5 A/B in this session — *specify* its routine form.
- Don't design the trading platform (session 3) — only the kit surfaces it will consume.
- Don't plan a fleet: lab v1 is ONE loop + the benchmark + the inbox (rail before scale).

## 4. Paste-ready prompt

> You are a **Claude Fable 5** session at **`/effort ultracode`** on the SuperBot repo. Read
> `docs/planning/kit-lab-repo-founding-brief-2026-07-07.md` — it is your full brief and reading
> route. Research the substrate-kit deeply, then produce the executable founding plan for the
> extracted kit repo + the self-improvement lab (`docs/planning/kit-lab-founding-plan-<date>.md`):
> the multi-consumer release discipline, the benchmark suite specified to runnable depth (the
> cold-start A/B routine, the Q-0248 model-allocation dataset, guard telemetry, the
> ideas-that-ship metric), the lab's routine loop with its Q-0241-shaped rails, the work-surface
> provisioning (recommended first website: the program console), the program-governance home
> layout, and the friction-report protocol. Decide-and-flag everything reversible; never wait
> for me; silence = consent.
