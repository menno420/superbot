"""Tests for the setup workspace anchor renderer.

``views/setup/_anchor.py`` is the thin renderer that backs the
aggressive "no ephemeral setup panels" policy. These tests cover:

* ``render_setup_state`` edits an existing anchor when fetchable.
* ``render_setup_state`` posts a new anchor and persists the id when
  the existing one is missing.
* ``render_setup_state`` returns False when the workspace channel is
  unresolvable (no perms / kicked).
* ``push_setup_notice`` appends a one-shot message and never touches
  the anchor id.
* Both helpers swallow discord.HTTPException and return False rather
  than raising.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from views.setup._anchor import push_setup_notice, render_setup_state


def _guild(guild_id: int = 99) -> MagicMock:
    g = MagicMock(spec=discord.Guild)
    g.id = guild_id
    return g


def _channel(channel_id: int = 555) -> MagicMock:
    c = MagicMock(spec=discord.TextChannel)
    c.id = channel_id
    c.send = AsyncMock()
    c.fetch_message = AsyncMock()
    return c


def _session(
    *,
    channel_id: int | None = 555,
    message_id: int | None = 4242,
) -> SimpleNamespace:
    return SimpleNamespace(
        setup_channel_id=channel_id,
        setup_message_id=message_id,
    )


# ---------------------------------------------------------------------------
# render_setup_state — edit-in-place when anchor is fetchable
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_render_setup_state_edits_existing_anchor():
    guild = _guild()
    channel = _channel()
    session = _session()
    existing_msg = MagicMock()
    existing_msg.edit = AsyncMock()
    channel.fetch_message.return_value = existing_msg

    embed = discord.Embed(title="Hub")
    view = MagicMock(spec=discord.ui.View)

    with (
        patch(
            "views.setup._anchor.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=session,
        ),
        patch(
            "views.setup._anchor.setup_channel.ensure_setup_channel",
            new_callable=AsyncMock,
            return_value=(channel, False),
        ),
        patch(
            "views.setup._anchor.setup_session.set_setup_channel_id",
            new_callable=AsyncMock,
        ),
    ):
        ok = await render_setup_state(guild, embed=embed, view=view)

    assert ok is True
    channel.fetch_message.assert_awaited_once_with(4242)
    existing_msg.edit.assert_awaited_once_with(embed=embed, view=view)
    channel.send.assert_not_called()


# ---------------------------------------------------------------------------
# render_setup_state — repost when anchor missing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_render_setup_state_reposts_when_anchor_missing():
    guild = _guild()
    channel = _channel()
    session = _session()
    channel.fetch_message.side_effect = discord.NotFound(MagicMock(), "gone")
    new_msg = MagicMock()
    new_msg.id = 9999
    channel.send.return_value = new_msg

    embed = discord.Embed(title="Hub")

    with (
        patch(
            "views.setup._anchor.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=session,
        ),
        patch(
            "views.setup._anchor.setup_channel.ensure_setup_channel",
            new_callable=AsyncMock,
            return_value=(channel, False),
        ),
        patch(
            "views.setup._anchor.setup_session.set_setup_channel_id",
            new_callable=AsyncMock,
        ),
        patch(
            "views.setup._anchor.setup_session.set_setup_message_id",
            new_callable=AsyncMock,
        ) as set_msg_id,
    ):
        ok = await render_setup_state(guild, embed=embed)

    assert ok is True
    channel.send.assert_awaited_once_with(embed=embed, view=None)
    # Cleared stale id then persisted the fresh one.
    set_msg_id.assert_any_call(guild.id, None)
    set_msg_id.assert_any_call(guild.id, 9999)


# ---------------------------------------------------------------------------
# render_setup_state — controlled failure when workspace unreachable
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_render_setup_state_returns_false_when_channel_missing():
    """When ensure_setup_channel returns None (missing perms / kicked),
    the renderer must report failure cleanly so callers can surface a
    controlled ephemeral.
    """
    guild = _guild()
    session = _session()

    with (
        patch(
            "views.setup._anchor.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=session,
        ),
        patch(
            "views.setup._anchor.setup_channel.ensure_setup_channel",
            new_callable=AsyncMock,
            return_value=(None, False),
        ),
    ):
        ok = await render_setup_state(guild, embed=discord.Embed(title="x"))

    assert ok is False


@pytest.mark.asyncio
async def test_render_setup_state_returns_false_on_http_failure_during_send():
    """If both fetch and send fail, the helper must swallow the
    HTTPException and return False — never raise.
    """
    guild = _guild()
    channel = _channel()
    session = _session(message_id=None)  # no existing anchor → goes straight to send
    channel.send.side_effect = discord.HTTPException(MagicMock(), "rate limited")

    with (
        patch(
            "views.setup._anchor.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=session,
        ),
        patch(
            "views.setup._anchor.setup_channel.ensure_setup_channel",
            new_callable=AsyncMock,
            return_value=(channel, False),
        ),
        patch(
            "views.setup._anchor.setup_session.set_setup_channel_id",
            new_callable=AsyncMock,
        ),
    ):
        ok = await render_setup_state(guild, embed=discord.Embed(title="x"))

    assert ok is False


# ---------------------------------------------------------------------------
# push_setup_notice — append-only, never touches anchor id
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_push_setup_notice_appends_one_off_message():
    guild = _guild()
    channel = _channel()
    session = _session()
    embed = discord.Embed(title="Apply Recommended succeeded")

    with (
        patch(
            "views.setup._anchor.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=session,
        ),
        patch(
            "views.setup._anchor.setup_channel.ensure_setup_channel",
            new_callable=AsyncMock,
            return_value=(channel, False),
        ),
        patch(
            "views.setup._anchor.setup_session.set_setup_message_id",
            new_callable=AsyncMock,
        ) as set_msg_id,
    ):
        ok = await push_setup_notice(guild, embed=embed)

    assert ok is True
    channel.send.assert_awaited_once_with(embed=embed)
    # push_setup_notice must NEVER touch the anchor id — anchor stays
    # the source of truth.
    set_msg_id.assert_not_called()


@pytest.mark.asyncio
async def test_push_setup_notice_returns_false_when_channel_missing():
    guild = _guild()
    session = _session()

    with (
        patch(
            "views.setup._anchor.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=session,
        ),
        patch(
            "views.setup._anchor.setup_channel.ensure_setup_channel",
            new_callable=AsyncMock,
            return_value=(None, False),
        ),
    ):
        ok = await push_setup_notice(guild, embed=discord.Embed(title="x"))

    assert ok is False


@pytest.mark.asyncio
async def test_push_setup_notice_swallows_http_failure():
    guild = _guild()
    channel = _channel()
    channel.send.side_effect = discord.HTTPException(MagicMock(), "fail")
    session = _session()

    with (
        patch(
            "views.setup._anchor.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=session,
        ),
        patch(
            "views.setup._anchor.setup_channel.ensure_setup_channel",
            new_callable=AsyncMock,
            return_value=(channel, False),
        ),
    ):
        ok = await push_setup_notice(guild, embed=discord.Embed(title="x"))

    assert ok is False
