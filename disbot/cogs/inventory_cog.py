from __future__ import annotations

import functools
import logging

import discord
from discord.ext import commands

from utils import db
from views.base import BaseView

logger = logging.getLogger("bot")

# ---------------------------------------------------------------------------
# Item catalogue — static metadata, never written to DB
# ---------------------------------------------------------------------------
ITEM_CATALOGUE: dict[str, dict] = {
    # Mining Materials (mining_inventory table)
    "stone": {
        "category": "Mining Materials",
        "emoji": "🪨",
        "type": "Ore",
        "rarity": "Common",
    },
    "iron": {
        "category": "Mining Materials",
        "emoji": "⚙️",
        "type": "Ore",
        "rarity": "Uncommon",
    },
    "gold": {
        "category": "Mining Materials",
        "emoji": "🥇",
        "type": "Ore",
        "rarity": "Rare",
    },
    "diamond": {
        "category": "Mining Materials",
        "emoji": "💎",
        "type": "Gem",
        "rarity": "Epic",
    },
    "wood": {
        "category": "Mining Materials",
        "emoji": "🪵",
        "type": "Resource",
        "rarity": "Common",
    },
    # Crafted/built structures (mining_inventory after !build)
    "stone hut": {
        "category": "Crafted Items",
        "emoji": "🏚️",
        "type": "Structure",
        "rarity": "Common",
    },
    "wooden house": {
        "category": "Crafted Items",
        "emoji": "🏠",
        "type": "Structure",
        "rarity": "Uncommon",
    },
    "gold statue": {
        "category": "Crafted Items",
        "emoji": "🗿",
        "type": "Structure",
        "rarity": "Rare",
    },
    "diamond throne": {
        "category": "Crafted Items",
        "emoji": "💺",
        "type": "Structure",
        "rarity": "Epic",
    },
    # Tools (mining_inventory + economy inventory)
    "iron pickaxe": {
        "category": "Tools",
        "emoji": "⛏️",
        "type": "Tool",
        "rarity": "Uncommon",
    },
    "axe": {"category": "Tools", "emoji": "🪓", "type": "Tool", "rarity": "Uncommon"},
    "toolkit": {
        "category": "Tools",
        "emoji": "🔧",
        "type": "Job Unlock",
        "rarity": "Uncommon",
    },
    # Economy items (inventory table, guild-scoped)
    "car": {
        "category": "Economy Items",
        "emoji": "🚗",
        "type": "Job Unlock",
        "rarity": "Rare",
    },
    "suit": {
        "category": "Economy Items",
        "emoji": "👔",
        "type": "Job Unlock",
        "rarity": "Rare",
    },
}

_CATEGORY_ORDER: tuple[str, ...] = (
    "Mining Materials",
    "Crafted Items",
    "Tools",
    "Economy Items",
)

_CATEGORY_META: dict[str, dict] = {
    "Mining Materials": {"emoji": "⛏️", "color": discord.Color.dark_gold()},
    "Crafted Items": {"emoji": "🏗️", "color": discord.Color.orange()},
    "Tools": {"emoji": "🔧", "color": discord.Color.blurple()},
    "Economy Items": {"emoji": "💼", "color": discord.Color.gold()},
    "Other": {"emoji": "📦", "color": discord.Color.dark_grey()},
}

_RARITY_ORDER: dict[str, int] = {
    "Epic": 0,
    "Rare": 1,
    "Uncommon": 2,
    "Common": 3,
}


# ---------------------------------------------------------------------------
# Shared async helper — used by both the cog command and economy_cog panel
# ---------------------------------------------------------------------------
async def _build_combined_inventory(
    user_id: int, guild_id: int
) -> dict[str, list[tuple[str, int, dict]]]:
    """Fetch both inventory tables and return items grouped by category.

    Returns {category_name: [(item_key, qty, meta_dict), ...]} with only
    non-empty categories and items sorted rarest-first within each category.
    """
    eco_inv: dict[str, int] = await db.get_inventory(user_id, guild_id)
    mine_inv: dict[str, int] = await db.get_mining_inventory(str(user_id))

    combined: dict[str, int] = {}
    for k, v in mine_inv.items():
        combined[k.lower()] = v
    for k, v in eco_inv.items():
        key = k.lower()
        combined[key] = combined.get(key, 0) + v

    grouped: dict[str, list[tuple[str, int, dict]]] = {}
    for item_key, qty in combined.items():
        if qty <= 0:
            continue
        meta = ITEM_CATALOGUE.get(item_key, {})
        cat = meta.get("category", "Other")
        grouped.setdefault(cat, []).append((item_key, qty, meta))

    for cat_items in grouped.values():
        cat_items.sort(key=lambda x: _RARITY_ORDER.get(x[2].get("rarity", ""), 99))

    return grouped


