"""Server Management hub cog — the unified operator entry point (PR14).

A thin command host for the Server Management hub: one builder
(:func:`views.server_management.hub.build_server_management_hub`), two front
doors. The persistent ``!servermanagement`` panel anchors via
``panel_manager.get_or_render_panel`` (restored across restart by the registered
:class:`~views.server_management.hub.ServerManagementHubView`); the ephemeral
``/server-management`` slash renders the same builder for a quick, throwaway
view.

The cog holds **no domain logic** — every action routes into an existing manager
inside the hub view. Importing the hub view module here also triggers its
``@register`` side-effect so the persistent-view registry is populated before
``on_ready`` runs ``restore_anchors`` (the same pattern moderation uses for
``ModPanelView``).
"""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from core.runtime import panel_manager
from core.runtime.permission_checks import admin_or_owner, app_admin_or_owner
from views.server_management.hub import build_server_management_hub

logger = logging.getLogger("bot")


class ServerManagementCog(commands.Cog):
    """Hosts the unified Server Management hub command + slash front doors."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(
        name="servermanagement",
        aliases=["servermenu", "guildmenu"],
    )
    @commands.guild_only()
    @admin_or_owner()
    async def servermanagement(self, ctx: commands.Context) -> None:
        """Open the unified Server Management hub."""
        embed, view = await build_server_management_hub(ctx.guild)
        # Panel-anchor key is the snake_case subsystem identity
        # (Q-0026 — written to panel_anchors.subsystem, must resolve in
        # SUBSYSTEMS); the command name above stays ``servermanagement``.
        msg = await panel_manager.get_or_render_panel(
            ctx,
            "server_management",
            embed,
            view,
        )
        view.message = msg

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook (returns the Server Management hub).

        Raises when invoked outside a guild so the help router falls back to
        the command-list embed (the hub is guild-only).
        """
        guild = interaction.guild
        if guild is None:
            raise RuntimeError("Server Management hub requires a guild")
        return await build_server_management_hub(guild)

    @app_commands.command(
        name="server-management",
        description="Open the Server Management hub (moderation, channels, roles, cleanup, setup).",
    )
    @app_commands.default_permissions(administrator=True)
    @app_admin_or_owner()
    @app_commands.guild_only()
    async def server_management_slash(
        self,
        interaction: discord.Interaction,
    ) -> None:
        """Ephemeral slash front door for the Server Management hub."""
        if interaction.guild is None:
            await interaction.response.send_message(
                "Use `/server-management` from inside a server.",
                ephemeral=True,
            )
            return
        embed, view = await build_server_management_hub(interaction.guild)
        await interaction.response.send_message(
            embed=embed,
            view=view,
            ephemeral=True,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ServerManagementCog(bot))
    logger.info("ServerManagementCog loaded.")
