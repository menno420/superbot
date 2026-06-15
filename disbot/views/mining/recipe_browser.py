"""Mining recipe browser — grouped by item type, then variants.

Owner UX ask (2026-06-15): don't list every tier of a sword separately — group
into **Swords**, **Pickaxes**, **Helmets** … and open a type to its variants
(wood → diamond). The base type is the last word of the product name
("iron **sword**" → ``sword``), so the grouping is derived from the recipe set,
never a hand-kept list. Two levels (type → variant) each fit one 25-option
select, so the old Prev/Next paging is gone.

Crafting itself stays the one shared :func:`services.mining_workflow.craft`.
"""

from __future__ import annotations

from collections import defaultdict

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit
from services import mining_workflow
from utils import db
from utils.mining import items, structures, workshop
from utils.mining.recipes import load_recipes
from utils.ui_constants import ERROR_COLOR, MINING_COLOR, SUCCESS_COLOR
from views.base import HubView

# Per base-type emoji so the type list reads at a glance. Unknown types fall back
# to the item-kind emoji (tools/structures/…).
_TYPE_EMOJI: dict[str, str] = {
    "sword": "🗡️",
    "shield": "🛡️",
    "pickaxe": "⛏️",
    "helmet": "⛑️",
    "chestplate": "🦺",
    "leggings": "👖",
    "boots": "🥾",
    "lantern": "💡",
    "torch": "🔦",
    "throne": "👑",
    "fortress": "🏰",
    "statue": "🗿",
    "hut": "🛖",
    "house": "🏠",
}
_KIND_EMOJI: dict[str, str] = {
    "tool": "🛠️",
    "structure": "🏛️",
    "consumable": "🧨",
    "resource": "⛏️",
    "treasure": "💎",
}


def _base_type(product: str) -> str:
    """The grouping key for a product — its last word ("iron sword" → "sword")."""
    return product.split()[-1].lower()


def _pluralize(base: str) -> str:
    """Label form of a base type — already-plural words (boots, leggings) stay."""
    if base.endswith("s"):
        return base
    if base.endswith(("x", "z", "ch", "sh")):
        return base + "es"
    return base + "s"


def _type_emoji(base: str, sample: str) -> str:
    return _TYPE_EMOJI.get(base) or _KIND_EMOJI.get(items.classify(sample).value, "📦")


def _grouped() -> dict[str, list[tuple[str, dict[str, int]]]]:
    """All recipes grouped by base type, each group's variants name-ordered."""
    groups: dict[str, list[tuple[str, dict[str, int]]]] = defaultdict(list)
    for name, materials in sorted(load_recipes().items()):
        groups[_base_type(name)].append((name, materials))
    return groups


def _affordable(materials: dict[str, int], inventory: dict[str, int]) -> bool:
    return all(inventory.get(mat, 0) >= qty for mat, qty in materials.items())


