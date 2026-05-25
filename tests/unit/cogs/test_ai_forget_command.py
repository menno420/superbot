"""Tests for !ai forget — channel-scoped cache flush."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from cogs.ai_cog import AICog
from services import ai_conversation_service


@pytest.fixture(autouse=True)
def _reset_buffers():
    ai_conversation_service._reset_for_tests()
    yield
    ai_conversation_service._reset_for_tests()


def _ctx(guild_id: int | None = 1, channel_id: int = 100):
    ctx = MagicMock()
    ctx.guild = SimpleNamespace(id=guild_id) if guild_id else None
    ctx.channel = SimpleNamespace(id=channel_id, mention=f"<#{channel_id}>")
    ctx.author = SimpleNamespace(id=42)
    ctx.send = AsyncMock()
    return ctx


@pytest.mark.asyncio
async def test_forget_flushes_only_current_channel():
    ai_conversation_service.append(1, 100, user_id=1, role="user", text="keep-elsewhere")
    ai_conversation_service.append(1, 200, user_id=1, role="user", text="drop-me")

    cog = AICog(bot=MagicMock())
    ctx = _ctx(guild_id=1, channel_id=200)
    await cog.ai_forget.callback(cog, ctx)

    assert ai_conversation_service.recent_turns(1, 100)
    assert ai_conversation_service.recent_turns(1, 200) == []
    ctx.send.assert_awaited_once()
    assert "Cleared" in ctx.send.await_args.args[0]


@pytest.mark.asyncio
async def test_forget_reports_no_cache_when_empty():
    cog = AICog(bot=MagicMock())
    ctx = _ctx(guild_id=1, channel_id=200)
    await cog.ai_forget.callback(cog, ctx)

    msg = ctx.send.await_args.args[0]
    assert "No chat memory" in msg


@pytest.mark.asyncio
async def test_forget_requires_guild_context():
    cog = AICog(bot=MagicMock())
    ctx = _ctx(guild_id=None)
    await cog.ai_forget.callback(cog, ctx)

    msg = ctx.send.await_args.args[0]
    assert "guild context" in msg
