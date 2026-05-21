"""``services.setup_draft`` service-level tests.

Patches the DB primitives in :mod:`utils.db.setup_draft` and asserts the
service correctly normalises metadata, serialises values, hydrates ops
back from rows, and routes lifecycle calls.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from services import setup_draft
from services.setup_operations import SetupOperation


# ---------------------------------------------------------------------------
# append
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_append_routes_scalar_op_through_db():
    op = SetupOperation(
        kind="set_setting",
        subsystem="moderation",
        setting_name="warn_threshold",
        value=3,
    )
    with (
        patch.object(
            setup_draft.db, "insert", new=AsyncMock(return_value=1),
        ) as insert,
        patch.object(
            setup_draft.db, "list_rows", new=AsyncMock(return_value=[]),
        ),
    ):
        seq = await setup_draft.append(
            op,
            guild_id=42,
            actor_id=99,
            label="warn_threshold = 3",
            metadata={"source": "manual", "reason": "Operator entered value"},
        )
    assert seq == 1
    insert.assert_awaited_once()
    kwargs = insert.await_args.kwargs
    assert kwargs["guild_id"] == 42
    assert kwargs["op_kind"] == "set_setting"
    assert kwargs["subsystem"] == "moderation"
    assert kwargs["setting_name"] == "warn_threshold"
    assert kwargs["value_raw"] == "3"
    assert kwargs["actor_id"] == 99
    assert kwargs["label"] == "warn_threshold = 3"
    md = kwargs["metadata"]
    assert md["source"] == "manual"
    assert md["reason"] == "Operator entered value"
    # Defaults filled.
    assert md["confidence"] == "medium"
    assert md["risk"] == "low"  # set_setting default
    assert "rollback_note" in md


@pytest.mark.asyncio
async def test_append_serialises_bool_values_as_true_false():
    op = SetupOperation(
        kind="set_setting",
        subsystem="logging",
        setting_name="enabled",
        value=False,
    )
    with (
        patch.object(
            setup_draft.db, "insert", new=AsyncMock(return_value=1),
        ) as insert,
        patch.object(
            setup_draft.db, "list_rows", new=AsyncMock(return_value=[]),
        ),
    ):
        await setup_draft.append(
            op,
            guild_id=42,
            actor_id=99,
            label="logging.enabled = false",
        )
    assert insert.await_args.kwargs["value_raw"] == "false"


@pytest.mark.asyncio
async def test_append_serialises_none_value_as_none():
    op = SetupOperation(
        kind="clear_binding",
        subsystem="logging",
        binding_name="mod_channel",
    )
    with (
        patch.object(
            setup_draft.db, "insert", new=AsyncMock(return_value=1),
        ) as insert,
        patch.object(
            setup_draft.db, "list_rows", new=AsyncMock(return_value=[]),
        ),
    ):
        await setup_draft.append(
            op,
            guild_id=42,
            actor_id=99,
            label="clear mod_channel",
        )
    assert insert.await_args.kwargs["value_raw"] is None


@pytest.mark.asyncio
async def test_append_default_risk_per_op_kind():
    # create_role drafts default to high risk, create_channel to medium.
    insert_mock = AsyncMock(return_value=1)
    with (
        patch.object(setup_draft.db, "insert", new=insert_mock),
        patch.object(setup_draft.db, "list_rows", new=AsyncMock(return_value=[])),
    ):
        op = SetupOperation(kind="create_role", subsystem="roles", resource_name="moderator")
        await setup_draft.append(op, guild_id=1, actor_id=1, label="create moderator")
        assert insert_mock.await_args.kwargs["metadata"]["risk"] == "high"

    insert_mock = AsyncMock(return_value=1)
    with (
        patch.object(setup_draft.db, "insert", new=insert_mock),
        patch.object(setup_draft.db, "list_rows", new=AsyncMock(return_value=[])),
    ):
        op = SetupOperation(kind="create_channel", subsystem="logging", resource_name="bot-log")
        await setup_draft.append(op, guild_id=1, actor_id=1, label="create #bot-log")
        assert insert_mock.await_args.kwargs["metadata"]["risk"] == "medium"


@pytest.mark.asyncio
async def test_append_operator_metadata_wins_over_default():
    op = SetupOperation(kind="set_setting", subsystem="moderation", setting_name="warn_threshold", value=3)
    insert_mock = AsyncMock(return_value=1)
    with (
        patch.object(setup_draft.db, "insert", new=insert_mock),
        patch.object(setup_draft.db, "list_rows", new=AsyncMock(return_value=[])),
    ):
        await setup_draft.append(
            op,
            guild_id=1,
            actor_id=1,
            label="warn_threshold = 3",
            metadata={"risk": "high", "confidence": "low"},
        )
        md = insert_mock.await_args.kwargs["metadata"]
        assert md["risk"] == "high"
        assert md["confidence"] == "low"


@pytest.mark.asyncio
async def test_append_setup_operation_metadata_wins_over_argument():
    op = SetupOperation(
        kind="set_setting",
        subsystem="moderation",
        setting_name="warn_threshold",
        value=3,
        metadata={"source": "preset:community", "reason": "preset baseline"},
    )
    insert_mock = AsyncMock(return_value=1)
    with (
        patch.object(setup_draft.db, "insert", new=insert_mock),
        patch.object(setup_draft.db, "list_rows", new=AsyncMock(return_value=[])),
    ):
        await setup_draft.append(
            op,
            guild_id=1,
            actor_id=1,
            label="warn_threshold = 3",
            metadata={"source": "manual"},
        )
        md = insert_mock.await_args.kwargs["metadata"]
        # SetupOperation.metadata takes precedence over the `metadata=` argument.
        assert md["source"] == "preset:community"
        assert md["reason"] == "preset baseline"


@pytest.mark.asyncio
async def test_append_rejects_empty_label():
    op = SetupOperation(kind="set_setting", subsystem="moderation", setting_name="warn_threshold", value=3)
    with pytest.raises(ValueError, match="label"):
        await setup_draft.append(op, guild_id=1, actor_id=1, label="")


@pytest.mark.asyncio
async def test_append_preserves_session_started_at_across_appends():
    earlier = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    insert_mock = AsyncMock(return_value=2)
    with (
        patch.object(
            setup_draft.db,
            "list_rows",
            new=AsyncMock(return_value=[{"session_started_at": earlier}]),
        ),
        patch.object(setup_draft.db, "insert", new=insert_mock),
    ):
        op = SetupOperation(kind="set_setting", subsystem="x", setting_name="y", value=1)
        await setup_draft.append(op, guild_id=1, actor_id=1, label="x.y = 1")
        assert insert_mock.await_args.kwargs["session_started_at"] == earlier


@pytest.mark.asyncio
async def test_append_uses_now_when_draft_is_empty():
    insert_mock = AsyncMock(return_value=1)
    with (
        patch.object(
            setup_draft.db, "list_rows", new=AsyncMock(return_value=[]),
        ),
        patch.object(setup_draft.db, "insert", new=insert_mock),
    ):
        op = SetupOperation(kind="set_setting", subsystem="x", setting_name="y", value=1)
        await setup_draft.append(op, guild_id=1, actor_id=1, label="x.y = 1")
        when = insert_mock.await_args.kwargs["session_started_at"]
        assert isinstance(when, datetime)
        assert when.tzinfo is not None


# ---------------------------------------------------------------------------
# list_ops
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_ops_hydrates_setup_operations_in_order():
    rows = [
        {
            "seq": 1, "op_kind": "set_setting", "subsystem": "moderation",
            "setting_name": "warn_threshold", "binding_name": None,
            "value_raw": "3", "target_id": None, "target_name": None,
            "target_kind": None, "resource_mode": None, "resource_name": None,
            "existing_id": None, "automation_rule_id": None,
            "automation_rule_name": None, "trigger_kind": None,
            "action_kind": None, "trigger_config_json": None,
            "action_config_json": None, "schedule": None, "timezone": None,
            "metadata_json": {"source": "manual"},
        },
        {
            "seq": 2, "op_kind": "bind_channel", "subsystem": "logging",
            "binding_name": "mod_channel", "setting_name": None,
            "value_raw": None, "target_id": 999, "target_name": "#log",
            "target_kind": "channel", "resource_mode": None,
            "resource_name": None, "existing_id": None,
            "automation_rule_id": None, "automation_rule_name": None,
            "trigger_kind": None, "action_kind": None,
            "trigger_config_json": None, "action_config_json": None,
            "schedule": None, "timezone": None,
            "metadata_json": {"source": "scan", "confidence": "high"},
        },
    ]
    with patch.object(
        setup_draft.db, "list_rows", new=AsyncMock(return_value=rows),
    ):
        ops = await setup_draft.list_ops(1)
    assert len(ops) == 2
    assert ops[0].kind == "set_setting"
    assert ops[0].setting_name == "warn_threshold"
    assert ops[0].value == "3"
    assert ops[0].metadata == {"source": "manual"}
    assert ops[1].kind == "bind_channel"
    assert ops[1].binding_name == "mod_channel"
    assert ops[1].target_id == 999


@pytest.mark.asyncio
async def test_list_ops_returns_empty_when_no_rows():
    with patch.object(
        setup_draft.db, "list_rows", new=AsyncMock(return_value=[]),
    ):
        ops = await setup_draft.list_ops(1)
    assert ops == []


@pytest.mark.asyncio
async def test_list_ops_handles_string_jsonb_payloads():
    """asyncpg may return JSONB as a pre-decoded dict OR as a JSON string
    depending on codec configuration; the service must handle both.
    """
    rows = [
        {
            "seq": 1, "op_kind": "set_setting", "subsystem": "x",
            "setting_name": "y", "binding_name": None, "value_raw": "1",
            "target_id": None, "target_name": None, "target_kind": None,
            "resource_mode": None, "resource_name": None, "existing_id": None,
            "automation_rule_id": None, "automation_rule_name": None,
            "trigger_kind": None, "action_kind": None,
            "trigger_config_json": '{"a": 1}',
            "action_config_json": None,
            "schedule": None, "timezone": None,
            "metadata_json": '{"source": "manual"}',
        },
    ]
    with patch.object(
        setup_draft.db, "list_rows", new=AsyncMock(return_value=rows),
    ):
        ops = await setup_draft.list_ops(1)
    assert ops[0].trigger_config == {"a": 1}
    assert ops[0].metadata == {"source": "manual"}


# ---------------------------------------------------------------------------
# clear / count
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_clear_routes_to_db_layer():
    with patch.object(setup_draft.db, "clear", new=AsyncMock(return_value=4)) as clear:
        n = await setup_draft.clear(1)
    assert n == 4
    clear.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_count_routes_to_db_layer():
    with patch.object(setup_draft.db, "count", new=AsyncMock(return_value=2)) as count:
        n = await setup_draft.count(1)
    assert n == 2
    count.assert_awaited_once_with(1)


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------


def test_serialise_value_handles_known_shapes():
    assert setup_draft._serialise_value(None) is None
    assert setup_draft._serialise_value(True) == "true"
    assert setup_draft._serialise_value(False) == "false"
    assert setup_draft._serialise_value(3) == "3"
    assert setup_draft._serialise_value(3.14) == "3.14"
    assert setup_draft._serialise_value("hello") == "hello"


def test_default_risk_table_covers_all_operation_kinds():
    """Every known OperationKind literal must have a default risk."""
    from utils.db import setup_draft as draft_db

    missing = sorted(draft_db._KNOWN_OP_KINDS - setup_draft._DEFAULT_RISK_BY_KIND.keys())
    assert not missing, f"missing default risk for op kinds: {missing}"
