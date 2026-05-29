# AI evals

Capability tests for the model behind the gateway — *quality*, not plumbing.
`pytest` checks the wiring (loop, JSON parse, degradation); these check whether
the answers are actually **good**, and score **OpenAI vs Claude** on identical
inputs so you can decide which model each task should default to.

## Run it (opt-in — makes real, paid API calls)

```sh
RUN_EVALS=1 \
OPENAI_API_KEY=sk-... \
ANTHROPIC_API_KEY=sk-ant-... \
python3.10 scripts/run_evals.py --provider both
```

Flags: `--provider openai|anthropic|both`, `--threshold 0.8`, `--category tool_use`.
Set `AI_DEFAULT_PROVIDER` to pin the model used by the LLM-as-judge grader so
grading stays consistent across candidate providers.

The script exits non-zero if the overall pass rate is below `--threshold`, so it
can gate an opt-in (non-PR) CI job.

## What's covered

`tool_use` · `tool_restraint` · `structured` · `safety` (prompt-injection &
untrusted-data) · `grounding` (no fabrication) · `knowledge` · `format`
(instruction-following). See `cases.py`.

Graders are deterministic where possible (`tool_called`, `json_valid`,
`not_contains`, …); fuzzy-quality cases use `llm_judge` (LLM-as-judge against a
rubric).

## How it's built

- `harness.py` — `EvalCase` / `EvalOutcome` / `GradeResult`, the runner, and the
  per-provider `Scorecard`.
- `graders.py` — deterministic graders + `llm_judge` + `all_of` / `any_of`.
- `cases.py` — the golden set. Offers the **real** tool specs from
  `services.ai_tools` but executes deterministic stubs (no DB).
- `test_evals_harness.py` — the CI machinery test (fake provider, **no API**).

## Adding a case

Append an `EvalCase` to `CASES` in `cases.py`. Grow the set from real failures —
when someone reports a bad answer, add it here so it becomes a permanent
regression probe.
