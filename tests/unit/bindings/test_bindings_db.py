"""Phase 2b unit tests — utils.db.bindings CRUD primitives.

Mocks the asyncpg pool and asserts each primitive issues the expected
SQL with the expected parameters (mirrors the pattern from
tests/unit/resources/test_resource_cache.py).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from utils.db import bindings as bindings_db


@pytest.fixture
def _mock_pool():
    """Patch ``utils.db.pool.get()`` for read primitives."""
    pool_mock = MagicMock()
    pool_mock.execute = AsyncMock()
    pool_mock.fetchrow = AsyncMock()
    pool_mock.fetch = AsyncMock()
    pool_mock.acquire = MagicMock()
    with patch.object(bindings_db, "pool") as pool_module:
        pool_module.get = MagicMock(return_value=pool_mock)
        yield pool_mock


# ---------------------------------------------------------------------------
# Read primitives
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_one_returns_dict_when_row_present(_mock_pool):
    _mock_pool.fetchrow.return_value = {
        "guild_id": 1,
        "subsystem": "xp",
        "binding_name": "announce_channel",
        "kind": "channel",
        "target_id": 42,
        "status": "bound",
        "last_validated_at": None,
        "last_updated_at": None,
        "version": 1,
    }
    row = await bindings_db.get_one(1, "xp", "announce_channel")
    assert row is not None
    assert row["target_id"] == 42
    assert row["status"] == "bound"


@pytest.mark.asyncio
async def test_get_one_returns_none_when_absent(_mock_pool):
    _mock_pool.fetchrow.return_value = None
    assert await bindings_db.get_one(1, "xp", "announce_channel") is None


@pytest.mark.asyncio
async def test_list_for_guild_unfiltered(_mock_pool):
    _mock_pool.fetch.return_value = []
    await bindings_db.list_for_guild(1)
    sql, *args = _mock_pool.fetch.await_args.args
    assert "WHERE guild_id = $1" in sql
    assert "AND subsystem" not in sql
    assert args == [1]


@pytest.mark.asyncio
async def test_list_for_guild_filtered_by_subsystem(_mock_pool):
    _mock_pool.fetch.return_value = []
    await bindings_db.list_for_guild(1, subsystem="xp")
    sql, *args = _mock_pool.fetch.await_args.args
    assert "subsystem = $2" in sql
    assert args == [1, "xp"]


@pytest.mark.asyncio
async def test_count_by_status_unfiltered(_mock_pool):
    _mock_pool.fetch.return_value = [
        {"status": "bound", "n": 5},
        {"status": "missing", "n": 2},
    ]
    result = await bindings_db.count_by_status(1)
    assert result == {"bound": 5, "missing": 2}


@pytest.mark.asyncio
async def test_count_by_status_filtered_by_subsystem(_mock_pool):
    _mock_pool.fetch.return_value = []
    await bindings_db.count_by_status(1, subsystem="xp")
    sql, *args = _mock_pool.fetch.await_args.args
    assert "subsystem = $2" in sql
    assert args == [1, "xp"]


@pytest.mark.asyncio
async def test_count_by_subsystem(_mock_pool):
    _mock_pool.fetch.return_value = [
        {"subsystem": "economy", "n": 1},
        {"subsystem": "xp", "n": 2},
    ]
    result = await bindings_db.count_by_subsystem(1)
    assert result == {"economy": 1, "xp": 2}


# ---------------------------------------------------------------------------
# Maintenance
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_for_guild_parses_combined_count():
    """delete_for_guild returns the parsed sum of both DELETE results."""
    conn_mock = MagicMock()
    conn_mock.execute = AsyncMock()
    # First execute (audit table) returns DELETE 7; second (bindings) DELETE 3
    conn_mock.execute.side_effect = ["DELETE 7", "DELETE 3"]
    conn_mock.transaction = MagicMock()

    transaction_cm = MagicMock()
    transaction_cm.__aenter__ = AsyncMock(return_value=None)
    transaction_cm.__aexit__ = AsyncMock(return_value=False)
    conn_mock.transaction.return_value = transaction_cm

    acquire_cm = MagicMock()
    acquire_cm.__aenter__ = AsyncMock(return_value=conn_mock)
    acquire_cm.__aexit__ = AsyncMock(return_value=False)

    pool_mock = MagicMock()
    pool_mock.acquire = MagicMock(return_value=acquire_cm)
    with patch.object(bindings_db, "pool") as pool_module:
        pool_module.get = MagicMock(return_value=pool_mock)
        deleted = await bindings_db.delete_for_guild(42)
    assert deleted == 10


@pytest.mark.asyncio
async def test_get_audit_count(_mock_pool):
    _mock_pool.fetchrow.return_value = {"n": 7}
    assert await bindings_db.get_audit_count(1) == 7


@pytest.mark.asyncio
async def test_get_audit_count_zero(_mock_pool):
    _mock_pool.fetchrow.return_value = None
    assert await bindings_db.get_audit_count(1) == 0
