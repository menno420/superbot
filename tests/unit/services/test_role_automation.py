"""Phase 9h / Track 7 PR 20 — role_automation service tests.

Pins:

* ``compute_assignments`` produces no mutations (pure read).
* The decision logic respects the documented invariants:
  - Skip bots / skip members in skip-role list / skip joined_at=None.
  - Never demote: a member at a higher tier stays put.
  - Promote when days_in_guild crosses the next threshold.
* ``explain_assignment_for`` returns deterministic per-member
  reasoning.
* ``check_preflight`` flags missing manage_roles, missing roles,
  and hierarchy blockers (roles >= bot's top role position).
* ``apply`` calls ``member.add_roles`` / ``member.remove_roles``
  per assignment when not dry-run; emits one
  ``audit.action_recorded`` event per change.
* ``apply(dry_run=True)`` performs no Discord side effects and no
  audit emit.
* A raising ``add_roles`` is isolated — the rest of the batch
  continues, failure counter increments.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import discord
import pytest

from services.role_automation import (
    FORBIDDEN,
    UNKNOWN,
    ApplyError,
    ApplyResult,
    Assignment,
    PreflightResult,
    RoleThreshold,
    _classify_exception,
    apply,
    check_preflight,
    compute_assignments,
    explain_assignment_for,
    summarize_failures,
)
from utils.role_feasibility import ABOVE_BOT, BOT_MISSING_MANAGE_ROLES


def _role(rid: int, name: str, position: int = 1):
    return SimpleNamespace(id=rid, name=name, position=position)


def _member(
    *,
    mid: int,
    display: str,
    roles=(),
    joined_days_ago: int | None = None,
    is_bot: bool = False,
):
    joined_at = (
        datetime.now(tz=timezone.utc) - timedelta(days=joined_days_ago)
        if joined_days_ago is not None
        else None
    )
    return SimpleNamespace(
        id=mid,
        display_name=display,
        roles=list(roles),
        joined_at=joined_at,
        bot=is_bot,
        add_roles=AsyncMock(),
        remove_roles=AsyncMock(),
    )


def _guild(
    *,
    roles=(),
    members=(),
    me=None,
    guild_id: int = 1,
):
    return SimpleNamespace(
        id=guild_id,
        roles=list(roles),
        members=list(members),
        me=me,
    )


def _me_member(*, manage_roles: bool = True, top_position: int = 10):
    return SimpleNamespace(
        guild_permissions=SimpleNamespace(manage_roles=manage_roles),
        top_role=SimpleNamespace(position=top_position),
    )


# ---------------------------------------------------------------------------
# compute_assignments
# ---------------------------------------------------------------------------


def test_compute_assignments_empty_thresholds_returns_empty():
    g = _guild(members=[_member(mid=1, display="a", joined_days_ago=100)])
    assert compute_assignments(g, []) == ()


def test_compute_assignments_skips_bots_and_missing_joined_at():
    threshold_role = _role(100, "Veteran")
    g = _guild(
        roles=[threshold_role],
        members=[
            _member(mid=1, display="bot", joined_days_ago=100, is_bot=True),
            _member(mid=2, display="ghost"),  # no joined_at
        ],
    )
    plans = compute_assignments(
        g,
        [RoleThreshold("Veteran", 30)],
    )
    assert plans == ()


def test_compute_assignments_skips_members_with_time_exempt_role():
    admin = _role(99, "Admin")
    threshold_role = _role(100, "Veteran")
    member = _member(
        mid=1,
        display="adminuser",
        roles=[admin],
        joined_days_ago=100,
    )
    g = _guild(roles=[admin, threshold_role], members=[member])
    plans = compute_assignments(
        g,
        [RoleThreshold("Veteran", 30)],
        exempt_role_ids=frozenset({99}),  # Admin role id is time-exempt
    )
    assert plans == ()


def test_compute_assignments_keeps_previous_tier_when_stacking():
    """With keep_previous_tier=True (time_roles_stack ON), promotion adds the
    new tier but does NOT remove the previous one.
    """
    veteran = _role(100, "Veteran", position=2)
    legendary = _role(101, "Legendary", position=3)
    member = _member(
        mid=1,
        display="u1",
        roles=[veteran],
        joined_days_ago=120,
    )
    g = _guild(roles=[veteran, legendary], members=[member])
    plans = compute_assignments(
        g,
        [
            RoleThreshold("Veteran", 30),
            RoleThreshold("Legendary", 90),
        ],
        keep_previous_tier=True,
    )
    assert len(plans) == 1
    assert plans[0].add_role_name == "Legendary"
    assert plans[0].remove_role_names == ()  # Veteran kept (stacking on)


def test_compute_assignments_promotes_member_who_crosses_threshold():
    veteran = _role(100, "Veteran")
    g = _guild(
        roles=[veteran],
        members=[_member(mid=1, display="u1", joined_days_ago=45)],
    )
    plans = compute_assignments(
        g,
        [RoleThreshold("Veteran", 30)],
    )
    assert len(plans) == 1
    assert plans[0].add_role_id == 100
    assert plans[0].add_role_name == "Veteran"
    assert plans[0].remove_role_ids == ()


def test_compute_assignments_never_demotes():
    veteran = _role(100, "Veteran", position=2)
    legendary = _role(101, "Legendary", position=3)
    member = _member(
        mid=1,
        display="u1",
        roles=[legendary],
        joined_days_ago=45,
    )
    g = _guild(roles=[veteran, legendary], members=[member])
    plans = compute_assignments(
        g,
        [
            RoleThreshold("Veteran", 30),
            RoleThreshold("Legendary", 90),
        ],
    )
    # 45 days isn't enough for Legendary, but member already has it
    # — never demote.
    assert plans == ()


def test_compute_assignments_emits_remove_when_promoting():
    veteran = _role(100, "Veteran", position=2)
    legendary = _role(101, "Legendary", position=3)
    member = _member(
        mid=1,
        display="u1",
        roles=[veteran],
        joined_days_ago=120,
    )
    g = _guild(roles=[veteran, legendary], members=[member])
    plans = compute_assignments(
        g,
        [
            RoleThreshold("Veteran", 30),
            RoleThreshold("Legendary", 90),
        ],
    )
    assert len(plans) == 1
    assert plans[0].add_role_name == "Legendary"
    assert plans[0].remove_role_names == ("Veteran",)


def test_compute_assignments_resolves_tier_by_role_id_after_rename():
    """PR6 id-first: a threshold keyed by role_id survives a role rename.

    The row still stores the old name, but the role (id 100) was renamed to
    "NewName"; resolution is id-first, so the tier resolves to the renamed role
    and assigns it under its current name.
    """
    renamed = _role(100, "NewName")
    member = _member(mid=1, display="u1", joined_days_ago=45)
    g = _guild(roles=[renamed], members=[member])
    plans = compute_assignments(g, [RoleThreshold("OldName", 30, role_id=100)])
    assert len(plans) == 1
    assert plans[0].add_role_id == 100
    assert plans[0].add_role_name == "NewName"


def test_compute_assignments_drops_tier_whose_role_is_gone():
    """A threshold whose role resolves by neither id nor name is dropped."""
    member = _member(mid=1, display="u1", joined_days_ago=45)
    g = _guild(roles=[], members=[member])
    plans = compute_assignments(g, [RoleThreshold("Ghost", 30, role_id=999)])
    assert plans == ()


def test_explain_assignment_for_returns_per_member_plan():
    veteran = _role(100, "Veteran")
    target = _member(mid=42, display="u42", joined_days_ago=60)
    g = _guild(
        roles=[veteran],
        members=[
            _member(mid=1, display="x", joined_days_ago=10),
            target,
        ],
    )
    plan = explain_assignment_for(g, target, [RoleThreshold("Veteran", 30)])
    assert plan is not None
    assert plan.member_id == 42
    assert "Veteran" in plan.reason


def test_explain_assignment_for_returns_none_when_no_change_needed():
    veteran = _role(100, "Veteran")
    target = _member(
        mid=42,
        display="u42",
        roles=[veteran],
        joined_days_ago=60,
    )
    g = _guild(roles=[veteran], members=[target])
    plan = explain_assignment_for(g, target, [RoleThreshold("Veteran", 30)])
    assert plan is None


# ---------------------------------------------------------------------------
# check_preflight
# ---------------------------------------------------------------------------


def test_preflight_flags_missing_manage_roles():
    veteran = _role(100, "Veteran", position=5)
    g = _guild(
        roles=[veteran],
        me=_me_member(manage_roles=False, top_position=10),
    )
    result = check_preflight(g, [RoleThreshold("Veteran", 30)])
    assert result.bot_has_manage_roles is False
    assert result.ok is False


def test_preflight_flags_missing_role():
    g = _guild(
        roles=[],  # progression role absent
        me=_me_member(),
    )
    result = check_preflight(g, [RoleThreshold("Veteran", 30)])
    assert "Veteran" in result.missing_roles
    assert result.ok is False


def test_preflight_flags_hierarchy_blocker():
    above_bot = _role(100, "Veteran", position=20)  # above bot's 10
    g = _guild(roles=[above_bot], me=_me_member(top_position=10))
    result = check_preflight(g, [RoleThreshold("Veteran", 30)])
    assert "Veteran" in result.hierarchy_blockers
    assert result.ok is False


def test_preflight_ok_when_all_clear():
    veteran = _role(100, "Veteran", position=5)
    g = _guild(roles=[veteran], me=_me_member(top_position=10))
    result = check_preflight(g, [RoleThreshold("Veteran", 30)])
    assert result.ok is True


# ---------------------------------------------------------------------------
# apply
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_dry_run_does_not_touch_members():
    veteran = _role(100, "Veteran")
    member = _member(mid=1, display="u1", joined_days_ago=60)
    g = _guild(roles=[veteran], members=[member])
    plans = compute_assignments(g, [RoleThreshold("Veteran", 30)])
    result = await apply(g, plans, dry_run=True)
    assert isinstance(result, ApplyResult)
    assert result.skipped == len(plans)
    member.add_roles.assert_not_awaited()
    member.remove_roles.assert_not_awaited()


@pytest.mark.asyncio
async def test_apply_calls_add_roles_for_promotions():
    veteran = _role(100, "Veteran")
    member = _member(mid=1, display="u1", joined_days_ago=60)
    g = _guild(roles=[veteran], members=[member])
    plans = compute_assignments(g, [RoleThreshold("Veteran", 30)])
    with patch(
        "services.role_automation.emit_audit_action",
        new_callable=AsyncMock,
    ) as emit_mock:
        result = await apply(g, plans)
    member.add_roles.assert_awaited_once()
    assert result.succeeded == 1
    emit_mock.assert_awaited()


@pytest.mark.asyncio
async def test_apply_isolates_per_member_failures():
    veteran = _role(100, "Veteran")
    ok = _member(mid=1, display="ok", joined_days_ago=60)
    bad = _member(mid=2, display="bad", joined_days_ago=60)
    bad.add_roles = AsyncMock(side_effect=RuntimeError("hierarchy"))
    g = _guild(roles=[veteran], members=[ok, bad])
    plans = compute_assignments(g, [RoleThreshold("Veteran", 30)])
    with patch(
        "services.role_automation.emit_audit_action",
        new_callable=AsyncMock,
    ):
        result = await apply(g, plans)
    ok.add_roles.assert_awaited_once()
    assert result.succeeded == 1
    assert result.failed == 1
    assert any("hierarchy" in e for e in result.errors)


@pytest.mark.asyncio
async def test_apply_emits_one_audit_event_per_change():
    veteran = _role(100, "Veteran", position=2)
    legendary = _role(101, "Legendary", position=3)
    member = _member(
        mid=1,
        display="u1",
        roles=[veteran],
        joined_days_ago=120,
    )
    g = _guild(roles=[veteran, legendary], members=[member])
    plans = compute_assignments(
        g,
        [
            RoleThreshold("Veteran", 30),
            RoleThreshold("Legendary", 90),
        ],
    )
    assert len(plans) == 1
    with patch(
        "services.role_automation.emit_audit_action",
        new_callable=AsyncMock,
    ) as emit_mock:
        await apply(g, plans)
    # Promote = 1 remove + 1 add = 2 audit events
    assert emit_mock.await_count == 2


# ---------------------------------------------------------------------------
# check_preflight — id-first parity (must match compute_assignments / apply)
# ---------------------------------------------------------------------------


def test_preflight_resolves_role_by_id_after_rename():
    """A threshold carrying a persisted role_id must NOT report 'missing' when
    the role was renamed — preflight has to resolve id-first like the assignment
    path, or it diverges from what apply() can actually do.
    """
    renamed = _role(100, "NewName", position=5)
    g = _guild(roles=[renamed], me=_me_member(top_position=10))
    result = check_preflight(g, [RoleThreshold("OldName", 30, role_id=100)])
    assert result.missing_roles == ()  # resolved by id, not flagged missing
    assert result.ok is True


# ---------------------------------------------------------------------------
# apply — preflight guard + failure classification (the 26-errors fix)
# ---------------------------------------------------------------------------


def _forbidden() -> discord.Forbidden:
    resp = SimpleNamespace(status=403, reason="Forbidden")
    return discord.Forbidden(resp, "Missing Permissions")


@pytest.mark.asyncio
async def test_apply_blocks_entire_batch_when_bot_lacks_manage_roles():
    """No Manage Roles ⇒ every member would 403. apply() must detect it ONCE,
    skip the batch, and classify each failure — never call Discord, never emit
    one ERROR traceback per member (the health-flooding shape).
    """
    veteran = _role(100, "Veteran", position=5)
    members = [
        _member(mid=i, display=f"u{i}", joined_days_ago=60) for i in (1, 2, 3)
    ]
    g = _guild(
        roles=[veteran],
        members=members,
        me=_me_member(manage_roles=False, top_position=10),
    )
    plans = compute_assignments(g, [RoleThreshold("Veteran", 30)])
    assert len(plans) == 3
    with patch(
        "services.role_automation.emit_audit_action",
        new_callable=AsyncMock,
    ):
        result = await apply(g, plans)
    assert result.succeeded == 0
    assert result.failed == 3
    assert result.failure_counts() == {BOT_MISSING_MANAGE_ROLES: 3}
    for m in members:
        m.add_roles.assert_not_awaited()
        m.remove_roles.assert_not_awaited()


@pytest.mark.asyncio
async def test_apply_skips_role_above_bot_without_calling_discord():
    """A progression role at/above the bot's top role is pre-empted per-member
    with an ABOVE_BOT failure instead of a raised 403.
    """
    above = _role(100, "Veteran", position=20)  # above the bot's top (10)
    member = _member(mid=1, display="u1", joined_days_ago=60)
    g = _guild(roles=[above], members=[member], me=_me_member(top_position=10))
    plans = compute_assignments(g, [RoleThreshold("Veteran", 30)])
    assert len(plans) == 1
    with patch(
        "services.role_automation.emit_audit_action",
        new_callable=AsyncMock,
    ):
        result = await apply(g, plans)
    assert result.succeeded == 0
    assert result.failed == 1
    assert result.failures[0].code == ABOVE_BOT
    assert result.failures[0].phase == "preflight"
    member.add_roles.assert_not_awaited()


@pytest.mark.asyncio
async def test_apply_classifies_forbidden_raised_during_mutation():
    """A Forbidden that slips past the precheck (e.g. integration-managed
    target) is classified FORBIDDEN, not the catch-all UNKNOWN.
    """
    veteran = _role(100, "Veteran", position=5)
    member = _member(mid=1, display="u1", joined_days_ago=60)
    member.add_roles = AsyncMock(side_effect=_forbidden())
    g = _guild(roles=[veteran], members=[member], me=_me_member(top_position=10))
    plans = compute_assignments(g, [RoleThreshold("Veteran", 30)])
    with patch(
        "services.role_automation.emit_audit_action",
        new_callable=AsyncMock,
    ):
        result = await apply(g, plans)
    assert result.failed == 1
    assert result.failures[0].code == FORBIDDEN
    assert result.failures[0].phase == "mutate"


def test_classify_exception_maps_discord_errors():
    """Predictable Discord errors are 'expected' (warn, stay out of ERROR
    health); anything else is unexpected (ERROR + traceback).
    """
    assert _classify_exception(_forbidden()) == (FORBIDDEN, False)
    assert _classify_exception(RuntimeError("boom")) == (UNKNOWN, True)


def test_apply_result_errors_property_and_failure_counts():
    """The structured ``failures`` drives both the back-compat ``errors`` strings
    and the grouped ``failure_counts`` / ``summarize_failures`` operator surface.
    """
    failures = (
        ApplyError(1, "preflight", BOT_MISSING_MANAGE_ROLES, "no perms"),
        ApplyError(2, "preflight", BOT_MISSING_MANAGE_ROLES, "no perms"),
        ApplyError(3, "mutate", UNKNOWN, "boom"),
    )
    r = ApplyResult(attempted=3, failed=3, failures=failures)
    assert r.failure_counts() == {BOT_MISSING_MANAGE_ROLES: 2, UNKNOWN: 1}
    assert "member 3: boom" in r.errors
    # Busiest cause first, human-labelled.
    assert summarize_failures(r) == "missing Manage Roles: 2, unexpected error: 1"
    assert summarize_failures(ApplyResult()) == ""
