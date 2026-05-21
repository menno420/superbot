"""Tests for the command_routing resolver + writer.

Covers the scope-chain walk (channel → category → guild → default-true)
and the writer's pass-through to the DB primitives.  The DB primitives
themselves are mocked so the tests stay asyncpg-free.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from services import command_routing

# ---------------------------------------------------------------------------
# is_cog_enabled — scope chain
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_is_cog_enabled_returns_true_when_no_policy_rows():
    """A fresh guild with no policy rows defaults to enabled for every cog."""
    with patch(
        "services.command_routing.db.get_one",
        new=AsyncMock(return_value=None),
    ) as get_mock:
        result = await command_routing.is_cog_enabled(
            guild_id=1,
            cog_name="games",
            channel_id=999,
            category_id=42,
        )
    assert result is True
    # Three lookups: channel, category, guild.
    assert get_mock.await_count == 3


@pytest.mark.asyncio
async def test_is_cog_enabled_returns_channel_override_when_present():
    """Channel scope wins over category and guild."""
    async def fake_get(guild_id, scope, scope_id, cog):
        if scope == "channel" and scope_id == 999:
            return {"enabled": False}
        return None

    with patch("services.command_routing.db.get_one", new=fake_get):
        result = await command_routing.is_cog_enabled(
            guild_id=1,
            cog_name="games",
            channel_id=999,
            category_id=42,
        )
    assert result is False


@pytest.mark.asyncio
async def test_is_cog_enabled_walks_to_category_when_channel_unset():
    async def fake_get(guild_id, scope, scope_id, cog):
        if scope == "channel":
            return None
        if scope == "category" and scope_id == 42:
            return {"enabled": True}
        return None

    with patch("services.command_routing.db.get_one", new=fake_get):
        result = await command_routing.is_cog_enabled(
            guild_id=1,
            cog_name="games",
            channel_id=999,
            category_id=42,
        )
    assert result is True


@pytest.mark.asyncio
async def test_is_cog_enabled_walks_to_guild_when_channel_and_category_unset():
    async def fake_get(guild_id, scope, scope_id, cog):
        if scope == "guild" and scope_id is None:
            return {"enabled": False}
        return None

    with patch("services.command_routing.db.get_one", new=fake_get):
        result = await command_routing.is_cog_enabled(
            guild_id=1,
            cog_name="games",
            channel_id=999,
            category_id=42,
        )
    assert result is False


@pytest.mark.asyncio
async def test_is_cog_enabled_skips_channel_lookup_when_channel_id_none():
    """DM-like context (no channel) skips the channel-scope query."""
    with patch(
        "services.command_routing.db.get_one",
        new=AsyncMock(return_value=None),
    ) as get_mock:
        await command_routing.is_cog_enabled(
            guild_id=1,
            cog_name="games",
            channel_id=None,
            category_id=42,
        )
    # Two lookups: category, guild.
    assert get_mock.await_count == 2


@pytest.mark.asyncio
async def test_is_cog_enabled_skips_category_lookup_when_category_id_none():
    with patch(
        "services.command_routing.db.get_one",
        new=AsyncMock(return_value=None),
    ) as get_mock:
        await command_routing.is_cog_enabled(
            guild_id=1,
            cog_name="games",
            channel_id=999,
            category_id=None,
        )
    # Two lookups: channel, guild.
    assert get_mock.await_count == 2


@pytest.mark.asyncio
async def test_is_cog_enabled_default_true_when_only_guild_lookup_runs():
    """No channel + no category + no guild policy row → still enabled."""
    with patch(
        "services.command_routing.db.get_one",
        new=AsyncMock(return_value=None),
    ):
        result = await command_routing.is_cog_enabled(
            guild_id=1,
            cog_name="games",
            channel_id=None,
            category_id=None,
        )
    assert result is True


# ---------------------------------------------------------------------------
# set_policy — passthrough
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_policy_passes_through_to_db_layer():
    with patch(
        "services.command_routing.db.set_one",
        new_callable=AsyncMock,
    ) as set_mock:
        await command_routing.set_policy(
            guild_id=1,
            scope_type="category",
            scope_id=42,
            cog_name="games",
            enabled=False,
            actor_id=99,
        )
    set_mock.assert_awaited_once_with(
        guild_id=1,
        scope_type="category",
        scope_id=42,
        cog_name="games",
        enabled=False,
        actor_id=99,
    )


# ---------------------------------------------------------------------------
# list_for_guild — passthrough
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_for_guild_passes_through_to_db_layer():
    rows = [{"scope_type": "guild", "cog_name": "games", "enabled": True}]
    with patch(
        "services.command_routing.db.list_for_guild",
        new=AsyncMock(return_value=rows),
    ):
        result = await command_routing.list_for_guild(1)
    assert result == rows
