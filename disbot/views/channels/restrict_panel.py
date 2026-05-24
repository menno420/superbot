"""Channel-restriction sub-panel.

Pick a channel, then lock (deny send_messages for @everyone) or unlock
(restore send_messages).  Auto-returns to the manager hub after the
action lands.
"""

from __future__ import annotations

import asyncio
import logging

import discord
from discord.ext import commands

from core.runtime import resources
from core.runtime.interaction_helpers import safe_defer, safe_edit, safe_followup
from core.runtime.panel_recovery import restore_parent_or_send_fresh
from utils.ui_constants import CHANNEL_COLOR, ERROR_COLOR, SUCCESS_COLOR
from views.base import BaseView
from views.channels._helpers import _ChannelSelect

logger = logging.getLogger("bot")


class _RestrictSubView(BaseView):
    """Restriction management: pick a channel, then choose lock or unlock."""

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
            placeholder="Select a channel to manage…",
        )
        self.add_item(self.channel_select)

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
        logger.error("RestrictSubView error on %s: %s", item, error, exc_info=True)
        msg = f"❌ {type(error).__name__}: {error}"
        await safe_followup(interaction, msg, ephemeral=True)

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🔒 Manage Restrictions",
            description=(
                "Select a channel, then choose a restriction action.\n\n"
                "**🔒 Lock** — disable send messages for @everyone\n"
                "**🔓 Unlock** — restore send messages for @everyone"
            ),
            color=CHANNEL_COLOR,
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

    async def _apply_restriction(
        self,
        interaction: discord.Interaction,
        *,
        send_messages: bool,
        action_label: str,
        past_tense: str,
        embed_color: discord.Color,
    ) -> None:
        if not self.selected_channel_id:
            await interaction.response.send_message(
                "Please select a channel first.",
                ephemeral=True,
            )
            return

        channel = resources.resolve_channel(
            interaction.guild,
            channel_id=self.selected_channel_id,
            kind="any",
        )
        if channel is None:
            await interaction.response.send_message(
                f"Channel `{self.selected_channel_name}` not found.",
                ephemeral=True,
            )
            return

        # Defer before the Discord permission write: set_permissions is
        # not instant under load and the subsequent edit_message would
        # race the 3 s interaction token.
        if not await safe_defer(interaction):
            return

        try:
            await channel.set_permissions(
                interaction.guild.default_role,
                send_messages=send_messages,
            )
        except discord.Forbidden:
            await safe_followup(
                interaction,
                "❌ I don't have permission to change that channel's permissions.",
                ephemeral=True,
            )
            return
        except discord.HTTPException as exc:
            await safe_followup(
                interaction,
                f"❌ Failed to update permissions: {exc}",
                ephemeral=True,
            )
            return

        result_embed = discord.Embed(
            title=f"{action_label} Applied",
            description=f"`{self.selected_channel_name}` has been {past_tense}.",
            color=embed_color,
        )
        result_embed.set_footer(text="Returning to the management panel…")

        for item in self.children:
            item.disabled = True

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

    @discord.ui.button(label="Lock", style=discord.ButtonStyle.red, emoji="🔒", row=1)
    async def lock_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self._apply_restriction(
            interaction,
            send_messages=False,
            action_label="🔒 Lock",
            past_tense="locked (send messages disabled for @everyone)",
            embed_color=ERROR_COLOR,
        )

    @discord.ui.button(
        label="Unlock",
        style=discord.ButtonStyle.green,
        emoji="🔓",
        row=1,
    )
    async def unlock_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self._apply_restriction(
            interaction,
            send_messages=True,
            action_label="🔓 Unlock",
            past_tense="unlocked (send messages restored for @everyone)",
            embed_color=SUCCESS_COLOR,
        )

    @discord.ui.button(label="↩️ Back", style=discord.ButtonStyle.grey, row=2)
    async def back_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        from views.channels.main_panel import _ChannelManagerView

        manager = _ChannelManagerView(self.ctx)
        manager.message = self.manager_message
        await interaction.response.edit_message(
            embed=manager.build_embed(),
            view=manager,
        )
        self.stop()
