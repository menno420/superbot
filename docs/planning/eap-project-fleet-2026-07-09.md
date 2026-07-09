# EAP Project fleet — broad capability + model-comparison test plan (2026-07-09)

> **Status:** `plan` — prep artifact for a **dedicated next session** that creates the repos and
> launches this fleet. Not executed yet; this doc is the refined plan + ready-to-paste materials
> so that session is pure execution.
> **Provenance:** owner directive 2026-07-09 (directing-session chat) — run several Claude Code
> Projects in parallel across varied domains as an extensive capability eval, plus a dedicated
> model-comparison sub-experiment, plus the already-planned substrate-kit self-improvement lab.
> **Urgency:** the free EAP window closes **Friday 2026-07-10** — the evaluation guidebook's
> evidence-package deadline is that same day
> ([`projects-eap-evaluation-guidebook-2026-07-07.md`](projects-eap-evaluation-guidebook-2026-07-07.md)
> §5). Today (Thursday) is the last day to get autonomous fleet runtime in *before* that
> deadline, though nothing here stops mattering after — the collaboration goal outlives the free
> window (same doc §5).

## Why a fleet, not one more Project

Two of the three running Projects (rebuild, websites) are both **SuperBot-domain, agent-coding
tasks** — real signal, but narrow. Anthropic's own seven-axis feedback frame (use-case fit,
coordinator judgment, reliability/completion, memory, proactivity, routines/scheduling, sidebar
states) is much better served by variety: different domains stress different failure modes, and
a **model-comparison** sub-experiment is the one thing no single Project can answer — Anthropic
flagged that default settings are tuned around the new default model (Opus 4.8, was Fable 5),
which is itself worth verifying empirically rather than taking on faith.

## The fleet — 7 domain-breadth Projects

Each row: target repo (new, owner-creates next session, empty is fine — same Contents-API seed
pattern as `websites`), the task brief, the EAP axis it's best positioned to stress, suggested
model. All are genuinely useful or genuinely interesting outputs, not throwaway busywork — a
Project that produces something nobody wants is a worse eval than one that doesn't, per the
guidebook's own integrity rule against staging observations.

| # | Domain | Repo | Task brief | Primary axis | Suggested model |
|---|---|---|---|---|---|
| 1 | **Games** | `game-lab` | Design and ship one complete, polished, playable browser game from scratch — your own concept, but finished: real art/UX pass, no placeholder assets, deployed and playable at a URL by end of run. | reliability/completion (does "finished" actually mean finished) | Opus 4.8 |
| 2 | **Bots (non-Discord domain)** | `bot-lab` | Build and deploy a real, useful bot on a *different* platform than Discord (Telegram, or a fresh single-purpose Discord bot unrelated to SuperBot's mechanics) — something a stranger could add and get value from day one. | use-case fit (transfers bot-building competence without SuperBot's scaffolding to lean on) | Sonnet 5 |
| 3 | **Research** | `research-lab` | Pick one genuinely useful, well-scoped research question (your choice — a live, evolving space, e.g. "state of AI coding-agent evals in 2026" or a competitive analysis relevant to SuperBot) and produce a rigorously cited, continuously-updated report repo over the full run. | coordinator judgment (source discipline, synthesis quality, unsupervised for a full day) | Fable 5 |
| 4 | **Coding** *(anchors the model-comparison set — see below)* | `codetool-lab-{model}` | Design and ship a real, general-purpose open-source-quality CLI tool or library solving a genuine problem — tests, docs, CI, published — deliberately unrelated to SuperBot so there's no borrowed scaffolding. | reliability/completion + the model-comparison axis itself | 3 parallel runs — see below |
| 5 | **Design** | `design-lab` | Build a polished, standalone design system + a set of example interfaces judged purely on visual/UX craft (spirit of `botsite/ds/`, but a clean-room build, not a fork). | use-case fit for a taste-heavy, less-verifiable task | Opus 4.8 |
| 6 | **Something you'd actually use** | `personal-lab` | A real tool solving an actual friction point in your own day-to-day — **name the specific friction next session** (I don't have enough of your daily context to pick one honestly; picking blind would risk exactly the "staged observation" problem the guidebook warns against). | proactivity (does it ask the right clarifying questions, or guess and drift) | Sonnet 5 |
| 7 | **Deliberately open-ended** | `wildcard-lab` | Minimal brief on purpose: "build something interesting and useful, your own judgment, your own domain." The contrast case against every tightly-specified brief above and against the rebuild Project's exhaustive spec. | proactivity + coordinator judgment under maximum freedom | Fable 5 |

## The model-comparison sub-experiment

Row 4 (coding) runs **three times in parallel**, identical brief, three repos
(`codetool-lab-fable5`, `codetool-lab-opus48`, `codetool-lab-sonnet5`), one per model. Coding was
picked as the anchor because its output is the most objectively comparable across models — tests
pass or don't, the tool works or doesn't, docs are complete or aren't — versus design or research
where taste dominates and a model difference is harder to isolate from judgment-call variance.

**Comparison protocol:**
- Identical Custom Instructions + startup prompt across all three (the shared template below,
  with only the repo name swapped) — the *only* variable is the model.
