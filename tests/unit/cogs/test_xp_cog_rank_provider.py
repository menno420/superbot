"""Unit tests for the non-XP provider rank card (`!rank <category>`).

Pins the H3 extension: a category rank (mining / deathmatch / …) renders as a
themed image card on the provider's own ``card_theme``, with the embed pointed
at the attachment; an unranked member or a Pillow-less host falls back to the
plain embed.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from cogs import xp_cog


def _member() -> MagicMock:
    member = MagicMock(spec=discord.Member)
    member.id = 7
    member.display_name = "AstroFox"
    avatar = MagicMock()
    avatar.url = "https://cdn.example/avatar.png"
    member.display_avatar = avatar
    return member


def _guild() -> MagicMock:
    guild = MagicMock(spec=discord.Guild)
    guild.id = 42
    guild.name = "Demo Server"
    return guild


def _provider(rank, rendered) -> MagicMock:
    provider = MagicMock()
    provider.display_title = "⛏️ Mining Leaderboard"
    provider.select_label = "Mining"
    provider.empty_hint = "No mining records yet."
    provider.card_theme = "abyss"
    provider.member_rank = AsyncMock(return_value=(rank, rendered))
    return provider


@pytest.mark.asyncio
async def test_ranked_member_gets_themed_image_card():
    provider = _provider(3, "1,200 blocks")
    with patch.object(
        xp_cog, "render_rank_card", return_value=b"\x89PNG\r\n\x1a\nfake"
    ) as render:
        embed, card = await xp_cog._build_rank_provider_response(
            provider, _member(), _guild()
        )

    assert isinstance(card, discord.File)
    assert embed.image.url == f"attachment://{xp_cog.RANK_CARD_FILENAME}"
    # The card rides the provider's own skin and labels the value panel.
    _, kwargs = render.call_args
    assert kwargs["theme"] == "abyss"
    assert ("Mining", "1,200 blocks") in kwargs["stats"]
    assert ("Rank", "#3") in kwargs["stats"]


@pytest.mark.asyncio
async def test_unranked_member_stays_plain_embed_with_hint():
    provider = _provider(None, None)
    with patch.object(xp_cog, "render_rank_card") as render:
        embed, card = await xp_cog._build_rank_provider_response(
            provider, _member(), _guild()
        )

    assert card is None
    assert embed.description == "No mining records yet."
    render.assert_not_called()  # no render attempt for an empty state


@pytest.mark.asyncio
async def test_pillow_unavailable_falls_back_to_embed_only():
    provider = _provider(3, "1,200 blocks")
    with patch.object(xp_cog, "render_rank_card", return_value=None):
        embed, card = await xp_cog._build_rank_provider_response(
            provider, _member(), _guild()
        )

    assert card is None
    assert embed.image.url is None
    # The numeric fields still render in the fallback embed.
    assert [f.name for f in embed.fields] == ["Rank", "Value"]
