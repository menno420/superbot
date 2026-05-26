"""Discord embed builders for YouTube video responses."""
from __future__ import annotations

from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from services.youtube_context_service import VideoContext


def _fmt_duration(seconds: int) -> str:
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def build_video_card_embed(ctx: "VideoContext", ai_summary: str) -> discord.Embed:
    """Single-video describe embed with metadata and AI-generated summary."""
    meta = ctx.metadata
    title = (meta.title or ctx.reference.video_id)[:256]
    embed = discord.Embed(
        title=title,
        url=ctx.reference.canonical_url,
        description=(ai_summary or "")[:4096] or None,
        color=discord.Color.red(),
    )
    if meta.channel_name:
        embed.set_author(name=meta.channel_name[:256])
    if meta.thumbnail_url:
        embed.set_thumbnail(url=meta.thumbnail_url)
    if meta.duration_seconds is not None:
        embed.add_field(
            name="Duration",
            value=_fmt_duration(meta.duration_seconds),
            inline=True,
        )
    if meta.published_at:
        embed.add_field(
            name="Published",
            value=meta.published_at.strftime("%Y-%m-%d"),
            inline=True,
        )
    transcript_note = "Transcript available" if ctx.transcript.available else "No transcript"
    embed.set_footer(text=transcript_note)
    return embed


def build_compare_embed(
    a: "VideoContext",
    b: "VideoContext",
    ai_text: str,
) -> discord.Embed:
    """Side-by-side comparison embed for two YouTube videos."""
    embed = discord.Embed(
        title="Video Comparison",
        description=(ai_text or "")[:4096] or None,
        color=discord.Color.blurple(),
    )
    for label, ctx in (("Video A", a), ("Video B", b)):
        meta = ctx.metadata
        name = (meta.title or ctx.reference.video_id)[:100]
        lines = [f"[{name}]({ctx.reference.canonical_url})"]
        if meta.channel_name:
            lines.append(f"by {meta.channel_name[:80]}")
        if meta.duration_seconds is not None:
            lines.append(_fmt_duration(meta.duration_seconds))
        embed.add_field(name=label, value="\n".join(lines), inline=True)
    return embed
