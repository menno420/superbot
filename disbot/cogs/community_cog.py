"""Community hub cog — thin router that opens :class:`CommunityHubView`.

There is no pre-existing "community" domain cog. Per the mother-hub
map, the Community hub aggregates XP + Roles (primary) and cross-links
to Counting / Chain / Leaderboard — so a new cog owns the hub view
without taking on any business logic. Game state stays in counting/
chain_cog, role-XP rules stay in role_cog, etc.

This cog only owns:

* The ``!community`` command that opens the hub directly.
* The :meth:`build_help_menu_view` hook that surfaces the hub from
  ``!help`` → "Community".

No DB writes, no game logic, no governance resolution. The view's
buttons forward to each child cog's existing ``build_help_menu_view``
hook — same routing pattern as :class:`HelpCategoryView`.
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from core.runtime.interaction_helpers import help_ctx_shim
from views.base import send_panel
from views.community.hub import CommunityHubView, build_community_hub_embed

logger = logging.getLogger("bot.cogs.community")


class CommunityCog(commands.Cog):
    """Router-only Community hub. No business logic lives here."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="community")
    async def community_menu(self, ctx: commands.Context) -> None:
        """Open the Community hub — XP, Roles, and community activities."""
        view = CommunityHubView(ctx.author)
        await send_panel(ctx, embed=build_community_hub_embed(), view=view)

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook — returns the Community hub panel."""
        ctx_shim = help_ctx_shim(interaction)
        view = CommunityHubView(ctx_shim.author)
        return build_community_hub_embed(), view


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CommunityCog(bot))
