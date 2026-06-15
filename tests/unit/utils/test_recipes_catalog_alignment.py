"""Recipes ↔ item-catalog alignment — the content-governance gate.

Owner decision (2026-06-10, mining-finalization session): the item catalog
(`utils/mining/items.py`) is the **single source of truth** for the mining
economy ("curated economy + deeper ladders").  The legacy Minecraft-style
recipe tree (47 recipes; ~25 products unknown to the catalog, 7 using
unobtainable materials) was trimmed to the curated set.

These invariants make recipes.json self-governing: any future recipe must
produce a catalogued (or equippable) item from obtainable materials, so
content additions (the PR-3 deeper ladders, future tiers) can never
reintroduce unclassified inventory junk or dead recipes.
"""

from __future__ import annotations

from utils import equipment
from utils.mining import items
from utils.mining.recipes import DEFAULT_RECIPES, load_recipes

# Resources that drop from mine/harvest/explore — the economy's raw inputs.
# Bronze + silver joined the ore ladder with the V-16 gear sets (Q-0092).
_MINEABLE = {"wood", "stone", "bronze", "iron", "silver", "gold", "diamond"}

# The curated post-trim recipe set.  Extending content = adding the recipe,
# its ItemDef, and (for gear) stats/durability/prices — then this line.
_EXPECTED_RECIPES = {
    "pickaxe",
    "iron pickaxe",
    "torch",
    "lantern",
    "sword",
    "shield",
    "stone hut",
    "wooden house",
    "gold statue",
    "diamond throne",
    "giant fortress",
    # Deeper ladders (2026-06-10)
    "gold pickaxe",
    "diamond pickaxe",
    "diamond lantern",
    # The V-16 combat-set families (Q-0092): 6 families × 5 tiers, each
    # forged from its tier's ore ("armor"/"diamond armor" folded into the
    # chestplate family — migration 068).
    *(
        f"{tier} {family}"
        for tier in ("bronze", "iron", "silver", "gold", "diamond")
        for family in ("sword", "shield", "helmet", "chestplate", "leggings", "boots")
    ),
}


def _obtainable(item: str, recipes: dict, seen: frozenset = frozenset()) -> bool:
    if item in _MINEABLE:
        return True
    if item in seen or item not in recipes:
        return False
    return all(_obtainable(mat, recipes, seen | {item}) for mat in recipes[item])


def test_recipe_set_is_the_curated_one():
    assert set(load_recipes()) == _EXPECTED_RECIPES


def test_every_recipe_product_is_catalogued():
    """No recipe may produce an item the taxonomy doesn't know — unknown
    products default to RESOURCE, don't equip, and have no value."""
    for product in load_recipes():
        assert items.lookup(product) is not None or equipment.is_equippable(
            product,
        ), f"recipe product {product!r} has no ItemDef and is not equippable"


def test_every_recipe_material_is_obtainable():
    recipes = load_recipes()
    for product, materials in recipes.items():
        for mat in materials:
            assert _obtainable(mat, recipes), (
                f"recipe {product!r} needs {mat!r}, which is neither mineable "
                f"nor craftable"
            )


def test_every_wearing_gear_is_reacquirable():
    """The durability loop: anything that can break must be craftable or
    buyable, or breaking it would be a dead end."""
    from utils.mining.market import GEAR_SHOP

    recipes = load_recipes()
    for name in equipment.MAX_DURABILITY:
        assert name in recipes or name in GEAR_SHOP, (
            f"{name!r} wears out but is neither craftable nor in the gear shop"
        )


def test_default_recipes_are_a_subset_of_the_curated_set():
    """The fallback defaults must never resurrect a trimmed recipe."""
    assert set(DEFAULT_RECIPES) <= _EXPECTED_RECIPES