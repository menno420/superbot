from __future__ import annotations

import logging

import discord
from discord.ext import commands

from core.runtime.interaction_helpers import safe_defer
from utils import db
from utils.ui_constants import ECONOMY_COLOR
from views.base import BaseView
from views.roles._helpers import _find_role_normalized

logger = logging.getLogger("bot")


class XpRolesPanel(BaseView):
    """XP level-based role automation panel."""

    def __init__(self, ctx: commands.Context, parent: BaseView | None = None) -> None:
        super().__init__(ctx.author, timeout=300)
        self.ctx = ctx
        self.parent = parent

    async def build_embed(self) -> discord.Embed:
        all_rows = await db.get_role_thresholds(self.ctx.guild.id)
        xp_rows = [r for r in all_rows if r.get("level_required") is not None]
        embed = discord.Embed(title="⚡ XP Role Automation", color=ECONOMY_COLOR)
        if xp_rows:
            lines = []
            for r in sorted(xp_rows, key=lambda x: x["level_required"]):
                status = "✅" if r.get("xp_auto_assign") else "⏸️"
                lines.append(
                    f"{status} Level **{r['level_required']}** → **{r['role_name']}**",
                )
            embed.description = "\n".join(lines)
        else:
            embed.description = (
                "No XP threshold roles configured.\n"
                "Use **➕ Add / Edit** to assign a role at a specific XP level."
            )
        embed.set_footer(text="✅ auto-assign active  ⏸️ configured but paused")
        return embed

    async def _refresh(self) -> None:
        if self.message:
            await self.message.edit(embed=await self.build_embed(), view=self)

    @discord.ui.button(label="➕ Add / Edit", style=discord.ButtonStyle.green, row=0)
    async def add_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await interaction.response.send_modal(XpThresholdModal(self))

    @discord.ui.button(label="➖ Remove", style=discord.ButtonStyle.red, row=0)
    async def remove_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        all_rows = await db.get_role_thresholds(self.ctx.guild.id)
        xp_rows = [r for r in all_rows if r.get("level_required") is not None]
        if not xp_rows:
            await interaction.response.send_message(
                "No XP threshold roles to remove.",
                ephemeral=True,
            )
            return
        view = _XpRemoveView(self, xp_rows)
        await interaction.response.send_message(
            "Select an XP threshold role to remove:",
            view=view,
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


class XpThresholdModal(
    discord.ui.Modal,
    title="Add / Edit XP Threshold",
):  # type: ignore[call-arg]
    role_name = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Role name (must exist in server)",
        max_length=100,
    )
    level = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="XP Level required",
        placeholder="e.g. 5",
        max_length=4,
    )
    auto_assign = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Enable auto-assign? (yes/no)",
        placeholder="yes",
        required=False,
        max_length=3,
    )

    def __init__(self, parent: XpRolesPanel) -> None:
        super().__init__()
        self.parent = parent

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            lvl = int(self.level.value.strip())
            if lvl < 0:
                raise ValueError
        except ValueError:
            await interaction.response.send_message(
                "❌ Level must be a non-negative integer.",
                ephemeral=True,
            )
            return

        raw_auto = self.auto_assign.value.strip().lower()
        enabled = raw_auto not in ("no", "n", "false", "0")

        discord_role = _find_role_normalized(
            interaction.guild,
            self.role_name.value.strip(),
        )
        store_name = discord_role.name if discord_role else self.role_name.value.strip()

        try:
            await db.set_role_xp_threshold(
                interaction.guild.id,
                store_name,
                lvl,
                enabled,
            )
        except Exception as exc:
            logger.error("XP threshold save failed: %s", exc, exc_info=True)
            await interaction.response.send_message(
                f"❌ Failed to save: {exc}",
                ephemeral=True,
            )
            return

        if not await safe_defer(interaction):
            return
        await self.parent._refresh()


class _XpRemoveSelect(discord.ui.Select):
    def __init__(self, parent: XpRolesPanel, rows: list[dict]) -> None:
        self.parent = parent  # type: ignore[misc]
        options = [
            discord.SelectOption(
                label=r["role_name"],
                value=r["role_name"],
                description=f"Level {r['level_required']}",
            )
            for r in rows
        ][:25]
        super().__init__(
            placeholder="Choose an XP threshold to remove…",
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        # Clear XP columns only; preserves any days_required on the same row.
        await db.set_role_xp_threshold(
            interaction.guild.id,
            self.values[0],
            None,
            False,
        )
        await interaction.response.send_message(
            f"✅ Removed XP threshold for **{self.values[0]}**.",
            ephemeral=True,
        )
        await self.parent._refresh()  # type: ignore[attr-defined]


class _XpRemoveView(discord.ui.View):
    def __init__(self, parent: XpRolesPanel, rows: list[dict]) -> None:
        super().__init__(timeout=60)
        self.add_item(_XpRemoveSelect(parent, rows))
