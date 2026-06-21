"""Tests for the ``!temproles`` member-facing listing on ``RoleGrantsCog``.

The command reads through ``role_grants_service.list_active_grants`` (a pure read
seam) and renders the caller's — or, with Manage Roles, another member's — active
temp roles. These tests drive the command callback directly with stubbed ctx.
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from cogs.role_grants_cog import RoleGrantsCog


def _ctx(author, guild):
    return SimpleNamespace(author=author, guild=guild, send=AsyncMock())


def _author(uid: int, *, manage_roles: bool = False, name: str = "Asker"):
    # spec=discord.Member so the cog's ``isinstance(author, discord.Member)``
    # staff check sees a Member (as it would in a guild context).
    author = MagicMock(spec=discord.Member)
    author.id = uid
    author.display_name = name
    author.guild_permissions = SimpleNamespace(manage_roles=manage_roles)
    return author


@pytest.mark.asyncio
async def test_temproles_lists_own_active_grants():
    cog = RoleGrantsCog(MagicMock())
    author = _author(5)
    guild = SimpleNamespace(id=1)
    ctx = _ctx(author, guild)
    expires = datetime(2026, 6, 21, 14, 0, tzinfo=timezone.utc)
    role = SimpleNamespace(id=42, mention="<@&42>")

    with patch(
        "cogs.role_grants_cog.role_grants_service.list_active_grants",
        new=AsyncMock(return_value=[(role, expires)]),
    ) as list_mock:
        await cog.temproles.callback(cog, ctx, None)

    list_mock.assert_awaited_once_with(guild, 5)
    sent = ctx.send.await_args.args[0]
    assert "You have" in sent and "1 active temp role" in sent
    assert "<@&42>" in sent and str(int(expires.timestamp())) in sent


@pytest.mark.asyncio
async def test_temproles_empty_message_when_none():
    cog = RoleGrantsCog(MagicMock())
    ctx = _ctx(_author(5), SimpleNamespace(id=1))
    with patch(
        "cogs.role_grants_cog.role_grants_service.list_active_grants",
        new=AsyncMock(return_value=[]),
    ):
        await cog.temproles.callback(cog, ctx, None)
    assert "no active temp roles" in ctx.send.await_args.args[0]


@pytest.mark.asyncio
async def test_temproles_other_member_denied_without_manage_roles():
    cog = RoleGrantsCog(MagicMock())
    ctx = _ctx(_author(5, manage_roles=False), SimpleNamespace(id=1))
    other = _author(7, name="Other")
    with patch(
        "cogs.role_grants_cog.role_grants_service.list_active_grants",
        new=AsyncMock(),
    ) as list_mock:
        await cog.temproles.callback(cog, ctx, other)

    list_mock.assert_not_awaited()
    assert "Manage Roles" in ctx.send.await_args.args[0]


@pytest.mark.asyncio
async def test_temproles_staff_can_view_other_member():
    cog = RoleGrantsCog(MagicMock())
    ctx = _ctx(_author(5, manage_roles=True), SimpleNamespace(id=1))
    other = _author(7, name="Other")
    expires = datetime(2026, 6, 21, 14, 0, tzinfo=timezone.utc)
    role = SimpleNamespace(id=42, mention="<@&42>")
    with patch(
        "cogs.role_grants_cog.role_grants_service.list_active_grants",
        new=AsyncMock(return_value=[(role, expires)]),
    ) as list_mock:
        await cog.temproles.callback(cog, ctx, other)

    list_mock.assert_awaited_once_with(ctx.guild, 7)
    sent = ctx.send.await_args.args[0]
    assert "**Other** has" in sent and "<@&42>" in sent


@pytest.mark.asyncio
async def test_temproles_staff_viewing_self_uses_you_phrasing():
    cog = RoleGrantsCog(MagicMock())
    author = _author(5, manage_roles=True)
    ctx = _ctx(author, SimpleNamespace(id=1))
    with patch(
        "cogs.role_grants_cog.role_grants_service.list_active_grants",
        new=AsyncMock(return_value=[]),
    ):
        await cog.temproles.callback(cog, ctx, author)
    assert "You have" in ctx.send.await_args.args[0]
