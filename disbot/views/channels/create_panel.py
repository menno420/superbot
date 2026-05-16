"""Channel-creation sub-panel + its supporting name / category / modal widgets.

A `_CreateSubView` opens from the main hub's "Create Channel" button.
The view holds a name selection + a category selection, then creates
the channel on the green button.  ``_CustomNameModal`` allows free-form
naming; ``_NameSelect`` and ``_CategorySelect`` are the preset pickers.
"""

from __future__ import annotations

import asyncio
import logging

import discord
from discord.ext import commands

from core.runtime.interaction_helpers import safe_defer
from utils.channels import get_or_create_category, safe_channel_name
from utils.ui_constants import SUCCESS_COLOR
from views.base import BaseView
from views.channels._helpers import _CATEGORY_PRESETS, _NAME_PRESETS

logger = logging.getLogger("bot")


class _CreateSubView(BaseView):
    """Channel-creation sub-panel — mirrors the old _ChannelCreatorView."""

    def __init__(
        self,
        ctx: commands.Context,
        *,
        manager_message: discord.Message | None,
    ):
        super().__init__(ctx.author, timeout=120)
        self.ctx = ctx
        self.manager_message = manager_message
        self.chosen_name: str | None = None
        self.chosen_cat: str | None = None

        # Category options: existing guild categories first, then presets
        existing_cats = [c.name for c in ctx.guild.categories]
        cat_options = [
            discord.SelectOption(label=c, description="Existing category")
            for c in existing_cats[:15]
        ]
        for p in _CATEGORY_PRESETS:
            if p not in existing_cats and len(cat_options) < 24:
                cat_options.append(
                    discord.SelectOption(label=p, description="New category"),
                )
        if not cat_options:
            cat_options = [discord.SelectOption(label=p) for p in _CATEGORY_PRESETS]

        self.name_select = _NameSelect(_NAME_PRESETS, self)
        self.cat_select = _CategorySelect(cat_options, self)
        self.add_item(self.name_select)
        self.add_item(self.cat_select)

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item,
    ) -> None:
        logger.error("CreateSubView error on %s: %s", item, error, exc_info=True)
        msg = f"❌ {type(error).__name__}: {error}"
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(msg, ephemeral=True)
            else:
                await interaction.followup.send(msg, ephemeral=True)
        except Exception:
            pass

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="➕ Create Channel",
            description=(
                "Use the menus below to pick a name and category.\n"
                "Click **Custom Name** to type your own name."
            ),
            color=SUCCESS_COLOR,
        )
        embed.add_field(
            name="Selected name",
            value=f"`{self.chosen_name}`" if self.chosen_name else "*(none)*",
            inline=True,
        )
        embed.add_field(
            name="Selected category",
            value=f"`{self.chosen_cat}`" if self.chosen_cat else "*(none)*",
            inline=True,
        )
        return embed

    @discord.ui.button(
        label="Custom Name",
        style=discord.ButtonStyle.grey,
        emoji="✏️",
        row=2,
    )
    async def custom_name_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        await interaction.response.send_modal(_CustomNameModal(self))

    @discord.ui.button(
        label="Create Channel",
        style=discord.ButtonStyle.green,
        emoji="✅",
        row=2,
    )
    async def create_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not self.chosen_name:
            await interaction.response.send_message(
                "Please select or enter a channel name first.",
                ephemeral=True,
            )
            return

        if not await safe_defer(interaction, ephemeral=True):
            return

        guild = interaction.guild
        safe = await safe_channel_name(guild, self.chosen_name)
        category = None
        if self.chosen_cat:
            try:
                category = await get_or_create_category(guild, self.chosen_cat)
            except discord.Forbidden:
                await interaction.followup.send(
                    "❌ I don't have permission to create categories.",
                    ephemeral=True,
                )
                return
            except discord.HTTPException as exc:
                await interaction.followup.send(
                    f"❌ Failed to create category: {exc}",
                    ephemeral=True,
                )
                return

        try:
            ch = await guild.create_text_channel(safe, category=category)
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ I don't have permission to create channels.",
                ephemeral=True,
            )
            return
        except discord.HTTPException as exc:
            await interaction.followup.send(
                f"❌ Failed to create channel: {exc}",
                ephemeral=True,
            )
            return

        for item in self.children:
            item.disabled = True

        suffix = (
            f' (renamed from "{self.chosen_name}")' if safe != self.chosen_name else ""
        )
        embed = discord.Embed(
            title="✅ Channel Created",
            description=(
                f"{ch.mention} created"
                + (f" in **{self.chosen_cat}**" if self.chosen_cat else "")
                + suffix
                + "\n\nReturning to the management panel…"
            ),
            color=SUCCESS_COLOR,
        )
        try:
            await self.manager_message.edit(embed=embed, view=self)
        except Exception:
            await interaction.followup.send(
                f"✅ Channel {ch.mention} created!"
                + (f" in **{self.chosen_cat}**" if self.chosen_cat else ""),
                ephemeral=True,
            )

        self.stop()

        # Brief visual pause before restoring the manager panel
        await asyncio.sleep(2)
        from views.channels.main_panel import _ChannelManagerView

        manager = _ChannelManagerView(self.ctx)
        manager.message = self.manager_message
        try:
            await self.manager_message.edit(embed=manager.build_embed(), view=manager)
        except Exception:
            pass

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, emoji="❌", row=2)
    async def cancel_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        from views.channels.main_panel import _ChannelManagerView

        manager = _ChannelManagerView(self.ctx)
        manager.message = self.manager_message
        await interaction.response.edit_message(
            embed=manager.build_embed(),
            view=manager,
        )
        self.stop()

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


