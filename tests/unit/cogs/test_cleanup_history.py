from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from cogs.cleanup_cog import Cleanup


def _msg(content: str):
    m = MagicMock()
    m.content = content
    m.author = SimpleNamespace(bot=False)
    m.delete = AsyncMock()
    return m


def _ctx(messages):
    ctx = MagicMock()
    me = SimpleNamespace()
    ctx.guild = SimpleNamespace(id=1, me=me)
    ctx.channel = MagicMock()

    async def _history(limit=100):
        for m in messages[:limit]:
            yield m

    ctx.channel.history = _history
    ctx.channel.permissions_for = MagicMock(
        return_value=SimpleNamespace(manage_messages=True)
    )
    ctx.channel.name = "general"
    ctx.channel.id = 9
    ctx.author = SimpleNamespace(id=42)
    ctx.message = MagicMock()
    ctx.message.delete = AsyncMock()
    ctx.send = AsyncMock()
    return ctx


def _confirmed_reaction():
    return SimpleNamespace(emoji="✅", message=SimpleNamespace(id=100))


@pytest.mark.asyncio
async def test_cleanuphistory_keyword_mode_deletes_only_matching_message():
    cog = Cleanup(MagicMock())
    match = _msg("hello bad")
    other = _msg("clean")
    ctx = _ctx([match, other])
    confirm = MagicMock(id=100)
    confirm.add_reaction = AsyncMock()
    confirm.delete = AsyncMock()
    ctx.send.side_effect = [confirm, MagicMock()]
    with (
        patch("cogs.cleanup_cog.db.get_prohibited_words", new=AsyncMock(return_value=[])),
        patch.object(cog.bot, "wait_for", new=AsyncMock(return_value=(_confirmed_reaction(), ctx.author))),
    ):
        await cog.cleanup_history.callback(cog, ctx, 10, keyword="keyword bad")
    match.delete.assert_awaited_once()
    other.delete.assert_not_called()


@pytest.mark.asyncio
async def test_cleanuphistory_backward_compat_keyword():
    cog = Cleanup(MagicMock())
    match = _msg("contains legacyword")
    ctx = _ctx([match])
    confirm = MagicMock(id=100)
    confirm.add_reaction = AsyncMock()
    confirm.delete = AsyncMock()
    ctx.send.side_effect = [confirm, MagicMock()]
    with (
        patch("cogs.cleanup_cog.db.get_prohibited_words", new=AsyncMock(return_value=[])),
        patch.object(cog.bot, "wait_for", new=AsyncMock(return_value=(_confirmed_reaction(), ctx.author))),
    ):
        await cog.cleanup_history.callback(cog, ctx, 10, keyword="legacyword")
    match.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_cleanuphistory_commands_mode_deletes_prefixed_messages():
    cog = Cleanup(MagicMock())
    cmd = _msg("   !help me")
    normal = _msg("hello world")
    ctx = _ctx([cmd, normal])
    confirm = MagicMock(id=100)
    confirm.add_reaction = AsyncMock()
    confirm.delete = AsyncMock()
    ctx.send.side_effect = [confirm, MagicMock()]
    with (
        patch("cogs.cleanup_cog.db.get_prohibited_words", new=AsyncMock(return_value=[])),
        patch.object(cog.bot, "wait_for", new=AsyncMock(return_value=(_confirmed_reaction(), ctx.author))),
    ):
        await cog.cleanup_history.callback(cog, ctx, 10, keyword="commands")
    cmd.delete.assert_awaited_once()
    normal.delete.assert_not_called()


@pytest.mark.asyncio
async def test_cleanuphistory_prohibited_mode_uses_word_boundary():
    cog = Cleanup(MagicMock())
    exact = _msg("this has badword here")
    partial = _msg("this has badwording")
    ctx = _ctx([exact, partial])
    confirm = MagicMock(id=100)
    confirm.add_reaction = AsyncMock()
    confirm.delete = AsyncMock()
    ctx.send.side_effect = [confirm, MagicMock()]
    with (
        patch("cogs.cleanup_cog.db.get_prohibited_words", new=AsyncMock(return_value=["badword"])),
        patch.object(cog.bot, "wait_for", new=AsyncMock(return_value=(_confirmed_reaction(), ctx.author))),
    ):
        await cog.cleanup_history.callback(cog, ctx, 10, keyword="prohibited")
    exact.delete.assert_awaited_once()
    partial.delete.assert_not_called()


@pytest.mark.asyncio
async def test_cleanuphistory_zero_match_skips_confirmation():
    cog = Cleanup(MagicMock())
    ctx = _ctx([_msg("hello world")])
    with patch("cogs.cleanup_cog.db.get_prohibited_words", new=AsyncMock(return_value=[])):
        await cog.cleanup_history.callback(cog, ctx, 10, keyword="keyword missing")
    first_msg = ctx.send.await_args_list[0].args[0]
    assert "Matched 0" in first_msg


@pytest.mark.asyncio
async def test_cleanuphistory_cancel_confirmation_deletes_nothing():
    cog = Cleanup(MagicMock())
    match = _msg("keyword hit")
    ctx = _ctx([match])
    confirm = MagicMock(id=100)
    confirm.add_reaction = AsyncMock()
    confirm.delete = AsyncMock()
    ctx.send.side_effect = [confirm, MagicMock()]
    reaction = SimpleNamespace(emoji="❌", message=SimpleNamespace(id=100))
    with (
        patch("cogs.cleanup_cog.db.get_prohibited_words", new=AsyncMock(return_value=[])),
        patch.object(cog.bot, "wait_for", new=AsyncMock(return_value=(reaction, ctx.author))),
    ):
        await cog.cleanup_history.callback(cog, ctx, 10, keyword="keyword keyword")
    match.delete.assert_not_called()


@pytest.mark.asyncio
async def test_cleanuphistory_delete_failure_is_counted():
    cog = Cleanup(MagicMock())
    match = _msg("keyword hit")
    resp = MagicMock(status=500)
    resp.reason = "oops"
    match.delete.side_effect = discord.HTTPException(resp, "boom")
    ctx = _ctx([match])
    confirm = MagicMock(id=100)
    confirm.add_reaction = AsyncMock()
    confirm.delete = AsyncMock()
    status_msg = MagicMock()
    ctx.send.side_effect = [confirm, status_msg]
    with (
        patch("cogs.cleanup_cog.db.get_prohibited_words", new=AsyncMock(return_value=[])),
        patch.object(cog.bot, "wait_for", new=AsyncMock(return_value=(_confirmed_reaction(), ctx.author))),
    ):
        await cog.cleanup_history.callback(cog, ctx, 10, keyword="keyword keyword")
    completion = ctx.send.await_args_list[-1].args[0]
    assert "failed 1" in completion
