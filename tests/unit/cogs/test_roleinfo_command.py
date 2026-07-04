"""Tests for the read-only ``!roleinfo`` command + its permission summary helper.

Closes the assessment punch-list "utility roleinfo" gap. The command is
member-tier and read-only (no audited seam), so the tests pin the rendered
detail card and the notable-permission summarisation rules.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest
from discord.ext import commands

from cogs.role_cog import RoleCog
from views.roles.role_info import _yes_no, summarize_role_permissions


def _role(
    *,
    name="Veteran",
    rid=555,
    color_value=0x5865F2,
    members=3,
    position=7,
    hoist=True,
    mentionable=False,
    managed=False,
    permissions=None,
):
    role = MagicMock(spec=discord.Role)
    role.name = name
    role.id = rid
    role.color = discord.Color(color_value)
    role.mention = f"<@&{rid}>"
    role.members = [MagicMock() for _ in range(members)]
    role.position = position
    role.hoist = hoist
    role.mentionable = mentionable
    role.managed = managed
    role.created_at = datetime(2024, 1, 2, tzinfo=timezone.utc)
    role.permissions = permissions or discord.Permissions.none()
    return role


def test_yes_no():
    assert _yes_no(True) == "Yes"
    assert _yes_no(False) == "No"


def test_summarize_permissions_administrator_short_circuits():
    perms = discord.Permissions(administrator=True, manage_roles=True)
    assert summarize_role_permissions(perms) == "Administrator (all permissions)"


def test_summarize_permissions_lists_notable_in_order():
    perms = discord.Permissions(
        ban_members=True,
        manage_roles=True,
        kick_members=True,
    )
    # Display order is _NOTABLE_PERMISSIONS order, not the kwarg order.
    assert summarize_role_permissions(perms) == (
        "Manage Roles, Kick Members, Ban Members"
    )


def test_summarize_permissions_none_notable():
    perms = discord.Permissions(send_messages=True, read_messages=True)
    assert summarize_role_permissions(perms) == "No notable permissions"


@pytest.mark.asyncio
async def test_roleinfo_renders_detail_card():
    cog = RoleCog(MagicMock())
    ctx = MagicMock()
    ctx.author = "alice"
    ctx.send = AsyncMock()
    role = _role(permissions=discord.Permissions(manage_messages=True))

    await cog.roleinfo.callback(cog, ctx, role=role)

    ctx.send.assert_awaited_once()
    embed = ctx.send.await_args.kwargs["embed"]
    assert embed.title == "Role Info — Veteran"
    fields = {f.name: f.value for f in embed.fields}
    assert fields["Mention"] == "<@&555>"
    assert fields["ID"] == "555"
    assert fields["Members"] == "3"
    assert fields["Position"] == "7"
    assert fields["Hoisted"] == "Yes"
    assert fields["Mentionable"] == "No"
    assert fields["Key Permissions"] == "Manage Messages"
    assert fields["Created"] == "2024-01-02"


@pytest.mark.asyncio
async def test_roleinfo_default_color_is_labelled():
    cog = RoleCog(MagicMock())
    ctx = MagicMock()
    ctx.author = "alice"
    ctx.send = AsyncMock()
    role = _role(color_value=0)  # discord "default" / no colour

    await cog.roleinfo.callback(cog, ctx, role=role)

    embed = ctx.send.await_args.kwargs["embed"]
    fields = {f.name: f.value for f in embed.fields}
    assert fields["Colour"] == "Default"


@pytest.mark.asyncio
async def test_roleinfo_error_handler_friendly_on_bad_role():
    cog = RoleCog(MagicMock())
    ctx = MagicMock()
    ctx.send = AsyncMock()

    await cog.roleinfo_error(ctx, commands.RoleNotFound("ghost"))

    ctx.send.assert_awaited_once()
    msg = ctx.send.await_args.args[0]
    assert "couldn't find that role" in msg


@pytest.mark.asyncio
async def test_roleinfo_error_handler_reraises_unexpected():
    cog = RoleCog(MagicMock())
    ctx = MagicMock()
    ctx.send = AsyncMock()

    boom = RuntimeError("unexpected")
    with pytest.raises(RuntimeError):
        await cog.roleinfo_error(ctx, boom)
    ctx.send.assert_not_awaited()
