"""Unit tests for :class:`cogs.games_cog.GamesCog` (Phase 3).

The cog is a router-only thin wrapper that opens :class:`GamesHubView`.
These tests assert the contract surfaces:

* ``!games`` is registered as a prefix command.
* ``build_help_menu_view`` returns the expected (embed, view) shape.
* The cog contains no command alias claiming any game's command name —
  game logic stays in the original cogs.
"""

from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest
from discord.ext import commands

from cogs.games_cog import GamesCog
from governance.models import VisibilityResult
from utils.subsystem_registry import SUBSYSTEMS
from views.games.hub import GamesHubView


def _author(id_: int = 1) -> MagicMock:
    author = MagicMock(spec=discord.Member)
    author.id = id_
    return author


def _cog() -> GamesCog:
    bot = MagicMock(spec=commands.Bot)
    return GamesCog(bot)


@contextmanager
def _all_visible():
    """Patch resolve_visibility to return every subsystem visible.

    PR D: `build_games_hub_panel` resolves governance internally before
    constructing the view. Tests that don't exercise the governance
    surface still need this so the factory doesn't try to hit the DB.
    """
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


def test_cog_registers_games_command():
    cog = _cog()
    command_names = {cmd.name for cmd in cog.get_commands()}
    assert "games" in command_names


def test_cog_owns_no_game_subcommands():
    """The hub must not steal a game-specific command name."""
    cog = _cog()
    reserved = {
        "blackjack",
        "bj",
        "deathmatch",
        "dm",
        "rps",
        "mine",
        "minemenu",
        "countingmenu",
        "chainmenu",
        "chain",
    }
    command_names: set[str] = set()
    for cmd in cog.get_commands():
        command_names.add(cmd.name)
        command_names.update(cmd.aliases)
    assert command_names.isdisjoint(reserved), (
        f"GamesCog registered reserved game commands: "
        f"{command_names & reserved}"
    )


@pytest.mark.asyncio
async def test_build_help_menu_view_returns_embed_and_view():
    cog = _cog()
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = _author()
    interaction.guild = MagicMock()
    interaction.guild_id = 42
    interaction.channel = MagicMock()
    interaction.client = MagicMock()

    with _all_visible():
        embed, view = await cog.build_help_menu_view(interaction)

    assert isinstance(embed, discord.Embed)
    assert isinstance(view, GamesHubView)


@pytest.mark.asyncio
async def test_games_command_sends_panel():
    cog = _cog()
    ctx = MagicMock(spec=commands.Context)
    ctx.author = _author()
    ctx.guild = MagicMock()
    ctx.channel = MagicMock()
    ctx.message = MagicMock()
    ctx.message.author = ctx.author
    ctx.send = AsyncMock(return_value=MagicMock(spec=discord.Message))

    # Invoke the underlying callback directly so we don't need a real bot.
    with _all_visible():
        await cog.games_menu.callback(cog, ctx)

    ctx.send.assert_awaited_once()
    _args, kwargs = ctx.send.call_args
    assert isinstance(kwargs["view"], GamesHubView)
    assert isinstance(kwargs["embed"], discord.Embed)
