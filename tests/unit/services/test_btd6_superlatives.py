"""Price superlatives so the AI can answer 'most/least expensive' questions."""

from __future__ import annotations

import pytest

from services import btd6_ai_knowledge_block_service as kb
from services import btd6_data_service as ds
from services import btd6_knowledge_service as ks
from services import btd6_stats_service as ss


@pytest.fixture(autouse=True)
def _fresh():
    ds.reset_cache()
    ss.reset_cache()
    yield
    ds.reset_cache()
    ss.reset_cache()


def test_all_upgrade_prices_includes_paragons():
    prices = ks.all_upgrade_prices()
    assert prices
    assert any(p.path == "paragon" for p in prices)


def test_most_expensive_is_a_paragon_and_sorted():
    top = ks.upgrades_by_price(highest=True, limit=5)
    assert top[0].path == "paragon"  # Paragons are the priciest upgrades
    assert [p.cost for p in top] == sorted((p.cost for p in top), reverse=True)


def test_cheapest_are_low_tier():
    cheap = ks.upgrades_by_price(highest=False, limit=3)
    assert cheap[0].cost <= ks.upgrades_by_price(highest=True, limit=1)[0].cost
    assert cheap[0].cost > 0


@pytest.mark.parametrize(
    "q",
    [
        "what is the most expensive upgrade in btd6",
        "cheapest tower",
        "which upgrade has the highest cost",
    ],
)
def test_superlative_questions_trigger_catalog_block(q):
    assert kb.looks_like_btd6_catalog_question(q)


def test_kind_filter_separates_towers_paragons_and_upgrades():
    reg = ks.upgrades_by_price(highest=True, limit=5, kind="regular")
    par = ks.upgrades_by_price(highest=True, limit=5, kind="paragon")
    assert reg and par
    assert all(u.path != "paragon" for u in reg)
    assert all(u.path == "paragon" for u in par)
    # The priciest regular (tier-5) upgrade is still cheaper than the top Paragon.
    assert reg[0].cost < par[0].cost


def test_catalog_block_keeps_categories_distinct():
    text = kb._btd6_catalog_block().text
    # The three "most expensive" questions are separately labelled.
    assert "Tower placement cost" in text  # most expensive *tower* (base)
    assert "Most expensive upgrades (tiers 1-5" in text  # excludes Paragons
    assert "Most expensive Paragons" in text  # the tier-6 super-upgrade
    assert "Cheapest upgrades:" in text
