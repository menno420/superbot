# Session: P1-1 eval-coverage expansion — golden tool-selection probes (14 → 20/34)

> **Status:** `complete` — PR #886; born-red card flipped as the deliberate final step (Q-0133).

**Branch:** `claude/eval-coverage-expansion-2026-06-15` · **Date:** 2026-06-15 · **Type:** P1-1 (S1 AI eval matrix)

## What this did

Continued the standing #1 priority (PR883's pointer) and the work I was mid-flight on before the #884
conflict fix: **eval-coverage expansion**, dog-fooding the #879 self-cleaning drift guard exactly as
#881 did. Added **6 golden tool-selection probes** to `tests/evals/cases.py` for high-value uncovered
tools (each verified against the real production tool spec, so the trigger is unambiguous):
`get_ai_tool_catalog` · `btd6_cumulative_cost` · `btd6_paragon_requirements` ·
`btd6_monkey_knowledge_lookup` · `btd6_mode_lookup` · `btd6_list_roster`. Removed those 6 from the
`_ACK_UNCOVERED_TOOLS` sets, raised `_TOOL_COVERAGE_FLOOR` **14 → 20**, bumped `GOLDEN_SET_VERSION`
(`2026-06-15.1`). Tests-only, additive; the live probes run with creds, the CI drift guard proves the
coverage structurally.

Verified: `tests/evals/` 41/41 · `check_quality --full` green (9674) · `check_architecture` 0 errors.

## Context delta

- Clean continuation — the #881 hotspot probes were a turn-key template right in `cases.py`, so the
  only real work was verifying each candidate tool's *actual* spec (so the user message genuinely
  triggers THAT tool, not a neighbour) before writing the probe. The pre-verification (dumping the 6
  specs) is what kept these from being filler probes.
- This is the **second PR of one chat session** (after the mining #884). The per-session enders
  (Q-0089 new idea · Q-0102 prev-session review · Q-0104 closing audit) were completed in the #884
  card; this card is the born-red gate + record for the #886 deliverable. Closing audit re-run here:
  `check_docs --strict` ✓ · `check_current_state_ledger --strict` ✓ (folded #886 into the eval entry,
  no new bullet — ratchet held at 20).

## Handoff

The eval pick-list still has tools to cover (`_ACK_UNCOVERED_TOOLS`: the remaining BTD6 lookups, the
`_ACK_SERVER_TOOLS` guild-introspection set, `get_ai_policy_explanation`, `diagnostics_health_snapshot`)
— the next tranche is the same turn-key pattern. But the **owner-steered priority remains the mining
lane** ([`planning/mining-structures-skill-tree-plan-2026-06-14.md`](../docs/planning/mining-structures-skill-tree-plan-2026-06-14.md));
the session-end `continue`-labeled issue points the next routine there.
