# 2026-06-19 — BUG-0018 root-fix: stop `site.json` hard-equality test reddening on idea-doc churn

> **Status:** `complete`

## What I'm about to do

Dispatch run, no work order → bugs-first. BUG-0018 (bug book) is recorded **FIXED (immediate)**
but with a **root-fix RECOMMENDED** and left open as a recurring trap: the hard byte-equality test
`test_committed_site_json_matches_a_fresh_build` compares `commands[]` in full, but
`commands[].linked_ideas` **and** `commands[].status` are derived from `docs/ideas/` (+ the bug
book), which churns far more often than `site.json` is regenerated. So every idea-doc PR silently
drifts `site.json` and reddens `main` between regenerations.

Implementing the documented recommendation (a): exclude the high-churn **idea/bug-derived** command
fields (`linked_ideas`, `status`) from the **hard** equality assertion — the stable command fields
(name/aliases/category/cooldown/permissions/usage/description/use_cases/examples/notes) stay pinned —
and rely on the already-existing **warn-only** generated-artifact freshness umbrella
(`check_generated_artifacts_fresh.py`, #1027) for the structural identity of those derived fields.
This is a test-contract change only — no producer/runtime change.

## What shipped (PR #1143)

- `tests/unit/scripts/test_export_dashboard_data.py` — `test_committed_site_json_matches_a_fresh_build`
  now strips `_VOLATILE_COMMAND_FIELDS = ("linked_ideas", "status")` from each command before the hard
  `commands` equality (via a `_stable_commands` helper); the other families (`counts`/`catalogue`/
  `bot_changelog`) and the stable command fields stay byte-pinned.
- `docs/health/bug-book.md` — BUG-0018 → **FIXED (root)**; recorded recommendation (a), why `status`
  was excluded too (not just `linked_ideas`), and why (b) (auto-regen) was rejected.
- Verified: full CI mirror green (`check_quality.py --full`, 10900 passed); `check_generated_artifacts_fresh`
  reports all 4 artifacts fresh (the warn-only umbrella that now solely covers the derived-field identity).

## ⟲ Previous-session review (Q-0102)

The prior dispatch run (PR #1120) handled BUG-0018 correctly *for the moment* — it regenerated the
artifact and went green — but it stopped at the symptom and explicitly punted the root cause to "the
owner / reconciliation routine" as "a contract decision." That deferral was the miss: a recurring
CI-reddening trap with a clearly-specified recommended fix (a) is squarely a bugs-first, contained,
reversible job the dispatch routine should *close*, not defer (CLAUDE.md "Bugs first, durably" +
Q-0166 "don't leave drift you've already spotted"). It also under-scoped the fix to `linked_ideas`
only, missing that `status` is equally idea-derived. **System improvement surfaced:** when a bug-book
entry is logged `FIXED (immediate) / root-fix RECOMMENDED`, that is itself a standing dispatch backlog
signal — a contained recommended root-fix shouldn't wait for a human. (Captured as the session idea.)

## 💡 Session idea (Q-0089)

Add a tiny warn-only `check_bug_book_rootfix_backlog.py` guard (stdlib, Q-0105 disposable) that lists
any bug-book entry whose status contains `RECOMMENDED` / `root-fix RECOMMENDED` / `immediate` but not a
terminal `FIXED (root)` — surfacing "symptom-fixed but root-fix still owed" entries as a dispatch
backlog the next empty-fire run can pick up, the same way `check_plan_backlog` surfaces thin plans.
Rationale: this very session existed because such an entry sat un-promoted; a guard would have flagged it.

## 📤 Run report

- **Run type:** routine · dispatch
- **PR:** #1143 (BUG-0018 root-fix)
- **⚑ Owner-decisions:** none
- **⚑ Owner-manual-steps:** none
- **⚑ Self-initiated:** none (bugs-first root-fix of an OPEN-ish bug-book item; no idea→plan promotion)
