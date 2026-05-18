"""Phase 2 PR-5 — utils.db.platform_migration_checkpoints primitives."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from utils.db import platform_migration_checkpoints as checkpoint_db


@pytest.fixture
def _mock_pool():
    pool_mock = MagicMock()
    pool_mock.execute = AsyncMock()
    pool_mock.fetchrow = AsyncMock()
    pool_mock.fetch = AsyncMock()
    with patch.object(checkpoint_db, "pool") as pool_module:
        pool_module.get = MagicMock(return_value=pool_mock)
        yield pool_mock


# ---------------------------------------------------------------------------
# get_checkpoint
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_checkpoint_per_guild_uses_equality(_mock_pool):
    _mock_pool.fetchrow.return_value = None
    await checkpoint_db.get_checkpoint("binding_backfill", guild_id=42)
    sql, *args = _mock_pool.fetchrow.await_args.args
    assert "guild_id = $2" in sql
    assert args == ["binding_backfill", 42]


@pytest.mark.asyncio
async def test_get_checkpoint_global_uses_is_null(_mock_pool):
    """Global lookup MUST use ``IS NULL`` — equality with NULL never matches."""
    _mock_pool.fetchrow.return_value = None
    await checkpoint_db.get_checkpoint("binding_backfill")
    sql, *args = _mock_pool.fetchrow.await_args.args
    assert "guild_id IS NULL" in sql
    assert args == ["binding_backfill"]


@pytest.mark.asyncio
async def test_get_checkpoint_decodes_summary_json(_mock_pool):
    _mock_pool.fetchrow.return_value = {
        "id": 1,
        "name": "binding_backfill",
        "guild_id": 42,
        "status": "dry_run_complete",
        "version": 1,
        "started_at": None,
        "completed_at": None,
        "summary_json": json.dumps({"counts": {"match": 3}}),
    }
    row = await checkpoint_db.get_checkpoint("binding_backfill", guild_id=42)
    assert row is not None
    assert row["summary_json"] == {"counts": {"match": 3}}


@pytest.mark.asyncio
async def test_get_checkpoint_passes_through_dict_summary(_mock_pool):
    """If asyncpg returns a dict (codec installed), pass-through unchanged."""
    _mock_pool.fetchrow.return_value = {
        "id": 1,
        "name": "binding_backfill",
        "guild_id": 42,
        "status": "dry_run_complete",
        "version": 1,
        "started_at": None,
        "completed_at": None,
        "summary_json": {"counts": {"match": 3}},
    }
    row = await checkpoint_db.get_checkpoint("binding_backfill", guild_id=42)
    assert row is not None
    assert row["summary_json"] == {"counts": {"match": 3}}


@pytest.mark.asyncio
async def test_get_checkpoint_returns_none_when_absent(_mock_pool):
    _mock_pool.fetchrow.return_value = None
    assert await checkpoint_db.get_checkpoint("does_not_exist", guild_id=42) is None


# ---------------------------------------------------------------------------
# upsert_checkpoint
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_upsert_global_uses_partial_index_clause(_mock_pool):
    await checkpoint_db.upsert_checkpoint(
        name="binding_backfill",
        guild_id=None,
        status="pending",
        summary_json={"foo": 1},
    )
    sql, *args = _mock_pool.execute.await_args.args
    assert "ON CONFLICT (name) WHERE guild_id IS NULL" in sql
    assert args[0] == "binding_backfill"
    # version default 1
    assert args[2] == 1
    # summary_json JSON-encoded
    assert json.loads(args[3]) == {"foo": 1}


@pytest.mark.asyncio
async def test_upsert_guild_uses_partial_index_clause(_mock_pool):
    await checkpoint_db.upsert_checkpoint(
        name="binding_backfill",
        guild_id=42,
        status="dry_run_complete",
        version=2,
        summary_json={"counts": {"match": 1}},
        mark_completed=True,
    )
    sql, *args = _mock_pool.execute.await_args.args
    assert "ON CONFLICT (name, guild_id) WHERE guild_id IS NOT NULL" in sql
    assert "completed_at = NOW()" in sql
    assert args[0] == "binding_backfill"
    assert args[1] == 42
    assert args[2] == "dry_run_complete"
    assert args[3] == 2
    assert json.loads(args[4]) == {"counts": {"match": 1}}


@pytest.mark.asyncio
async def test_upsert_without_mark_completed_preserves_completed_at(_mock_pool):
    await checkpoint_db.upsert_checkpoint(
        name="binding_backfill",
        guild_id=42,
        status="in_progress",
    )
    sql, *_ = _mock_pool.execute.await_args.args
    # NOT setting completed_at = NOW(); preserve previous value
    assert "completed_at = completed_at" in sql


@pytest.mark.asyncio
async def test_upsert_rejects_unknown_status(_mock_pool):
    with pytest.raises(ValueError, match="unknown status"):
        await checkpoint_db.upsert_checkpoint(
            name="binding_backfill",
            guild_id=42,
            status="weird_status",
        )
    _mock_pool.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_upsert_string_summary_passed_through(_mock_pool):
    """If caller already serialised the summary, do not double-encode."""
    payload = '{"already": "serialised"}'
    await checkpoint_db.upsert_checkpoint(
        name="binding_backfill",
        guild_id=42,
        status="pending",
        summary_json=payload,
    )
    _, *args = _mock_pool.execute.await_args.args
    assert args[4] == payload


@pytest.mark.asyncio
async def test_upsert_none_summary_becomes_sql_null(_mock_pool):
    await checkpoint_db.upsert_checkpoint(
        name="binding_backfill",
        guild_id=42,
        status="pending",
        summary_json=None,
    )
    _, *args = _mock_pool.execute.await_args.args
    assert args[4] is None


# ---------------------------------------------------------------------------
# list_checkpoints
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_checkpoints_no_filter(_mock_pool):
    _mock_pool.fetch.return_value = []
    await checkpoint_db.list_checkpoints()
    sql, *args = _mock_pool.fetch.await_args.args
    assert "WHERE" not in sql
    assert args == []


@pytest.mark.asyncio
async def test_list_checkpoints_filtered_by_name_prefix(_mock_pool):
    _mock_pool.fetch.return_value = []
    await checkpoint_db.list_checkpoints(name_prefix="binding_")
    sql, *args = _mock_pool.fetch.await_args.args
    assert "name LIKE" in sql
    assert args == ["binding_%"]


@pytest.mark.asyncio
async def test_list_checkpoints_filtered_by_guild(_mock_pool):
    _mock_pool.fetch.return_value = []
    await checkpoint_db.list_checkpoints(guild_id=42)
    sql, *args = _mock_pool.fetch.await_args.args
    assert "guild_id = $1" in sql
    assert args == [42]


# ---------------------------------------------------------------------------
# count_by_status
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_count_by_status_returns_histogram(_mock_pool):
    _mock_pool.fetch.return_value = [
        {"status": "pending", "n": 2},
        {"status": "complete", "n": 5},
    ]
    assert await checkpoint_db.count_by_status() == {
        "pending": 2,
        "complete": 5,
    }


# ---------------------------------------------------------------------------
# delete_for_guild
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_for_guild_only_touches_guild_rows(_mock_pool):
    """Phase 2 retention: global rows (guild_id IS NULL) MUST survive."""
    _mock_pool.execute.return_value = "DELETE 4"
    deleted = await checkpoint_db.delete_for_guild(42)
    sql, *args = _mock_pool.execute.await_args.args
    assert "WHERE guild_id = $1" in sql
    assert "IS NULL" not in sql
    assert args == [42]
    assert deleted == 4


@pytest.mark.asyncio
async def test_delete_for_guild_handles_unexpected_status(_mock_pool):
    _mock_pool.execute.return_value = "junk"
    assert await checkpoint_db.delete_for_guild(42) == 0
