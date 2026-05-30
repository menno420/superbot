"""PR-G — ``role_cog`` threshold paths must route through ``role_automation``.

Verifies that the cog no longer calls ``member.add_roles`` /
``member.remove_roles`` directly inside the threshold flow. The cog
delegates the decision to ``role_automation.compute_assignments`` /
``explain_assignment_for`` and the mutation to ``role_automation.apply``,
which is what emits ``audit.action_recorded``.

The reaction-role and create/delete-role paths are intentionally NOT
routed through this service (different domain) and are exempt from
the routing check below.
"""

from __future__ import annotations

import re
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cogs.role_cog import RoleCog
from services import role_automation

_REPO_ROOT = Path(__file__).resolve().parents[3]
_ROLE_COG = _REPO_ROOT / "disbot" / "cogs" / "role_cog.py"


@pytest.fixture(autouse=True)
def _stub_role_exemptions():
    """Stub the role-exemption reads (DB-backed) so the routing tests stay
    pure. ``_assign_roles`` / ``on_member_join`` now consult
    ``role_exemption_service`` for the time-exempt set + stacking toggle.
    """
    from services import role_exemption_service as res

    with (
        patch.object(
            res,
            "get_exempt_role_ids",
            new=AsyncMock(return_value=res.ExemptRoleIds(frozenset(), frozenset())),
        ),
        patch.object(res, "time_roles_stack", new=AsyncMock(return_value=False)),
    ):
        yield


@pytest.mark.asyncio
async def test_assign_roles_delegates_to_role_automation():
    """_assign_roles must call compute_assignments + apply, not Discord directly."""
    bot = MagicMock()
    cog = RoleCog(bot)

    guild = MagicMock()
    guild.id = 1
    guild.members = []

    fake_apply_result = role_automation.ApplyResult(
        attempted=2,
        succeeded=2,
        failed=0,
    )

    with (
        patch(
            "cogs.role_cog._ensure_defaults",
            new_callable=AsyncMock,
        ),
        patch(
            "cogs.role_cog.db.get_role_thresholds",
            new_callable=AsyncMock,
            return_value=[
                {"role_name": "Newbie", "days_required": 0},
                {"role_name": "Veteran", "days_required": 30},
            ],
        ),
        patch(
            "cogs.role_cog.db.get_setting",
            new_callable=AsyncMock,
            return_value="Admin",
        ),
        patch(
            "cogs.role_cog.role_automation.compute_assignments",
            return_value=(),
        ) as compute_mock,
        patch(
            "cogs.role_cog.role_automation.apply",
            new_callable=AsyncMock,
            return_value=fake_apply_result,
        ) as apply_mock,
    ):
        count = await cog._assign_roles(guild)

    compute_mock.assert_called_once()
    apply_mock.assert_awaited_once()
    assert count == 2
    # The cog must pass a tuple of RoleThreshold objects, not raw rows.
    threshold_arg = compute_mock.call_args.args[1]
    assert all(isinstance(t, role_automation.RoleThreshold) for t in threshold_arg)


@pytest.mark.asyncio
async def test_assign_roles_excludes_xp_auto_assign_roles():
    """XP reward roles must NOT be reconciled by the time-based loop.

    Regression: ``role_thresholds`` holds both time-based and XP roles. The
    time-based ``role_check`` runs on boot; if an ``xp_auto_assign`` role is
    fed into it, members who hold the level-earned role but don't meet a
    ``days_required`` threshold get it stripped (the "lost testrole on
    restart" bug). The XP role must be filtered out before compute_assignments.
    """
    bot = MagicMock()
    cog = RoleCog(bot)
    guild = MagicMock(id=1)
    guild.members = []

    with (
        patch("cogs.role_cog._ensure_defaults", new_callable=AsyncMock),
        patch(
            "cogs.role_cog.db.get_role_thresholds",
            new_callable=AsyncMock,
            return_value=[
                {
                    "role_name": "Veteran",
                    "days_required": 30,
                    "level_required": None,
                    "xp_auto_assign": False,
                },
                {
                    "role_name": "testrole",
                    "days_required": 0,
                    "level_required": 6,
                    "xp_auto_assign": True,
                },
            ],
        ),
        patch(
            "cogs.role_cog.db.get_setting",
            new_callable=AsyncMock,
            return_value="Admin",
        ),
        patch(
            "cogs.role_cog.role_automation.compute_assignments",
            return_value=(),
        ) as compute_mock,
        patch(
            "cogs.role_cog.role_automation.apply",
            new_callable=AsyncMock,
            return_value=role_automation.ApplyResult(
                attempted=0, succeeded=0, failed=0
            ),
        ),
    ):
        await cog._assign_roles(guild)

    names = {t.role_name for t in compute_mock.call_args.args[1]}
    assert "Veteran" in names  # time-based role still reconciled
    assert "testrole" not in names  # XP reward role excluded from time-based loop


