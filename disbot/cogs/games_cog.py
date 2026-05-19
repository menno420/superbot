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
from discord import app_commands
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

    @app_commands.command(
        name="games",
        description="Open the Games hub (competitive + activities).",
    )
    async def games_slash(self, interaction: discord.Interaction) -> None:
        """Slash front door for the Games hub — ephemeral, governance-filtered.

        PR E1 — user-tier slash front door. Reuses
        :func:`views.games.hub.build_games_hub_panel` so visibility
        filtering and the click-time recheck from PR D apply
        identically to the slash entry. The response is ephemeral —
        slash hubs are personal panels per the ``/help`` convention.
        """
        embed, view = await build_games_hub_panel(
            interaction.user,
            interaction=interaction,
        )
        await interaction.response.send_message(
            embed=embed,
            view=view,
            ephemeral=True,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GamesCog(bot))
