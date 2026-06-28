"""Counting leaderboard rendering — the player-facing standings.

Turns the per-channel ``leaderboard`` tally that :mod:`cogs.counting.handler`
increments on every accepted count into the embeds for ``!counttop`` and the
``!count_info`` top-counters summary.  Kept out of ``counting_cog`` so the cog
stays under the S4.6 LOC threshold; the ranking math itself is the pure
:func:`cogs.counting.game_logic.top_counters`.
"""

from __future__ import annotations

import discord

from cogs.counting import game_logic
from core.runtime import resources

_MEDALS = ("🥇", "🥈", "🥉")


def _ranked_lines(
    guild: discord.Guild,
    ranked: list[tuple[str, int]],
    *,
    with_unit: bool,
) -> list[str]:
    """Format ``(user_id, count)`` pairs into medal/rank lines.

    *with_unit* appends "count(s)" (the full ``!counttop`` look); the compact
    ``count_info`` summary leaves it off.
    """
    lines = []
    for rank, (user_id, count) in enumerate(ranked):
        prefix = _MEDALS[rank] if rank < len(_MEDALS) else f"**{rank + 1}.**"
        member = resources.resolve_member(guild, user_id)
        name = member.display_name if member else f"User {user_id}"
        if with_unit:
            unit = "count" if count == 1 else "counts"
            lines.append(f"{prefix} {name} — **{count}** {unit}")
        else:
            lines.append(f"{prefix} {name} — **{count}**")
    return lines


def build_leaderboard_embed(
    guild: discord.Guild,
    channel: discord.abc.GuildChannel,
    leaderboard: dict[str, int],
) -> discord.Embed:
    """The full ``!counttop`` leaderboard embed for one counting channel."""
    ranked = game_logic.top_counters(leaderboard, limit=10)
    embed = discord.Embed(
        title=f"🔢 Counting Leaderboard — #{channel.name}",
        color=discord.Color.gold(),
    )
    if not ranked:
        embed.description = "No correct counts yet — be the first to count!"
    else:
        embed.description = "\n".join(_ranked_lines(guild, ranked, with_unit=True))
    return embed


def top_field_value(
    guild: discord.Guild,
    leaderboard: dict[str, int],
) -> str | None:
    """The compact top-3 body for the ``!count_info`` field (``None`` when empty)."""
    ranked = game_logic.top_counters(leaderboard, limit=3)
    if not ranked:
        return None
    body = "\n".join(_ranked_lines(guild, ranked, with_unit=False))
    return f"{body}\n*See all with `!counttop`*"
