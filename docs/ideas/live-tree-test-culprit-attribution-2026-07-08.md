# Culprit attribution for live-tree ground-truth tests (2026-07-08)

> **Status:** `ideas` — capture only, not a plan, not approval.
> **Subsystem:** none (agent-workflow / CI tooling).
> *(Grooming capture, 2026-07-08, from the PR #1846 follow-on pass — Wave-2,
> coordinator-dispatched. Promotes the Q-0089 flag on the Wave-1 lane B session card,
> `.sessions/2026-07-08-wave1-lane-b-supersede-checker.md`, which deliberately left the
> capture card-only per campaign rails "route follow-ons to Wave-2 grooming".)*

## The problem

Live-tree ground-truth tests (`test_check_plan_homing.py::test_live_repo_plans_are_all_homed`,
and siblings that assert a property of the **checked-out tree**, not the diff) have a built-in
attribution gap: when one fails on a fresh branch, the failure is almost never *caused by that
branch's diff* — it inherits drift some earlier merge shipped to `main`. Observed repeatedly:

- **PR #1843 (2026-07-08):** a docs-only PR added a `docs/planning/` plan without a routing-doc
  link. Its own `code-quality` ran green in 12 s (the docs-only fast path skips pytest), so the
  live-tree homing test never ran on it — and then failed on every subsequent full-CI branch
  until two parallel sessions homed the plan by hand. (Full archaeology:
  `docs/operations/ci-what-runs-where.md` §2b, dated note 2026-07-08.)
- **Band-#1800 reconciliation (2026-07-07):** the same test was red for every open PR because
  three kit-lab plans were homed only from a sibling index, and the pass had to detective the
  culprit by hand.
- **Band-#1230 (2026-06-21):** same class — doc edits removed the last routing links.

Each time, an innocent session burns time proving "not my diff" and then bisecting `main` by
hand. Nothing attributes the breakage to the merge that caused it.

## The idea

1. **Named CI step.** Run the live-tree ground-truth tests as their own named step (e.g.
   `live-tree ground truth`) inside `code-quality`, separate from the general pytest blob — so
   a red is *immediately legible* as "the tree drifted; probably not your diff" instead of an
   anonymous pytest failure the session debugs as its own.
2. **Post-merge culprit issue.** A `push:main` leg runs the same tests on `main` itself; on
   failure it opens (or updates) a **culprit issue** naming the merge that flipped main red —
   which on a push-triggered run is precisely the commit being tested, so attribution is free,
   no bisect needed. The issue is the durable handoff: the next session fixes the drift at the
   root instead of every open PR independently rediscovering it.
3. **Companion root fix** (smaller, arguably first): the docs-only fast path is the one PR
   class that can *introduce* this drift while skipping the test that guards it. Running the
   cheap live-tree docs guards (`check_plan_homing.py --strict` at minimum — stdlib, no deps)
   on the docs-only path too closes the introduction vector; culprit attribution then handles
   whatever still slips through (e.g. semantic merges of two individually-green PRs).

## Why it's worth having

Friction → guard (Q-0194): the by-hand archaeology this idea mechanizes has now been done at
least three times (band-#1230, band-#1800, and the #1843 pass that produced this capture). The
live-tree test family is growing (plan homing, session-slug uniqueness, ledger parity …), and
every new member widens the "innocent branch inherits main's drift" window. Attribution is the
cheap half — a push-main failure names its own culprit.

Workflow edits are owner-gated (Q-0194 split) — the checker/step design is free to plan; the
`.github/workflows/` wiring ships owner-directed or via a router DISCUSS Q.
