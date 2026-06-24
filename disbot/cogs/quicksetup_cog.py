"""Quick Setup cog — the front door to Essential Setup.

A thin command surface (prefix + slash) that opens the plain-language,
direct-apply setup spine in :mod:`views.setup.essential_setup`.  Kept as its
own small cog rather than crowding ``setup_cog`` (which is at the size ceiling).
"""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands


class QuickSetupCog(commands.Cog):
    """Opens Essential Setup (the short, jargon-free guided spine)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="quicksetup", aliases=["essentialsetup"])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def quicksetup_cmd(self, ctx: commands.Context) -> None:
        """Open Essential Setup — a few simple steps, each saved instantly."""
        from views.setup.essential_setup import open_essential_setup_prefix

        await open_essential_setup_prefix(ctx)

    @app_commands.command(
        name="quicksetup",
        description="Quick guided setup — a few simple steps, no jargon.",
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def quicksetup_slash(self, interaction: discord.Interaction) -> None:
        """Slash front door for Essential Setup (admin-gated)."""
        from views.setup.essential_setup import open_essential_setup

        await open_essential_setup(interaction)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(QuickSetupCog(bot))
