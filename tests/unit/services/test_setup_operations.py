"""Setup operation dispatcher tests — PR 1.

Pins:

* ``validate_operation`` accepts every known OperationKind and rejects
  unknown kinds as ``not_yet_implemented``.
* ``operations_from_recommendations`` maps each ``target_kind`` to the
  correct ``bind_*`` kind and surfaces unknown target kinds as
  not-yet-implemented operations rather than silently dropping them.
* ``apply_operations`` routes each kind to the correct pipeline mock.
* Batch apply isolates failure: one failed operation does not abort later
  ones.
* Result objects carry stable fields: ``status``, ``label``, ``mutation_id``
  (when available), and ``error`` (when failed/not_yet_implemented).
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.setup_operations import (
    SetupOperation,
    SetupOperationBatchResult,
    SetupOperationResult,
    apply_operations,
    operations_from_recommendations,
    preview_operations,
    validate_operation,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _guild(guild_id: int = 1, owner_id: int = 99):
    g = MagicMock()
    g.id = guild_id
    g.owner_id = owner_id
    return g


def _actor(actor_id: int = 99):
    m = MagicMock()
    m.id = actor_id
    m.guild = SimpleNamespace(owner_id=actor_id)
    return m


def _bind_op(
    kind: str = "bind_channel",
    subsystem: str = "logging",
    binding_name: str = "mod_channel",
    target_id: int = 100,
    target_name: str = "mod-log",
    target_kind: str = "channel",
) -> SetupOperation:
    return SetupOperation(
        kind=kind,
        subsystem=subsystem,
        binding_name=binding_name,
        target_id=target_id,
        target_name=target_name,
        target_kind=target_kind,
    )


def _rec(
    subsystem: str = "logging",
    binding_name: str = "mod_channel",
    target_kind: str = "channel",
    target_id: int = 100,
    target_name: str = "mod-log",
    confidence: str = "high",
):
    # Use SimpleNamespace to avoid the deep asyncpg import chain that
    # services.setup_plan → services.guild_snapshot → utils.db.pool triggers.
    # operations_from_recommendations uses duck-typing, so this is fine.
    return SimpleNamespace(
        subsystem=subsystem,
        binding_name=binding_name,
        target_kind=target_kind,
        target_id=target_id,
        target_name=target_name,
        confidence=confidence,
        source="deterministic",
        reason="test",
    )


# ---------------------------------------------------------------------------
# validate_operation
# ---------------------------------------------------------------------------


def test_validate_operation_known_kind_returns_none():
    from services.setup_operations import _KNOWN_KINDS

    for kind in _KNOWN_KINDS:
        op = SetupOperation(kind=kind, subsystem="logging")
        assert validate_operation(op) is None, f"expected None for known kind {kind!r}"


def test_validate_operation_unknown_kind_returns_not_yet_implemented():
    op = SetupOperation(kind="totally_made_up_kind", subsystem="logging")
    result = validate_operation(op)
    assert result is not None
    assert result.status == "not_yet_implemented"
    assert "totally_made_up_kind" in (result.error or "")


def test_validate_operation_result_carries_operation_reference():
    op = SetupOperation(kind="unknown_xyz", subsystem="logging")
    result = validate_operation(op)
    assert result is not None
    assert result.operation is op


# ---------------------------------------------------------------------------
# operations_from_recommendations
# ---------------------------------------------------------------------------


def test_operations_from_recommendations_maps_channel():
    ops = operations_from_recommendations([_rec(target_kind="channel")])
    assert len(ops) == 1
    assert ops[0].kind == "bind_channel"


def test_operations_from_recommendations_maps_role():
    ops = operations_from_recommendations([_rec(target_kind="role")])
    assert ops[0].kind == "bind_role"


def test_operations_from_recommendations_maps_category():
    ops = operations_from_recommendations([_rec(target_kind="category")])
    assert ops[0].kind == "bind_category"


def test_operations_from_recommendations_maps_thread():
    ops = operations_from_recommendations([_rec(target_kind="thread")])
    assert ops[0].kind == "bind_thread"


def test_operations_from_recommendations_maps_member():
    ops = operations_from_recommendations([_rec(target_kind="member")])
    assert ops[0].kind == "bind_member"


def test_operations_from_recommendations_preserves_fields():
    rec = _rec(
        subsystem="logging",
        binding_name="mod_channel",
        target_id=42,
        target_name="mod-log",
        target_kind="channel",
    )
    ops = operations_from_recommendations([rec])
    op = ops[0]
    assert op.subsystem == "logging"
    assert op.binding_name == "mod_channel"
    assert op.target_id == 42
    assert op.target_name == "mod-log"
    assert op.target_kind == "channel"


def test_operations_from_recommendations_unknown_target_kind_not_silently_dropped():
    """Unknown target_kind produces an operation that the dispatcher surfaces as
    not_yet_implemented rather than silently omitting it from the batch."""
    ops = operations_from_recommendations([_rec(target_kind="webhook")])
    assert len(ops) == 1
    # The kind won't be in _KNOWN_KINDS, so validate_operation will flag it.
    result = validate_operation(ops[0])
    assert result is not None
    assert result.status == "not_yet_implemented"


def test_operations_from_recommendations_metadata_carries_confidence():
    rec = _rec(confidence="medium")
    ops = operations_from_recommendations([rec])
    meta = ops[0].metadata or {}
    assert meta.get("confidence") == "medium"


def test_operations_from_recommendations_empty_list_returns_empty():
    assert operations_from_recommendations([]) == []


# ---------------------------------------------------------------------------
# preview_operations
# ---------------------------------------------------------------------------


def test_preview_operations_known_kinds_all_applied():
    ops = [_bind_op("bind_channel"), _bind_op("bind_role", target_kind="role")]
    results = preview_operations(ops)
    assert all(r.status == "applied" for r in results)


def test_preview_operations_unknown_kind_returns_not_yet_implemented():
    ops = [SetupOperation(kind="bind_webhook", subsystem="x")]
    results = preview_operations(ops)
    assert results[0].status == "not_yet_implemented"


# ---------------------------------------------------------------------------
# apply_operations — binding path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_binding_operation_routes_through_binding_pipeline():
    mock_result = MagicMock(mutation_id="m-001")
    mock_pipeline = MagicMock()
    mock_pipeline.set_binding = AsyncMock(return_value=mock_result)

    op = _bind_op(kind="bind_channel", target_kind="channel")
    # Pipelines are lazily imported inside dispatch functions, so patch the source.
    with patch(
        "services.binding_mutation.BindingMutationPipeline",
        return_value=mock_pipeline,
    ):
        batch = await apply_operations([op], guild=_guild(), actor=_actor())

    mock_pipeline.set_binding.assert_awaited_once()
    assert len(batch.applied) == 1
    assert batch.applied[0].mutation_id == "m-001"
    assert batch.applied[0].status == "applied"


@pytest.mark.asyncio
async def test_apply_clear_binding_routes_through_binding_pipeline():
    mock_result = MagicMock(mutation_id="m-clr")
    mock_pipeline = MagicMock()
    mock_pipeline.clear_binding = AsyncMock(return_value=mock_result)

    op = SetupOperation(
        kind="clear_binding",
        subsystem="logging",
        binding_name="mod_channel",
        target_kind="channel",
    )
    with patch(
        "services.binding_mutation.BindingMutationPipeline",
        return_value=mock_pipeline,
    ):
        batch = await apply_operations([op], guild=_guild(), actor=_actor())

    mock_pipeline.clear_binding.assert_awaited_once()
    assert len(batch.applied) == 1
    assert batch.applied[0].mutation_id == "m-clr"


# ---------------------------------------------------------------------------
# apply_operations — settings path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_setting_operation_routes_through_settings_pipeline():
    mock_result = MagicMock(mutation_id="m-set")
    mock_pipeline = MagicMock()
    mock_pipeline.set_value = AsyncMock(return_value=mock_result)

    op = SetupOperation(
        kind="set_setting",
        subsystem="economy",
        setting_name="daily_coins",
        value=100,
    )
    with patch(
        "services.settings_mutation.SettingsMutationPipeline",
        return_value=mock_pipeline,
    ):
        batch = await apply_operations([op], guild=_guild(), actor=_actor())

    mock_pipeline.set_value.assert_awaited_once()
    assert len(batch.applied) == 1
    assert batch.applied[0].mutation_id == "m-set"


# ---------------------------------------------------------------------------
# apply_operations — automation path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_automation_create_routes_through_automation_pipeline():
    mock_result = MagicMock(mutation_id="m-auto")
    mock_pipeline = MagicMock()
    mock_pipeline.create_rule = AsyncMock(return_value=mock_result)

    op = SetupOperation(
        kind="add_automation_rule",
        subsystem="automation",
        automation_rule_name="daily-summary",
        trigger_kind="schedule",
        action_kind="post_readiness_summary",
    )
    with patch(
        "services.automation_mutation.AutomationMutationPipeline",
        return_value=mock_pipeline,
    ):
        batch = await apply_operations([op], guild=_guild(), actor=_actor())

    mock_pipeline.create_rule.assert_awaited_once()
    assert len(batch.applied) == 1
    assert batch.applied[0].mutation_id == "m-auto"


@pytest.mark.asyncio
async def test_apply_automation_enable_routes_through_automation_pipeline():
    mock_result = MagicMock(mutation_id="m-en")
    mock_pipeline = MagicMock()
    mock_pipeline.set_enabled = AsyncMock(return_value=mock_result)

    op = SetupOperation(
        kind="enable_automation_rule",
        subsystem="automation",
        automation_rule_id=7,
    )
    with patch(
        "services.automation_mutation.AutomationMutationPipeline",
        return_value=mock_pipeline,
    ):
        batch = await apply_operations([op], guild=_guild(), actor=_actor())

    mock_pipeline.set_enabled.assert_awaited_once()
    call_kwargs = mock_pipeline.set_enabled.await_args.kwargs
    assert call_kwargs["enabled"] is True
    assert call_kwargs["rule_id"] == 7


@pytest.mark.asyncio
async def test_apply_automation_disable_passes_enabled_false():
    mock_result = MagicMock(mutation_id="m-dis")
    mock_pipeline = MagicMock()
    mock_pipeline.set_enabled = AsyncMock(return_value=mock_result)

    op = SetupOperation(
        kind="disable_automation_rule",
        subsystem="automation",
        automation_rule_id=3,
    )
    with patch(
        "services.automation_mutation.AutomationMutationPipeline",
        return_value=mock_pipeline,
    ):
        batch = await apply_operations([op], guild=_guild(), actor=_actor())

    call_kwargs = mock_pipeline.set_enabled.await_args.kwargs
    assert call_kwargs["enabled"] is False


# ---------------------------------------------------------------------------
# apply_operations — resource provisioning path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_create_channel_routes_through_provisioning_pipeline():
    mock_result = MagicMock(mutation_id="m-prov")
    mock_pipeline = MagicMock()
    mock_pipeline.provision = AsyncMock(return_value=mock_result)

    op = SetupOperation(
        kind="create_channel",
        subsystem="logging",
        binding_name="mod_channel",
        resource_name="mod-log",
    )
    with patch(
        "services.resource_provisioning.ResourceProvisioningPipeline",
        return_value=mock_pipeline,
    ):
        batch = await apply_operations([op], guild=_guild(), actor=_actor())

    mock_pipeline.provision.assert_awaited_once()
    assert len(batch.applied) == 1
    assert batch.applied[0].mutation_id == "m-prov"


# ---------------------------------------------------------------------------
# Batch isolation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_batch_isolates_failure_one_failed_does_not_abort_others():
    mock_pipeline = MagicMock()
    mock_pipeline.set_binding = AsyncMock(
        side_effect=[
            MagicMock(mutation_id="m-ok"),
            RuntimeError("boom"),
            MagicMock(mutation_id="m-ok2"),
        ]
    )

    ops = [
        _bind_op(target_id=1),
        _bind_op(target_id=2),
        _bind_op(target_id=3),
    ]
    with patch(
        "services.binding_mutation.BindingMutationPipeline",
        return_value=mock_pipeline,
    ):
        batch = await apply_operations(ops, guild=_guild(), actor=_actor())

    assert len(batch.applied) == 2
    assert len(batch.failed) == 1
    assert "boom" in (batch.failed[0].error or "")
    # total results == total ops
    assert len(batch.results) == 3


@pytest.mark.asyncio
async def test_not_yet_implemented_kind_does_not_abort_batch():
    """An unrecognised kind in a batch is surfaced as not_yet_implemented
    and subsequent operations still execute."""
    mock_pipeline = MagicMock()
    mock_pipeline.set_binding = AsyncMock(return_value=MagicMock(mutation_id="m-ok"))

    ops = [
        SetupOperation(kind="bind_webhook", subsystem="x"),  # unknown
        _bind_op(),  # known
    ]
    with patch(
        "services.binding_mutation.BindingMutationPipeline",
        return_value=mock_pipeline,
    ):
        batch = await apply_operations(ops, guild=_guild(), actor=_actor())

    assert len(batch.not_yet_implemented) == 1
    assert len(batch.applied) == 1
    assert len(batch.results) == 2


# ---------------------------------------------------------------------------
# Result shape invariants
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_result_applied_has_mutation_id_and_no_error():
    mock_result = MagicMock(mutation_id="m-shape")
    mock_pipeline = MagicMock()
    mock_pipeline.set_binding = AsyncMock(return_value=mock_result)

    with patch(
        "services.binding_mutation.BindingMutationPipeline",
        return_value=mock_pipeline,
    ):
        batch = await apply_operations([_bind_op()], guild=_guild(), actor=_actor())

    r = batch.applied[0]
    assert r.status == "applied"
    assert r.mutation_id == "m-shape"
    assert r.error is None
    assert r.label != ""


@pytest.mark.asyncio
async def test_result_failed_has_error_text_and_no_mutation_id():
    mock_pipeline = MagicMock()
    mock_pipeline.set_binding = AsyncMock(side_effect=ValueError("bad value"))

    with patch(
        "services.binding_mutation.BindingMutationPipeline",
        return_value=mock_pipeline,
    ):
        batch = await apply_operations([_bind_op()], guild=_guild(), actor=_actor())

    r = batch.failed[0]
    assert r.status == "failed"
    assert "bad value" in (r.error or "")
    assert r.mutation_id is None
    assert r.label != ""


def test_result_not_yet_implemented_carries_kind_in_error():
    op = SetupOperation(kind="bind_smoke_signal", subsystem="y")
    result = validate_operation(op)
    assert result is not None
    assert result.status == "not_yet_implemented"
    assert "bind_smoke_signal" in (result.error or "")
    assert result.label != ""


# ---------------------------------------------------------------------------
# SetupOperationBatchResult partition helpers
# ---------------------------------------------------------------------------


def test_batch_result_partitions_are_consistent():
    ops_result = [
        SetupOperationResult(status="applied", operation=_bind_op(), label="a"),
        SetupOperationResult(
            status="failed", operation=_bind_op(), label="b", error="e"
        ),
        SetupOperationResult(status="skipped", operation=_bind_op(), label="c"),
        SetupOperationResult(
            status="not_yet_implemented", operation=_bind_op(), label="d", error="nyi"
        ),
    ]
    batch = SetupOperationBatchResult(results=ops_result)
    assert len(batch.applied) == 1
    assert len(batch.failed) == 1
    assert len(batch.skipped) == 1
    assert len(batch.not_yet_implemented) == 1
    assert batch.applied[0].label == "a"
    assert batch.failed[0].label == "b"
    assert batch.skipped[0].label == "c"
    assert batch.not_yet_implemented[0].label == "d"
