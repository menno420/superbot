"""Stage-2 walk bug #2 — the on_ready startup greeting targets ``#bot-spam``.

The greeting looked up ``name="bot_spam"`` (underscore), which
``resolve_channel`` matches by exact name, so it never matched the real
``#bot-spam`` channel and the greeting was silently dead. This pins the
hyphenated name.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from cogs.admin_cog import AdminCog

# ruff: noqa: S101


def _guild(channel_name: str):
    me = SimpleNamespace(id=1)
    channel = MagicMock()
    channel.name = channel_name
    channel.permissions_for = MagicMock(
        return_value=SimpleNamespace(send_messages=True),
    )
    channel.send = AsyncMock()
    guild = SimpleNamespace(me=me, text_channels=[channel], categories=[])
    return guild, channel


@pytest.mark.asyncio
async def test_on_ready_greets_bot_spam_channel():
    guild, channel = _guild("bot-spam")
    bot = MagicMock()
    bot.guilds = [guild]
    bot.user = SimpleNamespace(name="Galaxy Bot")
    cog = AdminCog(bot)

    await cog.on_ready()

    channel.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_on_ready_ignores_underscore_named_channel():
    # The old buggy literal ("bot_spam") must NOT resolve — guards the regression.
    guild, channel = _guild("bot_spam")
    bot = MagicMock()
    bot.guilds = [guild]
    bot.user = SimpleNamespace(name="Galaxy Bot")
    cog = AdminCog(bot)

    await cog.on_ready()

    channel.send.assert_not_called()
