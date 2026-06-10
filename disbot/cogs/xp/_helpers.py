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
    """Build the rank card embed for a member.

    Ranks come from the canonical :mod:`services.rank_providers` registry
    (its docstring names this builder as a consumer) — the inline rank SQL
    this function used to carry was the drift the registry exists to kill.
    """
    from services.rank_providers import get_provider

    row = await db.get_xp(member.id, guild.id)
    level, current, needed = db.level_progress(row["xp"])

    async def _rank(provider_name: str) -> int | str:
        provider = get_provider(provider_name)
        if provider is None:  # registry always has xp/coins; stay crash-proof
            return "?"
        position, _ = await provider.member_rank(guild, member.id)
        return position if position is not None else "?"

    xp_rank = await _rank("xp")
    co_rank = await _rank("coins")

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
