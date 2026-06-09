"""Mining market panel — sell ore / buy gear (the economy loop UI).

An ephemeral child of the mining hub.  The actual money + inventory moves live
in :mod:`cogs.mining.market` (one audited implementation, shared with the
``!sell`` / ``!buy`` commands); this view is just the buttons + select that call
it.  ``cogs.mining.market`` is lazy-imported inside handlers because
``views → cogs`` at module level is a layer-rule error.
"""

from __future__ import annotations

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit
from utils import db
from utils.ui_constants import ERROR_COLOR, MINING_COLOR, SUCCESS_COLOR
from views.base import HubView


async def build_market_embed(
    user_id: int,
    guild_id: int,
    *,
    note: str = "",
) -> discord.Embed:
    """Build the market embed: what you can sell, the gear shop, your balance."""
    from cogs.mining import market

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
    embed.add_field(
        name="🛍️ Buy gear",
        value="\n".join(
            f"**{name.title()}** — {price} 🪙" for name, price in market.shop_listing()
        ),
        inline=False,
    )
    embed.set_footer(
        text=f"Balance: {balance} 🪙  •  Sell all your ore, or pick gear to buy.",
    )
    return embed


class _MiningBuySelect(discord.ui.Select):
    """Gear-shop dropdown — buys one item through the audited market path."""

    def __init__(self, user_id: int, guild_id: int, options: list) -> None:
        self._user_id = user_id
        self._guild_id = guild_id
        super().__init__(placeholder="Buy gear with coins…", options=options, row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await safe_defer(interaction):
            return
        from cogs.mining import market

        result = await market.apply_buy(self._user_id, self._guild_id, self.values[0])
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
        from cogs.mining import market

        options = [
            discord.SelectOption(label=f"{name.title()} — {price} 🪙", value=name)
            for name, price in market.shop_listing()
        ]
        self.add_item(_MiningBuySelect(author.id, guild_id, options))

    @discord.ui.button(
        label="💰 Sell All Ore",
        style=discord.ButtonStyle.success,
        row=1,
    )
    async def sell_all_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        if not await safe_defer(interaction):
            return
        from cogs.mining import market

        result = await market.apply_sell_all(self._author.id, self.guild_id)
        embed = await build_market_embed(
            self._author.id,
            self.guild_id,
            note=("✅ " if result.ok else "❌ ") + result.message,
        )
        embed.color = SUCCESS_COLOR if result.ok else ERROR_COLOR
        await safe_edit(interaction, embed=embed, view=self)

    @discord.ui.button(label="↩ Mining Hub", style=discord.ButtonStyle.secondary, row=1)
    async def back_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        # Late import keeps the module-load graph acyclic (the hub imports this).
        from views.mining.main_panel import MiningHubView

        view = MiningHubView()
        await interaction.response.edit_message(embed=view.build_embed(), view=view)
        self.stop()


__all__ = ["MiningMarketView", "build_market_embed"]
