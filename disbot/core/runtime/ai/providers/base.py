"""Provider protocol for the AI gateway.

A provider implements one method, ``execute``, that converts a typed
:class:`AIRequest` into raw response text (JSON or plain text,
depending on ``AIRequest.mode``). The gateway handles redaction,
routing, timeout, parsing, metrics, and degradation around this
method.

Providers may raise:

* :class:`ProviderUnavailableError` — the provider cannot run (missing
  SDK, missing API key, configuration error). The gateway converts
  this into a degraded :class:`AIResponse` with a descriptive
  ``fallback_reason``.
* Any other exception — the gateway logs it, increments the failure
  counter, and converts it into a degraded response. Provider
  implementations should not swallow exceptions silently; the
  gateway is the single fault boundary.
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from core.runtime.ai.contracts import AIRequest, AIToolBudget

#: A read-only tool handler: receives parsed arguments and returns a
#: JSON-serialisable result (or a string). Handlers live in the
#: services layer; the alias is declared here so the gateway and
#: providers can reference the type without importing ``services``.
ToolHandler = Callable[[dict[str, Any]], Awaitable[Any]]

#: Gateway-provided callback a provider invokes during a tool loop.
#: Given a tool name and parsed arguments, it returns the (already
#: redacted) tool result as a string to feed back into the model
#: context. It never raises — tool failures come back as a JSON error
#: string so the loop can continue and the model can react.
ToolDispatch = Callable[[str, dict[str, Any]], Awaitable[str]]


def cap_tool_result(result: str, max_chars: int | None) -> str:
    """Bound a tool-result string to the request budget (no-op when ``max_chars`` is None).

    Keeps an over-large result from blowing the context/token budget on the follow-up hop.
    ``None`` (the default budget) returns the result unchanged — the historical behaviour.
    """
    if max_chars is None or len(result) <= max_chars:
        return result
    return result[:max_chars] + " …[tool result truncated]"


@dataclass
class ToolLoopState:
    """Per-request accounting that bounds a provider's model<->tool loop by its budget.

    Shared by both adapters so the rule is enforced (and tested) once. The default budget
    (``max_calls``/``max_wall_seconds`` = ``None``) reproduces the historical hop-only bound:
    :meth:`may_offer_tools` then returns True for every hop below ``max_hops`` exactly as the
    old ``hop < _TOOL_HOP_LIMIT`` check did. Tighter caps stop the loop offering further tools
    — the next hop produces the final tool-free answer.
    """

    budget: AIToolBudget
    calls_made: int = 0
    started_monotonic: float = field(default_factory=time.monotonic)

    def may_offer_tools(self, hop: int) -> bool:
        """True if this hop may still offer tools, given hop / call / wall-time caps."""
        budget = self.budget
        if hop >= budget.max_hops:
            return False
        if budget.max_calls is not None and self.calls_made >= budget.max_calls:
            return False
        if budget.max_wall_seconds is not None:
            elapsed = time.monotonic() - self.started_monotonic
            if elapsed >= budget.max_wall_seconds:
                return False
        return True

    def record_call(self) -> None:
        """Count one dispatched tool call against the budget."""
        self.calls_made += 1


class ProviderUnavailableError(RuntimeError):
    """Raised when a provider cannot execute the request.

    Typical causes: missing SDK package, missing API key,
    configuration mismatch. The gateway converts this into a
    degraded :class:`AIResponse` rather than propagating it.
    """


@runtime_checkable
class Provider(Protocol):
    """Provider adapter contract.

    Implementations live under ``core/runtime/ai/providers/`` and are
    the only modules permitted to import external LLM SDKs.
    """

    name: str

    async def execute(
        self,
        request: AIRequest,
        *,
        model: str,
        dispatch: ToolDispatch | None = None,
    ) -> str:
        """Run the provider call and return the raw text response.

        Args:
            request: The typed :class:`AIRequest` (already redacted by
                the gateway before this is called).
            model: The provider-specific model identifier resolved by
                :mod:`core.runtime.ai.routing`.
            dispatch: Optional tool-dispatch callback. When provided
                *and* ``request.tools`` is non-empty, the provider may
                offer those tools to the model and run a bounded
                tool-call loop, invoking ``dispatch`` for each call.
                When ``None`` (the default), the provider behaves
                exactly as the no-tools path. Providers that do not
                support tools ignore this argument.

        Returns:
            The raw assistant text. For ``AIResponseMode.JSON`` the
            text is expected to be a JSON document; the gateway
            parses it. For ``AIResponseMode.TEXT`` the text is
            returned as-is on the :attr:`AIResponse.text` field.

        Raises:
            ProviderUnavailableError: if the provider cannot serve this
                request (no API key, missing SDK).
            Exception: any other failure is caught by the gateway.
        """
        ...
