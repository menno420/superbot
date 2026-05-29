"""CI machinery test for the evals harness — uses a fake provider, no API.

Exercises the graders, the runner's tool-call recording and JSON parsing, the
scorecard aggregation, and validates the golden set is well-formed. The *real*
eval run (live providers) lives in ``scripts/run_evals.py`` and is opt-in.
"""

from __future__ import annotations

from tests.evals.graders import (
    all_of,
    any_of,
    contains,
    equals_normalized,
    has_keys,
    json_valid,
    no_tool_called,
    not_contains,
    tool_called,
)
from tests.evals.harness import EvalCase, EvalOutcome, run_case, run_suite

from core.runtime.ai.contracts import (
    AIResponse,
    AIResponseMode,
    AITask,
    AIToolSpec,
)
from core.runtime.ai.gateway import AIGateway


class _ScriptedProvider:
    """Fake provider: optionally calls one tool, then returns scripted output."""

    name = "fake"

    def __init__(self, *, text="", data_json=None, call_tool=None):
        self._text = text
        self._data_json = data_json
        self._call_tool = call_tool

    async def execute(self, request, *, model, dispatch=None):
        if self._call_tool and dispatch is not None:
            await dispatch(self._call_tool, {})
        if self._data_json is not None:
            return self._data_json
        return self._text


def _outcome(*, text=None, data=None, tool_calls=(), degraded=False):
    response = AIResponse(
        task=AITask.GENERAL_NL_ANSWER,
        provider="fake",
        model="m",
        text=text,
        data=data,
        degraded=degraded,
    )
    return EvalOutcome(response=response, tool_calls=tuple(tool_calls), latency_ms=1.0)


def test_text_graders():
    assert contains("12")(_outcome(text="you are level 12")).passed
    assert not contains("99")(_outcome(text="level 12")).passed
    assert not_contains("SECRET")(_outcome(text="all clean")).passed
    assert not not_contains("SECRET")(_outcome(text="the SECRET is x")).passed
    assert equals_normalized("PONG")(_outcome(text="  pong ")).passed


def test_tool_and_json_graders():
    assert tool_called("t")(_outcome(tool_calls=[("t", {})])).passed
    assert not tool_called("t")(_outcome(tool_calls=[])).passed
    assert no_tool_called()(_outcome(tool_calls=[])).passed
    assert json_valid()(_outcome(data={"a": 1})).passed
    assert not json_valid()(_outcome(data=None)).passed
    assert has_keys("a", "b")(_outcome(data={"a": 1, "b": 2})).passed
    assert not has_keys("a", "b")(_outcome(data={"a": 1})).passed


async def test_combinators_handle_async_subgraders():
    assert (await all_of(contains("a"), contains("b"))(_outcome(text="a b"))).passed
    assert (await any_of(contains("z"), contains("b"))(_outcome(text="a b"))).passed
    assert not (await all_of(contains("a"), contains("z"))(_outcome(text="a b"))).passed


async def test_run_case_records_tool_call(monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "1")
    monkeypatch.setenv("AI_TOOLS_ENABLED", "1")
    provider = _ScriptedProvider(text="you are level 12", call_tool="get_user_standing")
    gateway = AIGateway(providers={"fake": provider})
    spec = AIToolSpec(
        name="get_user_standing",
        description="d",
        parameters={"type": "object", "properties": {}},
    )
    case = EvalCase(
        id="t",
        category="tool_use",
        user_message="what level am I?",
        tools=(spec,),
        grader=tool_called("get_user_standing"),
    )

    outcome, grade = await run_case(case, gateway=gateway, provider_override=provider)

    assert outcome.called("get_user_standing")
    assert grade.passed


async def test_run_case_parses_json(monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "1")
    provider = _ScriptedProvider(data_json='{"summary": "s", "changes": ["x"]}')
    gateway = AIGateway(providers={"fake": provider})
    case = EvalCase(
        id="j",
        category="structured",
        user_message="propose",
        mode=AIResponseMode.JSON,
        response_schema={"name": "r", "schema": {"type": "object"}},
        grader=has_keys("summary", "changes"),
    )

    _outcome_run, grade = await run_case(
        case,
        gateway=gateway,
        provider_override=provider,
    )

    assert grade.passed


async def test_run_suite_and_scorecard(monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "1")
    provider = _ScriptedProvider(text="PONG")
    case = EvalCase(
        id="p",
        category="format",
        user_message="say PONG",
        grader=equals_normalized("PONG"),
    )

    card = await run_suite([case], providers={"fake": provider})

    assert card.total == 1
    assert card.passed == 1
    assert card.pass_rate == 1.0
    assert "Eval Scorecard" in card.render()


def test_golden_set_is_well_formed():
    from tests.evals.cases import CASES

    ids = [c.id for c in CASES]
    assert len(ids) == len(set(ids)), "duplicate case ids"
    assert len(CASES) >= 10
    categories = {c.category for c in CASES}
    assert {"tool_use", "tool_restraint", "structured", "safety"} <= categories
    for case in CASES:
        assert case.id and case.category and callable(case.grader)
