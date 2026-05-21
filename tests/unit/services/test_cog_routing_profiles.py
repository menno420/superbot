"""Tests for ``services.cog_routing_profiles`` — named routing bundles."""

from __future__ import annotations

from unittest.mock import MagicMock

import discord
import pytest

from services.cog_routing_profiles import (
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
# Catalogue
# ---------------------------------------------------------------------------


def test_documented_profile_slugs():
    assert known_profile_slugs() == {
        "games_in_game_channels",
        "economy_in_economy_channels",
        "moderation_to_staff",
        "recommended_by_name",
    }


@pytest.mark.parametrize("slug", sorted(known_profile_slugs()))
def test_get_profile_returns_match(slug):
    profile = get_profile(slug)
    assert profile is not None
    assert profile.slug == slug


def test_get_profile_returns_none_for_unknown():
    assert get_profile("does-not-exist") is None


def test_apply_profile_raises_on_unknown_slug():
    with pytest.raises(KeyError):
        apply_profile("does-not-exist", _guild())


# ---------------------------------------------------------------------------
# games_in_game_channels
# ---------------------------------------------------------------------------


def test_games_in_game_channels_disables_at_guild_and_enables_on_detected():
    games_ch = _text_channel("games", channel_id=100)
    bj_ch = _text_channel("blackjack", channel_id=101)
    general_ch = _text_channel("general", channel_id=200)
    guild = _guild(text_channels=[games_ch, bj_ch, general_ch])

    ops = apply_profile("games_in_game_channels", guild)
    # First op: guild-scope disable.
    assert ops[0].target_kind == "guild"
    assert ops[0].value == "games"
    assert ops[0].metadata["enabled"] == "false"
    # Per-channel enables on detected game channels only.
    channel_ops = [op for op in ops[1:] if op.target_kind == "channel"]
    assert {op.target_id for op in channel_ops} == {100, 101}
    for op in channel_ops:
        assert op.metadata["enabled"] == "true"
        assert op.value == "games"


def test_games_in_game_channels_falls_back_when_no_game_channels():
    guild = _guild(text_channels=[_text_channel("general"), _text_channel("random")])
    ops = apply_profile("games_in_game_channels", guild)
    # Just the guild-scope disable; nothing to re-enable.
    assert len(ops) == 1
    assert ops[0].target_kind == "guild"
    assert ops[0].metadata["enabled"] == "false"


# ---------------------------------------------------------------------------
# economy_in_economy_channels
# ---------------------------------------------------------------------------


def test_economy_in_economy_channels_picks_game_and_mining_channels():
    games_ch = _text_channel("games", channel_id=100)
    mining_ch = _text_channel("mining", channel_id=101)
    random_ch = _text_channel("random", channel_id=200)
    guild = _guild(text_channels=[games_ch, mining_ch, random_ch])

    ops = apply_profile("economy_in_economy_channels", guild)
    assert ops[0].target_kind == "guild"
    assert ops[0].value == "economy"
    channel_ops = [op for op in ops[1:] if op.target_kind == "channel"]
    assert {op.target_id for op in channel_ops} == {100, 101}


def test_economy_profile_deduplicates_channels_matching_multiple_tags():
    """A channel named ``game-mining`` matches both ``likely_game`` and
    ``likely_mining``; it should appear only once in the staged ops."""
    multi_ch = _text_channel("game-mining", channel_id=100)
    guild = _guild(text_channels=[multi_ch])
    ops = apply_profile("economy_in_economy_channels", guild)
    channel_ops = [op for op in ops if op.target_kind == "channel"]
    assert len(channel_ops) == 1


# ---------------------------------------------------------------------------
# moderation_to_staff
# ---------------------------------------------------------------------------


def test_moderation_to_staff_re_enables_on_mod_admin_channels():
    mod_ch = _text_channel("mod-chat", channel_id=300)
    admin_ch = _text_channel("admin", channel_id=301)
    log_ch = _text_channel("mod-log", channel_id=302)
    random_ch = _text_channel("general", channel_id=400)
    guild = _guild(text_channels=[mod_ch, admin_ch, log_ch, random_ch])

    ops = apply_profile("moderation_to_staff", guild)
    assert ops[0].target_kind == "guild"
    assert ops[0].value == "moderation"
    assert ops[0].metadata["enabled"] == "false"
    channel_ops = [op for op in ops[1:] if op.target_kind == "channel"]
    assert {op.target_id for op in channel_ops} == {300, 301, 302}


# ---------------------------------------------------------------------------
# Op shape contract
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("slug", sorted(known_profile_slugs()))
def test_every_profile_only_stages_set_cog_routing(slug):
    games_ch = _text_channel("games", channel_id=100)
    mod_ch = _text_channel("mod-chat", channel_id=200)
    guild = _guild(text_channels=[games_ch, mod_ch])
    ops = apply_profile(slug, guild)
    assert ops
    for op in ops:
        assert op.kind == "set_cog_routing"
        assert op.subsystem == "cog_routing"
        assert op.target_kind in ("guild", "channel")
        # Every op declares an enabled flag for the dispatcher.
        assert (op.metadata or {}).get("enabled") in ("true", "false")


@pytest.mark.parametrize("slug", sorted(known_profile_slugs()))
def test_profiles_are_deterministic(slug):
    games_ch = _text_channel("games", channel_id=100)
    mod_ch = _text_channel("mod-chat", channel_id=200)
    guild = _guild(text_channels=[games_ch, mod_ch])
    a = apply_profile(slug, guild)
    b = apply_profile(slug, guild)
    assert [(op.target_kind, op.target_id, op.value, op.metadata) for op in a] == [
        (op.target_kind, op.target_id, op.value, op.metadata) for op in b
    ]


# ---------------------------------------------------------------------------
# recommended_by_name (compound)
# ---------------------------------------------------------------------------


def test_recommended_by_name_applies_all_three_per_cog_profiles():
    """The compound profile produces the union of games + economy +
    moderation routing ops in one builder invocation."""
    games_ch = _text_channel("games", channel_id=100)
    mining_ch = _text_channel("mining", channel_id=101)
    mod_ch = _text_channel("mod-chat", channel_id=200)
    guild = _guild(text_channels=[games_ch, mining_ch, mod_ch])

    ops = apply_profile("recommended_by_name", guild)
    cogs_touched = {op.value for op in ops}
    assert cogs_touched == {"games", "economy", "moderation"}
    # Three guild-scope disable ops (one per cog).
    guild_disables = [
        op
        for op in ops
        if op.target_kind == "guild" and op.metadata["enabled"] == "false"
    ]
    assert len(guild_disables) == 3
    # Per-channel enables for the matching channels per cog.
    channel_enables = [
        op
        for op in ops
        if op.target_kind == "channel" and op.metadata["enabled"] == "true"
    ]
    assert channel_enables  # at least one


def test_recommended_by_name_with_no_matching_channels_only_disables():
    """With no matching channels in the guild, the profile produces
    three guild-scope disable ops and nothing else."""
    guild = _guild(text_channels=[_text_channel("general")])
    ops = apply_profile("recommended_by_name", guild)
    assert len(ops) == 3
    for op in ops:
        assert op.target_kind == "guild"
        assert op.metadata["enabled"] == "false"
