"""Integration tests for typed ``!help <name>`` parity with the dropdown.

After the routing-consistency PR, typed Help and the Help dropdown both
go through :func:`cogs.help_cog._resolve_route` and
:func:`cogs.help_cog._open_route`. These tests verify the resolver
+ opener pipeline lands on the same surface as the dropdown would.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from cogs import help_cog


def _opener() -> help_cog.HelpOpener:
    user = MagicMock()
    user.id = 1
    bot = MagicMock()
    return help_cog.HelpOpener(
        user=user,
        guild=None,
        guild_id=None,
        client=bot,
        channel=MagicMock(),
    )


def _opener_with_fake_cog(cog_subsystem: str, fake_cog) -> help_cog.HelpOpener:
    opener = _opener()
    # Patch ``_cog_for_subsystem`` to return our fake cog for the
    # subsystem the route resolves to.
    return opener, fake_cog


# ---------------------------------------------------------------------------
# Hub routes — open the host cog's panel via build_help_menu_view
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_help_games_opens_games_hub_panel(monkeypatch):
    """``!help games`` must resolve to the games hub and call its
    ``build_help_menu_view`` (matching the dropdown).
    """
    opener = _opener()
    route = help_cog._resolve_route("games", bot=opener.client)
    assert route.kind == "hub"
    assert route.target == "games"

    fake_view = discord.ui.View()
    fake_embed = discord.Embed(title="Games Hub")
    fake_cog = MagicMock()
    fake_cog.build_help_menu_view = AsyncMock(return_value=(fake_embed, fake_view))

    monkeypatch.setattr(help_cog, "_cog_for_subsystem", lambda _bot, _key: fake_cog)
    embed, view = await help_cog._open_route(
        route,
        opener,
        visible_subsystems={"games"},
        member_tier="user",
    )
    fake_cog.build_help_menu_view.assert_awaited_once()
    assert embed is fake_embed
    assert view is fake_view


@pytest.mark.asyncio
async def test_help_platform_opens_platform_hub_via_dedicated_builder(monkeypatch):
    """``!help platform`` must call ``build_platform_help_menu_view`` —
    the Platform hub's dedicated builder — not the generic hook.
    """
    opener = _opener()
    route = help_cog._resolve_route("platform", bot=opener.client)
    assert route.kind == "hub"
    assert route.target == "diagnostic"

    fake_view = discord.ui.View()
    fake_embed = discord.Embed(title="Platform hub")
    fake_cog = MagicMock()
    fake_cog.build_platform_help_menu_view = AsyncMock(
        return_value=(fake_embed, fake_view),
    )
    fake_cog.build_help_menu_view = AsyncMock(
        return_value=(discord.Embed(title="WRONG"), discord.ui.View()),
    )

    monkeypatch.setattr(help_cog, "_cog_for_subsystem", lambda _bot, _key: fake_cog)
    embed, view = await help_cog._open_route(
        route,
        opener,
        visible_subsystems={"diagnostic"},
        member_tier="administrator",
    )
    fake_cog.build_platform_help_menu_view.assert_awaited_once()
    fake_cog.build_help_menu_view.assert_not_called()
    assert embed.title == "Platform hub"
    assert view is fake_view


@pytest.mark.asyncio
async def test_help_diagnostic_singular_opens_platform_hub(monkeypatch):
    """The singular hub key ``diagnostic`` is the Platform / Diagnostics
    hub. ``!help diagnostic`` routes the same as ``!help platform``.
    """
    opener = _opener()
    route = help_cog._resolve_route("diagnostic", bot=opener.client)
    assert route.kind == "hub"
    assert route.target == "diagnostic"

    fake_view = discord.ui.View()
    fake_embed = discord.Embed(title="Platform hub")
    fake_cog = MagicMock()
    fake_cog.build_platform_help_menu_view = AsyncMock(
        return_value=(fake_embed, fake_view),
    )

    monkeypatch.setattr(help_cog, "_cog_for_subsystem", lambda _bot, _key: fake_cog)
    embed, view = await help_cog._open_route(
        route,
        opener,
        visible_subsystems={"diagnostic"},
        member_tier="administrator",
    )
    fake_cog.build_platform_help_menu_view.assert_awaited_once()
    assert embed.title == "Platform hub"


@pytest.mark.asyncio
async def test_help_diagnostics_plural_opens_diagnostics_hub(monkeypatch):
    """``!help diagnostics`` / ``!help diag`` open the Diagnostics Hub
    via the generic ``build_help_menu_view`` hook — not the Platform Hub
    builder. This is the canary against any future change that merges
    the two hooks.
    """
    opener = _opener()
    route = help_cog._resolve_route("diagnostics", bot=opener.client)
    assert route.kind == "subsystem"
    assert route.target == "diagnostic"

    fake_view = discord.ui.View()
    fake_embed = discord.Embed(title="Diagnostics Hub")
    fake_cog = MagicMock()
    fake_cog.build_help_menu_view = AsyncMock(return_value=(fake_embed, fake_view))
    fake_cog.build_platform_help_menu_view = AsyncMock(
        return_value=(discord.Embed(title="WRONG"), discord.ui.View()),
    )

    monkeypatch.setattr(help_cog, "_cog_for_subsystem", lambda _bot, _key: fake_cog)
    embed, view = await help_cog._open_route(
        route,
        opener,
        visible_subsystems={"diagnostic"},
        member_tier="administrator",
    )
    fake_cog.build_help_menu_view.assert_awaited_once()
    fake_cog.build_platform_help_menu_view.assert_not_called()
    assert embed.title == "Diagnostics Hub"


# ---------------------------------------------------------------------------
# Subsystem routes — open panel hooks, not command-list fallback
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_help_blackjack_opens_blackjack_panel(monkeypatch):
    """``!help blackjack`` must open the Blackjack panel via the cog's
    ``build_help_menu_view`` hook, not the command-list fallback.
    """
    opener = _opener()
    route = help_cog._resolve_route("blackjack", bot=opener.client)
    assert route.kind == "subsystem"
    assert route.target == "blackjack"

    fake_view = discord.ui.View()
    fake_embed = discord.Embed(title="Blackjack")
    fake_cog = MagicMock()
    fake_cog.build_help_menu_view = AsyncMock(return_value=(fake_embed, fake_view))

    monkeypatch.setattr(help_cog, "_cog_for_subsystem", lambda _bot, _key: fake_cog)
    embed, view = await help_cog._open_route(
        route,
        opener,
        visible_subsystems={"blackjack"},
        member_tier="user",
    )
    fake_cog.build_help_menu_view.assert_awaited_once()
    assert embed is fake_embed
    assert view is fake_view


@pytest.mark.asyncio
async def test_subsystem_route_falls_back_to_command_list_on_hook_failure(monkeypatch):
    """If a cog's ``build_help_menu_view`` raises, the resolver must
    fall back to the command-list embed rather than crashing.
    """
    opener = _opener()
    route = help_cog._resolve_route("blackjack", bot=opener.client)

    fake_cog = MagicMock()
    fake_cog.build_help_menu_view = AsyncMock(side_effect=RuntimeError("boom"))
    fake_cog.qualified_name = "BlackjackCog"
    fake_cog.get_commands = MagicMock(return_value=[])

    monkeypatch.setattr(help_cog, "_cog_for_subsystem", lambda _bot, _key: fake_cog)
    embed, view = await help_cog._open_route(
        route,
        opener,
        visible_subsystems={"blackjack"},
        member_tier="user",
    )
    assert view is None  # command-list fallback is embed-only
    assert isinstance(embed, discord.Embed)


# ---------------------------------------------------------------------------
# Advanced route — opens HelpPanelView
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_help_advanced_opens_help_panel_view():
    """``!help advanced`` opens the paginated HelpPanelView."""
    opener = _opener()
    route = help_cog._resolve_route("advanced", bot=opener.client)
    assert route.kind == "advanced"

    embed, view = await help_cog._open_route(
        route,
        opener,
        visible_subsystems={"games", "economy"},
        member_tier="user",
    )
    assert isinstance(view, help_cog.HelpPanelView)
    assert isinstance(embed, discord.Embed)


# ---------------------------------------------------------------------------
# Command route — single-command embed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_help_command_name_returns_single_command_embed():
    """``!help <command>`` returns the single-command help embed."""
    opener = _opener()
    fake_cmd = MagicMock()
    fake_cmd.name = "daily"
    fake_cmd.aliases = []
    fake_cmd.signature = ""
    fake_cmd.help = "Claim your daily reward."
    opener.client.get_command = MagicMock(return_value=fake_cmd)

    route = help_cog._resolve_route("daily", bot=opener.client)
    assert route.kind == "command"

    embed, view = await help_cog._open_route(
        route,
        opener,
        visible_subsystems=set(),
        member_tier="user",
    )
    assert view is None
    assert "daily" in (embed.title or "")


# ---------------------------------------------------------------------------
# Unknown route — not-found fallback
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unknown_name_returns_not_found_embed():
    opener = _opener()
    opener.client.get_command = MagicMock(return_value=None)
    route = help_cog._resolve_route("not-a-real-thing", bot=opener.client)
    assert route.kind == "unknown"

    embed, view = await help_cog._open_route(
        route,
        opener,
        visible_subsystems=set(),
        member_tier="user",
    )
    assert view is None
    assert "not-a-real-thing" in (embed.description or "")
