"""Tests for ``services.cleanup_profiles`` — named cleanup bundles."""

from __future__ import annotations

from unittest.mock import MagicMock

import discord
import pytest

from services.cleanup_profiles import (
    PROFILES,
    apply_profile,
    get_profile,
    known_profile_slugs,
)


def _text_channel(name: str, channel_id: int = 1) -> discord.TextChannel:
    ch = MagicMock(spec=discord.TextChannel)
    ch.id = channel_id
    ch.name = name
    return ch


def _guild(*, text_channels=(), guild_id: int = 1) -> discord.Guild:
    g = MagicMock(spec=discord.Guild)
    g.id = guild_id
    g.name = "Test Guild"
    g.text_channels = list(text_channels)
    return g


# ---------------------------------------------------------------------------
# Catalogue / lookup
# ---------------------------------------------------------------------------


def test_documented_profile_slugs():
    assert known_profile_slugs() == {
        "off",
        "light",
        "standard",
        "strict",
        "silent_bot",
        "moderation_safe",
    }


@pytest.mark.parametrize("slug", sorted(known_profile_slugs()))
def test_get_profile_returns_match(slug):
    profile = get_profile(slug)
    assert profile is not None
    assert profile.slug == slug
    assert profile.display_name
    assert profile.description


def test_get_profile_returns_none_for_unknown_slug():
    assert get_profile("does-not-exist") is None


def test_apply_profile_raises_on_unknown_slug():
    with pytest.raises(KeyError):
        apply_profile("does-not-exist", _guild())


# ---------------------------------------------------------------------------
# Uniform profiles (off / light / standard / strict)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("slug", "expected_level"),
    [
        ("off", "Off"),
        ("light", "Light"),
        ("standard", "Standard"),
        ("strict", "Strict"),
    ],
)
def test_uniform_profile_emits_single_guild_op(slug, expected_level):
    guild = _guild(text_channels=[_text_channel("random"), _text_channel("bot-cmds")])
    ops = apply_profile(slug, guild)
    assert len(ops) == 1
    op = ops[0]
    assert op.kind == "set_cleanup_policy"
    assert op.subsystem == "cleanup"
    assert op.target_kind == "guild"
    assert op.target_id == guild.id
    assert op.value == expected_level


# ---------------------------------------------------------------------------
# Silent-bot profile
# ---------------------------------------------------------------------------


def test_silent_bot_emits_light_guild_default_plus_strict_on_bot_channels():
    bot_ch = _text_channel("bot-commands", channel_id=100)
    spam_ch = _text_channel("bot-spam", channel_id=200)
    general_ch = _text_channel("general", channel_id=300)
    guild = _guild(text_channels=[bot_ch, spam_ch, general_ch])

    ops = apply_profile("silent_bot", guild)
    # Guild-level Light first.
    assert ops[0].target_kind == "guild"
    assert ops[0].value == "Light"
    # Bot/cmd channels get Strict.
    channel_ops = [op for op in ops[1:] if op.target_kind == "channel"]
    assert len(channel_ops) == 2
    assert {op.target_id for op in channel_ops} == {100, 200}
    for op in channel_ops:
        assert op.value == "Strict"


def test_silent_bot_with_no_bot_channels_falls_back_to_guild_light_only():
    guild = _guild(text_channels=[_text_channel("general"), _text_channel("random")])
    ops = apply_profile("silent_bot", guild)
    assert len(ops) == 1
    assert ops[0].value == "Light"


# ---------------------------------------------------------------------------
# Moderation-safe profile
# ---------------------------------------------------------------------------


def test_moderation_safe_emits_standard_guild_plus_off_on_mod_channels():
    mod_ch = _text_channel("mod-chat", channel_id=400)
    staff_ch = _text_channel("staff", channel_id=401)
    admin_ch = _text_channel("admin", channel_id=402)
    general_ch = _text_channel("general", channel_id=500)
    guild = _guild(text_channels=[mod_ch, staff_ch, admin_ch, general_ch])

    ops = apply_profile("moderation_safe", guild)
    assert ops[0].target_kind == "guild"
    assert ops[0].value == "Standard"
    channel_ops = [op for op in ops[1:] if op.target_kind == "channel"]
    assert {op.target_id for op in channel_ops} == {400, 401, 402}
    for op in channel_ops:
        assert op.value == "Off"


def test_moderation_safe_skips_regular_channels():
    guild = _guild(text_channels=[_text_channel("general"), _text_channel("random")])
    ops = apply_profile("moderation_safe", guild)
    assert len(ops) == 1
    assert ops[0].value == "Standard"


# ---------------------------------------------------------------------------
# Op shape contract — every profile produces only ``set_cleanup_policy`` ops.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("slug", sorted(known_profile_slugs()))
def test_every_profile_only_stages_cleanup_policy_ops(slug):
    bot_ch = _text_channel("bot-spam", channel_id=100)
    mod_ch = _text_channel("mod-log", channel_id=200)
    guild = _guild(text_channels=[bot_ch, mod_ch])
    ops = apply_profile(slug, guild)
    assert ops  # every profile emits at least the guild default
    for op in ops:
        assert op.kind == "set_cleanup_policy"
        assert op.subsystem == "cleanup"
        assert op.target_kind in ("guild", "channel")


@pytest.mark.parametrize("slug", sorted(known_profile_slugs()))
def test_profiles_are_deterministic(slug):
    """Same guild + same channels → same op sequence."""
    bot_ch = _text_channel("bot-cmds", channel_id=100)
    mod_ch = _text_channel("mod-chat", channel_id=200)
    guild = _guild(text_channels=[bot_ch, mod_ch])
    a = apply_profile(slug, guild)
    b = apply_profile(slug, guild)
    assert [(op.target_kind, op.target_id, op.value) for op in a] == [
        (op.target_kind, op.target_id, op.value) for op in b
    ]
