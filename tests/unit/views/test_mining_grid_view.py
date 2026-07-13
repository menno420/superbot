"""Grid Mine navigator view (hub-redesign PR 3) — dig-moves-you model.

Owner model (post-#1281): every dig is locomotion — a directional dig moves you into
the adjacent cell and mines it.  Pins:

- the navigator's button surface (six directional dig buttons + nav, no Mine-here);
- ``build_grid_embed`` renders position / depth / seed / map;
- a dig routes through ``mining_workflow.dig`` and re-renders in place with the loot;
- a blocked dig surfaces the hint;
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


def test_view_carries_six_directional_dig_buttons_plus_nav():
    view = MineGridView(MagicMock(id=1), guild_id=2)
    labels = " | ".join(b.label or "" for b in _buttons(view))
    for token in ("North", "South", "East", "West", "Deeper", "Up"):
        assert token in labels, f"missing {token!r} dig button"
    # The separate "Mine here" button is gone — digging IS moving now.
    assert "Mine here" not in labels
    assert "Mining Menu" in labels
    assert "Help" in labels


def test_view_locks_to_invoking_user():
    view = MineGridView(MagicMock(id=42), guild_id=2)
    assert view.user_id == 42
    assert view.guild_id == 2


def test_dpad_layout_rows():
    view = MineGridView(MagicMock(id=1), guild_id=2)
    assert _find_button(view, "North").row == 0
    assert _find_button(view, "West").row == 1
    assert _find_button(view, "East").row == 1
    assert _find_button(view, "South").row == 2
    assert _find_button(view, "Deeper").row == 3
    assert _find_button(view, "Up").row == 3


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
        get_energy=AsyncMock(return_value=(60, 0)),
        get_equipment=AsyncMock(return_value={}),
        get_skills=AsyncMock(return_value={}),
    ):
        embed = await build_grid_embed(1, 2)
    field_names = [f.name for f in embed.fields]
    assert any("Depth" in n for n in field_names)
    assert any("Position" in n for n in field_names)
    assert any("Energy" in n for n in field_names)
    seed_field = next(f for f in embed.fields if "seed" in f.name.lower())
    assert "4242" in seed_field.value
    map_field = next(f for f in embed.fields if "Map" in f.name)
    assert grid.PLAYER_GLYPH in map_field.value


@pytest.mark.asyncio
async def test_build_grid_embed_passes_int_user_id_to_bigint_keyed_reads():
    """Regression: ``!mine`` crashed because ``build_grid_embed`` passed the
    *stringified* user id to ``db.get_skills`` — but ``player_skills`` is keyed on
    a BIGINT ``user_id`` (shared with game_xp), so asyncpg raised ``DataError`` on
    every dig-navigator open.  The mining tables above it (``mining_player_state``,
    ``mining_equipment``, ``mining_discovered``) use a TEXT ``user_id`` and take the
    string.  Pin BOTH halves of that split so neither side regresses; a mocked
    ``db`` can't surface the type mismatch, only this call-arg contract can.
    """
    reads = {
        name: AsyncMock(return_value=default)
        for name, default in (
            ("get_depth", 0),
            ("get_position", (0, 0)),
            ("get_world_seed", 4242),
            ("get_discovered_window", set()),
            ("get_energy", (60, 0)),
            ("get_equipment", {}),
            ("get_skills", {}),
        )
    }
    with patch.multiple("views.mining.grid_mine_view.db", **reads):
        await build_grid_embed(1234, 5678)

    # BIGINT-keyed read → the raw int user id (the exact bug).
    assert reads["get_skills"].await_args.args[0] == 1234
    assert isinstance(reads["get_skills"].await_args.args[0], int)
    # TEXT-keyed mining reads → the stringified id (must stay a str).
    for text_keyed in ("get_depth", "get_position", "get_equipment", "get_energy"):
        arg = reads[text_keyed].await_args.args[0]
        assert arg == "1234", f"{text_keyed} should receive the str user id, got {arg!r}"
        assert isinstance(arg, str)


@pytest.mark.asyncio
async def test_build_grid_embed_widens_window_with_a_brighter_light():
    # A diamond-lantern-grade light (light_radius 3 → reveal radius 4, BUG-0026)
    # widens the discovered-cell query beyond the base 2 — proving the stat is wired.
    from utils.equipment import EffectiveStats

    window = AsyncMock(return_value=set())
    with patch.multiple(
        "views.mining.grid_mine_view.db",
        get_depth=AsyncMock(return_value=0),
        get_position=AsyncMock(return_value=(0, 0)),
        get_world_seed=AsyncMock(return_value=4242),
        get_discovered_window=window,
        get_energy=AsyncMock(return_value=(60, 0)),
        get_equipment=AsyncMock(return_value={"light": "diamond lantern"}),
        get_skills=AsyncMock(return_value={}),
    ), patch(
        "views.mining.grid_mine_view.character_stats",
        return_value=EffectiveStats(light_radius=3),
    ):
        await build_grid_embed(1, 2)
    # get_discovered_window(suid, guild, depth, x-R, x+R, y-R, y+R) — R must be 4.
    assert window.await_args.args[3:7] == (-4, 4, -4, 4)


# ---------------------------------------------------------------------------
# Dig routing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_north_dig_routes_through_workflow_and_rerenders():
    view = MineGridView(MagicMock(id=1), guild_id=2)
    btn = _find_button(view, "North")
    interaction = MagicMock()

    dig_result = mining_workflow.DigResult(
        moved=True,
        x=0,
        y=1,
        depth=0,
        found="stone",
        amount=2,
        wear=WearReport(),
    )
    with (
        patch(
            "views.mining.grid_mine_view.safe_defer",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "views.mining.grid_mine_view.mining_workflow.dig",
            new_callable=AsyncMock,
            return_value=dig_result,
        ) as dig,
        patch(
            "views.mining.grid_mine_view.build_grid_embed",
            new_callable=AsyncMock,
            return_value=discord.Embed(title="map"),
        ) as build,
        patch(
            "views.mining.grid_mine_view.safe_edit",
            new_callable=AsyncMock,
            return_value=True,
        ) as edit,
    ):
        await btn.callback(interaction)

    dig.assert_awaited_once_with(1, 2, grid.NORTH)
    note = build.await_args.kwargs["note"]
    assert "2× stone" in note
    assert "north" in note
    edit.assert_awaited_once()
    assert edit.await_args.kwargs["view"] is view  # re-renders in place


@pytest.mark.asyncio
async def test_deeper_dig_routes_down_and_shows_cell_note():
    view = MineGridView(MagicMock(id=1), guild_id=2)
    btn = _find_button(view, "Deeper")
    interaction = MagicMock()

    dig_result = mining_workflow.DigResult(
        moved=True,
        x=0,
        y=0,
        depth=1,
        found="gold",
        amount=4,
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
            "views.mining.grid_mine_view.mining_workflow.dig",
            new_callable=AsyncMock,
            return_value=dig_result,
        ) as dig,
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

    dig.assert_awaited_once_with(1, 2, grid.DOWN)
    note = build.await_args.kwargs["note"]
    assert "deeper" in note
    assert "4× gold" in note
    assert "rich gold vein" in note


@pytest.mark.asyncio
async def test_blocked_dig_surfaces_the_hint():
    view = MineGridView(MagicMock(id=1), guild_id=2)
    btn = _find_button(view, "Deeper")
    interaction = MagicMock()

    blocked = mining_workflow.DigResult(
        moved=False,
        x=0,
        y=0,
        depth=0,
        found=None,
        amount=0,
        wear=WearReport(),
        hint="Equip a brighter light to descend.",
    )
    with (
        patch(
            "views.mining.grid_mine_view.safe_defer",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "views.mining.grid_mine_view.mining_workflow.dig",
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
