"""UX Lab PR-C wings — mock studio, compare, persistence exhibit."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from views.ux_lab.compare import CompareView, render_pattern_preview
from views.ux_lab.mockups import MockupsWingView
from views.ux_lab.persistent_demo import UxLabPersistentDemo


def _author() -> MagicMock:
    author = MagicMock(spec=discord.Member)
    author.id = 1234
    return author


async def _noop_builder(
    interaction: discord.Interaction,
) -> tuple[discord.Embed, discord.ui.View]:
    return discord.Embed(), discord.ui.View()


def _interaction() -> MagicMock:
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = _author()
    interaction.response = MagicMock()
    interaction.response.is_done = MagicMock(return_value=False)
    interaction.response.edit_message = AsyncMock()
    interaction.response.send_message = AsyncMock()
    return interaction


def test_mock_studio_pages_within_caps_and_bannered():
    wing = MockupsWingView(_author(), home_builder=_noop_builder)
    for index, pattern_id in enumerate(wing._exhibit_ids()):
        wing._index = index
        wing.state.clear()
        embeds, view = wing.build()
        assert len(view.children) <= 25, pattern_id
        assert sum(len(e) for e in embeds) <= 6000, pattern_id
        # Every mock page must declare itself a mock.
        assert any("MOCK" in (e.description or "") for e in embeds), pattern_id


@pytest.mark.asyncio
async def test_mock_rsvp_counts_update_in_place():
    wing = MockupsWingView(_author(), home_builder=_noop_builder)
    wing._index = wing._exhibit_ids().index("mock_event_rsvp")
    wing.build()
    yes_btn = next(
        item
        for item in wing.children
        if isinstance(item, discord.ui.Button)
        and item.style is discord.ButtonStyle.success
    )
    await yes_btn.callback(_interaction())
    assert wing.state["rsvp"]["yes"] == 5


def test_security_mock_omits_declined_tiers():
    """Q-0111: tiers 3+4 were declined — the mock must not render them."""
    wing = MockupsWingView(_author(), home_builder=_noop_builder)
    wing._index = wing._exhibit_ids().index("mock_security_alerts")
    embeds, view = wing.build()
    text = " ".join((e.title or "") + (e.description or "") for e in embeds)
    labels = " ".join(
        str(i.label) for i in view.children if isinstance(i, discord.ui.Button)
    )
    assert "VPN" not in labels and "Alt detection" not in labels
    assert "declined" in text


def test_compare_builds_and_previews_every_comparable_pattern():
    panel = CompareView(_author(), home_builder=_noop_builder)
    embeds, view = panel.build()
    assert len(view.children) <= 25
    # Preview helper renders for a sample of patterns across categories.
    for pattern_id in (
        "danger_confirm_then_result",
        "settings_multi_select_preview",
        "cv2_container_dashboard",
        "mock_welcome_ab",
    ):
        previews = render_pattern_preview(pattern_id, _author())
        assert previews, pattern_id
        assert sum(len(e) for e in previews) <= 6000, pattern_id


@pytest.mark.asyncio
async def test_compare_flip_swaps_sides_in_place():
    panel = CompareView(_author(), home_builder=_noop_builder)
    panel._category = None
    panel._a = "info_card"
    panel._b = "success_card"
    embeds, _ = panel.build()
    flip = next(
        item
        for item in panel.children
        if isinstance(item, discord.ui.Button) and item.label == "Show B"
    )
    interaction = _interaction()
    await flip.callback(interaction)
    assert panel._showing_b is True
    interaction.response.edit_message.assert_awaited_once()


def test_persistent_demo_contract():
    """Static custom_ids + timeout=None — the PersistentView contract."""
    view = UxLabPersistentDemo()
    assert view.timeout is None
    ids = {item.custom_id for item in view.children}
    assert ids == {"ux_lab:persist:ping", "ux_lab:persist:remove"}
    assert UxLabPersistentDemo.SUBSYSTEM == "ux_lab"


@pytest.mark.asyncio
async def test_persistent_demo_remove_requires_admin():
    view = UxLabPersistentDemo()
    interaction = _interaction()
    interaction.user.guild_permissions = MagicMock()
    interaction.user.guild_permissions.administrator = False
    interaction.message = MagicMock()
    interaction.message.delete = AsyncMock()
    # Decorated callbacks live on the class (instance attr is the component);
    # drive them as type(view).method(view, interaction, button).
    await type(view).remove(view, interaction, MagicMock())
    interaction.message.delete.assert_not_awaited()
    interaction.response.send_message.assert_awaited_once()
