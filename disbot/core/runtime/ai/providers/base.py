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

from collections.abc import Awaitable, Callable
from typing import Any, Protocol, runtime_checkable

from core.runtime.ai.contracts import AIRequest

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
