# Session: P1-1 eval-coverage expansion — golden tool-selection probes (14 → 20/34)

> **Status:** `in-progress` — born-red session card (Q-0133). Flipped to `complete` as the
> deliberate final step.

**Branch:** `claude/eval-coverage-expansion-2026-06-15` · **Date:** 2026-06-15 · **Type:** P1-1 (S1 AI eval matrix)

## What I'm about to do

Continue the standing #1 priority (PR883's pointer): **continued eval-coverage expansion** off the
#879 `_ACK_UNCOVERED_TOOLS` pick-list, dog-fooding the self-cleaning drift guard exactly as #881 did
(8→14). Add **6 golden tool-selection probes** to `tests/evals/cases.py` for high-value uncovered
tools whose triggers are unambiguous (verified against the real tool specs):
`get_ai_tool_catalog` · `btd6_cumulative_cost` · `btd6_paragon_requirements` ·
`btd6_monkey_knowledge_lookup` · `btd6_mode_lookup` · `btd6_list_roster`. Remove those 6 from the ack
sets, raise `_TOOL_COVERAGE_FLOOR` 14 → 20, bump `GOLDEN_SET_VERSION`. Tests-only, additive,
CI-runnable (the live probes need creds; the CI drift guard proves the coverage structurally).

(Close-out + enders + badge flip at the bottom as the final step.)