async def build_recipe_embed(
    user_id: int,
    guild_id: int,
    *,
    base_type: str | None = None,
    note: str = "",
) -> discord.Embed:
    """The type list (``base_type=None``) or one type's variants."""
    inventory = await db.get_mining_inventory(str(user_id), guild_id)
    forge_level = (await db.get_structures(user_id, guild_id)).get(structures.FORGE, 0)
    groups = _grouped()

    embed = discord.Embed(title="📖 Recipes", color=MINING_COLOR)
    if note:
        embed.description = note

    if base_type is None:
        # Level 1 — the type list, with a craftable-now count per type.
        embed.set_footer(text="Pick a type below to see its variants.")
        for base in sorted(groups):
            variants = groups[base]
            craftable = sum(1 for _, m in variants if _affordable(m, inventory))
            emoji = _type_emoji(base, variants[0][0])
            value = f"{len(variants)} variant{'s' * (len(variants) != 1)}"
            if craftable:
                value += f"  •  ✅ {craftable} craftable now"
            embed.add_field(
                name=f"{emoji} {_pluralize(base).title()}",
                value=value,
                inline=True,
            )
        return embed

    # Level 2 — variants of the chosen type, with have/need per material.
    variants = groups.get(base_type, [])
    emoji = _type_emoji(base_type, variants[0][0] if variants else base_type)
    embed.title = f"📖 {emoji} {_pluralize(base_type).title()}"
    embed.set_footer(text="Pick a variant to craft it  •  ↩ Types to go back")
    if not variants:
        embed.add_field(
            name="Nothing here", value="No recipes of this type.", inline=False
        )
    for name, materials in variants:
        have_lines = ", ".join(
            f"{mat} {min(inventory.get(mat, 0), qty)}/{qty}"
            for mat, qty in sorted(materials.items())
        )
        if not structures.meets_forge_requirement(name, forge_level):
            marker = "🔒"
            need = structures.forge_level_name(structures.forge_level_required(name))
            have_lines += f"\n🔥 needs **{need}** (`!forge`)"
        else:
            marker = "✅" if _affordable(materials, inventory) else "▫️"
        embed.add_field(name=f"{marker} {name.title()}", value=have_lines, inline=True)
    return embed


class _TypeSelect(discord.ui.Select):
    """Level 1 — pick an item type (Swords / Pickaxes / …)."""

    def __init__(self, inventory: dict[str, int]) -> None:
        groups = _grouped()
        options = []
        for base in sorted(groups):
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
        super().__init__(placeholder="Browse a type…", options=options[:25], row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await safe_defer(interaction):
            return
        view: MiningRecipeBrowserView = self.view  # type: ignore[assignment]
        await view.render(interaction, base_type=self.values[0])


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
                description=workshop.describe_materials(materials)[:100],
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
            base_type=view.base_type,
            note=("✅ " if result.ok else "❌ ") + result.message,
            ok=result.ok,
        )


class MiningRecipeBrowserView(HubView):
    """Type select → variant select (crafts); a child of the mining hub."""

    SUBSYSTEM = "mining"

    def __init__(
        self,
        author: discord.Member | discord.User,
        guild_id: int,
        *,
        base_type: str | None = None,
    ) -> None:
        super().__init__(author)
        self.guild_id = guild_id
        self.base_type = base_type

    @classmethod
    async def create(
        cls,
        author: discord.Member | discord.User,
        guild_id: int,
        *,
        base_type: str | None = None,
    ) -> MiningRecipeBrowserView:
        """Async factory — affordability marks depend on inventory."""
        view = cls(author, guild_id, base_type=base_type)
        inventory = await db.get_mining_inventory(str(author.id), guild_id)
        if base_type is None:
            view.add_item(_TypeSelect(inventory))
        else:
            variants = _grouped().get(base_type, [])
            if variants:
                view.add_item(_VariantSelect(variants, inventory))
            view.add_item(_BackToTypesButton())
        return view

    async def render(
        self,
        interaction: discord.Interaction,
        *,
        base_type: str | None,
        note: str = "",
        ok: bool | None = None,
    ) -> None:
        """Rebuild for a new type / craft result."""
        embed = await build_recipe_embed(
            self._author.id,
            self.guild_id,
            base_type=base_type,
            note=note,
        )
        if ok is not None:
            embed.color = SUCCESS_COLOR if ok else ERROR_COLOR
        new_view = await MiningRecipeBrowserView.create(
            self._author,
            self.guild_id,
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


class _BackToTypesButton(discord.ui.Button):
    """Return from a type's variants to the type list (level 2 → level 1)."""

    def __init__(self) -> None:
        super().__init__(label="↩ Types", style=discord.ButtonStyle.secondary, row=2)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: MiningRecipeBrowserView = self.view  # type: ignore[assignment]
        await view.render(interaction, base_type=None)


__all__ = ["MiningRecipeBrowserView", "build_recipe_embed"]
