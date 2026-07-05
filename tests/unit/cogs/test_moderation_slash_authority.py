"""Stage-2 walk bug #4 — ``/moderation`` slash honours the configured mod role.

The slash front door previously gated on ``app_perms_or_owner`` alone, which
never consulted governance, so a configured-moderator-role holder (without the
raw Discord ``moderate_members`` permission) was denied the slash while
``!modmenu`` and the panel admitted them. The fix routes the slash through
``_require_mod_slash`` (Discord perm OR platform owner OR the governance
capability) and drops the client-side ``default_permissions`` hide so the
runtime check is the sole authority boundary.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from discord import app_commands
from discord.ext import commands

from cogs.moderation_cog import ModerationCog, _require_mod_slash

# ruff: noqa: S101


def _predicate():
    """The bare async predicate the slash check wraps (via the command)."""
    cog = ModerationCog(MagicMock(spec=commands.Bot))
    cmd = next(c for c in cog.walk_app_commands() if c.name == "moderation")
    assert len(cmd.checks) == 1
    return cmd.checks[0]


def _interaction(*, moderate_members: bool):
    # id far from any platform-owner id configured in the test env.
    return SimpleNamespace(
        user=SimpleNamespace(
            id=987654321,
            guild_permissions=SimpleNamespace(moderate_members=moderate_members),
        ),
    )


@pytest.mark.asyncio
async def test_slash_permission_path_admits(monkeypatch):
    """A raw moderate_members holder is admitted without consulting governance."""
    import cogs.moderation_cog as cog_mod

    spy = AsyncMock(return_value=False)
    monkeypatch.setattr(cog_mod, "can_execute", spy)
    assert await _predicate()(_interaction(moderate_members=True)) is True
    spy.assert_not_awaited()  # the permission short-circuits


@pytest.mark.asyncio
async def test_slash_capability_path_admits(monkeypatch):
    """A configured-mod-role holder (no raw perm) is admitted via governance —
    the bug being fixed."""
    import cogs.moderation_cog as cog_mod

    monkeypatch.setattr(cog_mod, "can_execute", AsyncMock(return_value=True))
    assert await _predicate()(_interaction(moderate_members=False)) is True


@pytest.mark.asyncio
async def test_slash_neither_raises_missing_permissions(monkeypatch):
    """No perm and no capability → the same denial as before (MissingPermissions)."""
    import cogs.moderation_cog as cog_mod

    monkeypatch.setattr(cog_mod, "can_execute", AsyncMock(return_value=False))
    with pytest.raises(app_commands.MissingPermissions):
        await _predicate()(_interaction(moderate_members=False))


def test_slash_has_no_client_side_default_permissions():
    """The client-side hide is dropped so role-only mods can see/invoke it."""
    cog = ModerationCog(MagicMock(spec=commands.Bot))
    cmd = next(c for c in cog.walk_app_commands() if c.name == "moderation")
    assert cmd.default_permissions is None
