# Idea — a `reconcile`-issue ↔ marker band-consistency guard

> **Status:** `ideas` — **SHIPPED 2026-06-27** (dispatch run, self-initiated Q-0172):
> `scripts/check_reconcile_marker.py` + `tests/unit/scripts/test_check_reconcile_marker.py`. The
> shipped guard implements the conflation check (assertion 1 below) + the band-boundary check
> (assertion 2) + the linked-pass-record existence check (assertion 3); it also caught + fixed a live
> drift (the band-#1470 marker read `PR #1472` — the pass's own PR — instead of the reset target
> `#1470`). *Not folded into `check_current_state_ledger.py` — kept a standalone disposable (Q-0105)
> sibling instead, simpler to delete if it proves noisy.* Assertion 1's "latest open/closed reconcile
> issue" cross-check (below) was **not** built — the marker is self-consistent without a network call,
> so the guard stays pure-stdlib/offline.
> Raised by the band-#1470 Q-0107 reconciliation pass (2026-06-26, Q-0089).
> Lane: S4 (docs system) / S3 (the engine's tooling). Size: small (one stdlib checker + test).

## The problem

The `Last reconciliation pass: PR #N` marker text in `current-state.md` is hand-written, and it
conflates two different numbers that *look* interchangeable but are not:

- the **reset target** — the latest *merged* PR at pass time (the trigger workflow keys off this), and
- the **pass identity** — the PR the docs-only pass itself shipped as.

The band-#1440 pass wrote `PR #1441 (… twenty-fifth … reconciliation pass …)` — but #1441 was a
*dashboard refresh* (the latest merged PR, so a correct reset target) while the 25th pass itself shipped
as PR **#1443** (`claude/reconcile-1440`). The convention ("reset to the latest PR") was followed
correctly; only the *parenthetical* was wrong — it claimed the reset target *was* the pass. The
band-#1470 pass then spent real time disentangling this before it could trust the marker.

This is a recurring micro-drift: every pass re-writes the marker by hand, so every pass can re-introduce
the same conflation, and the next pass re-explains it in prose instead of the checker catching it.

## The idea

A tiny stdlib checker — `scripts/check_reconcile_marker.py` (warn-first, disposable per Q-0105) — that,
given the current `Last reconciliation pass` marker `#N` and the latest open/closed `reconcile` issue,
asserts:

1. the marker `#N` is the **latest merged PR** known to the ledger (not an older one, not the pass's own
   PR number guessed wrong), and
2. the parenthetical band label (`band-#M`) matches the cadence boundary the triggering issue crossed
   (`M` = the multiple of 30 just below `N`), and
3. the linked `reconciliation-pass-*` doc exists and is the single `plan`-badged one.

It folds naturally into the existing `check_current_state_ledger.py` family (same parse of the
Recently-shipped block) and would have flagged the #1441-vs-#1443 conflation at the root.

## Why it's worth having

Reuses the parse the ledger checker already does; turns a recurring "each pass re-explains the marker in
prose" cost into a one-line CI signal. Pairs with the existing reconciliation-tooling cluster (the
planned-slice hit-rate tracker, the band-archetype classifier, the one-plan-badged-pass guard) — all of
which automate a prose judgement this routine currently re-makes by hand each pass. Cheap, contained, and
exactly the "leave the next run better-equipped" lane the loop exists for.
