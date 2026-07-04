"""fishing_workflow curio layer — the coral → cosmetic-carving conversion.

Coral is the deepwater-only rare drop; ``craft_curio`` is its sole sink (a cosmetic
collection, never a bait, never sold). Mirrors the pearl-craft tests.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services import fishing_workflow as wf
from utils.fishing import curios as curios_mod

_IDOL = curios_mod.curio_by_key("coral idol")
_IDOL_CORAL = _IDOL.coral_cost


@pytest.mark.asyncio
async def test_craft_curio_debits_coral_and_grants_the_carving():
    sentinel_conn = MagicMock(name="conn")

    @asynccontextmanager
    async def _ctx():
        yield sentinel_conn

    with (
        patch.object(
            wf.db,
            "get_mining_inventory",
            AsyncMock(return_value={wf.CORAL_ITEM: _IDOL_CORAL + 1}),
        ),
        patch.object(wf.db, "transaction", _ctx),
        patch.object(wf.db, "update_mining_item", AsyncMock()) as write,
        patch.object(wf.economy_service, "debit_in_txn", AsyncMock()) as debit,
    ):
        result = await wf.craft_curio(99, 1, "coral idol")

    assert result.success is True
    assert result.curio is _IDOL
    # exactly the recipe's coral debited + exactly one curio granted, no coins
    write.assert_any_await("99", 1, wf.CORAL_ITEM, -_IDOL_CORAL, conn=sentinel_conn)
    write.assert_any_await("99", 1, _IDOL.item, 1, conn=sentinel_conn)
    assert write.await_count == 2
    debit.assert_not_awaited()


@pytest.mark.asyncio
async def test_craft_curio_without_enough_coral_writes_nothing():
    with (
        patch.object(
            wf.db,
            "get_mining_inventory",
            AsyncMock(return_value={wf.CORAL_ITEM: _IDOL_CORAL - 1}),
        ),
        patch.object(wf.db, "update_mining_item", AsyncMock()) as write,
    ):
        result = await wf.craft_curio(99, 1, "coral idol")

    assert result.success is False
    assert result.curio is None
    write.assert_not_awaited()  # no coral, no write


@pytest.mark.asyncio
async def test_craft_curio_rejects_an_unknown_curio_without_reading_inventory():
    with (
        patch.object(wf.db, "get_mining_inventory", AsyncMock()) as inv,
        patch.object(wf.db, "update_mining_item", AsyncMock()) as write,
    ):
        result = await wf.craft_curio(99, 1, "driftwood")

    assert result.success is False
    inv.assert_not_awaited()
    write.assert_not_awaited()
