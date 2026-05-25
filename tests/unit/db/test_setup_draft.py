"""``utils.db.setup_draft`` CRUD tests.

Mocks the asyncpg pool and asserts each primitive issues SQL with the
expected shape and parameters.  Mirrors the pattern from
``tests/unit/db/test_setup_session.py``.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from utils.db import setup_draft as draft_db


@pytest.fixture
def _mock_pool():
    pool_mock = MagicMock()
    pool_mock.execute = AsyncMock()
    pool_mock.fetchrow = AsyncMock()
    pool_mock.fetch = AsyncMock()
    with patch.object(draft_db, "pool") as pool_module:
        pool_module.get = MagicMock(return_value=pool_mock)
        yield pool_mock


# ---------------------------------------------------------------------------
# insert
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_insert_rejects_unknown_op_kind(_mock_pool):
    with pytest.raises(ValueError, match="op_kind"):
        await draft_db.insert(
            guild_id=1,
            session_started_at=datetime.now(timezone.utc),
            op_kind="garbage",
            subsystem="moderation",
            binding_name=None,
            setting_name="warn_threshold",
            target_id=None,
            target_name=None,
            target_kind=None,
            value_raw="3",
            resource_mode=None,
            resource_name=None,
            existing_id=None,
            automation_rule_id=None,
            automation_rule_name=None,
            trigger_kind=None,
            action_kind=None,
            trigger_config=None,
            action_config=None,
            schedule=None,
            timezone=None,
            actor_id=99,
            label="warn_threshold = 3",
            metadata={"source": "manual"},
        )
    _mock_pool.fetchrow.assert_not_awaited()


@pytest.mark.asyncio
async def test_insert_rejects_empty_subsystem(_mock_pool):
    with pytest.raises(ValueError, match="subsystem"):
        await draft_db.insert(
            guild_id=1,
            session_started_at=datetime.now(timezone.utc),
            op_kind="set_setting",
            subsystem="",
            binding_name=None,
            setting_name="warn_threshold",
            target_id=None,
            target_name=None,
            target_kind=None,
            value_raw="3",
            resource_mode=None,
            resource_name=None,
            existing_id=None,
            automation_rule_id=None,
            automation_rule_name=None,
            trigger_kind=None,
            action_kind=None,
            trigger_config=None,
            action_config=None,
            schedule=None,
            timezone=None,
            actor_id=99,
            label="x",
            metadata=None,
        )


@pytest.mark.asyncio
async def test_insert_rejects_empty_label(_mock_pool):
    with pytest.raises(ValueError, match="label"):
        await draft_db.insert(
            guild_id=1,
            session_started_at=datetime.now(timezone.utc),
            op_kind="set_setting",
            subsystem="moderation",
            binding_name=None,
            setting_name="warn_threshold",
            target_id=None,
            target_name=None,
            target_kind=None,
            value_raw="3",
            resource_mode=None,
            resource_name=None,
            existing_id=None,
            automation_rule_id=None,
            automation_rule_name=None,
            trigger_kind=None,
            action_kind=None,
            trigger_config=None,
            action_config=None,
            schedule=None,
            timezone=None,
            actor_id=99,
            label="",
            metadata=None,
        )


@pytest.mark.asyncio
async def test_insert_issues_upsert_with_expected_params(_mock_pool):
    _mock_pool.fetchrow.return_value = {"seq": 1}
    when = datetime(2026, 5, 21, 12, 0, 0, tzinfo=timezone.utc)
    seq = await draft_db.insert(
        guild_id=42,
        session_started_at=when,
        op_kind="set_setting",
        subsystem="moderation",
        binding_name=None,
        setting_name="warn_threshold",
        target_id=None,
        target_name=None,
        target_kind=None,
        value_raw="3",
        resource_mode=None,
        resource_name=None,
        existing_id=None,
        automation_rule_id=None,
        automation_rule_name=None,
        trigger_kind=None,
        action_kind=None,
        trigger_config=None,
        action_config=None,
        schedule=None,
        timezone=None,
        actor_id=99,
        label="warn_threshold = 3",
        metadata={"source": "manual", "confidence": "high"},
    )
    assert seq == 1
    sql, *args = _mock_pool.fetchrow.await_args.args
    assert "INSERT INTO setup_draft_operations" in sql
    assert "ON CONFLICT" in sql
    assert "DO UPDATE SET" in sql
    assert "RETURNING seq" in sql
    # First two positional args are guild_id + session_started_at.
    assert args[0] == 42
    assert args[1] == when
    # Op kind + subsystem.
    assert args[2] == "set_setting"
    assert args[3] == "moderation"
    # Setting name + label.
    assert "warn_threshold" in args
    assert "warn_threshold = 3" in args


@pytest.mark.asyncio
async def test_insert_serialises_json_payloads(_mock_pool):
    _mock_pool.fetchrow.return_value = {"seq": 7}
    when = datetime.now(timezone.utc)
    await draft_db.insert(
        guild_id=42,
        session_started_at=when,
        op_kind="add_automation_rule",
        subsystem="automation",
        binding_name=None,
        setting_name=None,
        target_id=None,
        target_name=None,
        target_kind=None,
        value_raw=None,
        resource_mode=None,
        resource_name=None,
        existing_id=None,
        automation_rule_id=None,
        automation_rule_name="welcome",
        trigger_kind="message",
        action_kind="reply",
        trigger_config={"pattern": "hello"},
        action_config={"text": "hi"},
        schedule=None,
        timezone=None,
        actor_id=99,
        label="add welcome rule",
        metadata={"source": "preset:community"},
    )
    args = _mock_pool.fetchrow.await_args.args[1:]
    # The trigger_config / action_config / metadata serialised to JSON.
    json_args = [a for a in args if isinstance(a, str)]
    assert any('"pattern"' in s for s in json_args), json_args
    assert any('"text"' in s for s in json_args), json_args
    assert any('"preset:community"' in s for s in json_args), json_args


# ---------------------------------------------------------------------------
# list_rows
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_rows_returns_ordered_dicts(_mock_pool):
    _mock_pool.fetch.return_value = [
        {
            "id": 1, "guild_id": 1, "seq": 1, "op_kind": "set_setting",
            "subsystem": "moderation", "binding_name": None,
            "setting_name": "warn_threshold", "value_raw": "3",
            "label": "warn_threshold = 3", "metadata_json": None,
        },
        {
            "id": 2, "guild_id": 1, "seq": 2, "op_kind": "bind_channel",
            "subsystem": "logging", "binding_name": "mod_channel",
            "setting_name": None, "target_id": 999, "target_name": "#log",
            "target_kind": "channel", "label": "bind mod_channel → #log",
            "metadata_json": None,
        },
    ]
    rows = await draft_db.list_rows(1)
    assert [r["seq"] for r in rows] == [1, 2]
    sql, *args = _mock_pool.fetch.await_args.args
    assert "FROM setup_draft_operations" in sql
    assert "ORDER BY seq ASC" in sql
    assert args == [1]


@pytest.mark.asyncio
async def test_list_rows_returns_empty_list_when_no_rows(_mock_pool):
    _mock_pool.fetch.return_value = []
    rows = await draft_db.list_rows(1)
    assert rows == []


# ---------------------------------------------------------------------------
# clear / count
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_clear_returns_deleted_row_count(_mock_pool):
    _mock_pool.fetchrow.return_value = {"n": 3}
    n = await draft_db.clear(1)
    assert n == 3
    sql, *args = _mock_pool.fetchrow.await_args.args
    assert "DELETE FROM setup_draft_operations" in sql
    assert args == [1]


@pytest.mark.asyncio
async def test_clear_returns_zero_when_no_rows(_mock_pool):
    _mock_pool.fetchrow.return_value = {"n": 0}
    n = await draft_db.clear(1)
    assert n == 0


@pytest.mark.asyncio
async def test_count_returns_pending_row_count(_mock_pool):
    _mock_pool.fetchrow.return_value = {"n": 5}
    n = await draft_db.count(1)
    assert n == 5
    sql, *args = _mock_pool.fetchrow.await_args.args
    assert "COUNT(*)" in sql
    assert "FROM setup_draft_operations" in sql
    assert args == [1]


@pytest.mark.asyncio
async def test_count_returns_zero_when_no_rows(_mock_pool):
    _mock_pool.fetchrow.return_value = {"n": 0}
    n = await draft_db.count(1)
    assert n == 0


# ---------------------------------------------------------------------------
# Constant sanity
# ---------------------------------------------------------------------------


def test_known_op_kinds_matches_documented_set():
    assert draft_db._KNOWN_OP_KINDS == frozenset(
        {
            "bind_channel", "bind_role", "bind_category", "bind_thread",
            "bind_member", "clear_binding", "set_setting",
            "create_channel", "create_role", "create_category",
            "add_automation_rule", "enable_automation_rule",
            "disable_automation_rule",
            "set_cleanup_policy", "set_cog_routing",
        },
    )


def test_migration_file_present():
    """The migration file backing this primitive must exist."""
    from pathlib import Path

    here = Path(__file__).resolve().parents[3]
    assert (
        here / "disbot" / "migrations" / "035_setup_draft_operations.sql"
    ).is_file(), "migration 035_setup_draft_operations.sql is missing"


def test_migration_file_is_idempotent():
    """The migration must use CREATE TABLE IF NOT EXISTS so re-running is safe."""
    from pathlib import Path

    here = Path(__file__).resolve().parents[3]
    sql = (
        here / "disbot" / "migrations" / "035_setup_draft_operations.sql"
    ).read_text()
    assert "CREATE TABLE IF NOT EXISTS setup_draft_operations" in sql
    assert "CREATE UNIQUE INDEX IF NOT EXISTS" in sql
    assert "CREATE INDEX IF NOT EXISTS" in sql


def test_migration_lists_all_known_op_kinds_in_check():
    """The CHECK constraint must cover every OperationKind literal."""
    from pathlib import Path

    here = Path(__file__).resolve().parents[3]
    sql = (
        here / "disbot" / "migrations" / "035_setup_draft_operations.sql"
    ).read_text()
    for kind in draft_db._KNOWN_OP_KINDS:
        assert f"'{kind}'" in sql, f"CHECK omits op_kind {kind!r}"


# ---------------------------------------------------------------------------
# Phase 0 provenance — migration 045 + new helpers
# ---------------------------------------------------------------------------


def test_migration_045_present_and_idempotent():
    """Phase 0 migration adds provenance columns."""
    from pathlib import Path

    here = Path(__file__).resolve().parents[3]
    path = (
        here / "disbot" / "migrations" / "045_setup_draft_provenance.sql"
    )
    assert path.is_file(), "migration 045_setup_draft_provenance.sql is missing"
    sql = path.read_text()
    # All four columns added, all guarded by IF NOT EXISTS.
    assert "ADD COLUMN IF NOT EXISTS section_slug" in sql
    assert "ADD COLUMN IF NOT EXISTS staging_kind" in sql
    assert "ADD COLUMN IF NOT EXISTS group_id" in sql
    assert "ADD COLUMN IF NOT EXISTS parent_seq" in sql
    # Section-slug index is also created idempotently.
    assert "CREATE INDEX IF NOT EXISTS idx_setup_draft_operations_section_slug" in sql


def test_staging_kinds_set_includes_all_documented_values():
    """The DB-layer allowlist must include every staging_kind value
    documented in services.setup_draft (recommended is included here
    because the layer accepts it from the dedicated writer)."""
    assert draft_db._STAGING_KINDS == frozenset(
        {"recommended", "custom", "preset", "manual", "repair"},
    )


@pytest.mark.asyncio
async def test_insert_accepts_provenance_columns(_mock_pool):
    _mock_pool.fetchrow.return_value = {"seq": 1}
    when = datetime.now(timezone.utc)
    seq = await draft_db.insert(
        guild_id=42,
        session_started_at=when,
        op_kind="bind_channel",
        subsystem="logging",
        binding_name="mod_channel",
        setting_name=None,
        target_id=999,
        target_name="#mod-log",
        target_kind="channel",
        value_raw=None,
        resource_mode=None,
        resource_name=None,
        existing_id=None,
        automation_rule_id=None,
        automation_rule_name=None,
        trigger_kind=None,
        action_kind=None,
        trigger_config=None,
        action_config=None,
        schedule=None,
        timezone=None,
        actor_id=99,
        label="bind mod_channel → #mod-log",
        metadata={"source": "scan"},
        section_slug="logging",
        staging_kind="recommended",
        group_id="g-1",
        parent_seq=2,
    )
    assert seq == 1
    sql, *args = _mock_pool.fetchrow.await_args.args
    # New columns appear in the INSERT and UPDATE arms.
    assert "section_slug" in sql
    assert "staging_kind" in sql
    assert "group_id" in sql
    assert "parent_seq" in sql
    # And in the positional args list.
    assert "logging" in args
    assert "recommended" in args
    assert "g-1" in args
    assert 2 in args


@pytest.mark.asyncio
async def test_insert_rejects_unknown_staging_kind(_mock_pool):
    with pytest.raises(ValueError, match="staging_kind"):
        await draft_db.insert(
            guild_id=1,
            session_started_at=datetime.now(timezone.utc),
            op_kind="set_setting",
            subsystem="x",
            binding_name=None,
            setting_name="y",
            target_id=None,
            target_name=None,
            target_kind=None,
            value_raw="1",
            resource_mode=None,
            resource_name=None,
            existing_id=None,
            automation_rule_id=None,
            automation_rule_name=None,
            trigger_kind=None,
            action_kind=None,
            trigger_config=None,
            action_config=None,
            schedule=None,
            timezone=None,
            actor_id=99,
            label="x.y = 1",
            metadata=None,
            staging_kind="garbage",
        )


@pytest.mark.asyncio
async def test_insert_accepts_null_staging_kind_for_legacy_rows(_mock_pool):
    """Legacy / pre-Phase-0 callers don't pass staging_kind; that's a
    documented "manual / preserve" default.
    """
    _mock_pool.fetchrow.return_value = {"seq": 1}
    await draft_db.insert(
        guild_id=1,
        session_started_at=datetime.now(timezone.utc),
        op_kind="set_setting",
        subsystem="x",
        binding_name=None,
        setting_name="y",
        target_id=None,
        target_name=None,
        target_kind=None,
        value_raw="1",
        resource_mode=None,
        resource_name=None,
        existing_id=None,
        automation_rule_id=None,
        automation_rule_name=None,
        trigger_kind=None,
        action_kind=None,
        trigger_config=None,
        action_config=None,
        schedule=None,
        timezone=None,
        actor_id=99,
        label="x.y = 1",
        metadata=None,
        # staging_kind unset
    )
    _mock_pool.fetchrow.assert_awaited()


@pytest.mark.asyncio
async def test_list_rows_selects_provenance_columns(_mock_pool):
    _mock_pool.fetch.return_value = []
    await draft_db.list_rows(1)
    sql, *_ = _mock_pool.fetch.await_args.args
    assert "section_slug" in sql
    assert "staging_kind" in sql
    assert "group_id" in sql
    assert "parent_seq" in sql


@pytest.mark.asyncio
async def test_list_by_section_filters_by_section_slug(_mock_pool):
    _mock_pool.fetch.return_value = []
    await draft_db.list_by_section(1, "logging")
    sql, *args = _mock_pool.fetch.await_args.args
    assert "section_slug = $2" in sql
    assert args == [1, "logging"]


@pytest.mark.asyncio
async def test_delete_by_ids_uses_any_clause(_mock_pool):
    _mock_pool.fetchrow.return_value = {"n": 2}
    n = await draft_db.delete_by_ids(1, [7, 11])
    assert n == 2
    sql, *args = _mock_pool.fetchrow.await_args.args
    assert "DELETE FROM setup_draft_operations" in sql
    assert "= ANY($2::BIGINT[])" in sql
    assert args[0] == 1
    assert args[1] == [7, 11]


@pytest.mark.asyncio
async def test_delete_by_ids_noop_on_empty(_mock_pool):
    n = await draft_db.delete_by_ids(1, [])
    assert n == 0
    _mock_pool.fetchrow.assert_not_called()


@pytest.mark.asyncio
async def test_delete_by_seqs_uses_any_clause(_mock_pool):
    _mock_pool.fetchrow.return_value = {"n": 1}
    n = await draft_db.delete_by_seqs(1, [5])
    assert n == 1
    sql, *args = _mock_pool.fetchrow.await_args.args
    assert "DELETE FROM setup_draft_operations" in sql
    assert "= ANY($2::INT[])" in sql
    assert args == [1, [5]]


@pytest.mark.asyncio
async def test_delete_by_seqs_noop_on_empty(_mock_pool):
    n = await draft_db.delete_by_seqs(1, [])
    assert n == 0
    _mock_pool.fetchrow.assert_not_called()
