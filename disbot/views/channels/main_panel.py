"""Top-level channel-management hub.

Owns the three primary action buttons: create, delete, restrict, and
visibility.  Each button transitions the same Discord message to its
sub-panel; sub-panels return here via their back/cancel callbacks.
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from utils.ui_constants import CHANNEL_COLOR
from views.base import HubView
from views.channels._helpers import _build_channel_options

logger = logging.getLogger("bot")


class _ChannelManagerView(HubView):
    """Top-level channel management panel with three action modes."""

    def __init__(self, ctx: commands.Context):
        super().__init__(ctx.author)
        self.ctx = ctx

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item,
    ) -> None:
        logger.error("ChannelManagerView error on %s: %s", item, error, exc_info=True)
        msg = f"❌ {type(error).__name__}: {error}"
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(msg, ephemeral=True)
            else:
                await interaction.followup.send(msg, ephemeral=True)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Embed
    # ------------------------------------------------------------------

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🛠️ Channel Management Panel",
            description=(
                "Select an action below to manage your server's channels.\n\n"
                "**➕ Create Channel** — interactive channel creator\n"
                "**🗑️ Delete Channel** — select and delete a channel\n"
                "**🔒 Manage Restrictions** — lock or unlock a channel"
            ),
            color=CHANNEL_COLOR,
        )
        embed.set_footer(text="Only the command author can interact with this panel.")
        return embed

    # ------------------------------------------------------------------
    # Buttons (row 0)
    # ------------------------------------------------------------------

    @discord.ui.button(
        label="Create Channel",
        style=discord.ButtonStyle.green,
        emoji="➕",
        row=0,
    )
    async def create_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        # Local import — avoid circular dependency (create_panel imports back into us).
        from views.channels.create_panel import _CreateSubView

        sub = _CreateSubView(self.ctx, manager_message=self.message)
        await interaction.response.edit_message(embed=sub.build_embed(), view=sub)

    @discord.ui.button(
        label="Delete Channel",
        style=discord.ButtonStyle.red,
        emoji="🗑️",
        row=0,
    )
    async def delete_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        from views.channels.delete_panel import _DeleteSubView

        options = _build_channel_options(interaction.guild)
        if not options:
            await interaction.response.send_message(
                "No text or voice channels found on this server.",
                ephemeral=True,
            )
            return
        sub = _DeleteSubView(self.ctx, options=options, manager_message=self.message)
        await interaction.response.edit_message(embed=sub.build_embed(), view=sub)

    @discord.ui.button(
        label="Manage Restrictions",
        style=discord.ButtonStyle.blurple,
        emoji="🔒",
        row=0,
    )
    async def restrict_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        from views.channels.restrict_panel import _RestrictSubView

        options = _build_channel_options(interaction.guild)
        if not options:
            await interaction.response.send_message(
                "No text or voice channels found on this server.",
                ephemeral=True,
            )
            return
        sub = _RestrictSubView(self.ctx, options=options, manager_message=self.message)
        await interaction.response.edit_message(embed=sub.build_embed(), view=sub)

    @discord.ui.button(
        label="Subsystem Visibility",
        style=discord.ButtonStyle.grey,
        emoji="🔍",
        row=1,
    )
    async def visibility_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        from views.channels.visibility_panel import _VisibilitySubView

        sub = _VisibilitySubView(self.ctx, manager_message=self.message)
        await interaction.response.edit_message(embed=sub.build_embed(), view=sub)
