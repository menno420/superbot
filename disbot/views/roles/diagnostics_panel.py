from __future__ import annotations

import discord
from discord.ext import commands

from core.runtime.interaction_helpers import safe_defer
from utils import db
from utils.settings_keys import SKIP_ROLES
from utils.ui_constants import WARNING_COLOR
from views.base import BaseView


class DiagnosticsPanel(BaseView):
    """Role system diagnostics — counts, skip_roles, member cache status."""

    def __init__(self, ctx: commands.Context, parent: BaseView | None = None) -> None:
        super().__init__(ctx.author, timeout=300)
        self.ctx = ctx
        self.parent = parent

    async def build_embed(self) -> discord.Embed:
        guild = self.ctx.guild
        thresholds = await db.get_role_thresholds(guild.id)
        xp_rows = [r for r in thresholds if r.get("level_required") is not None]
        reaction_rows = await db.get_all_reaction_roles(guild.id)
        skip_roles = await db.get_setting(guild.id, SKIP_ROLES, "Admin")

        embed = discord.Embed(title="🔧 Role System Diagnostics", color=WARNING_COLOR)
        embed.add_field(name="Time Thresholds", value=str(len(thresholds)), inline=True)
        embed.add_field(name="XP Thresholds", value=str(len(xp_rows)), inline=True)
        embed.add_field(
            name="Reaction Roles",
            value=str(len(reaction_rows)),
            inline=True,
        )
        embed.add_field(name="Skip Roles", value=skip_roles or "*(none)*", inline=False)
        embed.add_field(
            name="Members Cached",
            value=str(len([m for m in guild.members if not m.bot])),
            inline=True,
        )
        embed.add_field(
            name="Total Roles",
            value=str(len(guild.roles) - 1),
            inline=True,
        )
        return embed

    @discord.ui.button(
        label="🔄 Refresh Members",
        style=discord.ButtonStyle.blurple,
        row=0,
    )
    async def refresh_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not await safe_defer(interaction, ephemeral=True):
            return
        await interaction.guild.chunk()
        await interaction.followup.send("✅ Member list refreshed.", ephemeral=True)

    @discord.ui.button(label="▶️ Run Assignment", style=discord.ButtonStyle.grey, row=0)
    async def run_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not await safe_defer(interaction, ephemeral=True):
            return
        cog = interaction.client.get_cog("RoleCog")  # type: ignore[attr-defined]
        count = await cog._assign_roles(interaction.guild) if cog else 0
        await interaction.followup.send(
            f"✅ Assignment complete — {count} role(s) assigned.",
            ephemeral=True,
        )

    @discord.ui.button(label="↩ Back", style=discord.ButtonStyle.secondary, row=1)
    async def back_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if self.parent:
            await interaction.response.edit_message(
                embed=self.parent.build_embed(),
                view=self.parent,
            )
        else:
            await interaction.response.edit_message(view=None)
        self.stop()
