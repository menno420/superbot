# Routine-system improvements — field notes from a live run (2026-06-14)

> **Status:** `ideas` — proposals, **not** approval. Written by the Claude Code
> routine that ran the 2026-06-14 "auth probe" session (PRs #840/#842/#845/#847/
> #848/#850/#851), at the owner's request, as first-hand feedback on the
> autonomous-routine system. Grounded in what actually happened that run; cites
> the real mechanisms in [`operations/autonomous-routines.md`](../operations/autonomous-routines.md)
> and [`operations/hermes-skills/dispatch.md`](../operations/hermes-skills/dispatch.md).

## The one-line takeaway

The **repo orientation already works** — a 2-word trigger ("auth probe") still
produced a correct, end-to-end session because `CLAUDE.md → current-state →
session logs → bug-book → planning docs` consistently carried the trail. The
weak links are at the **edges of the run**: the *intake* (what Hermes fires) and
the *outtake* (how the run reports back so you can accept/redirect without
checking in). Tighten those two edges and the no-check-in loop closes.

## What worked (keep / don't regret)

- **Layered memory did the steering.** I rarely guessed: the role-name security
  bug was already noted in a 2026-06-05 audit; the "missing bindings" trail was
  in the convergence plan; the bug-book gave a home and format. This is the
  payoff of the mapping you're doing — it generalizes.
- **`check_quality.py --full` as a true CI mirror** made "is it done?" binary.
- **Auto-merge on green** + push-to-`claude/` is friction-free and let me ship 7
  PRs without merge ceremony.
- **The context maps before edits** made "where does new code go?" obvious
  (e.g. the backfill orchestration → its own module, not the size-capped cog).

## Priority 1 — the run-report artifact (the linchpin of "Hermes reports to me")

**Observation.** Your target model is: routine works → Hermes summarizes "what it
did / changed / notes left" → you accept or redirect. Today that summary would be
*reconstructed* by Hermes reading N PRs + the session log ad hoc. Two classes of
information are easy to lose that way: **decisions that need you** and **manual
steps only you can do**. This run hit both (the backfill remediation needed your
call; running `!platform backfill apply` and `!platform consistency` are Discord
actions I can't perform) — I surfaced them *in chat*, which in a no-check-in run
would have evaporated.

**Proposal.** Standardize a **run-report block** every routine writes into its
`.sessions/<date>-<slug>.md` log (the artifact already mandated at session
close), with fixed headings Hermes can parse deterministically:

```
## Run report
- **Trigger:** <verbatim payload> · **Class:** <fix|…> · **Outcome:** <shipped/blocked>
- **Shipped:** #PR — one line each
- **⛏ Owner decisions needed:** <Q-#### refs, or "none">
- **🔧 Owner manual steps:** <e.g. "run !platform backfill apply in <guild>", or "none">
- **↪ Next:** <the sharpened current-state Next action>
```

Hermes's report to you becomes a near-mechanical roll-up of these blocks across
the day. The `Owner decisions` / `Owner manual steps` lines are the bits that
otherwise vanish — make them required fields (write "none" when empty).

## Priority 2 — align the routine prompt with the *actual* delivery model

**Observation.** The routine prompt is built around a **`PushNotification`** tool
as "the point of the run" — but that tool is **not provisioned in this
environment** (nor is `send_later`). For a genuinely unattended run I'd have had
no way to reach you; findings would have sat silent. It only worked because you
were present. And it's not even the right model: in your architecture the human
is reached **via Hermes reading artifacts**, not the routine pushing directly.

**Proposal.** Update the routine prompt so its "how a run reaches the owner"
section matches reality: *your deliverable is the PR(s) + the Priority-1 run
report; Hermes relays it. Do not depend on a push tool; never block waiting for a
human.* Either provision `PushNotification`/`send_later`, **or** delete them from
the prompt — a prompt whose central mechanism doesn't exist mis-steers the agent
(I spent real effort discovering the gap mid-run). A routine should also be able
to **self-check at startup whether it can reach the owner** and state it in the
run report if it can't (sibling of
[`agent-env-credential-smoke-check`](./agent-env-credential-smoke-check-2026-06-14.md)).

## Priority 3 — make Hermes use the dispatch contract it already has

**Observation.** The `superbot-dispatch` skill assembles a tidy
`TASK / CONTEXT / ACCEPTANCE / CLASS / NOTES` work order — but the fire I received
was the bare string `auth probe`. So the structured intake exists; Hermes just
isn't using it yet (you confirmed: "Hermes isn't tuned to the workflow"). The
inference gap was survivable here, but a thin payload on an *ambiguous* task
(vs. an exploratory probe) could send a run down the wrong path.

**Proposal.** Two cheap guards:
1. In the routine prompt's free-form branch, when the payload is **< ~5 words or
   has no `CLASS:`**, make the *first* action an explicit "infer scope from
   current-state Next action + classify, and record the inference in the run
   report" — so the interpretation is visible and reviewable, not silent.
2. Add a tiny **feedback line** to the run report (`Trigger quality: structured |
   thin`) so you can see, across runs, when Hermes is firing raw and nudge its
   tuning. Closes the loop on getting Hermes onto the dispatch skill.

## Priority 4 — the repo-area map for non-overlapping parallel runs

**Observation.** This run re-synced `main` ~6 times as *other* routines merged
PRs (#843/#846/#849/…) underneath it. No conflicts — but that was small-PR luck
plus the union-merge discipline, not a structural guarantee. You want parallel
agents that don't collide; `active-work.md` (Q-0126) is the early signal and
exists, but a dispatcher needs an **area map** to *choose* non-overlapping work.

**Proposal.** A short **`docs/owner/repo-area-map.md`** (or a section in
`autonomous-routines.md`): each routine/lane → the directories it owns + the
"do-not-touch-concurrently" seams (e.g. `disbot/cogs/*` vs `docs/*` vs
`scripts/hermes/*`). Hermes dispatches by area; each routine claims its area in
`active-work.md` at start (already the rule) and the map makes "is this free?"
answerable *before* the fire. This is the concrete form of the mapping you said
you're already doing — write it where the dispatcher can read it.

## Priority 5 — two small clarity fixes the run actually tripped on

- **Owner-directed vs. agent-originated under the phase gate.** Building
  `!platform backfill` looked feature-shaped and tripped the FIX-phase gate; I
  had to reason that the gate blocks *agent-originated* features, not
  *owner-directed correctness*. Correct, but implicit. State it once, crisply, in
  the phase-gate doc + routine prompt so a more literal agent doesn't wrongly
  refuse owner-approved work (or wrongly build).
- **"Productive once started" guard.** You have a limited daily routine budget,
  so a no-op "all's well, exiting" run is waste. The prompt's standing-queue
  fallback is good; make it a hard ladder: *trigger work → else current-state
  Next action → else an OPEN bug-book item → else backlog grooming.* A run should
  never exit having shipped nothing unless the repo is genuinely idle (rare, by
  your own design).

## Cross-cutting note

Every item above is an **edge** fix (intake / outtake / dispatch coordination),
not a core-orientation fix — because the core already works. The cheapest, highest-
leverage single change is **Priority 1** (the run-report block): it directly
produces the artifact your "Hermes summarizes, I accept/redirect" model consumes,
and it makes Priorities 2–3's feedback signals have somewhere to live.
