from __future__ import annotations

import discord


def error(message: str) -> discord.Embed:
    """Red error embed for user-facing error messages."""
    return discord.Embed(description=f"❌ {message}", color=discord.Color.red())
