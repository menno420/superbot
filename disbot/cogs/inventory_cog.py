from __future__ import annotations

import logging

import discord
from discord.ext import commands

from utils import db
from utils.ui_constants import ECONOMY_COLOR, INFO_COLOR, MINING_COLOR, WARNING_COLOR
from views.base import BaseView, send_panel

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
    "Mining Materials": {"emoji": "⛏️", "color": ECONOMY_COLOR},
    "Crafted Items": {"emoji": "🏗️", "color": WARNING_COLOR},
    "Tools": {"emoji": "🔧", "color": INFO_COLOR},
    "Economy Items": {"emoji": "💼", "color": ECONOMY_COLOR},
    "Other": {"emoji": "📦", "color": MINING_COLOR},
}

_RARITY_ORDER: dict[str, int] = {
    "Epic": 0,
    "Rare": 1,
    "Uncommon": 2,
    "Common": 3,
}

# Sort modes for the category detail view (punch #5). "rarity" is the default and
# matches the rarest-first grouping order; the others let a large inventory be
# re-ordered by quantity or name. Each is a stable total order (name tiebreak).
_SORT_MODES: tuple[str, ...] = ("rarity", "quantity", "name")
_SORT_LABEL: dict[str, str] = {
    "rarity": "Rarity",
    "quantity": "Quantity",
    "name": "Name",
}


def _sort_items(
    items: list[tuple[str, int, dict]],
    mode: str,
) -> list[tuple[str, int, dict]]:
    """Return *items* ordered by *mode* — a pure, total order (item key breaks ties).

    * ``rarity``   — rarest-first (the grouping default), key alpha within a tier.
    * ``quantity`` — highest quantity first, key alpha within a quantity.
    * ``name``     — item key alphabetical.
    """
    if mode == "quantity":
        return sorted(items, key=lambda x: (-x[1], x[0]))
    if mode == "name":
        return sorted(items, key=lambda x: x[0])
    return sorted(
        items,
        key=lambda x: (_RARITY_ORDER.get(x[2].get("rarity", ""), 99), x[0]),
    )


# ---------------------------------------------------------------------------
# Shared async helper — used by both the cog command and economy_cog panel
# ---------------------------------------------------------------------------
async def _build_combined_inventory(
    user_id: int,
    guild_id: int,
) -> dict[str, list[tuple[str, int, dict]]]:
    """Fetch both inventory tables and return items grouped by category.

    Returns {category_name: [(item_key, qty, meta_dict), ...]} with only
    non-empty categories and items sorted rarest-first within each category.
    """
    eco_inv: dict[str, int] = await db.get_inventory(user_id, guild_id)
    mine_inv: dict[str, int] = await db.get_mining_inventory(str(user_id), guild_id)

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
        category: str,
        items: list[tuple[str, int, dict]],
        hub: UnifiedInventoryView,
    ) -> None:
        super().__init__(author, timeout=180)
        self._category = category
        self._sort = _SORT_MODES[0]
        self._items = _sort_items(items, self._sort)
        self._hub = hub
        self._page = 0
        self._total_pages = max(1, (len(items) + self._PER_PAGE - 1) // self._PER_PAGE)
        self._rebuild_buttons()

    def _rebuild_buttons(self) -> None:
        self.clear_items()
        if self._total_pages > 1:
            prev_btn = discord.ui.Button(  # type: ignore[var-annotated]
                label="◀ Prev",
                style=discord.ButtonStyle.grey,
                row=1,
                disabled=self._page == 0,
            )
            prev_btn.callback = self._prev_page  # type: ignore[method-assign]
            self.add_item(prev_btn)

            next_btn = discord.ui.Button(  # type: ignore[var-annotated]
                label="Next ▶",
                style=discord.ButtonStyle.grey,
                row=1,
                disabled=self._page >= self._total_pages - 1,
            )
            next_btn.callback = self._next_page  # type: ignore[method-assign]
            self.add_item(next_btn)

        # Sort cycle — only worth offering when there is more than one item to order.
        if len(self._items) > 1:
            sort_btn = discord.ui.Button(  # type: ignore[var-annotated]
                label=f"🔀 Sort: {_SORT_LABEL[self._sort]}",
                style=discord.ButtonStyle.primary,
                row=1,
            )
            sort_btn.callback = self._cycle_sort  # type: ignore[method-assign]
            self.add_item(sort_btn)

        back_btn = discord.ui.Button(  # type: ignore[var-annotated]
            label="↩ Back",
            style=discord.ButtonStyle.secondary,
            row=1,
        )
        back_btn.callback = self._back_to_hub  # type: ignore[method-assign]
        self.add_item(back_btn)

    def build_embed(self) -> discord.Embed:
        cat_meta = _CATEGORY_META.get(
            self._category,
            {"emoji": "📦", "color": MINING_COLOR},
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
            text=(
                f"Page {self._page + 1}/{self._total_pages}  •  "
                f"Sorted by {_SORT_LABEL[self._sort]}  •  Click ↩ Back to return."
            ),
        )
        return embed

    async def _cycle_sort(self, interaction: discord.Interaction) -> None:
        idx = (_SORT_MODES.index(self._sort) + 1) % len(_SORT_MODES)
        self._sort = _SORT_MODES[idx]
        self._items = _sort_items(self._items, self._sort)
        self._page = 0
        self._rebuild_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

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
            embed=self._hub.build_hub_embed(),
            view=self._hub,
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
        target: discord.Member | discord.User,
        grouped: dict[str, list[tuple[str, int, dict]]],
    ) -> None:
        super().__init__(author, timeout=180)
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
            btn = discord.ui.Button(  # type: ignore[var-annotated]
                label=f"{cat_meta['emoji']} {cat} ({count})",
                style=discord.ButtonStyle.blurple,
                row=0,
            )
            btn.callback = self._make_open_callback(cat)  # type: ignore[method-assign]
            self.add_item(btn)

    def _make_open_callback(self, category: str):
        # Closure instead of functools.partial — discord.py inspects the
        # callback signature, and a partial with a kwonly arg can cause
        # the dispatcher to surface "An error occurred" on click.
        async def _callback(interaction: discord.Interaction) -> None:
            items = self._grouped.get(category, [])
            view = _CategoryView(self._author, category, items, hub=self)
            view.message = self.message
            await interaction.response.edit_message(
                embed=view.build_embed(),
                view=view,
            )

        return _callback

    def build_hub_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=f"🎒 {self.target.display_name}'s Inventory",
            color=ECONOMY_COLOR,
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
        self,
        interaction: discord.Interaction,
        *,
        category: str,
    ) -> None:
        items = self._grouped.get(category, [])
        view = _CategoryView(self._author, category, items, hub=self)
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
        self,
        ctx: commands.Context,
        member: discord.Member = None,
    ) -> None:
        """Show your (or another user's) unified inventory hub."""
        target = member or ctx.author
        grouped = await _build_combined_inventory(target.id, ctx.guild.id)
        view = UnifiedInventoryView(ctx.author, target, grouped)
        await send_panel(ctx, embed=view.build_hub_embed(), view=view)

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook (returns the inventory hub for the user)."""
        target = interaction.user
        grouped = await _build_combined_inventory(target.id, interaction.guild_id)
        view = UnifiedInventoryView(target, target, grouped)
        return view.build_hub_embed(), view


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(InventoryCog(bot))
    logger.info("InventoryCog loaded.")
