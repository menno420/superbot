"""Audited role-menu writes (reaction-roles overhaul PR 2).

PR 1 already covers the emoji-binding seam; these cover the menu CRUD added in
PR 2 — every config write emits ``audit.action_recorded`` and the option set is
reconciled (add/update + prune).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from services import reaction_role_service as rr


@pytest.mark.asyncio
async def test_create_menu_persists_options_and_audits():
    with (
        patch.object(rr.menu_db, "create_menu", new=AsyncMock(return_value=42)),
        patch.object(rr.menu_db, "get_options", new=AsyncMock(return_value=[])),
        patch.object(rr.menu_db, "add_option", new=AsyncMock()) as add_mock,
        patch.object(rr.menu_db, "remove_option", new=AsyncMock()) as rm_mock,
        patch(
            "services.audit_events.emit_audit_action",
            new=AsyncMock(return_value=True),
        ) as audit_mock,
    ):
        menu_id = await rr.create_menu(
            guild_id=1,
            channel_id=2,
            title="Pick",
            description=None,
            style="dropdown",
            mode="normal",
            max_roles=0,
            theme="default",
            role_options=[{"role_id": 10}, {"role_id": 20}],
            actor_id=99,
        )

    assert menu_id == 42
    assert add_mock.await_count == 2
    rm_mock.assert_not_awaited()
    audit_mock.assert_awaited_once()
    kwargs = audit_mock.await_args.kwargs
    assert kwargs["subsystem"] == "role"
    assert kwargs["mutation_type"] == "create_role_menu"
    assert "roles=2" in kwargs["new_value"]


@pytest.mark.asyncio
async def test_update_menu_prunes_removed_options_and_audits():
    # Existing options 10 + 30; new set is 10 + 20 → remove 30, upsert 10 & 20.
    with (
        patch.object(rr.menu_db, "update_menu", new=AsyncMock()),
        patch.object(
            rr.menu_db,
            "get_options",
            new=AsyncMock(return_value=[{"role_id": 10}, {"role_id": 30}]),
        ),
        patch.object(rr.menu_db, "add_option", new=AsyncMock()) as add_mock,
        patch.object(rr.menu_db, "remove_option", new=AsyncMock()) as rm_mock,
        patch(
            "services.audit_events.emit_audit_action",
            new=AsyncMock(return_value=True),
        ) as audit_mock,
    ):
        await rr.update_menu(
            5,
            1,
            title="Pick",
            description="d",
            style="button",
            mode="unique",
            max_roles=1,
            theme="game",
            role_options=[{"role_id": 10}, {"role_id": 20}],
            actor_id=7,
        )

    rm_mock.assert_awaited_once_with(5, 30)
    assert add_mock.await_count == 2
    audit_mock.assert_awaited_once()
    assert audit_mock.await_args.kwargs["mutation_type"] == "update_role_menu"


@pytest.mark.asyncio
async def test_delete_menu_audits():
    with (
        patch.object(rr.menu_db, "delete_menu", new=AsyncMock()) as del_mock,
        patch(
            "services.audit_events.emit_audit_action",
            new=AsyncMock(return_value=True),
        ) as audit_mock,
    ):
        await rr.delete_menu(5, 1, actor_id=7)

    del_mock.assert_awaited_once_with(5)
    audit_mock.assert_awaited_once()
    assert audit_mock.await_args.kwargs["mutation_type"] == "delete_role_menu"
