"""Mining recipe browser — Category → Type → Variant drill-down.

Owner UX (live session 2026-06-15): the flat recipe list, then the full type
list, were both too crowded. Three small levels instead:

* **Category** — Weapons / Armour / Tools / Structures / Items (derived from the
  item's equip slot + kind, never a hand-kept list).
* **Type** — Swords / Pickaxes / Helmets … (the product's last word).
* **Variant** — wood → diamond, which crafts on select.

Each level fits one 25-option select, so there is no pagination. Crafting itself
stays the one shared :func:`services.mining_workflow.craft`.
"""

from __future__ import annotations

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit
from services import mining_workflow
from utils import db, equipment
from utils.mining import structures, taxonomy, workshop
from utils.mining.recipes import load_recipes
from utils.ui_constants import ERROR_COLOR, MINING_COLOR, SUCCESS_COLOR
from views.base import HubView

# The 3-layer grouping (Category → Type → Variant) lives in
# ``utils.mining.taxonomy`` — the one source shared with the market. These thin
# aliases / wrappers keep this module's call sites unchanged.
_pluralize = taxonomy.pluralize
_type_emoji = taxonomy.type_emoji
_CATEGORY_EMOJI = taxonomy.CATEGORY_EMOJI
_base_type = taxonomy.base_type
_category_of = taxonomy.category_of


def _grouped() -> dict[str, list[tuple[str, dict[str, int]]]]:
    """``base_type → [(name, materials)]``, variants rarity-ordered (taxonomy)."""
    recipes = load_recipes()
    return {
        base: [(n, recipes[n]) for n in names]
        for base, names in taxonomy.grouped(recipes).items()
    }


def _types_by_category() -> dict[str, list[str]]:
    return taxonomy.types_by_category(load_recipes())


def _ordered_categories() -> list[str]:
    return taxonomy.ordered_categories(load_recipes())


def _affordable(materials: dict[str, int], inventory: dict[str, int]) -> bool:
    return all(inventory.get(mat, 0) >= qty for mat, qty in materials.items())


def _variant_desc(name: str, materials: dict[str, int]) -> str:
    """A variant's select-description: its stat bonus, then its material cost."""
    preview = equipment.describe_stats_compact(name)
    mats = workshop.describe_materials(materials)
    return (f"{preview} · {mats}" if preview else mats)[:100]


async def build_recipe_embed(
    user_id: int,
    guild_id: int,
    *,
    category: str | None = None,
    base_type: str | None = None,
    note: str = "",
) -> discord.Embed:
    """Categories (top), one category's types, or one type's variants."""
    inventory = await db.get_mining_inventory(str(user_id), guild_id)
    forge_level = (await db.get_structures(user_id, guild_id)).get(structures.FORGE, 0)
    groups = _grouped()

    embed = discord.Embed(title="📖 Recipes", color=MINING_COLOR)
    if note:
        embed.description = note

    if base_type is not None:
        # Level 2 — variants of the chosen type, with have/need per material.
        variants = groups.get(base_type, [])
        emoji = _type_emoji(base_type, variants[0][0] if variants else base_type)
        embed.title = f"📖 {emoji} {_pluralize(base_type).title()}"
        embed.set_footer(text="Pick a variant to craft  •  ↩ Types to go back")
        if not variants:
            embed.add_field(
                name="Nothing here",
                value="No recipes of this type.",
                inline=False,
            )
        for name, materials in variants:
            have_lines = ", ".join(
                f"{mat} {min(inventory.get(mat, 0), qty)}/{qty}"
                for mat, qty in sorted(materials.items())
            )
            if not structures.meets_forge_requirement(name, forge_level):
                marker = "🔒"
                need = structures.forge_level_name(
                    structures.forge_level_required(name),
                )
                have_lines += f"\n🔥 needs **{need}** (`!forge`)"
            else:
                marker = "✅" if _affordable(materials, inventory) else "▫️"
            preview = equipment.describe_stats_compact(name)
            value = (f"**{preview}**\n" if preview else "") + have_lines
            embed.add_field(
                name=f"{marker} {name.title()}",
                value=value,
                inline=True,
            )
        return embed

    if category is not None:
        # Level 1 — the types within a category, with a craftable-now count.
        embed.title = f"📖 {_CATEGORY_EMOJI.get(category, '')} {category}".strip()
        embed.set_footer(text="Pick a type  •  ↩ Categories to go back")
        for base in _types_by_category().get(category, []):
            variants = groups[base]
            craftable = sum(1 for _, m in variants if _affordable(m, inventory))
            value = f"{len(variants)} variant{'s' * (len(variants) != 1)}"
            if craftable:
                value += f"  •  ✅ {craftable} craftable now"
            embed.add_field(
                name=f"{_type_emoji(base, variants[0][0])} {_pluralize(base).title()}",
                value=value,
                inline=True,
            )
        return embed

    # Level 0 — the categories.
    embed.set_footer(text="Pick a category to browse.")
    by_cat = _types_by_category()
    for cat in _ordered_categories():
        types = by_cat[cat]
        total = sum(len(groups[b]) for b in types)
        embed.add_field(
            name=f"{_CATEGORY_EMOJI.get(cat, '')} {cat}".strip(),
            value=f"{len(types)} type{'s' * (len(types) != 1)} · {total} items",
            inline=True,
        )
    return embed


