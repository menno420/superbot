# Idea — the ledger guard should distinguish *benign newest-merge lag* from real drift

> **Status:** `ideas` — capture, **not** a plan, **not** approval. Source code and the
> binding contracts win over this file. Small/safe grooming-lane candidate (a tooling
> precision tweak for the reconciliation/`session-close` loop).

## The friction (observed this session, 2026-06-14)

`scripts/check_current_state_ledger.py` treats **any** recent merged PR absent from the
ledger as drift. But the script's own docstring says the opposite is fine:

> a brand-new merge legitimately lags the ledger by a session, so this must never hard-fail CI

Dogfooding the new subject-printing this session, the live run flagged **#862 + #863** — both
genuinely merged, both *expected* between-pass lag (last reconciliation marker is #840; these
reconcile at the #870 pass). So the two signals the guard currently conflates are:

- **Benign lag** — the newest 1–2 merges a session sees before the next reconciliation records
  them. Expected, documented, *not actionable* by a normal session.
- **Real drift** — an *older* merged PR (well behind the newest) that was never recorded. The
  failure class the guard exists to catch (#730/#733; the band-#800 ~14-PR hole).

Because `--strict` (run by `/session-close`) fails on *both*, the benign case produces a red
signal a routine has no clean way to act on — exactly the noise that trains an operator to
ignore the guard.

## The improvement

Give the guard a notion of an **expected-lag budget**: the newest *N* merged PRs (default ~2,
or "everything newer than the `Last reconciliation pass: #M` marker") are reported as
**`lagging` (informational)**, while anything older that's missing is **`drift` (actionable)**.
`--strict` then exits 1 only on real drift; lag prints as a distinct, non-failing line.

Sketch:
- Parse the `Last reconciliation pass:** PR #M` marker already in `current-state.md`.
- Partition `find_missing` output into `missing_drift` (`pr <= M` or beyond the lag budget) and
  `missing_lag` (`pr > M`, within budget).
- `main` prints both buckets distinctly; `--strict` gates on `missing_drift` only. Add
  `--lag N` to override the budget.

## Why it's worth having

- It sharpens a guard the whole autonomous loop leans on: a red `--strict` then means *"a PR
  actually fell through,"* not *"the newest merge hasn't been reconciled yet"* — so a routine
  can treat red as a real notify-worthy event.
- It removes the standing false-red that `/session-close --strict` hits on every session whose
  newest sibling merge lags.

## Caveat / disposability (Q-0105)

A precision convenience, not a correctness guard. If the marker-parsing proves brittle across
the reconciliation-cadence changes, fall back to a pure "newest N" budget — or drop it. Pairs
with the two already-shipped ledger-guard slices (print-subjects, range-scope).
