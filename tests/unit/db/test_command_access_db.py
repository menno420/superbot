"""PR-1 — guild command-access DB primitives.

Mocks the asyncpg pool and asserts each primitive issues the expected
SQL with the expected parameters.  Covers:

* policy upsert + read
* allowed-channel single insert / single delete (idempotent)
* allowed-channel atomic bulk replace (DELETE + executemany inside a
  ``conn.transaction()``)
* ``forget_guild`` sweeps the parent row (CASCADE handles the rest)
* mode validation rejects unknown modes
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from utils.db import command_access as db


@pytest.fixture
def _mock_pool():
    """Returns a pool stub whose .get() yields an object with execute /
    fetchrow / fetch AsyncMocks — the read-side primitives use these
    directly.  Tests that need conn.acquire()/transaction() patch
    pool.get separately so the connection-side mocks can be inspected.
    """
    pool_mock = MagicMock()
    pool_mock.execute = AsyncMock()
    pool_mock.fetchrow = AsyncMock()
    pool_mock.fetch = AsyncMock()
    with patch.object(db, "pool") as pool_module:
        pool_module.get = MagicMock(return_value=pool_mock)
        yield pool_mock


def _build_conn_pool_stub():
    """Build the acquire()/transaction() async-context-manager chain
    used by ``replace_allowed_channels``.  Returns (pool_stub, conn).
    """
    conn = MagicMock()
    conn.execute = AsyncMock()
    conn.executemany = AsyncMock()
    tx_cm = AsyncMock()
    tx_cm.__aenter__ = AsyncMock(return_value=None)
    tx_cm.__aexit__ = AsyncMock(return_value=None)
    conn.transaction = MagicMock(return_value=tx_cm)
    acquire_cm = AsyncMock()
    acquire_cm.__aenter__ = AsyncMock(return_value=conn)
    acquire_cm.__aexit__ = AsyncMock(return_value=None)
    pool_stub = MagicMock(acquire=MagicMock(return_value=acquire_cm))
    return pool_stub, conn


# ---------------------------------------------------------------------------
# Constants / validation
# ---------------------------------------------------------------------------


def test_known_modes_exposes_three_modes():
    assert db.KNOWN_MODES == frozenset(
        {"all_channels", "selected_channels", "disabled_except_bootstrap"},
    )


@pytest.mark.asyncio
async def test_set_mode_rejects_unknown_mode(_mock_pool):
    with pytest.raises(ValueError):
        await db.set_mode(guild_id=10, mode="garbage", updated_by=99)
    _mock_pool.execute.assert_not_awaited()


# ---------------------------------------------------------------------------
# Policy row — read / upsert
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_policy_returns_none_when_absent(_mock_pool):
    _mock_pool.fetchrow.return_value = None
    assert await db.get_policy(10) is None
    sql, *args = _mock_pool.fetchrow.await_args.args
    assert "FROM guild_command_access_policy" in sql
    assert args == [10]


@pytest.mark.asyncio
async def test_get_policy_returns_row_dict(_mock_pool):
    _mock_pool.fetchrow.return_value = {
        "mode": "selected_channels",
        "updated_by": 99,
        "updated_at": None,
        "created_at": None,
    }
    row = await db.get_policy(10)
    assert row is not None
    assert row["mode"] == "selected_channels"
    assert row["updated_by"] == 99


@pytest.mark.asyncio
async def test_set_mode_issues_upsert_with_correct_params(_mock_pool):
    await db.set_mode(guild_id=10, mode="all_channels", updated_by=99)
    sql, *args = _mock_pool.execute.await_args.args
    assert "INSERT INTO guild_command_access_policy" in sql
    assert "ON CONFLICT (guild_id)" in sql
    # Only mode / updated_by / updated_at move on conflict — created_at
    # is preserved.  Pin both that and the absence of created_at in
    # the UPDATE clause.
    assert "mode       = EXCLUDED.mode" in sql
    assert "updated_by = EXCLUDED.updated_by" in sql
    assert "updated_at = NOW()" in sql
    assert "created_at" not in sql.split("DO UPDATE SET")[1]
    assert args == [10, "all_channels", 99]


@pytest.mark.asyncio
async def test_set_mode_accepts_null_updated_by(_mock_pool):
    """Migration-installed rows pass updated_by=None."""
    await db.set_mode(guild_id=10, mode="disabled_except_bootstrap", updated_by=None)
    _, _, _, updated_by = _mock_pool.execute.await_args.args
    assert updated_by is None


# ---------------------------------------------------------------------------
# Allowed channels — list / add / remove
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_allowed_channels_returns_sorted_ids(_mock_pool):
    _mock_pool.fetch.return_value = [
        {"channel_id": 100},
        {"channel_id": 200},
        {"channel_id": 300},
    ]
    ids = await db.list_allowed_channels(10)
    assert ids == [100, 200, 300]
    sql, *args = _mock_pool.fetch.await_args.args
    assert "FROM guild_command_access_channels" in sql
    assert "ORDER BY channel_id" in sql
    assert args == [10]


@pytest.mark.asyncio
async def test_list_allowed_channels_returns_empty_when_no_rows(_mock_pool):
    _mock_pool.fetch.return_value = []
    assert await db.list_allowed_channels(10) == []


@pytest.mark.asyncio
async def test_add_allowed_channel_is_idempotent(_mock_pool):
    await db.add_allowed_channel(guild_id=10, channel_id=555, created_by=99)
    sql, *args = _mock_pool.execute.await_args.args
    assert "INSERT INTO guild_command_access_channels" in sql
    assert "ON CONFLICT (guild_id, channel_id) DO NOTHING" in sql
    assert args == [10, 555, 99]


@pytest.mark.asyncio
async def test_remove_allowed_channel_deletes_single_row(_mock_pool):
    await db.remove_allowed_channel(guild_id=10, channel_id=555)
    sql, *args = _mock_pool.execute.await_args.args
    assert "DELETE FROM guild_command_access_channels" in sql
    assert "guild_id = $1 AND channel_id = $2" in sql
    assert args == [10, 555]


# ---------------------------------------------------------------------------
# Allowed channels — atomic bulk replace
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_replace_allowed_channels_runs_delete_and_insert_in_txn():
    pool_stub, conn = _build_conn_pool_stub()
    with patch.object(db, "pool") as pool_module:
        pool_module.get = MagicMock(return_value=pool_stub)
        await db.replace_allowed_channels(
            guild_id=10,
            channel_ids=[300, 100, 200],
            created_by=99,
        )

    # Inside the transaction: a single DELETE scoped to the guild plus
    # one executemany carrying every (guild_id, channel_id, created_by)
    # tuple in stable sort order.
    conn.transaction.assert_called_once()
    delete_sql, *del_args = conn.execute.await_args.args
    assert "DELETE FROM guild_command_access_channels" in delete_sql
    assert "WHERE guild_id = $1" in delete_sql
    assert del_args == [10]
    conn.executemany.assert_awaited_once()
    insert_sql, payload = conn.executemany.await_args.args
    assert "INSERT INTO guild_command_access_channels" in insert_sql
    # Sorted + deduped on the way in.
    assert payload == [(10, 100, 99), (10, 200, 99), (10, 300, 99)]


@pytest.mark.asyncio
async def test_replace_allowed_channels_dedupes_input():
    pool_stub, conn = _build_conn_pool_stub()
    with patch.object(db, "pool") as pool_module:
        pool_module.get = MagicMock(return_value=pool_stub)
        await db.replace_allowed_channels(
            guild_id=10,
            channel_ids=[555, 555, 100, 555],
            created_by=99,
        )

    _, payload = conn.executemany.await_args.args
    assert payload == [(10, 100, 99), (10, 555, 99)]


@pytest.mark.asyncio
async def test_replace_allowed_channels_empty_skips_insert():
    """An empty desired set is a "reset to no allowed channels" — the
    DELETE still runs, but ``executemany`` must not be called with an
    empty payload (asyncpg raises on empty executemany).
    """
    pool_stub, conn = _build_conn_pool_stub()
    with patch.object(db, "pool") as pool_module:
        pool_module.get = MagicMock(return_value=pool_stub)
        await db.replace_allowed_channels(
            guild_id=10,
            channel_ids=[],
            created_by=99,
        )

    conn.execute.assert_awaited_once()
    conn.executemany.assert_not_called()


# ---------------------------------------------------------------------------
# Guild teardown
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_forget_guild_deletes_parent_row(_mock_pool):
    """CASCADE on the child table handles the rest, so the primitive
    only needs to drop the policy row.
    """
    await db.forget_guild(guild_id=10)
    sql, *args = _mock_pool.execute.await_args.args
    assert "DELETE FROM guild_command_access_policy" in sql
    assert args == [10]
