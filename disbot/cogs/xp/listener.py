"""XP on_message handler (S4.2 extraction).

The pre-decomposition listener body was ~95 LOC inside
``cogs/xp_cog.py``.  Extracted here per the F-3 convention so the
cog file stays focused on commands and the handler is unit-testable
without spinning up the full XpCog instance.

Two entry points:

  handle_message(bot, message)        — drives the full cooldown +
                                         award + announce + role-grant
                                         flow.  Called from
                                         XpCog.on_message.
  announce_level_up(bot, message,     — extracted level-up bookkeeping
                    new_xp, new_level)  (announcement + log embed +
                                         role assignment).
"""

from __future__ import annotations

import logging
import random
import time

import discord
from discord.ext import commands

from services import xp_service
from utils import db
from utils.cooldowns import check_cooldown
from utils.guild_config_accessors import get_xp_config, get_xp_threshold_roles
from utils.helpers import post_log_embed
from utils.ui_constants import ECONOMY_COLOR

logger = logging.getLogger("bot.cogs.xp.listener")


async def handle_message(bot: commands.Bot, message: discord.Message) -> None:
    """The XP on_message hot path.  Bot/no-guild messages are dropped early.

    Hits the F-1 cached config (S2.2) on the common cooldown-skipped
    path so most messages run with zero DB-config reads.
    """
    if message.author.bot or not message.guild:
        return

    user_id = message.author.id
    guild_id = message.guild.id
    now = int(time.time())

    cfg = await get_xp_config(guild_id)

    row = await db.get_xp(user_id, guild_id)
    on_cd, _ = check_cooldown(row["last_xp"], cfg.cooldown)
    if on_cd:
        return

    amount = random.randint(cfg.xp_min, cfg.xp_max)
    result = await xp_service.award(
        guild_id=guild_id,
        user_id=user_id,
        amount=amount,
        source="chat",
        now=now,
    )

    if result.leveled_up:
        await announce_level_up(
            bot,
            message,
            new_xp=result.new_xp,
            new_level=result.new_level,
            announce_channel=cfg.announce_channel,
        )


async def announce_level_up(
    bot: commands.Bot,
    message: discord.Message,
    *,
    new_xp: int,
    new_level: int,
    announce_channel: str,
) -> None:
    """Post the level-up embed + log embed + apply XP threshold roles."""
    announce_ch: discord.TextChannel | None = None
    if announce_channel:
        announce_ch = message.guild.get_channel(int(announce_channel))  # type: ignore[assignment]
    announce_ch = announce_ch or message.channel  # type: ignore[assignment]

    embed = discord.Embed(
        title="🎉 Level Up!",
        description=f"{message.author.mention} reached **Level {new_level}**!",
        color=ECONOMY_COLOR,
    )
    try:
        await announce_ch.send(embed=embed)
    except discord.Forbidden:
        pass

    log_embed = discord.Embed(
        title="🏆 Level Up",
        description=(
            f"{message.author.mention} reached **Level {new_level}**! "
            f"(Total XP: {new_xp})"
        ),
        color=ECONOMY_COLOR,
    )
    await post_log_embed(bot, message.guild.id, log_embed)

    await _apply_xp_threshold_roles(message, new_level)


async def _apply_xp_threshold_roles(
    message: discord.Message,
    new_level: int,
) -> None:
    """Grant XP-threshold roles whose level_required <= new_level.

    Hits the F-1 cached threshold-roles list (S2.2) so the role list
    is at most one DB read per (TTL × guild) instead of per-level-up.
    """
    try:
        xp_roles = await get_xp_threshold_roles(message.guild.id)
        for role_cfg in xp_roles:
            if role_cfg["level_required"] <= new_level:
                discord_role = discord.utils.get(
                    message.guild.roles,
                    name=role_cfg["role_name"],
                )
                if (
                    discord_role
                    and discord_role not in message.author.roles  # type: ignore[union-attr]
                ):
                    try:
                        await message.author.add_roles(  # type: ignore[union-attr]
                            discord_role,
                            reason=f"XP level-up: reached level {new_level}",
                        )
                        logger.info(
                            "XP role assigned: %s → %s (level %d)",
                            message.author.display_name,
                            discord_role.name,
                            new_level,
                        )
                    except (discord.Forbidden, discord.HTTPException) as role_err:
                        logger.warning(
                            "Could not assign XP role %s to %s: %s",
                            discord_role.name,
                            message.author.display_name,
                            role_err,
                        )
    except Exception:
        logger.error(
            "XP role assignment check failed for guild %d",
            message.guild.id,
            exc_info=True,
        )
