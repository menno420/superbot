"""Unit tests for the rank-card data + image-response builders (xp_helpers).

Pins the H3 rank-card seam:

* ``build_rank_card_data`` fetches the XP row + ranks once and projects them.
* ``build_rank_response`` returns the embed plus an optional image card, with
  the embed image pointed at the attachment when the card renders, and a clean
  embed-only fallback when Pillow is unavailable.
* The embed produced from the fetched data is byte-identical to the historical
  ``_build_rank_embed`` field layout (no drift between embed and image).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from services import xp_helpers


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


def _patch_ranks(xp_rank, coin_rank):
    """Patch get_xp + the rank providers; returns the get_xp mock."""
    xp_provider = MagicMock()
    xp_provider.member_rank = AsyncMock(return_value=(xp_rank, "x"))
    coin_provider = MagicMock()
    coin_provider.member_rank = AsyncMock(return_value=(coin_rank, "c"))

    def _get_provider(name):
        return {"xp": xp_provider, "coins": coin_provider}.get(name)

    row = {"user_id": 7, "guild_id": 42, "xp": 150, "messages": 1337, "coins": 910}
    get_xp = AsyncMock(return_value=row)
    return get_xp, _get_provider


@pytest.mark.asyncio
async def test_build_rank_card_data_fetches_once_and_projects():
    get_xp, get_provider = _patch_ranks(3, 5)
    with (
        patch.object(xp_helpers.db, "get_xp", get_xp),
        patch(
            "services.rank_providers.get_provider",
            side_effect=get_provider,
        ),
    ):
        data = await xp_helpers.build_rank_card_data(_member(), _guild())

    get_xp.assert_awaited_once()  # single DB read
    assert data.display_name == "AstroFox"
    assert data.avatar_url == "https://cdn.example/avatar.png"
    assert data.xp_rank == 3 and data.co_rank == 5
    assert data.total_xp == 150 and data.messages == 1337 and data.coins == 910
    # level_progress(150) is deterministic from the curve.
    expected_level, expected_current, expected_needed = xp_helpers.db.level_progress(
        150
    )
    assert data.level == expected_level
    assert data.current == expected_current and data.needed == expected_needed


@pytest.mark.asyncio
async def test_build_rank_card_data_off_board_member_uses_question_mark():
    xp_provider = MagicMock()
    xp_provider.member_rank = AsyncMock(return_value=(None, None))
    coin_provider = MagicMock()
    coin_provider.member_rank = AsyncMock(return_value=(None, None))

    def _get_provider(name):
        return {"xp": xp_provider, "coins": coin_provider}.get(name)

    row = {"user_id": 7, "guild_id": 42, "xp": 0, "messages": 0, "coins": 0}
    with (
        patch.object(xp_helpers.db, "get_xp", AsyncMock(return_value=row)),
        patch(
            "services.rank_providers.get_provider",
            side_effect=_get_provider,
        ),
    ):
        data = await xp_helpers.build_rank_card_data(_member(), _guild())

    assert data.xp_rank == "?" and data.co_rank == "?"


@pytest.mark.asyncio
async def test_build_rank_response_attaches_card_and_points_embed_at_it():
    get_xp, get_provider = _patch_ranks(3, 5)
    with (
        patch.object(xp_helpers.db, "get_xp", get_xp),
        patch(
            "services.rank_providers.get_provider",
            side_effect=get_provider,
        ),
        patch.object(
            xp_helpers, "render_rank_card", return_value=b"\x89PNG\r\n\x1a\nfake"
        ),
    ):
        embed, card = await xp_helpers.build_rank_response(_member(), _guild(), "both")

    assert isinstance(card, discord.File)
    assert card.filename == xp_helpers.RANK_CARD_FILENAME
    assert embed.image.url == f"attachment://{xp_helpers.RANK_CARD_FILENAME}"
    # Embed parity: the "both" view carries every field the historical builder did.
    field_names = [f.name for f in embed.fields]
    assert field_names == [
        "XP Rank",
        "Level",
        "Total XP",
        "Progress",
        "Messages",
        "Coin Rank",
        "🪙 Coins",
    ]


@pytest.mark.asyncio
async def test_build_rank_response_falls_back_to_embed_only_without_pillow():
    get_xp, get_provider = _patch_ranks(3, 5)
    with (
        patch.object(xp_helpers.db, "get_xp", get_xp),
        patch(
            "services.rank_providers.get_provider",
            side_effect=get_provider,
        ),
        patch.object(xp_helpers, "render_rank_card", return_value=None),
    ):
        embed, card = await xp_helpers.build_rank_response(_member(), _guild(), "both")

    assert card is None
    assert embed.image.url is None  # no attachment image set on the fallback


@pytest.mark.asyncio
async def test_coins_view_omits_xp_fields_and_progress():
    get_xp, get_provider = _patch_ranks(3, 5)
    with (
        patch.object(xp_helpers.db, "get_xp", get_xp),
        patch(
            "services.rank_providers.get_provider",
            side_effect=get_provider,
        ),
        patch.object(xp_helpers, "render_rank_card", return_value=None),
    ):
        embed, _ = await xp_helpers.build_rank_response(_member(), _guild(), "coins")

    assert [f.name for f in embed.fields] == ["Coin Rank", "🪙 Coins"]
