"""Pre-provider safety checks for AI requests.

These checks run synchronously inside the gateway before any
external call. They are deterministic and cheap; they never depend
on an LLM. A check that fires returns a textual reason; the gateway
short-circuits with a degraded :class:`AIResponse` and never sends
the request.

Checks (composable, ordered):

1. Empty / whitespace-only ``system_prompt`` — guards against
   misconfigured callers that build prompts dynamically.
2. Empty ``payload`` — same.
3. Payload size cap — JSON-serialised size in bytes must stay below
   :data:`MAX_PAYLOAD_BYTES`. Protects against accidental large
   dumps (e.g. an entire guild snapshot pasted in).

Future hooks: more sophisticated prompt-injection heuristics. The
plan defers those until a real abuse signal exists; deterministic
size/empty checks are the conservative baseline.
"""

from __future__ import annotations

import json

from core.runtime.ai.contracts import AIRequest

# Conservative ceiling for the serialised payload size in bytes.
# Setup advisor snapshots run well under 100 KiB; this rejects
# obvious mistakes without blocking legitimate use.
MAX_PAYLOAD_BYTES = 256 * 1024


def precheck(request: AIRequest) -> str | None:
    """Run safety checks; return the first failure reason or ``None``."""
    if not request.system_prompt or not request.system_prompt.strip():
        return "safety: empty system_prompt"
    if not request.payload:
        return "safety: empty payload"
    try:
        size = len(json.dumps(request.payload, default=str).encode("utf-8"))
    except (TypeError, ValueError):
        return "safety: payload is not JSON-serialisable"
    if size > MAX_PAYLOAD_BYTES:
        return f"safety: payload {size}B exceeds {MAX_PAYLOAD_BYTES}B cap"
    return None
