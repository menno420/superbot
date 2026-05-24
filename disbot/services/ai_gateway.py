"""Service-layer shim for the AI gateway.

Cogs and services consume the AI gateway through this module — not
directly from :mod:`core.runtime.ai.gateway` — so the dependency
direction stays ``cogs → services → core/runtime``. Anything
exported here is provider-neutral and safe to import from any cog
or service.
"""

from __future__ import annotations

from core.runtime.ai.contracts import (
    AIDiagnosticsSnapshot,
    AIRequest,
    AIRequestContext,
    AIResponse,
    AIResponseMode,
    AIScope,
    AISuggestion,
    AISuggestionKind,
    AITask,
)
from core.runtime.ai.gateway import AIGateway, get_default_gateway

__all__ = [
    "AIDiagnosticsSnapshot",
    "AIGateway",
    "AIRequest",
    "AIRequestContext",
    "AIResponse",
    "AIResponseMode",
    "AIScope",
    "AISuggestion",
    "AISuggestionKind",
    "AITask",
    "execute",
    "get_default_gateway",
]


async def execute(request: AIRequest) -> AIResponse:
    """Run ``request`` through the default gateway.

    Convenience wrapper around ``get_default_gateway().execute(request)``
    for callers that do not need to construct or replace the gateway
    instance themselves.
    """
    return await get_default_gateway().execute(request)
