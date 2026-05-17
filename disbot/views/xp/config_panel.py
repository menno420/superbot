"""XP configuration panel (S4.2-followup extraction).

``XpConfigView`` is the ephemeral admin view spawned by ``!xpconfig``
(and the "⚙️ Configure" button on the XP hub).  It surfaces three
fields — XP range, cooldown, level-up channel — each editable via a
modal in ``views.xp.modals``.
"""

from __future__ import annotations

import discord
from discord.ext import commands

from cogs.xp._helpers import _guild_xp_settings
from core.runtime.interaction_helpers import safe_edit
from utils import db
from utils.settings_keys import XP_ANNOUNCE_CHANNEL
from utils.ui_constants import UTILITY_COLOR


class XpConfigView(discord.ui.View):
    def __init__(self, ctx: commands.Context):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.message: discord.Message | None = None

    async def build_embed(self) -> discord.Embed:
        gid = self.ctx.guild.id
        xp_min, xp_max, cooldown = await _guild_xp_settings(gid)
        cid = await db.get_setting(gid, XP_ANNOUNCE_CHANNEL, "")
        channel_str = f"<#{cid}>" if cid else "Same channel as message"

        embed = discord.Embed(title="⚙️ XP Configuration", color=UTILITY_COLOR)
        embed.add_field(name="XP per message", value=f"{xp_min}–{xp_max}", inline=True)
        embed.add_field(name="Cooldown", value=f"{cooldown}s", inline=True)
        embed.add_field(name="Level-up channel", value=channel_str, inline=True)
        embed.set_footer(text="Click a button below to change a setting.")
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message(
                "This panel isn't for you.",
                ephemeral=True,
            )
            return False
        return True

    _run_checks = interaction_check

    async def _refresh(self, interaction: discord.Interaction):  # type: ignore[override]
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

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(view=self)
        except Exception:
            pass
