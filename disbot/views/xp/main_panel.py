"""XP hub panel (S4.2-followup extraction).

``_XpHubView`` is the interactive XP panel opened by ``!xpmenu`` and
referenced by ``HelpCog`` via ``XpCog.build_help_menu_view``.  Shows
the invoking user's rank card with stat-switch and admin-action buttons.
"""

from __future__ import annotations

import discord
from discord.ext import commands

from services.xp_helpers import _build_rank_embed
from views.base import HubView


class _XpHubView(HubView):
    """Interactive XP hub — shows rank card with quick admin actions."""

    def __init__(self, ctx: commands.Context):
        super().__init__(ctx.author)
        self.ctx = ctx

    async def build_embed(self) -> discord.Embed:
        embed = await _build_rank_embed(self.ctx.author, self.ctx.guild, "both")  # type: ignore[arg-type]
        embed.title = f"🏆 XP Panel — {self.ctx.author.display_name}"
        is_admin = self.ctx.author.guild_permissions.administrator  # type: ignore[union-attr]
        lines = ["Use the buttons below to switch stat views."]
        if is_admin:
            lines.append("Admin controls: ⚙️ Configure · 🎁 Give XP · 🔄 Reset XP")
        embed.set_footer(text=" · ".join(lines))
        # Show or hide admin buttons based on permissions
        for item in self.children:
            if hasattr(item, "_admin_only"):
                item.disabled = not is_admin
        return embed

    @discord.ui.button(label="📊 Both", style=discord.ButtonStyle.blurple, row=0)
    async def btn_both(self, interaction: discord.Interaction, _: discord.ui.Button):
        embed = await _build_rank_embed(self.ctx.author, self.ctx.guild, "both")  # type: ignore[arg-type]
        embed.title = f"🏆 XP Panel — {self.ctx.author.display_name}"
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🏆 XP", style=discord.ButtonStyle.blurple, row=0)
    async def btn_xp(self, interaction: discord.Interaction, _: discord.ui.Button):
        embed = await _build_rank_embed(self.ctx.author, self.ctx.guild, "xp")  # type: ignore[arg-type]
        embed.title = f"🏆 XP Panel — {self.ctx.author.display_name}"
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🪙 Coins", style=discord.ButtonStyle.blurple, row=0)
    async def btn_coins(self, interaction: discord.Interaction, _: discord.ui.Button):
        embed = await _build_rank_embed(self.ctx.author, self.ctx.guild, "coins")  # type: ignore[arg-type]
        embed.title = f"🏆 XP Panel — {self.ctx.author.display_name}"
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="⚙️ Configure", style=discord.ButtonStyle.grey, row=1)
    async def btn_config(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:  # type: ignore[union-attr]
            await interaction.response.send_message(
                "❌ Administrator permission required.",
                ephemeral=True,
            )
            return
        from views.xp.config_panel import XpConfigView

        config_view = XpConfigView(self.ctx, parent=self)
        config_view.message = self.message
        await interaction.response.edit_message(
            embed=await config_view.build_embed(),
            view=config_view,
        )

    @discord.ui.button(label="🎁 Give XP", style=discord.ButtonStyle.grey, row=1)
    async def btn_givexp(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:  # type: ignore[union-attr]
            await interaction.response.send_message(
                "❌ Administrator permission required.",
                ephemeral=True,
            )
            return
        from views.xp.modals import _GiveXpModal

        await interaction.response.send_modal(_GiveXpModal(self))

    @discord.ui.button(label="🔄 Reset XP", style=discord.ButtonStyle.danger, row=1)
    async def btn_resetxp(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:  # type: ignore[union-attr]
            await interaction.response.send_message(
                "❌ Administrator permission required.",
                ephemeral=True,
            )
            return
        from views.xp.modals import _ResetXpModal

        await interaction.response.send_modal(_ResetXpModal(self))
