# Idea — Forward-only Project: measure the quality cost of forbidding destructive actions

> **Status:** `ideas` · raised by the owner 2026-07-08 (EAP-email thread) · EAP-evaluation-adjacent
> **Provenance:** owner directive — "if we genuinely don't need these to do our work, create a
> fresh project with better-scoped instructions so it does not even think about doing any
> destructive actions… show what happens if we try to prevent it and how it affects the quality
> of our work."

## The concept

We established (this session) that destructive git (force-push, remote-branch delete, history
rewrite, first-publish-to-a-new-public-repo) is **friction, not a work-stopper** — every use has a
forward-only alternative. This idea turns that claim into an **experiment**: configure a Project's
Custom Instructions so agents *never attempt* destructive actions — forward-only by design — then
run real work through it and record the **actual quality cost**.

Two payoffs:
1. **Practical.** Agents stop wasting cycles hitting walls they can't clear (the coordinator spent
   real effort probing/relaying denied destructive ops this session). Forward-only-by-instruction
   removes that waste.
2. **Email evidence.** Instead of *asserting* "it's only friction," we **demonstrate** the cost
   empirically — the strongest possible version of that argument for the Anthropic feedback.

## What "forward-only instructions" say (draft)

> This Project never performs destructive or history-rewriting git. Do not force-push, delete
> remote branches, rebase-and-force, `--amend` an already-pushed commit, or first-publish to a new
> public repo from a session. Instead: a fresh branch instead of rewriting a stale one; a fixup
> commit instead of an amend; let squash-merge flatten history; leave branch cleanup to GitHub's
> auto-delete-on-merge + a token-backed Action; route any genuinely-needed destructive step to the
> owner via decide-and-flag. Treat the absence of these operations as normal, not a blocker.

## How to run it (fork to decide)

- **Re-instruct the current Project** — continuity (keeps rebuild state + coordinator memory), but
  the coordinator is already "contaminated" with wall-probing history, so it's a less clean
  baseline.
- **A fresh Project** — clean baseline for the experiment and separates it from the rebuild, but
  loses accumulated memory and adds a second Project to run.

Recommendation: **re-instruct the current Project** unless we specifically want a clean A/B; the
experiment is informative either way, and a fresh Project fragments the rebuild.

## Deliverable when run

An observations note (work still shipped? messier history? any stuck/confused states? cycles
saved?) → the EAP evaluation log + a follow-up-email paragraph. Needs run-time, so the **results**
are follow-up-email material; email 1 can preview it ("we're now quantifying the constraint's
cost").

## Dedup

No existing `docs/ideas/` entry proposes an instruction-level forward-only configuration or a
quality-cost measurement of the permission constraint; this is distinct from the permission-probe
report (which maps *what* is walled, not the *cost of avoiding* it).
