"""Auto-managed private setup channel.

When SuperBot joins a guild and has Manage Channels permission, it
creates a private ``#superbot-setup`` channel visible only to the bot
itself and the guild owner. The launcher cog posts the setup launcher
in that channel and @mentions the owner so they discover the wizard
immediately.

This module owns the idempotent "ensure" operation. The actual Discord
channel creation routes through
:func:`core.runtime.guild_resources.ensure_channel` — the canonical
infrastructure primitive on the S4.5 no-silent-auto-create allowlist.

Constraints preserved:

* No ``guild.create_text_channel`` call here — that lives in
  ``guild_resources.ensure_channel``.
* No DB writes here. The caller updates ``setup_session`` with the
  new channel id via the standard ``start_session`` upsert.
* No required permissions raise; missing perms / HTTP failures
  surface as ``(None, False)`` and the caller falls back to
  ``post_launcher`` (which already DMs the owner if no channel is
  sendable).

The channel name is namespaced so it does not collide with
operator-named "setup" channels.
"""

from __future__ import annotations

import logging

import discord

from core.runtime.guild_resources import ensure_channel

logger = logging.getLogger("bot.services.setup_channel")

#: Channel name for the bot-managed setup workspace. Namespaced so
#: operator-created "setup" channels are not accidentally adopted.
SETUP_CHANNEL_NAME = "superbot-setup"


def _private_overwrites(
    guild: discord.Guild,
) -> dict[discord.Member | discord.Role, discord.PermissionOverwrite]:
    """Build the permission overwrite set for the private setup channel.

    Visible to the bot and the guild owner; hidden from @everyone.
    Administrator-tier members keep their global view permission via
    Discord's own permission resolver — we only restrict ``@everyone``.
    """
    overwrites: dict[discord.Member | discord.Role, discord.PermissionOverwrite] = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
    }
    if guild.me is not None:
        overwrites[guild.me] = discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            embed_links=True,
            read_message_history=True,
            manage_messages=True,
        )
    if guild.owner is not None:
        overwrites[guild.owner] = discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
        )
    return overwrites


def _bot_can_manage_channels(guild: discord.Guild) -> bool:
    """True iff the bot member holds Manage Channels in this guild."""
    me = guild.me
    if me is None:
        return False
    return bool(getattr(me.guild_permissions, "manage_channels", False))


async def ensure_setup_channel(
    guild: discord.Guild,
    *,
    existing_channel_id: int | None = None,
) -> tuple[discord.TextChannel | None, bool]:
    """Return the private setup channel for ``guild``, creating if absent.

    Idempotent. The function tries the following, in order:

    1. If ``existing_channel_id`` is given and the channel is still in
       the guild cache, return it unchanged.
    2. Look up by canonical name (``superbot-setup``) — covers the
       restart case where the cog lost track of the channel id.
    3. Create the channel with private overwrites via
       :func:`core.runtime.guild_resources.ensure_channel`. Requires
       the bot to hold Manage Channels.

    Returns:
        ``(channel, was_just_created)`` where ``channel`` is ``None``
        when the bot lacks permission or Discord refused the create.
        Callers should fall back to the existing ``post_launcher``
        path in that case so setup still gets a launcher somewhere.
    """
    if existing_channel_id is not None:
        existing = guild.get_channel(existing_channel_id)
        if isinstance(existing, discord.TextChannel):
            return existing, False

    if not _bot_can_manage_channels(guild):
        logger.info(
            "setup_channel: bot lacks Manage Channels in guild %d; falling back",
            guild.id,
        )
        return None, False

    try:
        channel = await ensure_channel(
            guild,
            SETUP_CHANNEL_NAME,
            kind="text",
            category=None,
            overwrites=_private_overwrites(guild),
        )
    except discord.Forbidden as exc:
        logger.warning(
            "setup_channel: forbidden creating #%s in guild %d: %s",
            SETUP_CHANNEL_NAME,
            guild.id,
            exc,
        )
        return None, False
    except discord.HTTPException as exc:
        logger.warning(
            "setup_channel: HTTP error creating #%s in guild %d: %s",
            SETUP_CHANNEL_NAME,
            guild.id,
            exc,
        )
        return None, False

    if not isinstance(channel, discord.TextChannel):
        logger.warning(
            "setup_channel: guild_resources returned non-text channel for guild %d",
            guild.id,
        )
        return None, False

    return channel, True


__all__ = [
    "SETUP_CHANNEL_NAME",
    "ensure_setup_channel",
]
