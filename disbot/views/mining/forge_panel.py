"""Mining forge panel — the §7.5 Forge structure UI (Slice B).

An ephemeral child of the mining hub: shows the forge's built level, what gear
tiers it unlocks, the next build cost (coins + materials), and a 🔥 Build button.
Every build runs through :mod:`services.mining_workflow` (one transaction per
operation — Q-0071/RS02: coin debit + material consume + level raise commit
together); this view is only the button that calls it.
"""

from __future__ import annotations

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit
from services import mining_workflow
from utils import db
from utils.mining import structures, workshop
from utils.ui_constants import ERROR_COLOR, MINING_COLOR, SUCCESS_COLOR
from views.base import HubView


async def build_forge_embed(
    user_id: int,
    guild_id: int,
    *,
    note: str = "",
) -> discord.Embed:
    """The forge embed: built level, unlocked tiers, and the next build cost."""
    built = await db.get_structures(user_id, guild_id)
    level = built.get(structures.FORGE, 0)

    embed = discord.Embed(title="🔥 Forge", color=MINING_COLOR)
    if note:
        embed.description = note
    embed.add_field(
        name="Level",
        value=(
            f"**{structures.forge_level_name(level)}** "
            f"({level}/{structures.MAX_FORGE_LEVEL})"
        ),
        inline=False,
    )
    unlocked = structures.tiers_unlocked_at(level)
    unlocked_text = ", ".join(t.title() for t in unlocked) if unlocked else "—"
    embed.add_field(
        name="Unlocks (beyond free tiers)",
        value=(
            f"{unlocked_text}\n"
            "Bronze · Iron · Silver gear, tools, and structures craft "
            "without a forge."
        ),
        inline=False,
    )
    cost = structures.forge_build_cost(level)
    if cost is None:
        embed.add_field(
            name="Maxed",
            value="Your forge is at its highest level — it unlocks every gear tier.",
            inline=False,
        )
        embed.set_footer(text="↩ Mining Hub")
    else:
        nxt = structures.forge_level_name(level + 1)
        nxt_tiers = structures.tiers_unlocked_at(level + 1)
        gain = [t for t in nxt_tiers if t not in unlocked]
        gain_text = f" → unlocks **{gain[-1]}-tier** gear" if gain else ""
        embed.add_field(
            name=f"Next: {nxt}{gain_text}",
            value=f"{workshop.describe_materials(cost.materials)} + **{cost.coins}** 🪙",
            inline=False,
        )
        embed.set_footer(text="🔥 Build  •  ↩ Mining Hub")
    return embed


class MiningForgeView(HubView):
    """Build/upgrade-the-forge panel; a child of the mining hub."""

    SUBSYSTEM = "mining"

    def __init__(self, author: discord.Member | discord.User, guild_id: int) -> None:
        super().__init__(author)
        self.guild_id = guild_id

    @discord.ui.button(label="🔥 Build", style=discord.ButtonStyle.success, row=0)
    async def build_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        result = await mining_workflow.build_structure(
            self._author.id,
            self.guild_id,
            structures.FORGE,
        )
        embed = await build_forge_embed(
            self._author.id,
            self.guild_id,
            note=("✅ " if result.ok else "❌ ") + result.message,
        )
        embed.color = SUCCESS_COLOR if result.ok else ERROR_COLOR
        await safe_edit(interaction, embed=embed, view=self)

    @discord.ui.button(label="↩ Workshop", style=discord.ButtonStyle.secondary, row=0)
    async def back_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        # Back to the Workshop sub-hub that opened this panel (owner ask 2026-06-15).
        from views.mining.workshop_hub import (
            MiningWorkshopHubView,
            build_workshop_hub_embed,
        )

        await interaction.response.edit_message(
            embed=build_workshop_hub_embed(),
            view=MiningWorkshopHubView(self._author, self.guild_id),
            attachments=[],
        )
        self.stop()


__all__ = ["MiningForgeView", "build_forge_embed"]
