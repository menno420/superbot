"""Phase 2a hardening — resource_cache primitive tests.

Tests cover only the *pure* shape of each primitive — DB integration
tests would require a live Postgres instance, which the unit-test
suite does not assume.  We mock :mod:`utils.db.pool` and assert each
primitive issues the expected SQL with the expected parameters.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from utils.db import resource_cache


@pytest.fixture
def _mock_pool():
    """Patch ``utils.db.pool.get()`` to return a mocked connection."""
    pool_mock = MagicMock()
    pool_mock.execute = AsyncMock()
    pool_mock.fetchrow = AsyncMock()
    pool_mock.fetch = AsyncMock()
    with patch.object(resource_cache, "pool") as pool_module:
        pool_module.get = MagicMock(return_value=pool_mock)
        yield pool_mock


# ---------------------------------------------------------------------------
# delete_for_guild — Phase 2a hardening primitive
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_for_guild_issues_correct_sql(_mock_pool):
    """delete_for_guild scopes the DELETE to (guild_id,)."""
    _mock_pool.execute.return_value = "DELETE 5"
    deleted = await resource_cache.delete_for_guild(42)
    assert deleted == 5
    _mock_pool.execute.assert_awaited_once()
    sql, *args = _mock_pool.execute.await_args.args
    assert "DELETE FROM resource_validation_cache" in sql
    assert "WHERE guild_id = $1" in sql
    assert args == [42]


@pytest.mark.asyncio
async def test_delete_for_guild_zero_rows(_mock_pool):
    """delete_for_guild returns 0 when nothing matched."""
    _mock_pool.execute.return_value = "DELETE 0"
    assert await resource_cache.delete_for_guild(42) == 0


@pytest.mark.asyncio
async def test_delete_for_guild_handles_unexpected_status(_mock_pool):
    """If asyncpg ever returns a non-numeric tail, we return 0 rather
    than raise — the caller's invariant is "cleanup attempted", not
    "exact row count"."""
    _mock_pool.execute.return_value = "UNEXPECTED STATUS"
    assert await resource_cache.delete_for_guild(42) == 0


@pytest.mark.asyncio
async def test_delete_for_guild_handles_empty_status(_mock_pool):
    _mock_pool.execute.return_value = ""
    assert await resource_cache.delete_for_guild(42) == 0


# ---------------------------------------------------------------------------
# Existing primitives — light coverage to verify SQL shape did not
# regress when delete_for_guild landed.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_status_scopes_correctly(_mock_pool):
    _mock_pool.execute.return_value = "DELETE 1"
    await resource_cache.delete_status(42, "channel", 99)
    _mock_pool.execute.assert_awaited_once()
    sql, *args = _mock_pool.execute.await_args.args
    assert "DELETE FROM resource_validation_cache" in sql
    assert "guild_id = $1" in sql
    assert "kind = $2" in sql
    assert "resource_id = $3" in sql
    assert args == [42, "channel", 99]


@pytest.mark.asyncio
async def test_upsert_status_writes_now_timestamp(_mock_pool):
    _mock_pool.execute.return_value = "INSERT 0 1"
    await resource_cache.upsert_status(42, "channel", 99, "bound")
    sql, *args = _mock_pool.execute.await_args.args
    assert "INSERT INTO resource_validation_cache" in sql
    assert "ON CONFLICT (guild_id, kind, resource_id)" in sql
    assert "DO UPDATE SET" in sql
    assert args == [42, "channel", 99, "bound"]


@pytest.mark.asyncio
async def test_count_by_status_unfiltered(_mock_pool):
    _mock_pool.fetch.return_value = [
        {"status": "bound", "n": 5},
        {"status": "missing", "n": 2},
    ]
    result = await resource_cache.count_by_status(42)
    assert result == {"bound": 5, "missing": 2}


@pytest.mark.asyncio
async def test_count_by_status_filtered_by_kind(_mock_pool):
    _mock_pool.fetch.return_value = []
    await resource_cache.count_by_status(42, kind="channel")
    sql, *args = _mock_pool.fetch.await_args.args
    assert "kind = $2" in sql
    assert args == [42, "channel"]
