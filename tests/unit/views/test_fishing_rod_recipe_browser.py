"""fishing rod recipe browser — the live-progress panel (S1 follow-up to #1515).

Pins that the browser shows every craftable tier with the player's eligible-fish
progress (not just the bare requirement), only enables Craft for the immediate
next tier, and round-trips back to the rod shop. Discord I/O is mocked.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services import fishing_workflow
from utils.fishing import rods as rods_mod
from views.fishing.rod_recipe_browser import (
    RodRecipeBrowserView,
    build_recipe_panel,
    build_rod_recipe_embed,
)


def _author(user_id: int = 1) -> MagicMock:
    author = MagicMock()
    author.id = user_id
    author.display_name = "Anya"
    return author


def _interaction(user_id: int = 1) -> MagicMock:
    interaction = MagicMock()
    interaction.user = _author(user_id)
    interaction.message = MagicMock()
    interaction.response.edit_message = AsyncMock()
    interaction.response.send_message = AsyncMock()
    return interaction


# ---------------------------------------------------------------------------
# build_rod_recipe_embed — pure embed assembly
# ---------------------------------------------------------------------------


def test_owned_tiers_show_as_already_wielded():
    embed = build_rod_recipe_embed(current_tier=2, eligible={})
    blob = embed.fields[0].value
    assert "✅" in blob and "Bronze Rod" in blob
    assert "✅" in blob and "Silver Rod" in blob


def test_next_tier_shows_live_progress_toward_its_requirement():
    # Tier 1 recipe needs 10 fish; player has 7 eligible.
    embed = build_rod_recipe_embed(current_tier=0, eligible={1: 7})
    blob = embed.fields[0].value
    assert "7/10 eligible fish" in blob
    assert "ready to craft" not in blob


def test_next_tier_flags_ready_to_craft_once_the_requirement_is_met():
    embed = build_rod_recipe_embed(current_tier=0, eligible={1: 12})
    blob = embed.fields[0].value
    # progress caps display at the requirement even when the player has more
    assert "10/10 eligible fish" in blob
    assert "ready to craft!" in blob


def test_further_out_tiers_are_locked_not_next():
    embed = build_rod_recipe_embed(current_tier=0, eligible={2: 99})
    blob = embed.fields[0].value
    # tier 2 isn't the immediate next tier (tier 1 is), so it stays locked
    # even though the player happens to have plenty of size-≤12 fish.
    silver_line = next(line for line in blob.splitlines() if "Silver Rod" in line)
    assert silver_line.startswith("🔒")


def test_top_tier_owner_sees_no_next_marker():
    embed = build_rod_recipe_embed(current_tier=rods_mod.MAX_TIER, eligible={})
    blob = embed.fields[0].value
    assert "**▶**" not in blob
    assert blob.count("✅") == len(rods_mod.ROD_RECIPES)


# ---------------------------------------------------------------------------
# build_recipe_panel — the async embed+view assembly shared by command/button
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_build_recipe_panel_assembles_from_live_state():
    with (
        patch(
            "views.fishing.rod_recipe_browser.db.get_rod_tier",
            AsyncMock(return_value=1),
        ),
        patch(
            "views.fishing.rod_recipe_browser.db.get_mining_inventory",
            AsyncMock(return_value={"perch": 5}),
        ),
    ):
        embed, view = await build_recipe_panel(_author(), 1)

    assert isinstance(view, RodRecipeBrowserView)
    assert view.craft_btn.disabled is False  # tier 1 owned, tier 2 still craftable
    blob = embed.fields[0].value
    assert "Silver Rod" in blob


# ---------------------------------------------------------------------------
# RodRecipeBrowserView — craft + back navigation
# ---------------------------------------------------------------------------


def test_top_tier_disables_the_craft_button():
    view = RodRecipeBrowserView(_author(), 1, at_max=True)
    assert view.craft_btn.disabled is True


@pytest.mark.asyncio
async def test_craft_button_calls_craft_rod_and_rerenders():
    view = RodRecipeBrowserView(_author(7), 1, at_max=False)
    interaction = _interaction(7)
    with (
        patch.object(
            fishing_workflow,
            "craft_rod",
            AsyncMock(
                return_value=fishing_workflow.RodCraftResult(True, "Crafted!", tier=1),
            ),
        ) as craft,
        patch(
            "views.fishing.rod_recipe_browser.db.get_mining_inventory",
            AsyncMock(return_value={}),
        ),
        patch("views.fishing.rod_recipe_browser.safe_defer", AsyncMock(return_value=True)),
        patch("views.fishing.rod_recipe_browser.safe_edit", AsyncMock()) as edit,
    ):
        await type(view).craft_btn(view, interaction, MagicMock())

    craft.assert_awaited_once_with(7, 1)
    edit.assert_awaited_once()
    # crafted into tier 1 (not the top) — the next tier (2) keeps Craft live
    assert view.craft_btn.disabled is False


@pytest.mark.asyncio
async def test_back_button_returns_to_the_rod_shop():
    from views.fishing.rod_shop import RodShopView

    view = RodRecipeBrowserView(_author(7), 99, at_max=False)
    interaction = _interaction(7)
    with (
        patch(
            "views.fishing.rod_recipe_browser.db.get_rod_tier",
            AsyncMock(return_value=0),
        ),
        patch(
            "views.fishing.rod_recipe_browser.db.get_coins",
            AsyncMock(return_value=0),
        ),
        patch(
            "views.fishing.rod_recipe_browser.safe_defer",
            AsyncMock(return_value=True),
        ),
        patch(
            "views.fishing.rod_recipe_browser.safe_edit",
            AsyncMock(),
        ) as edit,
    ):
        await type(view).back_btn(view, interaction, MagicMock())

    edit.assert_awaited_once()
    _, kwargs = edit.await_args
    assert isinstance(kwargs["view"], RodShopView)
