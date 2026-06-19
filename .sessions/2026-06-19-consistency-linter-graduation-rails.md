# 2026-06-19 — Consistency-linter graduation rails (per-rule severity + tracker)

> **Status:** `in-progress`

## What I'm about to do

Empty scheduled dispatch fire. Per current-state ▶ Next action, the next ungated startable is the
next consistency-linter slice: rules 2/3/4 (`back_button`, `panel_base_class`,
`select_option_truncation`) are now at 0; rule 1 (`edit_in_place`, 17 left) is blocked on the AI-nav
redesign (plan promoted last session, #1060). The flip-to-error is gated on "stays clean a couple
more sessions" — those rules only reached 0 in #1056/#1057/#1059 (all 2026-06-19), so the flip is
**not yet due**.

**This slice builds the graduation rails** so the eventual flip is a one-word change, without
prematurely flipping anything:

- per-rule `severity` (`"warning"` → `"error"` graduates a rule) + a `graduation` blocker/candidate
  note on the `Rule` dataclass; findings inherit their rule's severity;
- a `--list-rules` readout (the per-rule graduation tracker — implements #1060's session idea) +
  surface graduation status in the report;
- wire `check_consistency.py --mode strict` into the pre-PR suite (`check_quality.py`) as a no-op
  gate that becomes live the instant a rule's severity flips to `error`;
- a graduation tracker table in the linter plan recording each rule's clean-since date + blocker.

All rules stay warn-only this session (respecting the plan's caution); the rails make graduation
mechanical for a future session.
