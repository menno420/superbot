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
    ctx.guild = SimpleNamespace(id=1)
    ctx.channel = MagicMock()

    async def _history(limit=100):
        for m in messages[:limit]:
            yield m

    ctx.channel.history = _history
    ctx.channel.name = "general"
    ctx.channel.id = 9
    ctx.author = SimpleNamespace(id=42)
    ctx.message = MagicMock()
    ctx.message.delete = AsyncMock()
    ctx.send = AsyncMock()
    return ctx


@pytest.mark.asyncio
async def test_cleanuphistory_keyword_mode_deletes_matches():
    cog = Cleanup(MagicMock())
    ctx = _ctx([_msg("hello bad"), _msg("clean")])
    confirm = MagicMock(id=100)
    confirm.add_reaction = AsyncMock()
    confirm.delete = AsyncMock()
    ctx.send.side_effect = [confirm, MagicMock()]
    reaction = SimpleNamespace(emoji="✅", message=SimpleNamespace(id=100))
    with (
        patch("cogs.cleanup_cog.db.get_prohibited_words", new=AsyncMock(return_value=[])),
        patch.object(cog.bot, "wait_for", new=AsyncMock(return_value=(reaction, ctx.author))),
    ):
        await cog.cleanup_history.callback(cog, ctx, 10, keyword="keyword bad")
    assert ctx.channel.history is not None
    assert ctx.send.await_count >= 2


@pytest.mark.asyncio
async def test_cleanuphistory_backward_compat_keyword():
    cog = Cleanup(MagicMock())
    match = _msg("contains legacyword")
    ctx = _ctx([match])
    confirm = MagicMock(id=100)
    confirm.add_reaction = AsyncMock()
    confirm.delete = AsyncMock()
    ctx.send.side_effect = [confirm, MagicMock()]
    reaction = SimpleNamespace(emoji="✅", message=SimpleNamespace(id=100))
    with (
        patch("cogs.cleanup_cog.db.get_prohibited_words", new=AsyncMock(return_value=[])),
        patch.object(cog.bot, "wait_for", new=AsyncMock(return_value=(reaction, ctx.author))),
    ):
        await cog.cleanup_history.callback(cog, ctx, 10, keyword="legacyword")
    match.delete.assert_awaited_once()

