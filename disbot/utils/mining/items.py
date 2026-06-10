"""Item taxonomy — pure classification of mining items (foundation).

Today every mining item (ore, wood, a built structure, a tool, a
consumable) is an undifferentiated string key in ``mining_inventory``.
That works for storage but means no layer can answer "is this a tool?",
"what tier is this pickaxe?", or "sort my inventory sensibly" without
hard-coding name lists at each call site.

This module is the single, pure source of truth for that taxonomy.  It
classifies known items, exposes tool tiers (the backbone of a crafting
progression), and provides display/sorting helpers.  No Discord, no DB.

It is additive foundation: nothing imports it in a command path yet.  A
future crafting service / cog and the exploration renderer would consume
:func:`classify`, :func:`tool_tier`, and :func:`sort_inventory`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ItemKind(Enum):
    RESOURCE = "resource"  # raw materials: stone, iron, gold, diamond, wood
    TOOL = "tool"  # pickaxe, axe, torch, lantern, dynamite
    CONSUMABLE = "consumable"  # used up on use: dynamite, torch
    STRUCTURE = "structure"  # built via recipes: stone hut, gold statue
    TREASURE = "treasure"  # high-value finds with no crafting use


@dataclass(frozen=True)
class ItemDef:
    name: str
    kind: ItemKind
    # 0 for non-tiered items; 1..5 for a tool/material progression.
    tier: int = 0
    # Relative display/economy value; used by total_value + sorting.
    value: int = 1
    stackable: bool = True
    tags: frozenset[str] = field(default_factory=frozenset)


# Canonical catalog.  Names are stored lower-cased to match inventory keys.
_CATALOG: dict[str, ItemDef] = {
    # resources (ordered by value / depth)
    "wood": ItemDef("wood", ItemKind.RESOURCE, tier=1, value=1),
    "stone": ItemDef("stone", ItemKind.RESOURCE, tier=1, value=1),
    "iron": ItemDef("iron", ItemKind.RESOURCE, tier=2, value=3),
    "gold": ItemDef("gold", ItemKind.RESOURCE, tier=3, value=6),
    "diamond": ItemDef("diamond", ItemKind.RESOURCE, tier=4, value=12),
    # tools (tier drives crafting upgrades / loadout strength)
    "axe": ItemDef("axe", ItemKind.TOOL, tier=1, value=5),
    "pickaxe": ItemDef("pickaxe", ItemKind.TOOL, tier=1, value=5),
    "torch": ItemDef(
        "torch",
        ItemKind.CONSUMABLE,
        tier=1,
        value=2,
        tags=frozenset({"light"}),
    ),
    "lantern": ItemDef(
        "lantern",
        ItemKind.TOOL,
        tier=2,
        value=10,
        tags=frozenset({"light"}),
    ),
    "dynamite": ItemDef(
        "dynamite",
        ItemKind.CONSUMABLE,
        tier=2,
        value=8,
        tags=frozenset({"blast"}),
    ),
    "lucky charm": ItemDef(
        "lucky charm",
        ItemKind.TREASURE,
        tier=3,
        value=20,
        tags=frozenset({"luck"}),
    ),
    # Combat gear (deathmatch) — equippable tools-of-war; never sellable (TOOL,
    # not RESOURCE).  Values are for inventory net-worth display, not a sale price.
    "sword": ItemDef(
        "sword",
        ItemKind.TOOL,
        tier=1,
        value=5,
        tags=frozenset({"weapon"}),
    ),
    "iron sword": ItemDef(
        "iron sword",
        ItemKind.TOOL,
        tier=2,
        value=15,
        tags=frozenset({"weapon"}),
    ),
    "shield": ItemDef(
        "shield",
        ItemKind.TOOL,
        tier=1,
        value=8,
        tags=frozenset({"armor"}),
    ),
    "armor": ItemDef(
        "armor",
        ItemKind.TOOL,
        tier=2,
        value=18,
        tags=frozenset({"armor"}),
    ),
    # Structures are built via recipes rather than mined.
    "stone hut": ItemDef("stone hut", ItemKind.STRUCTURE, value=10, stackable=False),
    "iron pickaxe": ItemDef("iron pickaxe", ItemKind.TOOL, tier=2, value=15),
    "gold statue": ItemDef(
        "gold statue",
        ItemKind.STRUCTURE,
        value=30,
        stackable=False,
    ),
    "diamond throne": ItemDef(
        "diamond throne",
        ItemKind.STRUCTURE,
        value=80,
        stackable=False,
    ),
    "wooden house": ItemDef(
        "wooden house",
        ItemKind.STRUCTURE,
        value=12,
        stackable=False,
    ),
    "giant fortress": ItemDef(
        "giant fortress",
        ItemKind.STRUCTURE,
        value=150,
        stackable=False,
    ),
}

# Tool upgrade ladder — the spine of a future crafting progression.  Each
# entry maps a tool family to its ordered tiers (lowest → highest).
TOOL_LADDERS: dict[str, tuple[str, ...]] = {
    "pickaxe": ("pickaxe", "iron pickaxe"),
    "light": ("torch", "lantern"),
}


def lookup(name: str) -> ItemDef | None:
    """Return the :class:`ItemDef` for *name*, or None if unknown."""
    return _CATALOG.get(name.lower())


def classify(name: str) -> ItemKind:
    """Classify *name*.  Unknown items default to RESOURCE — the safest
    assumption for an inventory total (counts toward totals, no special
    behaviour).
    """
    item = _CATALOG.get(name.lower())
    return item.kind if item else ItemKind.RESOURCE


def is_tool(name: str) -> bool:
    return classify(name) is ItemKind.TOOL


def is_consumable(name: str) -> bool:
    return classify(name) is ItemKind.CONSUMABLE


def tool_tier(name: str) -> int:
    """Tier of *name* (0 if unknown or non-tiered)."""
    item = _CATALOG.get(name.lower())
    return item.tier if item else 0


def item_value(name: str) -> int:
    """Per-unit value of *name* (1 for unknown items)."""
    item = _CATALOG.get(name.lower())
    return item.value if item else 1


def total_value(inventory: dict[str, int]) -> int:
    """Sum the economic value of an ``{item_name: qty}`` inventory."""
    return sum(item_value(name) * qty for name, qty in inventory.items() if qty > 0)


def next_tool_upgrade(name: str) -> str | None:
    """Return the next tier up from *name* in its ladder, or None if *name*
    is already top-tier / not on a ladder.
    """
    lowered = name.lower()
    for ladder in TOOL_LADDERS.values():
        if lowered in ladder:
            idx = ladder.index(lowered)
            if idx + 1 < len(ladder):
                return ladder[idx + 1]
            return None
    return None


def sort_inventory(inventory: dict[str, int]) -> list[tuple[str, int]]:
    """Return inventory items ordered for display.

    Sort key: kind (resources, then tools, then consumables, then
    structures, then treasure), then descending value, then name.  Items
    with zero quantity are dropped.
    """
    kind_order = {
        ItemKind.RESOURCE: 0,
        ItemKind.TOOL: 1,
        ItemKind.CONSUMABLE: 2,
        ItemKind.STRUCTURE: 3,
        ItemKind.TREASURE: 4,
    }
    rows = [(name, qty) for name, qty in inventory.items() if qty > 0]
    rows.sort(
        key=lambda kv: (
            kind_order[classify(kv[0])],
            -item_value(kv[0]),
            kv[0].lower(),
        ),
    )
    return rows


def summarize_inventory(
    inventory: dict[str, int],
) -> list[tuple[ItemKind, list[tuple[str, int]]]]:
    """Group a raw ``{item: qty}`` inventory into ordered display sections.

    Returns ``[(kind, [(name, qty), ...]), ...]`` using the same ordering as
    :func:`sort_inventory` (kind, then value desc, then name), chunked into one
    section per :class:`ItemKind` that has at least one positive-quantity item.
    Pure: no Discord, no DB — call sites turn the sections into embeds/text.
    """
    sections: list[tuple[ItemKind, list[tuple[str, int]]]] = []
    current: ItemKind | None = None
    for name, qty in sort_inventory(inventory):
        kind = classify(name)
        if kind is not current:
            sections.append((kind, []))
            current = kind
        sections[-1][1].append((name, qty))
    return sections


__all__ = [
    "ItemKind",
    "ItemDef",
    "TOOL_LADDERS",
    "lookup",
    "classify",
    "is_tool",
    "is_consumable",
    "tool_tier",
    "item_value",
    "total_value",
    "next_tool_upgrade",
    "sort_inventory",
    "summarize_inventory",
]
