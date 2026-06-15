"""Mining home panel — the §7.5 Home structure UI (Slice C).

An ephemeral child of the mining hub: shows the Home's built level, the backdrop
it gives the Character card, the next build cost (coins + materials), and a 🏠
Build button.  Home is purely cosmetic — a coin/material sink with a visible
reward, never a gameplay gate.  Every build runs through
:mod:`services.mining_workflow` (one transaction per operation — Q-0071/RS02:
coin debit + material consume + level raise commit together); this view is only
the button that calls it.
"""

from __future__ import annotations

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit
from services import mining_workflow
from utils import db
from utils.mining import structures, workshop
from utils.ui_constants import ERROR_COLOR, MINING_COLOR, SUCCESS_COLOR
from views.base import HubView


async def build_home_embed(
    user_id: int,
    guild_id: int,
    *,
    note: str = "",
) -> discord.Embed:
    """The home embed: built level, the card backdrop it gives, and next cost."""
    built = await db.get_structures(user_id, guild_id)
    level = built.get(structures.HOME, 0)

    embed = discord.Embed(title="🏠 Home", color=MINING_COLOR)
    if note:
        embed.description = note
    embed.add_field(
        name="Level",
        value=(
            f"**{structures.level_name(structures.HOME, level)}** "
            f"({level}/{structures.MAX_HOME_LEVEL})"
        ),
        inline=False,
    )
    embed.add_field(
        name="What it does",
        value=(
            "A built Home gives your **Character card** a personalized "
            "backdrop — each level a richer one. Purely cosmetic."
        ),
        inline=False,
    )
    cost = structures.build_cost(structures.HOME, level)
    if cost is None:
        embed.add_field(
            name="Maxed",
            value="Your Home is at its grandest — the Grand Hall backdrop is yours.",
            inline=False,
        )
        embed.set_footer(text="↩ Mining Hub")
    else:
        nxt = structures.level_name(structures.HOME, level + 1)
        embed.add_field(
            name=f"Next: {nxt}",
            value=f"{workshop.describe_materials(cost.materials)} + **{cost.coins}** 🪙",
            inline=False,
        )
        embed.set_footer(text="🏠 Build  •  ↩ Mining Hub")
    return embed


class MiningHomeView(HubView):
    """Build/upgrade-the-home panel; a child of the mining hub."""

    SUBSYSTEM = "mining"

    def __init__(self, author: discord.Member | discord.User, guild_id: int) -> None:
        super().__init__(author)
        self.guild_id = guild_id

    @discord.ui.button(label="🏠 Build", style=discord.ButtonStyle.success, row=0)
    async def build_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        result = await mining_workflow.build_structure(
            self._author.id,
            self.guild_id,
            structures.HOME,
        )
        embed = await build_home_embed(
            self._author.id,
            self.guild_id,
            note=("✅ " if result.ok else "❌ ") + result.message,
        )
        embed.color = SUCCESS_COLOR if result.ok else ERROR_COLOR
        await safe_edit(interaction, embed=embed, view=self)

    @discord.ui.button(label="↩ Mining Hub", style=discord.ButtonStyle.secondary, row=0)
    async def back_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        # Late import keeps the module-load graph acyclic (the hub imports this).
        from views.mining.main_panel import MiningHubView, build_overview_embed

        embed = await build_overview_embed(
            self._author.id,
            self.guild_id,
            name=getattr(self._author, "display_name", None),
        )
        view = MiningHubView()
        await interaction.response.edit_message(embed=embed, view=view)
        self.stop()


__all__ = ["MiningHomeView", "build_home_embed"]
