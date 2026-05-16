from __future__ import annotations

import asyncio

import discord


async def safe_channel_name(guild: discord.Guild, base: str) -> str:
    """Return `base` with an auto-incremented suffix if that name already exists."""
    existing = {ch.name for ch in guild.channels}
    if base not in existing:
        return base
    i = 2
    while f"{base}-{i}" in existing:
        i += 1
    return f"{base}-{i}"


async def get_or_create_category(
    guild: discord.Guild,
    name: str,
    overwrites: dict | None = None,
) -> discord.CategoryChannel:
    """Return an existing category by name, or create one."""
    cat = discord.utils.get(guild.categories, name=name)
    if cat:
        return cat
    return await guild.create_category(name, overwrites=overwrites or {})


async def create_private_channel(
    guild: discord.Guild,
    name: str,
    members: list[discord.Member],
    category_name: str,
    *,
    auto_increment: bool = True,
) -> discord.TextChannel:
    """Create a private text channel visible only to `members` and the bot.

    The category is created if it doesn't exist yet.
    If `auto_increment` is True, a numeric suffix is appended when the
    channel name is already taken (e.g. match-1 → match-2).
    """
    if auto_increment:
        name = await safe_channel_name(guild, name)

    cat_overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
    }
    cat = await get_or_create_category(guild, category_name, overwrites=cat_overwrites)

    overwrites: dict = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
    }
    for m in members:
        overwrites[m] = discord.PermissionOverwrite(
            read_messages=True,
            send_messages=True,
        )

    return await guild.create_text_channel(name, overwrites=overwrites, category=cat)


async def cleanup_category(
    category: discord.CategoryChannel,
    delay: float = 0.0,
) -> None:
    """Delete every channel in *category*, then delete the category itself."""
    if delay:
        await asyncio.sleep(delay)
    for ch in list(category.channels):
        try:
            await ch.delete()
        except Exception:
            pass
    try:
        await category.delete()
    except Exception:
        pass
