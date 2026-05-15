"""Persistent panel lifecycle management.

A panel is a Discord message with an interactive view that is anchored to a
specific (user, channel, subsystem) triple in the database.  The runtime
platform enforces one panel per triple at a time:

  - If an anchor exists and the message is still accessible: edit in-place.
  - If the anchor's message was deleted: create a new message, overwrite anchor.
  - If no anchor exists: send new message, store anchor.

This eliminates the "stale message pile-up" problem where every command run
sends a new message that orphans previous panels.

Public surface:
    get_or_render_panel(ctx, subsystem, embed, view) → discord.Message
"""

from __future__ import annotations

import logging

import discord
from core.runtime import message_anchor_manager
from discord.ext import commands

logger = logging.getLogger("bot.runtime.panels")


async def get_or_render_panel(
    ctx: commands.Context,
    subsystem: str,
    embed: discord.Embed,
    view: discord.ui.View,
) -> discord.Message:
    """Send or update the persistent panel for this user in this channel.

    Returns the Discord Message that contains the panel (either the existing
    anchored message after editing, or the newly sent one).
    """
    user_id = ctx.author.id
    guild_id = ctx.guild.id
    channel_id = ctx.channel.id

    anchor = await message_anchor_manager.get(user_id, channel_id, subsystem)

    if anchor and not anchor["is_stale"]:
        try:
            msg = await ctx.channel.fetch_message(anchor["message_id"])
            await msg.edit(embed=embed, view=view)
            logger.debug(
                "Panel updated in-place | subsystem=%s | user=%d | msg=%d",
                subsystem,
                user_id,
                msg.id,
            )
            return msg
        except discord.NotFound:
            logger.debug(
                "Panel anchor stale (msg deleted) | subsystem=%s | user=%d",
                subsystem,
                user_id,
            )
            await message_anchor_manager.mark_stale(str(anchor["anchor_id"]))
        except (discord.Forbidden, discord.HTTPException) as exc:
            logger.warning(
                "Cannot edit panel message | subsystem=%s | user=%d: %s",
                subsystem,
                user_id,
                exc,
            )
            await message_anchor_manager.mark_stale(str(anchor["anchor_id"]))

    msg = await ctx.send(embed=embed, view=view)
    await message_anchor_manager.upsert(
        user_id, guild_id, channel_id, subsystem, msg.id
    )
    logger.debug(
        "New panel anchored | subsystem=%s | user=%d | msg=%d",
        subsystem,
        user_id,
        msg.id,
    )
    return msg
