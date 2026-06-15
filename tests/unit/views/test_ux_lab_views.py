"""UX Lab view smoke tests — every exhibit builds inside platform caps.

Construction-level verification (no Discord connection): each wing page must
respect the legacy 25-component / 10-embed / 6000-char caps with the spec
card included, and demo callbacks must drive without touching anything
outside the view (the runtime half of the zero-write fence).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from views.ux_lab.buttons import ButtonsWingView
from views.ux_lab.embeds import EmbedsWingView
from views.ux_lab.home import UxLabHomeView, build_home_embed, home_builder
from views.ux_lab.modals import ModalsWingView
from views.ux_lab.probes import ProbesBenchView
from views.ux_lab.selects import SelectsWingView
from views.ux_lab.wing import NAV_ROW

_WINGS = (ButtonsWingView, SelectsWingView, ModalsWingView, EmbedsWingView)


def _author() -> MagicMock:
    author = MagicMock(spec=discord.Member)
    author.id = 1234
    author.display_name = "Tester"
    return author


async def _noop_builder(
    interaction: discord.Interaction,
) -> tuple[discord.Embed, discord.ui.View]:
    return discord.Embed(), discord.ui.View()


def _interaction(*, done: bool = False) -> MagicMock:
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = _author()
    interaction.response = MagicMock()
    interaction.response.is_done = MagicMock(return_value=done)
    interaction.response.edit_message = AsyncMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.send_modal = AsyncMock()
    interaction.edit_original_response = AsyncMock()
    return interaction


@pytest.mark.parametrize("wing_cls", _WINGS)
def test_every_exhibit_builds_within_caps(wing_cls):
    wing = wing_cls(_author(), home_builder=_noop_builder)
    ids = wing._exhibit_ids()
    assert ids, wing_cls.__name__
    for index, pattern_id in enumerate(ids):
        wing._index = index
        wing.state.clear()
        embeds, view = wing.build()
        assert view is wing
        assert 1 <= len(embeds) <= 10, pattern_id
        assert sum(len(e) for e in embeds) <= 6000, pattern_id
        assert len(view.children) <= 25, pattern_id
        # Exhibit items stay off the nav row; nav row carries exactly 4.
        nav_items = [i for i in view.children if getattr(i, "row", None) == NAV_ROW]
        assert len(nav_items) == 4, pattern_id


@pytest.mark.parametrize("wing_cls", _WINGS)
@pytest.mark.asyncio
async def test_wing_navigation_advances_and_resets_state(wing_cls):
    wing = wing_cls(_author(), home_builder=_noop_builder)
    wing.build()
    wing.state["leftover"] = True
    next_btn = next(
        item
        for item in wing.children
        if isinstance(item, discord.ui.Button)
        and item.emoji is not None
        and str(item.emoji) == "▶"
    )
    interaction = _interaction()
    await next_btn.callback(interaction)
    assert wing._index == 1
    assert wing.state == {}
    interaction.response.edit_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_toggle_pill_flips_and_rerenders_in_place():
    wing = ButtonsWingView(_author(), home_builder=_noop_builder)
    wing._index = wing._exhibit_ids().index("toggle_pills")
    wing.build()
    pill = next(
        item
        for item in wing.children
        if isinstance(item, discord.ui.Button)
        and item.label is not None
        and item.label.startswith("Caps")
    )
    assert wing.state["flags"]["Caps"] is False
    await pill.callback(_interaction())
    assert wing.state["flags"]["Caps"] is True


@pytest.mark.asyncio
async def test_danger_confirm_never_executes_on_first_click():
    wing = ButtonsWingView(_author(), home_builder=_noop_builder)
    wing._index = wing._exhibit_ids().index("danger_confirm_then_result")
    wing.build()
    danger = next(
        item
        for item in wing.children
        if isinstance(item, discord.ui.Button)
        and item.style is discord.ButtonStyle.danger
    )
    await danger.callback(_interaction())
    assert wing.state["stage"] == "confirming"


def test_home_view_and_embed_build():
    embed = build_home_embed()
    assert len(embed) <= 6000
    view = UxLabHomeView(_author())
    assert 1 <= len(view.children) <= 25
    # Author lock stays on (workbench default — not a public panel).
    assert view._public is False


@pytest.mark.asyncio
async def test_home_builder_returns_fresh_home():
    interaction = _interaction()
    embed, view = await home_builder(interaction)
    assert isinstance(view, UxLabHomeView)
    assert "UX Lab" in (embed.title or "")


def test_probe_bench_builds_within_caps():
    bench = ProbesBenchView(_author(), home_builder=_noop_builder)
    embeds, view = bench.build()
    assert len(view.children) <= 25
    assert sum(len(e) for e in embeds) <= 6000


@pytest.mark.asyncio
async def test_probe_select_26_reports_rejection_layer():
    bench = ProbesBenchView(_author(), home_builder=_noop_builder)
    channel = MagicMock()
    channel.send = AsyncMock()
    result = await bench._probe_select_26(channel)
    # Wherever the rejection lands (library or API mock-pass-through),
    # the probe must report rather than raise.
    assert result.probe_id == "probe_select_26_options"
    assert result.detail
