"""Tests for core.runtime.panel_recovery — Phase S2.3."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from core.runtime.panel_recovery import restore_parent_or_send_fresh


def _make_message() -> MagicMock:
    msg = MagicMock(spec=discord.Message)
    msg.id = 12345
    msg.edit = AsyncMock()
    msg.channel = MagicMock(spec=discord.TextChannel)
    msg.channel.send = AsyncMock()
    return msg


def _make_channel() -> MagicMock:
    ch = MagicMock(spec=discord.TextChannel)
    ch.send = AsyncMock()
    return ch


def _embed() -> discord.Embed:
    return discord.Embed(title="restored panel")


def _view() -> discord.ui.View:
    return discord.ui.View(timeout=None)


def _http_exc(status: int, text: str) -> discord.HTTPException:
    """Build a discord.HTTPException for tests without a real aiohttp response."""
    resp = MagicMock()
    resp.status = status
    resp.reason = text
    return discord.HTTPException(resp, text)


def _not_found() -> discord.NotFound:
    resp = MagicMock()
    resp.status = 404
    resp.reason = "Not Found"
    return discord.NotFound(resp, "Not Found")


def _forbidden() -> discord.Forbidden:
    resp = MagicMock()
    resp.status = 403
    resp.reason = "Forbidden"
    return discord.Forbidden(resp, "Forbidden")


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_returns_edited_parent_on_success():
    parent = _make_message()
    embed = _embed()
    view = _view()

    result = await restore_parent_or_send_fresh(
        parent_message=parent,
        channel=_make_channel(),
        embed=embed,
        view=view,
    )

    assert result is parent
    parent.edit.assert_awaited_once_with(embed=embed, view=view)


# ---------------------------------------------------------------------------
# Parent missing / deleted
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_parent_none_sends_fresh_to_channel():
    channel = _make_channel()
    sent = MagicMock(spec=discord.Message)
    channel.send.return_value = sent

    result = await restore_parent_or_send_fresh(
        parent_message=None,
        channel=channel,
        embed=_embed(),
        view=_view(),
    )

    assert result is sent
    channel.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_parent_not_found_falls_back_to_fresh_send():
    parent = _make_message()
    parent.edit.side_effect = _not_found()
    channel = _make_channel()
    sent = MagicMock(spec=discord.Message)
    channel.send.return_value = sent

    result = await restore_parent_or_send_fresh(
        parent_message=parent,
        channel=channel,
        embed=_embed(),
        view=_view(),
    )

    assert result is sent
    parent.edit.assert_awaited_once()
    channel.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_parent_not_found_uses_parent_channel_when_no_channel_arg():
    """Channel defaults to parent_message.channel when omitted."""
    parent = _make_message()
    parent.edit.side_effect = _not_found()
    sent = MagicMock(spec=discord.Message)
    parent.channel.send.return_value = sent

    result = await restore_parent_or_send_fresh(
        parent_message=parent,
        embed=_embed(),
        view=_view(),
    )

    assert result is sent
    parent.channel.send.assert_awaited_once()


# ---------------------------------------------------------------------------
# Forbidden / HTTP error
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_edit_forbidden_returns_none_without_falling_back():
    """Forbidden means we LOST permission — don't loop by trying send."""
    parent = _make_message()
    parent.edit.side_effect = _forbidden()
    channel = _make_channel()

    result = await restore_parent_or_send_fresh(
        parent_message=parent,
        channel=channel,
        embed=_embed(),
        view=_view(),
    )

    assert result is None
    parent.edit.assert_awaited_once()
    channel.send.assert_not_awaited()


@pytest.mark.asyncio
async def test_edit_http_exception_returns_none():
    parent = _make_message()
    parent.edit.side_effect = _http_exc(500, "Internal Server Error")
    channel = _make_channel()

    result = await restore_parent_or_send_fresh(
        parent_message=parent,
        channel=channel,
        embed=_embed(),
        view=_view(),
    )

    assert result is None
    channel.send.assert_not_awaited()


# ---------------------------------------------------------------------------
# Fresh-send failure modes
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fresh_send_forbidden_returns_none():
    channel = _make_channel()
    channel.send.side_effect = _forbidden()

    result = await restore_parent_or_send_fresh(
        parent_message=None,
        channel=channel,
        embed=_embed(),
        view=_view(),
    )

    assert result is None


@pytest.mark.asyncio
async def test_no_parent_no_channel_returns_none():
    result = await restore_parent_or_send_fresh(
        parent_message=None,
        channel=None,
        embed=_embed(),
        view=_view(),
    )
    assert result is None


# ---------------------------------------------------------------------------
# Wiring smoke checks — each channel sub-panel imports the utility
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "module_path",
    [
        "views.channels.restrict_panel",
        "views.channels.delete_panel",
        "views.channels.create_panel",
    ],
)
def test_channel_subpanels_import_recovery_helper(module_path):
    import importlib

    mod = importlib.import_module(module_path)
    assert hasattr(mod, "restore_parent_or_send_fresh"), (
        f"{module_path} still uses the silent `except Exception: pass` "
        f"pattern instead of the panel_recovery helper."
    )
