# 2026-06-22 — Help reachability guard (orphan check)

> **Status:** `in-progress`

Self-initiated (Q-0172), owner-greenlit follow-up to the help-menu regrouping
(#1290) + Advanced removal (#1294). With the "All Commands / Advanced" catch-all
gone, an un-homed subsystem is now *completely unreachable* from the menu — so a
standing guard that asserts "every subsystem is homed" graduated from
nice-to-have to load-bearing.

## What I'm about to do
- Add a `check_reachability()` + `--check` CLI mode to
  `tools/sim/help_menu_grouping_sim.py`: exits non-zero on any orphan
  (parent_hub-less non-hub subsystem), section over the 12-item dropdown page,
  or feature needing > 3 clicks.
- Wire it as a CI-enforced invariant: `tests/unit/invariants/test_help_reachability.py`
  (runs in the existing pytest suite — no workflow YAML change), plus a
  has-teeth test proving the guard catches a synthetic orphan.
