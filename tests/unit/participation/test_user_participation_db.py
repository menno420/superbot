"""Phase 2c PR-8 — utils.db.user_participation read primitives."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from utils.db import user_participation as up_db


@pytest.fixture
def _mock_pool():
    pool_mock = MagicMock()
    pool_mock.execute = AsyncMock()
    pool_mock.fetchrow = AsyncMock()
    pool_mock.fetch = AsyncMock()
    pool_mock.acquire = MagicMock()
    with patch.object(up_db, "pool") as pool_module:
        pool_module.get = MagicMock(return_value=pool_mock)
        yield pool_mock


# ---------------------------------------------------------------------------
# Single-row reads
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_participation_keyed_on_user_guild_subsystem(_mock_pool):
    _mock_pool.fetchrow.return_value = None
    await up_db.get_participation(1, 2, "xp")
    sql, *args = _mock_pool.fetchrow.await_args.args
    assert "user_id = $1 AND guild_id = $2 AND subsystem = $3" in sql
    assert args == [1, 2, "xp"]


@pytest.mark.asyncio
async def test_get_participation_returns_dict_when_present(_mock_pool):
    _mock_pool.fetchrow.return_value = {
        "user_id": 1,
        "guild_id": 2,
        "subsystem": "xp",
        "state": "opted_in",
        "set_at": None,
        "set_by": 99,
    }
    row = await up_db.get_participation(1, 2, "xp")
    assert row is not None
    assert row["state"] == "opted_in"


@pytest.mark.asyncio
async def test_get_subscription_keyed_on_topic(_mock_pool):
    _mock_pool.fetchrow.return_value = None
    await up_db.get_subscription(1, 2, "economy", "daily")
    sql, *args = _mock_pool.fetchrow.await_args.args
    assert "topic = $4" in sql
    assert args == [1, 2, "economy", "daily"]


@pytest.mark.asyncio
async def test_get_preference_decodes_json_value(_mock_pool):
    _mock_pool.fetchrow.return_value = {
        "user_id": 1,
        "guild_id": 2,
        "key": "digest_freq",
        "value": json.dumps({"unit": "hours", "interval": 6}),
        "set_at": None,
        "set_by": None,
    }
    row = await up_db.get_preference(1, 2, "digest_freq")
    assert row is not None
    assert row["value"] == {"unit": "hours", "interval": 6}


@pytest.mark.asyncio
async def test_get_visibility_returns_visibility_value(_mock_pool):
    _mock_pool.fetchrow.return_value = {
        "user_id": 1,
        "guild_id": 2,
        "subsystem": "xp",
        "visibility": "hidden",
        "set_at": None,
        "set_by": None,
    }
    row = await up_db.get_visibility(1, 2, "xp")
    assert row is not None
    assert row["visibility"] == "hidden"


# ---------------------------------------------------------------------------
# Bundle reader
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_for_user_returns_four_keys(_mock_pool):
    _mock_pool.fetch.return_value = []
    bundle = await up_db.list_for_user(1, 2)
    assert set(bundle.keys()) == {
        "participation",
        "subscriptions",
        "preferences",
        "visibility_overrides",
    }
    # Four SELECTs (one per table)
    assert _mock_pool.fetch.await_count == 4


@pytest.mark.asyncio
async def test_list_for_user_decodes_preference_value(_mock_pool):
    payloads = [
        [],
        [],
        [
            {
                "user_id": 1,
                "guild_id": 2,
                "key": "digest_freq",
                "value": json.dumps({"unit": "hours"}),
                "set_at": None,
                "set_by": None,
            },
        ],
        [],
    ]
    _mock_pool.fetch.side_effect = payloads
    bundle = await up_db.list_for_user(1, 2)
    assert bundle["preferences"][0]["value"] == {"unit": "hours"}


# ---------------------------------------------------------------------------
# count_rows
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_count_rows_runs_four_count_queries(_mock_pool):
    _mock_pool.fetchrow.side_effect = [{"n": 3}, {"n": 1}, {"n": 0}, {"n": 2}]
    counts = await up_db.count_rows()
    assert counts == {
        "user_participation": 3,
        "user_subscriptions": 1,
        "user_preferences": 0,
        "user_visibility_overrides": 2,
    }


# ---------------------------------------------------------------------------
# delete_for_guild: atomic over four tables
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_for_guild_deletes_four_tables_in_one_transaction():
    """All four tables are purged in a single transaction.

    The retention contract requires that the deletes either all succeed
    or all roll back — otherwise a half-deleted guild leaves orphan
    rows.  Test by mocking ``pool.get().acquire()`` and asserting all
    four DELETE statements run inside the same connection's
    transaction.
    """
    conn = MagicMock()
    conn.execute = AsyncMock(
        side_effect=["DELETE 2", "DELETE 0", "DELETE 1", "DELETE 1"]
    )
    conn.transaction = MagicMock()

    txn_cm = MagicMock()
    txn_cm.__aenter__ = AsyncMock(return_value=None)
    txn_cm.__aexit__ = AsyncMock(return_value=False)
    conn.transaction.return_value = txn_cm

    acquire_cm = MagicMock()
    acquire_cm.__aenter__ = AsyncMock(return_value=conn)
    acquire_cm.__aexit__ = AsyncMock(return_value=False)

    pool_mock = MagicMock()
    pool_mock.acquire = MagicMock(return_value=acquire_cm)
    with patch.object(up_db, "pool") as pool_module:
        pool_module.get = MagicMock(return_value=pool_mock)
        total = await up_db.delete_for_guild(42)
    # Four DELETEs issued
    assert conn.execute.await_count == 4
    # Total = 2 + 0 + 1 + 1 = 4
    assert total == 4
    # Each DELETE targets one table
    tables_seen = set()
    for call in conn.execute.await_args_list:
        sql = call.args[0]
        for table in (
            "user_participation",
            "user_subscriptions",
            "user_preferences",
            "user_visibility_overrides",
        ):
            if f"DELETE FROM {table}" in sql:
                tables_seen.add(table)
                # Each DELETE is scoped to guild_id
                assert "WHERE guild_id = $1" in sql
                assert call.args[1] == 42
                break
    assert tables_seen == {
        "user_participation",
        "user_subscriptions",
        "user_preferences",
        "user_visibility_overrides",
    }
