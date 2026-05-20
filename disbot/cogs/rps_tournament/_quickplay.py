"""RPS quick-play command body (S4.6).

``!rps`` (and the PvP shape ``!rps @user [bet]``) is a one-shot
view-spawning command — no tournament state, no cog state.  Extracted
from the cog so the cog file fits under the S4.6 size ceiling.

The cog command stub delegates here with just ``ctx``, ``target``, and
``bet``.
"""

from __future__ import annotations

import discord
from discord.ext import commands

from utils import db as global_db
from utils.ui_constants import GAME_COLOR
from views.rps import (
    _FREE_WIN,
    _RpsPvpChallengeView,
    _RpsView,
)


async def run_quickrps_command(
    ctx: commands.Context,
    target: discord.Member | None,
    bet: int,
) -> None:
    """Body of ``!rps [target] [bet]``."""
    if bet < 0:
        await ctx.send("Bet must be 0 or a positive number.", delete_after=5)
        return

    # PvP challenge
    if target and target != ctx.author:
        if target.bot:
            await ctx.send("You can't challenge a bot to PvP.", delete_after=5)
            return
        if bet > 0:
            bal = await global_db.get_coins(ctx.author.id, ctx.guild.id)
            if bet > bal:
                await ctx.send(f"❌ You only have **{bal}** 🪙.", delete_after=8)
                return
        bet_str = f"**{bet}** 🪙" if bet else "free play"
        view = _RpsPvpChallengeView(ctx.author, target, ctx.guild.id, bet)  # type: ignore[arg-type]
        embed = discord.Embed(
            title="✂️ RPS Challenge!",
            description=(
                f"{ctx.author.mention} challenges {target.mention} to Rock Paper Scissors "
                f"({bet_str}).\n{target.mention}, do you accept?"
            ),
            color=GAME_COLOR,
        )
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg
        return

    # vs bot
    if bet > 0:
        bal = await global_db.get_coins(ctx.author.id, ctx.guild.id)
        if bet > bal:
            await ctx.send(f"❌ You only have **{bal}** 🪙.", delete_after=10)
            return
    view = _RpsView(ctx.author, ctx.guild.id, bet)  # type: ignore[assignment, arg-type]
    bet_str = f"**{bet}** 🪙" if bet else f"Free play (win = +{_FREE_WIN} 🪙)"
    embed = discord.Embed(
        title="✂️ Rock · Paper · Scissors",
        description=f"Bet: {bet_str}\nChoose your move!",
        color=GAME_COLOR,
    )
    msg = await ctx.send(embed=embed, view=view)
    view.message = msg
