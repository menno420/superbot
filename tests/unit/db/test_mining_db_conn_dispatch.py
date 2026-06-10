"""RS02 conn-dispatch pins for the mining DB primitives.

The workflow service composes these inside ONE ``db.transaction()``
(Q-0071), so a primitive given ``conn=`` must (a) run on that exact
connection and (b) NEVER open its own transaction — a nested/self
transaction would let a sub-leg commit independently of the workflow.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from utils.db.games import mining


@pytest.mark.asyncio
async def test_apply_inventory_deltas_with_conn_never_self_transacts():
    conn = MagicMock(name="workflow_conn")
    conn.execute = AsyncMock()
    with patch("utils.db.games.mining.pool.get") as mock_get:
        await mining.apply_inventory_deltas(
            "1",
            99,
            {"wood": -2, "pickaxe": 1},
            conn=conn,
        )
    # The pool is never touched and no transaction is opened — the caller
    # owns commit/rollback.
    mock_get.assert_not_called()
    conn.transaction.assert_not_called()
    assert conn.execute.await_count == 2


@pytest.mark.asyncio
async def test_apply_inventory_deltas_without_conn_owns_a_transaction():
    """The standalone path keeps its own atomicity (the pre-RS02 contract)."""
    conn = MagicMock(name="own_conn")
    conn.execute = AsyncMock()
    txn_cm = AsyncMock()
    txn_cm.__aenter__ = AsyncMock(return_value=None)
    txn_cm.__aexit__ = AsyncMock(return_value=None)
    conn.transaction = MagicMock(return_value=txn_cm)
    acquire_cm = AsyncMock()
    acquire_cm.__aenter__ = AsyncMock(return_value=conn)
    acquire_cm.__aexit__ = AsyncMock(return_value=None)
    fake_pool = MagicMock()
    fake_pool.acquire = MagicMock(return_value=acquire_cm)

    with patch("utils.db.games.mining.pool.get", return_value=fake_pool):
        await mining.apply_inventory_deltas("1", 99, {"wood": -2})
    conn.transaction.assert_called_once()
    conn.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_write_primitives_dispatch_conn_through_pool_helpers():
    sentinel = MagicMock(name="conn")
    with patch(
        "utils.db.games.mining.pool.execute",
        new_callable=AsyncMock,
    ) as ex:
        await mining.update_mining_item("1", 99, "wood", 1, conn=sentinel)
    assert ex.await_args.kwargs["conn"] is sentinel

    from utils.db.games import mining_equipment, mining_gear_wear, mining_player_state

    with patch(
        "utils.db.games.mining_gear_wear.pool.execute",
        new_callable=AsyncMock,
    ) as ex:
        await mining_gear_wear.clear_gear_wear("1", 99, "pickaxe", conn=sentinel)
    assert ex.await_args.kwargs["conn"] is sentinel

    with patch(
        "utils.db.games.mining_equipment.pool.execute",
        new_callable=AsyncMock,
    ) as ex:
        await mining_equipment.equip_item("1", 99, "tool", "pickaxe", conn=sentinel)
    assert ex.await_args.kwargs["conn"] is sentinel

    with patch(
        "utils.db.games.mining_player_state.pool.execute",
        new_callable=AsyncMock,
    ) as ex:
        await mining_player_state.set_last_broken("1", 99, None, conn=sentinel)
    assert ex.await_args.kwargs["conn"] is sentinel