- Judge on: did it finish (reliability/completion), how many owner-only stalls it hit and how it
  handled them (coordinator judgment), whether the status reports were accurate vs. inflated
  (the audit checklist's spec-correctness lens — [`rebuild-project-audit-checklist-2026-07-08.md`](rebuild-project-audit-checklist-2026-07-08.md)
  applies here unchanged), and raw output quality (a same-brief code review across the three
  repos at end of run).
- If you want a second comparable pair, **design** (row 5) is the next-best anchor (visually
  diffable side-by-side) — defer that expansion to next session's capacity/appetite rather than
  committing to it now.

## The substrate-kit self-improvement Project — already fully planned

This is **not new planning** — [`kit-lab-founding-plan-2026-07-07.md`](kit-lab-founding-plan-2026-07-07.md)
is a complete, decided (KF-1…KF-11) founding plan for exactly this: a dedicated Project working
strictly on `substrate-kit` itself (releases, benchmarks B1–B4, the daily lab loop, program-law
home, friction protocol). Its own numbering calls this **"program session 4"** and its kickoff
precondition — the kit repo existing — is already satisfied. Next session's job for this one is
narrower than the other seven: work through its **§7.2 provisioning checklist (P1–P13)**, most of
which is quick owner clicks (Railway project, a scoped PAT, repo settings), then launch it as its
own Project targeting `menno420/substrate-kit` directly (no new repo needed). Read that plan's §6
(the lab loop) and §7 before launching — it already answers most of what would otherwise need
deciding fresh.

## Shared Custom Instructions template (fill in `{REPO}` / `{TASK_BRIEF}` per Project)

```
Run autonomously for at least a full day (through the end of the current free evaluation
window if that's sooner) and produce real, finished, working results — not scaffolding, not a
plan document. The deliverable is something that actually works and that a stranger could use
or inspect, not a description of what would exist.

Work in menno420/{REPO} (seeded with a README; normal git push works from the start).

YOUR TASK: {TASK_BRIEF}

Pick your own stack, structure, and defaults — decide and flag, never wait; note your choices as
you go rather than asking first, except for anything genuinely destructive or irreversible
outside this repo, which always asks first.

If this task needs live infrastructure: your container carries RAILWAY_API_KEY (full account
access — use this) AND ALSO RAILWAY_PROJECT_ID / RAILWAY_SERVICE_ID / RAILWAY_ENVIRONMENT_ID,
which are PRE-SET TO THE PRODUCTION SUPERBOT PROJECT — RAILWAY_SERVICE_ID resolves to the live
bot. Never pass those three ambient IDs to any Railway call. Use RAILWAY_API_KEY alone to create
your own fresh project via projectCreate, then use only those new IDs from that point on. Never
call a delete/restore/destructive mutation against anything outside your own new project, and
never against anything — even your own — without stating exactly what you're about to delete and
getting an explicit owner go-ahead first.

FORWARD-ONLY GIT: fresh branch → PR → squash-merge; never force-push, delete a remote branch, or
amend a pushed commit.

Send a status report at each real milestone. In your final report (or if you hit the runtime
limit first), include a short honest note on anything that surprised you, blocked you, or went
unusually well while working in this environment — friction and delight are both useful data,
not just wins.
```

Startup prompt is just the task brief in first-person, one paragraph, same shape as the websites
Project's — draft these fresh next session once repo names are confirmed, not worth pre-writing
seven near-identical variants here.

## Next-session execution checklist

1. **Confirm/trim the list** — 7 domain Projects + 3 model-comparison variants + 1 kit-lab
   Project is 11 total running Projects. That's a lot to monitor even with light owner touch —
   decide next session whether to launch all 11 at once or stagger (e.g. kit-lab + the 3-model
   coding comparison first, since those are the most fully specified, then the rest as capacity
   allows).
2. **Create repos** — one empty (or auto-init) repo per Project (10 new; `substrate-kit` already
   exists for the lab). Same pattern as `websites`: create, I seed the README via Contents API if
   `git push` first-publish would otherwise wall it.
3. **Provision the kit-lab Project's P1–P13 checklist** (mostly quick, see the founding plan §7.2)
   before or alongside the others — it's the most "ready" of the eleven.
4. **Create each Project** in Claude Code, repo list = its own target repo (write) + read access
   to whatever source repos its brief needs (most need none beyond their own).
5. **Paste Custom Instructions + startup prompt** per Project, filled from the shared template.
6. **Pick a model per Project** per the suggestions table (swap freely — the suggestions spread
   deliberately across Fable 5 / Opus 4.8 / Sonnet 5 rather than defaulting all to one).
7. Come back to this directing session (or a successor) to start tracking status reports against
   the audit checklist, same as the rebuild and websites Projects — the checklist's two axes
   apply unchanged to every fleet member.

## Feeding this into the Friday evidence package

Each Project's final-report friction/delight notes (per the shared template's last paragraph) are
the raw material — pull them into
[`projects-eap-evaluation-log.md`](projects-eap-evaluation-log.md) as dated entries against the
seven axes once they arrive, same integrity rules as the guidebook already sets (observed vs.
inferred, log both directions, never stage). The model-comparison results in particular are
exactly the kind of "confirm, contradict, or deepen" evidence §3 of the guidebook asks for on the
**coordinator judgment** axis.
