# /plan-band

The dedicated planning session the Q-0164 backlog flag asks for: assess how much buildable work is
left and promote ideas -> plans to fill the next *full band*. Makes "we're low on plans -> plan more"
a one-command session.

## What this does

Runs the **plan-the-next-full-band** half of the Q-0107 reconciliation pass (the procedure in
`docs/operations/autonomous-routines.md` § "Routine: superbot docs reconciliation", STEP 2 "PLAN THE
NEXT FULL BAND") on its own: review the executable plans, measure buildable depth against the 30-PR
cadence (Q-0134), and — if short — promote the best owner-aligned ideas into fully complete plans, or
raise the `⚠️ PLAN BACKLOG THIN` flag (Q-0164). This is the idea->plan->reality step with no extra
owner planning. Wrapper around the routine's saved prompt, not new policy.

> This is **docs/planning only** — no `disbot/` runtime code. It is the planning lane; building the
> plans is a separate (dispatch / session) step.

## Invocation

```
/plan-band
```

No arguments.

## Instructions for Claude

### Step 1 — measure buildable depth (Q-0144 + Q-0164)

Review the executable plans (`docs/planning/*`, `docs/roadmap.md`): **how much real, *buildable* work
is left?** The bar is **DEPTH >= the cadence** — leave enough genuine buildable work to reach the
NEXT reconciliation pass (~30 PRs of capacity), as larger multi-PR initiatives **or** more slices,
whichever keeps each a real change. (The old "~9 PRs" horizon drained the queue ~20 PRs before each
refill — that gap is exactly what Q-0164 fixed.) The `scripts/check_plan_backlog.py` signal, where
present, turns this judgment into a number.

### Step 2 — branch by what you find

- **Enough work remains** -> plan the next band into the band-planning doc, highest-value first,
  modular, each slice a meaningful change. **Do NOT pad to 30 with filler.**
- **NOT enough buildable work remains** -> this is the **idea->plan step**: review `docs/ideas/`
  (dedup-grep first) and promote the best owner-aligned ideas into **fully complete, executable**
  plans in `docs/planning/` — scoped against the repo's house style (existing subsystems / folios /
  game cogs) so an executor can build them cold. Index each in `docs/ideas/README.md` + the roadmap so
  it becomes a `▶ Next action`.
- **STILL can't fill the band after promoting what you honestly can** -> that is the **signal, not a
  failure** (Q-0164): set a loud `⚠️ PLAN BACKLOG THIN` line in `docs/current-state.md` ▶ Next action
  **and** the run-report `⚑ Owner-decisions` line, so the owner drops ideas or schedules a dedicated
  planning session. **Never invent low-value filler to look busy** (the Q-0089 bar).

### Step 3 — report

Print: buildable depth estimate (PRs) vs. the 30-PR cadence · ideas promoted to plans (with paths) ·
whether `⚠️ PLAN BACKLOG THIN` was raised · the roadmap rows added.

### Notes

- This is the planning lane of the self-driving loop — how an idea becomes a plan becomes reality with
  no extra owner planning, and how the owner learns *early* that the backlog needs him.
- A *manual* session does not run the full Q-0107 reconciliation automatically (Q-0124); `/plan-band`
  is the deliberate way to do just the planning half when an agent or the owner wants it. The
  every-30-PR pass runs the reconciliation routine automatically.
