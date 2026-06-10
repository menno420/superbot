"""Best-loadout picker — the old MULTIEQUIP, as a pure helper.

Given an inventory, pick the strongest owned item for each equipment slot
(the Gear panel's "Equip Best" button).  "Strongest" = the sum of the
item's stat contributions — a single scalar is enough because gear within
one slot is strictly tiered (pickaxe < iron < gold < diamond …).
"""

from __future__ import annotations

from dataclasses import astuple

from utils import equipment


def _power(item: str) -> int:
    return sum(astuple(equipment.item_stats(item)))


def best_loadout(inventory: dict[str, int]) -> dict[str, str]:
    """``{slot: item}`` — the strongest owned, equippable item per slot."""
    best: dict[str, tuple[int, str]] = {}
    for item, qty in inventory.items():
        if qty < 1:
            continue
        slot = equipment.slot_for(item)
        if slot is None:
            continue
        score = _power(item)
        if slot not in best or score > best[slot][0]:
            best[slot] = (score, item)
    return {slot: item for slot, (_, item) in best.items()}


__all__ = ["best_loadout"]
