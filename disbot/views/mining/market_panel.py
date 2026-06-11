"""Mining market panel — sell ore / buy gear (the economy loop UI).

An ephemeral child of the mining hub.  The actual money + inventory moves
live in :mod:`services.mining_workflow` (one transaction per operation —
Q-0071 — shared with the ``!sell`` / ``!buy`` commands); this view is just
the buttons + select that call it.  Pure pricing/listing helpers come from
:mod:`utils.mining.market`.
"""

from __future__ import annotations

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit
from services import mining_workflow
from utils import db
from utils.mining import market
from utils.ui_constants import ERROR_COLOR, MINING_COLOR, SUCCESS_COLOR
from views.base import HubView


async def build_market_embed(
    user_id: int,
    guild_id: int,
    *,
    note: str = "",
) -> discord.Embed:
    """Build the market embed: what you can sell, the gear shop, your balance."""
    inventory = await db.get_mining_inventory(str(user_id), guild_id)
    balance = await db.get_coins(user_id, guild_id)
    sellables = market.sellable_inventory(inventory)
    sale_total = sum(qty * price for _, qty, price in sellables)

    embed = discord.Embed(title="🛒 Mining Market", color=MINING_COLOR)
    if note:
        embed.description = note
    if sellables:
        embed.add_field(
            name=f"💰 Sell resources (total {sale_total} 🪙)",
            value="\n".join(
                f"**{name.title()}** ×{qty} → {qty * price} 🪙"
                for name, qty, price in sellables
            ),
            inline=False,
        )
    else:
        embed.add_field(
            name="💰 Sell resources",
            value="Nothing to sell — go `!mine` some ore first.",
            inline=False,
        )
    # One field per shop section — the set-piece catalogue (41 items) outgrew
    # a single field's 1024-char cap, and the sections mirror the buy selects.
    for label, rows in market.shop_sections():
        embed.add_field(
            name=f"Buy: {label}",
            value="\n".join(f"**{name.title()}** — {price} 🪙" for name, price in rows),
            inline=False,
        )
    embed.set_footer(
        text=f"Balance: {balance} 🪙  •  Sell all your ore, or pick gear to buy.",
    )
    return embed


class _MiningBuySelect(discord.ui.Select):
    """Gear-shop dropdown — buys one item through the audited market path.

    One select per shop section (market.shop_sections) keeps every section
    under Discord's 25-option cap as the catalogue grows.
    """

    def __init__(
        self,
        user_id: int,
        guild_id: int,
        options: list,
        *,
        placeholder: str = "Buy gear with coins…",
        row: int = 0,
    ) -> None:
        self._user_id = user_id
        self._guild_id = guild_id
        super().__init__(placeholder=placeholder, options=options, row=row)

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await safe_defer(interaction):
            return
        result = await mining_workflow.buy(
            self._user_id,
            self._guild_id,
            self.values[0],
        )
        embed = await build_market_embed(
            self._user_id,
            self._guild_id,
            note=("✅ " if result.ok else "❌ ") + result.message,
        )
        embed.color = SUCCESS_COLOR if result.ok else ERROR_COLOR
        await safe_edit(interaction, embed=embed, view=self.view)


class MiningMarketView(HubView):
    """Sell-all + buy-gear panel; a child of the mining hub."""

    SUBSYSTEM = "mining"

    def __init__(self, author: discord.Member | discord.User, guild_id: int) -> None:
        super().__init__(author)
        self.guild_id = guild_id
        for row, (label, rows) in enumerate(market.shop_sections()[:3]):
            options = [
                discord.SelectOption(label=f"{name.title()} — {price} 🪙", value=name)
                for name, price in rows
            ]
            self.add_item(
                _MiningBuySelect(
                    author.id,
                    guild_id,
                    options[:25],
                    placeholder=f"Buy: {label}…",
                    row=row,
                ),
            )

    @discord.ui.button(
        label="💰 Sell All Ore",
        style=discord.ButtonStyle.success,
        row=3,
    )
    async def sell_all_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        if not await safe_defer(interaction):
            return
        result = await mining_workflow.sell_all(self._author.id, self.guild_id)
        embed = await build_market_embed(
            self._author.id,
            self.guild_id,
            note=("✅ " if result.ok else "❌ ") + result.message,
        )
        embed.color = SUCCESS_COLOR if result.ok else ERROR_COLOR
        await safe_edit(interaction, embed=embed, view=self)

    @discord.ui.button(label="↩ Mining Hub", style=discord.ButtonStyle.secondary, row=3)
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


__all__ = ["MiningMarketView", "build_market_embed"]
