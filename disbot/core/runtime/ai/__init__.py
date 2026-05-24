"""AI runtime — the provider-neutral platform layer.

This package owns the AI gateway and its contract types. Cogs and
services consume AI through ``services.ai_gateway`` (a service-layer
shim) rather than importing this package directly, keeping the
dependency direction cogs → services → core/runtime.

Public API:
    AIGateway, get_default_gateway, reset_default_gateway
    AIRequest, AIResponse, AIRequestContext, AISuggestion,
    AIDiagnosticsSnapshot, AITask, AIScope, AIResponseMode,
    AISuggestionKind
    redact_text, redact_payload
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
from core.runtime.ai.gateway import (
    AIGateway,
    get_default_gateway,
    reset_default_gateway,
)
from core.runtime.ai.redaction import redact_text

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
    "get_default_gateway",
    "redact_text",
    "reset_default_gateway",
]