@pytest.mark.asyncio
async def test_assign_roles_returns_zero_when_no_thresholds():
    """Empty threshold list short-circuits without calling the service."""
    bot = MagicMock()
    cog = RoleCog(bot)
    guild = MagicMock(id=1)

    with (
        patch(
            "cogs.role_cog._ensure_defaults",
            new_callable=AsyncMock,
        ),
        patch(
            "cogs.role_cog.db.get_role_thresholds",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "cogs.role_cog.role_automation.compute_assignments",
        ) as compute_mock,
        patch(
            "cogs.role_cog.role_automation.apply",
            new_callable=AsyncMock,
        ) as apply_mock,
    ):
        count = await cog._assign_roles(guild)

    assert count == 0
    compute_mock.assert_not_called()
    apply_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_on_member_join_delegates_to_role_automation():
    """on_member_join must route through explain_assignment_for + apply."""
    bot = MagicMock()
    cog = RoleCog(bot)

    member = MagicMock()
    member.bot = False
    member.guild = MagicMock(id=1)

    fake_plan = role_automation.Assignment(
        member_id=42,
        member_display="bob",
        add_role_id=7,
        add_role_name="Newbie",
        remove_role_ids=(),
        remove_role_names=(),
        reason="…",
        days_in_guild=0,
    )

    with (
        patch(
            "cogs.role_cog._ensure_defaults",
            new_callable=AsyncMock,
        ),
        patch(
            "cogs.role_cog.db.get_role_thresholds",
            new_callable=AsyncMock,
            return_value=[
                {"role_name": "Newbie", "days_required": 0},
            ],
        ),
        patch(
            "cogs.role_cog.role_automation.explain_assignment_for",
            return_value=fake_plan,
        ) as explain_mock,
        patch(
            "cogs.role_cog.role_automation.apply",
            new_callable=AsyncMock,
            return_value=role_automation.ApplyResult(),
        ) as apply_mock,
    ):
        await cog.on_member_join(member)

    explain_mock.assert_called_once()
    apply_mock.assert_awaited_once()
    # apply is called with a one-tuple containing the planned assignment.
    plan_arg = apply_mock.await_args.args[1]
    assert plan_arg == (fake_plan,)


@pytest.mark.asyncio
async def test_on_member_join_skips_when_no_plan():
    """If explain_assignment_for returns None, apply is not invoked."""
    bot = MagicMock()
    cog = RoleCog(bot)
    member = MagicMock()
    member.bot = False
    member.guild = MagicMock(id=1)

    with (
        patch(
            "cogs.role_cog._ensure_defaults",
            new_callable=AsyncMock,
        ),
        patch(
            "cogs.role_cog.db.get_role_thresholds",
            new_callable=AsyncMock,
            return_value=[{"role_name": "Newbie", "days_required": 0}],
        ),
        patch(
            "cogs.role_cog.role_automation.explain_assignment_for",
            return_value=None,
        ),
        patch(
            "cogs.role_cog.role_automation.apply",
            new_callable=AsyncMock,
        ) as apply_mock,
    ):
        await cog.on_member_join(member)

    apply_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_on_member_join_excludes_xp_auto_assign_roles():
    """The join path must also keep XP reward roles out of the time-based
    reconciliation. The "lost testrole on restart" regression lived in BOTH
    role_check/_assign_roles AND on_member_join; this is the join-path mirror
    of test_assign_roles_excludes_xp_auto_assign_roles so neither half can
    silently re-regress.
    """
    bot = MagicMock()
    cog = RoleCog(bot)
    member = MagicMock()
    member.bot = False
    member.guild = MagicMock(id=1)

    with (
        patch("cogs.role_cog._ensure_defaults", new_callable=AsyncMock),
        patch(
            "cogs.role_cog.db.get_role_thresholds",
            new_callable=AsyncMock,
            return_value=[
                {
                    "role_name": "Veteran",
                    "days_required": 30,
                    "level_required": None,
                    "xp_auto_assign": False,
                },
                {
                    "role_name": "testrole",
                    "days_required": 0,
                    "level_required": 6,
                    "xp_auto_assign": True,
                },
            ],
        ),
        patch(
            "cogs.role_cog.role_automation.explain_assignment_for",
            return_value=None,
        ) as explain_mock,
    ):
        await cog.on_member_join(member)

    # explain_assignment_for(guild, member, threshold_objs) — args[2] is the
    # filtered threshold tuple fed into the time-based reconciliation.
    names = {t.role_name for t in explain_mock.call_args.args[2]}
    assert "Veteran" in names  # time-based role still reconciled on join
    assert "testrole" not in names  # XP reward role excluded from join path


def test_role_cog_threshold_paths_do_not_call_member_role_apis_directly():
    """Static check: the threshold path must not call Discord member.add_roles
    / member.remove_roles directly. Reaction-role and admin role create/delete
    paths intentionally still call Discord directly (out of role_automation
    scope) and are exempt.
    """
    src = _ROLE_COG.read_text()

    # The two threshold methods are ``_assign_roles`` and ``on_member_join``.
    # Both must be free of direct member.add_roles / member.remove_roles.
    threshold_methods = [
        _extract_method(src, "_assign_roles"),
        _extract_method(src, "on_member_join"),
    ]
    for body in threshold_methods:
        assert body is not None, "Expected to find the threshold method in role_cog.py"
        assert "member.add_roles" not in body, (
            "Threshold path must not call member.add_roles directly — "
            "route through services.role_automation.apply (PR-G)."
        )
        assert "member.remove_roles" not in body, (
            "Threshold path must not call member.remove_roles directly — "
            "route through services.role_automation.apply (PR-G)."
        )


def _extract_method(src: str, name: str) -> str | None:
    """Return the source of method ``name`` (until the next method/class)."""
    pattern = re.compile(
        r"^[ \t]*(async\s+)?def\s+" + re.escape(name) + r"\s*\(",
        re.MULTILINE,
    )
    match = pattern.search(src)
    if not match:
        return None
    start = match.start()
    # Find the start of the next method/class at same or shallower indent.
    next_def = re.compile(
        r"^[ \t]*(async\s+)?def\s+\w+\s*\(|^class\s+\w+",
        re.MULTILINE,
    )
    next_match = next_def.search(src, pos=match.end())
    end = next_match.start() if next_match else len(src)
    return src[start:end]
