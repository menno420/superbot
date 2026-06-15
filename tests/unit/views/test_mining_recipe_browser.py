"""Recipe browser — grouped by item type (Swords → variants), craft-on-select.

Owner UX ask (2026-06-15): group every tier of an item under one type, opened to
its variants — replacing the old flat, paginated recipe list.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from views.mining.recipe_browser import (
    MiningRecipeBrowserView,
    _base_type,
    _grouped,
)

_AUTHOR = SimpleNamespace(id=1, display_name="Digger")


def _inventory_patch(inventory=None):
    return patch(
        "views.mining.recipe_browser.db.get_mining_inventory",
        new_callable=AsyncMock,
        return_value=inventory or {},
    )


def test_base_type_is_the_last_word():
    assert _base_type("iron sword") == "sword"
    assert _base_type("diamond pickaxe") == "pickaxe"
    assert _base_type("torch") == "torch"


def test_grouped_collapses_variants_under_one_type():
    groups = _grouped()
    # Every sword tier lives under one "sword" group, not as separate entries.
    assert "sword" in groups
    swords = [name for name, _ in groups["sword"]]
    assert len(swords) > 1
    assert all(_base_type(name) == "sword" for name in swords)


@pytest.mark.asyncio
async def test_top_level_shows_a_type_select_not_a_flat_list():
    with _inventory_patch({"wood": 100}):
        view = await MiningRecipeBrowserView.create(_AUTHOR, 99)
    selects = [c for c in view.children if isinstance(c, discord.ui.Select)]
    buttons = {b.label for b in view.children if isinstance(b, discord.ui.Button)}
    # One type select (no flat recipe list, no Prev/Next pager).
    assert len(selects) == 1
    assert 1 < len(selects[0].options) <= 25  # one option per base type
    assert "↩ Workshop" in buttons


@pytest.mark.asyncio
async def test_choosing_a_type_opens_only_that_type_variants():
    with _inventory_patch():
        view = await MiningRecipeBrowserView.create(_AUTHOR, 99, base_type="sword")
    selects = [c for c in view.children if isinstance(c, discord.ui.Select)]
    buttons = {b.label for b in view.children if isinstance(b, discord.ui.Button)}
    assert len(selects) == 1  # the variant select
    assert all(_base_type(o.value) == "sword" for o in selects[0].options)
    assert "↩ Types" in buttons  # back to the type list (level 2 → level 1)


@pytest.mark.asyncio
async def test_variant_select_crafts_through_the_workflow():
    with _inventory_patch():
        view = await MiningRecipeBrowserView.create(_AUTHOR, 99, base_type="sword")
    variant_select = [c for c in view.children if isinstance(c, discord.ui.Select)][0]
    interaction = MagicMock()

    from utils.mining.market import TradeResult

    with (
        patch("views.mining.recipe_browser.safe_defer", AsyncMock(return_value=True)),
        patch(
            "views.mining.recipe_browser.mining_workflow.craft",
            AsyncMock(return_value=TradeResult(True, "Crafted!")),
        ) as craft,
        patch.object(MiningRecipeBrowserView, "render", AsyncMock()),
    ):
        target = variant_select.options[0].value
        variant_select._values = [target]
        await variant_select.callback(interaction)
    craft.assert_awaited_once_with(1, 99, target)
