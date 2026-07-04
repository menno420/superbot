"""UX Lab cog — the interface-gallery workbench entry point.

Thin by design: this cog only routes ``!uxlab`` / ``/uxlab`` to the gallery
home view. All exhibit content lives in ``views/ux_lab/``; pattern metadata
lives in ``utils/ux_patterns/``. The lab performs **zero writes** — no DB,
no guild mutations, no audit events (enforced by
``tests/unit/invariants/test_ux_lab_zero_write.py``).

Design: ``docs/planning/ux-lab-interface-gallery-plan-2026-06-12.md``.
Audience: administrators (panel callbacks re-check via BaseView author lock;
the entry commands carry the admin permission gate). Q-0116 may widen this.
"""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from core.runtime.permission_checks import admin_or_owner, app_admin_or_owner
from views.base import send_panel
from views.ux_lab import UxLabHomeView, build_home_embed

logger = logging.getLogger("bot.uxlab")


class UxLabCog(commands.Cog, name="UX Lab"):  # type: ignore[call-arg]
    """Browse every Discord UX pattern SuperBot could use — safely fake."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self) -> None:
        # Anchor-free boot registration (the SetupLauncherView precedent) so
        # the persistence exhibit's panel keeps answering across restarts.
        from views.ux_lab.persistent_demo import UxLabPersistentDemo

        self.bot.add_view(UxLabPersistentDemo())

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help/hub direct-navigation hook (returns the gallery home)."""
        if interaction.guild is None:
            return (
                discord.Embed(description="The UX Lab only opens inside a server."),
                discord.ui.View(),
            )
        return build_home_embed(), UxLabHomeView(interaction.user)

    @commands.guild_only()
    @admin_or_owner()
    @commands.command(name="uxlab", aliases=["interfacelab"])
    async def uxlab(self, ctx: commands.Context) -> None:
        """Open the UX Lab — the interface gallery + limit probe bench."""
        await send_panel(ctx, embed=build_home_embed(), view=UxLabHomeView(ctx.author))

    @app_commands.command(
        name="uxlab",
        description="Open the UX Lab — browse interface patterns (admin).",
    )
    @app_commands.default_permissions(administrator=True)
    @app_admin_or_owner()
    @app_commands.guild_only()
    async def uxlab_slash(self, interaction: discord.Interaction) -> None:
        """Slash front door to the same panel (one door, not one per action)."""
        view = UxLabHomeView(interaction.user)
        await interaction.response.send_message(
            embed=build_home_embed(),
            view=view,
        )
        view.message = await interaction.original_response()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(UxLabCog(bot))
