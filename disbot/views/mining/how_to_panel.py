"""Mining How-to panel — a one-screen "how mining works" guide for new players.

Mining completion-cert punch-list #1 (``docs/planning/feature-completion/units/mining.md``):
the hub already carries an inline ``_ACTIONS_GUIDE`` routing list and per-panel blurbs, but
there was no single dedicated 📖 How-to button at the hub — the bar Fishing/Blackjack already
meet. This adds it: a static, one-screen onboarding guide reached from the main hub, returning
via the established "↩ Mining Hub" back button (mirrors ``character_hub``).

A child of the mining hub: ``HubView`` + ``SUBSYSTEM = "mining"`` (invoker lock + standard nav),
no game logic of its own. The back button swaps to a nav-carrying view (``MiningHubView``), so it
is not a dead-end terminal handler (the #1529 ``no_dead_end`` arch guard).
"""

from __future__ import annotations

import discord

from utils.ui_constants import MINING_COLOR
from views.base import HubView

_HOW_TO = (
    "New to mining? Here's the whole loop in one screen.\n\n"
    "**1. ⛏️ Mine** — open the grid and roam the underground with the movement buttons, then "
    "**Mine here** to dig the ore under you. Deeper depths hold richer ore (and need a better "
    "💡 light to see — grab a torch, then a lantern).\n"
    "**2. 🌲 Harvest** — chop wood, the basic crafting material. No tools needed.\n"
    "**3. 🧰 Gear** — equip your best tool, light, and combat gear. **Equip Best** does it in one "
    "click; matching set pieces give a bonus.\n"
    "**4. 🔨 Workshop** — turn raw resources into better gear and structures: **Craft** (build it), "
    "**Repair** (worn tools), **🔥 Forge** (gates the top gear tiers), **🛒 Market** (buy/sell).\n"
    "**5. 🧍 Character** — everything about you: **Inventory** · **Stats** · **🌳 Skills** (spend "
    "points to specialize) · **🏦 Vault** (stash loot safely, off your pack) · **🏠 Home**.\n\n"
    "**Watch your 🎒 pack** — it holds a limited number of *item types*; sell or vault what you "
    "don't need. **Watch durability** — tools wear down and break; repair or re-craft them at the "
    "Workshop. Level up by mining and harvesting to unlock deeper ladders and skill points."
)


def build_how_to_embed() -> discord.Embed:
    """The static "how mining works" onboarding guide (no per-player state)."""
    embed = discord.Embed(
        title="📖 How mining works",
        description=_HOW_TO,
        color=MINING_COLOR,
    )
    embed.set_footer(text="Only you can interact with this panel.")
    return embed


class MiningHowToView(HubView):
    """The How-to panel — a static guide with a back button to the mining hub."""

    SUBSYSTEM = "mining"

    def __init__(self, author: discord.Member | discord.User, guild_id: int) -> None:
        super().__init__(author)
        self.guild_id = guild_id

    @discord.ui.button(label="↩ Mining Hub", style=discord.ButtonStyle.secondary, row=2)
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


__all__ = ["MiningHowToView", "build_how_to_embed"]
