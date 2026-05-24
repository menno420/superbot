"""AIGateway pipeline tests — Module 1 of the AI/BTD6 plan.

The gateway is the single chokepoint for AI provider calls. These
tests pin the behaviour the plan requires:

* Typed :class:`AIResponse` returned for every code path.
* Degrades on provider exception (never re-raises).
* Degrades on timeout.
* Degrades when feature-flag is off.
* Redaction is invoked before the provider sees the payload.
* JSON-mode parses successfully into ``response.data``.
* JSON-mode flags ``degraded`` on bad JSON without raising.
* Safety prechecks short-circuit oversized payloads.
"""

from __future__ import annotations

import asyncio

import pytest

from core.runtime.ai.contracts import (
    AIRequest,
    AIRequestContext,
    AIResponseMode,
    AIScope,
    AITask,
)
from core.runtime.ai.diagnostics import DiagnosticsCollector
from core.runtime.ai.gateway import AIGateway
from core.runtime.ai.providers.base import ProviderUnavailableError


_DEFAULT_PAYLOAD = {"hello": "world"}


def _make_request(
    *,
    mode: AIResponseMode = AIResponseMode.JSON,
    payload: dict | None = None,
    system_prompt: str = "Test system prompt.",
    timeout: float = 5.0,
) -> AIRequest:
    return AIRequest(
        context=AIRequestContext(
            task=AITask.SETUP_SUGGEST,
            scope=AIScope.ADMIN,
            source="test",
        ),
        system_prompt=system_prompt,
        payload=_DEFAULT_PAYLOAD if payload is None else payload,
        mode=mode,
        timeout_seconds=timeout,
    )


class _FakeProvider:
    """Provider that returns a configurable text or raises."""

    name = "fake"

    def __init__(self, *, text: str | None = None, exc: Exception | None = None) -> None:
        self._text = text
        self._exc = exc
        self.received_request: AIRequest | None = None
        self.received_model: str | None = None

    async def execute(self, request: AIRequest, *, model: str) -> str:
        self.received_request = request
        self.received_model = model
        if self._exc is not None:
            raise self._exc
        if self._text is None:
            raise RuntimeError("FakeProvider configured with neither text nor exc")
        return self._text


@pytest.fixture(autouse=True)
def _enable_ai(monkeypatch):
    """Module 1 ships AI disabled by default; enable for these tests."""
    monkeypatch.setenv("AI_ENABLED", "1")
    yield


def _gateway_with(provider: _FakeProvider) -> tuple[AIGateway, DiagnosticsCollector]:
    collector = DiagnosticsCollector()
    gateway = AIGateway(providers={"fake": provider}, collector=collector)
    return gateway, collector


@pytest.mark.asyncio
async def test_gateway_returns_typed_ai_response():
    provider = _FakeProvider(text='{"answer": 42}')
    gateway, _ = _gateway_with(provider)

    request = _make_request()
    response = await gateway.execute(request, provider_override=provider)

    assert response.task is AITask.SETUP_SUGGEST
    assert response.provider == "fake"
    assert response.degraded is False
    assert response.data == {"answer": 42}
    assert response.text == '{"answer": 42}'


@pytest.mark.asyncio
async def test_gateway_degrades_on_provider_exception():
    provider = _FakeProvider(exc=RuntimeError("upstream rate limit"))
    gateway, collector = _gateway_with(provider)

    response = await gateway.execute(
        _make_request(), provider_override=provider,
    )

    assert response.degraded is True
    assert "rate limit" in (response.fallback_reason or "")
    snap = collector.snapshot()
    assert snap.failures_observed == 1
    assert snap.degraded is True


@pytest.mark.asyncio
async def test_gateway_degrades_on_timeout():
    class _SlowProvider:
        name = "fake"

        async def execute(self, request: AIRequest, *, model: str) -> str:
            await asyncio.sleep(10)  # well past the 0.05s timeout below
            return "never"

    provider = _SlowProvider()
    gateway = AIGateway(providers={"fake": provider}, collector=DiagnosticsCollector())

    request = _make_request(timeout=0.05)
    response = await gateway.execute(request, provider_override=provider)

    assert response.degraded is True
    assert response.fallback_reason is not None
    assert "timeout" in response.fallback_reason


