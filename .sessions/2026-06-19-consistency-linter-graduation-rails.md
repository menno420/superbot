# 2026-06-19 — Consistency-linter graduation rails (per-rule severity + tracker)

> **Status:** `complete`

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

## Shipped (#1063)

- **`scripts/check_consistency.py`** — `Rule` gains `severity` (`"warning"`→`"error"` graduates a
  rule) + a `graduation` blocker/candidate note; `run_checks` stamps each finding with its rule's
  severity, so `--mode strict` fails on a graduated rule. New `--list-rules` prints the per-rule
  tracker; the report footer names clean warn-only candidates. Docstring documents the one-field
  graduation step.
- **`scripts/check_quality.py`** — the pre-PR suite now runs `check_consistency --mode strict`: a
  no-op gate while all rules are warn-only, **live the instant a rule's `severity` flips**. So
  graduation = change one field, no wire-in edit.
- **`tests/unit/scripts/test_check_consistency.py`** — +4 tests (severity inheritance for a
  graduated rule · warn-only rules stay warnings · every rule carries a graduation note · `--list-rules`
  prints severity + status). 33 pass.
- **`docs/planning/repo-consistency-linter-plan-2026-06-17.md`** — graduation tracker table
  (severity · status · clean-since/blocker per rule) + updated step 3.
- **Ledger reconcile (Q-0166):** added the missing #1053/#1055/#1060/#1061 entries (the ledger
  checker flagged them); trimmed the oldest live entry (#1028) to the archive (20-entry soft
  ratchet); re-pointed the ▶ Next action to the graduation-rails state.

All rules stay **warn-only** this session. Tracker: `edit_in_place` BLOCKED (17 `views/ai/`,
AI-nav redesign); `back_button` / `panel_base_class` / `select_option_truncation` CANDIDATE
(clean since #1059/#1057/#1056, all 2026-06-19).

## Continuation (the handoff)

The flip is now a **one-field change**. A future session runs `python3.10
scripts/check_consistency.py --list-rules`, confirms a CANDIDATE rule has stayed at 0 across a
couple more sessions, then flips its `severity` to `"error"` in `RULES` — `back_button` /
`select_option_truncation` first (`panel_base_class` is the lowest-value flip; the arch
`baseview_inheritance` ratchet already errors on it). Optionally also add the strict step to
`code-quality.yml` so it gates auto-merge (the pre-PR suite is advisory). Rule 1 stays blocked
until the AI-nav plan (#1060) PR 2 clears its 17 — that needs a runtime/live-guild session
(`needs-hermes-review`).

## Context delta

- **Pointed to and needed:** the linter plan's step-3 "graduation" sentence + #1058/#1059's triage
  records gave the exact rule states; the ▶ Next action named "graduation prep" as the slice.
- **Discovered by hand:** `check_consistency` was **not wired into CI or pre-commit at all** (only
  run manually) and `severity` was hardcoded on `Finding` with no per-rule mechanism — so "graduation
  prep" was named but no rails existed. Built them; the flip was a multi-step change, now it's one
  field.

## ⟲ Previous-session review (Q-0102)

The previous slice (#1060) did well to connect the warn-only backlog to the *product* work that
clears it (promoting the AI-nav idea to unblock rule 1), and its session idea was precisely the
per-rule graduation-blocker tracker. What it left undone: it named "graduation prep" as the next
slice on rule *counts* alone, without noting that the graduation *mechanism* didn't exist yet
(severity was hardcoded; the linter wasn't in any CI/pre-PR path) — so this session rediscovered
that the flip was not a one-liner. **System improvement:** when a session names "X is the next
slice," it should state whether the *machinery* for X exists, not just the data state — a one-line
"mechanism: present/absent" note in the handoff would save the next session the rediscovery hop.
Also: #1060's per-rule-tracker idea was small enough to have shipped in the same session it was
conceived; capturing-not-building added a hop (this session built it).

## 💡 Session idea (Q-0089)

**A "graduation auto-eligibility" verdict in `--list-rules`.** The flip gate is "stays clean across a
couple more sessions" — today a human eyeballs the clean-since marker. Extend `--list-rules` (or a
tiny companion) to read git history and count merged PRs that *touched `disbot/views/`* since a
rule's `clean since` marker, then print a deterministic `ELIGIBLE` / `N more views-PRs` verdict per
CANDIDATE rule. That turns the soft "couple more sessions" gate into a machine readout, closing the
graduation loop the same way the ledger/cadence checkers made reconciliation due-ness mechanical.
Distinct from #1058's `--diff` baseline idea (which regression-guards *new* findings); this is about
*when a clean rule may graduate*. Captured, not built.

## 📊 Doc audit (Q-0104)

- `check_current_state_ledger.py --strict` ✓ (last 15 merged PRs present); `check_docs.py --strict` ✓
  (Recently-shipped back to the 20 ratchet); the linter plan's graduation table is reachable and
  current; the ▶ Next action reflects the shipped rails.
- **New owner decisions:** none (Q-0170 the linter, Q-0172 the idea→plan gate are already recorded).
- Nothing from this session lives only in chat — the mechanism is in source + the plan tracker.

## 📤 Run report

- **Did:** built the consistency-linter graduation rails (per-rule `severity` + `--list-rules`
  tracker + pre-PR strict gate), making the warn-only→error flip a one-field change; reconciled the
  ledger drift (#1053/#1055/#1060/#1061) on sight. · **Outcome:** shipped (auto-merge armed; born-red
  card flipped to complete as the final step).
- **Shipped:** #1063 — `check_consistency.py` severity rails · `check_quality.py` wire-in ·
  +4 tests · plan graduation tracker · current-state ledger catch-up + next-action.
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** `none`
- **⚑ Owner manual steps:** `none`
- **⚑ Self-initiated:** **YES** — empty scheduled fire with no work order; took the documented
  ▶ Next ungated startable (consistency-linter graduation prep) and built the graduation *mechanism*
  unprompted, plus implemented #1060's captured per-rule-tracker idea (Q-0172 / Q-0015). No new
  idea→plan promotion; no rule flipped to error (gated on a couple more clean sessions). Docs/tooling
  only — reversible.
- **↪ Next:** flip a CANDIDATE rule to error once it stays at 0 a couple more sessions
  (`--list-rules` confirms); execute the AI-nav plan (#1060) PR 1 in a runtime session to start
  clearing rule 1's 17.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs this session | 1 (#1063) |
| Files touched | 6 (2 scripts · 1 test · 1 plan · 2 ledger docs) |
| Tests added | 4 (33 total in the linter suite); full suite 10664 passed |
| Ideas groomed (Q-0015) | 1 (#1060's per-rule tracker idea → built as `--list-rules`) |
| New ideas contributed (Q-0089) | 1 (graduation auto-eligibility verdict) |
| Ledger drift fixed (Q-0166) | 4 entries (#1053/#1055/#1060/#1061) |
| CI-red rounds | 1 (born-red session gate, by design) |
| Repo-rule trips | 0 |