# ---------------------------------------------------------------------------
# Category detail view
# ---------------------------------------------------------------------------
class _CategoryView(BaseView):
    """Paginated item list for a single inventory category."""

    _PER_PAGE = 8

    def __init__(
        self,
        author: discord.Member | discord.User,
        ctx: commands.Context,
        category: str,
        items: list[tuple[str, int, dict]],
        hub: UnifiedInventoryView,
    ) -> None:
        super().__init__(author, timeout=180)
        self._ctx = ctx
        self._category = category
        self._items = items
        self._hub = hub
        self._page = 0
        self._total_pages = max(1, (len(items) + self._PER_PAGE - 1) // self._PER_PAGE)
        self._rebuild_buttons()

    def _rebuild_buttons(self) -> None:
        self.clear_items()
        if self._total_pages > 1:
            prev_btn = discord.ui.Button(
                label="◀ Prev",
                style=discord.ButtonStyle.grey,
                row=1,
                disabled=self._page == 0,
            )
            prev_btn.callback = self._prev_page
            self.add_item(prev_btn)

            next_btn = discord.ui.Button(
                label="Next ▶",
                style=discord.ButtonStyle.grey,
                row=1,
                disabled=self._page >= self._total_pages - 1,
            )
            next_btn.callback = self._next_page
            self.add_item(next_btn)

        back_btn = discord.ui.Button(
            label="↩ Back",
            style=discord.ButtonStyle.secondary,
            row=1,
        )
        back_btn.callback = self._back_to_hub
        self.add_item(back_btn)

    def build_embed(self) -> discord.Embed:
        cat_meta = _CATEGORY_META.get(
            self._category, {"emoji": "📦", "color": discord.Color.dark_grey()}
        )
        embed = discord.Embed(
            title=f"{cat_meta['emoji']} {self._category}",
            color=cat_meta["color"],
        )
        embed.set_author(
            name=f"{self._hub.target.display_name}'s Inventory",
            icon_url=self._hub.target.display_avatar.url,
        )

        start = self._page * self._PER_PAGE
        page_items = self._items[start : start + self._PER_PAGE]

        lines = []
        for item_key, qty, meta in page_items:
            emoji = meta.get("emoji", "📦")
            rarity = meta.get("rarity", "Unknown")
            itype = meta.get("type", "Item")
            display_name = item_key.replace("_", " ").title()
            lines.append(f"{emoji} **{display_name}** × {qty}  `{rarity}` · {itype}")

        embed.description = "\n".join(lines) if lines else "Nothing here."
        embed.set_footer(
            text=f"Page {self._page + 1}/{self._total_pages}  •  Click ↩ Back to return."
        )
        return embed

    async def _prev_page(self, interaction: discord.Interaction) -> None:
        self._page = max(0, self._page - 1)
        self._rebuild_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _next_page(self, interaction: discord.Interaction) -> None:
        self._page = min(self._total_pages - 1, self._page + 1)
        self._rebuild_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _back_to_hub(self, interaction: discord.Interaction) -> None:
        self._hub.message = self.message
        await interaction.response.edit_message(
            embed=self._hub.build_hub_embed(), view=self._hub
        )
        self.stop()


# ---------------------------------------------------------------------------
# Unified inventory hub view
# ---------------------------------------------------------------------------
class UnifiedInventoryView(BaseView):
    """Main inventory hub — one button per non-empty category."""

    def __init__(
        self,
        author: discord.Member | discord.User,
        ctx: commands.Context,
        target: discord.Member | discord.User,
        grouped: dict[str, list[tuple[str, int, dict]]],
    ) -> None:
        super().__init__(author, timeout=180)
        self.ctx = ctx
        self.target = target
        self._grouped = grouped
        self._add_category_buttons()

    def _add_category_buttons(self) -> None:
        self.clear_items()
        ordered = [c for c in _CATEGORY_ORDER if c in self._grouped]
        if "Other" in self._grouped:
            ordered.append("Other")

        for cat in ordered:
            cat_meta = _CATEGORY_META.get(cat, {"emoji": "📦"})
            count = len(self._grouped[cat])
            btn = discord.ui.Button(
                label=f"{cat_meta['emoji']} {cat} ({count})",
                style=discord.ButtonStyle.blurple,
                row=0,
            )
            btn.callback = functools.partial(self._open_category, category=cat)
            self.add_item(btn)

    def build_hub_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=f"🎒 {self.target.display_name}'s Inventory",
            color=discord.Color.blurple(),
        )
        embed.set_thumbnail(url=self.target.display_avatar.url)

        if not self._grouped:
            embed.description = (
                "No items yet — go mining with `!mine` or visit `!shop`!"
            )
        else:
            lines = []
            ordered = [c for c in _CATEGORY_ORDER if c in self._grouped]
            if "Other" in self._grouped:
                ordered.append("Other")
            for cat in ordered:
                cat_meta = _CATEGORY_META.get(cat, {"emoji": "📦"})
                items = self._grouped[cat]
                preview_parts = [
                    f"{m.get('emoji', '📦')} {n.replace('_', ' ').title()}"
                    for n, _, m in items[:3]
                ]
                preview = ", ".join(preview_parts)
                if len(items) > 3:
                    preview += f" +{len(items) - 3} more"
                lines.append(f"{cat_meta['emoji']} **{cat}** — {preview}")
            embed.description = "\n".join(lines)

        embed.set_footer(text="Select a category below to view details.")
        return embed

    async def _open_category(
        self, interaction: discord.Interaction, *, category: str
    ) -> None:
        items = self._grouped.get(category, [])
        view = _CategoryView(self.ctx.author, self.ctx, category, items, hub=self)
        view.message = self.message
        await interaction.response.edit_message(embed=view.build_embed(), view=view)


# ---------------------------------------------------------------------------
# Cog
# ---------------------------------------------------------------------------
class InventoryCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="inventory", aliases=["inv"])
    async def inventory(
        self, ctx: commands.Context, member: discord.Member = None
    ) -> None:
        """Show your (or another user's) unified inventory hub."""
        target = member or ctx.author
        grouped = await _build_combined_inventory(target.id, ctx.guild.id)
        view = UnifiedInventoryView(ctx.author, ctx, target, grouped)
        msg = await ctx.send(embed=view.build_hub_embed(), view=view)
        view.message = msg


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(InventoryCog(bot))
    logger.info("InventoryCog loaded.")
