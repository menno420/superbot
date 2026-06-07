"""Dispatcher tests for the ``set_role_threshold`` op kind (PR11).

Pins the apply path the setup wizard's Roles section uses:

* ``set_role_threshold`` routes through the audited
  :func:`services.role_automation.set_time_threshold` /
  :func:`services.role_automation.set_xp_threshold` seam — a service,
  not a raw DB write (the setup-operations invariant forbids a
  top-level ``utils.db`` import).
* The threshold sub-kind ("time" / "xp") rides ``op.setting_name`` and
  the numeric value rides ``op.value``; ``op.target_id`` is the role id.

Tests stay asyncpg-free by patching the role_automation setters.
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


def _guild(guild_id: int = 1, *, role=None):
    return SimpleNamespace(
        id=guild_id,
        owner_id=99,
        get_role=lambda rid: role,
    )


def _actor(actor_id: int = 99):
    return SimpleNamespace(id=actor_id)


# ---------------------------------------------------------------------------
# Registration / preview state
# ---------------------------------------------------------------------------


def test_set_role_threshold_is_a_known_kind():
    assert "set_role_threshold" in _KNOWN_KINDS


def test_validate_operation_accepts_set_role_threshold():
    op = SetupOperation(
        kind="set_role_threshold",
        subsystem="roles",
        setting_name="time",
        target_id=555,
        target_name="Veteran",
        value=7,
    )
    assert validate_operation(op) is None


def test_preview_reports_applied():
    op = SetupOperation(
        kind="set_role_threshold",
        subsystem="roles",
        setting_name="xp",
        target_id=555,
        value=10,
    )
    assert [r.status for r in preview_operations([op])] == ["applied"]


# ---------------------------------------------------------------------------
# Dispatch — time tier
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_time_threshold_routes_through_service():
    op = SetupOperation(
        kind="set_role_threshold",
        subsystem="roles",
        setting_name="time",
        target_id=555,
        target_name="Veteran",
        value=7,
    )
    with patch(
        "services.role_automation.set_time_threshold",
        new_callable=AsyncMock,
        return_value="mid-time",
    ) as setter:
        batch = await apply_operations([op], guild=_guild(), actor=_actor())

    setter.assert_awaited_once()
    kwargs = setter.await_args.kwargs
    assert kwargs["guild_id"] == 1
    assert kwargs["role_id"] == 555
    assert kwargs["role_name"] == "Veteran"
    assert kwargs["days"] == 7
    assert kwargs["actor_id"] == 99
    assert len(batch.applied) == 1
    assert batch.applied[0].mutation_id == "mid-time"
    assert batch.not_yet_implemented == []


@pytest.mark.asyncio
async def test_time_threshold_resolves_role_name_id_first():
    """When the role still resolves on the guild, its live name wins over
    the (possibly stale) ``target_name`` snapshot.
    """
    live_role = SimpleNamespace(id=555, name="Veteran-renamed")
    op = SetupOperation(
        kind="set_role_threshold",
        subsystem="roles",
        setting_name="time",
        target_id=555,
        target_name="Veteran-old",
        value=30,
    )
    with patch(
        "services.role_automation.set_time_threshold",
        new_callable=AsyncMock,
        return_value="mid",
    ) as setter:
        await apply_operations([op], guild=_guild(role=live_role), actor=_actor())
    assert setter.await_args.kwargs["role_name"] == "Veteran-renamed"


# ---------------------------------------------------------------------------
# Dispatch — XP tier
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_xp_threshold_routes_through_service():
    op = SetupOperation(
        kind="set_role_threshold",
        subsystem="roles",
        setting_name="xp",
        target_id=777,
        target_name="Pro",
        value=25,
    )
    with patch(
        "services.role_automation.set_xp_threshold",
        new_callable=AsyncMock,
        return_value="mid-xp",
    ) as setter:
        batch = await apply_operations([op], guild=_guild(), actor=_actor())

    setter.assert_awaited_once()
    kwargs = setter.await_args.kwargs
    assert kwargs["role_id"] == 777
    assert kwargs["role_name"] == "Pro"
    assert kwargs["level"] == 25
    assert len(batch.applied) == 1
    assert batch.applied[0].mutation_id == "mid-xp"


@pytest.mark.asyncio
async def test_value_coerced_from_draft_string():
    """Drafts round-trip values as strings; the dispatcher coerces back."""
    op = SetupOperation(
        kind="set_role_threshold",
        subsystem="roles",
        setting_name="time",
        target_id=555,
        target_name="Veteran",
        value="14",  # came back from the draft store as a string
    )
    with patch(
        "services.role_automation.set_time_threshold",
        new_callable=AsyncMock,
        return_value="mid",
    ) as setter:
        await apply_operations([op], guild=_guild(), actor=_actor())
    assert setter.await_args.kwargs["days"] == 14


# ---------------------------------------------------------------------------
# Validation failures (per-op, never raise)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rejects_unknown_sub_kind():
    op = SetupOperation(
        kind="set_role_threshold",
        subsystem="roles",
        setting_name="bananas",
        target_id=555,
        value=7,
    )
    with patch(
        "services.role_automation.set_time_threshold",
        new_callable=AsyncMock,
    ) as setter:
        batch = await apply_operations([op], guild=_guild(), actor=_actor())
    setter.assert_not_awaited()
    assert len(batch.failed) == 1
    assert "setting_name" in batch.failed[0].error


@pytest.mark.asyncio
async def test_rejects_missing_target_id():
    op = SetupOperation(
        kind="set_role_threshold",
        subsystem="roles",
        setting_name="time",
        target_id=None,
        value=7,
    )
    batch = await apply_operations([op], guild=_guild(), actor=_actor())
    assert len(batch.failed) == 1
    assert "target_id" in batch.failed[0].error


@pytest.mark.asyncio
async def test_rejects_non_positive_value():
    op = SetupOperation(
        kind="set_role_threshold",
        subsystem="roles",
        setting_name="time",
        target_id=555,
        target_name="Veteran",
        value=0,
    )
    batch = await apply_operations([op], guild=_guild(), actor=_actor())
    assert len(batch.failed) == 1
    assert "positive" in batch.failed[0].error


@pytest.mark.asyncio
async def test_rejects_unresolvable_role_name():
    """No live role and no target_name snapshot → fail (never write a
    nameless row)."""
    op = SetupOperation(
        kind="set_role_threshold",
        subsystem="roles",
        setting_name="time",
        target_id=555,
        target_name=None,
        value=7,
    )
    batch = await apply_operations([op], guild=_guild(role=None), actor=_actor())
    assert len(batch.failed) == 1
    assert "role name" in batch.failed[0].error


@pytest.mark.asyncio
async def test_setter_failure_isolated_per_op():
    failing = SetupOperation(
        kind="set_role_threshold", subsystem="roles",
        setting_name="time", target_id=1, target_name="A", value=7,
    )
    ok = SetupOperation(
        kind="set_role_threshold", subsystem="roles",
        setting_name="xp", target_id=2, target_name="B", value=5,
    )
    with (
        patch(
            "services.role_automation.set_time_threshold",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB down"),
        ),
        patch(
            "services.role_automation.set_xp_threshold",
            new_callable=AsyncMock,
            return_value="mid",
        ),
    ):
        batch = await apply_operations(
            [failing, ok], guild=_guild(), actor=_actor(),
        )
    assert len(batch.failed) == 1
    assert "DB down" in batch.failed[0].error
    assert len(batch.applied) == 1
