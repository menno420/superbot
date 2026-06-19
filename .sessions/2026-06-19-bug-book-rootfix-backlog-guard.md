# 2026-06-19 — Self-initiated tooling: bug-book deferred-root-fix backlog guard

> **Status:** `complete`

## Arc

Second slice of a dispatch run (no work order). The first slice (PR #1143) closed BUG-0018 — a bug
that had sat logged `FIXED (immediate) / root-fix RECOMMENDED` and un-promoted until a later run
noticed it *by hand*. That miss is itself a workflow gap: a symptom-fixed-but-root-owed bug-book
entry has no signal making it a pickable backlog item. This slice builds the guard that surfaces it
(promoted from the #1143 session idea — idea→plan→build is open, Q-0172).

## What shipped (PR — self-initiated, Q-0172)

- `scripts/check_bug_book_rootfix_backlog.py` — stdlib, warn-only (Q-0105 disposable header). Parses
  `docs/health/bug-book.md` and flags entries whose `## BUG-NNNN` header / `- **Status:**` line shows
  a deferred root fix: `PARTIALLY FIXED`, `root-fix RECOMMENDED`, or `FIXED (immediate)` without
  `(root)`. Skips terminal (`FIXED` / `FIXED (root)`) and honestly-labelled `OPEN`. Scoped to the
  header + status line (never body prose) so a "recommendation" mention in a root-cause paragraph
  can't false-positive. `--strict` exits 1 on a non-empty backlog.
- `tests/unit/scripts/test_check_bug_book_rootfix_backlog.py` — 9 tests over an inline fixture
  (deterministic as real entries open/close): the three flagged classes, the terminal/OPEN
  exclusions, the `FIXED (root)` short-circuit (the BUG-0018 self-fix shape), reason strings,
  empty book, and the advisory-vs-`--strict` exit contract.
- `docs/health/bug-book.md` — a discoverability pointer in the intro convention block so future
  agents know the guard exists.
- Live run (against `origin/main`'s bug book, pre-#1143) correctly flags **BUG-0018** (the entry
  #1143 fixes) + **BUG-0009** (genuinely PARTIALLY FIXED, slice 3 open) — proving it would have
  caught exactly the miss that prompted it. Once #1143 merges, BUG-0018 drops off (→ FIXED root).

## Verification

- `python3.10 scripts/check_quality.py --check-only` green (black/isort/ruff/check_docs/consistency).
- Targeted pytest green (9 passed); full mirror run before push.

## ⟲ Previous-session review (Q-0102)

(See the sibling log `2026-06-19-site-json-drift-rootfix.md` — same run.) The system improvement that
review surfaced is exactly this slice: a `FIXED (immediate) / root-fix RECOMMENDED` entry is a
standing backlog signal, and the workflow had no tool to make it pickable. Now it does.

## 💡 Session idea (Q-0089)

Wire `check_bug_book_rootfix_backlog.py` (and the sibling `check_plan_backlog`) into the
`/session-close` skill's advisory readout, so every session close prints the current deferred-root
backlog + thin-plan signals — turning "what should the next empty-fire run pick up?" into a standing,
zero-effort prompt rather than something an agent has to think to run. (Deferred to keep this PR
tooling-only; captured here for a follow-up.)

## 📤 Run report

- **Run type:** routine · dispatch
- **⚑ Owner-decisions:** none
- **⚑ Owner-manual-steps:** none
- **⚑ Self-initiated:** YES — promoted the #1143 session idea (deferred-root-fix backlog guard) to a
  built, tested, warn-only tool with no dispatch/owner ask (Q-0172). Reversible (disposable Q-0105
  tool, not CI-wired). Flagged for owner review.
