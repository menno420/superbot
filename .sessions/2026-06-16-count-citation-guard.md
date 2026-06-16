# Session — count-citation guard (soft check_docs rule)

> **Status:** `in-progress` — born-red per Q-0133; flips to `complete` as the final step.
> **Date:** 2026-06-16 · **Branch:** `claude/hopeful-meitner-772pv8` · **PR:** #961

## What I'm about to do

The owner-picked follow-on (#3 of the architecture-review thread): the **count-citation guard** — close
the drift loop the three #957 fixes opened (bare hand-maintained inventory counts in binding docs).

1. **`scripts/check_docs.py`** — a **soft** check (`inventory_count_flags` / `print_inventory_count_report`,
   never changes exit code, like the census ratchets): flag a bare `N migrations/workflows/extensions/
   cogs/subsystems` in a **binding** doc unless it cites a regen command (`scripts/*.py`), is marked
   `generated`, or carries `<!-- count-ok -->`. Pinned-to-code docs (`smoke-test-checklist`,
   `help-command-surface-map`, `ai-config-ownership`) are exempt — their own doc-tests guard their counts.
2. **`tests/unit/scripts/test_check_docs.py`** — 6 logic tests (uncited→flag · citations exempt ·
   adjacent-line citation · non-binding ignored · pinned exempt · silent-when-clean). Deliberately **no**
   repo zero-pinning test → keeps the guard genuinely soft (no FP hard-gate on a future legit count).
3. Idea docs updated: architecture-atlas #3 → shipped; `readiness-maps-cite-regen-command` → mechanism
   partially shipped (remaining: widen scope to `production-readiness/*`).

Design rationale: calibration grep showed the count pattern is widespread + often stale across non-binding
docs — a hard gate would red CI on dozens of pre-existing instances, against the repo's anti-FP-gate
culture. Soft + binding-scoped + pinned-exempt = clean zero-flag baseline now, useful nudge on any new
count. (The idea itself called for "a soft check_docs rule.")

(Close-out enders added at the bottom before the flip.)
