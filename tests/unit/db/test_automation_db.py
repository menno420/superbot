"""Phase 9g / Track 6 PR 15 — automation DB primitives tests.

Mocks the asyncpg pool and asserts each primitive issues the
expected SQL with the expected parameters. JSONB serialisation
is verified by checking the encoded argument.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from utils.db import automation as db


@pytest.fixture
def _mock_pool():
    pool_mock = MagicMock()
    pool_mock.execute = AsyncMock()
    pool_mock.fetchrow = AsyncMock()
    pool_mock.fetch = AsyncMock()
    with patch.object(db, "pool") as pool_module:
        pool_module.get = MagicMock(return_value=pool_mock)
        yield pool_mock


# ---------------------------------------------------------------------------
# Rules — read
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_rule_returns_decoded_jsonb(_mock_pool):
    _mock_pool.fetchrow.return_value = {
        "id": 1,
        "guild_id": 10,
        "name": "daily-readiness",
        "enabled": True,
        "trigger_kind": "scheduled_time",
        "trigger_config": '{"quiet_hours": [0, 6]}',
        "action_kind": "post_readiness_summary",
        "action_config": '{"channel_id": 555}',
        "schedule": "0 9 * * *",
        "timezone": "UTC",
        "last_run_at": None,
        "next_run_at": None,
        "failure_count": 0,
        "last_error": None,
        "created_by": 99,
        "created_at": None,
        "updated_at": None,
    }
    row = await db.get_rule(1)
    assert row is not None
    assert row["trigger_config"] == {"quiet_hours": [0, 6]}
    assert row["action_config"] == {"channel_id": 555}


@pytest.mark.asyncio
async def test_get_rule_returns_none_when_no_row(_mock_pool):
    _mock_pool.fetchrow.return_value = None
    assert await db.get_rule(1) is None


@pytest.mark.asyncio
async def test_get_rule_handles_dict_jsonb_from_codec(_mock_pool):
    """asyncpg's JSONB codec, when installed, returns dicts directly.
    The read primitive must accept both forms."""
    _mock_pool.fetchrow.return_value = {
        "id": 1,
        "guild_id": 10,
        "name": "x",
        "enabled": False,
        "trigger_kind": "manual",
        "trigger_config": {"already": "a dict"},
        "action_kind": "notify_owner",
        "action_config": {"template": "hi"},
        "schedule": None,
        "timezone": "UTC",
        "last_run_at": None,
        "next_run_at": None,
        "failure_count": 0,
        "last_error": None,
        "created_by": None,
        "created_at": None,
        "updated_at": None,
    }
    row = await db.get_rule(1)
    assert row["trigger_config"] == {"already": "a dict"}


@pytest.mark.asyncio
async def test_list_rules_for_guild_decodes_all_rows(_mock_pool):
    _mock_pool.fetch.return_value = [
        {
            "id": 1,
            "guild_id": 10,
            "name": "a",
            "enabled": True,
            "trigger_kind": "manual",
            "trigger_config": "{}",
            "action_kind": "notify_owner",
            "action_config": '{"template": "hi"}',
            "schedule": None,
            "timezone": "UTC",
            "last_run_at": None,
            "next_run_at": None,
            "failure_count": 0,
            "last_error": None,
            "created_by": None,
            "created_at": None,
            "updated_at": None,
        },
    ]
    rows = await db.list_rules_for_guild(10)
    assert len(rows) == 1
    assert rows[0]["action_config"]["template"] == "hi"


# ---------------------------------------------------------------------------
# Rules — write
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_insert_rule_issues_jsonb_encoded_args(_mock_pool):
    _mock_pool.fetchrow.return_value = {"id": 7}
    new_id = await db.insert_rule(
        guild_id=10,
        name="welcome",
        trigger_kind="member_join",
        action_kind="send_message",
        trigger_config={},
        action_config={"channel_id": 1, "template": "hi"},
        created_by=99,
    )
    assert new_id == 7
    sql, *args = _mock_pool.fetchrow.await_args.args
    assert "INSERT INTO automation_rules" in sql
    assert args[0] == 10  # guild_id
    assert args[1] == "welcome"
    assert args[2] == "member_join"
    # trigger_config encoded as JSON string
    assert json.loads(args[3]) == {}
    assert args[4] == "send_message"
    assert json.loads(args[5])["channel_id"] == 1


@pytest.mark.asyncio
async def test_insert_rule_raises_when_returning_empty(_mock_pool):
    _mock_pool.fetchrow.return_value = None
    with pytest.raises(RuntimeError):
        await db.insert_rule(
            guild_id=10,
            name="x",
            trigger_kind="manual",
            action_kind="notify_owner",
        )


@pytest.mark.asyncio
async def test_set_enabled_writes_update(_mock_pool):
    await db.set_enabled(7, True)
    sql, *args = _mock_pool.execute.await_args.args
    assert "UPDATE automation_rules" in sql
    assert args == [7, True]


@pytest.mark.asyncio
async def test_record_failure_returns_new_count(_mock_pool):
    _mock_pool.fetchrow.return_value = {"failure_count": 3}
    count = await db.record_failure(7, "boom")
    assert count == 3
    sql, *args = _mock_pool.fetchrow.await_args.args
    assert "failure_count + 1" in sql
    assert args[0] == 7


@pytest.mark.asyncio
async def test_record_failure_truncates_long_error_text(_mock_pool):
    _mock_pool.fetchrow.return_value = {"failure_count": 1}
    long = "x" * 2000
    await db.record_failure(7, long)
    args = _mock_pool.fetchrow.await_args.args
    # Stored error is truncated to 1024 chars.
    assert len(args[2]) == 1024


@pytest.mark.asyncio
async def test_reset_failure_count_clears_error(_mock_pool):
    await db.reset_failure_count(7)
    sql, *args = _mock_pool.execute.await_args.args
    assert "failure_count = 0" in sql
    assert args == [7]


@pytest.mark.asyncio
async def test_delete_rule_executes_delete(_mock_pool):
    await db.delete_rule(7)
    sql, *args = _mock_pool.execute.await_args.args
    assert "DELETE FROM automation_rules" in sql
    assert args == [7]


@pytest.mark.asyncio
async def test_delete_rules_for_guild_returns_parsed_count(_mock_pool):
    _mock_pool.execute.return_value = "DELETE 5"
    count = await db.delete_rules_for_guild(10)
    assert count == 5


# ---------------------------------------------------------------------------
# Runs — append-only
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_claim_run_returns_id_on_success(_mock_pool):
    _mock_pool.fetchrow.return_value = {"id": 42}
    run_id = await db.claim_run(
        rule_id=1,
        guild_id=10,
        idempotency_key="key-1",
    )
    assert run_id == 42


@pytest.mark.asyncio
async def test_claim_run_returns_none_on_unique_violation(_mock_pool):
    _mock_pool.fetchrow.side_effect = RuntimeError("unique violation")
    run_id = await db.claim_run(
        rule_id=1,
        guild_id=10,
        idempotency_key="dup",
    )
    assert run_id is None


@pytest.mark.asyncio
async def test_mark_running_writes_update(_mock_pool):
    await db.mark_running(42)
    sql, *args = _mock_pool.execute.await_args.args
    assert "status = 'running'" in sql
    assert args == [42]


@pytest.mark.asyncio
async def test_finish_run_rejects_unknown_status(_mock_pool):
    with pytest.raises(ValueError):
        await db.finish_run(run_id=42, status="garbage")
    _mock_pool.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_finish_run_writes_jsonb_summary(_mock_pool):
    await db.finish_run(
        run_id=42,
        status="success",
        result_summary={"sent": 1},
    )
    args = _mock_pool.execute.await_args.args
    # args[0] is the SQL; args[1..] are bind params (run_id, status, summary, error).
    assert args[1] == 42
    assert args[2] == "success"
    assert json.loads(args[3])["sent"] == 1


@pytest.mark.asyncio
async def test_list_runs_for_rule_decodes_summary(_mock_pool):
    _mock_pool.fetch.return_value = [
        {
            "id": 1,
            "rule_id": 1,
            "guild_id": 10,
            "status": "success",
            "dry_run": False,
            "idempotency_key": "k",
            "started_at": None,
            "finished_at": None,
            "result_summary": '{"sent": 1}',
            "error": None,
        },
    ]
    rows = await db.list_runs_for_rule(1, limit=10)
    assert rows[0]["result_summary"] == {"sent": 1}


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


def test_known_run_statuses():
    assert db.KNOWN_RUN_STATUSES == frozenset(
        {"queued", "running", "success", "failure", "skipped"},
    )


def test_parse_delete_count_handles_empty_results():
    assert db._parse_delete_count(None) == 0
    assert db._parse_delete_count("") == 0
    assert db._parse_delete_count("garbage") == 0
    assert db._parse_delete_count("DELETE 0") == 0
    assert db._parse_delete_count("DELETE 7") == 7
