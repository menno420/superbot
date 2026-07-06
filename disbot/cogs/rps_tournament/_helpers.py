"""RPS tournament helper functions (S4.6).

Module-level helpers extracted from ``cogs/rps_tournament_cog.py``:

  add_player_to_db        — idempotent rps_players row insert
  update_player_stats     — schedule async stat update
  create_match_channel    — PvP tournament private channel
  create_bot_match_channel — bot-vs-player private channel
  schedule_channel_deletion — 5-minute delayed delete
  delete_all_match_channels — full RPS Tournaments category cleanup
  clear_stale_tournament_flag — on-startup ACTIVE_TOURNAMENT sweep
  cleanup_orphaned_channels — on-startup match-channel cleanup

None reference cog instance state — they take what they need as
arguments.  Failure-handling logs and swallows so the cog's
high-level flow is not interrupted by transient Discord errors.
"""

from __future__ import annotations

import asyncio
import logging

import discord
from discord.ext import commands

from core.runtime import resources, tasks
from services import tournament_state_service
from utils import db as global_db
from utils.channels import cleanup_category, create_private_channel

logger = logging.getLogger("bot")


# ---------------------------------------------------------------------------
# Player stat helpers
# ---------------------------------------------------------------------------


async def add_player_to_db(user, guild_id: int) -> None:
    """Idempotent insert into the rps_players stats table.

    PR R1: ``guild_id`` required.  rps_players' PK is
    ``(user_id, guild_id)`` since migration 005; defaulting to 0 made
    every guild's stats collide at the same row.
    """
    try:
        await global_db.rps_ensure_player(user.id, guild_id, user.display_name)
    except Exception as e:
        logger.exception("Error adding RPS player to database: %s", e)


def update_player_stats(player, result: str) -> None:
    """Schedule an async stats update without blocking the event loop.

    PR R1: derives ``guild_id`` from ``player.guild`` and passes it
    through so ``rps_update_stat`` writes to the correct guild row.
    Players passed in here always come from a guild context (bot
    matches and tournament matches both originate in guild channels)
    so ``player.guild`` is non-None.
    """
    guild = getattr(player, "guild", None)
    if guild is None:
        logger.warning(
            "update_player_stats: player=%s has no guild context; skipping stat update",
            player.id,
        )
        return
    tasks.spawn(
        f"rps:stat:{player.id}",
        _async_update_stat(player.id, guild.id, result),
    )


async def _async_update_stat(user_id: int, guild_id: int, result: str) -> None:
    try:
        await global_db.rps_update_stat(user_id, guild_id, result)
    except Exception as e:
        logger.exception("Error updating RPS player stats: %s", e)


# ---------------------------------------------------------------------------
# Channel helpers
# ---------------------------------------------------------------------------


async def create_match_channel(guild, player1, player2, ctx):
    """Create a private channel for a PvP tournament match."""
    try:
        return await create_private_channel(
            guild,
            f"rps-{player1.display_name}-vs-{player2.display_name}",
            [player1, player2],
            "RPS Tournaments",
        )
    except discord.Forbidden:
        await ctx.send("I do not have permission to create channels.")
        return None
    except Exception as e:
        logger.exception(f"Error creating match channel: {e}")
        await ctx.send(f"An error occurred while creating the match channel: {e}")
        return None


async def create_bot_match_channel(guild, player, ctx):
    """Create a private channel for a bot-vs-player match."""
    try:
        return await create_private_channel(
            guild,
            f"rps-{player.display_name}-vs-bot",
            [player],
            "RPS Bot Matches",
        )
    except discord.Forbidden:
        await ctx.send("I do not have permission to create channels.")
        return None
    except Exception as e:
        logger.exception(f"Error creating bot match channel: {e}")
        await ctx.send(f"An error occurred while creating the match channel: {e}")
        return None


async def schedule_channel_deletion(channel) -> None:
    """Delete a match channel after a 5-minute delay (post-match cleanup)."""
    await asyncio.sleep(300)
    try:
        await channel.delete()
    except discord.Forbidden:
        logger.warning(
            f"Failed to delete channel {channel.name}: insufficient permissions.",
        )
    except Exception as e:
        logger.exception(
            f"An error occurred while deleting channel {channel.name}: {e}",
        )


async def delete_all_match_channels(guild) -> None:
    """Delete all RPS tournament match channels and the parent category."""
    category = resources.resolve_channel(
        guild,
        name="RPS Tournaments",
        kind="category",
    )
    if category:
        await cleanup_category(category)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Startup tasks
# ---------------------------------------------------------------------------


async def clear_stale_tournament_flag(bot: commands.Bot) -> None:
    """Reset ACTIVE_TOURNAMENT for any guild where it was left as 'rps'.

    Called once at cog_load to recover from a crash that left the
    flag set without an active in-memory tournament.
    """
    await bot.wait_until_ready()
    for guild in bot.guilds:
        flag = await tournament_state_service.get_active(guild.id)
        if flag == "rps":
            await tournament_state_service.clear_active(guild.id)


async def cleanup_orphaned_channels(bot: commands.Bot) -> None:
    """At startup, drop leftover RPS Tournament + RPS Bot Match channels.

    Sends a 5-min warning to each channel first, then deletes the
    parent categories.  Called once at cog_load.
    """
    await bot.wait_until_ready()
    for guild in bot.guilds:
        for cat_name in ("RPS Tournaments", "RPS Bot Matches"):
            cat = resources.resolve_channel(guild, name=cat_name, kind="category")
            if not cat or not cat.channels:
                continue
            for ch in cat.channels:
                # Match channels are TextChannel; voice/stage/forum slots
                # can't receive a "match interrupted" notice.
                if not isinstance(ch, discord.TextChannel):
                    continue
                try:
                    await ch.send(
                        "⚠️ The bot restarted and this match was interrupted. "
                        "This channel will be deleted in 5 minutes.",
                    )
                except Exception:
                    pass
            await asyncio.sleep(300)
            await cleanup_category(cat)
