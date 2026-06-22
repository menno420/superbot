"""Grid Mine navigator view (hub-redesign PR 3).

Replaces the old MineView descent/navigation tests (the linear Descend/Ascend view
was removed).  Pins:

- the navigator's button surface (six movement buttons + Mine here + nav);
- ``build_grid_embed`` renders position / depth / seed / map;
- movement and Mine here route through ``mining_workflow`` and re-render in place;
- Mining Menu returns to the hub; Help dispatches (with a fallback).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from services import mining_workflow
from utils.mining import grid
from utils.mining.workshop import WearReport
from views.mining.grid_mine_view import MineGridView, build_grid_embed


def _buttons(view: discord.ui.View) -> list[discord.ui.Button]:
    return [c for c in view.children if isinstance(c, discord.ui.Button)]


def _find_button(view: discord.ui.View, label_substr: str) -> discord.ui.Button:
    for child in view.children:
        if isinstance(child, discord.ui.Button) and label_substr in (child.label or ""):
            return child
    raise AssertionError(f"No button with label containing {label_substr!r}")


# ---------------------------------------------------------------------------
# Button surface
# ---------------------------------------------------------------------------


def test_view_carries_six_movement_buttons_plus_mine_here_and_nav():
    view = MineGridView(MagicMock(id=1), guild_id=2)
    labels = " | ".join(b.label or "" for b in _buttons(view))
    for token in ("North", "South", "East", "West", "Up", "Down", "Mine here"):
        assert token in labels, f"missing {token!r} button"
    assert "Mining Menu" in labels
    assert "Help" in labels


def test_view_locks_to_invoking_user():
    view = MineGridView(MagicMock(id=42), guild_id=2)
    assert view.user_id == 42
    assert view.guild_id == 2


def test_dpad_layout_rows():
    view = MineGridView(MagicMock(id=1), guild_id=2)
    assert _find_button(view, "North").row == 0
    assert _find_button(view, "Mine here").row == 1
    assert _find_button(view, "South").row == 2
    assert _find_button(view, "Down").row == 3


# ---------------------------------------------------------------------------
# build_grid_embed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_build_grid_embed_shows_position_depth_seed_and_map():
    with patch.multiple(
        "views.mining.grid_mine_view.db",
        get_depth=AsyncMock(return_value=0),
        get_position=AsyncMock(return_value=(0, 0)),
        get_world_seed=AsyncMock(return_value=4242),
        get_discovered_window=AsyncMock(return_value=set()),
    ):
        embed = await build_grid_embed(1, 2)
    field_names = [f.name for f in embed.fields]
    assert any("Depth" in n for n in field_names)
    assert any("Position" in n for n in field_names)
    seed_field = next(f for f in embed.fields if "seed" in f.name.lower())
    assert "4242" in seed_field.value
    map_field = next(f for f in embed.fields if "Map" in f.name)
    assert grid.PLAYER_GLYPH in map_field.value


# ---------------------------------------------------------------------------
# Movement routing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_north_button_routes_through_workflow_and_rerenders():
    view = MineGridView(MagicMock(id=1), guild_id=2)
    btn = _find_button(view, "North")
    interaction = MagicMock()

    move_result = mining_workflow.MoveResult(
        moved=True,
        x=0,
        y=1,
        depth=0,
        note="You head north.",
    )
    with (
        patch(
            "views.mining.grid_mine_view.safe_defer",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "views.mining.grid_mine_view.mining_workflow.move",
            new_callable=AsyncMock,
            return_value=move_result,
        ) as move,
        patch(
            "views.mining.grid_mine_view.build_grid_embed",
            new_callable=AsyncMock,
            return_value=discord.Embed(title="map"),
        ),
        patch(
            "views.mining.grid_mine_view.safe_edit",
            new_callable=AsyncMock,
            return_value=True,
        ) as edit,
    ):
        await btn.callback(interaction)

    move.assert_awaited_once_with(1, 2, grid.NORTH)
    edit.assert_awaited_once()
    assert edit.await_args.kwargs["view"] is view  # re-renders in place


@pytest.mark.asyncio
async def test_blocked_move_surfaces_hint_in_the_note():
    view = MineGridView(MagicMock(id=1), guild_id=2)
    btn = _find_button(view, "Down")
    interaction = MagicMock()

    blocked = mining_workflow.MoveResult(
        moved=False,
        x=0,
        y=0,
        depth=0,
        note="You can't dig any deeper here.",
        hint="Equip a brighter light.",
    )
    with (
        patch(
            "views.mining.grid_mine_view.safe_defer",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "views.mining.grid_mine_view.mining_workflow.move",
            new_callable=AsyncMock,
            return_value=blocked,
        ),
        patch(
            "views.mining.grid_mine_view.build_grid_embed",
            new_callable=AsyncMock,
            return_value=discord.Embed(title="map"),
        ) as build,
        patch(
            "views.mining.grid_mine_view.safe_edit",
            new_callable=AsyncMock,
            return_value=True,
        ),
    ):
        await btn.callback(interaction)

    note = build.await_args.kwargs["note"]
    assert "brighter light" in note


# ---------------------------------------------------------------------------
# Mine here routing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mine_here_button_grants_loot_and_shows_cell_note():
    view = MineGridView(MagicMock(id=1), guild_id=2)
    btn = _find_button(view, "Mine here")
    interaction = MagicMock()

    result = mining_workflow.MineResult(
        found="gold",
        amount=4,
        depth=0,
        wear=WearReport(),
        cell_note="💎 You struck a rich gold vein!",
    )
    with (
        patch(
            "views.mining.grid_mine_view.safe_defer",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "views.mining.grid_mine_view.mining_workflow.mine_here",
            new_callable=AsyncMock,
            return_value=result,
        ) as mine_here,
        patch(
            "views.mining.grid_mine_view.build_grid_embed",
            new_callable=AsyncMock,
            return_value=discord.Embed(title="map"),
        ) as build,
        patch(
            "views.mining.grid_mine_view.safe_edit",
            new_callable=AsyncMock,
            return_value=True,
        ),
    ):
        await btn.callback(interaction)

    mine_here.assert_awaited_once_with(1, 2)
    note = build.await_args.kwargs["note"]
    assert "gold" in note
    assert "rich gold vein" in note


# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_menu_button_returns_to_mining_hub():
    view = MineGridView(MagicMock(id=1), guild_id=2)
    btn = _find_button(view, "Mining Menu")
    interaction = MagicMock()
    interaction.user.display_name = "tester"

    with (
        patch(
            "views.mining.grid_mine_view.safe_defer",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "views.mining.main_panel.build_overview_embed",
            new_callable=AsyncMock,
            return_value=discord.Embed(title="⛏️ Mining Hub"),
        ),
        patch(
            "views.mining.grid_mine_view.safe_edit",
            new_callable=AsyncMock,
            return_value=True,
        ) as edit,
    ):
        await btn.callback(interaction)

    edit.assert_awaited_once()
    assert type(edit.await_args.kwargs["view"]).__name__ == "MiningHubView"


@pytest.mark.asyncio
async def test_help_button_dispatches_to_help_panel():
    view = MineGridView(MagicMock(id=1), guild_id=2)
    btn = _find_button(view, "Help")
    interaction = MagicMock()

    fake_view = discord.ui.View()
    fake_embed = discord.Embed(title="Help")
    with (
        patch(
            "views.mining.grid_mine_view.safe_defer",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "cogs.help_cog.resolve_help_panel_state",
            new_callable=AsyncMock,
            return_value=(fake_embed, fake_view),
        ),
        patch(
            "views.mining.grid_mine_view.safe_edit",
            new_callable=AsyncMock,
            return_value=True,
        ) as edit,
    ):
        await btn.callback(interaction)

    assert edit.await_args.kwargs["view"] is fake_view


@pytest.mark.asyncio
async def test_help_button_falls_back_on_failure():
    view = MineGridView(MagicMock(id=1), guild_id=2)
    btn = _find_button(view, "Help")
    interaction = MagicMock()

    with (
        patch(
            "views.mining.grid_mine_view.safe_defer",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "cogs.help_cog.resolve_help_panel_state",
            new_callable=AsyncMock,
            side_effect=RuntimeError("help down"),
        ),
        patch(
            "views.mining.grid_mine_view.safe_edit",
            new_callable=AsyncMock,
            return_value=True,
        ) as edit,
    ):
        await btn.callback(interaction)

    embed = edit.await_args.kwargs["embed"]
    assert "Help unavailable" in (embed.title or "")
    assert edit.await_args.kwargs["view"] is view
