"""The leaderboard **image card** (Q-0023 visual card engine, H2).

The board attaches a rendered top-N image when a provider exposes the
structured ``(name, score, value_text)`` projection, and falls back to the
plain embed otherwise — Pillow-less hosts, empty boards, and card-less
categories must all degrade cleanly. These tests pin that contract at the
cog seam without a real Pillow render (the renderer is mocked to isolate the
attach/fallback decision; the renderer's own byte output is covered in
``tests/unit/views/test_ux_lab_layout_image_wings.py``).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from cogs import leaderboard_cog
from cogs.leaderboard_cog import _CARD_FILENAME, _render_card
from services.rank_providers import RankEntry, get_provider
from utils.ux_patterns.image_builders import (
    _bar_fraction,
    _clean_name,
    render_leaderboard_image,
)


def _guild() -> MagicMock:
    guild = MagicMock(spec=discord.Guild)
    guild.id = 1
    return guild


def _structured_entries() -> list[RankEntry]:
    return [
        RankEntry(label="**Alice** — 250 XP", name="Alice", score=250.0, value_text="250 XP"),
        RankEntry(label="**Bob** — 100 XP", name="Bob", score=100.0, value_text="100 XP"),
    ]


# ---------------------------------------------------------------------------
# _render_card — the attach/fallback decision
# ---------------------------------------------------------------------------


def test_render_card_returns_file_when_rows_are_structured():
    provider = get_provider("xp")
    assert provider is not None
    with patch(
        "cogs.leaderboard_cog.render_leaderboard_image",
        return_value=b"\xff\xd8jpeg-bytes",
    ) as render:
        card = _render_card(provider, _structured_entries())
    assert isinstance(card, discord.File)
    assert card.filename == _CARD_FILENAME
    # The provider title + value texts are forwarded to the renderer.
    _args, kwargs = render.call_args
    assert kwargs["title"] == provider.display_title
    assert kwargs["value_texts"] == ("250 XP", "100 XP")


def test_render_card_forwards_the_provider_theme():
    """The board renders in the provider's declared skin (the H2-polish slice)."""
    provider = get_provider("mining")  # declares card_theme="abyss"
    assert provider is not None
    with patch(
        "cogs.leaderboard_cog.render_leaderboard_image",
        return_value=b"\xff\xd8jpeg-bytes",
    ) as render:
        _render_card(provider, _structured_entries())
    _args, kwargs = render.call_args
    assert kwargs["theme"] == "abyss"


def test_render_card_is_none_for_empty_board():
    provider = get_provider("xp")
    assert provider is not None
    assert _render_card(provider, []) is None


def test_render_card_is_none_when_any_entry_lacks_projection():
    """A category that hasn't opted into the card (no name/score) renders
    embed-only — never a partial/broken board."""
    provider = get_provider("xp")
    assert provider is not None
    mixed = [
        RankEntry(label="**Alice** — 250 XP", name="Alice", score=250.0),
        RankEntry(label="**Bob** — legacy row"),  # no name/score
    ]
    assert _render_card(provider, mixed) is None


def test_render_card_is_none_when_pillow_unavailable():
    provider = get_provider("xp")
    assert provider is not None
    with patch("cogs.leaderboard_cog.render_leaderboard_image", return_value=None):
        assert _render_card(provider, _structured_entries()) is None


# ---------------------------------------------------------------------------
# _build_provider_response — embed image wiring
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_response_sets_embed_image_when_card_present():
    provider = get_provider("xp")
    assert provider is not None
    with patch.object(
        provider, "top", new=AsyncMock(return_value=_structured_entries())
    ), patch(
        "cogs.leaderboard_cog.render_leaderboard_image",
        return_value=b"\xff\xd8jpeg",
    ):
        embed, card = await leaderboard_cog._build_provider_response(provider, _guild())
    assert card is not None
    assert embed.image.url == f"attachment://{_CARD_FILENAME}"
    # The embed text board stays the source of truth / fallback.
    assert "Alice" in (embed.description or "")


@pytest.mark.asyncio
async def test_response_has_no_image_when_card_absent():
    provider = get_provider("xp")
    assert provider is not None
    with patch.object(
        provider, "top", new=AsyncMock(return_value=_structured_entries())
    ), patch("cogs.leaderboard_cog.render_leaderboard_image", return_value=None):
        embed, card = await leaderboard_cog._build_provider_response(provider, _guild())
    assert card is None
    assert embed.image.url is None
    assert "Alice" in (embed.description or "")


# ---------------------------------------------------------------------------
# render_leaderboard_image — title / value_texts / empty
# ---------------------------------------------------------------------------


def test_renderer_returns_none_for_empty_rows():
    # No PIL needed — the empty guard precedes any canvas work.
    assert render_leaderboard_image(()) is None


def test_renderer_honours_title_and_value_texts():
    pytest.importorskip("PIL")
    data = render_leaderboard_image(
        (("Alice", 250.0), ("Bob", 100.0)),
        title="🏆 XP Leaderboard",
        value_texts=("250 XP", "100 XP"),
    )
    assert data is not None and len(data) > 0


@pytest.mark.parametrize("theme", ["midnight", "ember", "verdant", "abyss"])
def test_renderer_renders_in_every_named_theme(theme):
    pytest.importorskip("PIL")
    data = render_leaderboard_image((("Alice", 250.0),), theme=theme)
    assert data is not None and len(data) > 0


def test_renderer_handles_outlier_and_unresolved_rows():
    # A runaway leader + an unresolved <@id> row + an emoji title must render
    # cleanly to bytes (no crash, no clipped value, no tofu).
    pytest.importorskip("PIL")
    data = render_leaderboard_image(
        (("tramway", 118030.0), ("<@123456789012345678>", 8450.0), ("m", 3720.0)),
        title="🏆 XP Leaderboard",
        value_texts=("118,030 XP", "8,450 XP", "3,720 XP"),
    )
    assert data is not None and len(data) > 0


# ---------------------------------------------------------------------------
# render helpers — name cleaning + outlier-safe bar scaling
# ---------------------------------------------------------------------------


def test_clean_name_neutralises_raw_mentions():
    # A member who left / isn't cached renders as <@id>; never bake that into
    # the image — show a neutral placeholder instead.
    assert _clean_name("<@1118746464013787268>") == "unknown"
    assert _clean_name("<@!123>") == "unknown"
    assert _clean_name("  <@123>  ") == "unknown"
    # Resolved names (even with punctuation) pass through untouched.
    assert _clean_name("tramway") == "tramway"
    assert _clean_name("What the...?!") == "What the...?!"


def test_bar_fraction_is_outlier_safe():
    # The runaway leader fills the bar; every other row keeps a visible, floored
    # bar instead of collapsing into an invisible stub (the screenshot bug).
    assert _bar_fraction(118030, 118030) == pytest.approx(1.0)
    small = _bar_fraction(3720, 118030)
    assert 0.12 <= small < 1.0
    # Monotonic — more score is always a longer bar.
    assert _bar_fraction(10045, 118030) > _bar_fraction(3720, 118030)
    # Degenerate inputs never raise / go negative.
    assert _bar_fraction(0, 100) == 0.0
    assert _bar_fraction(50, 0) == 0.0
