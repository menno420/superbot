"""Tests for the ``create_managed_role`` setup operation (server-management PR13).

Pins:

* dispatch routes through ``RoleLifecycleService`` (the audited manual-role
  owner) — *not* the provisioning pipeline — and never calls ``guild.create_*``
  directly (that AST pin lives in ``test_setup_operations_invariants``);
* an optional time/XP tier is threaded into ``role_automation`` as a
  best-effort companion using the freshly-created role id;
* a failed tier never flips the op to ``failed`` (the role was created);
* a non-success lifecycle outcome surfaces as ``failed``;
* the read-only preflight renders ABSENT → a descriptive proposed value with a
  Manage-Roles note;
* the kind is known + validates.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from services import setup_operations as so
from services.lifecycle import contracts as lc
from services.setup_change_plan import ABSENT


def _guild(gid: int = 1, *, manage_roles: bool = True):
    me = SimpleNamespace(
        guild_permissions=SimpleNamespace(manage_roles=manage_roles),
    )
    return SimpleNamespace(id=gid, me=me, roles=[])


def _success(role_id: int = 123, name: str = "Owner", mid: str = "m1"):
    return lc.LifecycleResult(
        mutation_id=mid,
        guild_id=1,
        domain="role",
        operation="create",
        outcome=lc.SUCCESS,
        reversibility=lc.COMPENSATABLE,
        steps=(lc.StepResult(role_id, name, True),),
        committed_at=lc.now_utc(),
    )


def _op(name="Owner", **role_template):
    return so.SetupOperation(
        kind="create_managed_role",
        subsystem="roles",
        resource_name=name,
        resource_mode="create",
        metadata={"role_template": {"template_slug": "t", **role_template}},
    )


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_routes_through_role_lifecycle_service():
    op = _op("Owner", color="#E91E63", hoist=True)
    svc = MagicMock()
    svc.apply = AsyncMock(return_value=_success(role_id=555, name="Owner", mid="mid-1"))
    with patch(
        "services.role_lifecycle_service.RoleLifecycleService", return_value=svc
    ):
        batch = await so.apply_operations(
            [op],
            guild=_guild(),
            actor=SimpleNamespace(id=9),
        )
    assert len(batch.applied) == 1
    result = batch.results[0]
    assert result.status == "applied"
    assert result.mutation_id == "mid-1"
    svc.apply.assert_awaited_once()
    request = svc.apply.await_args.args[1]
    assert request.operation == "create"
    assert request.name == "Owner"
    assert request.hoist is True
    assert isinstance(request.color, discord.Color)


@pytest.mark.asyncio
async def test_time_tier_companion_uses_new_role_id():
    op = _op("Regular", time_days=7)
    svc = MagicMock()
    svc.apply = AsyncMock(return_value=_success(role_id=777, name="Regular"))
    with (
        patch("services.role_lifecycle_service.RoleLifecycleService", return_value=svc),
        patch(
            "services.role_automation.set_time_threshold",
            new_callable=AsyncMock,
        ) as set_time,
    ):
        batch = await so.apply_operations(
            [op],
            guild=_guild(),
            actor=SimpleNamespace(id=9),
        )
    assert batch.results[0].status == "applied"
    set_time.assert_awaited_once()
    assert set_time.await_args.kwargs["role_id"] == 777
    assert set_time.await_args.kwargs["days"] == 7


@pytest.mark.asyncio
async def test_xp_tier_companion_uses_new_role_id():
    op = _op("Level 5", xp_level=5)
    svc = MagicMock()
    svc.apply = AsyncMock(return_value=_success(role_id=888, name="Level 5"))
    with (
        patch("services.role_lifecycle_service.RoleLifecycleService", return_value=svc),
        patch(
            "services.role_automation.set_xp_threshold",
            new_callable=AsyncMock,
        ) as set_xp,
    ):
        batch = await so.apply_operations(
            [op],
            guild=_guild(),
            actor=SimpleNamespace(id=9),
        )
    assert batch.results[0].status == "applied"
    set_xp.assert_awaited_once()
    assert set_xp.await_args.kwargs["role_id"] == 888
    assert set_xp.await_args.kwargs["level"] == 5


@pytest.mark.asyncio
async def test_tier_failure_does_not_fail_the_op():
    op = _op("Regular", time_days=7)
    svc = MagicMock()
    svc.apply = AsyncMock(return_value=_success(role_id=777, name="Regular"))
    with (
        patch("services.role_lifecycle_service.RoleLifecycleService", return_value=svc),
        patch(
            "services.role_automation.set_time_threshold",
            new_callable=AsyncMock,
            side_effect=RuntimeError("db down"),
        ),
    ):
        batch = await so.apply_operations(
            [op],
            guild=_guild(),
            actor=SimpleNamespace(id=9),
        )
    # The role itself was created — a failed tier is a soft, logged companion.
    assert batch.results[0].status == "applied"


@pytest.mark.asyncio
async def test_no_tier_means_no_role_automation_call():
    op = _op("Owner")
    svc = MagicMock()
    svc.apply = AsyncMock(return_value=_success(role_id=1, name="Owner"))
    with (
        patch("services.role_lifecycle_service.RoleLifecycleService", return_value=svc),
        patch(
            "services.role_automation.set_time_threshold",
            new_callable=AsyncMock,
        ) as set_time,
        patch(
            "services.role_automation.set_xp_threshold",
            new_callable=AsyncMock,
        ) as set_xp,
    ):
        await so.apply_operations([op], guild=_guild(), actor=SimpleNamespace(id=9))
    set_time.assert_not_called()
    set_xp.assert_not_called()


# ---------------------------------------------------------------------------
# Failure handling
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_blocked_outcome_surfaces_as_failed():
    op = _op("Owner")
    blocked = lc.LifecycleResult(
        mutation_id="m",
        guild_id=1,
        domain="role",
        operation="create",
        outcome=lc.BLOCKED,
        reversibility=lc.COMPENSATABLE,
        steps=(lc.StepResult(0, "", False, "bot lacks the Manage Roles permission"),),
        committed_at=lc.now_utc(),
    )
    svc = MagicMock()
    svc.apply = AsyncMock(return_value=blocked)
    with patch(
        "services.role_lifecycle_service.RoleLifecycleService", return_value=svc
    ):
        batch = await so.apply_operations(
            [op],
            guild=_guild(),
            actor=SimpleNamespace(id=9),
        )
    result = batch.results[0]
    assert result.status == "failed"
    assert "blocked" in (result.error or "")


@pytest.mark.asyncio
async def test_missing_name_is_failed():
    op = so.SetupOperation(kind="create_managed_role", subsystem="roles")
    batch = await so.apply_operations([op], guild=_guild(), actor=SimpleNamespace(id=9))
    result = batch.results[0]
    assert result.status == "failed"
    assert "resource_name" in (result.error or "")


# ---------------------------------------------------------------------------
# Preflight + label + known-kind
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_preflight_renders_absent_to_descriptive_proposed():
    op = _op("Owner", hoist=True, time_days=7)
    entries = await so.preflight_operations([op], guild=_guild(manage_roles=True))
    entry = entries[0]
    assert entry.current == ABSENT
    proposed = str(entry.proposed.value)
    assert "Owner" in proposed
    assert "7d" in proposed
    assert "Manage Roles" not in proposed  # bot can manage → no warning note


@pytest.mark.asyncio
async def test_preflight_notes_missing_manage_roles():
    op = _op("Owner")
    entries = await so.preflight_operations([op], guild=_guild(manage_roles=False))
    assert "Manage Roles" in str(entries[0].proposed.value)


def test_label_describes_role_and_tier():
    assert so._label(_op("Regular", time_days=7)) == "create role @Regular +7d"
    assert so._label(_op("Level 5", xp_level=5)) == "create role @Level 5 +L5"


def test_create_managed_role_is_known_and_validates():
    assert "create_managed_role" in so._KNOWN_KINDS
    op = so.SetupOperation(kind="create_managed_role", subsystem="roles")
    assert so.validate_operation(op) is None
