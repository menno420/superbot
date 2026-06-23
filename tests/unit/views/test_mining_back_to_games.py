"""Regression tests for PR #1 — Games → Mining attaches Back-to-Games.

Live Discord testing reported that opening Mining from the Games hub did
not show a visible Back-to-Games button. The Games child button (now the
shared ``views.hub_children.HubChildButton`` that ``_GameHubButton``
subclasses) calls ``attach_back_to_games_button`` on the child view.

These tests pin the model-level contract: after Games → Mining the
returned view carries ``custom_id="games:back"``. They reuse the
existing ``attach_back_to_games_button`` helper — PR #1 does NOT
duplicate it.

If these tests pass but the button still does not render in live
Discord, the remaining root cause is client-side (component cap
interaction with PersistentView, row layout collision, mobile
rendering) and the live debugging steps in plan §5a Bug #5 take over.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from governance.models import VisibilityResult
from utils.subsystem_registry import SUBSYSTEMS
from views.games.hub import GamesHubView, _GameHubButton, attach_back_to_games_button
from views.mining.main_panel import MiningHubView


def _author() -> MagicMock:
    author = MagicMock(spec=discord.Member)
    author.id = 1
    author.display_name = "tester"
    return author


def _has_back_to_games(view: discord.ui.View) -> bool:
    # A child reaches Games either via the legacy externally-pushed "games:back"
    # button OR — since 2026-06-23 — the universal "nav:hub:games" control
    # auto-attached in the panel's __init__ (attach_standard_nav).
    return any(
        getattr(c, "custom_id", None) in ("games:back", "nav:hub:games")
        for c in view.children
    )


def test_attach_back_to_games_button_adds_games_back_id():
    """Sanity-check: the helper exists and adds the canonical custom_id.
    PR #1 reuses this helper rather than creating a parallel one.
    """
    view = MiningHubView()
    added = attach_back_to_games_button(view, _author())
    assert added is True
    assert _has_back_to_games(view)


@pytest.mark.asyncio
async def test_games_hub_button_attaches_back_to_games_on_child(monkeypatch):
    """End-to-end via the Games child button (the shared
    ``HubChildButton`` callback ``_GameHubButton`` inherits): clicking
    Mining from the Games hub must call ``attach_back_to_games_button``
    on the child MiningHubView so the user can return to Games.
    """
    hub = GamesHubView(_author())
    button = next(
        c
        for c in hub.children
        if isinstance(c, _GameHubButton) and c._subsystem == "mining"  # type: ignore[attr-defined]
    )

    mining_view = MiningHubView()
    mining_embed = discord.Embed(title="Mining")
    fake_cog = MagicMock()
    fake_cog.build_help_menu_view = AsyncMock(
        return_value=(mining_embed, mining_view),
    )

    # The shared callback does a local import; patch the help-cog symbol
    # it pulls in at that point.
    monkeypatch.setattr(
        "cogs.help_cog._cog_for_subsystem",
        lambda _bot, _key: fake_cog,
    )

    interaction = MagicMock()
    interaction.user = _author()
    interaction.client = MagicMock()
    interaction.response.edit_message = AsyncMock()

    # The button re-resolves governance at click time. Stub it to return
    # every subsystem visible so the test exercises the routing path, not
    # the gating.
    vis_result = VisibilityResult(
        visible_subsystems=set(SUBSYSTEMS),
        member_tier="moderator",
        resolved_from={},
        traces={},
    )
    with patch(
        "services.governance_service.resolve_visibility",
        new_callable=AsyncMock,
        return_value=vis_result,
    ):
        await button.callback(interaction)

    interaction.response.edit_message.assert_awaited_once()
    kwargs = interaction.response.edit_message.await_args.kwargs
    swapped = kwargs["view"]
    assert swapped is mining_view
    assert _has_back_to_games(swapped), (
        "Games → Mining must let the user return to Games. MiningHubView "
        "self-attaches 'nav:hub:games' in __init__, so the shared HubChildButton "
        "callback de-duplicates the external attach_back_to_games_button push."
    )


@pytest.mark.asyncio
async def test_back_to_games_attaches_below_25_component_cap():
    """MiningHubView has 6 action buttons after PR #1's no-op Overview
    removal. Back-to-Games adds 1, well under Discord's 25-cap.
    """
    view = MiningHubView()
    component_count_before = len(view.children)
    assert component_count_before <= 24
    attach_back_to_games_button(view, _author())
    assert _has_back_to_games(view)
    assert len(view.children) == component_count_before + 1
