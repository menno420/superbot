"""XP level-role grants honour exemptions + the xp_roles_stack toggle."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cogs.xp import listener
from services.role_exemption_service import ExemptRoleIds


def _apply_result(succeeded: int = 1, failed: int = 0) -> SimpleNamespace:
    return SimpleNamespace(succeeded=succeeded, failed=failed, failures=())


_XP_ROWS = [
    {"role_name": "Lvl5", "level_required": 5},
    {"role_name": "Lvl10", "level_required": 10},
]


def _role(rid: int, name: str) -> SimpleNamespace:
    return SimpleNamespace(id=rid, name=name)


def _message(member_roles: list) -> tuple[MagicMock, MagicMock]:
    member = MagicMock()
    member.roles = list(member_roles)
    member.add_roles = AsyncMock()
    member.remove_roles = AsyncMock()
    member.display_name = "u"
    msg = MagicMock()
    msg.author = member
    msg.guild = MagicMock(id=1)
    return msg, member


@pytest.mark.asyncio
async def test_exempt_xp_member_gets_no_level_roles():
    admin = _role(99, "Admin")
    msg, member = _message([admin])
    with (
        patch(
            "services.role_exemption_service.get_exempt_role_ids",
            new=AsyncMock(
                return_value=ExemptRoleIds(xp=frozenset({99}), time=frozenset()),
            ),
        ),
        patch(
            "services.role_exemption_service.xp_roles_stack",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "cogs.xp.listener.get_xp_threshold_roles",
            new=AsyncMock(return_value=_XP_ROWS),
        ),
        patch("services.xp_role_sync.resources") as res_mock,
        patch(
            "services.role_automation.apply",
            new=AsyncMock(return_value=_apply_result()),
        ) as apply_mock,
    ):
        res_mock.resolve_role.return_value = _role(5, "Lvl5")
        await listener._apply_xp_threshold_roles(msg, 10)

    # Exempt member: nothing applied — not even through the audited seam.
    apply_mock.assert_not_awaited()
    member.add_roles.assert_not_awaited()
    member.remove_roles.assert_not_awaited()


@pytest.mark.asyncio
async def test_xp_roles_stack_adds_all_qualifying():
    lvl5, lvl10 = _role(5, "Lvl5"), _role(10, "Lvl10")
    roles_by_name = {"Lvl5": lvl5, "Lvl10": lvl10}
    msg, member = _message([])  # holds nothing
    with (
        patch(
            "services.role_exemption_service.get_exempt_role_ids",
            new=AsyncMock(return_value=ExemptRoleIds(frozenset(), frozenset())),
        ),
        patch(
            "services.role_exemption_service.xp_roles_stack",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "cogs.xp.listener.get_xp_threshold_roles",
            new=AsyncMock(return_value=_XP_ROWS),
        ),
        patch("services.xp_role_sync.resources") as res_mock,
        patch(
            "services.role_automation.apply",
            new=AsyncMock(return_value=_apply_result(succeeded=2)),
        ) as apply_mock,
    ):
        res_mock.resolve_role.side_effect = (
            lambda guild, *, role_id=None, name=None: roles_by_name.get(name)
        )
        await listener._apply_xp_threshold_roles(msg, 10)

    # Routed through the audited seam, not a direct member.add_roles.
    member.add_roles.assert_not_awaited()
    apply_mock.assert_awaited_once()
    assignments = apply_mock.await_args.args[1]
    # Stacking mode: one promote assignment per newly-earned role, no removals.
    assert {a.add_role_id for a in assignments} == {5, 10}
    assert all(a.remove_role_ids == () for a in assignments)
    assert apply_mock.await_args.kwargs["actor_type"] == "system"


@pytest.mark.asyncio
async def test_xp_roles_single_mode_keeps_highest_removes_lower():
    lvl5, lvl10 = _role(5, "Lvl5"), _role(10, "Lvl10")
    roles_by_name = {"Lvl5": lvl5, "Lvl10": lvl10}
    msg, member = _message([lvl5])  # already holds the lower role
    with (
        patch(
            "services.role_exemption_service.get_exempt_role_ids",
            new=AsyncMock(return_value=ExemptRoleIds(frozenset(), frozenset())),
        ),
        patch(
            "services.role_exemption_service.xp_roles_stack",
            new=AsyncMock(return_value=False),
        ),
        patch(
            "cogs.xp.listener.get_xp_threshold_roles",
            new=AsyncMock(return_value=_XP_ROWS),
        ),
        patch("services.xp_role_sync.resources") as res_mock,
        patch(
            "services.role_automation.apply",
            new=AsyncMock(return_value=_apply_result()),
        ) as apply_mock,
    ):
        res_mock.resolve_role.side_effect = (
            lambda guild, *, role_id=None, name=None: roles_by_name.get(name)
        )
        await listener._apply_xp_threshold_roles(msg, 10)

    # Single-role mode: one audited assignment promotes the highest earned role
    # and demotes the lower one — no direct member.add_roles/remove_roles.
    member.add_roles.assert_not_awaited()
    member.remove_roles.assert_not_awaited()
    apply_mock.assert_awaited_once()
    assignments = apply_mock.await_args.args[1]
    assert len(assignments) == 1
    assert assignments[0].add_role_id == 10
    assert assignments[0].remove_role_ids == (5,)
    assert apply_mock.await_args.kwargs["actor_type"] == "system"