class _NameSelect(discord.ui.Select):
    """Name preset picker used by _CreateSubView."""

    def __init__(self, presets: list[str], view):
        options = [discord.SelectOption(label=p, value=p) for p in presets]
        super().__init__(
            placeholder="Pick a channel name…",
            min_values=1,
            max_values=1,
            options=options,
            row=0,
        )
        self._parent = view

    async def callback(self, interaction: discord.Interaction):
        self._parent.chosen_name = self.values[0]  # type: ignore[attr-defined]
        try:
            await interaction.response.edit_message(
                embed=self._parent.build_embed(),  # type: ignore[attr-defined]
                view=self._parent,  # type: ignore[attr-defined, arg-type]
            )
        except discord.HTTPException:
            await safe_defer(interaction)


class _CategorySelect(discord.ui.Select):
    """Category picker used by _CreateSubView."""

    def __init__(self, options: list[discord.SelectOption], view):
        super().__init__(
            placeholder="Pick a category…",
            min_values=1,
            max_values=1,
            options=options,
            row=1,
        )
        self._parent = view

    async def callback(self, interaction: discord.Interaction):
        self._parent.chosen_cat = self.values[0]  # type: ignore[attr-defined]
        try:
            await interaction.response.edit_message(
                embed=self._parent.build_embed(),  # type: ignore[attr-defined]
                view=self._parent,  # type: ignore[attr-defined, arg-type]
            )
        except discord.HTTPException:
            await safe_defer(interaction)


class _CustomNameModal(discord.ui.Modal, title="Custom Channel Name"):  # type: ignore[call-arg]
    channel_name = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Channel name",
        placeholder="e.g. my-channel",
        max_length=100,
    )

    def __init__(self, view: _CreateSubView):
        super().__init__()
        self._view = view

    async def on_submit(self, interaction: discord.Interaction):
        name = self.channel_name.value.strip().lower().replace(" ", "-")
        self._view.chosen_name = name
        if not await safe_defer(interaction):
            return
        if self._view.manager_message:
            await self._view.manager_message.edit(
                embed=self._view.build_embed(),
                view=self._view,
            )
