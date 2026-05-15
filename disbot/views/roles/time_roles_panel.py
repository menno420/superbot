from __future__ import annotations

import discord
from discord.ext import commands
from utils import db
from utils.ui_constants import ECONOMY_COLOR, ROLE_COLOR, WARNING_COLOR
from views.base import BaseView
from views.roles._helpers import _DEFAULT_THRESHOLDS, _find_role_normalized


class TimeRolesPanel(BaseView):
    """Days-in-server threshold management panel."""

    def __init__(self, ctx: commands.Context, parent: BaseView | None = None) -> None:
        super().__init__(ctx.author, timeout=300)
        self.ctx = ctx
        self.parent = parent

    async def build_embed(self) -> discord.Embed:
        thresholds = await db.get_role_thresholds(self.ctx.guild.id)
        embed = discord.Embed(title="⏱️ Time-Based Roles", color=ROLE_COLOR)
        if thresholds:
            lines = [
                f"**{r['role_name']}** — {r['days_required']} day(s)"
                for r in thresholds
            ]
            embed.description = "\n".join(lines)
        else:
            embed.description = "No thresholds configured."
        embed.set_footer(text="Roles auto-assigned based on days in server.")
        return embed

    async def _refresh(self) -> None:
        if self.message:
            await self.message.edit(embed=await self.build_embed(), view=self)

    @discord.ui.button(label="➕ Add / Edit", style=discord.ButtonStyle.green, row=0)
    async def add_btn(
        self, interaction: discord.Interaction, _: discord.ui.Button
    ) -> None:
        await interaction.response.send_modal(TimeThresholdAddModal(self))

    @discord.ui.button(label="➖ Remove", style=discord.ButtonStyle.red, row=0)
    async def remove_btn(
        self, interaction: discord.Interaction, _: discord.ui.Button
    ) -> None:
        thresholds = await db.get_role_thresholds(self.ctx.guild.id)
        if not thresholds:
            await interaction.response.send_message(
                "No thresholds to remove.", ephemeral=True
            )
            return
        view = _TimeRemoveView(self, thresholds)
        await interaction.response.send_message(
            "Select a threshold to remove:", view=view, ephemeral=True
        )

    @discord.ui.button(label="🔄 Reset Defaults", style=discord.ButtonStyle.grey, row=0)
    async def reset_btn(
        self, interaction: discord.Interaction, _: discord.ui.Button
    ) -> None:
        for name, days in _DEFAULT_THRESHOLDS:
            await db.set_role_threshold(self.ctx.guild.id, name, days)
        await interaction.response.edit_message(
            embed=await self.build_embed(), view=self
        )

    @discord.ui.button(label="▶️ Run Now", style=discord.ButtonStyle.blurple, row=1)
    async def run_btn(
        self, interaction: discord.Interaction, _: discord.ui.Button
    ) -> None:
        await interaction.response.defer(ephemeral=True)
        cog = interaction.client.get_cog("RoleCog")  # type: ignore[attr-defined]
        if cog:
            count = await cog._assign_roles(interaction.guild)
            await interaction.followup.send(
                f"✅ Assignment complete — {count} role(s) assigned.", ephemeral=True
            )

    @discord.ui.button(label="↩ Back", style=discord.ButtonStyle.secondary, row=1)
    async def back_btn(
        self, interaction: discord.Interaction, _: discord.ui.Button
    ) -> None:
        if self.parent:
            await interaction.response.edit_message(
                embed=self.parent.build_embed(), view=self.parent
            )
        else:
            await interaction.response.edit_message(view=None)
        self.stop()


class TimeThresholdAddModal(
    discord.ui.Modal, title="Add / Edit Threshold"
):  # type: ignore[call-arg]
    role_name = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Role name (must exist in server)", max_length=100
    )
    days = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Days in server required", placeholder="0", max_length=5
    )

    def __init__(self, parent: TimeRolesPanel) -> None:
        super().__init__()
        self.parent = parent

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            d = int(self.days.value)
            if d < 0:
                raise ValueError
        except ValueError:
            await interaction.response.send_message(
                "Days must be a non-negative integer.", ephemeral=True
            )
            return
        discord_role = _find_role_normalized(
            interaction.guild, self.role_name.value.strip()
        )
        store_name = discord_role.name if discord_role else self.role_name.value.strip()
        await db.set_role_threshold(interaction.guild.id, store_name, d)
        await interaction.response.defer()
        await self.parent._refresh()


class _TimeRemoveSelect(discord.ui.Select):
    def __init__(self, parent: TimeRolesPanel, thresholds: list[dict]) -> None:
        self.parent = parent  # type: ignore[misc]
        options = [
            discord.SelectOption(
                label=r["role_name"],
                value=r["role_name"],
                description=f"{r['days_required']} day(s)",
            )
            for r in thresholds
        ][:25]
        super().__init__(placeholder="Choose a threshold to remove…", options=options)

    async def callback(self, interaction: discord.Interaction) -> None:
        await db.remove_role_threshold(interaction.guild.id, self.values[0])
        await interaction.response.send_message(
            f"✅ Removed **{self.values[0]}** from auto-assignment.", ephemeral=True
        )
        await self.parent._refresh()  # type: ignore[attr-defined]


class _TimeRemoveView(discord.ui.View):
    def __init__(self, parent: TimeRolesPanel, thresholds: list[dict]) -> None:
        super().__init__(timeout=60)
        self.add_item(_TimeRemoveSelect(parent, thresholds))
