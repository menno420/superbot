"""Mining recipe browser — categorized, paginated crafting UI.

The old crafting cog's category browser (Weapons/Armour/Tools/Items pages),
modernized onto selects: a category dropdown (derived live from the item
taxonomy of each recipe's product — never a hand-kept list), a recipe
dropdown that **crafts on selection** (✅ marks affordable recipes), and
Prev/Next paging for catalog growth past Discord's 25-option cap (the
settings-hub pagination idiom).  Replaces scrolling the flat ``!buildlist``
dump; crafting itself stays the one shared
:func:`services.mining_workflow.craft` implementation.
"""

from __future__ import annotations

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit
from services import mining_workflow
from utils import db
from utils.mining import items, workshop
from utils.mining.recipes import load_recipes
from utils.ui_constants import ERROR_COLOR, MINING_COLOR, SUCCESS_COLOR
from views.base import HubView

_PAGE_SIZE = 25  # Discord's per-select option cap

_ALL = "all"
_KIND_LABELS: dict[str, str] = {
    "tool": "🛠️ Tools & Gear",
    "structure": "🏛️ Structures",
    "consumable": "🧨 Consumables",
    "resource": "⛏️ Resources",
    "treasure": "💎 Treasure",
}


def _category_of(product: str) -> str:
    return items.classify(product).value


def _recipes_for(category: str) -> list[tuple[str, dict[str, int]]]:
    """The (product, materials) rows for *category*, name-ordered."""
    rows = sorted(load_recipes().items())
    if category == _ALL:
        return rows
    return [(name, mats) for name, mats in rows if _category_of(name) == category]


