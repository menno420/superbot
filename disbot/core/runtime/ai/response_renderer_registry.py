"""Renderer registry for AI responses.

Lives in the AI runtime layer so renderer dispatch is owned by the AI
platform, not by individual feature cogs.  Renderers produce richer
Discord payloads (embeds) for tasks that benefit from them; tasks
without a registered renderer fall through to plain-text send.

Registration is idempotent: re-registering the same task silently
replaces the renderer, making repeated AICog.cog_load() safe.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Awaitable, Callable

import discord

if TYPE_CHECKING:
    from core.runtime.ai.contracts import AIResponse, AITask
    from core.runtime.ai.feature_facts import FeatureFactRequest

# Python 3.10-compatible alias — do not use Python 3.12 `type X = ...` syntax
RendererFn = Callable[
    ["AITask", "AIResponse", "FeatureFactRequest", "object | None"],
    Awaitable["RenderedResponse | None"],
]


@dataclass
class RenderedResponse:
    content: str | None
    embed: discord.Embed | None
    allowed_mentions: discord.AllowedMentions | None


_RENDERERS: dict["AITask", RendererFn] = {}


def register(task: "AITask", fn: RendererFn) -> None:
    """Register a renderer for a task.  Idempotent — safe to call multiple times."""
    _RENDERERS[task] = fn


async def render(
    task: "AITask",
    response: "AIResponse",
    req: "FeatureFactRequest",
    render_context: object | None,
) -> RenderedResponse | None:
    """Dispatch to the registered renderer, or return None for plain-text path."""
    fn = _RENDERERS.get(task)
    if fn is None:
        return None
    return await fn(task, response, req, render_context)


def _reset_for_tests() -> None:
    _RENDERERS.clear()


__all__ = ["RenderedResponse", "RendererFn", "register", "render"]
