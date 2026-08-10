# Idea — cap & consolidate the reconcile-tooling idea *cluster* (producer-side backlog hygiene)

> **Status:** `ideas` — session idea (Q-0089), captured 2026-08-10 (fifty-sixth Q-0107 reconciliation
> pass, band-#2370). Not approved for implementation. · **Class:** friction→guard · **Subsystem:**
> S4/S5 (docs-system / the reconcile routine's own idea backlog).

## The observation (what this pass actually surfaced)

`docs/ideas/` now holds **~40 reconcile/ledger-tooling idea files** — `reconcile-marker-generator`,
`reconcile-pass-tail-trim-actuator`, `band-archetype-classifier`, `reconcile-open-pr-disposition-actuator`,
`reconcile-band-coverage-linter` (55th pass), `docs-ledger-parsing-helper`, `ledger-*` (a dozen of
them), and more. Every one of them proposes automating a *slice* of the same mechanical pass, and
**every one is blocked on the same gate**: the docs-only reconcile routine has no `scripts/` executor,
and the repo is frozen as the superbot-next oracle
([`routine-self-improvement-backlog-has-no-executor-2026-08-03.md`](routine-self-improvement-backlog-has-no-executor-2026-08-03.md)
names that *consumer*-side gap).

This pass adds the missing *producer*-side half: **each frozen-repo reconcile pass is expected to emit a
Q-0089 idea, and with the mechanical surface fully ideated, the honest ideas that remain are all
same-shaped tooling fragments** — so the routine keeps minting near-duplicate, caveated,
provably-undeliverable ideas. That is itself the backlog drift grooming exists to prevent
(`docs/ideas/README.md`: "every idea eventually becomes implemented or discussed — never orphaned"),
inverted: ~40 ideas orphaned *in place*, none discussable one-at-a-time because they share one root.

## The idea

Two moves, both docs-only and shippable *now* (no frozen-repo executor needed):

1. **Consolidate the cluster into one umbrella plan.** Fold the ~40 reconcile-tooling fragments into a
   single `docs/planning/reconcile-pass-actuator-plan.md` — one buildable spec for a dry-run-first
   `scripts/reconcile_pass.py` that composes the already-ideated pieces (compute band since marker →
   classify PRs (dashboard/dep/reconcile/runtime) → emit the two grouped Recently-shipped bullets +
   marker reset + trim candidates + open-PR disposition, all as a reviewable diff). The fragments
   become sub-items with `▶ FOLDED INTO` pointers, not 40 separate READMEs to re-triage. When an
   executor *does* appear (owner lifts the freeze, or a dispatch/tooling seat runs — the condition
   the 08-03 idea waits on), there is **one** plan to build, not 40 to re-read.

2. **Cap same-shaped Q-0089 output under freeze.** Add a one-line rule to the reconcile routine's saved
   prompt (`operations/autonomous-routines.md`, STEP 4): *once the mechanical surface is fully ideated,
   a pass may satisfy Q-0089 by **grooming** one existing reconcile-tooling idea toward the umbrella
   plan instead of minting a new fragment* — honoring "never force filler" (Q-0089) explicitly for the
   steady-state frozen pass, so the backlog stops growing faster than it can be drained.

## Why it's worth having (and why it's not itself filler)

It is the one genuinely *new* thing this steady-state pass can observe: not another slice to automate,
but the meta-fact that the slice-ideas have saturated and are now drift. Move 1 is a real grooming
deliverable a docs-only pass **can** ship (it is exactly the Q-0015 "structure a bigger idea into a
plan" lane); move 2 makes the routine self-limiting so pass N+1 doesn't re-create the problem.
Reversible (pure docs reorganization; the fragments' content is preserved in the umbrella plan).

## Route out

Distinct from `routine-self-improvement-backlog-has-no-executor` (that is the *executor* gap — this is
the *idea-proliferation* gap; they compose: consolidate the fragments **and** wait for the executor)
and from `reconcile-band-coverage-linter` / `reconcile-marker-generator` / the other fragments (those
are the *members* of the cluster this idea proposes to fold). Collect into
[`planning/routine-debt.md`](../planning/routine-debt.md) at the next pass that has grooming capacity;
the umbrella plan is the natural home for the whole `reconcile-*`/`ledger-*` tooling family.
