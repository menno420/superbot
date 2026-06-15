"""Workshop sub-hub — the "make, repair & trade" group of the mining hub.

Part of the Option A hub declutter (owner-directed, 2026-06-15;
``docs/planning/mining-hub-redesign-2026-06-15.md``): the main mining hub shrinks
from 16 buttons to 6, and this sub-hub absorbs the production/economy actions —
**Craft** (the consolidated Build + Craft + Recipes entry), **Repair**, **Forge**,
and **Market**.

Each button opens the existing panel **in place** (the ``main_panel`` child-opener
pattern); this view owns no game logic, it only groups. Writes still flow through
``services.mining_workflow`` from inside those panels.
"""

from __future__ import annotations

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit
from utils.ui_constants import MINING_COLOR
from views.base import HubView

_GUIDE = (
    "**🔨 Craft** — browse recipes and craft / build anything (tools, gear, structures)\n"
    "**🛠️ Repair** — the Workshop: repair worn gear, quick-craft a broken item\n"
    "**🔥 Forge** — build & use the Forge to unlock gold/diamond gear crafting\n"
    "**🛒 Market** — sell ore for coins, buy gear and supplies"
)


def build_workshop_hub_embed() -> discord.Embed:
    """The Workshop sub-hub overview (static — the panels own live state)."""
    embed = discord.Embed(
        title="🔨 Workshop — make, repair & trade",
        description=_GUIDE,
        color=MINING_COLOR,
    )
    embed.set_footer(text="Only you can interact with this panel.")
    return embed


class MiningWorkshopHubView(HubView):
    """Sub-hub grouping Craft / Repair / Forge / Market; a child of the mining hub."""

    SUBSYSTEM = "mining"

    def __init__(self, author: discord.Member | discord.User, guild_id: int) -> None:
        super().__init__(author)
        self.guild_id = guild_id

    @discord.ui.button(label="🔨 Craft", style=discord.ButtonStyle.primary, row=0)
    async def craft_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        # Craft = the recipe browser (browse + craft by category). It subsumes the
        # old Build modal — one crafting surface (owner consolidation 2026-06-15).
        from views.mining.recipe_browser import (
            MiningRecipeBrowserView,
            build_recipe_embed,
        )

        embed = await build_recipe_embed(self._author.id, self.guild_id)
        view = await MiningRecipeBrowserView.create(self._author, self.guild_id)
        await safe_edit(interaction, embed=embed, view=view, attachments=[])

    @discord.ui.button(label="🛠️ Repair", style=discord.ButtonStyle.secondary, row=0)
    async def repair_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        from views.mining.workshop_panel import (
            MiningWorkshopView,
            build_workshop_embed,
        )

        embed = await build_workshop_embed(self._author.id, self.guild_id)
        view = await MiningWorkshopView.create(self._author, self.guild_id)
        await safe_edit(interaction, embed=embed, view=view, attachments=[])

    @discord.ui.button(label="🔥 Forge", style=discord.ButtonStyle.primary, row=0)
    async def forge_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        from views.mining.forge_panel import MiningForgeView, build_forge_embed

        embed = await build_forge_embed(self._author.id, self.guild_id)
        view = MiningForgeView(self._author, self.guild_id)
        await safe_edit(interaction, embed=embed, view=view, attachments=[])

    @discord.ui.button(label="🛒 Market", style=discord.ButtonStyle.primary, row=0)
    async def market_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        from views.mining.market_panel import MiningMarketView, build_market_embed

        embed = await build_market_embed(self._author.id, self.guild_id)
        view = MiningMarketView(self._author, self.guild_id)
        await safe_edit(interaction, embed=embed, view=view, attachments=[])

    @discord.ui.button(label="↩ Mining Hub", style=discord.ButtonStyle.secondary, row=1)
    async def back_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        from views.mining.main_panel import MiningHubView, build_overview_embed

        embed = await build_overview_embed(
            self._author.id,
            self.guild_id,
            name=getattr(self._author, "display_name", None),
        )
        await interaction.response.edit_message(
            embed=embed,
            view=MiningHubView(),
            attachments=[],
        )
        self.stop()


__all__ = ["MiningWorkshopHubView", "build_workshop_hub_embed"]
