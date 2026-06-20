"""Read-only Character overview aggregates position, gear, coins, net worth."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from views.mining.character_panel import (
    _gear_overview,
    build_character_doll,
    build_character_embed,
)
from views.mining.main_panel import MiningHubView


def test_hub_has_character_button():
    ids = {getattr(c, "custom_id", None) for c in MiningHubView().children}
    assert "mining:character" in ids


@pytest.mark.asyncio
async def test_build_character_embed_aggregates_every_owner():
    with patch(
        "views.mining.character_panel.db.get_mining_inventory",
        new_callable=AsyncMock,
        return_value={"diamond": 2},
    ), patch(
        "views.mining.character_panel.db.get_equipment",
        new_callable=AsyncMock,
        return_value={"tool": "iron pickaxe", "weapon": "iron sword"},
    ), patch(
        "views.mining.character_panel.db.get_gear_wear",
        new_callable=AsyncMock,
        return_value={"iron pickaxe": 42},
    ), patch(
        "views.mining.character_panel.db.get_depth",
        new_callable=AsyncMock,
        return_value=2,
    ), patch(
        "views.mining.character_panel.db.get_max_depth",
        new_callable=AsyncMock,
        return_value=2,
    ), patch(
        "views.mining.character_panel.db.get_coins",
        new_callable=AsyncMock,
        return_value=150,
    ), patch(
        "views.mining.character_panel.game_xp_service.level_info",
        new_callable=AsyncMock,
        return_value=(3, 40, 145),
    ), patch(
        "views.mining.character_panel.title_service.equipped_title",
        new_callable=AsyncMock,
        return_value=None,
    ):
        embed = await build_character_embed(123, 7, name="Digger")

    blob = embed.title + " " + " ".join(f"{f.name} {f.value}" for f in embed.fields)
    assert "Digger" in embed.title
    assert "Deep" in blob  # depth 2 → the Deep (world.describe_position)
    assert "Iron Pickaxe" in blob  # equipped tool
    assert "Iron Sword" in blob  # equipped weapon
    assert "+4" in blob  # iron pickaxe mining_power
    assert "+6" in blob  # iron sword damage
    assert "150" in blob  # coins
    assert "24" in blob  # net worth = diamond value (12) × 2
    assert "Level **3**" in blob  # shared game level (game_xp_service)
    assert "Deepest" in blob  # the 065 depth record
    # No title equipped → no description (byte-identical to the pre-titles card).
    assert not embed.description


@pytest.mark.asyncio
async def test_character_embed_shows_equipped_title_when_set():
    from utils.mining import titles

    title = titles.get_title("the_deep")
    with patch(
        "views.mining.character_panel.db.get_mining_inventory",
        new_callable=AsyncMock,
        return_value={},
    ), patch(
        "views.mining.character_panel.db.get_equipment",
        new_callable=AsyncMock,
        return_value={},
    ), patch(
        "views.mining.character_panel.db.get_gear_wear",
        new_callable=AsyncMock,
        return_value={},
    ), patch(
        "views.mining.character_panel.db.get_depth",
        new_callable=AsyncMock,
        return_value=0,
    ), patch(
        "views.mining.character_panel.db.get_max_depth",
        new_callable=AsyncMock,
        return_value=0,
    ), patch(
        "views.mining.character_panel.db.get_coins",
        new_callable=AsyncMock,
        return_value=0,
    ), patch(
        "views.mining.character_panel.game_xp_service.level_info",
        new_callable=AsyncMock,
        return_value=(1, 0, 100),
    ), patch(
        "views.mining.character_panel.title_service.equipped_title",
        new_callable=AsyncMock,
        return_value=title,
    ):
        embed = await build_character_embed(123, 7, name="Digger")

    assert embed.description and "the Deep One" in embed.description


def test_gear_overview_lists_names_without_durability():
    """The Character card keeps gear high-level — equipped item names only, no
    per-slot durability fraction (that detail lives in !gear; the paper-doll is
    the visual)."""
    from utils import equipment

    summary = _gear_overview(
        {equipment.TOOL: "iron pickaxe", equipment.WEAPON: "iron sword"},
    )
    assert "Iron Pickaxe" in summary
    assert "Iron Sword" in summary
    # The item-names line carries no per-slot durability fraction like (42/320)
    # (a set-progress line further down may legitimately read "1/6 pieces").
    names_line = summary.splitlines()[0]
    assert "/" not in names_line
    assert "(" not in names_line


def test_gear_overview_empty_state_points_at_gear():
    summary = _gear_overview({})
    assert "gear" in summary.lower()


def test_gear_overview_shows_active_set_bonus():
    """When a full same-tier set is worn, the overview surfaces the set bonus
    line (still high-level — no durability)."""
    from utils import equipment

    full_set = {slot: f"diamond {slot}" for slot in equipment.SET_SLOTS}
    summary = _gear_overview(full_set)
    if equipment.active_set_tier(full_set) is not None:
        assert "set" in summary.lower()


@pytest.mark.asyncio
async def test_build_character_doll_renders_equipped_loadout():
    """The character image is the V-16 paper-doll — build_character_doll feeds
    the equipped loadout + Home backdrop into render_character_for."""
    with patch(
        "views.mining.character_panel.db.get_equipment",
        new_callable=AsyncMock,
        return_value={"weapon": "iron sword"},
    ), patch(
        "views.mining.character_panel.db.get_structures",
        new_callable=AsyncMock,
        return_value={},
    ), patch(
        "utils.character_render.render_character_for",
        return_value=b"PNGDATA",
    ) as mock_render:
        png = await build_character_doll(123, 7)

    assert png == b"PNGDATA"
    mock_render.assert_called_once()
    # The equipped loadout is what gets rendered (the same figure !gear shows).
    assert mock_render.call_args.args[0] == {"weapon": "iron sword"}
