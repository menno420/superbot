"""Games hub cog — thin router that opens :class:`GamesHubView`.

This cog contains **zero** game logic. Individual game logic stays in
Blackjack, RPS Tournament, Deathmatch, Mining, Counting, and Chain.
The hub here only owns:

* The ``!games`` command that opens the hub directly.
* The :meth:`build_help_menu_view` hook that surfaces the hub from
  ``!help`` → "Games".

The view itself (in :mod:`views.games.hub`) discovers its children from
``SUBSYSTEMS`` by filtering on ``parent_hub == "games"`` — there is no
hard-coded child list here.
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from core.runtime.interaction_helpers import help_ctx_shim
from views.base import send_panel
from views.games.hub import build_games_hub_panel

logger = logging.getLogger("bot.cogs.games")


class GamesCog(commands.Cog):
    """Router-only Games hub. No game logic lives here."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="games")
    async def games_menu(self, ctx: commands.Context) -> None:
        """Open the Games hub — competitive games and channel activities."""
        embed, view = await build_games_hub_panel(ctx.author, ctx=ctx)
        await send_panel(ctx, embed=embed, view=view)

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook — returns the Games hub panel."""
        ctx_shim = help_ctx_shim(interaction)
        return await build_games_hub_panel(ctx_shim.author, interaction=interaction)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GamesCog(bot))
