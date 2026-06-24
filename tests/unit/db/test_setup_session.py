"""Phase 9e / Track 4 PR 8 — ``utils.db.setup_session`` CRUD tests.

Mocks the asyncpg pool and asserts each primitive issues the expected
SQL with the expected parameters (mirrors the pattern from
``tests/unit/bindings/test_bindings_db.py``).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from utils.db import setup_session as ss_db


@pytest.fixture
def _mock_pool():
    pool_mock = MagicMock()
    pool_mock.execute = AsyncMock()
    pool_mock.fetchrow = AsyncMock()
    with patch.object(ss_db, "pool") as pool_module:
        pool_module.get = MagicMock(return_value=pool_mock)
        yield pool_mock


@pytest.mark.asyncio
async def test_get_returns_dict_when_row_present(_mock_pool):
    _mock_pool.fetchrow.return_value = {
        "guild_id": 1,
        "guild_name": "Test",
        "owner_id": 99,
        "joined_at": None,
        "setup_status": "pending",
        "setup_channel_id": 11,
        "setup_message_id": 22,
        "last_readiness_score": 0,
        "current_step": None,
        "delegated_admins": [],
        "created_at": None,
        "updated_at": None,
    }
    row = await ss_db.get(1)
    assert row is not None
    assert row["setup_status"] == "pending"
    assert row["owner_id"] == 99


@pytest.mark.asyncio
async def test_get_returns_none_when_no_row(_mock_pool):
    _mock_pool.fetchrow.return_value = None
    row = await ss_db.get(1)
    assert row is None


@pytest.mark.asyncio
async def test_upsert_issues_insert_with_correct_params(_mock_pool):
    await ss_db.upsert(
        guild_id=1,
        guild_name="My Guild",
        owner_id=99,
        setup_channel_id=11,
        setup_message_id=22,
    )
    _mock_pool.execute.assert_awaited_once()
    sql, *args = _mock_pool.execute.await_args.args
    assert "INSERT INTO setup_session" in sql
    assert args == [1, "My Guild", 99, "pending", 11, 22]


@pytest.mark.asyncio
async def test_upsert_rejects_unknown_status(_mock_pool):
    with pytest.raises(ValueError, match="setup_status"):
        await ss_db.upsert(
            guild_id=1,
            guild_name="x",
            owner_id=99,
            setup_status="garbage",
        )
    _mock_pool.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_set_status_rejects_unknown_value(_mock_pool):
    with pytest.raises(ValueError, match="status"):
        await ss_db.set_status(1, "garbage")
    _mock_pool.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_set_status_writes_update(_mock_pool):
    await ss_db.set_status(1, "in_progress")
    sql, *args = _mock_pool.execute.await_args.args
    assert "UPDATE setup_session" in sql
    assert args == [1, "in_progress"]


@pytest.mark.asyncio
async def test_set_step_accepts_none(_mock_pool):
    await ss_db.set_step(1, None)
    sql, *args = _mock_pool.execute.await_args.args
    assert "current_step" in sql
    assert args == [1, None]


@pytest.mark.asyncio
async def test_set_step_records_token(_mock_pool):
    await ss_db.set_step(1, "logging")
    sql, *args = _mock_pool.execute.await_args.args
    assert "current_step" in sql
    assert args == [1, "logging"]


@pytest.mark.asyncio
async def test_set_readiness_score_persists_value(_mock_pool):
    await ss_db.set_readiness_score(1, 87)
    sql, *args = _mock_pool.execute.await_args.args
    assert "last_readiness_score" in sql
    assert args == [1, 87]


@pytest.mark.asyncio
async def test_add_and_remove_delegated_admin(_mock_pool):
    await ss_db.add_delegated_admin(1, 555)
    sql, *args = _mock_pool.execute.await_args.args
    assert "delegated_admins" in sql
    assert args == [1, 555]

    _mock_pool.execute.reset_mock()
    await ss_db.remove_delegated_admin(1, 555)
    sql, *args = _mock_pool.execute.await_args.args
    assert "ARRAY_REMOVE" in sql
    assert args == [1, 555]


@pytest.mark.asyncio
async def test_clear_deletes_row(_mock_pool):
    await ss_db.clear(1)
    sql, *args = _mock_pool.execute.await_args.args
    assert "DELETE FROM setup_session" in sql
    assert args == [1]


def test_known_statuses_matches_documented_set():
    assert ss_db.KNOWN_STATUSES == frozenset(
        {"pending", "in_progress", "complete", "dismissed"},
    )


# ---------------------------------------------------------------------------
# Essential Setup restart-revive anchor (migration 099)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_selects_essential_anchor_columns(_mock_pool):
    _mock_pool.fetchrow.return_value = {"guild_id": 1, "setup_status": "pending"}
    await ss_db.get(1)
    sql = _mock_pool.fetchrow.await_args.args[0]
    assert "essential_message_id" in sql
    assert "essential_step" in sql


@pytest.mark.asyncio
async def test_set_essential_anchor_updates_both_columns(_mock_pool):
    await ss_db.set_essential_anchor(1, 555, 3)
    _mock_pool.execute.assert_awaited_once()
    sql, *args = _mock_pool.execute.await_args.args
    assert "UPDATE setup_session" in sql
    assert "essential_message_id" in sql
    assert "essential_step" in sql
    assert args == [1, 555, 3]


@pytest.mark.asyncio
async def test_set_essential_step_updates_step_only(_mock_pool):
    await ss_db.set_essential_step(1, 4)
    sql, *args = _mock_pool.execute.await_args.args
    assert "essential_step" in sql
    # Only the step is touched — the message-id anchor is left intact.
    assert "essential_message_id" not in sql
    assert args == [1, 4]


@pytest.mark.asyncio
async def test_clear_essential_anchor_nulls_both(_mock_pool):
    await ss_db.clear_essential_anchor(1)
    sql, *args = _mock_pool.execute.await_args.args
    assert "essential_message_id = NULL" in sql
    assert "essential_step" in sql and "NULL" in sql
    assert args == [1]
