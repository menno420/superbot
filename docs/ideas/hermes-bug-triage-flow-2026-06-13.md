# Idea: Hermes-mediated bug-triage flow (curated, batched bug intake)

> **Status:** `ideas` → **owner-directed, design captured, not yet built** (2026-06-13, owner
> voice). The owner wants `/bugreport` to route **through Hermes** as an intelligent gatekeeper
> rather than the current direct instant-fire. Build is the next-session headline for the agent
> control plane. Source code + binding contracts win over anything here.

**Captured:** 2026-06-13 · **Owning area:** agent control plane (Hermes) + the bot's Discord
intake. Companion: `docs/operations/autonomous-routines.md`, `docs/operations/hermes-dispatch-bridge.md`.

## The problem with `/bugreport` today

`disbot/cogs/hermes_cog.py` (#757) wires `/bugreport` to **directly POST to the Claude Code
Routine `/fire` endpoint** — bypassing Hermes entirely (despite the name). The routine then
reproduces → fixes → **self-merges on green CI**. So every admin `/bugreport` = **one routine
run + one auto-merge to `main` → auto-deploy**, instantly, unscreened. That is:

- **Cap-hungry** — one of ~15 daily routine runs per report.
- **Unscreened** — a spam/prank/duplicate/non-bug report still spins a full fix-and-merge session.
- **Not what the owner asked for** — he wants a curated, batched, Hermes-in-the-loop flow.

## The wanted flow (owner's words, sharpened)

```
Discord report → HERMES triages first:
   ├─ spam / prank / not-a-bug → discard (optionally note it)
   └─ genuine / worth-investigating → Hermes:
        · reproduces / diagnoses (log-triage skill: VPS + prod logs)
        · pulls related files / recent changes / context
        · rewords it into a CLEAR issue with directions
        · SAVES it — a `bug` GitHub issue (repo) and/or a #bug-reports Discord summary
   → the nightly EXECUTOR sweeps accumulated `bug` issues and batch-fixes them
   → admin "fix now" (e.g. /dispatch or a label) bypasses the batch for urgent ones
```

Hermes becomes the **different-model gatekeeper + curator**: it filters noise, turns a vague
report into a precise work order with evidence, and **batches** so the routine cap is respected.
This is the same "non-Claude mind in the loop" value as the Q-0117 review gate, applied at intake.

## The pieces it needs (build order)

1. **Intake change (cog).** `/bugreport` → **post the report into a `#bug-reports` Discord
   channel** instead of calling `_fire_work_order`. (Hermes is now *on* Discord, so it can watch
   that channel.) Small `hermes_cog.py` change; drop the instant `/fire` call for `/bugreport`.
   Keep `/dispatch` (owner) as the explicit "fix now" lever.
2. **`superbot-bug-triage` Hermes skill** — the filter + reproduce + reword + save logic
   (read-only diagnosis via `log-triage`; produces a curated issue body).
3. **Hermes's second sanctioned write: `gh issue create`** — to file the curated `bug` issue.
   This expands the read-only model by one more write (today it has exactly one: `gh pr merge`
   in `review-merge`, Q-0117). **Needs an owner decision** (a Q-block) like Q-0117 was.
4. **Executor sweeps `bug` issues** — small executor-prompt tweak so STEP 1 lists open `bug`
   issues, fixes a small batch per run, and closes them (already half-present: it reads the
   bug-book; add the `bug`-issue source).
5. **Gateway config** — Hermes watches the `#bug-reports` channel (process new messages there),
   not just DMs/mentions.

## Interim safety (until built)

The current `/bugreport` auto-merges to prod on every report. A **one-line cog tweak** can make
bug-fix dispatches **open a PR and hold** (not self-merge) until reviewed — no new infra. Worth
doing if `/bugreport` is used before the full flow lands. (Owner offered this; deferred with the
rest to next session.)

## Open decisions

1. **Where bugs are saved** — GitHub `bug` issue (executor-readable, the recommendation), a
   Discord channel (human-visible), or both. Both is cleanest: issue = the work queue, channel =
   the human log.
2. **Hermes's `gh issue create` write** — yes/no + scope (only `bug`/`reconcile`/`continue`
   labels?). The Q-0117 calibration discipline applies: trust the curation after it proves out.
3. **Batch trigger** — rely on the nightly executor sweep (cheap, no extra fires — recommended),
   or a threshold ("≥N open bugs → fire now", costs an extra run). Default to the nightly sweep.

## Routing

**Build next session** (owner-directed). It is a real multi-piece feature (cog + skill + an owner
write-boundary decision + executor tweak + gateway config), not a toggle. This doc is the spec;
the next control-plane session (or a planned executor step, once the owner decision on Hermes's
write lands) builds it.
