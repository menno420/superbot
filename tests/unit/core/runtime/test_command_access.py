"""Tests for fresh-guild bootstrap command access helpers."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from core.runtime.command_access import (
    can_bypass_channel_guard,
    is_bootstrap_command,
)


def _ctx(
    *,
    command_name: str = "help",
    qualified_name: str | None = None,
    aliases: tuple[str, ...] = (),
    invoked_with: str | None = None,
    author_id: int = 10,
    owner_id: int = 10,
    administrator: bool = False,
    manage_guild: bool = False,
    is_bot_owner: bool = False,
    guild: object | None = None,
):
    if guild is None:
        guild = SimpleNamespace(owner_id=owner_id)
    author = SimpleNamespace(
        id=author_id,
        guild_permissions=SimpleNamespace(
            administrator=administrator,
            manage_guild=manage_guild,
        ),
    )
    command = SimpleNamespace(
        name=command_name,
        qualified_name=qualified_name or command_name,
        aliases=aliases,
    )
    bot = SimpleNamespace(is_owner=AsyncMock(return_value=is_bot_owner))
    return SimpleNamespace(
        guild=guild,
        author=author,
        command=command,
        invoked_with=invoked_with or command_name,
        bot=bot,
    )


def test_is_bootstrap_command_accepts_bare_and_qualified_names():
    assert is_bootstrap_command("help") is True
    assert is_bootstrap_command("platform identity") is True
    assert is_bootstrap_command("settings access") is True


def test_is_bootstrap_command_rejects_normal_gameplay_commands():
    assert is_bootstrap_command("daily") is False
    assert is_bootstrap_command("blackjack") is False
    assert is_bootstrap_command(None) is False


@pytest.mark.asyncio
async def test_guild_owner_can_bypass_for_bootstrap_command():
    ctx = _ctx(command_name="help", author_id=42, owner_id=42)

    assert await can_bypass_channel_guard(ctx) is True


@pytest.mark.asyncio
async def test_administrator_can_bypass_for_bootstrap_command():
    ctx = _ctx(command_name="platform", author_id=7, owner_id=42, administrator=True)

    assert await can_bypass_channel_guard(ctx) is True


@pytest.mark.asyncio
async def test_manage_guild_member_can_bypass_for_bootstrap_command():
    ctx = _ctx(command_name="settings", author_id=7, owner_id=42, manage_guild=True)

    assert await can_bypass_channel_guard(ctx) is True


@pytest.mark.asyncio
async def test_bot_owner_can_bypass_for_bootstrap_command():
    ctx = _ctx(command_name="syncslash", author_id=7, owner_id=42, is_bot_owner=True)

    assert await can_bypass_channel_guard(ctx) is True


@pytest.mark.asyncio
async def test_non_operator_cannot_bypass_for_bootstrap_command():
    ctx = _ctx(command_name="help", author_id=7, owner_id=42)

    assert await can_bypass_channel_guard(ctx) is False


@pytest.mark.asyncio
async def test_operator_cannot_bypass_for_normal_command():
    ctx = _ctx(command_name="daily", author_id=42, owner_id=42)

    assert await can_bypass_channel_guard(ctx) is False


@pytest.mark.asyncio
async def test_dm_context_cannot_bypass():
    ctx = _ctx(command_name="help", guild=None)

    assert await can_bypass_channel_guard(ctx) is False


@pytest.mark.asyncio
async def test_alias_can_mark_command_as_bootstrap():
    ctx = _ctx(command_name="diagnostics", aliases=("diag",), invoked_with="diag", author_id=1, owner_id=1)

    assert await can_bypass_channel_guard(ctx) is True
