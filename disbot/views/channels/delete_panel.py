"""Channel-deletion sub-panel + confirmation step.

Two-stage flow: ``_DeleteSubView`` picks the channel; pressing
"Delete Selected" transitions to ``_DeleteConfirmView`` which actually
performs the delete after a confirmation click.
"""

from __future__ import annotations

import asyncio
import logging

import discord
from discord.ext import commands

from core.runtime import resources
from core.runtime.interaction_helpers import safe_defer, safe_edit, safe_followup
from core.runtime.panel_recovery import restore_parent_or_send_fresh
from utils.ui_constants import ERROR_COLOR, SUCCESS_COLOR, WARNING_COLOR
from views.base import BaseView
from views.channels._helpers import _build_channel_options, _ChannelSelect
from views.navigation import attach_back_button

logger = logging.getLogger("bot")


class _DeleteSubView(BaseView):
    """Channel-deletion sub-panel with a select menu and confirmation flow."""

    def __init__(
        self,
        ctx: commands.Context,
        *,
        options: list[discord.SelectOption],
        manager_message: discord.Message | None,
    ):
        super().__init__(ctx.author, timeout=120)
        self.ctx = ctx
        self.manager_message = manager_message
        self.selected_channel_id: int | None = None
        self.selected_channel_name: str | None = None

        self.channel_select = _ChannelSelect(
            options,
            self,
            placeholder="Select a channel to delete…",
        )
        self.add_item(self.channel_select)

        async def _build_parent(
            _interaction: discord.Interaction,
        ) -> tuple[discord.Embed, discord.ui.View]:
            from views.channels.main_panel import _ChannelManagerView

            manager = _ChannelManagerView(self.ctx)
            manager.message = self.manager_message
            return manager.build_embed(), manager

        attach_back_button(
            self,
            label="↩️ Back",
            custom_id="channels:delete:back",
            parent_builder=_build_parent,
            row=1,
        )

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item,
    ) -> None:
        # Channel-management views intentionally surface
        # ``type(error).__name__`` to admins for diagnosability — see
        # ``views.base.handle_view_error`` docstring. ``safe_followup``
        # collapses the legacy ``is_done()`` ladder to a single call
        # that routes through ``followup.send`` or ``response.send_message``
        # as appropriate, and swallows the recoverable errors itself.
        logger.error("DeleteSubView error on %s: %s", item, error, exc_info=True)
        msg = f"❌ {type(error).__name__}: {error}"
        await safe_followup(interaction, msg, ephemeral=True)

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🗑️ Delete Channel",
            description="Select the channel you want to delete, then press **Delete Selected**.",
            color=ERROR_COLOR,
        )
        embed.add_field(
            name="Selected channel",
            value=(
                f"`{self.selected_channel_name}`"
                if self.selected_channel_name
                else "*(none)*"
            ),
            inline=False,
        )
        return embed

    def _confirm_embed(self) -> discord.Embed:
        return discord.Embed(
            title="⚠️ Confirm Deletion",
            description=(
                f"Are you sure you want to delete **`{self.selected_channel_name}`**?\n"
                "**This action cannot be undone.**"
            ),
            color=ERROR_COLOR,
        )

    @discord.ui.button(
        label="Delete Selected",
        style=discord.ButtonStyle.red,
        emoji="🗑️",
        row=1,
    )
    async def delete_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not self.selected_channel_id:
            await interaction.response.send_message(
                "Please select a channel first.",
                ephemeral=True,
            )
            return
        confirm_view = _DeleteConfirmView(
            self.ctx,
            channel_id=self.selected_channel_id,
            channel_name=self.selected_channel_name,
            manager_message=self.manager_message,
        )
        await interaction.response.edit_message(
            embed=self._confirm_embed(),
            view=confirm_view,
        )
        self.stop()


class _DeleteConfirmView(BaseView):
    """Confirmation step before actually deleting a channel."""

    def __init__(
        self,
        ctx: commands.Context,
        *,
        channel_id: int,
        channel_name: str,
        manager_message: discord.Message | None,
    ):
        super().__init__(ctx.author, timeout=60)
        self.ctx = ctx
        self.channel_id = channel_id
        self.channel_name = channel_name
        self.manager_message = manager_message

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item,
    ) -> None:
        # See _DeleteSubView.on_error for the channels-view rationale.
        logger.error("DeleteConfirmView error on %s: %s", item, error, exc_info=True)
        msg = f"❌ {type(error).__name__}: {error}"
        await safe_followup(interaction, msg, ephemeral=True)

    @discord.ui.button(
        label="Confirm Delete",
        style=discord.ButtonStyle.red,
        emoji="🗑️",
        row=0,
    )
    async def confirm_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        # Defer before the Discord delete: channel.delete() is not
        # instant and the subsequent edit_message would race the 3 s
        # interaction token.
        if not await safe_defer(interaction):
            return

        channel = resources.resolve_channel(
            interaction.guild,
            channel_id=self.channel_id,
            kind="any",
        )
        if channel is None:
            result_embed = discord.Embed(
                title="❌ Channel Not Found",
                description=f"Channel `{self.channel_name}` could not be found — it may have already been deleted.",
                color=WARNING_COLOR,
            )
        else:
            try:
                await channel.delete()
                result_embed = discord.Embed(
                    title="✅ Channel Deleted",
                    description=f"`{self.channel_name}` has been deleted.",
                    color=SUCCESS_COLOR,
                )
            except discord.Forbidden:
                result_embed = discord.Embed(
                    title="❌ Permission Denied",
                    description="I don't have permission to delete that channel.",
                    color=ERROR_COLOR,
                )
            except discord.HTTPException as exc:
                result_embed = discord.Embed(
                    title="❌ Error",
                    description=f"Failed to delete channel: {exc}",
                    color=ERROR_COLOR,
                )

        for item in self.children:
            item.disabled = True
        result_embed.set_footer(text="Returning to the management panel…")
        await safe_edit(interaction, embed=result_embed, view=self)
        self.stop()

        await asyncio.sleep(2)
        from views.channels.main_panel import _ChannelManagerView

        manager = _ChannelManagerView(self.ctx)
        restored = await restore_parent_or_send_fresh(
            parent_message=self.manager_message,
            channel=interaction.channel,
            embed=manager.build_embed(),
            view=manager,
        )
        if restored is not None:
            manager.message = restored

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.grey,
        emoji="❌",
        row=0,
    )
    async def cancel_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        options = _build_channel_options(interaction.guild)
        sub = _DeleteSubView(
            self.ctx,
            options=options,
            manager_message=self.manager_message,
        )
        await interaction.response.edit_message(embed=sub.build_embed(), view=sub)
        self.stop()
