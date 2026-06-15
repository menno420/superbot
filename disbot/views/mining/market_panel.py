"""Mining market panel — sell ore + buy gear, grouped Category → Type → Variant.

An ephemeral child of the Workshop sub-hub.  The buy side uses the same
**3-layer menu doctrine** as the recipe browser (one shared
:mod:`utils.mining.taxonomy`): Weapons / Armour / Tools → Swords / Helmets … →
the tier variants (with price + stat preview), buying on the leaf.  Sell-all
lives on the root.  Every money/inventory move goes through
:mod:`services.mining_workflow` (one transaction per op — Q-0071, shared with
``!buy`` / ``!sell``); pricing/listing helpers are :mod:`utils.mining.market`.
"""

from __future__ import annotations

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit
from services import mining_workflow
from utils import db, equipment
from utils.mining import market, taxonomy
from utils.ui_constants import ERROR_COLOR, MINING_COLOR, SUCCESS_COLOR
from views.base import HubView


def _shop_names() -> list[str]:
    return [name for name, _ in market.shop_listing()]


async def build_market_embed(
    user_id: int,
    guild_id: int,
    *,
    category: str | None = None,
    base_type: str | None = None,
    note: str = "",
) -> discord.Embed:
    """The market root (sell + categories), a category's types, or a type's
    variants — mirroring the recipe browser's Category → Type → Variant.
    """
    balance = await db.get_coins(user_id, guild_id)
    names = _shop_names()
    embed = discord.Embed(title="🛒 Mining Market", color=MINING_COLOR)
    if note:
        embed.description = note

    if base_type is not None:
        # Level 2 — the tier variants, with price + stat preview + affordability.
        emoji = taxonomy.type_emoji(base_type, base_type)
        embed.title = f"🛒 {emoji} Buy {taxonomy.pluralize(base_type).title()}"
        for name in taxonomy.grouped(names).get(base_type, []):
            price = market.buy_price(name) or 0
            preview = equipment.describe_stats_compact(name)
            marker = "✅" if balance >= price else "▫️"
            value = (f"**{preview}**\n" if preview else "") + f"{price} 🪙"
            embed.add_field(name=f"{marker} {name.title()}", value=value, inline=True)
        embed.set_footer(
            text=f"Balance: {balance} 🪙  •  pick one to buy  •  ↩ Types to go back",
        )
        return embed

    if category is not None:
        # Level 1 — the types within a category (cheapest price as a hint).
        embed.title = f"🛒 {taxonomy.category_emoji(category)} {category}".strip()
        grouped = taxonomy.grouped(names)
        for base in taxonomy.types_by_category(names).get(category, []):
            variants = grouped[base]
            prices = [market.buy_price(n) or 0 for n in variants]
            embed.add_field(
                name=f"{taxonomy.type_emoji(base, variants[0])} {taxonomy.pluralize(base).title()}",
                value=f"{len(variants)} variant{'s' * (len(variants) != 1)}  •  from {min(prices)} 🪙",
                inline=True,
            )
        embed.set_footer(
            text=f"Balance: {balance} 🪙  •  pick a type  •  ↩ Categories to go back",
        )
        return embed

    # Level 0 — sell your ore, then pick a category to buy.
    inventory = await db.get_mining_inventory(str(user_id), guild_id)
    sellables = market.sellable_inventory(inventory)
    sale_total = sum(qty * price for _, qty, price in sellables)
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
    grouped = taxonomy.grouped(names)
    by_cat = taxonomy.types_by_category(names)
    for cat in taxonomy.ordered_categories(names):
        types = by_cat[cat]
        total = sum(len(grouped[b]) for b in types)
        embed.add_field(
            name=f"{taxonomy.category_emoji(cat)} {cat}".strip(),
            value=f"{len(types)} type{'s' * (len(types) != 1)} · {total} items",
            inline=True,
        )
    embed.set_footer(
        text=f"Balance: {balance} 🪙  •  sell your ore, or pick a category to buy.",
    )
    return embed


async def _render(
    interaction: discord.Interaction,
    view: MiningMarketView,
    *,
    category: str | None = None,
    base_type: str | None = None,
    note: str = "",
    ok: bool | None = None,
) -> None:
    embed = await build_market_embed(
        view._author.id,
        view.guild_id,
        category=category,
        base_type=base_type,
        note=note,
    )
    if ok is not None:
        embed.color = SUCCESS_COLOR if ok else ERROR_COLOR
    new_view = MiningMarketView(
        view._author,
        view.guild_id,
        category=category,
        base_type=base_type,
    )
    await safe_edit(interaction, embed=embed, view=new_view)
    view.stop()


