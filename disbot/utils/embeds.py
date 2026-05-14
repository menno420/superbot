from __future__ import annotations

import discord


def success(title: str, description: str = "", **fields: str) -> discord.Embed:
    """Green success embed with optional extra fields."""
    embed = discord.Embed(
        title=title, description=description, color=discord.Color.green()
    )
    for name, value in fields.items():
        embed.add_field(name=name.replace("_", " ").title(), value=value, inline=True)
    return embed


def error(message: str) -> discord.Embed:
    """Red error embed for user-facing error messages."""
    return discord.Embed(description=f"❌ {message}", color=discord.Color.red())


def info(title: str, description: str = "", **fields: str) -> discord.Embed:
    """Blue informational embed with optional extra fields."""
    embed = discord.Embed(
        title=title, description=description, color=discord.Color.blue()
    )
    for name, value in fields.items():
        embed.add_field(name=name.replace("_", " ").title(), value=value, inline=True)
    return embed


def warning(message: str) -> discord.Embed:
    """Yellow warning embed."""
    return discord.Embed(description=f"⚠️ {message}", color=discord.Color.yellow())
