"""Discord message anchor persistence.

An anchor is a (channel_id, message_id) pair stored in the DB that lets the
runtime platform find and edit an existing panel message instead of sending a
new one on every command invocation.

The anchor table enforces one row per (user, channel, subsystem) via a UNIQUE
constraint.  Stale anchors (message deleted) are marked and pruned by GC.

Public surface:
    get(user_id, channel_id, subsystem)           → dict | None
    upsert(user_id, guild_id, channel_id, subsystem, message_id) → dict
    get_by_message_id(message_id)                  → dict | None
    mark_stale(anchor_id)                          → None
    restore_anchors(bot)                           → None  (startup recovery)
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands
from utils import db

logger = logging.getLogger("bot.runtime.anchors")


async def get(user_id: int, channel_id: int, subsystem: str) -> dict | None:
    """Return the active anchor for (user, channel, subsystem), or None."""
    return await db.get_panel_anchor(user_id, channel_id, subsystem)


async def upsert(
    user_id: int,
    guild_id: int,
    channel_id: int,
    subsystem: str,
    message_id: int,
) -> dict:
    """Create or replace the anchor, resetting is_stale on conflict."""
    row = await db.upsert_panel_anchor(
        user_id, guild_id, channel_id, subsystem, message_id
    )
    logger.debug(
        "Anchor upserted | subsystem=%s | user=%d | msg=%d",
        subsystem,
        user_id,
        message_id,
    )
    return row


async def get_by_message_id(message_id: int) -> dict | None:
    """Return the anchor for a specific Discord message, or None."""
    return await db.get_panel_anchor_by_message(message_id)


async def mark_stale(anchor_id: str) -> None:
    """Mark an anchor as stale after detecting the Discord message was deleted."""
    await db.mark_panel_anchor_stale(anchor_id)
    logger.debug("Anchor marked stale: %s", anchor_id)


async def restore_anchors(bot: commands.Bot) -> None:
    """Re-attach persistent views to all anchored messages at bot startup.

    Fetches every non-stale anchor from DB and calls bot.add_view() with a
    fresh view instance so button interactions survive a bot restart.
    Messages that no longer exist are marked stale.
    """
    from core.runtime.persistent_views import get_view_class

    anchors = await db.get_all_active_panel_anchors()
    restored = 0
    stale = 0

    for anchor in anchors:
        view_cls = get_view_class(anchor["subsystem"])
        if view_cls is None:
            continue
        try:
            view = view_cls()
            bot.add_view(view, message_id=anchor["message_id"])
            restored += 1
        except Exception as exc:
            logger.warning(
                "Could not restore anchor %s (msg=%d subsystem=%s): %s",
                anchor["anchor_id"],
                anchor["message_id"],
                anchor["subsystem"],
                exc,
            )
            await mark_stale(str(anchor["anchor_id"]))
            stale += 1

    logger.info(
        "Anchor recovery complete — %d restored, %d marked stale", restored, stale
    )


async def try_fetch_message(
    bot: commands.Bot, channel_id: int, message_id: int
) -> discord.Message | None:
    """Fetch a Discord message, returning None if it no longer exists."""
    channel = bot.get_channel(channel_id)
    if channel is None:
        return None
    try:
        return await channel.fetch_message(message_id)
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        return None
