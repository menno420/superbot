"""Convert a BTD6 response object into a Discord embed.

Lives in ``utils/`` so both ``cogs/btd6/`` (the existing tower / hero /
round prefix+slash commands) and ``views/btd6/`` (the PR 2 drill-down
detail views) can render the same response shape without crossing
layer boundaries.

The input ``response`` is duck-typed: any object with the
:class:`services.btd6_response_builder.BTD6Response` attributes works.
Typing it as ``Any`` preserves the utils → services boundary.
"""

from __future__ import annotations

from typing import Any

import discord


def response_to_embed(response: Any) -> discord.Embed:
    """Convert a :class:`BTD6Response` into a Discord embed."""
    color = {
        "high": discord.Color.green(),
        "medium": discord.Color.gold(),
        "low": discord.Color.light_grey(),
    }.get(response.confidence, discord.Color.light_grey())
    embed = discord.Embed(
        title=response.title,
        description=response.short_answer,
        color=color,
    )
    if response.why_it_matters:
        embed.add_field(
            name="Why it matters",
            value=response.why_it_matters,
            inline=False,
        )
    for name, value in getattr(response, "fields", ()) or ():
        if value:
            embed.add_field(name=name, value=value[:1024], inline=False)
    if response.recommended_options:
        embed.add_field(
            name="Recommended options",
            value="\n".join(f"• {opt}" for opt in response.recommended_options),
            inline=False,
        )
    if response.common_mistakes:
        embed.add_field(
            name="Common mistakes",
            value="\n".join(f"• {m}" for m in response.common_mistakes),
            inline=False,
        )
    if response.version_sensitivity:
        embed.add_field(
            name="Version sensitivity",
            value=response.version_sensitivity,
            inline=False,
        )
    live_facts = getattr(response, "live_facts", ()) or ()
    if live_facts:
        value = "\n".join(f"• {fact}" for fact in live_facts)
        if len(value) > 1024:
            kept: list[str] = []
            running = 0
            for fact in live_facts:
                line = f"• {fact}"
                if running + len(line) + 1 > 990:
                    break
                kept.append(line)
                running += len(line) + 1
            dropped = len(live_facts) - len(kept)
            value = "\n".join(kept) + f"\n… ({dropped} more)"
        embed.add_field(name="Live data", value=value, inline=False)
    if response.follow_up:
        embed.add_field(name="Follow-up", value=response.follow_up, inline=False)
    if response.sources:
        embed.set_footer(text="Sources: " + " · ".join(response.sources))
    return embed


__all__ = ["response_to_embed"]
