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

from typing import Protocol, runtime_checkable

from core.runtime.ai.contracts import AIRequest


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

    async def execute(self, request: AIRequest, *, model: str) -> str:
        """Run the provider call and return the raw text response.

        Args:
            request: The typed :class:`AIRequest` (already redacted by
                the gateway before this is called).
            model: The provider-specific model identifier resolved by
                :mod:`core.runtime.ai.routing`.

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
