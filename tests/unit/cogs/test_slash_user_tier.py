"""Unit tests for the user-tier slash front doors (PR E1).

Pins the contract for ``/games``, ``/economy``, ``/community``, and
``/utility``:

* Each slash command is registered on its owning cog.
* Each callback returns ephemerally — slash hubs are personal
  panels per the ``/help`` convention.
* ``/games`` and ``/community`` route through the PR D factory so
  governance filtering applies identically to the slash entry.
* ``/economy`` and ``/utility`` route through ``build_help_menu_view``
  so the slash entry uses the same builder as the help-routed entry.
* No business-logic duplication — each callback delegates and
  surfaces the existing panel.
"""

from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest
from discord.ext import commands

from cogs.community_cog import CommunityCog
from cogs.economy_cog import EconomyCog
from cogs.games_cog import GamesCog
from cogs.utility_cog import UtilityCog
from governance.models import VisibilityResult
from utils.subsystem_registry import SUBSYSTEMS


def _interaction(user_id: int = 1) -> MagicMock:
    interaction = MagicMock(spec=discord.Interaction)
    user = MagicMock(spec=discord.Member)
    user.id = user_id
    interaction.user = user
    interaction.guild = MagicMock()
    interaction.guild_id = 42
    interaction.channel = MagicMock()
    interaction.client = MagicMock()
    interaction.response = MagicMock()
    interaction.response.is_done = MagicMock(return_value=False)
    interaction.response.send_message = AsyncMock()
    interaction.response.defer = AsyncMock()
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock()
    interaction.original_response = AsyncMock(return_value=MagicMock())
    return interaction


@contextmanager
def _all_visible():
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
        yield


# ---------------------------------------------------------------------------
# Slash commands exist on their owning cogs
# ---------------------------------------------------------------------------


def test_games_cog_has_slash_command():
    cog = GamesCog(MagicMock(spec=commands.Bot))
    app_command_names = {cmd.name for cmd in cog.walk_app_commands()}
    assert "games" in app_command_names


def test_economy_cog_has_slash_command():
    cog = EconomyCog(MagicMock(spec=commands.Bot))
    app_command_names = {cmd.name for cmd in cog.walk_app_commands()}
    assert "economy" in app_command_names


def test_community_cog_has_slash_command():
    cog = CommunityCog(MagicMock(spec=commands.Bot))
    app_command_names = {cmd.name for cmd in cog.walk_app_commands()}
    assert "community" in app_command_names


def test_utility_cog_has_slash_command():
    cog = UtilityCog(MagicMock(spec=commands.Bot))
    app_command_names = {cmd.name for cmd in cog.walk_app_commands()}
    assert "utility" in app_command_names


# ---------------------------------------------------------------------------
# /games — routes through the PR D factory, ephemeral
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_games_slash_responds_ephemerally_through_factory():
    cog = GamesCog(MagicMock(spec=commands.Bot))
    interaction = _interaction()
    with _all_visible():
        await cog.games_slash.callback(cog, interaction)

    interaction.response.send_message.assert_awaited_once()
    _args, kwargs = interaction.response.send_message.call_args
    assert kwargs.get("ephemeral") is True
    assert isinstance(kwargs.get("embed"), discord.Embed)
    # The view returned by build_games_hub_panel is a GamesHubView; verify
    # the slash callback didn't replace it with a different surface.
    from views.games.hub import GamesHubView

    assert isinstance(kwargs.get("view"), GamesHubView)


# ---------------------------------------------------------------------------
# /community — routes through the PR D factory, ephemeral
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_community_slash_responds_ephemerally_through_factory():
    cog = CommunityCog(MagicMock(spec=commands.Bot))
    interaction = _interaction()
    with _all_visible():
        await cog.community_slash.callback(cog, interaction)

    interaction.response.send_message.assert_awaited_once()
    _args, kwargs = interaction.response.send_message.call_args
    assert kwargs.get("ephemeral") is True
    assert isinstance(kwargs.get("embed"), discord.Embed)
    from views.community.hub import CommunityHubView

    assert isinstance(kwargs.get("view"), CommunityHubView)


