"""Community Spotlight cog — embed builders + EventBus level-up feed."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cogs import community_spotlight_cog as csc


@pytest.fixture(autouse=True)
def _clear_levelup_feed():
    csc._levelup_feed.clear()
    yield
    csc._levelup_feed.clear()


def _make_guild(*, member_count: int | None = 42) -> MagicMock:
    guild = MagicMock()
    guild.id = 999
    guild.name = "Test Server"
    guild.member_count = member_count
    return guild


@pytest.mark.asyncio
async def test_main_embed_builds_with_unchunked_guild():
    """member_count is None until the guild is chunked — must not crash."""
    guild = _make_guild(member_count=None)
    with (
        patch.object(
            csc.db,
            "get_guild_xp_totals",
            new_callable=AsyncMock,
            return_value=(0, 0),
        ),
        patch.object(csc, "get_provider", return_value=None),
    ):
        embed = await csc._build_main_embed(guild)
    assert "Test Server" in embed.title
    overview = embed.fields[0].value
    assert "**0** members" in overview


@pytest.mark.asyncio
async def test_main_embed_uses_db_owner_for_totals():
    guild = _make_guild()
    with (
        patch.object(
            csc.db,
            "get_guild_xp_totals",
            new_callable=AsyncMock,
            return_value=(12345, 678),
        ) as mock_totals,
        patch.object(csc, "get_provider", return_value=None),
    ):
        embed = await csc._build_main_embed(guild)
    mock_totals.assert_awaited_once_with(999)
    overview = embed.fields[0].value
    assert "**12,345** XP" in overview
    assert "**678** coins" in overview


@pytest.mark.asyncio
async def test_level_up_feed_caps_at_max_entries():
    bot = MagicMock()
    bot.get_guild.return_value = None
    cog = csc.CommunitySpotlightCog(bot)
    for level in range(1, 8):
        await cog._on_level_up(guild_id=999, user_id=1, new_level=level)
    feed = csc._levelup_feed[999]
    assert len(feed) == csc._MAX_LEVELUP_ENTRIES
    assert "Level **7**" in feed[-1]
