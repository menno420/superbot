# Session — 2026-06-23 · Close the new-subsystem checker's blind spots

> **Status:** `in-progress` — born-red HOLD card; flip to `complete` as the final step.

**Run type:** owner-directed. **Branch:** `claude/peaceful-franklin-klgw3f`.
**Trigger:** after the Karma build (PR #1332), the owner approved implementing the
"new-subsystem ripple" idea. On investigation, a scaffold + checker already exists
(`scripts/new_subsystem.py`, fronted by the `/new-subsystem` skill) — so the real value is
**auditing it against the Karma ground-truth and closing the gaps it misses**, not building a
parallel tool.

## What I'm about to do

Running `new_subsystem.py check` against the now-fully-wired `karma` surfaced **two** things:
1. A genuine drift in PR #1332 — karma is missing from `docs/repo-navigation-map.md` (the checker
   caught it). **Fix:** add the karma row.
2. The checker has **blind spots** — it does *not* verify three touch-points that actually broke
   Karma's CI (each cost a round of red): the **sector-folio map** (`docs/repo-sector-map.md`),
   the **extension-role overlay** (`architecture_rules/extension_roles.yaml`), and **config.py
   `INITIAL_EXTENSIONS` loading**. **Fix:** add those three checks to `build_checks`.

Deliverables: extend `scripts/new_subsystem.py` (+ its `tests/unit/scripts/test_new_subsystem.py`),
add the karma nav-map row, update the `/new-subsystem` skill's touch-point count, and re-badge the
`audited-score-subsystem-scaffold` idea (the generator half already existed).

## What changed

_(filled at close)_

## 💡 Session idea (Q-0089)

_(filled at close)_

## ⟲ Previous-session review (Q-0102)

_(filled at close)_

## 📋 Doc audit (Q-0104)

_(filled at close)_
