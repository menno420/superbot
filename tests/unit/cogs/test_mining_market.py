"""Tests for cogs.mining.market — sell/buy prices + audited orchestration.

The orchestration tests mock the economy seam and the mining CRUD so they pin
the *contract* (coins move through economy_service; the inventory side is
direct-lane; failure orderings never mint free coins or grant free items)
without a real DB.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from cogs.mining import market
from utils.mining import items
from services.economy_service import InsufficientFundsError

# ---------------------------------------------------------------------------
# Pure pricing
# ---------------------------------------------------------------------------


def test_sell_price_resources_reuse_item_value():
    assert market.sell_price("diamond") == items.item_value("diamond")
    assert market.sell_price("stone") == items.item_value("stone")


def test_only_resources_are_sellable():
    assert market.sell_price("pickaxe") is None  # a tool
    assert market.sell_price("iron sword") is None  # combat gear
    assert market.sell_price("stone hut") is None  # structure


def test_buy_price_and_shop_listing_sorted():
    assert market.buy_price("iron sword") == market.GEAR_SHOP["iron sword"]
    assert market.buy_price("not a real item") is None
    listing = market.shop_listing()
    prices = [p for _, p in listing]
    assert prices == sorted(prices)  # ascending by price


def test_sellable_inventory_filters_and_orders():
    inv = {"diamond": 2, "stone": 5, "pickaxe": 1, "iron sword": 1, "gold": 0}
    rows = market.sellable_inventory(inv)
    names = [n for n, _, _ in rows]
    assert "pickaxe" not in names  # tool
    assert "iron sword" not in names  # gear
    assert "gold" not in names  # qty 0
    assert names[0] == "diamond"  # highest unit price first


def test_total_sale_value_sums_only_resources():
    inv = {"diamond": 2, "stone": 3, "pickaxe": 1}
    expected = items.item_value("diamond") * 2 + items.item_value("stone") * 3
    assert market.total_sale_value(inv) == expected


# ---------------------------------------------------------------------------
# Orchestration — sell (faucet)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_sell_removes_ore_then_credits_coins():
    with patch(
        "cogs.mining.market.db.get_mining_inventory",
        new_callable=AsyncMock,
        return_value={"diamond": 5},
    ), patch(
        "cogs.mining.market.db.update_mining_item",
        new_callable=AsyncMock,
    ) as mock_remove, patch(
        "cogs.mining.market.economy_service.credit",
        new_callable=AsyncMock,
        return_value=999,
    ) as mock_credit:
        result = await market.apply_sell(123, 7, "diamond", 3)
    coins = items.item_value("diamond") * 3
    assert result.ok
    mock_remove.assert_awaited_once_with("123", 7, "diamond", -3)
    args, kwargs = mock_credit.await_args
    assert args[2] == coins
    assert kwargs["reason"] == market.SELL_REASON
    assert result.coins_delta == coins
    assert result.new_balance == 999


@pytest.mark.asyncio
async def test_apply_sell_rejects_nonsellable_before_any_io():
    result = await market.apply_sell(1, 1, "pickaxe", 1)
    assert not result.ok
    assert "can't sell" in result.message.lower()


@pytest.mark.asyncio
async def test_apply_sell_rejects_insufficient_quantity_without_crediting():
    with patch(
        "cogs.mining.market.db.get_mining_inventory",
        new_callable=AsyncMock,
        return_value={"iron": 2},
    ), patch(
        "cogs.mining.market.economy_service.credit",
        new_callable=AsyncMock,
    ) as mock_credit:
        result = await market.apply_sell(1, 1, "iron", 5)
    assert not result.ok
    mock_credit.assert_not_awaited()  # never mint coins for ore you don't have


@pytest.mark.asyncio
async def test_apply_sell_all_sells_only_resources_in_one_credit():
    with patch(
        "cogs.mining.market.db.get_mining_inventory",
        new_callable=AsyncMock,
        return_value={"stone": 4, "diamond": 1, "pickaxe": 1},
    ), patch(
        "cogs.mining.market.db.update_mining_item",
        new_callable=AsyncMock,
    ) as mock_remove, patch(
        "cogs.mining.market.economy_service.credit",
        new_callable=AsyncMock,
        return_value=500,
    ) as mock_credit:
        result = await market.apply_sell_all(1, 1)
    assert result.ok
    removed = {call.args[2] for call in mock_remove.await_args_list}
    assert "pickaxe" not in removed  # tools are never sold
    assert {"stone", "diamond"} <= removed
    mock_credit.assert_awaited_once()


@pytest.mark.asyncio
async def test_apply_sell_all_empty_inventory():
    with patch(
        "cogs.mining.market.db.get_mining_inventory",
        new_callable=AsyncMock,
        return_value={"pickaxe": 1},  # only non-sellable items
    ), patch(
        "cogs.mining.market.economy_service.credit",
        new_callable=AsyncMock,
    ) as mock_credit:
        result = await market.apply_sell_all(1, 1)
    assert not result.ok
    mock_credit.assert_not_awaited()


# ---------------------------------------------------------------------------
# Orchestration — buy (sink)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_buy_debits_then_grants_item():
    with patch(
        "cogs.mining.market.economy_service.debit",
        new_callable=AsyncMock,
        return_value=40,
    ) as mock_debit, patch(
        "cogs.mining.market.db.update_mining_item",
        new_callable=AsyncMock,
    ) as mock_add:
        result = await market.apply_buy(123, 7, "iron sword")
    assert result.ok
    args, kwargs = mock_debit.await_args
    assert args[2] == market.GEAR_SHOP["iron sword"]
    assert kwargs["reason"] == market.BUY_REASON
    mock_add.assert_awaited_once_with("123", 7, "iron sword", 1)


@pytest.mark.asyncio
async def test_apply_buy_insufficient_funds_grants_nothing():
    with patch(
        "cogs.mining.market.economy_service.debit",
        new_callable=AsyncMock,
        side_effect=InsufficientFundsError("nope"),
    ), patch(
        "cogs.mining.market.db.get_coins",
        new_callable=AsyncMock,
        return_value=5,
    ), patch(
        "cogs.mining.market.db.update_mining_item",
        new_callable=AsyncMock,
    ) as mock_add:
        result = await market.apply_buy(1, 1, "armor")
    assert not result.ok
    mock_add.assert_not_awaited()  # no free item when you can't pay


@pytest.mark.asyncio
async def test_apply_buy_unknown_item_before_any_io():
    result = await market.apply_buy(1, 1, "spaceship")
    assert not result.ok
    assert "isn't for sale" in result.message.lower()
