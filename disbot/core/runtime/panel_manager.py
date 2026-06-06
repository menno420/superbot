"""Persistent panel lifecycle management.

A panel is a Discord message with an interactive view that is anchored to a
specific (user, channel, subsystem) triple in the database.  The anchor table
enforces one panel per triple at a time.

Re-invocation behavior — every panel command sends a FRESH message at the
bottom of the channel.  If a prior anchored message exists for the same
(user, channel, subsystem), it is deleted first so the channel doesn't
accumulate orphaned panels.  This matches the user-facing expectation that
running a command produces a new visible result.

Concurrency note (RC-3 verification, 2026-06-05): the delete → mark_stale →
send → upsert sequence below is NOT internally serialised.  Two concurrent
invocations for the same (user, channel, subsystem) could race (double-send /
orphaned anchor).  This is unreproduced in practice and is deliberately left
unaddressed here — per the RC-3 plan (ADR-004) a panel-serialisation fix is a
separate change from the fail-open posture work, not bundled into it.

Public surface:
    get_or_render_panel(ctx, subsystem, embed, view) → discord.Message
"""

from __future__ import annotations

import logging
from collections.abc import Callable

import discord
from discord.ext import commands

from core.runtime import message_anchor_manager

logger = logging.getLogger("bot.runtime.panels")

# Optional hook, registered once at startup by ``HelpCog``, that appends a
# "↩ Back to Help" button (and seeds ``view._back_target``) on a freshly
# rendered hub view so directly-invoked hubs (`!modmenu`, `!economymenu`, …)
# get the same back-navigation as the `!help` route.  Core stays decoupled
# from the cogs/views layer by holding an opaque callable — the same
# register-at-startup pattern as ``cleanup_registry``.  A failure in the hook
# must never break panel rendering.
_back_to_help_attacher: Callable[[discord.ui.View], None] | None = None


def register_back_to_help_attacher(
    attacher: Callable[[discord.ui.View], None],
) -> None:
    """Register the hub back-to-help hook (idempotent; last registration wins)."""
    global _back_to_help_attacher
    _back_to_help_attacher = attacher


async def get_or_render_panel(
    ctx: commands.Context,
    subsystem: str,
    embed: discord.Embed,
    view: discord.ui.View,
) -> discord.Message:
    """Send a fresh panel message, deleting the prior anchored one if any.

    Returns the newly-sent Discord Message.
    """
    user_id = ctx.author.id
    guild_id = ctx.guild.id
    channel_id = ctx.channel.id

    anchor = await message_anchor_manager.get(user_id, channel_id, subsystem)

    if anchor and not anchor["is_stale"]:
        try:
            old_msg = await ctx.channel.fetch_message(anchor["message_id"])
            await old_msg.delete()
            logger.debug(
                "Prior panel deleted | subsystem=%s | user=%d | msg=%d",
                subsystem,
                user_id,
                anchor["message_id"],
            )
        except discord.NotFound:
            logger.debug(
                "Prior panel already gone | subsystem=%s | user=%d | msg=%d",
                subsystem,
                user_id,
                anchor["message_id"],
            )
        except (discord.Forbidden, discord.HTTPException) as exc:
            logger.warning(
                "Could not delete prior panel | subsystem=%s user=%d msg=%d: %s",
                subsystem,
                user_id,
                anchor["message_id"],
                exc,
            )
        await message_anchor_manager.mark_stale(str(anchor["anchor_id"]))

    # Give directly-invoked hubs the same "↩ Back to Help" affordance as the
    # !help route (and seed view._back_target so sub-panels inherit the chain).
    if _back_to_help_attacher is not None:
        try:
            _back_to_help_attacher(view)
        except Exception:  # noqa: BLE001 — back-nav must never break rendering
            logger.warning(
                "get_or_render_panel: back-to-help attach failed | subsystem=%s",
                subsystem,
                exc_info=True,
            )

    msg = await ctx.send(embed=embed, view=view)
    await message_anchor_manager.upsert(
        user_id,
        guild_id,
        channel_id,
        subsystem,
        msg.id,
    )
    logger.debug(
        "New panel anchored | subsystem=%s | user=%d | msg=%d",
        subsystem,
        user_id,
        msg.id,
    )
    return msg
