"""Contract tests for ``views.base`` helpers."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from views.base import BaseView, HubView, handle_view_error, send_panel


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


def test_hub_view_defaults_to_180s_timeout():
    """HubView freezes the 180s timeout so cog hubs stop repeating it."""
    author = MagicMock(id=42)
    view = HubView(author)
    assert view.timeout == 180
    assert view._author is author
    assert view._public is False


def test_hub_view_accepts_public_flag():
    """HubView passes through public=True for shared panels like Utility."""
    author = MagicMock(id=42)
    view = HubView(author, public=True)
    assert view.timeout == 180
    assert view._public is True


@pytest.mark.asyncio
async def test_handle_view_error_logs_and_sends_generic_ephemeral():
    """The shared error handler logs with context and sends a generic ephemeral."""
    view = MagicMock(spec=discord.ui.View)
    item = MagicMock(custom_id="cid", label="Click me")
    interaction = MagicMock()
    interaction.user = MagicMock(id=42)
    interaction.guild_id = 99
    interaction.channel_id = 100
    interaction.message = MagicMock(id=200)
    interaction.response.is_done.return_value = False
    interaction.response.send_message = AsyncMock()

    await handle_view_error(view, interaction, ValueError("boom"), item)

    interaction.response.send_message.assert_awaited_once()
    args, kwargs = interaction.response.send_message.call_args
    assert "An error occurred" in args[0]
    assert kwargs.get("ephemeral") is True


@pytest.mark.asyncio
async def test_handle_view_error_skips_send_when_response_done():
    """If the interaction was already responded to, don't double-send."""
    view = MagicMock(spec=discord.ui.View)
    item = MagicMock(custom_id="cid", label=None)
    interaction = MagicMock()
    interaction.response.is_done.return_value = True
    interaction.response.send_message = AsyncMock()

    await handle_view_error(view, interaction, RuntimeError("x"), item)

    interaction.response.send_message.assert_not_called()
