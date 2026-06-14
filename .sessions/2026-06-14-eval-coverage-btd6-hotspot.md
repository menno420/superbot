# Session: P1-1 — close the eval-coverage gap on the BTD6 defect hotspot

> **Status:** `complete`

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

## Shipped
- **`tests/evals/cases.py`** — 6 golden tool-selection probes for the highest-value uncovered BTD6
  tools, each modeled on a real live miss: `btd6_round_cash` (ABR range, BUG-0010) · `btd6_boss_lookup`
  (per-tier Lych HP, BUG-0002) · `btd6_map_lookup` ("which maps have water", design Update 5 #2) ·
  `btd6_paragon_stats_at_degree` (non-linear scaling) · `btd6_round_composition` · `btd6_answerability`
  (self-awareness). Each asserts the model reaches for the **right** deterministic tool. `GOLDEN_SET_VERSION`
  → `2026-06-14.2`.
- **`tests/evals/test_eval_coverage.py`** — dog-fooded the #879 ratchet exactly as designed: removed
  the 6 from `_ACK_BTD6_TOOLS` and raised `_TOOL_COVERAGE_FLOOR` **8 → 14**. Coverage is now **14/34**.

## Verified
`check_quality --full` green (**9645 passed**) · 41 `tests/evals/` tests pass · coverage introspection
confirms **14/34** tools referenced · no `disbot/` change (architecture unaffected, 0 errors). PR
**#881** (born-red → flipped complete last).

## 💡 Session idea (Q-0089)
**Routing-confusion probe pairs:** add golden cases that pin the model picks the *right* one of a
similarly-named BTD6 tool/entity pair — `btd6_round_cash` vs `btd6_round_composition`,
`btd6_paragon_calculate` vs `btd6_paragon_stats_at_degree`, and the PMFC↔POD entity substitution the
absence-claim design doc flagged (Update 5 #1). These directly target the *entity/tool-substitution*
failure class (the most dangerous live miss: a confident answer about the wrong subject), which
single-tool probes don't stress. Dedup-checked: no existing routing-confusion-pair idea.

## ⟲ Previous-session review (Q-0102)
Reviewing **#879 (the drift guard):** the right tool, built well (self-cleaning, meta-tested). **What
it left:** it created the instrument but left the gap *fully* at 8/34 with 26 acknowledged — a freshly
built ratchet that had never been *moved*, so "shrink the ack list" was only described, not
demonstrated. **System improvement (acted on this session):** **ship a ratchet already moved one
notch.** When you introduce a coverage/drift ratchet, de-acknowledge a few entries in the *same or
the very next* PR so the intended motion ("pick one off the pick-list") is demonstrated, not just
documented — otherwise a large acknowledged set reads as a permanent allowlist and never shrinks.
This session moved it 8 → 14 on the highest-value (hotspot) entries.

## Doc audit (Q-0104)
`check_docs --strict` ✓ · `check_quality --full` ✓ · no owner decision this session (priority was
derived: P1-1 > P1-3, P1-3 already airtight on the active tracks, so close the measured P1-1 gap on
the defect hotspot — no router entry). Ledger: folded #881 into the `#878 + #879` entry (one eval
arc → ratchet stays at 20); updated the AI map's coverage number 8/34 → 14/34.
**Grooming (Q-0015):** turned the #879 ratchet from a static gate into a *moving* one and advanced the
literal #1 priority (P1-1 eval coverage) on the area with the worst live-defect record (BTD6).
