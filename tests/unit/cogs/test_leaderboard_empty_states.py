"""Empty-state behaviour for the leaderboard panel (S4).

Per the user-centered UX rules in the mother-hub map (rule #5: Empty
states), an empty panel must explain what the feature does and what
the next step is — not just say "No data yet!".

PR G migrated the per-category branches into
:mod:`services.rank_providers`; these tests now exercise the shared
``_build_provider_embed`` renderer through each provider and verify
the empty-state description still carries a concrete next-step hint
(e.g. ``!mine``, ``!daily``).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from cogs import leaderboard_cog
from services.rank_providers import get_provider


def _guild() -> MagicMock:
    guild = MagicMock(spec=discord.Guild)
    guild.id = 999
    return guild


async def _empty_embed_for(provider_name: str) -> discord.Embed:
    provider = get_provider(provider_name)
    assert provider is not None
    return await leaderboard_cog._build_provider_embed(provider, _guild())


# ---------------------------------------------------------------------------
# Per-category empty-state next-step hint
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_xp_leaderboard_empty_hints_chat_to_earn_xp():
    with patch(
        "services.rank_providers.db.fetchall",
        new_callable=AsyncMock,
        return_value=[],
    ):
        embed = await _empty_embed_for("xp")
    assert "Chat" in (embed.description or "")
    assert "rank" in (embed.description or "").lower()


@pytest.mark.asyncio
async def test_coins_leaderboard_empty_hints_daily_and_work():
    with patch(
        "services.rank_providers.db.fetchall",
        new_callable=AsyncMock,
        return_value=[],
    ):
        embed = await _empty_embed_for("coins")
    assert "!daily" in (embed.description or "")
    assert "!work" in (embed.description or "")


@pytest.mark.asyncio
async def test_mining_leaderboard_empty_hints_mine_command():
    with patch(
        "services.rank_providers.db.get_all_mining_totals",
        new_callable=AsyncMock,
        return_value=[],
    ):
        embed = await _empty_embed_for("mining")
    assert "!mine" in (embed.description or "")


@pytest.mark.asyncio
async def test_deathmatch_leaderboard_empty_hints_start_a_match():
    with patch(
        "services.rank_providers.db.get_deathmatch_leaderboard",
        new_callable=AsyncMock,
        return_value=[],
    ):
        embed = await _empty_embed_for("deathmatch")
    assert "!deathmatch" in (embed.description or "")


@pytest.mark.asyncio
async def test_rps_leaderboard_empty_hints_challenge_someone():
    with patch(
        "services.rank_providers.db.rps_get_leaderboard",
        new_callable=AsyncMock,
        return_value=[],
    ):
        embed = await _empty_embed_for("rps")
    assert "!rps" in (embed.description or "")


@pytest.mark.asyncio
async def test_counting_leaderboard_empty_hints_count_in_channel():
    with patch(
        "services.rank_providers.db.get_counting_state",
        new_callable=AsyncMock,
        return_value={"channels": {}},
    ):
        embed = await _empty_embed_for("counting")
    # No "No data yet!" — must point at the counting channel.
    desc = embed.description or ""
    assert "No data yet!" not in desc
    assert "count" in desc.lower()
