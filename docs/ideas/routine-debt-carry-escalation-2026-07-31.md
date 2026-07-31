# Idea — escalate carried routine-debt on the reconciliation run report

> **Status:** `ideas` · **Subsystem:** S4/S5 (docs-system / ops tooling) · **Lane:** workflow (Q-0194
> friction→guard) · Captured 2026-07-31 (53rd Q-0107 reconciliation pass, band-#2280).

## The observation

The 52nd pass (band-#2250) did the right thing: it stopped minting a fresh standalone idea file every
pass and built [`planning/routine-debt.md`](../planning/routine-debt.md), a **collector** of the four
converging, ungated, self-mergeable tooling ideas the reconciliation passes keep surfacing (dashboard
coalesce · cadence-exclude-generated · control-plane marker staleness guard · THIN standing-vs-raised).
Items 2/3/4 are explicitly designed to ship as **one** docs-tooling PR; item 1 is owner-gated.

This 53rd pass carried that batch **one more pass, unexecuted** — and that is the gap. The reconciliation
routine has exactly one owner-facing escalation channel on its run report: the `⚑ PLAN BACKLOG THIN`
line (Q-0164). It has **no channel for "there is a ready, actionable tooling batch that no session has
picked up."** So a well-built collector can sit indefinitely: the docs-reconciliation routine correctly
won't ship the `check_*` code itself (it fragments the batch and is arguably out of the docs-only lane),
and nothing tells a *tooling-capable* dispatch/routine session — or the owner — that the batch is ripe and
aging. A collector nobody drains is only marginally better than four scattered captures.

## The idea

Give the reconciliation routine a second standing escalation line, parallel to `PLAN BACKLOG THIN`:

- **Convention (ship now):** when `planning/routine-debt.md` holds ⚑-actionable items that have been
  **carried ≥2 reconciliation passes**, the pass adds a
  `⚑ Routine-debt: N items (M self-mergeable), carried P passes` line to the `📤 Run report` footer, so
  the unexecuted batch is visible to the owner / dispatcher exactly where `PLAN BACKLOG THIN` already is.
  This is a pure doc-convention — no code — and can start this pass as its own first instance (the same
  "lead by example" path Q-0089 itself took on install).
- **Guard (later, folds into the routine-debt batch):** a warn-only stdlib `check_*` that parses
  `routine-debt.md`'s item table + a `carried-since:` marker and prints the same one-liner, so the
  escalation can't depend on an agent remembering to write it. This is *not* a fifth debt item competing
  with the batch — it is the **drain mechanism for the collector**, so it belongs above the batch in
  build priority (a batch with no drain signal is the thing being fixed).

## Why it's distinct (not filler, not a dup)

The four items in `routine-debt.md` are the *debts*. This is the *escalation path for the collector
itself* — the missing feedback edge between "a good collector exists" and "someone schedules it." It is
rooted directly in what this pass observed (carrying the batch again with no way to flag it), matching the
Q-0194 rule that friction a pass hits should become the cheapest enforcing prevention. If the owner drains
the batch next dispatch, this idea's convention simply stops firing — self-clearing, like THIN.
