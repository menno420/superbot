"""OpenAI provider adapter — the only module that imports ``openai``.

The invariant test
``tests/unit/invariants/test_ai_btd6_boundaries.py::test_provider_sdk_imports_only_in_providers``
fails if any other production module imports the ``openai`` SDK
directly. All consumers route through
:class:`core.runtime.ai.gateway.AIGateway`.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from core.runtime.ai.contracts import AIRequest, AIResponseMode
from core.runtime.ai.providers.base import ProviderUnavailableError

logger = logging.getLogger("bot.runtime.ai.openai_provider")


class OpenAIProvider:
    """Async OpenAI chat-completions adapter with strict JSON schema.

    The adapter is constructed once per gateway. A test can inject a
    duck-typed ``client`` (e.g. a ``MagicMock`` shaped like
    ``AsyncOpenAI``) without importing the SDK.
    """

    name = "openai"

    def __init__(
        self,
        *,
        client: Any = None,
        api_key: str | None = None,
    ) -> None:
        self._client = client
        self._api_key = api_key

    def _ensure_client(self) -> Any:
        if self._client is not None:
            return self._client
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise ProviderUnavailableError(
                "openai package is not installed; install ``openai>=1.40.0`` "
                "or set AI provider to ``deterministic``.",
            ) from exc
        api_key = self._api_key or os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            raise ProviderUnavailableError(
                "OPENAI_API_KEY is not set; cannot construct OpenAI client.",
            )
        self._client = AsyncOpenAI(api_key=api_key)
        return self._client

    async def execute(self, request: AIRequest, *, model: str) -> str:
        client = self._ensure_client()
        user_payload = json.dumps(request.payload, default=str)
        messages = [
            {"role": "system", "content": request.system_prompt},
            {"role": "user", "content": user_payload},
        ]
        kwargs: dict[str, Any] = {"model": model, "messages": messages}
        if request.mode is AIResponseMode.JSON and request.response_schema:
            kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": request.response_schema,
            }
        elif request.mode is AIResponseMode.JSON:
            # JSON requested but no schema provided — fall back to the
            # SDK's loose JSON mode so callers still get parseable output.
            kwargs["response_format"] = {"type": "json_object"}

        response = await client.chat.completions.create(**kwargs)
        text = _extract_response_text(response)
        if text is None:
            raise RuntimeError("openai: empty response (no choices/message/content)")
        return text


def _extract_response_text(response: Any) -> str | None:
    """Pull the assistant message text out of a Chat Completions response."""
    choices = getattr(response, "choices", None)
    if not choices:
        return None
    first = choices[0]
    message = getattr(first, "message", None)
    if message is None:
        return None
    content = getattr(message, "content", None)
    if not content:
        return None
    return content
