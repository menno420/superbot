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
            setup_draft.db,
            "insert",
            new=AsyncMock(return_value=1),
        ) as insert,
        patch.object(
            setup_draft.db,
            "list_rows",
            new=AsyncMock(return_value=[]),
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
            setup_draft.db,
            "insert",
            new=AsyncMock(return_value=1),
        ) as insert,
        patch.object(
            setup_draft.db,
            "list_rows",
            new=AsyncMock(return_value=[]),
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
            setup_draft.db,
            "insert",
            new=AsyncMock(return_value=1),
        ) as insert,
        patch.object(
            setup_draft.db,
            "list_rows",
            new=AsyncMock(return_value=[]),
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
        op = SetupOperation(
            kind="create_role", subsystem="roles", resource_name="moderator"
        )
        await setup_draft.append(op, guild_id=1, actor_id=1, label="create moderator")
        assert insert_mock.await_args.kwargs["metadata"]["risk"] == "high"

    insert_mock = AsyncMock(return_value=1)
    with (
        patch.object(setup_draft.db, "insert", new=insert_mock),
        patch.object(setup_draft.db, "list_rows", new=AsyncMock(return_value=[])),
    ):
        op = SetupOperation(
            kind="create_channel", subsystem="logging", resource_name="bot-log"
        )
        await setup_draft.append(op, guild_id=1, actor_id=1, label="create #bot-log")
        assert insert_mock.await_args.kwargs["metadata"]["risk"] == "medium"


@pytest.mark.asyncio
async def test_append_operator_metadata_wins_over_default():
    op = SetupOperation(
        kind="set_setting",
        subsystem="moderation",
        setting_name="warn_threshold",
        value=3,
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
    op = SetupOperation(
        kind="set_setting",
        subsystem="moderation",
        setting_name="warn_threshold",
        value=3,
    )
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
        op = SetupOperation(
            kind="set_setting", subsystem="x", setting_name="y", value=1
        )
        await setup_draft.append(op, guild_id=1, actor_id=1, label="x.y = 1")
        assert insert_mock.await_args.kwargs["session_started_at"] == earlier


@pytest.mark.asyncio
async def test_append_uses_now_when_draft_is_empty():
    insert_mock = AsyncMock(return_value=1)
    with (
        patch.object(
            setup_draft.db,
            "list_rows",
            new=AsyncMock(return_value=[]),
        ),
        patch.object(setup_draft.db, "insert", new=insert_mock),
    ):
        op = SetupOperation(
            kind="set_setting", subsystem="x", setting_name="y", value=1
        )
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
            "seq": 1,
            "op_kind": "set_setting",
            "subsystem": "moderation",
            "setting_name": "warn_threshold",
            "binding_name": None,
            "value_raw": "3",
            "target_id": None,
            "target_name": None,
            "target_kind": None,
            "resource_mode": None,
            "resource_name": None,
            "existing_id": None,
            "automation_rule_id": None,
            "automation_rule_name": None,
            "trigger_kind": None,
            "action_kind": None,
            "trigger_config_json": None,
            "action_config_json": None,
            "schedule": None,
            "timezone": None,
            "metadata_json": {"source": "manual"},
        },
        {
            "seq": 2,
            "op_kind": "bind_channel",
            "subsystem": "logging",
            "binding_name": "mod_channel",
            "setting_name": None,
            "value_raw": None,
            "target_id": 999,
            "target_name": "#log",
            "target_kind": "channel",
            "resource_mode": None,
            "resource_name": None,
            "existing_id": None,
            "automation_rule_id": None,
            "automation_rule_name": None,
            "trigger_kind": None,
            "action_kind": None,
            "trigger_config_json": None,
            "action_config_json": None,
            "schedule": None,
            "timezone": None,
            "metadata_json": {"source": "scan", "confidence": "high"},
        },
    ]
    with patch.object(
        setup_draft.db,
        "list_rows",
        new=AsyncMock(return_value=rows),
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
        setup_draft.db,
        "list_rows",
        new=AsyncMock(return_value=[]),
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
            "seq": 1,
            "op_kind": "set_setting",
            "subsystem": "x",
            "setting_name": "y",
            "binding_name": None,
            "value_raw": "1",
            "target_id": None,
            "target_name": None,
            "target_kind": None,
            "resource_mode": None,
            "resource_name": None,
            "existing_id": None,
            "automation_rule_id": None,
            "automation_rule_name": None,
            "trigger_kind": None,
            "action_kind": None,
            "trigger_config_json": '{"a": 1}',
            "action_config_json": None,
            "schedule": None,
            "timezone": None,
            "metadata_json": '{"source": "manual"}',
        },
    ]
    with patch.object(
        setup_draft.db,
        "list_rows",
        new=AsyncMock(return_value=rows),
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

    missing = sorted(
        draft_db._KNOWN_OP_KINDS - setup_draft._DEFAULT_RISK_BY_KIND.keys()
    )
    assert not missing, f"missing default risk for op kinds: {missing}"


# ---------------------------------------------------------------------------
# Provenance: append rejects recommended; list_rows typed wrapper
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_append_rejects_recommended_staging_kind():
    """Only :func:`replace_recommended_for_section` may write
    ``staging_kind='recommended'``.  The general append entry point
    must refuse it so ad-hoc callers cannot bypass the conflict
    preflight.
    """
    op = SetupOperation(
        kind="set_setting",
        subsystem="moderation",
        setting_name="warn_threshold",
        value=3,
    )
    with patch.object(
        setup_draft.db,
        "list_rows",
        new=AsyncMock(return_value=[]),
    ):
        with pytest.raises(ValueError, match="recommended"):
            await setup_draft.append(
                op,
                guild_id=42,
                actor_id=99,
                label="warn_threshold = 3",
                staging_kind="recommended",
            )


@pytest.mark.asyncio
async def test_append_rejects_unknown_staging_kind():
    op = SetupOperation(kind="set_setting", subsystem="x", setting_name="y", value=1)
    with patch.object(
        setup_draft.db,
        "list_rows",
        new=AsyncMock(return_value=[]),
    ):
        with pytest.raises(ValueError, match="staging_kind"):
            await setup_draft.append(
                op,
                guild_id=1,
                actor_id=1,
                label="x.y = 1",
                staging_kind="bogus",
            )


@pytest.mark.asyncio
async def test_append_passes_provenance_to_db_layer():
    op = SetupOperation(
        kind="set_setting",
        subsystem="moderation",
        setting_name="warn_threshold",
        value=3,
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
            label="x.y = 1",
            section_slug="moderation",
            staging_kind="custom",
            group_id="g1",
            parent_seq=5,
        )
    kwargs = insert_mock.await_args.kwargs
    assert kwargs["section_slug"] == "moderation"
    assert kwargs["staging_kind"] == "custom"
    assert kwargs["group_id"] == "g1"
    assert kwargs["parent_seq"] == 5


@pytest.mark.asyncio
async def test_list_rows_returns_typed_wrapper_with_provenance():
    """``list_rows`` exposes provenance via :class:`DraftOperationRow`."""
    rows = [
        {
            "id": 17,
            "guild_id": 1,
            "seq": 3,
            "op_kind": "set_setting",
            "subsystem": "moderation",
            "binding_name": None,
            "setting_name": "warn_threshold",
            "value_raw": "3",
            "target_id": None,
            "target_name": None,
            "target_kind": None,
            "resource_mode": None,
            "resource_name": None,
            "existing_id": None,
            "automation_rule_id": None,
            "automation_rule_name": None,
            "trigger_kind": None,
            "action_kind": None,
            "trigger_config_json": None,
            "action_config_json": None,
            "schedule": None,
            "timezone": None,
            "metadata_json": {"source": "manual"},
            "section_slug": "moderation",
            "staging_kind": "custom",
            "group_id": None,
            "parent_seq": None,
            "label": "warn_threshold = 3",
        },
    ]
    with patch.object(
        setup_draft.db,
        "list_rows",
        new=AsyncMock(return_value=rows),
    ):
        wrapped = await setup_draft.list_rows(1)
    assert len(wrapped) == 1
    row = wrapped[0]
    assert isinstance(row, setup_draft.DraftOperationRow)
    assert row.id == 17
    assert row.seq == 3
    assert row.section_slug == "moderation"
    assert row.staging_kind == "custom"
    assert row.label == "warn_threshold = 3"
    assert row.op.kind == "set_setting"
    assert row.op.setting_name == "warn_threshold"
    assert row.op.value == "3"


@pytest.mark.asyncio
async def test_list_rows_treats_null_provenance_as_legacy():
    """Pre-migration-045 rows arrive with NULL provenance; the wrapper
    surfaces them as None (caller treats null as "manual / preserve").
    """
    rows = [
        {
            "id": 1,
            "guild_id": 1,
            "seq": 1,
            "op_kind": "set_setting",
            "subsystem": "moderation",
            "binding_name": None,
            "setting_name": "warn_threshold",
            "value_raw": "3",
            "target_id": None,
            "target_name": None,
            "target_kind": None,
            "resource_mode": None,
            "resource_name": None,
            "existing_id": None,
            "automation_rule_id": None,
            "automation_rule_name": None,
            "trigger_kind": None,
            "action_kind": None,
            "trigger_config_json": None,
            "action_config_json": None,
            "schedule": None,
            "timezone": None,
            "metadata_json": None,
            "section_slug": None,
            "staging_kind": None,
            "group_id": None,
            "parent_seq": None,
            "label": "warn_threshold = 3",
        },
    ]
    with patch.object(
        setup_draft.db,
        "list_rows",
        new=AsyncMock(return_value=rows),
    ):
        wrapped = await setup_draft.list_rows(1)
    assert wrapped[0].section_slug is None
    assert wrapped[0].staging_kind is None


@pytest.mark.asyncio
async def test_delete_by_ids_routes_to_db_layer():
    with patch.object(
        setup_draft.db,
        "delete_by_ids",
        new=AsyncMock(return_value=2),
    ) as delete_mock:
        n = await setup_draft.delete_by_ids(1, [7, 11])
    assert n == 2
    delete_mock.assert_awaited_once_with(1, [7, 11])


@pytest.mark.asyncio
async def test_delete_by_ids_noop_on_empty_list():
    with patch.object(
        setup_draft.db,
        "delete_by_ids",
        new=AsyncMock(return_value=0),
    ) as delete_mock:
        n = await setup_draft.delete_by_ids(1, [])
    assert n == 0
    delete_mock.assert_not_called()


@pytest.mark.asyncio
async def test_delete_by_seqs_routes_to_db_layer():
    with patch.object(
        setup_draft.db,
        "delete_by_seqs",
        new=AsyncMock(return_value=1),
    ) as delete_mock:
        n = await setup_draft.delete_by_seqs(1, [5])
    assert n == 1
    delete_mock.assert_awaited_once_with(1, [5])


# ---------------------------------------------------------------------------
# replace_recommended_for_section
# ---------------------------------------------------------------------------


def _row(
    *,
    id: int,
    seq: int,
    op_kind: str,
    subsystem: str = "logging",
    binding_name: str | None = None,
    setting_name: str | None = None,
    section_slug: str | None = None,
    staging_kind: str | None = None,
    target_id: int | None = None,
    label: str = "x",
) -> dict:
    return {
        "id": id,
        "guild_id": 1,
        "seq": seq,
        "op_kind": op_kind,
        "subsystem": subsystem,
        "binding_name": binding_name,
        "setting_name": setting_name,
        "value_raw": None,
        "target_id": target_id,
        "target_name": None,
        "target_kind": None,
        "resource_mode": None,
        "resource_name": None,
        "existing_id": None,
        "automation_rule_id": None,
        "automation_rule_name": None,
        "trigger_kind": None,
        "action_kind": None,
        "trigger_config_json": None,
        "action_config_json": None,
        "schedule": None,
        "timezone": None,
        "metadata_json": None,
        "section_slug": section_slug,
        "staging_kind": staging_kind,
        "group_id": None,
        "parent_seq": None,
        "label": label,
        # Required by services.setup_draft._session_started_at, which
        # also reads through db.list_rows.
        "session_started_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
    }


@pytest.mark.asyncio
async def test_replace_recommended_inserts_into_empty_draft():
    """No prior rows: every new op is inserted as recommended."""
    op = SetupOperation(
        kind="bind_channel",
        subsystem="logging",
        binding_name="mod_channel",
        target_id=999,
        target_kind="channel",
    )
    insert_mock = AsyncMock(side_effect=[10])
    with (
        patch.object(
            setup_draft.db,
            "list_rows",
            new=AsyncMock(return_value=[]),
        ),
        patch.object(setup_draft.db, "insert", new=insert_mock),
        patch.object(
            setup_draft.db,
            "delete_by_ids",
            new=AsyncMock(return_value=0),
        ),
    ):
        result = await setup_draft.replace_recommended_for_section(
            1,
            "logging",
            [op],
            actor_id=99,
            labels={0: "bind mod_channel → #log"},
        )
    assert result.inserted_seqs == [10]
    assert result.conflicts == []
    insert_mock.assert_awaited_once()
    kwargs = insert_mock.await_args.kwargs
    assert kwargs["staging_kind"] == "recommended"
    assert kwargs["section_slug"] == "logging"


@pytest.mark.asyncio
async def test_replace_recommended_is_idempotent_on_repeat():
    """Calling twice with the same ops produces one row per slot.

    The helper deletes the prior recommended rows for the section
    before inserting fresh ones.  This is what the wizard relies on
    so a double-click on ``Apply recommended`` does not stage
    duplicates.
    """
    op = SetupOperation(
        kind="bind_channel",
        subsystem="logging",
        binding_name="mod_channel",
        target_id=999,
        target_kind="channel",
    )
    existing = [
        _row(
            id=33,
            seq=2,
            op_kind="bind_channel",
            binding_name="mod_channel",
            section_slug="logging",
            staging_kind="recommended",
            target_id=999,
        ),
    ]
    list_mock = AsyncMock(return_value=existing)
    insert_mock = AsyncMock(side_effect=[20])
    delete_mock = AsyncMock(return_value=1)
    with (
        patch.object(setup_draft.db, "list_rows", new=list_mock),
        patch.object(setup_draft.db, "insert", new=insert_mock),
        patch.object(setup_draft.db, "delete_by_ids", new=delete_mock),
    ):
        result = await setup_draft.replace_recommended_for_section(
            1,
            "logging",
            [op],
            actor_id=99,
        )
    # The prior recommended row was deleted by id, then the new row
    # was inserted as the only recommended row for the slot.
    delete_mock.assert_awaited_once_with(1, [33])
    assert result.deleted_count == 1
    assert result.inserted_seqs == [20]
    assert result.conflicts == []


@pytest.mark.asyncio
async def test_replace_recommended_refuses_to_overwrite_custom_row():
    """A non-recommended row at the same slot must not be overwritten."""
    op = SetupOperation(
        kind="bind_channel",
        subsystem="logging",
        binding_name="mod_channel",
        target_id=999,
        target_kind="channel",
    )
    existing = [
        _row(
            id=33,
            seq=2,
            op_kind="bind_channel",
            binding_name="mod_channel",
            section_slug="logging",
            staging_kind="custom",
            target_id=42,
            label="custom: mod_channel → #custom",
        ),
    ]
    list_mock = AsyncMock(return_value=existing)
    insert_mock = AsyncMock()
    delete_mock = AsyncMock(return_value=0)
    with (
        patch.object(setup_draft.db, "list_rows", new=list_mock),
        patch.object(setup_draft.db, "insert", new=insert_mock),
        patch.object(setup_draft.db, "delete_by_ids", new=delete_mock),
    ):
        result = await setup_draft.replace_recommended_for_section(
            1,
            "logging",
            [op],
            actor_id=99,
        )
    # The custom row was preserved: no recommended rows for this
    # section existed, so the delete short-circuited at the service
    # layer and never hit the DB primitive.
    delete_mock.assert_not_called()
    insert_mock.assert_not_called()  # refused, did not overwrite
    assert result.inserted_seqs == []
    assert len(result.conflicts) == 1
    conflict = result.conflicts[0]
    assert conflict.existing_row.staging_kind == "custom"
    assert conflict.existing_row.id == 33


@pytest.mark.asyncio
async def test_replace_recommended_preserves_other_sections_rows():
    """Recommended rows owned by a DIFFERENT section are not deleted."""
    op = SetupOperation(
        kind="bind_channel",
        subsystem="logging",
        binding_name="mod_channel",
        target_id=999,
        target_kind="channel",
    )
    other_section_row = _row(
        id=50,
        seq=4,
        op_kind="bind_channel",
        binding_name="join_channel",
        section_slug="other_section",  # different section
        staging_kind="recommended",
        target_id=111,
    )
    list_mock = AsyncMock(return_value=[other_section_row])
    insert_mock = AsyncMock(side_effect=[60])
    delete_mock = AsyncMock(return_value=0)
    with (
        patch.object(setup_draft.db, "list_rows", new=list_mock),
        patch.object(setup_draft.db, "insert", new=insert_mock),
        patch.object(setup_draft.db, "delete_by_ids", new=delete_mock),
    ):
        await setup_draft.replace_recommended_for_section(
            1,
            "logging",
            [op],
            actor_id=99,
        )
    # No prior recommended rows in THIS section, so the service-level
    # delete short-circuits and the DB primitive is never invoked.
    # The "other_section" recommended row is untouched.
    delete_mock.assert_not_called()


@pytest.mark.asyncio
async def test_replace_recommended_empty_section_slug_rejected():
    with pytest.raises(ValueError, match="section_slug"):
        await setup_draft.replace_recommended_for_section(
            1,
            "",
            [],
            actor_id=99,
        )
