"""Unit tests for :mod:`services.rank_providers` (PR G).

Pins:

* Provider registry exposes the six existing categories.
* Historical aliases (``!minelb``, ``!dm_lb``, ``!rpslb``,
  ``!countlb``, ``lb``, ``rankings``, etc.) resolve to the same
  providers they previously mapped to in
  ``cogs.leaderboard_cog.ALIASES_MAP``.
* Each provider's ``top`` returns ranked :class:`RankEntry` rows
  with provider-specific formatting baked into ``label``.
* Each provider's ``member_rank`` returns ``(rank, value)`` for an
  on-board user and ``(None, None)`` for an off-board user.
* The shared embed renderer in ``leaderboard_cog`` uses providers'
  ``empty_hint`` when ``top`` returns no rows.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from cogs.leaderboard_cog import _build_provider_embed
from services.rank_providers import (
    ALIASES,
    RankEntry,
    get_provider,
    provider_names,
)


def _guild() -> MagicMock:
    guild = MagicMock(spec=discord.Guild)
    guild.id = 42
    return guild


# ---------------------------------------------------------------------------
# Registry shape
# ---------------------------------------------------------------------------


def test_registry_exposes_canonical_categories():
    assert set(provider_names()) == {
        "xp",
        "coins",
        "mining",
        "creatures",
        "gamexp",
        "crafting",
        "deathmatch",
        "rps",
        "counting",
        "karma",
    }


def test_get_provider_returns_none_for_unknown_name():
    assert get_provider("not_a_category") is None
    assert get_provider("") is None


def test_get_provider_resolves_canonical_names():
    for name in ("xp", "coins", "mining", "deathmatch", "rps", "counting"):
        provider = get_provider(name)
        assert provider is not None
        assert provider.name == name


def test_historical_aliases_match_pre_pr_g_map():
    """The alias map mirrors the historical
    ``cogs.leaderboard_cog.ALIASES_MAP`` so existing operator
    shortcuts keep resolving to the same provider.
    """
    expected = {
        "minelb": "mining",
        "miningleaderboard": "mining",
        "dm_leaderboard": "deathmatch",
        "dm_lb": "deathmatch",
        "board": "deathmatch",
        "rpslb": "rps",
        "countlb": "counting",
        "counting_leaderboard": "counting",
        "lb": "xp",
        "rankings": "xp",
    }
    for alias, canonical in expected.items():
        assert ALIASES.get(alias) == canonical
        assert (get_provider(alias) or MagicMock()).name == canonical


def test_each_provider_has_select_metadata():
    """Select options in the leaderboard view come from providers —
    every provider must declare label/emoji/title so the registry
    can drive the dropdown without per-cog overrides.
    """
    for name in provider_names():
        provider = get_provider(name)
        assert provider is not None
        assert provider.display_title
        assert provider.select_label
        assert provider.empty_hint


# ---------------------------------------------------------------------------
# XP provider
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_xp_top_returns_rank_entries():
    provider = get_provider("xp")
    rows = [
        {"user_id": 1, "xp": 250, "level": 5},
        {"user_id": 2, "xp": 100, "level": 2},
    ]
    with patch(
        "services.rank_providers.db.fetchall",
        new_callable=AsyncMock,
        return_value=rows,
    ), patch(
        "services.rank_providers.resources.member_display",
        side_effect=lambda g, uid: f"User{uid}",
    ):
        entries = await provider.top(_guild())
    assert len(entries) == 2
    assert isinstance(entries[0], RankEntry)
    assert "User1" in entries[0].label
    assert "Level 5" in entries[0].label
    assert "250 XP" in entries[0].label


@pytest.mark.asyncio
async def test_top_entries_carry_structured_projection_for_the_image_card():
    """Every category populates ``name``/``score``/``value_text`` so the
    leaderboard image card can draw bars without re-parsing ``label``.

    Each provider is exercised through its own ``top`` so the projection is
    pinned end-to-end (not just on the dataclass default).
    """
    cases = [
        ("xp", "db.fetchall", [{"user_id": 1, "xp": 250, "level": 5}], 250.0),
        ("coins", "db.fetchall", [{"user_id": 1, "coins": 99}], 99.0),
        (
            "deathmatch",
            "db.get_deathmatch_leaderboard",
            [{"user_id": 1, "wins": 7, "losses": 2}],
            7.0,
        ),
        (
            "karma",
            "db.top_karma",
            [{"user_id": 1, "karma_points": 12}],
            12.0,
        ),
    ]
    for cat, target, rows, expected_score in cases:
        provider = get_provider(cat)
        assert provider is not None
        with patch(
            f"services.rank_providers.{target}",
            new_callable=AsyncMock,
            return_value=rows,
        ), patch(
            "services.rank_providers.resources.member_display",
            side_effect=lambda g, uid: f"User{uid}",
        ):
            entries = await provider.top(_guild())
        top = entries[0]
        assert top.name, cat
        assert "*" not in (top.name or ""), f"{cat}: name must be markdown-free"
        assert top.score == expected_score, cat
        assert top.value_text, cat


@pytest.mark.asyncio
async def test_xp_member_rank_finds_user_on_board():
    provider = get_provider("xp")
    rows = [
        {"user_id": 7, "xp": 500, "level": 10},
        {"user_id": 42, "xp": 250, "level": 5},
        {"user_id": 99, "xp": 100, "level": 2},
    ]
    with patch(
        "services.rank_providers.db.fetchall",
        new_callable=AsyncMock,
        return_value=rows,
    ):
        rank_pos, value = await provider.member_rank(_guild(), 42)
    assert rank_pos == 2
    assert value == "Level 5 (250 XP)"


@pytest.mark.asyncio
async def test_xp_member_rank_returns_none_when_off_board():
    provider = get_provider("xp")
    with patch(
        "services.rank_providers.db.fetchall",
        new_callable=AsyncMock,
        return_value=[{"user_id": 7, "xp": 500, "level": 10}],
    ):
        rank_pos, value = await provider.member_rank(_guild(), 999)
    assert rank_pos is None
    assert value is None


# ---------------------------------------------------------------------------
# Coins / Mining / Deathmatch / RPS / Counting providers
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_coins_top_renders_coins_glyph():
    provider = get_provider("coins")
    with patch(
        "services.rank_providers.db.fetchall",
        new_callable=AsyncMock,
        return_value=[{"user_id": 1, "coins": 9999}],
    ), patch(
        "services.rank_providers.resources.member_display",
        return_value="Alice",
    ):
        entries = await provider.top(_guild())
    assert "Alice" in entries[0].label
    assert "9999 🪙" in entries[0].label


@pytest.mark.asyncio
async def test_mining_top_caps_at_ten_entries():
    provider = get_provider("mining")
    rows = [(uid, uid * 10) for uid in range(1, 20)]
    with patch(
        "services.rank_providers.db.get_all_mining_totals",
        new_callable=AsyncMock,
        return_value=rows,
    ), patch(
        "services.rank_providers.resources.member_display",
        side_effect=lambda g, uid: f"U{uid}",
    ):
        entries = await provider.top(_guild())
    assert len(entries) == 10


@pytest.mark.asyncio
async def test_creatures_top_renders_caught_and_species():
    provider = get_provider("creatures")
    # top_collectors → [(user_id, total_caught, unique_species)]
    rows = [(1, 12, 8), (42, 5, 4)]
    with patch(
        "services.rank_providers.db.top_collectors",
        new_callable=AsyncMock,
        return_value=rows,
    ), patch(
        "services.rank_providers.creature_names",
        return_value=["a", "b"],
    ), patch(
        "services.rank_providers.resources.member_display",
        side_effect=lambda g, uid: f"U{uid}",
    ):
        entries = await provider.top(_guild())
    assert len(entries) == 2
    assert isinstance(entries[0], RankEntry)
    assert "U1" in entries[0].label
    assert "12 caught" in entries[0].label
    assert "8 species" in entries[0].label


@pytest.mark.asyncio
async def test_creatures_top_caps_at_ten():
    provider = get_provider("creatures")
    rows = [(uid, uid * 2, uid) for uid in range(1, 20)]
    with patch(
        "services.rank_providers.db.top_collectors",
        new_callable=AsyncMock,
        return_value=rows,
    ), patch(
        "services.rank_providers.creature_names",
        return_value=["a"],
    ), patch(
        "services.rank_providers.resources.member_display",
        side_effect=lambda g, uid: f"U{uid}",
    ):
        entries = await provider.top(_guild())
    assert len(entries) == 10


@pytest.mark.asyncio
async def test_creatures_member_rank_on_and_off_board():
    provider = get_provider("creatures")
    rows = [(1, 12, 8), (42, 5, 4)]
    with patch(
        "services.rank_providers.db.top_collectors",
        new_callable=AsyncMock,
        return_value=rows,
    ), patch(
        "services.rank_providers.creature_names",
        return_value=["a"],
    ):
        rank_pos, value = await provider.member_rank(_guild(), 42)
        assert rank_pos == 2
        assert value == "5 caught (4 species)"

        missing_pos, missing_value = await provider.member_rank(_guild(), 999)
        assert missing_pos is None and missing_value is None


@pytest.mark.asyncio
async def test_creatures_alias_resolves():
    assert (get_provider("creaturelb") or MagicMock()).name == "creatures"
    assert (get_provider("creature") or MagicMock()).name == "creatures"


@pytest.mark.asyncio
async def test_deathmatch_member_rank_finds_w_l_record():
    provider = get_provider("deathmatch")
    rows = [
        {"user_id": 1, "wins": 5, "losses": 1},
        {"user_id": 42, "wins": 3, "losses": 2},
    ]
    with patch(
        "services.rank_providers.db.get_deathmatch_leaderboard",
        new_callable=AsyncMock,
        return_value=rows,
    ):
        rank_pos, value = await provider.member_rank(_guild(), 42)
    assert rank_pos == 2
    assert value == "3W / 2L"


@pytest.mark.asyncio
async def test_deathmatch_top_forwards_guild_id():
    """Regression (audit P0-2): the deathmatch board must query the
    caller's guild, not the global ``guild_id=0`` pool.
    """
    provider = get_provider("deathmatch")
    mock_lb = AsyncMock(return_value=[])
    with patch("services.rank_providers.db.get_deathmatch_leaderboard", mock_lb):
        await provider.top(_guild())
    mock_lb.assert_awaited_once_with(42)


@pytest.mark.asyncio
async def test_deathmatch_member_rank_forwards_guild_id():
    """Regression (audit P0-2): member_rank must also scope by guild."""
    provider = get_provider("deathmatch")
    mock_lb = AsyncMock(return_value=[])
    with patch("services.rank_providers.db.get_deathmatch_leaderboard", mock_lb):
        await provider.member_rank(_guild(), 7)
    mock_lb.assert_awaited_once_with(42)


@pytest.mark.asyncio
async def test_rps_top_uses_pre_resolved_name():
    provider = get_provider("rps")
    rows = [{"name": "Bob", "wins": 4, "losses": 1, "ties": 2}]
    with patch(
        "services.rank_providers.db.rps_get_leaderboard",
        new_callable=AsyncMock,
        return_value=rows,
    ):
        entries = await provider.top(_guild())
    # RPS query returns a "name" column directly — no member_display.
    assert "Bob" in entries[0].label
    assert "4W / 1L / 2T" in entries[0].label


@pytest.mark.asyncio
async def test_counting_aggregates_across_channels():
    provider = get_provider("counting")
    state = {
        "channels": {
            "100": {"leaderboard": {"1": 50, "2": 20}},
            "200": {"leaderboard": {"1": 10, "3": 15}},
        },
    }
    with patch(
        "services.rank_providers.db.get_counting_state",
        new_callable=AsyncMock,
        return_value=state,
    ), patch(
        "services.rank_providers.resources.member_display",
        side_effect=lambda g, uid: f"U{uid}",
    ):
        entries = await provider.top(_guild())
        rank_pos, value = await provider.member_rank(_guild(), 1)
    # User 1 has 50 + 10 = 60 counts across two channels.
    assert "U1" in entries[0].label
    assert "60" in entries[0].label
    assert rank_pos == 1
    assert value == "60 counts"


# ---------------------------------------------------------------------------
# Shared embed renderer in leaderboard_cog uses provider empty_hint
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_build_provider_embed_surfaces_empty_hint():
    provider = get_provider("mining")
    with patch(
        "services.rank_providers.db.get_all_mining_totals",
        new_callable=AsyncMock,
        return_value=[],
    ):
        embed = await _build_provider_embed(provider, _guild())
    assert provider.empty_hint in (embed.description or "")


@pytest.mark.asyncio
async def test_build_provider_embed_applies_medal_prefixes():
    """First three entries get medal glyphs; the rest get ``#N`` prefixes."""
    provider = get_provider("xp")
    rows = [
        {"user_id": i, "xp": 1000 - i, "level": 10 - i}
        for i in range(1, 6)
    ]
    with patch(
        "services.rank_providers.db.fetchall",
        new_callable=AsyncMock,
        return_value=rows,
    ), patch(
        "services.rank_providers.resources.member_display",
        side_effect=lambda g, uid: f"U{uid}",
    ):
        embed = await _build_provider_embed(provider, _guild())
    description = embed.description or ""
    assert "🥇" in description
    assert "🥈" in description
    assert "🥉" in description
    assert "#4" in description
    assert "#5" in description
