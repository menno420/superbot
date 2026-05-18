"""Phase 2a unit tests — channel_service operations."""

from __future__ import annotations

from unittest.mock import MagicMock

import discord
from tests.unit.resources.test_discovery import (
    _mk_category,
    _mk_guild,
    _mk_text_channel,
    _mk_voice_channel,
)

from core.resources import channel_service
from core.resources.types import ChannelResource


def test_list_text_channels_filters_voice_out():
    text = _mk_text_channel(1, "general")
    voice = _mk_voice_channel(2, "Lounge")
    guild = _mk_guild(channels=[text, voice])
    result = channel_service.list_text_channels(guild)
    assert len(result) == 1
    assert result[0].id == 1


def test_list_voice_channels_filters_text_out():
    text = _mk_text_channel(1, "general")
    voice = _mk_voice_channel(2, "Lounge")
    guild = _mk_guild(channels=[text, voice])
    result = channel_service.list_voice_channels(guild)
    assert len(result) == 1
    assert result[0].id == 2


def test_filter_channels_applies_predicate():
    a = _mk_text_channel(1, "general")
    b = _mk_text_channel(2, "spam")
    guild = _mk_guild(channels=[a, b])
    result = channel_service.filter_channels(
        guild,
        lambda r: r.name.startswith("g"),
    )
    assert [r.id for r in result] == [1]


def test_get_channel_present():
    text = _mk_text_channel(42, "general")
    guild = _mk_guild(channels=[text])
    found = channel_service.get_channel(guild, 42)
    assert isinstance(found, ChannelResource)
    assert found.id == 42


def test_get_channel_missing():
    guild = _mk_guild()
    assert channel_service.get_channel(guild, 42) is None


def test_get_channel_rejects_category():
    cat = _mk_category(42, "Staff")
    guild = _mk_guild(categories=[cat])
    assert channel_service.get_channel(guild, 42) is None


def test_build_select_options_sorts_by_name_and_truncates():
    a = _mk_text_channel(1, "zebra")
    b = _mk_text_channel(2, "apple")
    voice = _mk_voice_channel(3, "Lounge")

    # Build a guild explicitly because the helper iterates guild.channels.
    guild = MagicMock(spec=discord.Guild)
    guild.channels = [a, b, voice]
    options = channel_service.build_select_options(guild)
    assert len(options) == 3
    # Sorted by name ascending.
    assert options[0].label == "Lounge"  # capital L sorts before lowercase
    assert options[1].label == "apple"
    assert options[2].label == "zebra"


def test_build_select_options_include_voice_false():
    text = _mk_text_channel(1, "general")
    voice = _mk_voice_channel(2, "Lounge")
    guild = MagicMock(spec=discord.Guild)
    guild.channels = [text, voice]
    options = channel_service.build_select_options(guild, include_voice=False)
    assert len(options) == 1
    assert options[0].label == "general"


def test_build_select_options_respects_limit():
    channels = [_mk_text_channel(i, f"ch{i:02d}") for i in range(30)]
    guild = MagicMock(spec=discord.Guild)
    guild.channels = channels
    options = channel_service.build_select_options(guild, limit=10)
    assert len(options) == 10
