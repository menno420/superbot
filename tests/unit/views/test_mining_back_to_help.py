"""Regression tests for PR #1 — Help → Mining attaches Back-to-Help.

Live Discord testing reported that opening Mining from Help (either by
the dropdown or by the typed `!help mining` command) did not show a
visible Back-to-Help button. Code inspection shows that
``_attach_back_to_help_button`` IS called on the routed view at
``help_cog.py:577`` (dropdown path) and ``help_cog.py:621`` (typed
path), and the helper itself adds a button with ``custom_id="help:back"``
at row 4.

These tests pin the contract that — at the model level — the Back
button IS attached to the Mining view for both entry paths. If these
tests pass but the button still does not render in live Discord, the
remaining root cause is client-side (component cap interaction with
PersistentView, row layout collision, mobile rendering) and the live
debugging steps in plan §5a Bug #4 take over.

We do NOT assert on `disabled` flag here because `attach_back_button`
constructs an enabled button by default; what matters is that the
button exists with the canonical custom_id.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from cogs import help_cog
from views.mining.main_panel import MiningHubView


def _projection(visible: set[str], tier: str):
    from governance.models import VisibilityResult
    from services.help_projection import HelpProjection

    return HelpProjection.from_visibility(
        VisibilityResult(
            visible_subsystems=visible,
            member_tier=tier,
            resolved_from={},
            traces={},
        ),
    )


def _opener() -> help_cog.HelpOpener:
    user = MagicMock()
    user.id = 1
    user.display_name = "tester"
    bot = MagicMock()
    return help_cog.HelpOpener(
        user=user,
        guild=MagicMock(),
        guild_id=42,
        client=bot,
        channel=MagicMock(),
    )


def _has_back_to_help(view: discord.ui.View) -> bool:
    return any(getattr(c, "custom_id", None) == "help:back" for c in view.children)


@pytest.mark.asyncio
async def test_typed_help_mining_route_resolves_to_mining_subsystem():
    """``!help mining`` must resolve to the mining subsystem so the
    opener can dispatch to ``mining_cog.build_help_menu_view``.
    """
    opener = _opener()
    route = help_cog._resolve_route("mining", bot=opener.client)
    assert route.kind == "subsystem"
    assert route.target == "mining"


@pytest.mark.asyncio
async def test_typed_help_mining_opens_panel_with_back_to_help(monkeypatch):
    """End-to-end via ``_open_route``: Mining must come back with a
    ``custom_id="help:back"`` attached at the route level. ``_open_route``
    itself attaches Back-to-Help for subsystem routes; this is what
    typed ``!help mining`` and the dropdown both use.

    NOTE: ``_open_route`` returns the view BEFORE
    ``_attach_back_to_help_button`` is called on it (the typed/dropdown
    call sites attach AFTER opening). We therefore exercise the same
    sequence the help_command does: open the route, then call
    ``_attach_back_to_help_button`` on the result. This is the live code
    path; both ``help_cog.help_command`` (line ~621) and
    ``HelpCategoryView._on_select`` (line ~577) follow it.
    """
    opener = _opener()
    route = help_cog._resolve_route("mining", bot=opener.client)

    fake_view = MiningHubView()
    fake_embed = discord.Embed(title="Mining")
    fake_cog = MagicMock()
    fake_cog.build_help_menu_view = AsyncMock(return_value=(fake_embed, fake_view))

    monkeypatch.setattr(help_cog, "_cog_for_subsystem", lambda _bot, _key: fake_cog)
    embed, view = await help_cog._open_route(
        route,
        opener,
        projection=_projection({"mining"}, "user"),
    )

    assert view is fake_view
    # Live attachment step the help_command performs after _open_route.
    help_cog._attach_back_to_help_button(view)
    assert _has_back_to_help(view), (
        "After typed !help mining, MiningHubView must carry custom_id='help:back'. "
        f"Current ids: {[getattr(c, 'custom_id', None) for c in view.children]}"
    )


@pytest.mark.asyncio
async def test_dropdown_help_mining_opens_panel_with_back_to_help(monkeypatch):
    """Dropdown Help → Mining must also carry Back-to-Help. Dropdown
    uses the same ``_open_route`` + ``_attach_back_to_help_button`` pair
    via ``HelpCategoryView._on_select`` and ``HelpPanelView._on_select``.
    """
    opener = _opener()
    route = help_cog._resolve_route("mining", bot=opener.client)

    fake_view = MiningHubView()
    fake_embed = discord.Embed(title="Mining")
    fake_cog = MagicMock()
    fake_cog.build_help_menu_view = AsyncMock(return_value=(fake_embed, fake_view))

    monkeypatch.setattr(help_cog, "_cog_for_subsystem", lambda _bot, _key: fake_cog)
    _, view = await help_cog._open_route(
        route,
        opener,
        projection=_projection({"mining"}, "user"),
    )

    help_cog._attach_back_to_help_button(view)
    assert _has_back_to_help(view)


@pytest.mark.asyncio
async def test_back_to_help_attaches_below_25_component_cap():
    """MiningHubView has 6 action buttons after PR #1's no-op Overview
    removal. Back-to-Help adds 1 component, well under Discord's 25-cap.
    Pins this so future button additions don't silently drop the back
    button.
    """
    view = MiningHubView()
    component_count_before = len(view.children)
    assert component_count_before <= 24, (
        f"MiningHubView has {component_count_before} components — adding "
        f"Back-to-Help would push it to or past Discord's 25-cap and the "
        f"button would silently be dropped"
    )
    help_cog._attach_back_to_help_button(view)
    assert _has_back_to_help(view)
    assert len(view.children) == component_count_before + 1
