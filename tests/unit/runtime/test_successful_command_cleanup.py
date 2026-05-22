from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

import bot1


def _ctx(*, guild=True, bot_author=False, with_message=True):
    ctx = MagicMock()
    ctx.guild = MagicMock() if guild else None
    ctx.author = MagicMock()
    ctx.author.bot = bot_author
    ctx.channel = MagicMock()
    ctx.channel.id = 123
    if with_message:
        ctx.message = MagicMock()
        ctx.message.delete = AsyncMock()
    else:
        ctx.message = None
    return ctx


@pytest.mark.asyncio
async def test_successful_command_is_deleted_when_policy_says_delete():
    ctx = _ctx()
    policy = SimpleNamespace(delete_message=True, delete_after_seconds=7)
    with (
        patch("bot1.governance_service.GovernanceContext.from_ctx", return_value=MagicMock()),
        patch("bot1.governance_service.resolve_cleanup_policy", new=AsyncMock(return_value=policy)),
    ):
        await bot1._maybe_cleanup_successful_command(ctx)
    ctx.message.delete.assert_awaited_once_with(delay=7)


@pytest.mark.asyncio
async def test_successful_command_preserved_when_policy_says_no_delete():
    ctx = _ctx()
    policy = SimpleNamespace(delete_message=False, delete_after_seconds=0)
    with (
        patch("bot1.governance_service.GovernanceContext.from_ctx", return_value=MagicMock()),
        patch("bot1.governance_service.resolve_cleanup_policy", new=AsyncMock(return_value=policy)),
    ):
        await bot1._maybe_cleanup_successful_command(ctx)
    ctx.message.delete.assert_not_called()


@pytest.mark.asyncio
async def test_dm_context_is_ignored():
    ctx = _ctx(guild=False)
    await bot1._maybe_cleanup_successful_command(ctx)
    ctx.message.delete.assert_not_called()


@pytest.mark.asyncio
async def test_missing_message_is_ignored():
    ctx = _ctx(with_message=False)
    await bot1._maybe_cleanup_successful_command(ctx)


@pytest.mark.asyncio
async def test_forbidden_does_not_raise():
    ctx = _ctx()
    response = MagicMock(status=403)
    response.reason = "Forbidden"
    policy = SimpleNamespace(delete_message=True, delete_after_seconds=0)
    ctx.message.delete.side_effect = discord.Forbidden(response, "Forbidden")
    with (
        patch("bot1.governance_service.GovernanceContext.from_ctx", return_value=MagicMock()),
        patch("bot1.governance_service.resolve_cleanup_policy", new=AsyncMock(return_value=policy)),
    ):
        await bot1._maybe_cleanup_successful_command(ctx)
