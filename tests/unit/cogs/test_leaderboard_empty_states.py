"""Empty-state behaviour for the leaderboard panel (S4).

Per the user-centered UX rules in the mother-hub map (rule #5: Empty
states), an empty panel must explain what the feature does and what
the next step is — not just say "No data yet!".

These tests stub the DB layer to return no rows for each category and
verify the embed description contains a concrete next-step hint (e.g.
``!mine``, ``!daily``).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from cogs import leaderboard_cog


def _guild() -> MagicMock:
    guild = MagicMock(spec=discord.Guild)
    guild.id = 999
    return guild


def _channel() -> MagicMock:
    return MagicMock(spec=discord.abc.GuildChannel)


# ---------------------------------------------------------------------------
# Per-category empty-state next-step hint
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_xp_leaderboard_empty_hints_chat_to_earn_xp():
    with patch.object(
        leaderboard_cog.db,
        "fetchall",
        new_callable=AsyncMock,
        return_value=[],
    ):
        embed = await leaderboard_cog._build_embed("xp", _guild(), _channel())
    assert "Chat" in (embed.description or "")
    assert "rank" in (embed.description or "").lower()


@pytest.mark.asyncio
async def test_coins_leaderboard_empty_hints_daily_and_work():
    with patch.object(
        leaderboard_cog.db,
        "fetchall",
        new_callable=AsyncMock,
        return_value=[],
    ):
        embed = await leaderboard_cog._build_embed("coins", _guild(), _channel())
    assert "!daily" in (embed.description or "")
    assert "!work" in (embed.description or "")


@pytest.mark.asyncio
async def test_mining_leaderboard_empty_hints_mine_command():
    with patch.object(
        leaderboard_cog.db,
        "get_all_mining_totals",
        new_callable=AsyncMock,
        return_value=[],
    ):
        embed = await leaderboard_cog._build_embed("mining", _guild(), _channel())
    assert "!mine" in (embed.description or "")


@pytest.mark.asyncio
async def test_deathmatch_leaderboard_empty_hints_start_a_match():
    with patch.object(
        leaderboard_cog.db,
        "get_deathmatch_leaderboard",
        new_callable=AsyncMock,
        return_value=[],
    ):
        embed = await leaderboard_cog._build_embed(
            "deathmatch",
            _guild(),
            _channel(),
        )
    assert "!deathmatch" in (embed.description or "")


@pytest.mark.asyncio
async def test_rps_leaderboard_empty_hints_challenge_someone():
    with patch.object(
        leaderboard_cog.db,
        "rps_get_leaderboard",
        new_callable=AsyncMock,
        return_value=[],
    ):
        embed = await leaderboard_cog._build_embed("rps", _guild(), _channel())
    assert "!rps" in (embed.description or "")


@pytest.mark.asyncio
async def test_counting_leaderboard_empty_hints_count_in_channel():
    with patch.object(
        leaderboard_cog.db,
        "get_counting_state",
        new_callable=AsyncMock,
        return_value={"channels": {}},
    ):
        embed = await leaderboard_cog._build_embed(
            "counting",
            _guild(),
            _channel(),
        )
    # No "No data yet!" — must point at the counting channel.
    desc = embed.description or ""
    assert "No data yet!" not in desc
    assert "count" in desc.lower()
