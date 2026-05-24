"""BTD6 AI augmentation tests (Module 5).

Pins:

* When ``BTD6_AI_ENABLED`` is unset, ``augment_with_ai=True`` does
  NOT call the gateway.
* When ``BTD6_AI_ENABLED=1`` AND ``AI_ENABLED=1``, the gateway is
  called with a structured deterministic payload.
* When the gateway returns degraded, the deterministic response
  comes back unchanged.
* When the gateway returns a valid explanation, follow_up is
  populated with the AI prose.
* When the gateway raises, the deterministic response comes back
  unchanged.
* No provider SDK imports appear outside ``providers/`` (covered by
  the existing invariant test).
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from core.runtime.ai.contracts import (
    AIResponse,
    AITask,
)
from services import ai_gateway, btd6_ai_service


def _ai_response(
    *, data: dict | None = None, degraded: bool = False, reason: str | None = None,
) -> AIResponse:
    return AIResponse(
        task=AITask.HELP_ANSWER,
        provider="fake",
        model="fake-1",
        text=None,
        data=data,
        suggestions=(),
        latency_ms=12.3,
        degraded=degraded,
        fallback_reason=reason,
    )


@pytest.mark.asyncio
async def test_augmentation_disabled_skips_gateway(monkeypatch):
    monkeypatch.delenv("BTD6_AI_ENABLED", raising=False)
    monkeypatch.setenv("AI_ENABLED", "1")

    spy = AsyncMock()
    monkeypatch.setattr(ai_gateway, "execute", spy)

    response = await btd6_ai_service.answer_question(
        "Dart Monkey", augment_with_ai=True,
    )

    spy.assert_not_awaited()
    assert "Dart Monkey" in response.title


@pytest.mark.asyncio
async def test_ai_platform_disabled_skips_gateway(monkeypatch):
    monkeypatch.setenv("BTD6_AI_ENABLED", "1")
    monkeypatch.delenv("AI_ENABLED", raising=False)

    spy = AsyncMock()
    monkeypatch.setattr(ai_gateway, "execute", spy)

    response = await btd6_ai_service.answer_question(
        "Dart Monkey", augment_with_ai=True,
    )

    spy.assert_not_awaited()
    assert "Dart Monkey" in response.title


@pytest.mark.asyncio
async def test_augmentation_passes_deterministic_payload_to_gateway(monkeypatch):
    monkeypatch.setenv("BTD6_AI_ENABLED", "1")
    monkeypatch.setenv("AI_ENABLED", "1")

    called_request: list = []

    async def _capture(request):
        called_request.append(request)
        return _ai_response(data={"explanation": "Dart Monkey is the cheapest."})

    monkeypatch.setattr(ai_gateway, "execute", _capture)

    response = await btd6_ai_service.answer_question(
        "Dart Monkey", augment_with_ai=True,
    )

    assert len(called_request) == 1
    payload = called_request[0].payload
    # Provider sees the resolved IDs, not raw user prose verbatim.
    assert "deterministic_answer" in payload
    assert "query_summary" in payload
    assert "dart_monkey" in payload["query_summary"]["resolved_towers"]
    # Augmentation appended.
    assert "cheapest" in response.follow_up.lower()


@pytest.mark.asyncio
async def test_gateway_degraded_returns_deterministic(monkeypatch):
    monkeypatch.setenv("BTD6_AI_ENABLED", "1")
    monkeypatch.setenv("AI_ENABLED", "1")

    async def _degraded(_request):
        return _ai_response(degraded=True, reason="timeout:5s")

    monkeypatch.setattr(ai_gateway, "execute", _degraded)

    response = await btd6_ai_service.answer_question(
        "Dart Monkey", augment_with_ai=True,
    )
    # Deterministic follow_up untouched.
    assert "Ask about a specific upgrade tier" in (response.follow_up or "")


@pytest.mark.asyncio
async def test_gateway_exception_returns_deterministic(monkeypatch):
    monkeypatch.setenv("BTD6_AI_ENABLED", "1")
    monkeypatch.setenv("AI_ENABLED", "1")

    async def _raise(_request):
        raise RuntimeError("network blip")

    monkeypatch.setattr(ai_gateway, "execute", _raise)

    response = await btd6_ai_service.answer_question(
        "Dart Monkey", augment_with_ai=True,
    )
    assert "Dart Monkey" in response.title


@pytest.mark.asyncio
async def test_gateway_invalid_payload_returns_deterministic(monkeypatch):
    """Missing 'explanation' key or non-string → deterministic baseline."""
    monkeypatch.setenv("BTD6_AI_ENABLED", "1")
    monkeypatch.setenv("AI_ENABLED", "1")

    async def _bad(_request):
        return _ai_response(data={"unexpected": "shape"})

    monkeypatch.setattr(ai_gateway, "execute", _bad)

    response = await btd6_ai_service.answer_question(
        "Dart Monkey", augment_with_ai=True,
    )
    assert "Ask about a specific upgrade tier" in (response.follow_up or "")


@pytest.mark.asyncio
async def test_empty_explanation_does_not_overwrite_follow_up(monkeypatch):
    monkeypatch.setenv("BTD6_AI_ENABLED", "1")
    monkeypatch.setenv("AI_ENABLED", "1")

    async def _empty(_request):
        return _ai_response(data={"explanation": "   "})

    monkeypatch.setattr(ai_gateway, "execute", _empty)

    response = await btd6_ai_service.answer_question(
        "Dart Monkey", augment_with_ai=True,
    )
    assert "Ask about a specific upgrade tier" in (response.follow_up or "")


@pytest.mark.asyncio
async def test_default_path_does_not_call_gateway(monkeypatch):
    """augment_with_ai defaults to False; never call the gateway."""
    monkeypatch.setenv("BTD6_AI_ENABLED", "1")
    monkeypatch.setenv("AI_ENABLED", "1")

    spy = AsyncMock()
    monkeypatch.setattr(ai_gateway, "execute", spy)

    await btd6_ai_service.answer_question("Dart Monkey")
    spy.assert_not_awaited()
