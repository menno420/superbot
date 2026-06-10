"""Gear panel — slot→item selects, Equip Best, workflow routing."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from utils.mining.loadout import best_loadout
from views.mining.gear_panel import _UNEQUIP_SENTINEL, MiningGearView
from views.mining.main_panel import MiningHubView

_AUTHOR = SimpleNamespace(id=1, display_name="Digger")


def _db_patches(inventory=None, equipped=None, wear=None):
    return (
        patch(
            "views.mining.gear_panel.db.get_mining_inventory",
            new_callable=AsyncMock,
            return_value=inventory or {},
        ),
        patch(
            "views.mining.gear_panel.db.get_equipment",
            new_callable=AsyncMock,
            return_value=equipped or {},
        ),
        patch(
            "views.mining.gear_panel.db.get_gear_wear",
            new_callable=AsyncMock,
            return_value=wear or {},
        ),
    )


def test_hub_has_gear_and_recipes_buttons():
    ids = {getattr(c, "custom_id", None) for c in MiningHubView().children}
    assert "mining:gear" in ids
    assert "mining:recipes" in ids


@pytest.mark.asyncio
async def test_factory_builds_slot_select_and_item_select_for_chosen_slot():
    p_inv, p_eq, p_wear = _db_patches(
        inventory={"pickaxe": 1, "iron pickaxe": 1, "torch": 1},
        equipped={"tool": "pickaxe"},
    )
    with p_inv, p_eq, p_wear:
        bare = await MiningGearView.create(_AUTHOR, 99)
        with_slot = await MiningGearView.create(_AUTHOR, 99, slot="tool")
    bare_selects = [c for c in bare.children if isinstance(c, discord.ui.Select)]
    assert len(bare_selects) == 1  # slot picker only
    slot_selects = [c for c in with_slot.children if isinstance(c, discord.ui.Select)]
    assert len(slot_selects) == 2
    item_select = slot_selects[1]
    values = {o.value for o in item_select.options}
    # Only tool-slot gear the player owns, plus the unequip sentinel.
    assert values == {"pickaxe", "iron pickaxe", _UNEQUIP_SENTINEL}


@pytest.mark.asyncio
async def test_item_select_routes_through_the_workflow():
    p_inv, p_eq, p_wear = _db_patches(inventory={"torch": 1})
    with p_inv, p_eq, p_wear:
        view = await MiningGearView.create(_AUTHOR, 99, slot="light")
    item_select = [c for c in view.children if isinstance(c, discord.ui.Select)][1]
    interaction = MagicMock()

    from utils.mining.market import TradeResult

    with (
        patch(
            "views.mining.gear_panel.safe_defer",
            AsyncMock(return_value=True),
        ),
        patch(
            "views.mining.gear_panel.mining_workflow.equip",
            AsyncMock(return_value=TradeResult(True, "ok")),
        ) as equip,
        patch("views.mining.gear_panel._rerender", AsyncMock()),
    ):
        item_select._values = ["torch"]
        await item_select.callback(interaction)
    equip.assert_awaited_once_with(1, 99, "torch")


def test_best_loadout_picks_the_strongest_per_slot():
    picks = best_loadout(
        {
            "pickaxe": 1,
            "diamond pickaxe": 1,
            "torch": 2,
            "lantern": 1,
            "wood": 50,  # not equippable — ignored
            "sword": 0,  # owned zero — ignored
        },
    )
    assert picks["tool"] == "diamond pickaxe"
    assert picks["light"] == "lantern"
    assert "weapon" not in picks
