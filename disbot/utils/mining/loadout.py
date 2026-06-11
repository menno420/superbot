"""Best-loadout picker — the old MULTIEQUIP, as a pure helper.

Given an inventory, pick the strongest loadout for the Gear panel's
"Equip Best" button.  Two candidates are compared by total stat power:

* the **per-slot greedy** pick (strongest owned item per slot), and
* for each tier the player owns *completely*, the **full same-tier set**
  (set bonus included) with greedy picks for the non-set slots.

The set candidates exist because the same-tier set bonus
(:func:`utils.equipment.set_bonus`) can outweigh a single higher-tier
piece — a naive greedy would happily break a complete set for one stronger
chestplate and *lower* the player's stats.
"""

from __future__ import annotations

from dataclasses import astuple

from utils import equipment


def _power(item: str) -> int:
    return sum(astuple(equipment.item_stats(item)))


def _loadout_power(loadout: dict[str, str]) -> int:
    """Total stat power of a full loadout — set bonus included."""
    return sum(astuple(equipment.compute_stats(loadout)))


def _greedy(inventory: dict[str, int]) -> dict[str, str]:
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


_FAMILY_BY_SLOT: dict[str, str] = {
    equipment.WEAPON: "sword",
    equipment.SHIELD: "shield",
    equipment.HELMET: "helmet",
    equipment.CHESTPLATE: "chestplate",
    equipment.LEGGINGS: "leggings",
    equipment.BOOTS: "boots",
}


def best_loadout(inventory: dict[str, int]) -> dict[str, str]:
    """``{slot: item}`` — the strongest equippable loadout (set-aware)."""
    owned = {item.lower() for item, qty in inventory.items() if qty >= 1}
    candidates = [_greedy(inventory)]
    for tier in equipment.TIER_ORDER:
        set_items = {
            slot: item
            for slot in equipment.SET_SLOTS
            if (item := f"{tier} {_FAMILY_BY_SLOT[slot]}") in owned
        }
        if len(set_items) != len(equipment.SET_SLOTS):
            continue  # incomplete tier — no set candidate
        candidate = dict(candidates[0])
        candidate.update(set_items)
        candidates.append(candidate)
    return max(candidates, key=_loadout_power)


__all__ = ["best_loadout"]
