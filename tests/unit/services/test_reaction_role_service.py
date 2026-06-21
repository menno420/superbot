"""Tests for services.reaction_role_service — the audited reaction-role seam.

Pins the finding this module closes: reaction-role config writes now emit
``audit.action_recorded`` (subsystem ``role``) like every other role mutation,
instead of going straight to the DB layer from the cog.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from services import reaction_role_service as rrs


@pytest.mark.asyncio
async def test_bind_emoji_persists_and_audits():
    with (
        patch.object(rrs.db, "add_reaction_role", new=AsyncMock()) as add_mock,
        patch(
            "services.audit_events.emit_audit_action",
            new=AsyncMock(return_value=True),
        ) as audit_mock,
    ):
        await rrs.bind_emoji(1, 555, "🎮", 42, actor_id=99)

    add_mock.assert_awaited_once_with(1, 555, "🎮", 42)
    audit_mock.assert_awaited_once()
    kwargs = audit_mock.await_args.kwargs
    assert kwargs["subsystem"] == "role"
    assert kwargs["mutation_type"] == "set_reaction_role"
    assert kwargs["target"] == "role:42"
    assert kwargs["guild_id"] == 1
    assert kwargs["actor_id"] == 99
    assert "message=555" in kwargs["new_value"]
    assert "emoji=🎮" in kwargs["new_value"]


@pytest.mark.asyncio
async def test_unbind_emoji_reads_prev_role_then_removes_and_audits():
    with (
        patch.object(
            rrs.db,
            "get_reaction_role",
            new=AsyncMock(return_value=42),
        ) as get_mock,
        patch.object(rrs.db, "remove_reaction_role", new=AsyncMock()) as rm_mock,
        patch(
            "services.audit_events.emit_audit_action",
            new=AsyncMock(return_value=True),
        ) as audit_mock,
    ):
        await rrs.unbind_emoji(1, 555, "🎮", actor_id=99)

    get_mock.assert_awaited_once_with(1, 555, "🎮")
    rm_mock.assert_awaited_once_with(1, 555, "🎮")
    kwargs = audit_mock.await_args.kwargs
    assert kwargs["mutation_type"] == "remove_reaction_role"
    # The audit row names the role that *was* bound (resolved before removal).
    assert kwargs["target"] == "role:42"
    assert kwargs["new_value"] is None


@pytest.mark.asyncio
async def test_unbind_unknown_binding_audits_without_a_role():
    with (
        patch.object(rrs.db, "get_reaction_role", new=AsyncMock(return_value=None)),
        patch.object(rrs.db, "remove_reaction_role", new=AsyncMock()),
        patch(
            "services.audit_events.emit_audit_action",
            new=AsyncMock(return_value=True),
        ) as audit_mock,
    ):
        await rrs.unbind_emoji(1, 555, "❓", actor_id=99)

    # No role resolved → the audit target falls back, never raises.
    assert audit_mock.await_args.kwargs["target"] == "role:unknown"


@pytest.mark.asyncio
async def test_reads_pass_through_to_db():
    with (
        patch.object(
            rrs.db,
            "get_reaction_role",
            new=AsyncMock(return_value=7),
        ) as get_mock,
        patch.object(
            rrs.db,
            "get_all_reaction_roles",
            new=AsyncMock(return_value=[{"x": 1}]),
        ) as list_mock,
    ):
        assert await rrs.get_binding(1, 555, "🎮") == 7
        assert await rrs.list_bindings(1) == [{"x": 1}]

    get_mock.assert_awaited_once_with(1, 555, "🎮")
    list_mock.assert_awaited_once_with(1)
