"""``utils.db.runtime_lock`` CRUD tests.

Mocks the asyncpg pool and asserts each primitive issues the expected
SQL with the expected parameters. Mirrors the mocking pattern used in
``tests/unit/db/test_setup_session.py``.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from utils.db import runtime_lock as rl_db


def _conn_ctx(conn):
    """Build an async-context-manager that yields ``conn``."""
    ctx = MagicMock()

    async def _enter(*_a, **_kw):
        return conn

    async def _exit(*_a, **_kw):
        return False

    ctx.__aenter__ = _enter
    ctx.__aexit__ = _exit
    return ctx


@pytest.fixture
def _mock_pool():
    """Patch the module's pool dependency with an AsyncMock-driven stub."""
    pool_mock = MagicMock()
    pool_mock.execute = AsyncMock()
    pool_mock.fetchrow = AsyncMock()
    conn = MagicMock()
    conn.execute = AsyncMock()
    conn.fetchrow = AsyncMock()
    pool_mock.acquire = MagicMock(return_value=_conn_ctx(conn))
    with patch.object(rl_db, "pool") as pool_module:
        pool_module.get = MagicMock(return_value=pool_mock)
        yield pool_mock, conn


@pytest.mark.asyncio
async def test_try_acquire_inserts_row_when_table_empty(_mock_pool):
    pool_mock, conn = _mock_pool
    conn.fetchrow.return_value = None
    boot_id = uuid.uuid4()
    result = await rl_db.try_acquire(boot_id)
    assert result.acquired is True
    assert result.holder_boot_id == boot_id
    assert result.reason == "acquired"
    # Three execute calls: pg_advisory_lock, INSERT/UPSERT, pg_advisory_unlock.
    assert conn.execute.await_count == 3
    insert_sql = conn.execute.await_args_list[1].args[0]
    assert "INSERT INTO bot_runtime_lock" in insert_sql


@pytest.mark.asyncio
async def test_try_acquire_refuses_when_row_is_fresh(_mock_pool):
    pool_mock, conn = _mock_pool
    held_by = uuid.uuid4()
    conn.fetchrow.return_value = {
        "boot_id": held_by,
        "heartbeat_at": "2026-05-20T00:00:00+00:00",
        "age_seconds": 5.0,  # well within DEFAULT_STALE_AFTER_SECONDS
    }
    new_boot = uuid.uuid4()
    result = await rl_db.try_acquire(new_boot)
    assert result.acquired is False
    assert result.holder_boot_id == held_by
    assert result.reason == "row_fresh"
    # advisory_lock + advisory_unlock; no INSERT.
    inserts = [
        call for call in conn.execute.await_args_list if "INSERT" in call.args[0]
    ]
    assert inserts == []


@pytest.mark.asyncio
async def test_try_acquire_reclaims_stale_row(_mock_pool):
    pool_mock, conn = _mock_pool
    held_by = uuid.uuid4()
    conn.fetchrow.return_value = {
        "boot_id": held_by,
        "heartbeat_at": "2026-05-19T23:00:00+00:00",
        "age_seconds": 3600.0,  # past the 90 s TTL
    }
    new_boot = uuid.uuid4()
    result = await rl_db.try_acquire(new_boot)
    assert result.acquired is True
    assert result.holder_boot_id == new_boot
    # Expected: advisory_lock, INSERT/UPSERT, advisory_unlock.
    inserts = [
        call for call in conn.execute.await_args_list if "INSERT" in call.args[0]
    ]
    assert len(inserts) == 1


@pytest.mark.asyncio
async def test_try_acquire_releases_advisory_lock_on_refusal(_mock_pool):
    pool_mock, conn = _mock_pool
    conn.fetchrow.return_value = {
        "boot_id": uuid.uuid4(),
        "heartbeat_at": "2026-05-20T00:00:00+00:00",
        "age_seconds": 1.0,
    }
    await rl_db.try_acquire(uuid.uuid4())
    unlock_calls = [
        call
        for call in conn.execute.await_args_list
        if "pg_advisory_unlock" in call.args[0]
    ]
    assert len(unlock_calls) == 1


@pytest.mark.asyncio
async def test_try_acquire_returns_acquired_when_existing_row_matches_boot(
    _mock_pool,
):
    """Re-acquire by the same boot is idempotent."""
    pool_mock, conn = _mock_pool
    boot_id = uuid.uuid4()
    conn.fetchrow.return_value = {
        "boot_id": boot_id,
        "heartbeat_at": "2026-05-20T00:00:00+00:00",
        "age_seconds": 1.0,
    }
    result = await rl_db.try_acquire(boot_id)
    assert result.acquired is True
    assert result.holder_boot_id == boot_id


@pytest.mark.asyncio
async def test_heartbeat_returns_true_on_update_one(_mock_pool):
    pool_mock, _conn = _mock_pool
    pool_mock.execute.return_value = "UPDATE 1"
    boot_id = uuid.uuid4()
    ok = await rl_db.heartbeat(boot_id)
    assert ok is True
    sql, *args = pool_mock.execute.await_args.args
    assert "UPDATE bot_runtime_lock" in sql
    assert args == ["discord_bot", boot_id]


@pytest.mark.asyncio
async def test_heartbeat_returns_false_when_no_row_updated(_mock_pool):
    pool_mock, _conn = _mock_pool
    pool_mock.execute.return_value = "UPDATE 0"
    ok = await rl_db.heartbeat(uuid.uuid4())
    assert ok is False


@pytest.mark.asyncio
async def test_release_deletes_only_own_row(_mock_pool):
    pool_mock, _conn = _mock_pool
    boot_id = uuid.uuid4()
    await rl_db.release(boot_id)
    sql, *args = pool_mock.execute.await_args.args
    assert "DELETE FROM bot_runtime_lock" in sql
    assert "AND boot_id   = $2" in sql
    assert args == ["discord_bot", boot_id]


@pytest.mark.asyncio
async def test_get_holder_returns_row_when_present(_mock_pool):
    pool_mock, _conn = _mock_pool
    boot_id = uuid.uuid4()
    pool_mock.fetchrow.return_value = {
        "lock_name": "discord_bot",
        "boot_id": boot_id,
        "acquired_at": None,
        "heartbeat_at": None,
    }
    row = await rl_db.get_holder()
    assert row is not None
    assert row["boot_id"] == boot_id


@pytest.mark.asyncio
async def test_get_holder_returns_none_when_absent(_mock_pool):
    pool_mock, _conn = _mock_pool
    pool_mock.fetchrow.return_value = None
    row = await rl_db.get_holder()
    assert row is None
