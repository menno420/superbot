# Idea — collapse the current-state control-plane bullet to a pure pointer (one source of truth)

> **Status:** `historical` — **EXECUTED 2026-06-16 (PR #943).** The `current-state.md` Gates
> control-plane bullet is now a pure pointer to the canonical table with zero verdict prose of its
> own, so the copy can no longer drift. The **optional** `check_docs` verdict-phrase lint (the
> belt-and-suspenders half) was **not** built — the pointer collapse alone removes the copy, so
> there is nothing left to drift; the lint stays a capture-only follow-up here. Routing: **S5
> Operations / docs system**. Raised 2026-06-15 (Q-0089) by the band-#930 reconciliation pass.

## The gap (observed twice now)

The autonomous-loop control-plane truth lives in **two** prose homes:

1. the **canonical table** — `docs/operations/autonomous-routines.md` § "Control-plane state"
   (rows 1–6, maintainer-verified; the band-#870 pass fixed it and it is correct), and
2. a **restating bullet** — `docs/current-state.md` § "Gates / blocked work" → "Autonomous loop…".

This pass found home #2 had **drifted again**: it still claimed the loop "has **never self-fired**"
and "stays inert until the owner adds `ROUTINE_PAT`", while home #1 (and the live read: the trigger
issue's `menno420` author) proved `ROUTINE_PAT` is set and the loop self-fires. This is the **same
drift class** the band-#870 pass already fixed once in home #1, now recurring in home #2. A single
fact with two independent prose homes is a standing drift generator — every reconciliation pass has
to re-sync them by hand, and `check_loop_health.py` (Q-0135) only reads live GitHub, not home #2.

## The idea

Make `current-state.md`'s Gates control-plane bullet a **pure pointer** — *"Autonomous loop: see
the canonical [Control-plane state table](../operations/autonomous-routines.md) — that table is the
single source of truth; do not restate its verdict here."* — with **zero verdict
prose of its own**. Then there is exactly one home for the verdict, and the second home cannot
contradict it.

Optionally generalize with a tiny `check_docs` rule: flag when the `current-state.md` Gates bullet
contains a control-plane *verdict phrase* ("never self-fired" / "blocked on `ROUTINE_PAT`" /
"self-fires") instead of a bare link — i.e. lint that the pointer stays a pointer. Cheap, disposable
(Q-0105), and it closes the recurrence at the structural level rather than relying on each pass to
notice the drift.

## Why it's worth having

The reconciliation loop's whole job is to kill drift; a fact it has to manually re-sync every pass
is drift the *system* should prevent. This is the smallest possible fix (delete the restated verdict,
keep the link) and it removes one recurring manual step from every future pass — first-class
workflow improvement (the point of the loop), not bot surface.

## Dedup

Distinct from `check_loop_health.py` (Q-0135), which probes **live GitHub** for the table's truth —
this is about the **second prose home** the probe doesn't read. Complementary: the probe keeps the
canonical table honest; this keeps a *copy* of the table from existing at all.

## Gate

None — pure docs/tooling, reversible. A future pass that touches the Gates section can apply the
pointer collapse directly; the lint half is an optional `check_docs` add.
