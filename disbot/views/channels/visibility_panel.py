"""Subsystem-visibility sub-panel + per-channel toggle grid.

Two-stage flow: ``_VisibilitySubView`` selects a channel via
``_ChannelSelectForVisibility``; the resulting ``_SubsystemToggleView``
shows one tri-state button per non-internal subsystem.

The toggle callback writes through ``governance_service.set_subsystem_visibility``,
which routes via ``GovernanceMutationPipeline`` (audit log + cache
invalidation + event emission per INV-E).
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from core.runtime import resources
from services import governance_service
from services.governance_service import GovernanceContext
from utils.subsystem_registry import all_subsystems_sorted
from utils.ui_constants import CHANNEL_COLOR
from views.base import BaseView

logger = logging.getLogger("bot")


class _ChannelSelectForVisibility(discord.ui.Select):
    def __init__(self, guild: discord.Guild):
        channels = guild.text_channels[:25]
        options = [
            discord.SelectOption(
                label=f"#{ch.name}"[:100],
                value=str(ch.id),
                description=f"ID: {ch.id}",
            )
            for ch in channels
        ]
        super().__init__(
            placeholder="Select a channel to configure…",
            min_values=1,
            max_values=1,
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction):
        channel_id = int(self.values[0])
        channel = resources.resolve_channel(
            interaction.guild,
            channel_id=channel_id,
            kind="any",
        )
        if not channel:
            await interaction.response.send_message(
                "Channel not found.",
                ephemeral=True,
            )
            return
        sub = _SubsystemToggleView(
            self.view.ctx,
            channel=channel,  # type: ignore[arg-type]
            manager_message=self.view.manager_message,
        )
        await sub.load(interaction.guild_id)
        await interaction.response.edit_message(embed=sub.build_embed(), view=sub)


class _VisibilitySubView(BaseView):
    def __init__(
        self,
        ctx: commands.Context,
        *,
        manager_message: discord.Message | None,
    ):
        super().__init__(ctx.author, timeout=180)
        self.ctx = ctx
        self.manager_message = manager_message
        self.add_item(_ChannelSelectForVisibility(ctx.guild))

    def build_embed(self) -> discord.Embed:
        return discord.Embed(
            title="🔍 Subsystem Visibility",
            description=(
                "Select a channel below to configure which subsystems are visible there.\n\n"
                "**Green** = enabled  •  **Red** = disabled  •  **Grey** = inheriting from parent scope\n\n"
                "_Showing up to 25 channels. Category and guild-scope controls coming soon._"
            ),
            color=CHANNEL_COLOR,
        )

    @discord.ui.button(label="↩ Back", style=discord.ButtonStyle.grey, row=1)
    async def back_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        from views.channels.main_panel import _ChannelManagerView

        view = _ChannelManagerView(self.ctx)
        view.message = self.manager_message
        await interaction.response.edit_message(embed=view.build_embed(), view=view)


class _SubsystemToggleView(BaseView):
    """Per-channel subsystem toggle panel."""

    def __init__(
        self,
        ctx: commands.Context,
        *,
        channel: discord.TextChannel,
        manager_message: discord.Message | None,
    ):
        super().__init__(ctx.author, timeout=180)
        self.ctx = ctx
        self.channel = channel
        self.manager_message = manager_message
        self._visibility: dict[str, bool | None] = {}

    async def load(self, guild_id: int) -> None:
        from utils import db

        rows = await db.get_subsystem_visibility(guild_id, "channel", self.channel.id)
        self._visibility = rows
        self._rebuild_buttons()

    def _rebuild_buttons(self) -> None:
        # Remove all items except the static back button
        for item in list(self.children):
            self.remove_item(item)

        visible_subsystems = [
            (name, meta)
            for name, meta in all_subsystems_sorted()
            if meta.get("visibility_mode", "normal") not in ("internal",)
        ][
            :20
        ]  # max 20 toggles to stay within Discord's 25-item limit

        for i, (name, meta) in enumerate(visible_subsystems):
            state = self._visibility.get(name)  # None = inherit
            if state is True:
                style = discord.ButtonStyle.green
                label = f"✓ {meta.get('display_name', name)}"
            elif state is False:
                style = discord.ButtonStyle.red
                label = f"✗ {meta.get('display_name', name)}"
            else:
                style = discord.ButtonStyle.grey
                label = f"~ {meta.get('display_name', name)}"

            btn = discord.ui.Button(  # type: ignore[var-annotated]
                label=label[:80],
                style=style,
                row=min(1 + i // 5, 4),
                custom_id=f"toggle_{name}",
            )
            btn.callback = self._make_toggle_callback(name)  # type: ignore[method-assign]
            self.add_item(btn)

    def _make_toggle_callback(self, subsystem_name: str):
        async def callback(interaction: discord.Interaction):
            current = self._visibility.get(subsystem_name)
            # Cycle: None (inherit) → True (force on) → False (force off) → None
            if current is None:
                new_val: bool | None = True
            elif current is True:
                new_val = False
            else:
                new_val = None

            gctx = GovernanceContext.from_interaction(interaction)
            try:
                await governance_service.set_subsystem_visibility(
                    gctx,
                    "channel",
                    self.channel.id,
                    subsystem_name,
                    new_val,
                )
            except Exception as exc:
                logger.warning(
                    "Subsystem visibility toggle failed | subsystem=%r exc=%s",
                    subsystem_name,
                    exc,
                    exc_info=True,
                )
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        f"Could not update visibility for **{subsystem_name}**: {exc}",
                        ephemeral=True,
                    )
                return
            self._visibility[subsystem_name] = new_val
            self._rebuild_buttons()
            await interaction.response.edit_message(embed=self.build_embed(), view=self)

        return callback

    def build_embed(self) -> discord.Embed:
        return discord.Embed(
            title=f"🔍 #{self.channel.name} — Subsystem Visibility",
            description=(
                "Toggle subsystem visibility for this channel.\n"
                "**✓ Green** = force enabled  •  **✗ Red** = force disabled  "
                "•  **~ Grey** = inherit from guild/category"
            ),
            color=CHANNEL_COLOR,
        )
