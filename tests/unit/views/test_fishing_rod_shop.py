"""fishing rod shop — the buy + craft panel (the fish→rod craft button, #1508 follow-up).

Pins that the rod shop offers both paths up the ladder: the ⬆️ Upgrade (coins,
``buy_rod``) and the 🎣 Craft from fish (``craft_rod``) buttons, that the embed
advertises the craft cost, and that both buttons re-gate off at the top tier.
Discord I/O is mocked.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services import fishing_workflow
from utils.fishing import rods as rods_mod
from views.fishing.rod_shop import RodShopView, build_rod_embed


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


def test_embed_advertises_the_craft_cost_for_the_next_rod():
    embed = build_rod_embed(rods_mod.STARTER, rods_mod.next_rod(0), balance=100)
    blob = "\n".join(f.value for f in embed.fields)
    assert "craft from" in blob.lower()
    assert rods_mod.rod_recipe_text(rods_mod.rod_recipe(1)) in blob


def test_top_tier_disables_both_buy_and_craft():
    view = RodShopView(_author(), 1, at_max=True)
    assert view.upgrade_btn.disabled is True
    assert view.craft_btn.disabled is True


@pytest.mark.asyncio
async def test_craft_button_calls_craft_rod_and_rerenders():
    view = RodShopView(_author(7), 1, at_max=False)
    interaction = _interaction(7)
    with (
        patch.object(
            fishing_workflow,
            "craft_rod",
            AsyncMock(
                return_value=fishing_workflow.RodCraftResult(True, "Crafted!", tier=1)
            ),
        ) as craft,
        patch("views.fishing.rod_shop.db.get_coins", AsyncMock(return_value=0)),
        patch("views.fishing.rod_shop.safe_defer", AsyncMock(return_value=True)),
        patch("views.fishing.rod_shop.safe_edit", AsyncMock()) as edit,
    ):
        await type(view).craft_btn(view, interaction, MagicMock())

    craft.assert_awaited_once_with(7, 1)
    edit.assert_awaited_once()
    # crafting into tier 1 (not the top) leaves both buttons live
    assert view.craft_btn.disabled is False
    assert view.upgrade_btn.disabled is False


@pytest.mark.asyncio
async def test_recipes_button_opens_the_recipe_browser():
    from views.fishing.rod_recipe_browser import RodRecipeBrowserView

    view = RodShopView(_author(7), 1, at_max=False)
    interaction = _interaction(7)
    with (
        patch(
            "views.fishing.rod_recipe_browser.db.get_rod_tier",
            AsyncMock(return_value=0),
        ),
        patch(
            "views.fishing.rod_recipe_browser.db.get_mining_inventory",
            AsyncMock(return_value={}),
        ),
        patch("views.fishing.rod_shop.safe_defer", AsyncMock(return_value=True)),
        patch("views.fishing.rod_shop.safe_edit", AsyncMock()) as edit,
    ):
        await type(view).recipes_btn(view, interaction, MagicMock())

    edit.assert_awaited_once()
    _, kwargs = edit.await_args
    assert isinstance(kwargs["view"], RodRecipeBrowserView)


@pytest.mark.asyncio
async def test_back_button_returns_to_the_fishing_menu():
    # The menu self.stop()s when it opens the shop, so the back button must mint
    # a fresh, fully-navigable FishingMenuView (punch-list #1, the trapped-view fix).
    from views.fishing.menu import FishingMenuView

    view = RodShopView(_author(7), 99, at_max=False)
    interaction = _interaction(7)
    with (
        patch(
            "views.fishing.menu.fishing_workflow.get_energy",
            AsyncMock(return_value=5),
        ),
        patch(
            "views.fishing.menu.fishing_workflow.get_venue",
            AsyncMock(return_value=None),
        ),
    ):
        await type(view).back_btn(view, interaction, MagicMock())

    interaction.response.edit_message.assert_awaited_once()
    _, kwargs = interaction.response.edit_message.await_args
    assert isinstance(kwargs["view"], FishingMenuView)
    assert view.is_finished()  # the shop view stopped so it can't fight for the message
