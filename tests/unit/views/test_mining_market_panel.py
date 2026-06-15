"""The Market — sell ore + buy gear, grouped Category → Type → Variant."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from utils.mining import market, taxonomy
from views.mining.main_panel import MiningHubView
from views.mining.market_panel import MiningMarketView
from views.mining.workshop_hub import MiningWorkshopHubView

_AUTHOR = SimpleNamespace(id=1, display_name="Digger")


def test_market_reachable_via_workshop_hub():
    hub_ids = {getattr(c, "custom_id", None) for c in MiningHubView().children}
    assert "mining:workshop" in hub_ids
    workshop_labels = {
        getattr(c, "label", "") or ""
        for c in MiningWorkshopHubView(SimpleNamespace(id=1), 2).children
    }
    assert any("Market" in lbl for lbl in workshop_labels)


def test_root_has_a_category_select_sell_all_and_back():
    view = MiningMarketView(_AUTHOR, guild_id=2)
    selects = [c for c in view.children if isinstance(c, discord.ui.Select)]
    labels = " | ".join(
        b.label or "" for b in view.children if isinstance(b, discord.ui.Button)
    )
    assert len(selects) == 1  # one small category select, not many flat ones
    assert {"Weapons", "Armour", "Tools"} <= {o.value for o in selects[0].options}
    assert "Sell All" in labels and "Workshop" in labels


def test_category_opens_only_its_types():
    view = MiningMarketView(_AUTHOR, guild_id=2, category="Armour")
    select = [c for c in view.children if isinstance(c, discord.ui.Select)][0]
    buttons = {b.label for b in view.children if isinstance(b, discord.ui.Button)}
    armour = set(taxonomy.types_by_category(list(market.GEAR_SHOP))["Armour"])
    assert {o.value for o in select.options} <= armour
    assert "↩ Categories" in buttons


def test_type_opens_a_buy_select_with_prices():
    view = MiningMarketView(_AUTHOR, guild_id=2, category="Weapons", base_type="sword")
    select = [c for c in view.children if isinstance(c, discord.ui.Select)][0]
    buttons = {b.label for b in view.children if isinstance(b, discord.ui.Button)}
    assert all(taxonomy.base_type(o.value) == "sword" for o in select.options)
    assert all("🪙" in (o.label or "") for o in select.options)  # price on each row
    assert "↩ Types" in buttons


def test_drilling_every_type_covers_the_whole_gear_shop():
    covered: set[str] = set()
    names = list(market.GEAR_SHOP)
    for cat in taxonomy.ordered_categories(names):
        for base in taxonomy.types_by_category(names)[cat]:
            view = MiningMarketView(_AUTHOR, guild_id=2, category=cat, base_type=base)
            sel = [c for c in view.children if isinstance(c, discord.ui.Select)][0]
            covered |= {o.value for o in sel.options}
    assert covered == set(market.GEAR_SHOP)


@pytest.mark.asyncio
async def test_buy_select_routes_through_the_workflow():
    view = MiningMarketView(_AUTHOR, guild_id=2, category="Weapons", base_type="sword")
    buy = [c for c in view.children if isinstance(c, discord.ui.Select)][0]
    interaction = MagicMock()

    from utils.mining.market import TradeResult

    with (
        patch("views.mining.market_panel.safe_defer", AsyncMock(return_value=True)),
        patch(
            "views.mining.market_panel.mining_workflow.buy",
            AsyncMock(return_value=TradeResult(True, "ok")),
        ) as buy_fn,
        patch("views.mining.market_panel._render", AsyncMock()),
    ):
        target = buy.options[0].value
        buy._values = [target]
        await buy.callback(interaction)
    buy_fn.assert_awaited_once_with(1, 2, target)
