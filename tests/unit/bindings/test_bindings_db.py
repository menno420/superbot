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
async def test_delete_active_bindings_for_guild_targets_active_table(_mock_pool):
    """delete_active_bindings_for_guild deletes ONLY from subsystem_bindings.

    Phase 2 retention policy: audit rows MUST survive guild teardown so
    the historical trail is preserved.  This test guards against a
    regression that would re-introduce audit deletion via this primitive.
    """
    _mock_pool.execute.return_value = "DELETE 3"
    deleted = await bindings_db.delete_active_bindings_for_guild(42)
    sql, *args = _mock_pool.execute.await_args.args
    assert "DELETE FROM subsystem_bindings" in sql
    assert "binding_audit_log" not in sql
    assert args == [42]
    assert deleted == 3


@pytest.mark.asyncio
async def test_delete_active_bindings_for_guild_handles_zero_rows(_mock_pool):
    _mock_pool.execute.return_value = "DELETE 0"
    assert await bindings_db.delete_active_bindings_for_guild(42) == 0


@pytest.mark.asyncio
async def test_delete_active_bindings_for_guild_handles_unexpected_status(_mock_pool):
    _mock_pool.execute.return_value = "unexpected"
    assert await bindings_db.delete_active_bindings_for_guild(42) == 0


@pytest.mark.asyncio
async def test_purge_binding_audit_for_guild_targets_audit_table(_mock_pool):
    """purge_binding_audit_for_guild deletes ONLY from binding_audit_log.

    This is the forensic/GDPR primitive — explicitly NOT wired into
    guild_lifecycle.teardown.  Kept separate so the active-row delete in
    teardown can't accidentally cascade to audit data.
    """
    _mock_pool.execute.return_value = "DELETE 7"
    deleted = await bindings_db.purge_binding_audit_for_guild(42)
    sql, *args = _mock_pool.execute.await_args.args
    assert "DELETE FROM binding_audit_log" in sql
    assert "subsystem_bindings" not in sql
    assert args == [42]
    assert deleted == 7


@pytest.mark.asyncio
async def test_legacy_delete_for_guild_removed():
    """The combined delete_for_guild primitive is intentionally gone.

    Splitting active-row delete from audit purge is a binding retention
    guarantee; restoring a combined primitive would re-open the silent
    audit-deletion path.
    """
    assert not hasattr(bindings_db, "delete_for_guild")


@pytest.mark.asyncio
async def test_get_audit_count(_mock_pool):
    _mock_pool.fetchrow.return_value = {"n": 7}
    assert await bindings_db.get_audit_count(1) == 7


@pytest.mark.asyncio
async def test_get_audit_count_zero(_mock_pool):
    _mock_pool.fetchrow.return_value = None
    assert await bindings_db.get_audit_count(1) == 0
