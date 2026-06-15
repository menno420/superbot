"""UX Lab PR-B wings — CV2 layout builders and PIL image exhibits.

Construction-level verification: every LayoutView the CV2 wing can send must
build inside the library-enforced 40-child / 4000-char budgets (discord.py
raises at construction, so instantiation IS the test), and every image
exhibit must render bytes under the 8 MiB bot cap with alt text attached.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import discord
import pytest

from utils.ux_patterns.image_builders import (
    render_event_poster,
    render_leaderboard_image,
    render_welcome_card,
)
from views.ux_lab.image_cards import _RENDERERS, ImageWingView
from views.ux_lab.layout_v2 import LayoutWingView, _LabLayout

_BOT_ATTACH_CAP = 8 * 1024 * 1024


def _author() -> MagicMock:
    author = MagicMock(spec=discord.Member)
    author.id = 1234
    return author


async def _noop_builder(
    interaction: discord.Interaction,
) -> tuple[discord.Embed, discord.ui.View]:
    return discord.Embed(), discord.ui.View()


def test_every_cv2_layout_builds_within_library_budgets():
    """discord.py raises ValueError at >40 children / >4000 chars — so a
    clean construction proves every exhibit fits the CV2 budget.
    """
    wing = LayoutWingView(_author(), home_builder=_noop_builder)
    builders = {
        "cv2_text_only": wing._build_text_only,
        "cv2_section_accessory": wing._build_sections,
        "cv2_container_dashboard": wing._build_container,
        "cv2_media_gallery": wing._build_gallery,
        "cv2_settings_page": wing._build_settings_page,
        "cv2_mobile_compact": wing._build_mobile_compact,
        "cv2_interactive_mix": wing._build_interactive,
    }
    for pattern_id, builder in builders.items():
        layout = builder(1234)
        assert isinstance(layout, _LabLayout), pattern_id
    layout, files = wing._build_file(1234)
    assert isinstance(layout, _LabLayout)
    assert files and files[0].description, "file exhibit must carry alt text"


def test_cv2_wing_browser_pages_within_caps():
    wing = LayoutWingView(_author(), home_builder=_noop_builder)
    for index, pattern_id in enumerate(wing._exhibit_ids()):
        wing._index = index
        embeds, view = wing.build()
        assert len(view.children) <= 25, pattern_id
        assert sum(len(e) for e in embeds) <= 6000, pattern_id


def test_layoutview_enforces_the_40_child_ceiling():
    """The fact the limits doc + probes P-03/P-04 rest on."""
    view = discord.ui.LayoutView()
    for n in range(40):
        view.add_item(discord.ui.TextDisplay(f"item {n}"))
    with pytest.raises(ValueError, match="maximum number of children"):
        view.add_item(discord.ui.TextDisplay("the 41st"))


@pytest.mark.asyncio
async def test_lab_layout_is_author_locked():
    layout = _LabLayout(author_id=1)
    stranger = MagicMock(spec=discord.Interaction)
    stranger.user = MagicMock()
    stranger.user.id = 2
    stranger.response = MagicMock()
    stranger.response.send_message = MagicMock()

    from unittest.mock import AsyncMock

    stranger.response.send_message = AsyncMock()
    assert await layout.interaction_check(stranger) is False
    stranger.response.send_message.assert_awaited_once()


def test_image_wing_pages_within_caps():
    wing = ImageWingView(_author(), home_builder=_noop_builder)
    for index, pattern_id in enumerate(wing._exhibit_ids()):
        wing._index = index
        embeds, view = wing.build()
        assert len(view.children) <= 25, pattern_id
        assert sum(len(e) for e in embeds) <= 6000, pattern_id


def test_every_image_exhibit_has_alt_text_and_filename():
    for pattern_id, (_renderer, filename, alt) in _RENDERERS.items():
        assert filename, pattern_id
        assert alt and len(alt) <= 1024, pattern_id


@pytest.mark.parametrize(
    "renderer",
    [render_welcome_card, render_leaderboard_image, render_event_poster],
)
def test_new_image_builders_render_under_the_bot_cap(renderer):
    pytest.importorskip("PIL")
    png = renderer()
    assert png is not None
    assert 0 < len(png) < _BOT_ATTACH_CAP


def test_shipped_renderers_still_render_from_sample_data():
    """The reuse contract: the lab exhibits the LIVE renderers."""
    pytest.importorskip("PIL")
    for pattern_id in (
        "pil_inventory_card",
        "pil_stat_card",
        "pil_character_paperdoll",
    ):
        renderer, _f, _a = _RENDERERS[pattern_id]
        data = renderer()
        assert data is not None and len(data) < _BOT_ATTACH_CAP, pattern_id
