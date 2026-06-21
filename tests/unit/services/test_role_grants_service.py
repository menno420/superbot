"""Tests for services.role_grants_service — the temp-role grant + expiry sweep."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from services import role_grants_service as svc


def _forbidden() -> discord.Forbidden:
    resp = MagicMock()
    resp.status = 403
    resp.reason = "Forbidden"
    return discord.Forbidden(resp, "nope")


@pytest.mark.asyncio
async def test_grant_temp_role_adds_persists_and_audits():
    role = SimpleNamespace(id=42, name="VIP")
    member = SimpleNamespace(id=5, roles=[], add_roles=AsyncMock())
    guild = SimpleNamespace(id=1)
    with (
        patch.object(svc.grants_db, "grant", new=AsyncMock()) as grant_mock,
        patch(
            "services.audit_events.emit_audit_action",
            new=AsyncMock(return_value=True),
        ) as audit_mock,
    ):
        expires = await svc.grant_temp_role(
            guild,
            member,
            role,
            seconds=3600,
            actor_id=99,
        )

    member.add_roles.assert_awaited_once()
    args = grant_mock.await_args
    assert args.args[:3] == (1, 5, 42)
    assert args.args[3] == expires
    assert args.kwargs["granted_by"] == 99
    assert audit_mock.await_args.kwargs["mutation_type"] == "grant_temp_role"
    assert audit_mock.await_args.kwargs["actor_type"] == "admin"


@pytest.mark.asyncio
async def test_sweep_removes_expired_role_and_deletes_row():
    role = SimpleNamespace(id=42, name="VIP")
    member = SimpleNamespace(id=5, roles=[role], remove_roles=AsyncMock())
    guild = SimpleNamespace(
        id=1,
        get_member=MagicMock(return_value=member),
        get_role=MagicMock(return_value=role),
    )
    expired = [{"grant_id": 7, "member_id": 5, "role_id": 42}]
    with (
        patch.object(svc.grants_db, "list_expired", new=AsyncMock(return_value=expired)),
        patch.object(svc.grants_db, "delete_grant", new=AsyncMock()) as del_mock,
        patch(
            "services.audit_events.emit_audit_action",
            new=AsyncMock(return_value=True),
        ) as audit_mock,
    ):
        resolved = await svc.sweep_expired(guild)

    assert resolved == 1
    member.remove_roles.assert_awaited_once()
    del_mock.assert_awaited_once_with(7)
    assert audit_mock.await_args.kwargs["mutation_type"] == "expire_temp_role"
    assert audit_mock.await_args.kwargs["actor_type"] == "system"


@pytest.mark.asyncio
async def test_sweep_keeps_row_when_role_unmanageable():
    role = SimpleNamespace(id=42, name="VIP")
    member = SimpleNamespace(
        id=5,
        roles=[role],
        remove_roles=AsyncMock(side_effect=_forbidden()),
    )
    guild = SimpleNamespace(
        id=1,
        get_member=MagicMock(return_value=member),
        get_role=MagicMock(return_value=role),
    )
    expired = [{"grant_id": 7, "member_id": 5, "role_id": 42}]
    with (
        patch.object(svc.grants_db, "list_expired", new=AsyncMock(return_value=expired)),
        patch.object(svc.grants_db, "delete_grant", new=AsyncMock()) as del_mock,
        patch("services.audit_events.emit_audit_action", new=AsyncMock()),
    ):
        resolved = await svc.sweep_expired(guild)

    # The grant is kept (no delete) so a later sweep retries once hierarchy is fixed.
    assert resolved == 0
    del_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_sweep_cleans_up_when_member_gone():
    guild = SimpleNamespace(
        id=1,
        get_member=MagicMock(return_value=None),
        get_role=MagicMock(return_value=SimpleNamespace(id=42)),
    )
    expired = [{"grant_id": 7, "member_id": 5, "role_id": 42}]
    with (
        patch.object(svc.grants_db, "list_expired", new=AsyncMock(return_value=expired)),
        patch.object(svc.grants_db, "delete_grant", new=AsyncMock()) as del_mock,
        patch("services.audit_events.emit_audit_action", new=AsyncMock()) as audit_mock,
    ):
        resolved = await svc.sweep_expired(guild)

    assert resolved == 1
    del_mock.assert_awaited_once_with(7)
    audit_mock.assert_not_awaited()  # no role mutation happened


@pytest.mark.asyncio
async def test_list_active_grants_filters_lapsed_and_vanished_roles():
    from datetime import datetime, timedelta, timezone

    now = datetime(2026, 6, 21, 12, 0, tzinfo=timezone.utc)
    role_live = SimpleNamespace(id=42, name="VIP")
    # role 99 is still active by expiry but has vanished from the guild;
    # role 7 has already lapsed (sweep has not run yet) — both must be dropped.
    rows = [
        {"role_id": 7, "expires_at": now - timedelta(minutes=1)},
        {"role_id": 42, "expires_at": now + timedelta(hours=2)},
        {"role_id": 99, "expires_at": now + timedelta(hours=5)},
    ]

    def _get_role(rid: int):
        return role_live if rid == 42 else None

    guild = SimpleNamespace(id=1, get_role=MagicMock(side_effect=_get_role))
    with (
        patch.object(svc.grants_db, "list_for_member", new=AsyncMock(return_value=rows)),
        patch.object(svc, "_utcnow", return_value=now),
    ):
        active = await svc.list_active_grants(guild, member_id=5)

    assert active == [(role_live, now + timedelta(hours=2))]


@pytest.mark.asyncio
async def test_list_active_grants_empty_when_no_rows():
    guild = SimpleNamespace(id=1, get_role=MagicMock(return_value=None))
    with patch.object(
        svc.grants_db, "list_for_member", new=AsyncMock(return_value=[])
    ):
        active = await svc.list_active_grants(guild, member_id=5)
    assert active == []
