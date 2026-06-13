# Idea — a "one live decade queue" machine-checkable invariant

> **Status:** `ideas` — capture only, not approved work. Contributed by the third Q-0107
> reconciliation pass (2026-06-13) as its Q-0089 session idea. Dedup-checked against
> `docs/ideas/` — novel (no existing idea covers the reconciliation-pointer drift class).

## The idea

Add a small invariant (extend `scripts/check_docs.py`, or a new
`scripts/check_decade_queue.py`) that asserts the **"one live queue" rule the docs already
state in prose** is actually true on disk:

1. **Exactly one** `docs/planning/reconciliation-pass-*.md` carries a non-`historical`
   status badge at a time (the live decade queue). Two `plan`-badged pass docs = drift.
2. The `current-state.md` **▶ Next action** link and the `roadmap.md` **live decade queue**
   pointer both resolve to **that same** live pass doc. A mismatch fails the check.

## Why I believe in it

This pass had to hand-verify *three* pointers agree (current-state ▶, roadmap top, roadmap
Now) and hand-re-badge the prior pass `historical`. That is exactly the kind of
multi-location consistency a human (or a routine) silently gets wrong — the same drift class
as the #763 false-green regex bug, where a convention was trusted but unenforced. The
reconciliation cadence is now **autonomous** (issue-triggered, #781), so the live-queue
pointer is read by routines that won't eyeball it the way a careful human pass does. An
invariant turns "the newest non-historical pass doc is the queue" from a convention every
pass must remember into a guard that fails CI the moment two pass docs disagree or a pointer
goes stale.

It is cheap (one reachability-style check over a known filename glob + two link resolutions),
directly motivated by manual work this pass did, and it strengthens the most-read line in the
most-read doc.

## Scope / cost

- Small: a glob over `reconciliation-pass-*.md`, parse each status badge, assert exactly one
  non-historical; then grep the two pointer links and assert they target it. ~40 lines.
- Carries the Q-0105 provenance/kill-switch header when adopted ("unverified: confirm across
  a few passes; delete if it proves noisy").
- Routing: agent-ecosystem/workflow lane (a reconciliation-discipline guard). Groom toward a
  quick-win tooling slice if a future pass has spare capacity — not a P0.
