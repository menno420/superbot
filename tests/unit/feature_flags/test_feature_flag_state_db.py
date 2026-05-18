"""Phase 2d PR-2 — utils.db.feature_flag_state primitives.

Mocks the asyncpg pool and asserts each primitive issues the expected
SQL with the expected parameters (mirrors
``tests/unit/bindings/test_bindings_db.py``).
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from utils.db import feature_flag_state as ff_db


@pytest.fixture
def _mock_pool():
    pool_mock = MagicMock()
    pool_mock.execute = AsyncMock()
    pool_mock.fetchrow = AsyncMock()
    pool_mock.fetch = AsyncMock()
    with patch.object(ff_db, "pool") as pool_module:
        pool_module.get = MagicMock(return_value=pool_mock)
        yield pool_mock


# ---------------------------------------------------------------------------
# get_global_override
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_global_override_returns_dict_when_row_present(_mock_pool):
    now = datetime.now(timezone.utc)
    _mock_pool.fetchrow.return_value = {
        "flag_name": "bindings.primary",
        "state": "canary",
        "rollout_percent": 25,
        "set_by": 99,
        "set_at": now,
    }
    row = await ff_db.get_global_override("bindings.primary")
    assert row == {
        "flag_name": "bindings.primary",
        "state": "canary",
        "rollout_percent": 25,
        "set_by": 99,
        "set_at": now,
    }
    sql, *args = _mock_pool.fetchrow.await_args.args
    assert "feature_flag_global_overrides" in sql
    assert args == ["bindings.primary"]


@pytest.mark.asyncio
async def test_get_global_override_returns_none(_mock_pool):
    _mock_pool.fetchrow.return_value = None
    assert await ff_db.get_global_override("missing.flag") is None


# ---------------------------------------------------------------------------
# get_guild_override
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_guild_override_scoped_to_guild(_mock_pool):
    _mock_pool.fetchrow.return_value = None
    await ff_db.get_guild_override("bindings.primary", 42)
    sql, *args = _mock_pool.fetchrow.await_args.args
    assert "feature_flag_guild_overrides" in sql
    assert "guild_id = $2" in sql
    assert args == ["bindings.primary", 42]


# ---------------------------------------------------------------------------
# delete_for_guild — preserves global rows
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_for_guild_targets_only_guild_overrides(_mock_pool):
    """Phase 2 retention: the GLOBAL override row must survive guild leave.

    This test guards against a regression that would re-introduce a
    cascade or accidentally touch ``feature_flag_global_overrides``.
    """
    _mock_pool.execute.return_value = "DELETE 4"
    deleted = await ff_db.delete_for_guild(42)
    sql, *args = _mock_pool.execute.await_args.args
    assert "feature_flag_guild_overrides" in sql
    assert "feature_flag_global_overrides" not in sql
    assert args == [42]
    assert deleted == 4


@pytest.mark.asyncio
async def test_delete_for_guild_handles_zero_rows(_mock_pool):
    _mock_pool.execute.return_value = "DELETE 0"
    assert await ff_db.delete_for_guild(42) == 0


@pytest.mark.asyncio
async def test_delete_for_guild_handles_unexpected_status(_mock_pool):
    _mock_pool.execute.return_value = "unexpected"
    assert await ff_db.delete_for_guild(42) == 0


# ---------------------------------------------------------------------------
# list helpers (used by diagnostics)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_global_overrides_returns_list(_mock_pool):
    _mock_pool.fetch.return_value = [
        {
            "flag_name": "bindings.primary",
            "state": "off",
            "rollout_percent": None,
            "set_by": None,
            "set_at": datetime.now(timezone.utc),
        },
    ]
    result = await ff_db.list_global_overrides()
    assert len(result) == 1
    assert result[0]["flag_name"] == "bindings.primary"


@pytest.mark.asyncio
async def test_list_guild_overrides_scoped_to_guild(_mock_pool):
    _mock_pool.fetch.return_value = []
    await ff_db.list_guild_overrides(42)
    sql, *args = _mock_pool.fetch.await_args.args
    assert "guild_id = $1" in sql
    assert args == [42]
