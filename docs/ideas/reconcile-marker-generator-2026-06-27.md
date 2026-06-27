# Idea — generate the reconciliation marker instead of hand-writing it

> **Status:** `ideas` — session idea (2026-06-27, Q-0089, from the dispatch run that shipped
> `check_reconcile_marker.py`). Lane: S4 (docs system) / S3 (the engine's tooling). Size: small
> (one stdlib emitter + a routine-prompt wiring line).

## The gap the guard left open

The `Last reconciliation pass:** PR #N (… band-#M … reset to the latest merged PR #R)` marker is
**hand-written** by every Q-0107 pass. This run shipped `scripts/check_reconcile_marker.py`, which
*validates* the marker's three internal invariants (N == R, M == (N // 30) * 30, the pass doc
exists) — but validation is the *detect* half. The drift it caught (the band-#1470 pass wrote its
own PR #1472 as the marker instead of the reset target #1470) happened because a human/agent typed
two numbers that must agree, and got one wrong. A guard turns that into a red check the *next* pass
has to fix; it doesn't stop the pass from emitting the wrong marker in the first place.

## The idea — generate, don't validate

A tiny `scripts/set_reconcile_marker.py` (stdlib, disposable Q-0105) that **emits the canonical
marker line** from inputs it derives, so the agreeing numbers come from one source and can't drift:

- read the **latest merged PR** the same way `check_reconciliation_due._latest_merged_pr()` does
  (`git log origin/main`), use it as both the leading `#N` and the `reset to … #R` (they are the
  same thing by construction),
- compute `band-#M = (N // STEP) * STEP`,
- take the ordinal + pass-doc path as args (or derive the ordinal from the existing marker + 1),
- print the exact marker line (and optionally rewrite it in `current-state.md` in place).

The reconcile routine's "reset the marker" step then becomes *run this script* instead of *hand-edit
the line* — `check_reconcile_marker.py` stays as the backstop for a marker edited any other way.

## Why it's worth having

- It is the generate-don't-validate complement to the guard (same philosophy as the
  migration-collision idea's Option 3: remove the shared hand-typed value rather than lint it). The
  guard catches the drift; the generator prevents it.
- Cheap, offline, read-only-by-default (print mode), pairs with the existing reconciliation-tooling
  cluster. → relates `scripts/check_reconcile_marker.py` · `scripts/check_reconciliation_due.py` ·
  `docs/operations/autonomous-routines.md` (the "reset the marker" step).

## Disposition

Decided-lane, small → execute when the dashboard/tooling lane next has capacity (a few-line emitter +
a test + the one routine-prompt wiring line).
