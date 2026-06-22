"""Casino subsystem — Discord plumbing for group casino games.

Owner-directed: a casino under the Games hub for **group card games** where
every player gets their own auto-updating ephemeral message.  v1 ships
multiplayer Texas Hold'em poker; roulette and friends dock into the same hub.

Layering (mirrors the games cogs):

    utils/cards/                 — pure 52-card primitives (shared)
    utils/poker/                 — pure hand eval + Hold'em engine (tested)
    views/casino/poker_table.py  — the per-player ephemeral table + broadcast
    views/casino/hub.py          — the Casino navigation hub

This file hosts only commands, the cog lifecycle, and the Help-menu hook.
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from views.casino import build_casino_hub_panel, poker_table

logger = logging.getLogger("bot.cogs.casino")


class CasinoCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_check(self, ctx: commands.Context) -> bool:
        if ctx.guild is None:
            raise commands.NoPrivateMessage()
        return True

    # ------------------------------------------------------------------ commands

    @commands.command(name="casino")
    async def casino(self, ctx: commands.Context) -> None:
        """Open the Casino hub — group card games like poker."""
        embed, view = build_casino_hub_panel(ctx.author)
        view.message = await ctx.send(embed=embed, view=view)

    @commands.command(name="poker", aliases=["holdem"])
    async def poker(self, ctx: commands.Context) -> None:
        """Open a multiplayer Texas Hold'em table in this channel."""
        existing = poker_table.get_table(ctx.channel.id)
        if existing is not None and not existing.ended:
            await ctx.send(
                "♠ There's already an active poker table in this channel — "
                "join that one or wait for it to finish.",
            )
            return
        table = await poker_table.launch_table(
            self.bot,
            ctx.channel,
            ctx.channel.id,
            ctx.author,
        )
        if table is None:
            await ctx.send("♠ A poker table is already open here.")

    # ------------------------------------------------------------------ help hook

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu / Games-hub direct-navigation hook — the Casino hub."""
        return build_casino_hub_panel(interaction.user)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CasinoCog(bot))