# ---------------------------------------------------------------------------
# /economy — routes through build_help_menu_view, ephemeral
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_economy_slash_defers_then_followups_ephemerally():
    cog = EconomyCog(MagicMock(spec=commands.Bot))
    interaction = _interaction()

    fake_embed = discord.Embed(title="Economy")
    fake_view = discord.ui.View()

    with patch.object(
        cog,
        "build_help_menu_view",
        AsyncMock(return_value=(fake_embed, fake_view)),
    ), patch(
        "cogs.economy_cog.safe_defer",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock_defer, patch(
        "cogs.economy_cog.safe_followup",
        new_callable=AsyncMock,
    ) as mock_followup:
        await cog.economy_slash.callback(cog, interaction)

    mock_defer.assert_awaited_once_with(interaction, ephemeral=True)
    mock_followup.assert_awaited_once()
    _args, kwargs = mock_followup.call_args
    assert kwargs.get("embed") is fake_embed
    assert kwargs.get("view") is fake_view
    assert kwargs.get("ephemeral") is True


@pytest.mark.asyncio
async def test_economy_slash_bails_when_defer_fails():
    """If ``safe_defer`` reports False (token expired or HTTP failure),
    the slash callback must abort without calling ``followup`` or
    ``build_help_menu_view``.
    """
    cog = EconomyCog(MagicMock(spec=commands.Bot))
    interaction = _interaction()

    with patch.object(
        cog,
        "build_help_menu_view",
        new_callable=AsyncMock,
    ) as mock_hook, patch(
        "cogs.economy_cog.safe_defer",
        new_callable=AsyncMock,
        return_value=False,
    ), patch(
        "cogs.economy_cog.safe_followup",
        new_callable=AsyncMock,
    ) as mock_followup:
        await cog.economy_slash.callback(cog, interaction)

    mock_hook.assert_not_awaited()
    mock_followup.assert_not_awaited()


# ---------------------------------------------------------------------------
# /utility — routes through build_help_menu_view, ephemeral
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_utility_slash_responds_ephemerally_via_hook():
    cog = UtilityCog(MagicMock(spec=commands.Bot))
    interaction = _interaction()

    fake_embed = discord.Embed(title="Utility")
    fake_view = discord.ui.View()

    with patch.object(
        cog,
        "build_help_menu_view",
        AsyncMock(return_value=(fake_embed, fake_view)),
    ):
        await cog.utility_slash.callback(cog, interaction)

    interaction.response.send_message.assert_awaited_once()
    _args, kwargs = interaction.response.send_message.call_args
    assert kwargs.get("embed") is fake_embed
    assert kwargs.get("view") is fake_view
    assert kwargs.get("ephemeral") is True


# ---------------------------------------------------------------------------
# Each slash callback exists and reuses the existing panel-builder
# ---------------------------------------------------------------------------


def test_slash_callbacks_have_descriptions():
    """The /slash UI surfaces command descriptions in Discord's
    autocomplete. Pin that every user-tier front door has a non-empty
    description so operators see what each command does.
    """
    cogs = [
        GamesCog(MagicMock(spec=commands.Bot)),
        EconomyCog(MagicMock(spec=commands.Bot)),
        CommunityCog(MagicMock(spec=commands.Bot)),
        UtilityCog(MagicMock(spec=commands.Bot)),
    ]
    seen: set[str] = set()
    for cog in cogs:
        for cmd in cog.walk_app_commands():
            if cmd.name in {"games", "economy", "community", "utility"}:
                seen.add(cmd.name)
                assert cmd.description, (
                    f"/{cmd.name} has empty description — Discord requires "
                    f"a non-empty description on slash commands."
                )
    assert seen == {"games", "economy", "community", "utility"}
