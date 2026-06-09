"""Anthropic (Claude) provider adapter.

The Claude twin of :mod:`core.runtime.ai.providers.openai_provider`. Like
that module, this is one of the only two production modules permitted to
import a provider SDK directly — the invariant test
``tests/unit/invariants/test_ai_btd6_boundaries.py::test_provider_sdk_imports_only_in_providers``
fails if any other production module imports ``anthropic``. All consumers
route through :class:`core.runtime.ai.gateway.AIGateway`.

Maps the provider-neutral :class:`AIRequest` onto the Anthropic Messages
API:

* ``system_prompt`` → a ``system`` block carrying ``cache_control`` so the
  stable prefix is prompt-cached (cheap/fast on repeat calls).
* ``payload`` → a single JSON user message (mirrors the OpenAI adapter).
* ``tools`` + ``dispatch`` → a bounded ``tool_use`` / ``tool_result`` loop,
  the same read-only tool contract the OpenAI adapter implements.
* ``AIResponseMode.JSON`` + ``response_schema`` → ``output_config.format``
  (structured outputs). The gateway parses the returned JSON.

Thinking / effort are intentionally not set: the adapter must work across
model tiers (Haiku, Sonnet, Opus) without 400s, and the gateway's callers
are short bot replies. Per-model thinking can be layered on later.
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

logger = logging.getLogger("bot.runtime.ai.anthropic_provider")

# Historical hop limit, kept as documentation + the default ``AIToolBudget.max_hops``
# (mirrors the OpenAI adapter). The live bound is now ``request.tool_budget.max_hops``.
_TOOL_HOP_LIMIT = 4

# Anthropic's Messages API requires ``max_tokens``. Fall back to this when
# the request does not set one.
_DEFAULT_MAX_TOKENS = 1024


class AnthropicProvider:
    """Async Anthropic Messages-API adapter with tool use + prompt caching.

    The adapter is constructed once per gateway. A test can inject a
    duck-typed ``client`` (shaped like ``AsyncAnthropic``) so the SDK is
    never imported during tests.

    When the gateway supplies a ``dispatch`` callback and the request
    carries ``tools``, the adapter offers those tools to the model and runs
    a bounded tool-use loop. When ``dispatch`` is ``None`` the behaviour is
    a plain single-shot completion.
    """

    name = "anthropic"

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
            from anthropic import AsyncAnthropic
        except ImportError as exc:
            raise ProviderUnavailableError(
                "anthropic package is not installed; install "
                "``anthropic>=0.40,<1.0`` or set the AI provider to "
                "``openai`` / ``deterministic``.",
            ) from exc
        api_key = self._api_key or os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise ProviderUnavailableError(
                "ANTHROPIC_API_KEY is not set; cannot construct Anthropic client.",
            )
        self._client = AsyncAnthropic(api_key=api_key)
        return self._client

    async def execute(
        self,
        request: AIRequest,
        *,
        model: str,
        dispatch: ToolDispatch | None = None,
    ) -> str:
        client = self._ensure_client()
        system = _system_blocks(request.system_prompt)
        messages: list[dict[str, Any]] = [
            {"role": "user", "content": json.dumps(request.payload, default=str)},
        ]
        output_config = _output_config(request)
        choice = request.tool_choice
        budget = request.tool_budget
        # NONE disables model-visible tools entirely (single-shot answer).
        offer_tools = (
            bool(request.tools)
            and dispatch is not None
            and choice.mode is not ToolRequirementMode.NONE
        )
        tool_params = _to_anthropic_tools(request.tools) if offer_tools else None
        max_tokens = request.max_output_tokens or _DEFAULT_MAX_TOKENS
        state = ToolLoopState(budget)

        for hop in range(budget.max_hops + 1):
            allow_tools = tool_params is not None and state.may_offer_tools(hop)
            kwargs: dict[str, Any] = {
                "model": model,
                "max_tokens": max_tokens,
                "system": system,
                "messages": messages,
            }
            if output_config is not None:
                kwargs["output_config"] = output_config
            if allow_tools:
                kwargs["tools"] = tool_params
                kwargs["tool_choice"] = _anthropic_tool_choice(choice, hop)

            response = await client.messages.create(**kwargs)
            blocks = _blocks_of(response)
            tool_uses = _tool_uses(blocks) if allow_tools else []

            if not tool_uses:
                text = _extract_text(blocks)
                if text is None:
                    raise RuntimeError("anthropic: empty response (no text content)")
                return text

            # The model asked for one or more tools. Echo its turn (the full
            # content blocks), then append each tool result, then loop.
            # ``dispatch`` never raises — failures come back as a JSON error
            # string the model can react to.
            messages.append(
                {"role": "assistant", "content": getattr(response, "content", blocks)},
            )
            tool_results: list[dict[str, Any]] = []
            for tool_use in tool_uses:
                raw_input = getattr(tool_use, "input", None)
                arguments = raw_input if isinstance(raw_input, dict) else {}
                state.record_call()
                result = cap_tool_result(
                    await dispatch(  # type: ignore[misc]
                        getattr(tool_use, "name", "") or "",
                        arguments,
                    ),
                    budget.max_result_chars,
                )
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": getattr(tool_use, "id", ""),
                        "content": result,
                    },
                )
            messages.append({"role": "user", "content": tool_results})

        # Unreachable: the final hop sets ``allow_tools=False`` and returns
        # above. Guard anyway so a contract change is loud.
        raise RuntimeError("anthropic: tool loop did not terminate")


def _system_blocks(system_prompt: str) -> list[dict[str, Any]]:
    """Wrap the system prompt as a cache-marked text block.

    ``cache_control`` makes the stable system prefix prompt-cacheable; it is
    a no-op (no error) when the prefix is shorter than the model's minimum
    cacheable length.
    """
    return [
        {
            "type": "text",
            "text": system_prompt,
            "cache_control": {"type": "ephemeral"},
        },
    ]


def _to_anthropic_tools(specs: tuple[AIToolSpec, ...]) -> list[dict[str, Any]]:
    """Translate provider-neutral specs into Anthropic ``tools`` entries.

    Note the Anthropic shape: a flat ``{name, description, input_schema}``
    (no OpenAI-style ``function`` wrapper, and ``input_schema`` rather than
    ``parameters``).
    """
    return [
        {
            "name": spec.name,
            "description": spec.description,
            "input_schema": spec.parameters,
        }
        for spec in specs
    ]


def _anthropic_tool_choice(choice: AIToolChoice, hop: int) -> dict[str, Any]:
    """Map the neutral tool-choice policy onto Anthropic's ``tool_choice`` for this hop.

    ``{"type": "auto"}`` every hop is the historical default. A ``REQUIRED_*`` policy forces a
    tool only on the **first** tool-offering hop, then relaxes to ``auto`` so a later hop can
    produce the final answer. ``REQUIRED_ANY`` / ``REQUIRED_GROUP`` → ``{"type": "any"}`` (the
    group is already narrowed by the resolver); ``REQUIRED_TOOL`` → ``{"type": "tool", ...}``.
    """
    if choice.mode is ToolRequirementMode.AUTO or hop > 0:
        return {"type": "auto"}
    if choice.mode is ToolRequirementMode.REQUIRED_TOOL and choice.tool_name:
        return {"type": "tool", "name": choice.tool_name}
    return {"type": "any"}


def _output_config(request: AIRequest) -> dict[str, Any] | None:
    """Build ``output_config`` for ``AIResponseMode.JSON`` with a schema."""
    if request.mode is not AIResponseMode.JSON or not request.response_schema:
        return None
    schema = request.response_schema
    # The neutral contract carries the OpenAI ``json_schema`` wrapper
    # (``{name, schema, strict}``); Anthropic wants the bare JSON Schema.
    if isinstance(schema, dict) and "schema" in schema:
        schema = schema["schema"]
    return {"format": {"type": "json_schema", "schema": schema}}


def _blocks_of(response: Any) -> list[Any]:
    """Return the response content blocks as a list (never ``None``)."""
    content = getattr(response, "content", None)
    return list(content) if content else []


def _tool_uses(blocks: list[Any]) -> list[Any]:
    return [b for b in blocks if getattr(b, "type", None) == "tool_use"]


def _extract_text(blocks: list[Any]) -> str | None:
    """Concatenate the text blocks of a Messages response."""
    parts = [
        getattr(b, "text", "") for b in blocks if getattr(b, "type", None) == "text"
    ]
    text = "".join(part for part in parts if part)
    return text or None
