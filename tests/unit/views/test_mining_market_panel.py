"""The mining hub opens a Market panel (sell ore / buy gear)."""

from __future__ import annotations

from types import SimpleNamespace

import discord

from views.mining.main_panel import MiningHubView
from views.mining.market_panel import MiningMarketView
from views.mining.workshop_hub import MiningWorkshopHubView


def test_market_reachable_via_workshop_hub():
    # Declutter (Option A, 2026-06-15): Market moved off the main hub into the
    # Workshop sub-hub, which the hub's Workshop button opens.
    hub_ids = {getattr(c, "custom_id", None) for c in MiningHubView().children}
    assert "mining:workshop" in hub_ids
    workshop_labels = {
        getattr(c, "label", "") or ""
        for c in MiningWorkshopHubView(SimpleNamespace(id=1), 2).children
    }
    assert any("Market" in lbl for lbl in workshop_labels)


def test_market_view_has_buy_selects_sell_and_back():
    from utils.mining import market

    view = MiningMarketView(SimpleNamespace(id=1), guild_id=2)
    selects = [c for c in view.children if isinstance(c, discord.ui.Select)]
    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    # One buy dropdown per shop section (the 41-item catalogue outgrew one
    # select's 25-option cap), each under the cap.
    assert len(selects) == len(market.shop_sections())
    assert all(len(s.options) <= 25 for s in selects)
    labels = " | ".join(b.label or "" for b in buttons)
    assert "Sell All" in labels
    assert "Hub" in labels  # back-to-hub navigation


def test_buy_selects_cover_the_whole_gear_shop():
    from utils.mining import market

    view = MiningMarketView(SimpleNamespace(id=1), guild_id=2)
    values = {
        opt.value
        for c in view.children
        if isinstance(c, discord.ui.Select)
        for opt in c.options
    }
    assert values == set(market.GEAR_SHOP)
