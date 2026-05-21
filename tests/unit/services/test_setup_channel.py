"""Tests for ``services.setup_channel`` — auto-created private setup channel."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from services.setup_channel import (
    SETUP_CHANNEL_NAME,
    ensure_setup_channel,
)


def _make_guild(
    *,
    guild_id: int = 1,
    can_manage_channels: bool = True,
    me_present: bool = True,
    owner_present: bool = True,
    cached_channel: discord.TextChannel | None = None,
):
    g = MagicMock(spec=discord.Guild)
    g.id = guild_id
    g.name = "Test"

    if me_present:
        me = MagicMock()
        me.guild_permissions = SimpleNamespace(manage_channels=can_manage_channels)
        g.me = me
    else:
        g.me = None

    if owner_present:
        g.owner = MagicMock()
        g.owner.mention = "<@99>"
    else:
        g.owner = None

    g.default_role = MagicMock()
    g.get_channel = MagicMock(
        return_value=cached_channel if cached_channel is not None else None,
    )
    return g


def _make_text_channel(channel_id: int = 7000):
    ch = MagicMock(spec=discord.TextChannel)
    ch.id = channel_id
    ch.name = SETUP_CHANNEL_NAME
    return ch


@pytest.mark.asyncio
async def test_ensure_setup_channel_creates_when_missing():
    guild = _make_guild()
    created = _make_text_channel(7000)

    with patch(
        "services.setup_channel.ensure_channel",
        new_callable=AsyncMock,
        return_value=created,
    ) as ensure_mock:
        channel, was_created = await ensure_setup_channel(guild)

    assert channel is created
    assert was_created is True
    ensure_mock.assert_awaited_once()
    kwargs = ensure_mock.await_args.kwargs
    assert kwargs["kind"] == "text"


@pytest.mark.asyncio
async def test_ensure_setup_channel_reuses_cached_id():
    """When the caller supplies the prior ``existing_channel_id`` and the
    guild still has that channel, no creation attempt is made."""
    cached = _make_text_channel(7000)
    guild = _make_guild(cached_channel=cached)

    with patch(
        "services.setup_channel.ensure_channel",
        new_callable=AsyncMock,
    ) as ensure_mock:
        channel, was_created = await ensure_setup_channel(
            guild,
            existing_channel_id=7000,
        )

    assert channel is cached
    assert was_created is False
    ensure_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_ensure_setup_channel_returns_none_when_no_manage_channels():
    """Without Manage Channels the bot cannot create; falls back to caller."""
    guild = _make_guild(can_manage_channels=False)

    with patch(
        "services.setup_channel.ensure_channel",
        new_callable=AsyncMock,
    ) as ensure_mock:
        channel, was_created = await ensure_setup_channel(guild)

    assert channel is None
    assert was_created is False
    ensure_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_ensure_setup_channel_returns_none_when_me_missing():
    """``guild.me`` may be ``None`` for guilds not yet fully resolved."""
    guild = _make_guild(me_present=False)

    channel, was_created = await ensure_setup_channel(guild)

    assert channel is None
    assert was_created is False


@pytest.mark.asyncio
async def test_ensure_setup_channel_handles_forbidden_gracefully():
    guild = _make_guild()

    with patch(
        "services.setup_channel.ensure_channel",
        new_callable=AsyncMock,
        side_effect=discord.Forbidden(MagicMock(), "manage_channels missing"),
    ):
        channel, was_created = await ensure_setup_channel(guild)

    assert channel is None
    assert was_created is False


@pytest.mark.asyncio
async def test_ensure_setup_channel_handles_http_error_gracefully():
    guild = _make_guild()

    with patch(
        "services.setup_channel.ensure_channel",
        new_callable=AsyncMock,
        side_effect=discord.HTTPException(MagicMock(), "boom"),
    ):
        channel, was_created = await ensure_setup_channel(guild)

    assert channel is None
    assert was_created is False


@pytest.mark.asyncio
async def test_ensure_setup_channel_returns_none_when_helper_yields_non_text():
    """If ``ensure_channel`` somehow returns a voice/category we refuse."""
    guild = _make_guild()
    bad = MagicMock(spec=discord.VoiceChannel)

    with patch(
        "services.setup_channel.ensure_channel",
        new_callable=AsyncMock,
        return_value=bad,
    ):
        channel, was_created = await ensure_setup_channel(guild)

    assert channel is None
    assert was_created is False


@pytest.mark.asyncio
async def test_ensure_setup_channel_passes_private_overwrites():
    """The ``overwrites`` dict denies @everyone view and grants the bot."""
    guild = _make_guild()
    created = _make_text_channel(7000)

    with patch(
        "services.setup_channel.ensure_channel",
        new_callable=AsyncMock,
        return_value=created,
    ) as ensure_mock:
        await ensure_setup_channel(guild)

    overwrites = ensure_mock.await_args.kwargs["overwrites"]
    # @everyone (default_role) must be present with view denied
    assert guild.default_role in overwrites
    default_overwrite = overwrites[guild.default_role]
    assert default_overwrite.view_channel is False
    # Bot must be granted access
    assert guild.me in overwrites
    # Owner must be granted access when present
    assert guild.owner in overwrites
