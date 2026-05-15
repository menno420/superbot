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


def server_info_embed(guild: discord.Guild) -> discord.Embed:
    """Standard server info embed used across admin and utility cogs."""
    embed = discord.Embed(
        title=guild.name,
        color=discord.Color.blurple(),
    )
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.add_field(name="Owner", value=str(guild.owner), inline=True)
    embed.add_field(name="Members", value=str(guild.member_count), inline=True)
    embed.add_field(name="Channels", value=str(len(guild.channels)), inline=True)
    embed.add_field(name="Roles", value=str(len(guild.roles)), inline=True)
    embed.add_field(name="Region", value=str(guild.preferred_locale), inline=True)
    embed.add_field(
        name="Created",
        value=discord.utils.format_dt(guild.created_at, style="D"),
        inline=True,
    )
    return embed


def user_info_embed(member: discord.Member) -> discord.Embed:
    """Standard user info embed used across admin and utility cogs."""
    embed = discord.Embed(
        title=member.display_name,
        color=member.color if member.color != discord.Color.default() else discord.Color.blurple(),
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Username", value=str(member), inline=True)
    embed.add_field(name="ID", value=str(member.id), inline=True)
    embed.add_field(name="Bot", value="Yes" if member.bot else "No", inline=True)
    if member.joined_at:
        embed.add_field(
            name="Joined",
            value=discord.utils.format_dt(member.joined_at, style="D"),
            inline=True,
        )
    embed.add_field(
        name="Account Created",
        value=discord.utils.format_dt(member.created_at, style="D"),
        inline=True,
    )
    top_roles = [r.mention for r in reversed(member.roles) if r.name != "@everyone"][:5]
    if top_roles:
        embed.add_field(name="Top Roles", value=" ".join(top_roles), inline=False)
    return embed
