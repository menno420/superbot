"""Tests for cogs.mining.workshop — durability, repair, crafting (the sink).

The orchestration tests mock the economy seam and the mining CRUD so they pin
the *contract* (repair coins move through economy_service; breaking consumes
the item from inventory + clears the slot + records last-broken; crafting
moves materials + product in ONE atomic call) without a real DB.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from cogs.mining import market, workshop
from services.economy_service import InsufficientFundsError
from utils import equipment

# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def test_every_wearing_item_is_equippable_with_positive_max():
    for name, maximum in equipment.MAX_DURABILITY.items():
        assert equipment.is_equippable(name), name
        assert maximum > 0, name


def test_repair_base_derived_from_gear_shop():
    # One knob: repair price follows the shop price at REPAIR_RATE.
    assert workshop.repair_base("pickaxe") == 13  # ceil(25 * 0.5)
    assert workshop.repair_base("torch") == 5  # ceil(10 * 0.5)
    assert workshop.repair_base("not an item") is None


def test_repair_cost_proportional_to_missing_durability():
    maximum = equipment.max_durability("pickaxe")
    assert maximum == 60
    assert workshop.repair_cost("pickaxe", maximum) is None  # not worn
    nearly_broken = workshop.repair_cost("pickaxe", 1)
    barely_worn = workshop.repair_cost("pickaxe", maximum - 1)
    assert nearly_broken == 13  # ~the full base
    assert barely_worn == 1  # min cost
    assert nearly_broken > barely_worn


def test_every_wearing_item_is_repairable():
    # Every item that wears must have a repair price (it is in the gear shop).
    for name in equipment.MAX_DURABILITY:
        assert workshop.repair_base(name) is not None, name


def test_durability_bar_renders_five_segments():
    assert workshop.durability_bar(60, 60) == "▰▰▰▰▰ 60/60"
    assert workshop.durability_bar(1, 60).startswith("▰▱▱▱▱")
    assert workshop.durability_bar(0, 60).startswith("▱▱▱▱▱")


def test_craftable_gear_lists_equippables_with_inventory_check():
    recipes = {
        "torch": {"wood": 2},
        "stone hut": {"stone": 5},  # structure — not gear
        "iron pickaxe": {"iron": 3, "wood": 1},
    }
    rows = workshop.craftable_gear(recipes, {"wood": 2})
    by_name = {g.name: g for g in rows}
    assert "stone hut" not in by_name
    assert by_name["torch"].craftable
    assert not by_name["iron pickaxe"].craftable


def test_starter_gear_has_obtainable_recipes():
    # The durability loop needs broken starter gear to be re-craftable starting
    # from mineable resources (wood/stone/iron/gold/diamond) — directly or via
    # craftable intermediates (wood → wooden planks → stick → iron pickaxe).
    from utils.mining.recipes import load_recipes

    recipes = load_recipes()
    mineable = {"wood", "stone", "iron", "gold", "diamond"}

    def obtainable(item: str, seen: frozenset[str] = frozenset()) -> bool:
        if item in mineable:
            return True
        if item in seen or item not in recipes:
            return False
        return all(obtainable(mat, seen | {item}) for mat in recipes[item])

    for item in ("pickaxe", "torch", "lantern", "iron pickaxe"):
        assert item in recipes, f"{item} has no recipe"
        assert obtainable(item), f"{item} needs unobtainable materials"


# ---------------------------------------------------------------------------
# Wear — the durability tick
# ---------------------------------------------------------------------------


def _wear_patches(wear: dict[str, int]):
    return (
        patch(
            "cogs.mining.workshop.db.get_gear_wear",
            new_callable=AsyncMock,
            return_value=wear,
        ),
        patch("cogs.mining.workshop.db.set_gear_wear", new_callable=AsyncMock),
        patch("cogs.mining.workshop.db.clear_gear_wear", new_callable=AsyncMock),
        patch("cogs.mining.workshop.db.update_mining_item", new_callable=AsyncMock),
        patch("cogs.mining.workshop.db.unequip_slot", new_callable=AsyncMock),
        patch("cogs.mining.workshop.db.set_last_broken", new_callable=AsyncMock),
    )


@pytest.mark.asyncio
async def test_apply_wear_ticks_equipped_tool():
    p_get, p_set, p_clear, p_inv, p_uneq, p_broken = _wear_patches({})
    with p_get, p_set as mock_set, p_clear, p_inv as mock_inv, p_uneq, p_broken:
        report = await workshop.apply_wear(
            1,
            7,
            action=workshop.ACTION_MINE,
            depth=0,
            equipped={"tool": "pickaxe"},
        )
    assert not report.broke
    mock_set.assert_awaited_once_with("1", 7, "pickaxe", 59)  # fresh 60 → 59
    mock_inv.assert_not_awaited()


@pytest.mark.asyncio
async def test_apply_wear_breaks_at_zero_consuming_the_item():
    p_get, p_set, p_clear, p_inv, p_uneq, p_broken = _wear_patches({"pickaxe": 1})
    with p_get, p_set as mock_set, p_clear as mock_clear, p_inv as mock_inv, (
        p_uneq
    ) as mock_uneq, p_broken as mock_broken:
        report = await workshop.apply_wear(
            1,
            7,
            action=workshop.ACTION_MINE,
            depth=0,
            equipped={"tool": "pickaxe"},
        )
    assert report.broke == ("pickaxe",)
    assert any("broke" in n for n in report.notes)
    mock_clear.assert_awaited_once_with("1", 7, "pickaxe")
    mock_inv.assert_awaited_once_with("1", 7, "pickaxe", -1)  # the sink
    mock_uneq.assert_awaited_once_with("1", 7, "tool")
    mock_broken.assert_awaited_once_with("1", 7, "pickaxe")
    mock_set.assert_not_awaited()


@pytest.mark.asyncio
async def test_apply_wear_light_only_wears_underground():
    # At the surface the light does not tick; underground it does.
    p_get, p_set, p_clear, p_inv, p_uneq, p_broken = _wear_patches({})
    with p_get, p_set as mock_set, p_clear, p_inv, p_uneq, p_broken:
        await workshop.apply_wear(
            1,
            7,
            action=workshop.ACTION_MINE,
            depth=0,
            equipped={"light": "torch"},
        )
        mock_set.assert_not_awaited()
        await workshop.apply_wear(
            1,
            7,
            action=workshop.ACTION_MINE,
            depth=1,
            equipped={"light": "torch"},
        )
        mock_set.assert_awaited_once_with("1", 7, "torch", 39)


@pytest.mark.asyncio
async def test_apply_wear_explore_ticks_charm_not_tool():
    p_get, p_set, p_clear, p_inv, p_uneq, p_broken = _wear_patches({})
    with p_get, p_set as mock_set, p_clear, p_inv, p_uneq, p_broken:
        await workshop.apply_wear(
            1,
            7,
            action=workshop.ACTION_EXPLORE,
            depth=0,
            equipped={"tool": "pickaxe", "charm": "lucky charm"},
        )
    mock_set.assert_awaited_once_with("1", 7, "lucky charm", 79)


@pytest.mark.asyncio
async def test_apply_wear_warns_when_nearly_broken():
    p_get, p_set, p_clear, p_inv, p_uneq, p_broken = _wear_patches({"pickaxe": 4})
    with p_get, p_set, p_clear, p_inv, p_uneq, p_broken:
        report = await workshop.apply_wear(
            1,
            7,
            action=workshop.ACTION_MINE,
            depth=0,
            equipped={"tool": "pickaxe"},
        )
    assert any("nearly worn out" in n for n in report.notes)


@pytest.mark.asyncio
async def test_apply_wear_skips_non_wearing_and_empty_slots_without_db():
    # No DB read at all when nothing equipped can wear (cheap fast path).
    with patch(
        "cogs.mining.workshop.db.get_gear_wear",
        new_callable=AsyncMock,
    ) as mock_get:
        report = await workshop.apply_wear(
            1,
            7,
            action=workshop.ACTION_MINE,
            depth=0,
            equipped={},
        )
    assert report == workshop.WearReport()
    mock_get.assert_not_awaited()


# ---------------------------------------------------------------------------
# Repair — the audited coin sink
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_repair_debits_then_clears_wear():
    with patch(
        "cogs.mining.workshop.db.get_mining_inventory",
        new_callable=AsyncMock,
        return_value={"pickaxe": 1},
    ), patch(
        "cogs.mining.workshop.db.get_gear_wear",
        new_callable=AsyncMock,
        return_value={"pickaxe": 10},
    ), patch(
        "cogs.mining.workshop.economy_service.debit",
        new_callable=AsyncMock,
        return_value=88,
    ) as mock_debit, patch(
        "cogs.mining.workshop.db.clear_gear_wear",
        new_callable=AsyncMock,
    ) as mock_clear:
        result = await workshop.apply_repair(123, 7, "pickaxe")
    assert result.ok
    args, kwargs = mock_debit.await_args
    assert args[:2] == (7, 123)
    assert args[2] == workshop.repair_cost("pickaxe", 10)
    assert kwargs["reason"] == workshop.REPAIR_REASON
    mock_clear.assert_awaited_once_with("123", 7, "pickaxe")
    assert result.new_balance == 88


@pytest.mark.asyncio
async def test_apply_repair_insufficient_funds_keeps_wear():
    with patch(
        "cogs.mining.workshop.db.get_mining_inventory",
        new_callable=AsyncMock,
        return_value={"pickaxe": 1},
    ), patch(
        "cogs.mining.workshop.db.get_gear_wear",
        new_callable=AsyncMock,
        return_value={"pickaxe": 10},
    ), patch(
        "cogs.mining.workshop.economy_service.debit",
        new_callable=AsyncMock,
        side_effect=InsufficientFundsError(),
    ), patch(
        "cogs.mining.workshop.db.get_coins",
        new_callable=AsyncMock,
        return_value=2,
    ), patch(
        "cogs.mining.workshop.db.clear_gear_wear",
        new_callable=AsyncMock,
    ) as mock_clear:
        result = await workshop.apply_repair(123, 7, "pickaxe")
    assert not result.ok
    mock_clear.assert_not_awaited()  # no free repair


@pytest.mark.asyncio
async def test_apply_repair_rejects_unworn_unowned_and_unwearing():
    with patch(
        "cogs.mining.workshop.db.get_mining_inventory",
        new_callable=AsyncMock,
        return_value={"pickaxe": 1},
    ), patch(
        "cogs.mining.workshop.db.get_gear_wear",
        new_callable=AsyncMock,
        return_value={},
    ):
        full = await workshop.apply_repair(1, 7, "pickaxe")
        assert not full.ok and "full durability" in full.message
    with patch(
        "cogs.mining.workshop.db.get_mining_inventory",
        new_callable=AsyncMock,
        return_value={},
    ):
        unowned = await workshop.apply_repair(1, 7, "pickaxe")
        assert not unowned.ok and "don't own" in unowned.message
    stone = await workshop.apply_repair(1, 7, "stone")
    assert not stone.ok and "doesn't wear" in stone.message


# ---------------------------------------------------------------------------
# Craft — atomic recipe application
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_craft_moves_materials_and_product_in_one_call():
    with patch(
        "cogs.mining.workshop.load_recipes",
        return_value={"torch": {"wood": 2}},
    ), patch(
        "cogs.mining.workshop.db.get_mining_inventory",
        new_callable=AsyncMock,
        return_value={"wood": 5},
    ), patch(
        "cogs.mining.workshop.db.apply_inventory_deltas",
        new_callable=AsyncMock,
    ) as mock_apply:
        result = await workshop.apply_craft(1, 7, "Torch")
    assert result.ok
    mock_apply.assert_awaited_once_with("1", 7, {"wood": -2, "torch": 1})


@pytest.mark.asyncio
async def test_apply_craft_rejects_missing_materials_without_writes():
    with patch(
        "cogs.mining.workshop.load_recipes",
        return_value={"torch": {"wood": 2}},
    ), patch(
        "cogs.mining.workshop.db.get_mining_inventory",
        new_callable=AsyncMock,
        return_value={"wood": 1},
    ), patch(
        "cogs.mining.workshop.db.apply_inventory_deltas",
        new_callable=AsyncMock,
    ) as mock_apply:
        result = await workshop.apply_craft(1, 7, "torch")
    assert not result.ok
    mock_apply.assert_not_awaited()


@pytest.mark.asyncio
async def test_apply_craft_unknown_recipe_hints_market_for_shop_items():
    with patch("cogs.mining.workshop.load_recipes", return_value={}):
        buyable = await workshop.apply_craft(1, 7, "lucky charm")
        unknown = await workshop.apply_craft(1, 7, "warp drive")
    assert not buyable.ok and "Market" in buyable.message
    assert not unknown.ok and "buildlist" in unknown.message


# ---------------------------------------------------------------------------
# Quick-craft — re-craft the last broken item
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_quick_craft_crafts_equips_and_clears_marker():
    with patch(
        "cogs.mining.workshop.db.get_last_broken",
        new_callable=AsyncMock,
        return_value="torch",
    ), patch(
        "cogs.mining.workshop.load_recipes",
        return_value={"torch": {"wood": 2}},
    ), patch(
        "cogs.mining.workshop.db.get_mining_inventory",
        new_callable=AsyncMock,
        return_value={"wood": 4},
    ), patch(
        "cogs.mining.workshop.db.apply_inventory_deltas",
        new_callable=AsyncMock,
    ), patch(
        "cogs.mining.workshop.db.get_equipment",
        new_callable=AsyncMock,
        return_value={},  # light slot free → auto-equip
    ), patch(
        "cogs.mining.workshop.db.equip_item",
        new_callable=AsyncMock,
    ) as mock_equip, patch(
        "cogs.mining.workshop.db.set_last_broken",
        new_callable=AsyncMock,
    ) as mock_marker:
        result = await workshop.apply_quick_craft(1, 7)
    assert result.ok
    mock_equip.assert_awaited_once_with("1", 7, "light", "torch")
    mock_marker.assert_awaited_once_with("1", 7, None)
    assert "equipped" in result.message


@pytest.mark.asyncio
async def test_apply_quick_craft_keeps_marker_when_craft_fails():
    with patch(
        "cogs.mining.workshop.db.get_last_broken",
        new_callable=AsyncMock,
        return_value="torch",
    ), patch(
        "cogs.mining.workshop.load_recipes",
        return_value={"torch": {"wood": 2}},
    ), patch(
        "cogs.mining.workshop.db.get_mining_inventory",
        new_callable=AsyncMock,
        return_value={},  # no materials
    ), patch(
        "cogs.mining.workshop.db.set_last_broken",
        new_callable=AsyncMock,
    ) as mock_marker:
        result = await workshop.apply_quick_craft(1, 7)
    assert not result.ok
    mock_marker.assert_not_awaited()  # still re-offerable next time


@pytest.mark.asyncio
async def test_apply_quick_craft_without_marker_is_a_friendly_noop():
    with patch(
        "cogs.mining.workshop.db.get_last_broken",
        new_callable=AsyncMock,
        return_value=None,
    ):
        result = await workshop.apply_quick_craft(1, 7)
    assert not result.ok
    assert isinstance(result, market.TradeResult)
