"""Tests for services.xp_migration (batch import orchestration)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from services import xp_migration


def _guild(gid: int = 1, members=None):
    return SimpleNamespace(id=gid, members=members or [])


def _import_result(raised: bool):
    return SimpleNamespace(raised=raised)


@pytest.mark.asyncio
async def test_import_levels_tallies_raised_and_unchanged():
    records = [(1, 3), (2, 13), (3, 4)]
    with (
        patch(
            "services.xp_migration.xp_service.import_level",
            new_callable=AsyncMock,
            side_effect=[
                _import_result(True),
                _import_result(False),  # already higher
                _import_result(True),
            ],
        ) as import_level,
        patch(
            "services.xp_migration.emit_audit_action",
            new_callable=AsyncMock,
        ) as audit,
    ):
        summary = await xp_migration.import_levels(
            _guild(),
            records,
            source="import:arcane",
            actor_id=42,
        )

    assert import_level.await_count == 3
    assert summary.total == 3
    assert summary.raised == 2
    assert summary.unchanged == 1
    # Exactly one summary audit action for the whole batch.
    assert audit.await_count == 1
    kwargs = audit.await_args.kwargs
    assert kwargs["subsystem"] == "xp"
    assert kwargs["mutation_type"] == "import_levels"
    assert kwargs["actor_id"] == 42
    assert kwargs["actor_type"] == "admin"


@pytest.mark.asyncio
async def test_import_levels_skips_role_sync_by_default():
    with (
        patch(
            "services.xp_migration.xp_service.import_level",
            new_callable=AsyncMock,
            return_value=_import_result(True),
        ),
        patch(
            "services.xp_migration.emit_audit_action",
            new_callable=AsyncMock,
        ),
        patch(
            "services.xp_migration._sync_level_roles",
            new_callable=AsyncMock,
        ) as sync,
    ):
        summary = await xp_migration.import_levels(
            _guild(),
            [(1, 3)],
            source="import:arcane",
        )
    sync.assert_not_awaited()
    assert summary.roles_succeeded == 0


@pytest.mark.asyncio
async def test_import_levels_runs_role_sync_when_requested():
    with (
        patch(
            "services.xp_migration.xp_service.import_level",
            new_callable=AsyncMock,
            return_value=_import_result(True),
        ),
        patch(
            "services.xp_migration.emit_audit_action",
            new_callable=AsyncMock,
        ),
        patch(
            "services.xp_migration._sync_level_roles",
            new_callable=AsyncMock,
            return_value=(5, 4, 1),
        ) as sync,
    ):
        summary = await xp_migration.import_levels(
            _guild(),
            [(1, 3), (2, 13)],
            source="import:arcane",
            apply_roles=True,
        )
    sync.assert_awaited_once()
    assert (summary.roles_attempted, summary.roles_succeeded, summary.roles_failed) == (
        5,
        4,
        1,
    )


@pytest.mark.asyncio
async def test_import_levels_actor_type_system_without_actor():
    with (
        patch(
            "services.xp_migration.xp_service.import_level",
            new_callable=AsyncMock,
            return_value=_import_result(True),
        ),
        patch(
            "services.xp_migration.emit_audit_action",
            new_callable=AsyncMock,
        ) as audit,
    ):
        await xp_migration.import_levels(_guild(), [(1, 3)], source="import:arcane")
    assert audit.await_args.kwargs["actor_type"] == "system"


# --------------------------------------------------------------------------- #
# _sync_level_roles — reads guild config once, plans present members, one apply
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_sync_level_roles_applies_present_members_only():
    present = SimpleNamespace(id=1, roles=[], display_name="here")
    guild = _guild(members=[present])
    xp_roles = [{"role_id": 10, "role_name": "L5", "level_required": 5}]

    with (
        patch(
            "services.xp_migration.get_xp_threshold_roles",
            new_callable=AsyncMock,
            return_value=xp_roles,
        ),
        patch(
            "services.xp_migration.role_exemption_service.get_exempt_role_ids",
            new_callable=AsyncMock,
            return_value=SimpleNamespace(xp=frozenset(), time=frozenset()),
        ),
        patch(
            "services.xp_migration.role_exemption_service.xp_roles_stack",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "services.xp_migration.xp_role_sync.plan_level_role_assignments",
            side_effect=lambda g, m, lvl, **kw: [f"assign-{m.id}"],
        ) as planner,
        patch(
            "services.xp_migration.role_automation.apply",
            new_callable=AsyncMock,
            return_value=SimpleNamespace(attempted=1, succeeded=1, failed=0),
        ) as apply,
    ):
        # user 1 present, user 99 absent from guild.members
        attempted, succeeded, failed = await xp_migration._sync_level_roles(
            guild,
            [(1, 5), (99, 7)],
            "import:arcane",
        )

    # Only the present member is planned; the absent one is skipped.
    assert planner.call_count == 1
    apply.assert_awaited_once()
    assert (attempted, succeeded, failed) == (1, 1, 0)


@pytest.mark.asyncio
async def test_sync_level_roles_noop_without_configured_roles():
    with patch(
        "services.xp_migration.get_xp_threshold_roles",
        new_callable=AsyncMock,
        return_value=[],
    ):
        assert await xp_migration._sync_level_roles(_guild(), [(1, 5)], "x") == (0, 0, 0)
