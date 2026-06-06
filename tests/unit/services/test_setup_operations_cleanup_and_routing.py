"""Dispatcher tests for ``set_cleanup_policy`` and ``set_cog_routing``.

These two op kinds were registered in PR #233 but routed to
``not_yet_implemented``.  This module pins the apply path that Final
Review uses:

* ``set_cleanup_policy`` goes through
  :func:`governance.writes.set_cleanup_policy_for_scope`, which
  handles the atomic DB write + governance audit row +
  ``audit.action_recorded`` event.
* ``set_cog_routing`` goes through
  :func:`services.command_routing.set_policy`, with an
  ``audit.action_recorded`` event emitted alongside so the apply is
  visible in the audit channel.

The tests stay asyncpg-free by patching the canonical writers.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from services.setup_operations import (
    _KNOWN_KINDS,
    SetupOperation,
    apply_operations,
    preview_operations,
    validate_operation,
)


def _guild(guild_id: int = 1, owner_id: int = 99):
    return SimpleNamespace(id=guild_id, owner_id=owner_id)


def _actor(actor_id: int = 99):
    return SimpleNamespace(id=actor_id)


# ---------------------------------------------------------------------------
# Registration / preview state
# ---------------------------------------------------------------------------


def test_set_cleanup_policy_is_a_known_kind():
    assert "set_cleanup_policy" in _KNOWN_KINDS


def test_set_cog_routing_is_a_known_kind():
    assert "set_cog_routing" in _KNOWN_KINDS


def test_validate_operation_accepts_set_cleanup_policy():
    op = SetupOperation(
        kind="set_cleanup_policy",
        subsystem="cleanup",
        target_kind="guild",
        value="Standard",
    )
    assert validate_operation(op) is None


def test_validate_operation_accepts_set_cog_routing():
    op = SetupOperation(
        kind="set_cog_routing",
        subsystem="cog_routing",
        target_kind="guild",
        value="games",
    )
    assert validate_operation(op) is None


def test_preview_operations_reports_applied_for_both_kinds():
    """Preview only inspects ``kind``; the dispatcher's routing arm is
    what proves the apply path.  Confirm both kinds round-trip as
    applied (not ``not_yet_implemented``).
    """
    ops = [
        SetupOperation(
            kind="set_cleanup_policy", subsystem="cleanup",
            target_kind="guild", value="Standard",
        ),
        SetupOperation(
            kind="set_cog_routing", subsystem="cog_routing",
            target_kind="guild", value="games",
        ),
    ]
    results = preview_operations(ops)
    assert [r.status for r in results] == ["applied", "applied"]


# ---------------------------------------------------------------------------
# set_cleanup_policy — dispatch
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_cleanup_policy_routes_through_governance_writer():
    op = SetupOperation(
        kind="set_cleanup_policy",
        subsystem="cleanup",
        target_kind="guild",
        target_id=None,
        target_name="guild",
        value="Standard",
    )
    with patch(
        "governance.writes.set_cleanup_policy_for_scope",
        new_callable=AsyncMock,
    ) as writer:
        batch = await apply_operations([op], guild=_guild(), actor=_actor())

    writer.assert_awaited_once()
    kwargs = writer.await_args.kwargs
    # Standard level → invalid+failed delete, 5s.
    assert kwargs["delete_invalid_commands"] is True
    assert kwargs["delete_failed_commands"] is True
    assert kwargs["delete_after_seconds"] == 5
    # Positional args: ctx, scope_type, scope_id.
    ctx_arg, scope_type, scope_id = writer.await_args.args
    assert scope_type == "guild"
    # Guild scope is keyed by guild_id (NOT 0): the resolver looks up guild
    # policy at scope_id=guild_id, so 0 was a silent no-op.  See
    # services.cleanup_levels.cleanup_scope_id.
    assert scope_id == 1  # == _guild().id
    assert ctx_arg.guild_id == 1
    assert ctx_arg.member is not None  # actor passed through

    assert len(batch.applied) == 1
    assert batch.applied[0].status == "applied"
    assert batch.failed == []
    assert batch.not_yet_implemented == []


@pytest.mark.asyncio
async def test_set_cleanup_policy_passes_through_each_level():
    """Every operator-facing level maps to the right column values."""
    from services.cleanup_levels import LEVELS

    for level_name, expected in LEVELS.items():
        op = SetupOperation(
            kind="set_cleanup_policy",
            subsystem="cleanup",
            target_kind="guild",
            value=level_name,
        )
        with patch(
            "governance.writes.set_cleanup_policy_for_scope",
            new_callable=AsyncMock,
        ) as writer:
            batch = await apply_operations([op], guild=_guild(), actor=_actor())
        kwargs = writer.await_args.kwargs
        assert kwargs["delete_invalid_commands"] == expected["delete_invalid_commands"]
        assert kwargs["delete_failed_commands"] == expected["delete_failed_commands"]
        assert kwargs["delete_after_seconds"] == expected["delete_after_seconds"]
        assert len(batch.applied) == 1, f"{level_name}: not applied"


@pytest.mark.asyncio
async def test_set_cleanup_policy_passes_category_scope_id():
    op = SetupOperation(
        kind="set_cleanup_policy",
        subsystem="cleanup",
        target_kind="category",
        target_id=42,
        target_name="Staff",
        value="Strict",
    )
    with patch(
        "governance.writes.set_cleanup_policy_for_scope",
        new_callable=AsyncMock,
    ) as writer:
        await apply_operations([op], guild=_guild(), actor=_actor())
    _, scope_type, scope_id = writer.await_args.args
    assert scope_type == "category"
    assert scope_id == 42


@pytest.mark.asyncio
async def test_set_cleanup_policy_rejects_unknown_scope_type():
    op = SetupOperation(
        kind="set_cleanup_policy",
        subsystem="cleanup",
        target_kind="role",  # cleanup_policies doesn't support role scope
        target_id=1,
        value="Strict",
    )
    with patch(
        "governance.writes.set_cleanup_policy_for_scope",
        new_callable=AsyncMock,
    ) as writer:
        batch = await apply_operations([op], guild=_guild(), actor=_actor())
    writer.assert_not_awaited()
    assert len(batch.failed) == 1
    assert "target_kind" in batch.failed[0].error


@pytest.mark.asyncio
async def test_set_cleanup_policy_rejects_unknown_level():
    op = SetupOperation(
        kind="set_cleanup_policy",
        subsystem="cleanup",
        target_kind="guild",
        value="Nuclear",  # not a known level
    )
    with patch(
        "governance.writes.set_cleanup_policy_for_scope",
        new_callable=AsyncMock,
    ) as writer:
        batch = await apply_operations([op], guild=_guild(), actor=_actor())
    writer.assert_not_awaited()
    assert len(batch.failed) == 1
    assert "level" in batch.failed[0].error


@pytest.mark.asyncio
async def test_set_cleanup_policy_rejects_category_without_target_id():
    op = SetupOperation(
        kind="set_cleanup_policy",
        subsystem="cleanup",
        target_kind="category",
        target_id=None,  # category scope must carry an id
        value="Strict",
    )
    with patch(
        "governance.writes.set_cleanup_policy_for_scope",
        new_callable=AsyncMock,
    ) as writer:
        batch = await apply_operations([op], guild=_guild(), actor=_actor())
    writer.assert_not_awaited()
    assert len(batch.failed) == 1
    assert "target_id" in batch.failed[0].error


@pytest.mark.asyncio
async def test_set_cleanup_policy_surfaces_writer_failure_per_op():
    """A writer raise should turn into a per-op `failed` result —
    other ops in the same batch keep running.
    """
    failing = SetupOperation(
        kind="set_cleanup_policy", subsystem="cleanup",
        target_kind="guild", value="Standard",
    )
    succeeding = SetupOperation(
        kind="set_cleanup_policy", subsystem="cleanup",
        target_kind="channel", target_id=999, value="Off",
    )
    calls = {"n": 0}

    async def writer(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("simulated DB down")
        return None

    with patch("governance.writes.set_cleanup_policy_for_scope", new=writer):
        batch = await apply_operations(
            [failing, succeeding], guild=_guild(), actor=_actor(),
        )
    assert len(batch.failed) == 1
    assert "simulated DB down" in batch.failed[0].error
    assert len(batch.applied) == 1


# ---------------------------------------------------------------------------
# set_cog_routing — dispatch
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_cog_routing_routes_through_command_routing_service():
    op = SetupOperation(
        kind="set_cog_routing",
        subsystem="cog_routing",
        target_kind="guild",
        target_id=None,
        target_name="guild",
        value="games",
        metadata={"enabled": "false"},
    )
    with (
        patch(
            "services.command_routing.set_policy",
            new_callable=AsyncMock,
        ) as set_policy,
        patch(
            "services.audit_events.emit_audit_action",
            new_callable=AsyncMock,
        ),
    ):
        batch = await apply_operations([op], guild=_guild(), actor=_actor())

    set_policy.assert_awaited_once()
    kwargs = set_policy.await_args.kwargs
    assert kwargs["guild_id"] == 1
    assert kwargs["scope_type"] == "guild"
    assert kwargs["scope_id"] is None  # guild scope is NULL
    assert kwargs["cog_name"] == "games"
    assert kwargs["enabled"] is False
    assert kwargs["actor_id"] == 99
    assert len(batch.applied) == 1
    assert batch.applied[0].status == "applied"
    # The dispatcher generates a mutation_id even though routing rows
    # don't ship through a full mutation pipeline.
    assert batch.applied[0].mutation_id


@pytest.mark.asyncio
async def test_set_cog_routing_default_enabled_true_when_metadata_missing():
    """A drafting bug that omits ``metadata.enabled`` defaults to
    enabled — never silently disable a cog.
    """
    op = SetupOperation(
        kind="set_cog_routing", subsystem="cog_routing",
        target_kind="guild", value="games",
    )
    with (
        patch(
            "services.command_routing.set_policy",
            new_callable=AsyncMock,
        ) as set_policy,
        patch(
            "services.audit_events.emit_audit_action",
            new_callable=AsyncMock,
        ),
    ):
        await apply_operations([op], guild=_guild(), actor=_actor())
    assert set_policy.await_args.kwargs["enabled"] is True


@pytest.mark.asyncio
async def test_set_cog_routing_handles_bool_enabled_metadata():
    """Accept ``metadata.enabled`` as a real bool too, not just "true"/"false"."""
    op = SetupOperation(
        kind="set_cog_routing", subsystem="cog_routing",
        target_kind="guild", value="games",
        metadata={"enabled": False},
    )
    with (
        patch(
            "services.command_routing.set_policy",
            new_callable=AsyncMock,
        ) as set_policy,
        patch(
            "services.audit_events.emit_audit_action",
            new_callable=AsyncMock,
        ),
    ):
        await apply_operations([op], guild=_guild(), actor=_actor())
    assert set_policy.await_args.kwargs["enabled"] is False


@pytest.mark.asyncio
async def test_set_cog_routing_passes_scope_id_for_non_guild_scopes():
    op = SetupOperation(
        kind="set_cog_routing", subsystem="cog_routing",
        target_kind="channel", target_id=555, target_name="general",
        value="economy", metadata={"enabled": "true"},
    )
    with (
        patch(
            "services.command_routing.set_policy",
            new_callable=AsyncMock,
        ) as set_policy,
        patch(
            "services.audit_events.emit_audit_action",
            new_callable=AsyncMock,
        ),
    ):
        await apply_operations([op], guild=_guild(), actor=_actor())
    kwargs = set_policy.await_args.kwargs
    assert kwargs["scope_type"] == "channel"
    assert kwargs["scope_id"] == 555


@pytest.mark.asyncio
async def test_set_cog_routing_emits_audit_action_event():
    """Routing apply must surface in the canonical audit stream so the
    audit channel and audit-row dashboards see it.
    """
    op = SetupOperation(
        kind="set_cog_routing", subsystem="cog_routing",
        target_kind="channel", target_id=999, value="games",
        metadata={"enabled": "false"},
    )
    with (
        patch(
            "services.command_routing.set_policy",
            new_callable=AsyncMock,
        ),
        patch(
            "services.audit_events.emit_audit_action",
            new_callable=AsyncMock,
        ) as emit,
    ):
        await apply_operations([op], guild=_guild(), actor=_actor())
    emit.assert_awaited_once()
    kwargs = emit.await_args.kwargs
    assert kwargs["subsystem"] == "cog_routing"
    assert kwargs["mutation_type"] == "set_cog_routing"
    assert kwargs["scope"] == "channel"
    assert kwargs["guild_id"] == 1
    assert kwargs["actor_id"] == 99
    assert kwargs["new_value"] == "disabled"


@pytest.mark.asyncio
async def test_set_cog_routing_rejects_unknown_scope_type():
    op = SetupOperation(
        kind="set_cog_routing", subsystem="cog_routing",
        target_kind="thread",  # routing supports guild/category/channel only
        target_id=1, value="games",
    )
    with patch(
        "services.command_routing.set_policy",
        new_callable=AsyncMock,
    ) as set_policy:
        batch = await apply_operations([op], guild=_guild(), actor=_actor())
    set_policy.assert_not_awaited()
    assert len(batch.failed) == 1
    assert "target_kind" in batch.failed[0].error


@pytest.mark.asyncio
async def test_set_cog_routing_rejects_empty_cog_name():
    op = SetupOperation(
        kind="set_cog_routing", subsystem="cog_routing",
        target_kind="guild", value="",
    )
    with patch(
        "services.command_routing.set_policy",
        new_callable=AsyncMock,
    ) as set_policy:
        batch = await apply_operations([op], guild=_guild(), actor=_actor())
    set_policy.assert_not_awaited()
    assert len(batch.failed) == 1
    assert "cog name" in batch.failed[0].error


@pytest.mark.asyncio
async def test_set_cog_routing_rejects_non_guild_scope_without_target_id():
    op = SetupOperation(
        kind="set_cog_routing", subsystem="cog_routing",
        target_kind="category", target_id=None, value="games",
    )
    with patch(
        "services.command_routing.set_policy",
        new_callable=AsyncMock,
    ) as set_policy:
        batch = await apply_operations([op], guild=_guild(), actor=_actor())
    set_policy.assert_not_awaited()
    assert len(batch.failed) == 1
    assert "target_id" in batch.failed[0].error


# ---------------------------------------------------------------------------
# No `not_yet_implemented` leftovers
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_neither_kind_returns_not_yet_implemented_after_wiring():
    """Smoke-check the regression these PRs aim to close: neither of
    the two newly-wired kinds may surface as ``not_yet_implemented``
    when patched canonical writers succeed.
    """
    ops = [
        SetupOperation(
            kind="set_cleanup_policy", subsystem="cleanup",
            target_kind="guild", value="Off",
        ),
        SetupOperation(
            kind="set_cog_routing", subsystem="cog_routing",
            target_kind="guild", value="games",
            metadata={"enabled": "true"},
        ),
    ]
    with (
        patch(
            "governance.writes.set_cleanup_policy_for_scope",
            new_callable=AsyncMock,
        ),
        patch(
            "services.command_routing.set_policy",
            new_callable=AsyncMock,
        ),
        patch(
            "services.audit_events.emit_audit_action",
            new_callable=AsyncMock,
        ),
    ):
        batch = await apply_operations(ops, guild=_guild(), actor=_actor())
    assert batch.not_yet_implemented == []
    assert len(batch.applied) == 2


# ---------------------------------------------------------------------------
# Final Review phase ordering — cleanup before cog_routing before automation
# ---------------------------------------------------------------------------


def test_phase_order_keeps_cleanup_before_cog_routing():
    """The wizard's Final Review applies cleanup before routing so a
    routing-table miss for a still-being-cleaned channel doesn't
    surprise anyone.  Pin the order here so a future _PHASE_ORDER
    edit can't silently reorder them.
    """
    from views.setup.final_review import _PHASE_ORDER

    cleanup_idx = next(
        i for i, (name, _) in enumerate(_PHASE_ORDER) if name == "cleanup_policy"
    )
    routing_idx = next(
        i for i, (name, _) in enumerate(_PHASE_ORDER) if name == "cog_routing"
    )
    automation_idx = next(
        i for i, (name, _) in enumerate(_PHASE_ORDER) if name == "automation_add"
    )
    assert cleanup_idx < routing_idx < automation_idx


@pytest.mark.asyncio
async def test_final_review_apply_ops_in_order_applies_both_kinds():
    """End-to-end: a mixed batch (cleanup + routing) applied via
    Final Review's _apply_ops_in_order routes through both writers
    in phase order.
    """
    from views.setup.final_review import _apply_ops_in_order

    ops = [
        SetupOperation(
            kind="set_cog_routing", subsystem="cog_routing",
            target_kind="guild", value="games",
            metadata={"enabled": "true"},
        ),
        SetupOperation(
            kind="set_cleanup_policy", subsystem="cleanup",
            target_kind="guild", value="Standard",
        ),
    ]
    with (
        patch(
            "governance.writes.set_cleanup_policy_for_scope",
            new_callable=AsyncMock,
        ) as cleanup_writer,
        patch(
            "services.command_routing.set_policy",
            new_callable=AsyncMock,
        ) as routing_writer,
        patch(
            "services.audit_events.emit_audit_action",
            new_callable=AsyncMock,
        ),
    ):
        summary = await _apply_ops_in_order(
            ops, guild=_guild(), actor=_actor(),
        )

    cleanup_writer.assert_awaited_once()
    routing_writer.assert_awaited_once()
    assert len(summary.applied) == 2
    assert summary.failed == []
    # Phase order: cleanup_policy (4) before cog_routing (5).
    assert "cleanup" in summary.applied[0].lower()
    assert "cog_routing" in summary.applied[1].lower()
