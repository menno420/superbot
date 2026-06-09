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

from core.runtime.ai.contracts import (
    AIRequest,
    AIResponseMode,
    AIToolChoice,
    AIToolSpec,
    ToolRequirementMode,
)
from core.runtime.ai.providers.base import (
    ProviderUnavailableError,
    ToolDispatch,
    ToolLoopState,
    cap_tool_result,
)

logger = logging.getLogger("bot.runtime.ai.openai_provider")

# Historical hop limit, kept as documentation + the default ``AIToolBudget.max_hops``
# (they must agree). The live bound is now ``request.tool_budget.max_hops``; a request
# without a budget uses this value, so default behaviour is unchanged.
_TOOL_HOP_LIMIT = 4


class OpenAIProvider:
    """Async OpenAI chat-completions adapter with strict JSON schema.

    The adapter is constructed once per gateway. A test can inject a
    duck-typed ``client`` (e.g. a ``MagicMock`` shaped like
    ``AsyncOpenAI``) without importing the SDK.

    When the gateway supplies a ``dispatch`` callback and the request
    carries ``tools``, the adapter offers those tools to the model and
    runs a bounded tool-call loop (see :data:`_TOOL_HOP_LIMIT`). When
    ``dispatch`` is ``None`` the behaviour is identical to a plain
    single-shot completion.
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

    async def execute(
        self,
        request: AIRequest,
        *,
        model: str,
        dispatch: ToolDispatch | None = None,
    ) -> str:
        client = self._ensure_client()
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": request.system_prompt},
            {"role": "user", "content": json.dumps(request.payload, default=str)},
        ]
        response_format = _response_format(request)
        choice = request.tool_choice
        budget = request.tool_budget
        # NONE disables model-visible tools entirely (single-shot answer); otherwise the
        # historical "offer when tools present and a dispatch is wired" rule holds.
        offer_tools = (
            bool(request.tools)
            and dispatch is not None
            and choice.mode is not ToolRequirementMode.NONE
        )
        tool_params = _to_openai_tools(request.tools) if offer_tools else None
        state = ToolLoopState(budget)

        for hop in range(budget.max_hops + 1):
            allow_tools = tool_params is not None and state.may_offer_tools(hop)
            kwargs: dict[str, Any] = {"model": model, "messages": messages}
            # Honour the request's output cap (the Anthropic adapter already
            # does). ``max_tokens`` is the Chat Completions field; the
            # default model (gpt-4o-mini) and other chat models accept it.
            if request.max_output_tokens:
                kwargs["max_tokens"] = request.max_output_tokens
            if response_format is not None:
                kwargs["response_format"] = response_format
            if allow_tools:
                kwargs["tools"] = tool_params
                kwargs["tool_choice"] = _openai_tool_choice(choice, hop)

            response = await client.chat.completions.create(**kwargs)
            message = _message_of(response)
            tool_calls = getattr(message, "tool_calls", None) if message else None

            if not allow_tools or not tool_calls:
                text = _extract_response_text(response)
                if text is None:
                    raise RuntimeError(
                        "openai: empty response (no choices/message/content)",
                    )
                return text

            # The model asked for one or more tools. Echo its tool-call
            # turn, then append each tool result, then loop for the
            # follow-up completion. ``dispatch`` never raises — failures
            # come back as a JSON error string the model can react to.
            messages.append(_assistant_tool_call_turn(message, tool_calls))
            for call in tool_calls:
                state.record_call()
                result = cap_tool_result(
                    await dispatch(  # type: ignore[misc]
                        _call_name(call),
                        _call_arguments(call),
                    ),
                    budget.max_result_chars,
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": getattr(call, "id", ""),
                        "content": result,
                    },
                )

        # Unreachable: the final hop sets ``allow_tools=False`` and
        # returns above. Guard anyway so a contract change is loud.
        raise RuntimeError("openai: tool loop did not terminate")


def _response_format(request: AIRequest) -> dict[str, Any] | None:
    """Build the ``response_format`` kwarg for ``request.mode``."""
    if request.mode is not AIResponseMode.JSON:
        return None
    if request.response_schema:
        return {"type": "json_schema", "json_schema": request.response_schema}
    # JSON requested but no schema provided — fall back to the SDK's
    # loose JSON mode so callers still get parseable output.
    return {"type": "json_object"}


def _to_openai_tools(specs: tuple[AIToolSpec, ...]) -> list[dict[str, Any]]:
    """Translate provider-neutral specs into OpenAI ``tools`` entries."""
    return [
        {
            "type": "function",
            "function": {
                "name": spec.name,
                "description": spec.description,
                "parameters": spec.parameters,
            },
        }
        for spec in specs
    ]


def _openai_tool_choice(choice: AIToolChoice, hop: int) -> Any:
    """Map the neutral tool-choice policy onto OpenAI's ``tool_choice`` for this hop.

    ``AUTO`` every hop is the historical default (byte-identical output). A ``REQUIRED_*``
    policy forces a tool only on the **first** tool-offering hop — guaranteeing "at least one"
    — then relaxes to ``"auto"`` so later hops can synthesise the final answer instead of being
    forced to keep calling tools. ``REQUIRED_GROUP`` arrives already narrowed to its group by
    the resolver, so "require any of the offered" is the correct mapping.
    """
    if choice.mode is ToolRequirementMode.AUTO or hop > 0:
        return "auto"
    if choice.mode is ToolRequirementMode.REQUIRED_TOOL and choice.tool_name:
        return {"type": "function", "function": {"name": choice.tool_name}}
    return "required"


def _assistant_tool_call_turn(message: Any, tool_calls: Any) -> dict[str, Any]:
    """Reconstruct the assistant message that requested ``tool_calls``."""
    return {
        "role": "assistant",
        "content": getattr(message, "content", None),
        "tool_calls": [
            {
                "id": getattr(call, "id", ""),
                "type": "function",
                "function": {
                    "name": _call_name(call),
                    "arguments": getattr(
                        getattr(call, "function", None),
                        "arguments",
                        "",
                    )
                    or "{}",
                },
            }
            for call in tool_calls
        ],
    }


def _call_name(call: Any) -> str:
    return getattr(getattr(call, "function", None), "name", "") or ""


def _call_arguments(call: Any) -> dict[str, Any]:
    """Parse a tool call's JSON arguments into a dict (never raises)."""
    raw = getattr(getattr(call, "function", None), "arguments", "") or "{}"
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _message_of(response: Any) -> Any:
    """Return the first choice's message object, or ``None``."""
    choices = getattr(response, "choices", None)
    if not choices:
        return None
    return getattr(choices[0], "message", None)


def _extract_response_text(response: Any) -> str | None:
    """Pull the assistant message text out of a Chat Completions response."""
    message = _message_of(response)
    if message is None:
        return None
    content = getattr(message, "content", None)
    if not content:
        return None
    return content
