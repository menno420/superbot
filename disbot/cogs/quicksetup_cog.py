"""Essential Setup cog — the front door to the guided setup spine.

A thin command surface (prefix + slash) that opens the plain-language,
direct-apply Essential Setup flow in :mod:`views.setup.essential_setup`.

This is the **primary** setup entry point: ``!setup`` / ``/setup`` open the
short, jargon-free guided spine (a separate ``#superbot-setup`` channel is
created for it).  The older section-list / draft → Final Review wizard now
lives behind ``!setupadvanced`` / ``/setup-advanced`` (:mod:`cogs.setup_cog`).

Kept as its own small cog rather than crowding ``setup_cog`` (which is at the
size ceiling); the file/class keep their ``quicksetup`` names for continuity,
but the operator-facing command is ``setup``.
"""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from core.runtime.permission_checks import admin_or_owner, app_admin_or_owner


class QuickSetupCog(commands.Cog):
    """Opens Essential Setup (the short, jargon-free guided spine) as ``!setup``."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="setup", aliases=["quicksetup", "essentialsetup"])
    @commands.guild_only()
    @admin_or_owner()
    async def setup_cmd(self, ctx: commands.Context) -> None:
        """Open Essential Setup — a few simple steps, each saved instantly."""
        from views.setup.essential_setup import open_essential_setup_prefix

        await open_essential_setup_prefix(ctx)

    @app_commands.command(
        name="setup",
        description="Guided setup — a few simple steps, no jargon.",
    )
    @app_commands.default_permissions(administrator=True)
    @app_admin_or_owner()
    @app_commands.guild_only()
    async def setup_slash(self, interaction: discord.Interaction) -> None:
        """Slash front door for Essential Setup (admin-gated)."""
        from views.setup.essential_setup import open_essential_setup

        await open_essential_setup(interaction)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(QuickSetupCog(bot))
