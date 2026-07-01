"""XP configuration panel (S4.2-followup extraction).

``XpConfigView`` is the ephemeral admin view spawned by ``!xpconfig``
(and the "⚙️ Configure" button on the XP hub).  It surfaces three
fields — XP range, cooldown, level-up channel — each editable via a
modal in ``views.xp.modals``.
"""

from __future__ import annotations

import discord
from discord.ext import commands

from core.runtime.config_arbitration import get_xp_announce_channel
from core.runtime.interaction_helpers import safe_edit
from services.xp_helpers import _guild_xp_settings
from utils.ui_constants import UTILITY_COLOR
from views.base import BaseView
from views.navigation import attach_back_button


class XpConfigView(BaseView):
    def __init__(
        self,
        ctx: commands.Context,
        parent: BaseView | None = None,
    ) -> None:
        super().__init__(ctx.author, timeout=300)
        self.ctx = ctx
        self.parent = parent

        if parent is not None:

            async def _build_parent(
                _interaction: discord.Interaction,
            ) -> tuple[discord.Embed, discord.ui.View]:
                # Parent (XP hub) has an async build_embed.
                embed = await parent.build_embed()  # type: ignore[attr-defined]
                return embed, parent

            attach_back_button(
                self,
                label="↩ Back",
                custom_id="xp:config:back",
                parent_builder=_build_parent,
                row=1,
            )

    async def build_embed(self) -> discord.Embed:
        gid = self.ctx.guild.id
        xp_min, xp_max, cooldown = await _guild_xp_settings(gid)
        # Binding-first read (the xp_announce_channel scalar was retired
        # in P0-3; arbitration resolves xp.announce_channel, legacy KV
        # remains the rollback fallback).
        ann = await get_xp_announce_channel(gid)
        cid = ann.value or ""
        channel_str = f"<#{cid}>" if cid else "Same channel as message"

        embed = discord.Embed(title="⚙️ XP Configuration", color=UTILITY_COLOR)
        embed.add_field(name="XP per message", value=f"{xp_min}–{xp_max}", inline=True)
        embed.add_field(name="Cooldown", value=f"{cooldown}s", inline=True)
        embed.add_field(name="Level-up channel", value=channel_str, inline=True)
        embed.set_footer(text="Click a button below to change a setting.")
        return embed

    async def _rerender(self, interaction: discord.Interaction):  # type: ignore[override]
        await safe_edit(interaction, embed=await self.build_embed(), view=self)

    @discord.ui.button(label="XP Range", style=discord.ButtonStyle.blurple, row=0)
    async def btn_xp_range(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        from views.xp.modals import _XpRangeModal

        await interaction.response.send_modal(_XpRangeModal(self))

    @discord.ui.button(label="Cooldown", style=discord.ButtonStyle.blurple, row=0)
    async def btn_cooldown(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        from views.xp.modals import _XpCooldownModal

        await interaction.response.send_modal(_XpCooldownModal(self))

    @discord.ui.button(
        label="Level-up Channel",
        style=discord.ButtonStyle.blurple,
        row=0,
    )
    async def btn_channel(self, interaction: discord.Interaction, _: discord.ui.Button):
        from views.xp.modals import _XpChannelModal

        await interaction.response.send_modal(_XpChannelModal(self))

    @discord.ui.button(
        label="📥 Import from another bot",
        style=discord.ButtonStyle.grey,
        row=1,
    )
    async def btn_import(self, interaction: discord.Interaction, _: discord.ui.Button):
        """Drill into the XP-import setup (pick channel + bot → scan → preview)."""
        from views.xp.import_panel import XpImportSetupView

        view = XpImportSetupView(self.ctx)
        await safe_edit(interaction, embed=view.build_embed(), view=view)
        view.message = self.message