class _CategorySelect(discord.ui.Select):
    """Level 0 — pick a category to buy from."""

    def __init__(self) -> None:
        names = _shop_names()
        grouped = taxonomy.grouped(names)
        by_cat = taxonomy.types_by_category(names)
        options = [
            discord.SelectOption(
                label=cat,
                value=cat,
                description=f"{len(by_cat[cat])} types · "
                f"{sum(len(grouped[b]) for b in by_cat[cat])} items"[:100],
                emoji=taxonomy.category_emoji(cat) or None,
            )
            for cat in taxonomy.ordered_categories(names)
        ]
        super().__init__(
            placeholder="Buy: pick a category…",
            options=options[:25],
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await safe_defer(interaction):
            return
        await _render(interaction, self.view, category=self.values[0])  # type: ignore[arg-type]


class _TypeSelect(discord.ui.Select):
    """Level 1 — pick a type within the chosen category."""

    def __init__(self, category: str) -> None:
        names = _shop_names()
        grouped = taxonomy.grouped(names)
        options = [
            discord.SelectOption(
                label=taxonomy.pluralize(base).title()[:100],
                value=base,
                description=f"{len(grouped[base])} variants · "
                f"from {min(market.buy_price(n) or 0 for n in grouped[base])} 🪙"[:100],
                emoji=taxonomy.type_emoji(base, grouped[base][0]),
            )
            for base in taxonomy.types_by_category(names).get(category, [])
        ]
        super().__init__(placeholder="Pick a type…", options=options[:25], row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await safe_defer(interaction):
            return
        view: MiningMarketView = self.view  # type: ignore[assignment]
        await _render(
            interaction,
            view,
            category=view.category,
            base_type=self.values[0],
        )


class _BuySelect(discord.ui.Select):
    """Level 2 — buy a tier variant through the audited market path."""

    def __init__(self, base_type: str) -> None:
        names = _shop_names()
        options = [
            discord.SelectOption(
                label=f"{name.title()} — {market.buy_price(name) or 0} 🪙"[:100],
                value=name,
                description=equipment.describe_stats_compact(name) or None,
            )
            for name in taxonomy.grouped(names).get(base_type, [])[:25]
        ]
        super().__init__(placeholder="Buy a variant…", options=options, row=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await safe_defer(interaction):
            return
        view: MiningMarketView = self.view  # type: ignore[assignment]
        result = await mining_workflow.buy(
            view._author.id,
            view.guild_id,
            self.values[0],
        )
        await _render(
            interaction,
            view,
            category=view.category,
            base_type=view.base_type,
            note=("✅ " if result.ok else "❌ ") + result.message,
            ok=result.ok,
        )


class _UpButton(discord.ui.Button):
    """Step one level up: variants → types (keep category) or types → categories."""

    def __init__(self, label: str, to: str) -> None:
        super().__init__(label=label, style=discord.ButtonStyle.secondary, row=2)
        self._to = to

    async def callback(self, interaction: discord.Interaction) -> None:
        view: MiningMarketView = self.view  # type: ignore[assignment]
        if self._to == "types":
            await _render(interaction, view, category=view.category)
        else:
            await _render(interaction, view)


class _SellAllButton(discord.ui.Button):
    """Sell every sellable resource (root level only)."""

    def __init__(self) -> None:
        super().__init__(
            label="💰 Sell All Ore",
            style=discord.ButtonStyle.success,
            row=2,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await safe_defer(interaction):
            return
        view: MiningMarketView = self.view  # type: ignore[assignment]
        result = await mining_workflow.sell_all(view._author.id, view.guild_id)
        await _render(
            interaction,
            view,
            note=("✅ " if result.ok else "❌ ") + result.message,
            ok=result.ok,
        )


class MiningMarketView(HubView):
    """Sell + buy panel; buy side drills Category → Type → Variant."""

    SUBSYSTEM = "mining"

    def __init__(
        self,
        author: discord.Member | discord.User,
        guild_id: int,
        *,
        category: str | None = None,
        base_type: str | None = None,
    ) -> None:
        super().__init__(author)
        self.guild_id = guild_id
        self.category = category
        self.base_type = base_type
        if base_type is not None:
            self.add_item(_BuySelect(base_type))
            self.add_item(_UpButton("↩ Types", "types"))
        elif category is not None:
            self.add_item(_TypeSelect(category))
            self.add_item(_UpButton("↩ Categories", "categories"))
        else:
            self.add_item(_CategorySelect())
            self.add_item(_SellAllButton())

    @discord.ui.button(label="↩ Workshop", style=discord.ButtonStyle.secondary, row=3)
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


__all__ = ["MiningMarketView", "build_market_embed"]