def _page_count(total: int) -> int:
    return max(1, (total + _PAGE_SIZE - 1) // _PAGE_SIZE)


async def build_recipe_embed(
    user_id: int,
    guild_id: int,
    *,
    category: str = _ALL,
    page: int = 0,
    note: str = "",
) -> discord.Embed:
    """One page of recipes with per-material have/need lines."""
    inventory = await db.get_mining_inventory(str(user_id), guild_id)
    rows = _recipes_for(category)
    pages = _page_count(len(rows))
    page = max(0, min(page, pages - 1))
    window = rows[page * _PAGE_SIZE : (page + 1) * _PAGE_SIZE]

    title = "📖 Recipes"
    if category != _ALL:
        title += f" — {_KIND_LABELS.get(category, category.title())}"
    embed = discord.Embed(title=title, color=MINING_COLOR)
    if note:
        embed.description = note
    if not window:
        embed.add_field(
            name="Nothing here",
            value="No recipes in this category yet.",
            inline=False,
        )
    for name, materials in window:
        have_lines = ", ".join(
            f"{mat} {min(inventory.get(mat, 0), qty)}/{qty}"
            for mat, qty in sorted(materials.items())
        )
        craftable = all(inventory.get(mat, 0) >= qty for mat, qty in materials.items())
        embed.add_field(
            name=f"{'✅' if craftable else '▫️'} {name.title()}",
            value=have_lines,
            inline=True,
        )
    embed.set_footer(
        text=(
            f"Page {page + 1}/{pages}  •  pick a recipe below to craft it  •  "
            "!craft <item>"
        ),
    )
    return embed


class _CategorySelect(discord.ui.Select):
    def __init__(self, current: str) -> None:
        present = {_category_of(name) for name in load_recipes()}
        options = [
            discord.SelectOption(
                label="All recipes",
                value=_ALL,
                default=current == _ALL,
            ),
        ]
        options += [
            discord.SelectOption(
                label=_KIND_LABELS.get(kind, kind.title()),
                value=kind,
                default=current == kind,
            )
            for kind in sorted(present)
        ][:24]
        super().__init__(placeholder="Filter by category…", options=options, row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await safe_defer(interaction):
            return
        view: MiningRecipeBrowserView = self.view  # type: ignore[assignment]
        await view.render(interaction, category=self.values[0], page=0)


class _RecipeSelect(discord.ui.Select):
    """Selecting a recipe crafts it (the workshop-panel craft idiom)."""

    def __init__(
        self,
        rows: list[tuple[str, dict[str, int]]],
        inventory: dict[str, int],
    ) -> None:
        options = [
            discord.SelectOption(
                label=name.title()[:100],
                value=name,
                description=workshop.describe_materials(materials)[:100],
                emoji=(
                    "✅"
                    if all(
                        inventory.get(mat, 0) >= qty for mat, qty in materials.items()
                    )
                    else None
                ),
            )
            for name, materials in rows[:_PAGE_SIZE]
        ]
        super().__init__(placeholder="Craft a recipe…", options=options, row=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await safe_defer(interaction):
            return
        view: MiningRecipeBrowserView = self.view  # type: ignore[assignment]
        result = await mining_workflow.craft(
            view._author.id,
            view.guild_id,
            self.values[0],
        )
        await view.render(
            interaction,
            category=view.category,
            page=view.page,
            note=("✅ " if result.ok else "❌ ") + result.message,
            ok=result.ok,
        )


class _PageButton(discord.ui.Button):
    def __init__(self, *, delta: int, disabled: bool) -> None:
        super().__init__(
            label="◀ Prev" if delta < 0 else "Next ▶",
            style=discord.ButtonStyle.secondary,
            disabled=disabled,
            row=2,
        )
        self._delta = delta

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await safe_defer(interaction):
            return
        view: MiningRecipeBrowserView = self.view  # type: ignore[assignment]
        await view.render(
            interaction,
            category=view.category,
            page=view.page + self._delta,
        )


class MiningRecipeBrowserView(HubView):
    """Category select → recipe select (crafts) → Prev/Next; a hub child."""

    SUBSYSTEM = "mining"

    def __init__(
        self,
        author: discord.Member | discord.User,
        guild_id: int,
        *,
        category: str = _ALL,
        page: int = 0,
    ) -> None:
        super().__init__(author)
        self.guild_id = guild_id
        self.category = category
        self.page = page

    @classmethod
    async def create(
        cls,
        author: discord.Member | discord.User,
        guild_id: int,
        *,
        category: str = _ALL,
        page: int = 0,
    ) -> MiningRecipeBrowserView:
        """Async factory — options depend on inventory + the recipe set."""
        rows = _recipes_for(category)
        pages = _page_count(len(rows))
        page = max(0, min(page, pages - 1))
        view = cls(author, guild_id, category=category, page=page)
        inventory = await db.get_mining_inventory(str(author.id), guild_id)
        view.add_item(_CategorySelect(category))
        window = rows[page * _PAGE_SIZE : (page + 1) * _PAGE_SIZE]
        if window:
            view.add_item(_RecipeSelect(window, inventory))
        view.add_item(_PageButton(delta=-1, disabled=page <= 0))
        view.add_item(_PageButton(delta=1, disabled=page >= pages - 1))
        return view

    async def render(
        self,
        interaction: discord.Interaction,
        *,
        category: str,
        page: int,
        note: str = "",
        ok: bool | None = None,
    ) -> None:
        """Rebuild the panel for a new category/page/result."""
        embed = await build_recipe_embed(
            self._author.id,
            self.guild_id,
            category=category,
            page=page,
            note=note,
        )
        if ok is not None:
            embed.color = SUCCESS_COLOR if ok else ERROR_COLOR
        new_view = await MiningRecipeBrowserView.create(
            self._author,
            self.guild_id,
            category=category,
            page=page,
        )
        await safe_edit(interaction, embed=embed, view=new_view)
        self.stop()

    @discord.ui.button(label="↩ Mining Hub", style=discord.ButtonStyle.secondary, row=2)
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


__all__ = ["MiningRecipeBrowserView", "build_recipe_embed"]
