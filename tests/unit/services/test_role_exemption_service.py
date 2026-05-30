"""Tests for services.role_exemption_service (read composition + audited writes)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from services import role_exemption_service as res


@pytest.mark.asyncio
async def test_get_exempt_role_ids_composes_xp_and_time_sets():
    rows = [
        {"role_id": 10, "exempt_xp": True, "exempt_time": False},
        {"role_id": 20, "exempt_xp": False, "exempt_time": True},
        {"role_id": 30, "exempt_xp": True, "exempt_time": True},
    ]
    with patch.object(res.gca, "get_role_exemptions", new=AsyncMock(return_value=rows)):
        out = await res.get_exempt_role_ids(1)
    assert out.xp == frozenset({10, 30})
    assert out.time == frozenset({20, 30})


@pytest.mark.asyncio
async def test_set_exemption_upserts_invalidates_and_audits():
    with (
        patch.object(res.db, "get_role_exemptions", new=AsyncMock(return_value=[])),
        patch.object(res.db, "set_role_exemption", new=AsyncMock()) as set_mock,
        patch.object(res.db, "clear_role_exemption", new=AsyncMock()) as clear_mock,
        patch.object(res.gca, "invalidate_role_exemptions") as inval_mock,
        patch(
            "services.audit_events.emit_audit_action",
            new=AsyncMock(return_value=True),
        ) as audit_mock,
    ):
        await res.set_exemption(1, 10, exempt_xp=True, exempt_time=False, actor_id=99)

    set_mock.assert_awaited_once()
    clear_mock.assert_not_awaited()
    inval_mock.assert_called_once_with(1)
    audit_mock.assert_awaited_once()
    # The audit row names the role + the new flags.
    kwargs = audit_mock.await_args.kwargs
    assert kwargs["subsystem"] == "role"
    assert kwargs["target"] == "role:10"
    assert "xp=True" in kwargs["new_value"]


@pytest.mark.asyncio
async def test_set_exemption_deletes_row_when_both_flags_clear():
    rows = [{"role_id": 10, "exempt_xp": True, "exempt_time": False}]
    with (
        patch.object(res.db, "get_role_exemptions", new=AsyncMock(return_value=rows)),
        patch.object(res.db, "set_role_exemption", new=AsyncMock()) as set_mock,
        patch.object(res.db, "clear_role_exemption", new=AsyncMock()) as clear_mock,
        patch.object(res.gca, "invalidate_role_exemptions"),
        patch(
            "services.audit_events.emit_audit_action",
            new=AsyncMock(return_value=True),
        ),
    ):
        await res.set_exemption(1, 10, exempt_xp=False, exempt_time=False, actor_id=99)

    clear_mock.assert_awaited_once_with(1, 10)
    set_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_stacking_toggles_resolve_with_correct_defaults():
    with patch(
        "services.settings_resolution.resolve_value",
        new=AsyncMock(side_effect=[True, False]),
    ) as rv:
        assert await res.time_roles_stack(1) is True
        assert await res.xp_roles_stack(1) is False

    # time default is False (single), xp default is True (stack).
    assert rv.await_args_list[0].args == (1, "role", "time_roles_stack", False)
    assert rv.await_args_list[1].args == (1, "role", "xp_roles_stack", True)
