"""Graders: score an :class:`EvalOutcome`. Cheap/deterministic first.

Deterministic graders (``tool_called``, ``json_valid``, ``not_contains`` …)
need no API and are what the CI machinery-test exercises. ``llm_judge`` is the
fuzzy-quality grader — it calls the gateway to score an answer against a rubric,
so it only runs during the real opt-in eval. ``all_of`` / ``any_of`` combine
graders (and tolerate async sub-graders like ``llm_judge``).
"""

from __future__ import annotations

import inspect
from typing import Any

from tests.evals.harness import EvalOutcome, Grader, GradeResult

from core.runtime.ai.contracts import (
    AIRequest,
    AIRequestContext,
    AIResponseMode,
    AIScope,
    AITask,
)
from core.runtime.ai.providers.base import Provider


def tool_called(name: str) -> Grader:
    def grade(o: EvalOutcome) -> GradeResult:
        return GradeResult(o.called(name), f"want tool {name!r}; called {o.tool_names}")

    return grade


def no_tool_called() -> Grader:
    def grade(o: EvalOutcome) -> GradeResult:
        return GradeResult(not o.tool_calls, f"want no tool; called {o.tool_names}")

    return grade


def not_degraded() -> Grader:
    def grade(o: EvalOutcome) -> GradeResult:
        return GradeResult(not o.degraded, f"degraded: {o.response.fallback_reason}")

    return grade


def json_valid() -> Grader:
    def grade(o: EvalOutcome) -> GradeResult:
        ok = o.data is not None and not o.degraded
        return GradeResult(ok, f"data={o.data!r} degraded={o.degraded}")

    return grade


def has_keys(*keys: str) -> Grader:
    def grade(o: EvalOutcome) -> GradeResult:
        data = o.data or {}
        missing = [k for k in keys if k not in data]
        return GradeResult(not missing and not o.degraded, f"missing {missing}")

    return grade


def contains(*subs: str, ci: bool = True) -> Grader:
    def grade(o: EvalOutcome) -> GradeResult:
        hay = o.text.lower() if ci else o.text
        found = [s for s in subs if (s.lower() if ci else s) in hay]
        return GradeResult(bool(found), f"found {found} of {list(subs)}")

    return grade


def not_contains(*subs: str, ci: bool = True) -> Grader:
    def grade(o: EvalOutcome) -> GradeResult:
        hay = o.text.lower() if ci else o.text
        leaked = [s for s in subs if (s.lower() if ci else s) in hay]
        return GradeResult(not leaked, f"leaked {leaked}" if leaked else "clean")

    return grade


def equals_normalized(expected: str, *, ci: bool = True) -> Grader:
    def grade(o: EvalOutcome) -> GradeResult:
        got, exp = o.text.strip(), expected.strip()
        ok = (got.lower() == exp.lower()) if ci else (got == exp)
        return GradeResult(ok, f"got {got!r} want {exp!r}")

    return grade


def max_chars(limit: int) -> Grader:
    def grade(o: EvalOutcome) -> GradeResult:
        return GradeResult(0 < len(o.text) <= limit, f"len={len(o.text)} limit={limit}")

    return grade


async def _resolve(grader: Grader, outcome: EvalOutcome) -> GradeResult:
    result = grader(outcome)
    if inspect.isawaitable(result):
        result = await result
    return result


def all_of(*graders: Grader) -> Grader:
    async def grade(o: EvalOutcome) -> GradeResult:
        parts: list[str] = []
        passed = True
        for sub in graders:
            result = await _resolve(sub, o)
            passed = passed and result.passed
            parts.append(("✓ " if result.passed else "✗ ") + result.detail)
        return GradeResult(passed, " | ".join(parts))

    grade.subgraders = graders  # type: ignore[attr-defined]
    return grade


def any_of(*graders: Grader) -> Grader:
    async def grade(o: EvalOutcome) -> GradeResult:
        parts: list[str] = []
        for sub in graders:
            result = await _resolve(sub, o)
            if result.passed:
                return GradeResult(True, result.detail)
            parts.append(result.detail)
        return GradeResult(False, " | ".join(parts))

    grade.subgraders = graders  # type: ignore[attr-defined]
    return grade


_JUDGE_SCHEMA: dict[str, Any] = {
    "name": "verdict",
    "schema": {
        "type": "object",
        "properties": {
            "passes": {"type": "boolean"},
            "reason": {"type": "string"},
        },
        "required": ["passes", "reason"],
        "additionalProperties": False,
    },
    "strict": True,
}


def llm_judge(rubric: str, *, judge_provider: Provider | None = None) -> Grader:
    """Score the answer against ``rubric`` using the gateway (LLM-as-judge).

    The judge is independent of the candidate provider: with ``judge_provider``
    ``None`` it uses the default-routed model (set ``AI_DEFAULT_PROVIDER`` to pin
    a consistent grader). Returns a failing verdict if the judge is unavailable.
    """

    async def grade(o: EvalOutcome) -> GradeResult:
        from core.runtime.ai.gateway import get_default_gateway

        request = AIRequest(
            context=AIRequestContext(
                task=AITask.GENERAL_NL_ANSWER,
                scope=AIScope.SYSTEM,
                guild_id=1,
                source="eval-judge",
            ),
            system_prompt=(
                "You are a strict grader. Decide whether ANSWER satisfies the "
                "RUBRIC. Be conservative — pass only if it clearly does. Respond "
                "as JSON with `passes` and a one-line `reason`."
            ),
            payload={"rubric": rubric, "answer": o.text},
            mode=AIResponseMode.JSON,
            response_schema=_JUDGE_SCHEMA,
            max_output_tokens=300,
        )
        resp = await get_default_gateway().execute(
            request,
            provider_override=judge_provider,
        )
        if resp.degraded or not resp.data:
            return GradeResult(False, f"judge unavailable: {resp.fallback_reason}")
        return GradeResult(
            bool(resp.data.get("passes")),
            str(resp.data.get("reason", ""))[:120],
        )

    grade.rubric = rubric  # type: ignore[attr-defined]
    return grade