@pytest.mark.asyncio
async def test_gateway_degrades_on_provider_unavailable():
    provider = _FakeProvider(exc=ProviderUnavailableError("OPENAI_API_KEY missing"))
    gateway, _ = _gateway_with(provider)

    response = await gateway.execute(_make_request(), provider_override=provider)

    assert response.degraded is True
    assert "OPENAI_API_KEY missing" in (response.fallback_reason or "")


@pytest.mark.asyncio
async def test_gateway_redacts_payload_before_provider_call():
    """The provider must never see un-redacted strings."""
    provider = _FakeProvider(text='{"ok": true}')
    gateway, _ = _gateway_with(provider)

    sensitive_payload = {
        "user_email": "alice@example.com",
        "api_key": "sk-1234567890abcdefghi",
        "nested": {"db_url": "postgres://user:secret@host/db"},
    }
    request = _make_request(payload=sensitive_payload)
    await gateway.execute(request, provider_override=provider)

    assert provider.received_request is not None
    received = provider.received_request.payload
    assert "alice@example.com" not in str(received)
    assert "sk-1234567890" not in str(received)
    assert "postgres://" not in str(received)


@pytest.mark.asyncio
async def test_gateway_json_mode_parses_data():
    provider = _FakeProvider(text='{"recommendations": [{"id": 1}]}')
    gateway, _ = _gateway_with(provider)

    response = await gateway.execute(
        _make_request(mode=AIResponseMode.JSON), provider_override=provider,
    )

    assert response.degraded is False
    assert response.data == {"recommendations": [{"id": 1}]}


@pytest.mark.asyncio
async def test_gateway_json_mode_marks_degraded_on_bad_json():
    provider = _FakeProvider(text="not actually json {{")
    gateway, collector = _gateway_with(provider)

    response = await gateway.execute(
        _make_request(mode=AIResponseMode.JSON), provider_override=provider,
    )

    assert response.degraded is True
    assert response.fallback_reason is not None
    assert "invalid_json" in response.fallback_reason
    snap = collector.snapshot()
    assert snap.failures_observed == 1


@pytest.mark.asyncio
async def test_gateway_text_mode_returns_raw_text():
    provider = _FakeProvider(text="plain prose answer")
    gateway, _ = _gateway_with(provider)

    response = await gateway.execute(
        _make_request(mode=AIResponseMode.TEXT), provider_override=provider,
    )

    assert response.degraded is False
    assert response.text == "plain prose answer"
    assert response.data is None


@pytest.mark.asyncio
async def test_gateway_short_circuits_oversized_payload():
    provider = _FakeProvider(text='{"ok": true}')
    gateway, _ = _gateway_with(provider)

    big = {"data": "x" * (300 * 1024)}  # 300 KiB — over the 256 KiB cap
    request = _make_request(payload=big)
    response = await gateway.execute(request, provider_override=provider)

    assert response.degraded is True
    assert "safety" in (response.fallback_reason or "")
    assert provider.received_request is None  # provider never invoked


@pytest.mark.asyncio
async def test_gateway_short_circuits_empty_payload():
    provider = _FakeProvider(text='{"ok": true}')
    gateway, _ = _gateway_with(provider)

    request = _make_request(payload={})
    response = await gateway.execute(request, provider_override=provider)

    assert response.degraded is True
    assert "empty payload" in (response.fallback_reason or "")
    assert provider.received_request is None


@pytest.mark.asyncio
async def test_gateway_respects_feature_flag(monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "0")
    provider = _FakeProvider(text='{"ok": true}')
    gateway = AIGateway(providers={"fake": provider}, collector=DiagnosticsCollector())

    # No override: routing resolves to default provider, but the feature
    # flag check should fire first and degrade without calling anyone.
    request = _make_request()
    response = await gateway.execute(request)

    assert response.degraded is True
    assert "feature_flag" in (response.fallback_reason or "")
    assert provider.received_request is None


@pytest.mark.asyncio
async def test_gateway_provider_override_bypasses_feature_flag():
    """provider_override is the test/test-injection seam; flag does not apply."""
    provider = _FakeProvider(text='{"ok": true}')
    gateway, _ = _gateway_with(provider)

    response = await gateway.execute(_make_request(), provider_override=provider)
    assert response.degraded is False
    assert provider.received_request is not None
