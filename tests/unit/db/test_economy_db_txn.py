"""Transaction-aware DB primitives (RS01 / Q-0071 plumbing).

Pins the SQL shapes that make the purchase workflow race-free —
``try_debit_coins`` (conditional UPDATE), ``try_grant_unique_item``
(conditional upsert) — and the conn-dispatch plumbing: a primitive given
``conn=`` must run on that connection, never re-acquire the pool, so a
workflow-owned transaction can never commit a sub-leg independently.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from utils.db import economy, inventory, pool

# ---------------------------------------------------------------------------
# SQL-shape pins
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_try_debit_coins_is_one_conditional_update():
    with patch(
        "utils.db.economy.pool.fetchone",
        new_callable=AsyncMock,
        return_value={"coins": 7},
    ) as mock_fetch:
        result = await economy.try_debit_coins(1, 99, 5)
    assert result == 7
    query, params = mock_fetch.await_args.args
    flat = " ".join(query.split())
    assert "UPDATE xp SET coins = xp.coins - $3" in flat
    assert "coins >= $3" in flat
    assert "RETURNING coins" in flat
    assert params == (1, 99, 5)


@pytest.mark.asyncio
async def test_try_debit_coins_returns_none_when_unaffordable():
    with patch(
        "utils.db.economy.pool.fetchone",
        new_callable=AsyncMock,
        return_value=None,
    ):
        assert await economy.try_debit_coins(1, 99, 5) is None


@pytest.mark.asyncio
async def test_credit_coins_upserts_with_returning():
    with patch(
        "utils.db.economy.pool.fetchone",
        new_callable=AsyncMock,
        return_value={"coins": 12},
    ) as mock_fetch:
        result = await economy.credit_coins(1, 99, 5)
    assert result == 12
    query, params = mock_fetch.await_args.args
    flat = " ".join(query.split())
    assert "ON CONFLICT (user_id, guild_id) DO UPDATE" in flat
    assert "GREATEST(0, xp.coins + $3)" in flat
    assert "RETURNING coins" in flat
    assert params == (1, 99, 5)


@pytest.mark.asyncio
async def test_insert_economy_audit_appends_one_row():
    with patch(
        "utils.db.economy.pool.execute",
        new_callable=AsyncMock,
    ) as mock_exec:
        await economy.insert_economy_audit(99, 1, None, -5, 7, "shop:car")
    query, params = mock_exec.await_args.args
    assert "INSERT INTO economy_audit_log" in query
    assert params == (99, 1, None, -5, 7, "shop:car")


@pytest.mark.asyncio
async def test_try_grant_unique_item_grants_when_not_owned():
    with patch(
        "utils.db.inventory.pool.fetchone",
        new_callable=AsyncMock,
        return_value={"item_name": "car"},
    ) as mock_fetch:
        assert await inventory.try_grant_unique_item(1, 99, "car") is True
    query, params = mock_fetch.await_args.args
    flat = " ".join(query.split())
    # Conditional upsert: insert when missing, only revive a stale
    # zero-quantity row — an owned row (> 0) returns nothing.
    assert "ON CONFLICT (user_id, guild_id, item_name)" in flat
    assert "WHERE inventory.quantity <= 0" in flat
    assert "RETURNING item_name" in flat
    assert params == (1, 99, "car")


@pytest.mark.asyncio
async def test_try_grant_unique_item_already_owned_returns_false():
    with patch(
        "utils.db.inventory.pool.fetchone",
        new_callable=AsyncMock,
        return_value=None,
    ):
        assert await inventory.try_grant_unique_item(1, 99, "car") is False


# ---------------------------------------------------------------------------
# Conn-dispatch plumbing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pool_primitives_dispatch_to_conn_not_pool():
    conn = MagicMock()
    conn.fetchrow = AsyncMock(return_value=None)
    conn.fetch = AsyncMock(return_value=[])
    conn.execute = AsyncMock()
    with patch("utils.db.pool.get") as mock_get:
        await pool.fetchone("SELECT 1 FROM xp", (), conn=conn)
        await pool.fetchall("SELECT 1 FROM xp", (), conn=conn)
        await pool.execute("SELECT 1 FROM xp", (), conn=conn)
    mock_get.assert_not_called()
    conn.fetchrow.assert_awaited_once()
    conn.fetch.assert_awaited_once()
    conn.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_conn_aware_primitives_pass_conn_through():
    sentinel = MagicMock(name="conn")
    with patch(
        "utils.db.economy.pool.fetchone",
        new_callable=AsyncMock,
        return_value=None,
    ) as f:
        await economy.try_debit_coins(1, 99, 5, conn=sentinel)
    assert f.await_args.kwargs["conn"] is sentinel

    with patch(
        "utils.db.inventory.pool.fetchone",
        new_callable=AsyncMock,
        return_value=None,
    ) as f2:
        await inventory.try_grant_unique_item(1, 99, "car", conn=sentinel)
    assert f2.await_args.kwargs["conn"] is sentinel


@pytest.mark.asyncio
async def test_transaction_yields_the_acquired_connection_inside_txn():
    conn = MagicMock(name="conn")
    txn_state: list[str] = []

    @asynccontextmanager
    async def _txn():
        txn_state.append("enter")
        yield
        txn_state.append("exit")

    conn.transaction = MagicMock(side_effect=lambda: _txn())

    @asynccontextmanager
    async def _acquire():
        yield conn

    fake_pool = MagicMock()
    fake_pool.acquire = MagicMock(side_effect=lambda: _acquire())

    with patch("utils.db.pool.get", return_value=fake_pool):
        async with pool.transaction() as got:
            assert got is conn
            assert txn_state == ["enter"]
    assert txn_state == ["enter", "exit"]
