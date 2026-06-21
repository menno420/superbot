# Idea — a line-budget guard for the `current-state.md` ▶ Next action callout

> **Status:** `ideas` — session idea (2026-06-21, Q-0089, from the band-#1230 reconciliation pass).
> Workflow/tooling. The *measurement* half that pairs with the (proposed) tail-trim **actuator** — the
> actuator cuts, this guard tells you the cut is overdue.
> **Subsystem:** none

## The observation

The `current-state.md` ▶ Next action callout grew to a **40.5 KB single-paragraph wall** before the
band-#1230 pass (this one) finally pruned it by hand to 3.3 KB. It got that big despite the bloat being a
*standing* Q-0102 finding restated by at least three prior passes — because the finding was **prose, not a
number**. Each pass read "this callout is a wall," judged the prune to be a separate session's job, prepended
its own line, and moved on. The wall always won.

The Recently-shipped *list* never has this problem: `scripts/check_docs.py` **soft-ratchets it at 20**, so a
21st entry is an immediate, visible, mechanical signal. The callout has no equivalent gauge — its size is
invisible to every checker, so "it's too big" stays a matter of taste that a busy pass can rationalize away.

## The idea

Add a tiny **warn-only** sub-check (either a new `scripts/check_current_state_callout.py` or a clause inside
`check_docs.py`) that measures the live ▶ Next action callout's character length and **warns when it crosses a
budget** (e.g. ≥ 6 KB), naming the regression: *"▶ Next action callout is N KB (budget 6 KB) — prune consumed
band-history into the per-band pass records (Q-0102)."* Keep it **warn-only** (Q-0105 disposable dev tooling)
so it never blocks CI, only nags — the same role the Recently-shipped ratchet plays, but for the callout.

Pairs with [`reconcile-pass-tail-trim-actuator`](./reconcile-pass-tail-trim-actuator-2026-06-20.md): that
idea is the **actuator** that performs the cut; this is the **gauge** that says the cut is due. Built
together they make the callout self-maintaining — a number trips, a `--callout` actuator run resolves it —
turning a multi-pass-standing judgment call into a deterministic loop.

## Why it's worth having

The whole point of the reconciliation loop is that drift gets *caught by a signal*, not by hoping a future
session notices. A prose finding that three passes acknowledged and none acted on is precisely the failure a
guard exists to prevent. This is cheap (a `len()` and a threshold), stdlib-only, and closes the exact gap
that let the wall reach 40 KB.

## Disposition

`ready` (a dispatch run — it adds a `scripts/` file + a `tests/unit/scripts/` regression, so not a docs-only
pass). Tracked as slice D2-adjacent in the [band-#1230 next-band queue](../planning/reconciliation-pass-2026-06-21-band1230.md).
