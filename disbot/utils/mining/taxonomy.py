"""Item taxonomy for the 3-layer menu doctrine — name → category / type / order.

Pure (stdlib + the stat model).  Shared by the recipe browser (**craft**) and the
market (**buy**) so both group gear identically — **Category → Type → Variant** —
each level ordered: categories by intent, types head-to-toe / weapon-first,
variants by rarity.  Everything derives from equipment slots + item kind; never a
hand-kept list.  See ``docs/building-roadmap/hub-ui-standard.md`` §
"The 3-layer menu doctrine".
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from utils import equipment
from utils.mining import items

# Semantic categories (a small first select), in display order.
CATEGORY_ORDER: tuple[str, ...] = ("Weapons", "Armour", "Tools", "Structures", "Items")
CATEGORY_EMOJI: dict[str, str] = {
    "Weapons": "⚔️",
    "Armour": "🛡️",
    "Tools": "🛠️",
    "Structures": "🏛️",
    "Items": "🎒",
}
_ARMOUR_SLOTS = frozenset(
    {
        equipment.HELMET,
        equipment.CHESTPLATE,
        equipment.LEGGINGS,
        equipment.BOOTS,
    },
)
_TOOL_SLOTS = frozenset({equipment.TOOL, equipment.LIGHT, equipment.CHARM})

# Per base-type emoji so each type reads at a glance.
TYPE_EMOJI: dict[str, str] = {
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


def base_type(name: str) -> str:
    """The type key for an item — its last word ("iron sword" → "sword")."""
    return name.split()[-1].lower()


def category_of(name: str) -> str:
    """The semantic category for an item, from its equip slot then its kind.
    Shields sit with Weapons (combat gear; they also carry a damage bonus).
    """
    slot = equipment.slot_for(name)
    if slot in (equipment.WEAPON, equipment.SHIELD):
        return "Weapons"
    if slot in _ARMOUR_SLOTS:
        return "Armour"
    if slot in _TOOL_SLOTS:
        return "Tools"
    if items.classify(name).value == "structure":
        return "Structures"
    return "Items"


def pluralize(base: str) -> str:
    """Label form of a base type — already-plural words (boots, leggings) stay."""
    if base.endswith("s"):
        return base
    if base.endswith(("x", "z", "ch", "sh")):
        return base + "es"
    return base + "s"


def type_emoji(base: str, sample: str) -> str:
    return TYPE_EMOJI.get(base) or _KIND_EMOJI.get(items.classify(sample).value, "📦")


def category_emoji(category: str) -> str:
    return CATEGORY_EMOJI.get(category, "")


def _slot_rank(sample: str) -> int:
    """A type's ordering position — its equip-slot index in ``equipment.SLOTS``
    (so armour reads head-to-toe helmet→boots and weapons read sword→shield);
    non-equippable types (structures) sort last.
    """
    slot = equipment.slot_for(sample)
    return equipment.SLOTS.index(slot) if slot in equipment.SLOTS else 99


def grouped(names: Iterable[str]) -> dict[str, list[str]]:
    """``base_type → [names]`` with each group's variants ordered by rarity
    (starter → bronze → … → diamond).
    """
    groups: dict[str, list[str]] = defaultdict(list)
    for name in names:
        groups[base_type(name)].append(name)
    for variants in groups.values():
        variants.sort(key=lambda n: (equipment.material_rank(n), n))
    return dict(groups)


def types_by_category(names: Iterable[str]) -> dict[str, list[str]]:
    """``category → [base_types]`` ordered by equip slot (body order)."""
    by_cat: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for base, variants in grouped(names).items():
        by_cat[category_of(variants[0])].append((base, variants[0]))
    return {
        cat: [b for b, _ in sorted(pairs, key=lambda bs: (_slot_rank(bs[1]), bs[0]))]
        for cat, pairs in by_cat.items()
    }


def ordered_categories(names: Iterable[str]) -> list[str]:
    """The categories present in *names*, in display order."""
    present = set(types_by_category(names))
    return [c for c in CATEGORY_ORDER if c in present]


__all__ = [
    "CATEGORY_ORDER",
    "CATEGORY_EMOJI",
    "TYPE_EMOJI",
    "base_type",
    "category_of",
    "pluralize",
    "type_emoji",
    "category_emoji",
    "grouped",
    "types_by_category",
    "ordered_categories",
]
