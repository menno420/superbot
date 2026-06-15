"""OpenAIProvider unit tests.

The provider is the only module that imports the OpenAI SDK
directly. These tests inject a duck-typed client (``MagicMock``
shaped like ``AsyncOpenAI``) and verify:

* The provider passes the schema to ``chat.completions.create``
  when ``AIResponseMode.JSON`` is requested.
* It falls back to ``response_format={"type": "json_object"}``
  when no schema is provided.
* It raises :class:`ProviderUnavailableError` when no client and no API
  key are available.
* It extracts the assistant message text correctly.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from core.runtime.ai.contracts import (
    AIRequest,
    AIRequestContext,
    AIResponseMode,
    AIScope,
    AITask,
)
from core.runtime.ai.providers.base import ProviderUnavailableError
from core.runtime.ai.providers.openai_provider import OpenAIProvider


def _response(content: str | None) -> MagicMock:
    message = MagicMock()
    message.content = content
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice] if content is not None else []
    return response


def _make_request(
    *,
    mode: AIResponseMode = AIResponseMode.JSON,
    response_schema: dict | None = None,
) -> AIRequest:
    return AIRequest(
        context=AIRequestContext(
            task=AITask.SETUP_SUGGEST, scope=AIScope.ADMIN, source="test",
        ),
        system_prompt="system",
        payload={"hello": "world"},
        mode=mode,
        response_schema=response_schema,
    )


@pytest.mark.asyncio
async def test_provider_uses_json_schema_when_provided():
    client = MagicMock()
    client.chat = MagicMock()
    client.chat.completions = MagicMock()
    client.chat.completions.create = AsyncMock(
        return_value=_response('{"ok": true}'),
    )
    provider = OpenAIProvider(client=client)

    schema = {"name": "Recs", "schema": {"type": "object"}, "strict": True}
    request = _make_request(response_schema=schema)
    out = await provider.execute(request, model="gpt-4o-mini")

    assert out == '{"ok": true}'
    call_kwargs = client.chat.completions.create.await_args.kwargs
    assert call_kwargs["model"] == "gpt-4o-mini"
    assert call_kwargs["response_format"] == {
        "type": "json_schema",
        "json_schema": schema,
    }


@pytest.mark.asyncio
async def test_provider_falls_back_to_json_object_without_schema():
    client = MagicMock()
    client.chat = MagicMock()
    client.chat.completions = MagicMock()
    client.chat.completions.create = AsyncMock(
        return_value=_response('{"ok": true}'),
    )
    provider = OpenAIProvider(client=client)

    out = await provider.execute(_make_request(), model="gpt-4o-mini")
    assert out == '{"ok": true}'
    call_kwargs = client.chat.completions.create.await_args.kwargs
    assert call_kwargs["response_format"] == {"type": "json_object"}


@pytest.mark.asyncio
async def test_provider_text_mode_omits_response_format():
    client = MagicMock()
    client.chat = MagicMock()
    client.chat.completions = MagicMock()
    client.chat.completions.create = AsyncMock(
        return_value=_response("plain text"),
    )
    provider = OpenAIProvider(client=client)

    out = await provider.execute(
        _make_request(mode=AIResponseMode.TEXT), model="gpt-4o-mini",
    )
    assert out == "plain text"
    call_kwargs = client.chat.completions.create.await_args.kwargs
    assert "response_format" not in call_kwargs


@pytest.mark.asyncio
async def test_provider_raises_provider_unavailable_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    provider = OpenAIProvider()  # no client, no api_key

    with pytest.raises(ProviderUnavailableError):
        await provider.execute(_make_request(), model="gpt-4o-mini")


@pytest.mark.asyncio
async def test_provider_raises_on_empty_choices():
    client = MagicMock()
    client.chat = MagicMock()
    client.chat.completions = MagicMock()
    client.chat.completions.create = AsyncMock(return_value=_response(None))
    provider = OpenAIProvider(client=client)

    with pytest.raises(RuntimeError, match="empty response"):
        await provider.execute(_make_request(), model="gpt-4o-mini")
