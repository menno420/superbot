"""The mining hub opens a Market panel (sell ore / buy gear)."""

from __future__ import annotations

from types import SimpleNamespace

import discord

from views.mining.main_panel import MiningHubView
from views.mining.market_panel import MiningMarketView


def test_hub_has_market_button():
    ids = {getattr(c, "custom_id", None) for c in MiningHubView().children}
    assert "mining:market" in ids


def test_market_view_has_buy_select_sell_and_back():
    view = MiningMarketView(SimpleNamespace(id=1), guild_id=2)
    selects = [c for c in view.children if isinstance(c, discord.ui.Select)]
    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    assert len(selects) == 1  # the buy-gear dropdown
    labels = " | ".join(b.label or "" for b in buttons)
    assert "Sell All" in labels
    assert "Hub" in labels  # back-to-hub navigation


def test_buy_select_lists_the_gear_shop():
    from utils.mining import market

    view = MiningMarketView(SimpleNamespace(id=1), guild_id=2)
    select = next(c for c in view.children if isinstance(c, discord.ui.Select))
    values = {opt.value for opt in select.options}
    assert values == set(market.GEAR_SHOP)
