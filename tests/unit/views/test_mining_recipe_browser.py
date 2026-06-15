"""Recipe browser — Category → Type → Variant drill-down, craft-on-select.

Owner UX (2026-06-15): a small category first select (Weapons / Armour / Tools …),
then types (Swords / Helmets …), then variants — instead of one crowded list.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from views.mining.recipe_browser import (
    MiningRecipeBrowserView,
    _base_type,
    _category_of,
    _grouped,
    _types_by_category,
)

_AUTHOR = SimpleNamespace(id=1, display_name="Digger")


def _inventory_patch(inventory=None):
    return patch(
        "views.mining.recipe_browser.db.get_mining_inventory",
        new_callable=AsyncMock,
        return_value=inventory or {},
    )


def test_base_type_is_the_last_word():
    assert _base_type("iron sword") == "sword"
    assert _base_type("diamond pickaxe") == "pickaxe"
    assert _base_type("torch") == "torch"


def test_category_of_maps_slot_then_kind_to_section():
    assert _category_of("iron sword") == "Weapons"
    assert _category_of("iron shield") == "Weapons"  # shields are combat gear
    assert _category_of("iron helmet") == "Armour"
    assert _category_of("iron pickaxe") == "Tools"
    assert _category_of("lantern") == "Tools"
    assert _category_of("stone hut") == "Structures"


def test_variants_within_a_type_are_ordered_by_rarity():
    from utils import equipment

    swords = [name for name, _ in _grouped()["sword"]]
    ranks = [equipment.material_rank(s) for s in swords]
    assert ranks == sorted(ranks)  # starter first → diamond last
    assert swords[0] == "sword" and swords[-1] == "diamond sword"


def test_armour_types_are_in_body_order_helmet_to_boots():
    assert _types_by_category()["Armour"] == [
        "helmet",
        "chestplate",
        "leggings",
        "boots",
    ]


def test_weapons_category_includes_shields_after_swords():
    weapons = _types_by_category()["Weapons"]
    assert "sword" in weapons and "shield" in weapons
    assert weapons.index("sword") < weapons.index("shield")


@pytest.mark.asyncio
async def test_variant_picker_shows_the_stat_preview():
    with _inventory_patch():
        view = await MiningRecipeBrowserView.create(
            _AUTHOR,
            99,
            category="Weapons",
            base_type="sword",
        )
    select = [c for c in view.children if isinstance(c, discord.ui.Select)][0]
    iron = next(o for o in select.options if o.value == "iron sword")
    assert "⚔️+6" in (iron.description or "")


def test_grouped_collapses_variants_under_one_type():
    swords = [name for name, _ in _grouped()["sword"]]
    assert len(swords) > 1
    assert all(_base_type(name) == "sword" for name in swords)


@pytest.mark.asyncio
async def test_top_level_shows_a_small_category_select():
    with _inventory_patch():
        view = await MiningRecipeBrowserView.create(_AUTHOR, 99)
    selects = [c for c in view.children if isinstance(c, discord.ui.Select)]
    assert len(selects) == 1
    labels = {o.label for o in selects[0].options}
    # A small, semantic first select — not the ~14 crowded types.
    assert {"Weapons", "Armour", "Tools"} <= labels
    assert len(selects[0].options) <= 8


@pytest.mark.asyncio
async def test_category_opens_only_its_types():
    with _inventory_patch():
        view = await MiningRecipeBrowserView.create(_AUTHOR, 99, category="Armour")
    select = [c for c in view.children if isinstance(c, discord.ui.Select)][0]
    buttons = {b.label for b in view.children if isinstance(b, discord.ui.Button)}
    armour_types = set(_types_by_category()["Armour"])
    assert armour_types  # non-empty
    assert {o.value for o in select.options} <= armour_types
    assert "↩ Categories" in buttons


@pytest.mark.asyncio
async def test_type_opens_only_that_type_variants():
    with _inventory_patch():
        view = await MiningRecipeBrowserView.create(
            _AUTHOR,
            99,
            category="Weapons",
            base_type="sword",
        )
    select = [c for c in view.children if isinstance(c, discord.ui.Select)][0]
    buttons = {b.label for b in view.children if isinstance(b, discord.ui.Button)}
    assert all(_base_type(o.value) == "sword" for o in select.options)
    assert "↩ Types" in buttons


@pytest.mark.asyncio
async def test_variant_select_crafts_through_the_workflow():
    with _inventory_patch():
        view = await MiningRecipeBrowserView.create(
            _AUTHOR,
            99,
            category="Weapons",
            base_type="sword",
        )
    variant_select = [c for c in view.children if isinstance(c, discord.ui.Select)][0]
    interaction = MagicMock()

    from utils.mining.market import TradeResult

    with (
        patch("views.mining.recipe_browser.safe_defer", AsyncMock(return_value=True)),
        patch(
            "views.mining.recipe_browser.mining_workflow.craft",
            AsyncMock(return_value=TradeResult(True, "Crafted!")),
        ) as craft,
        patch.object(MiningRecipeBrowserView, "render", AsyncMock()),
    ):
        target = variant_select.options[0].value
        variant_select._values = [target]
        await variant_select.callback(interaction)
    craft.assert_awaited_once_with(1, 99, target)
