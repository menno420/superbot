# 2026-06-19 — Bug-book guard: terminal short-circuit on `FIXED (root)` label, not bare `(root)`

> **Status:** `complete`

## Arc

Second-round Codex review on #1146 (which merged before this could be folded in). Valid edge case:
`_classify`'s terminal short-circuit keyed on bare `(root)`, so a *still-deferred* status whose prose
mentions `(root)` — e.g. `FIXED (immediate) — root-fix RECOMMENDED; add (root) after the durable fix`
— returned `None` before the deferred-signal checks, wrongly clearing exactly the entry the guard
exists to list.

## Fix

Tightened the short-circuit to the terminal **`FIXED (root)` label** (not any `(root)` occurrence) —
the bug-book contract is that a deferred entry *lacks* that terminal label. Real entries all write
`FIXED (root)` for the terminal case, so live output is unchanged (still reports only BUG-0009).

- `scripts/check_bug_book_rootfix_backlog.py` — one-line condition + docstring.
- `tests/unit/scripts/test_check_bug_book_rootfix_backlog.py` — `test_prose_root_marker_does_not_suppress_a_deferred_status` (14 tests total).
- Verified: 14 pass, `check_quality --check-only` green, full mirror before push.

## Note

This closes the #1144/#1146 review loop. Further review nitpicks on this warn-only, disposable (Q-0105)
tool would be diminishing returns against increasingly contrived wording — the contract-correct cases
are now covered; a later session should not chase further low-stakes edge cases here.

## 📤 Run report

- **Run type:** routine · dispatch
- **⚑ Owner-decisions:** none
- **⚑ Owner-manual-steps:** none
- **⚑ Self-initiated:** YES — review-driven hardening of the self-initiated #1144/#1146 guard. No
  dispatch/owner ask. Reversible (warn-only disposable tool).
