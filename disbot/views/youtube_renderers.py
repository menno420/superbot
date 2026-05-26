"""YouTube response renderer callables.

Registered explicitly from AICog.cog_load() — not as import side effects.
VIDEO_QA uses plain-text AI reply in M1; no renderer is registered for it.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import discord

from core.runtime.ai.response_renderer_registry import RenderedResponse

if TYPE_CHECKING:
    from core.runtime.ai.contracts import AIResponse, AITask
    from core.runtime.ai.feature_facts import FeatureFactRequest


async def render_describe(
    task: "AITask",
    response: "AIResponse",
    req: "FeatureFactRequest",
    render_context: object | None,
) -> RenderedResponse | None:
    """Renderer for VIDEO_DESCRIBE — single-video card embed."""
    from services.youtube_context_service import YouTubeContext
    from views.youtube_embeds import build_video_card_embed

    if not isinstance(render_context, YouTubeContext) or not render_context.videos:
        return None
    embed = build_video_card_embed(render_context.videos[0], response.text or "")
    return RenderedResponse(
        content=None,
        embed=embed,
        allowed_mentions=discord.AllowedMentions.none(),
    )


async def render_compare(
    task: "AITask",
    response: "AIResponse",
    req: "FeatureFactRequest",
    render_context: object | None,
) -> RenderedResponse | None:
    """Renderer for VIDEO_COMPARE — side-by-side comparison embed."""
    from services.youtube_context_service import YouTubeContext
    from views.youtube_embeds import build_compare_embed

    if not isinstance(render_context, YouTubeContext) or len(render_context.videos) < 2:
        return None
    embed = build_compare_embed(
        render_context.videos[0],
        render_context.videos[1],
        response.text or "",
    )
    return RenderedResponse(
        content=None,
        embed=embed,
        allowed_mentions=discord.AllowedMentions.none(),
    )
