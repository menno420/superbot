"""Shared XP helpers (S4.2-followup extraction).

These were top-level helpers in ``cogs/xp_cog.py`` consumed by the rank
command, the rank view, the hub panel, and the config panel.  Lifted
here per the F-3 convention so they live alongside the listener body
and are importable by both the cog and ``views/xp/*`` without
creating a circular import through ``cogs.xp_cog``.

Public-ish names (no leading underscore in spirit, but kept consistent
with the historical naming so the diff stays small):

    _STAT_TYPES         — vocabulary accepted by !rank / !leaderboard
    _guild_xp_settings  — tuple shim around get_xp_config (cache-aware)
    _progress_bar       — ascii bar renderer
    _build_rank_embed   — rank card embed builder
"""

from __future__ import annotations

import discord

from utils import db
from utils.guild_config_accessors import get_xp_config
from utils.ui_constants import UTILITY_COLOR

_STAT_TYPES: set[str] = {"xp", "coins", "both"}


async def _guild_xp_settings(guild_id: int) -> tuple[int, int, int]:
    """Return (xp_min, xp_max, cooldown_seconds) for this guild.

    Thin shim around ``guild_config_accessors.get_xp_config`` retained
    for the few callers that want the tuple shape directly.  Cache-aware
    — uses the same F-1 cache as the on_message hot path.
    """
    cfg = await get_xp_config(guild_id)
    return cfg.xp_min, cfg.xp_max, cfg.cooldown


def _progress_bar(current: int, needed: int, width: int = 10) -> str:
    filled = int((current / needed) * width) if needed else width
    return "█" * filled + "░" * (width - filled)


async def _build_rank_embed(
    member: discord.Member,
    guild: discord.Guild,
    stat: str,
) -> discord.Embed:
    """Build the rank card embed for a member."""
    row = await db.get_xp(member.id, guild.id)
    level, current, needed = db.level_progress(row["xp"])

    all_xp = await db.fetchall(
        "SELECT user_id FROM xp WHERE guild_id=$1 ORDER BY xp DESC",
        (guild.id,),
    )
    all_coins = await db.fetchall(
        "SELECT user_id FROM xp WHERE guild_id=$1 ORDER BY coins DESC",
        (guild.id,),
    )
    xp_rank = next(
        (i + 1 for i, r in enumerate(all_xp) if r["user_id"] == member.id),
        "?",
    )
    co_rank = next(
        (i + 1 for i, r in enumerate(all_coins) if r["user_id"] == member.id),
        "?",
    )

    embed = discord.Embed(title=f"📊 {member.display_name}", color=UTILITY_COLOR)
    embed.set_thumbnail(url=member.display_avatar.url)

    if stat in ("both", "xp"):
        bar = _progress_bar(current, needed)
        embed.add_field(name="XP Rank", value=f"#{xp_rank}", inline=True)
        embed.add_field(name="Level", value=str(level), inline=True)
        embed.add_field(name="Total XP", value=str(row["xp"]), inline=True)
        embed.add_field(
            name="Progress",
            value=f"`{bar}` {current}/{needed} XP",
            inline=False,
        )
        embed.add_field(name="Messages", value=str(row["messages"]), inline=True)

    if stat in ("both", "coins"):
        embed.add_field(name="Coin Rank", value=f"#{co_rank}", inline=True)
        embed.add_field(name="🪙 Coins", value=str(row.get("coins", 0)), inline=True)

    return embed
