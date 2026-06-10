"""Recipe browser — categories, craft-on-select, >25-recipe pagination."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from views.mining import recipe_browser
from views.mining.recipe_browser import MiningRecipeBrowserView, build_recipe_embed

_AUTHOR = SimpleNamespace(id=1, display_name="Digger")


def _inventory_patch(inventory=None):
    return patch(
        "views.mining.recipe_browser.db.get_mining_inventory",
        new_callable=AsyncMock,
        return_value=inventory or {},
    )


@pytest.mark.asyncio
async def test_factory_builds_category_recipe_and_pager_controls():
    with _inventory_patch({"wood": 100, "stone": 100}):
        view = await MiningRecipeBrowserView.create(_AUTHOR, 99)
    selects = [c for c in view.children if isinstance(c, discord.ui.Select)]
    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    assert len(selects) == 2  # category + recipes
    labels = {b.label for b in buttons}
    assert {"◀ Prev", "Next ▶", "↩ Mining Hub"} <= labels
    # One page today: both pagers disabled.
    pagers = [b for b in buttons if b.label in ("◀ Prev", "Next ▶")]
    assert all(b.disabled for b in pagers)


@pytest.mark.asyncio
async def test_category_filter_limits_the_recipe_select():
    with _inventory_patch():
        view = await MiningRecipeBrowserView.create(_AUTHOR, 99, category="structure")
    recipe_select = [c for c in view.children if isinstance(c, discord.ui.Select)][1]
    from utils.mining import items

    for option in recipe_select.options:
        assert items.classify(option.value) is items.ItemKind.STRUCTURE


@pytest.mark.asyncio
async def test_recipe_select_crafts_through_the_workflow():
    with _inventory_patch({"wood": 5}):
        view = await MiningRecipeBrowserView.create(_AUTHOR, 99)
    recipe_select = [c for c in view.children if isinstance(c, discord.ui.Select)][1]
    interaction = MagicMock()

    from utils.mining.market import TradeResult

    with (
        patch(
            "views.mining.recipe_browser.safe_defer",
            AsyncMock(return_value=True),
        ),
        patch(
            "views.mining.recipe_browser.mining_workflow.craft",
            AsyncMock(return_value=TradeResult(True, "Crafted **torch**!")),
        ) as craft,
        patch.object(MiningRecipeBrowserView, "render", AsyncMock()),
    ):
        recipe_select._values = ["torch"]
        await recipe_select.callback(interaction)
    craft.assert_awaited_once_with(1, 99, "torch")


@pytest.mark.asyncio
async def test_pagination_engages_past_25_recipes():
    """Synthetic fat catalog: the pager must slice pages and enable Next."""
    fat = {f"gadget {i:02d}": {"wood": 1} for i in range(60)}
    with (
        _inventory_patch(),
        patch.object(recipe_browser, "load_recipes", return_value=fat),
        patch(
            "views.mining.recipe_browser.items.classify",
            return_value=__import__(
                "utils.mining.items",
                fromlist=["ItemKind"],
            ).ItemKind.STRUCTURE,
        ),
    ):
        page0 = await MiningRecipeBrowserView.create(_AUTHOR, 99)
        page1 = await MiningRecipeBrowserView.create(_AUTHOR, 99, page=1)
        page_last = await MiningRecipeBrowserView.create(_AUTHOR, 99, page=99)
        embed = await build_recipe_embed(1, 99, page=1)

    def _options(view):
        return [c for c in view.children if isinstance(c, discord.ui.Select)][1].options

    assert len(_options(page0)) == 25
    assert _options(page1)[0].value == "gadget 25"
    # Out-of-range page clamps to the last page (60 → 3 pages → index 2).
    assert page_last.page == 2
    assert len(_options(page_last)) == 10
    assert "Page 2/3" in (embed.footer.text or "")
    pagers = {
        b.label: b
        for b in page0.children
        if isinstance(b, discord.ui.Button) and b.label in ("◀ Prev", "Next ▶")
    }
    assert pagers["◀ Prev"].disabled is True
    assert pagers["Next ▶"].disabled is False
