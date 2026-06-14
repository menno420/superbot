# Session: P1-1 — close the eval-coverage gap on the BTD6 defect hotspot

> **Status:** `in-progress`

**Branch:** `claude/wizardly-edison-xw34kb` · **PR:** (opening) · **Date:** 2026-06-14 · **Type:** AI hardening / eval coverage (P1-1; follows #878/#879)

## What I'm about to do (born-red declaration)
Advance the standing **#1 priority (P1-1)** by closing the coverage gap the #879 drift guard just
made measurable: only **8/34 tools** are eval-covered, and the uncovered set includes the **BTD6
tools — the live-defect hotspot** (#703/#706/#707/#709 were all BTD6 routing/grounding bugs).

Add golden tool-selection probes for the 6 highest-value uncovered BTD6 tools, modeled on real live
misses — `btd6_round_cash` (ABR, BUG-0010), `btd6_boss_lookup` (elite lych, BUG-0002),
`btd6_map_lookup` ("which maps have water"), `btd6_paragon_stats_at_degree` (non-linear scaling),
`btd6_round_composition`, `btd6_answerability` (self-awareness). Then **dog-food #879**: remove those
6 from the acknowledged-uncovered set and raise the coverage floor 8 → 14 (the ratchet working as
designed).

## Coordination
Bot tests only (`tests/evals/cases.py` + `tests/evals/test_eval_coverage.py`). No `disbot/` change.

_(filled in at session close: shipped / verified / idea / review / doc audit)_
