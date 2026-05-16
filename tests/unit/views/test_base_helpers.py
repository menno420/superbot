"""Contract tests for ``views.base`` helpers."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from views.base import BaseView, send_panel


@pytest.mark.asyncio
async def test_send_panel_sends_and_binds_message():
    """send_panel must call ctx.send(embed, view), assign view.message, return msg."""
    ctx = MagicMock()
    sent = MagicMock(spec=discord.Message)
    ctx.send = AsyncMock(return_value=sent)

    author = MagicMock(id=42)
    view = BaseView(author)
    embed = discord.Embed(title="hello")

    returned = await send_panel(ctx, embed=embed, view=view)

    ctx.send.assert_awaited_once_with(embed=embed, view=view)
    assert view.message is sent
    assert returned is sent


@pytest.mark.asyncio
async def test_send_panel_propagates_send_exception():
    """If ctx.send raises, send_panel must re-raise and not silently bind."""
    ctx = MagicMock()
    ctx.send = AsyncMock(side_effect=discord.HTTPException(MagicMock(status=500), "x"))

    author = MagicMock(id=42)
    view = BaseView(author)

    with pytest.raises(discord.HTTPException):
        await send_panel(ctx, embed=discord.Embed(), view=view)

    assert view.message is None
