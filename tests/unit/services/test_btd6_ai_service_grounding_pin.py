"""Regression pin for #354's always-on live grounding in answer_question.

The grounding flow is best-effort and ALWAYS attached: every call to
``answer_question`` invokes ``btd6_context_service.build`` and tries to
populate ``BTD6Response.live_facts``. Failures are swallowed and the
deterministic baseline is returned unchanged.

A previous plan revision suggested making this opt-in via a kwarg —
this test file pins the current behaviour so that suggestion can't be
silently re-introduced.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from services import btd6_ai_service, btd6_context_service


@pytest.mark.asyncio
async def test_answer_question_calls_build_exactly_once(monkeypatch):
    spy = AsyncMock(
        return_value=btd6_context_service.BTD6Context(
            facts=(),
            source_summary="ignored",
            confidence=0.0,
        ),
    )
    monkeypatch.setattr(btd6_context_service, "build", spy)

    await btd6_ai_service.answer_question("dart monkey")

    assert spy.await_count == 1


@pytest.mark.asyncio
async def test_empty_facts_leaves_response_unchanged(monkeypatch):
    async def _empty(_text):
        return btd6_context_service.BTD6Context(
            facts=(),
            source_summary="ignored",
            confidence=0.0,
        )

    monkeypatch.setattr(btd6_context_service, "build", _empty)

    response = await btd6_ai_service.answer_question("dart monkey")
    assert response.live_facts == ()


@pytest.mark.asyncio
async def test_build_raising_does_not_break_answer(monkeypatch):
    async def _boom(_text):
        raise RuntimeError("DB down")

    monkeypatch.setattr(btd6_context_service, "build", _boom)

    response = await btd6_ai_service.answer_question("dart monkey")
    # The deterministic baseline is preserved.
    assert response is not None
    assert response.live_facts == ()


@pytest.mark.asyncio
async def test_non_empty_facts_flow_into_response(monkeypatch):
    async def _facts(_text):
        return btd6_context_service.BTD6Context(
            facts=("Reversed Loop — type=race (source: data.ninjakiwi.com)",),
            source_summary="data.ninjakiwi.com (Tier 1)",
            confidence=0.5,
        )

    monkeypatch.setattr(btd6_context_service, "build", _facts)

    response = await btd6_ai_service.answer_question("current race?")
    assert response.live_facts == (
        "Reversed Loop — type=race (source: data.ninjakiwi.com)",
    )


def test_no_opt_in_kwarg_on_answer_question():
    """Defensive pin: a previous plan suggested ``include_facts_context``;
    if that ever lands, it would silently regress the always-on
    grounding shipped in #354."""
    import inspect

    sig = inspect.signature(btd6_ai_service.answer_question)
    assert "include_facts_context" not in sig.parameters, (
        "answer_question must keep grounding always-on; do not add "
        "include_facts_context kwarg"
    )
