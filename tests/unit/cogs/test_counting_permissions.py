"""BUG-0012 — counting staff check must gate on real permissions, not role names.

``CountingCog.is_staff_or_owner`` previously returned True for anyone holding a
role merely *named* ``"Admin"`` or ``"Moderator"`` — regardless of whether that
role carried any actual Discord permissions.  A powerless cosmetic role with a
matching name therefore bypassed the permission system and unlocked the counting
management commands.

These tests pin that the check now depends on real Discord permissions (via the
canonical ``utils.visibility_rules`` tier) and that a name match alone confers
nothing.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from cogs.counting_cog import CountingCog


def _cog(owner: bool = False) -> CountingCog:
    cog = CountingCog(MagicMock())
    cog.bot.is_owner = AsyncMock(return_value=owner)
    return cog


def _ctx(
    *,
    perms: discord.Permissions,
    role_names: tuple[str, ...] = (),
    member_id: int = 1,
    guild_owner_id: int = 999,
):
    ctx = MagicMock()
    member = MagicMock()
    member.id = member_id
    member.guild_permissions = perms
    roles = []
    for n in role_names:
        role = MagicMock()
        role.name = n  # `name` is reserved in the MagicMock constructor
        roles.append(role)
    member.roles = roles
    ctx.author = member
    ctx.guild = MagicMock()
    ctx.guild.owner_id = guild_owner_id
    return ctx


@pytest.mark.asyncio
async def test_role_named_admin_without_permissions_is_denied():
    """The core regression: a role *named* Admin/Moderator with no real
    permissions must NOT grant staff access."""
    cog = _cog(owner=False)
    ctx = _ctx(perms=discord.Permissions.none(), role_names=("Admin", "Moderator"))
    assert await cog.is_staff_or_owner(ctx) is False


@pytest.mark.asyncio
async def test_real_administrator_is_allowed():
    cog = _cog(owner=False)
    ctx = _ctx(perms=discord.Permissions(administrator=True))
    assert await cog.is_staff_or_owner(ctx) is True


@pytest.mark.asyncio
async def test_real_moderator_is_allowed():
    cog = _cog(owner=False)
    ctx = _ctx(perms=discord.Permissions(moderate_members=True))
    assert await cog.is_staff_or_owner(ctx) is True


@pytest.mark.asyncio
async def test_plain_member_is_denied():
    cog = _cog(owner=False)
    ctx = _ctx(perms=discord.Permissions.none())
    assert await cog.is_staff_or_owner(ctx) is False


@pytest.mark.asyncio
async def test_bot_owner_always_allowed():
    cog = _cog(owner=True)
    # Even with zero permissions, the bot owner passes.
    ctx = _ctx(perms=discord.Permissions.none())
    assert await cog.is_staff_or_owner(ctx) is True


@pytest.mark.asyncio
async def test_guild_owner_is_allowed():
    cog = _cog(owner=False)
    ctx = _ctx(perms=discord.Permissions.none(), member_id=42, guild_owner_id=42)
    assert await cog.is_staff_or_owner(ctx) is True