class _CategorySelect(discord.ui.Select):
    """Level 0 — pick a category (Weapons / Armour / Tools / …)."""

    def __init__(self) -> None:
        by_cat = _types_by_category()
        groups = _grouped()
        options = []
        for cat in _ordered_categories():
            types = by_cat[cat]
            total = sum(len(groups[b]) for b in types)
            options.append(
                discord.SelectOption(
                    label=cat,
                    value=cat,
                    description=f"{len(types)} types · {total} items"[:100],
                    emoji=_CATEGORY_EMOJI.get(cat),
                ),
            )
        super().__init__(placeholder="Pick a category…", options=options[:25], row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await safe_defer(interaction):
            return
        view: MiningRecipeBrowserView = self.view  # type: ignore[assignment]
        await view.render(interaction, category=self.values[0])


class _TypeSelect(discord.ui.Select):
    """Level 1 — pick a type within a category (Swords / Pickaxes / …)."""

    def __init__(self, category: str, inventory: dict[str, int]) -> None:
        groups = _grouped()
        options = []
        for base in _types_by_category().get(category, []):
            variants = groups[base]
            craftable = sum(1 for _, m in variants if _affordable(m, inventory))
            desc = f"{len(variants)} variant{'s' * (len(variants) != 1)}"
            if craftable:
                desc += f" · {craftable} craftable now"
            options.append(
                discord.SelectOption(
                    label=_pluralize(base).title()[:100],
                    value=base,
                    description=desc[:100],
                    emoji=_type_emoji(base, variants[0][0]),
                ),
            )
        super().__init__(placeholder="Pick a type…", options=options[:25], row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await safe_defer(interaction):
            return
        view: MiningRecipeBrowserView = self.view  # type: ignore[assignment]
        await view.render(interaction, category=view.category, base_type=self.values[0])


class _VariantSelect(discord.ui.Select):
    """Level 2 — pick a variant to craft (the workshop-panel craft idiom)."""

    def __init__(
        self,
        variants: list[tuple[str, dict[str, int]]],
        inventory: dict[str, int],
    ) -> None:
        options = [
            discord.SelectOption(
                label=name.title()[:100],
                value=name,
                description=_variant_desc(name, materials),
                emoji="✅" if _affordable(materials, inventory) else None,
            )
            for name, materials in variants[:25]
        ]
        super().__init__(placeholder="Craft a variant…", options=options, row=1)

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
            base_type=view.base_type,
            note=("✅ " if result.ok else "❌ ") + result.message,
            ok=result.ok,
        )


class MiningRecipeBrowserView(HubView):
    """Category → type → variant (crafts); a child of the Workshop hub."""

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

    @classmethod
    async def create(
        cls,
        author: discord.Member | discord.User,
        guild_id: int,
        *,
        category: str | None = None,
        base_type: str | None = None,
    ) -> MiningRecipeBrowserView:
        """Async factory — affordability marks depend on inventory."""
        view = cls(author, guild_id, category=category, base_type=base_type)
        inventory = await db.get_mining_inventory(str(author.id), guild_id)
        if base_type is not None:
            variants = _grouped().get(base_type, [])
            if variants:
                view.add_item(_VariantSelect(variants, inventory))
            view.add_item(_BackButton("↩ Types", "types"))
        elif category is not None:
            view.add_item(_TypeSelect(category, inventory))
            view.add_item(_BackButton("↩ Categories", "categories"))
        else:
            view.add_item(_CategorySelect())
        return view

    async def render(
        self,
        interaction: discord.Interaction,
        *,
        category: str | None = None,
        base_type: str | None = None,
        note: str = "",
        ok: bool | None = None,
    ) -> None:
        """Rebuild for a new level / craft result."""
        embed = await build_recipe_embed(
            self._author.id,
            self.guild_id,
            category=category,
            base_type=base_type,
            note=note,
        )
        if ok is not None:
            embed.color = SUCCESS_COLOR if ok else ERROR_COLOR
        new_view = await MiningRecipeBrowserView.create(
            self._author,
            self.guild_id,
            category=category,
            base_type=base_type,
        )
        await safe_edit(interaction, embed=embed, view=new_view)
        self.stop()

    @discord.ui.button(label="↩ Workshop", style=discord.ButtonStyle.secondary, row=2)
    async def back_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
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


class _BackButton(discord.ui.Button):
    """Step one level up: variants → types (keep category) or types → categories."""

    def __init__(self, label: str, to: str) -> None:
        super().__init__(label=label, style=discord.ButtonStyle.secondary, row=2)
        self._to = to

    async def callback(self, interaction: discord.Interaction) -> None:
        view: MiningRecipeBrowserView = self.view  # type: ignore[assignment]
        if self._to == "types":
            await view.render(interaction, category=view.category, base_type=None)
        else:
            await view.render(interaction, category=None, base_type=None)


__all__ = ["MiningRecipeBrowserView", "build_recipe_embed"]
