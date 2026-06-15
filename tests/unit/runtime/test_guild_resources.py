"""Tests for core.runtime.guild_resources (Phase D extraction).

The resolvers are pure-read primitives: they wrap ``guild.get_channel`` /
``guild.get_role`` / ``guild.get_member`` plus the settings-channel
binding pattern.  Tests verify:

- ID-preferred resolution (id wins over name when both supplied)
- name-with-kind/category filtering
- malformed input (None, non-numeric, missing-from-cache) returns None
- ``resolve_members`` batch behavior (no N+1)
- ``member_display`` fallback formatting
- ``resolve_settings_channel`` reads via ``utils.db.get_setting``
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.runtime import guild_resources

# ---------------------------------------------------------------------------
# Helpers — build minimal mock guilds without spinning up discord.py state
# ---------------------------------------------------------------------------


def _make_channel(channel_id: int, name: str, *, category_id: int | None = None):
    ch = SimpleNamespace(id=channel_id, name=name, category_id=category_id)
    return ch


def _make_role(role_id: int, name: str):
    return SimpleNamespace(id=role_id, name=name)


def _make_member(member_id: int, display_name: str):
    return SimpleNamespace(id=member_id, display_name=display_name)


def _make_guild(
    *,
    text_channels=(),
    voice_channels=(),
    categories=(),
    roles=(),
    members_by_id=None,
):
    guild = MagicMock()
    guild.id = 1
    guild.text_channels = list(text_channels)
    guild.voice_channels = list(voice_channels)
    guild.categories = list(categories)
    guild.channels = (
        list(text_channels) + list(voice_channels) + list(categories)
    )
    guild.roles = list(roles)

    id_to_channel = {ch.id: ch for ch in guild.channels}
    guild.get_channel = lambda cid: id_to_channel.get(cid)

    id_to_role = {r.id: r for r in guild.roles}
    guild.get_role = lambda rid: id_to_role.get(rid)

    members = members_by_id or {}
    guild.get_member = lambda mid: members.get(mid)

    return guild


# ---------------------------------------------------------------------------
# resolve_channel
# ---------------------------------------------------------------------------


class TestResolveChannel:
    def test_by_id_hits_cache(self):
        ch = _make_channel(100, "general")
        guild = _make_guild(text_channels=[ch])
        assert guild_resources.resolve_channel(guild, channel_id=100) is ch

    def test_by_id_accepts_string(self):
        ch = _make_channel(100, "general")
        guild = _make_guild(text_channels=[ch])
        assert guild_resources.resolve_channel(guild, channel_id="100") is ch

    def test_by_id_invalid_falls_through_to_name(self):
        ch = _make_channel(100, "general")
        guild = _make_guild(text_channels=[ch])
        # invalid id, but name matches
        assert (
            guild_resources.resolve_channel(
                guild, channel_id="not-an-int", name="general"
            )
            is ch
        )

    def test_by_id_invalid_no_name_returns_none(self):
        guild = _make_guild()
        assert (
            guild_resources.resolve_channel(guild, channel_id="not-an-int") is None
        )

    def test_by_id_missing_falls_through_to_name(self):
        ch = _make_channel(100, "general")
        guild = _make_guild(text_channels=[ch])
        # id 999 not in cache; fall back to name
        assert (
            guild_resources.resolve_channel(guild, channel_id=999, name="general")
            is ch
        )

    def test_by_name_text_only_default(self):
        text_ch = _make_channel(100, "general")
        voice_ch = _make_channel(200, "general")  # same name, voice channel
        guild = _make_guild(text_channels=[text_ch], voice_channels=[voice_ch])
        # default kind=text → returns text channel, not voice
        result = guild_resources.resolve_channel(guild, name="general")
        assert result is text_ch

    def test_by_name_voice_kind(self):
        voice_ch = _make_channel(200, "general")
        guild = _make_guild(voice_channels=[voice_ch])
        result = guild_resources.resolve_channel(guild, name="general", kind="voice")
        assert result is voice_ch

    def test_by_name_any_kind_picks_first(self):
        text_ch = _make_channel(100, "general")
        voice_ch = _make_channel(200, "general")
        guild = _make_guild(text_channels=[text_ch], voice_channels=[voice_ch])
        result = guild_resources.resolve_channel(guild, name="general", kind="any")
        # iteration order = text_channels + voice_channels per _make_guild
        assert result is text_ch

    def test_by_name_with_category_filter(self):
        cat_a = _make_channel(50, "Bot")
        cat_b = _make_channel(60, "Other")
        ch_in_a = _make_channel(100, "log", category_id=50)
        ch_in_b = _make_channel(101, "log", category_id=60)
        guild = _make_guild(
            text_channels=[ch_in_a, ch_in_b], categories=[cat_a, cat_b]
        )
        result = guild_resources.resolve_channel(
            guild, name="log", category="Bot"
        )
        assert result is ch_in_a

    def test_by_name_category_obj_filter(self):
        cat = SimpleNamespace(id=50, name="Bot")
        ch = _make_channel(100, "log", category_id=50)
        guild = _make_guild(text_channels=[ch], categories=[cat])
        result = guild_resources.resolve_channel(
            guild, name="log", category=cat
        )
        assert result is ch

    def test_by_name_missing_returns_none(self):
        guild = _make_guild()
        assert guild_resources.resolve_channel(guild, name="missing") is None

    def test_no_args_returns_none(self):
        guild = _make_guild()
        assert guild_resources.resolve_channel(guild) is None


# ---------------------------------------------------------------------------
# ensure_channel
# ---------------------------------------------------------------------------


class TestEnsureChannel:
    @pytest.mark.asyncio
    async def test_returns_existing(self):
        ch = _make_channel(100, "general")
        guild = _make_guild(text_channels=[ch])
        guild.create_text_channel = AsyncMock()
        result = await guild_resources.ensure_channel(guild, "general")
        assert result is ch
        guild.create_text_channel.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_creates_when_absent(self):
        guild = _make_guild()
        created = _make_channel(999, "new-channel")
        guild.create_text_channel = AsyncMock(return_value=created)
        result = await guild_resources.ensure_channel(guild, "new-channel")
        assert result is created
        guild.create_text_channel.assert_awaited_once_with(
            "new-channel", category=None, overwrites={}
        )

    @pytest.mark.asyncio
    async def test_creates_voice(self):
        guild = _make_guild()
        created = SimpleNamespace(id=999, name="vc")
        guild.create_voice_channel = AsyncMock(return_value=created)
        result = await guild_resources.ensure_channel(guild, "vc", kind="voice")
        assert result is created
        guild.create_voice_channel.assert_awaited_once()


# ---------------------------------------------------------------------------
# resolve_role
# ---------------------------------------------------------------------------


class TestResolveRole:
    def test_by_id(self):
        role = _make_role(100, "Member")
        guild = _make_guild(roles=[role])
        assert guild_resources.resolve_role(guild, role_id=100) is role

    def test_by_id_string(self):
        role = _make_role(100, "Member")
        guild = _make_guild(roles=[role])
        assert guild_resources.resolve_role(guild, role_id="100") is role

    def test_by_name_exact(self):
        role = _make_role(100, "Member")
        guild = _make_guild(roles=[role])
        assert guild_resources.resolve_role(guild, name="Member") is role

    def test_by_name_case_sensitive(self):
        role = _make_role(100, "Member")
        guild = _make_guild(roles=[role])
        assert guild_resources.resolve_role(guild, name="member") is None

    def test_by_id_falls_through_to_name(self):
        role = _make_role(100, "Member")
        guild = _make_guild(roles=[role])
        assert (
            guild_resources.resolve_role(guild, role_id=999, name="Member")
            is role
        )

    def test_no_args_returns_none(self):
        guild = _make_guild()
        assert guild_resources.resolve_role(guild) is None

    def test_missing_returns_none(self):
        guild = _make_guild()
        assert guild_resources.resolve_role(guild, role_id=100) is None


# ---------------------------------------------------------------------------
# resolve_member / resolve_members / member_display
# ---------------------------------------------------------------------------


class TestResolveMember:
    def test_found(self):
        m = _make_member(42, "Alice")
        guild = _make_guild(members_by_id={42: m})
        assert guild_resources.resolve_member(guild, 42) is m

    def test_str_id(self):
        m = _make_member(42, "Alice")
        guild = _make_guild(members_by_id={42: m})
        assert guild_resources.resolve_member(guild, "42") is m

    def test_missing(self):
        guild = _make_guild()
        assert guild_resources.resolve_member(guild, 42) is None

    def test_invalid_id(self):
        guild = _make_guild()
        assert guild_resources.resolve_member(guild, "abc") is None
        assert guild_resources.resolve_member(guild, None) is None  # type: ignore[arg-type]


class TestResolveMemberByName:
    def test_found(self):
        m = _make_member(42, "Alice")
        guild = _make_guild()
        guild.get_member_named = lambda name: m if name == "Alice" else None
        assert guild_resources.resolve_member_by_name(guild, "Alice") is m

    def test_missing(self):
        guild = _make_guild()
        guild.get_member_named = lambda name: None
        assert guild_resources.resolve_member_by_name(guild, "Bob") is None

    def test_empty_string_short_circuits(self):
        guild = _make_guild()
        guild.get_member_named = MagicMock()
        assert guild_resources.resolve_member_by_name(guild, "") is None
        guild.get_member_named.assert_not_called()


class TestResolveMembers:
    def test_partial_batch(self):
        m1 = _make_member(1, "Alice")
        m3 = _make_member(3, "Carol")
        guild = _make_guild(members_by_id={1: m1, 3: m3})
        result = guild_resources.resolve_members(guild, [1, 2, 3])
        assert result == {1: m1, 3: m3}

    def test_empty(self):
        guild = _make_guild()
        assert guild_resources.resolve_members(guild, []) == {}

    def test_drops_invalid_ids(self):
        m = _make_member(1, "Alice")
        guild = _make_guild(members_by_id={1: m})
        result = guild_resources.resolve_members(guild, [1, "abc", None, 999])
        assert result == {1: m}


class TestMemberDisplay:
    def test_cached_returns_display_name(self):
        m = _make_member(42, "Alice")
        guild = _make_guild(members_by_id={42: m})
        assert guild_resources.member_display(guild, 42) == "Alice"

    def test_missing_returns_mention(self):
        guild = _make_guild()
        assert guild_resources.member_display(guild, 42) == "<@42>"

    def test_str_id(self):
        m = _make_member(42, "Alice")
        guild = _make_guild(members_by_id={42: m})
        assert guild_resources.member_display(guild, "42") == "Alice"

    def test_invalid_id_returns_raw_mention(self):
        guild = _make_guild()
        assert guild_resources.member_display(guild, "abc") == "<@abc>"


# ---------------------------------------------------------------------------
# resolve_settings_channel
# ---------------------------------------------------------------------------


class TestResolveSettingsChannel:
    @pytest.mark.asyncio
    async def test_unset_setting_returns_none(self):
        guild = _make_guild()
        with patch(
            "utils.db.get_setting",
            new_callable=AsyncMock,
            return_value="",
        ) as m:
            result = await guild_resources.resolve_settings_channel(
                guild, "log_channel"
            )
            assert result is None
            m.assert_awaited_once_with(guild.id, "log_channel", "")

    @pytest.mark.asyncio
    async def test_resolves_channel_by_id(self):
        ch = _make_channel(123, "logs")
        guild = _make_guild(text_channels=[ch])
        with patch(
            "utils.db.get_setting",
            new_callable=AsyncMock,
            return_value="123",
        ):
            result = await guild_resources.resolve_settings_channel(
                guild, "log_channel"
            )
            assert result is ch

    @pytest.mark.asyncio
    async def test_setting_points_at_missing_channel(self):
        guild = _make_guild()  # cache empty
        with patch(
            "utils.db.get_setting",
            new_callable=AsyncMock,
            return_value="999",
        ):
            result = await guild_resources.resolve_settings_channel(
                guild, "log_channel"
            )
            assert result is None
