"""Phase 2d PR-2 — utils.db.environment_tiers primitives."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from utils.db import environment_tiers as et_db


@pytest.fixture
def _mock_pool():
    pool_mock = MagicMock()
    pool_mock.execute = AsyncMock()
    pool_mock.fetchrow = AsyncMock()
    pool_mock.fetch = AsyncMock()
    with patch.object(et_db, "pool") as pool_module:
        pool_module.get = MagicMock(return_value=pool_mock)
        yield pool_mock


@pytest.mark.asyncio
async def test_get_tier_returns_string_when_row_present(_mock_pool):
    _mock_pool.fetchrow.return_value = {"tier": "canary"}
    assert await et_db.get_tier(42) == "canary"


@pytest.mark.asyncio
async def test_get_tier_returns_none_when_absent(_mock_pool):
    _mock_pool.fetchrow.return_value = None
    assert await et_db.get_tier(42) is None


@pytest.mark.asyncio
async def test_delete_for_guild_targets_correct_guild(_mock_pool):
    _mock_pool.execute.return_value = "DELETE 1"
    deleted = await et_db.delete_for_guild(42)
    sql, *args = _mock_pool.execute.await_args.args
    assert "environment_tiers" in sql
    assert "WHERE guild_id = $1" in sql
    assert args == [42]
    assert deleted == 1


@pytest.mark.asyncio
async def test_delete_for_guild_handles_zero_rows(_mock_pool):
    _mock_pool.execute.return_value = "DELETE 0"
    assert await et_db.delete_for_guild(42) == 0


@pytest.mark.asyncio
async def test_delete_for_guild_handles_unexpected_status(_mock_pool):
    _mock_pool.execute.return_value = "weird"
    assert await et_db.delete_for_guild(42) == 0


@pytest.mark.asyncio
async def test_list_for_diagnostics_returns_rows(_mock_pool):
    _mock_pool.fetch.return_value = [
        {"guild_id": 1, "tier": "owner_guild_only", "set_by": 99, "set_at": None},
        {"guild_id": 2, "tier": "canary", "set_by": 99, "set_at": None},
    ]
    rows = await et_db.list_for_diagnostics()
    assert len(rows) == 2
    assert rows[0]["tier"] == "owner_guild_only"
