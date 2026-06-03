"""Registered renderer for BTD6 answers — emits a verified-data embed.

Runs in the natural-language stage **after** the faithfulness verifier, so the
reply it formats is already grounded; the renderer never bypasses verification.
Falls through to plain text (returns ``None``) when there is no deterministic
data to anchor — e.g. a conversational BTD6 reply that resolved no entity.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from core.runtime.ai.redaction import redact_text
from core.runtime.ai.response_renderer_registry import RenderedResponse
from utils.btd6.answer_embed import BTD6RenderContext, build_answer_embed

if TYPE_CHECKING:
    from core.runtime.ai.contracts import AIResponse, AITask
    from core.runtime.ai.feature_facts import FeatureFactRequest


async def render_btd6_answer(
    _task: AITask,
    response: AIResponse,
    _req: FeatureFactRequest,
    render_context: object | None,
) -> RenderedResponse | None:
    if not isinstance(render_context, BTD6RenderContext):
        return None
    # The registry hands us the raw response, while the plain-text path sends a
    # redacted reply — re-redact here so the embed never leaks a snowflake the
    # plain path would have scrubbed. (Idempotent on already-clean text.)
    text = redact_text(response.text or "").value
    embed = build_answer_embed(text, render_context)
    if embed is None:
        return None
    return RenderedResponse(content=None, embed=embed, allowed_mentions=None)


__all__ = ["render_btd6_answer"]
