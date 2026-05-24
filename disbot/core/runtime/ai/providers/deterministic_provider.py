"""Deterministic fallback provider.

The deterministic provider never makes an external call. It always
raises :class:`DeterministicFallbackError`, which the gateway converts
into a degraded :class:`AIResponse` with ``fallback_reason``
``provider=deterministic``. Consumers that want a deterministic
baseline (e.g. the setup advisor) check for ``degraded`` and apply
their own local logic.

This provider is the default in CI/dev environments where no LLM
API key is configured. Its existence keeps the gateway boot-safe:
``get_default_gateway()`` always returns a usable instance.
"""

from __future__ import annotations

from core.runtime.ai.contracts import AIRequest


class DeterministicFallbackError(RuntimeError):
    """Signal that no LLM provider is willing or able to serve this request."""


class DeterministicProvider:
    """Always-available no-op provider.

    ``execute`` raises :class:`DeterministicFallbackError`. The gateway
    catches it and returns a degraded :class:`AIResponse` so callers
    have a uniform "degrade gracefully" code path.
    """

    name = "deterministic"

    async def execute(self, request: AIRequest, *, model: str) -> str:
        raise DeterministicFallbackError(
            "deterministic provider selected; no external call performed",
        )
