"""AI §7.5 — deterministic BTD6 *paragon* base-cost comparison.

The paragon member of the multi-entity comparison floor — the paragon-entity
sibling of the tower cost builders (``test_btd6_cost_comparison.py`` ranks tower
upgrade states, ``test_btd6_difficulty_cost_comparison.py`` ranks difficulties,
``test_btd6_round_range_comparison.py`` ranks income). "is Glaive Dominus or
Ascended Shadow cheaper" ranks the **base build price** of **two or more**
paragons, so the model can never mis-state which is cheaper / by how much (the
BUG-0009 "grounded values, wrong assembly" class the value-only faithfulness
guard cannot catch). These pin the deterministic ``compare_paragon_costs``
primitive + the floor reply / dispatcher wiring, and the exclusivity with the
tower cost builders (a "paragon" question must not be priced as the base tower).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import btd6_context_service, btd6_data_service  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_dataset_cache():
    btd6_data_service.reset_cache()
    yield
    btd6_data_service.reset_cache()


# --- the primitive (btd6_data_service.compare_paragon_costs) -------------------


def test_compare_ranks_ascending_with_spread():
    result = btd6_data_service.compare_paragon_costs(
        ["glaive dominus", "ascended shadow"],
    )
    assert result["found"] is True
    # Ranked ascending — cheapest first.
    costs = [e["base_cost"] for e in result["entries"]]
    assert costs == sorted(costs)
    assert result["cheapest"]["name"] == "Glaive Dominus"
    assert result["most_expensive"]["name"] == "Ascended Shadow"
    assert result["cheapest"]["base_cost"] == 375_000
    assert result["most_expensive"]["base_cost"] == 500_000
    assert result["spread"] == 125_000
    assert result["all_equal"] is False
    assert result["difficulty"] == "medium"


def test_compare_resolves_aliases_and_tower_names():
    # "dart" (alias) + "wizard monkey" (tower name) both resolve to paragons.
    result = btd6_data_service.compare_paragon_costs(["dart", "wizard monkey"])
    assert result["found"] is True
    ids = {e["paragon_id"] for e in result["entries"]}
    assert ids == {"apex_plasma_master", "magus_perfectus"}


def test_compare_equal_base_prices_is_a_real_tie():
    # Ascended Shadow and Navarch share a $500,000 base — a genuine all-equal.
    result = btd6_data_service.compare_paragon_costs(
        ["ascended shadow", "navarch of the seas"],
    )
    assert result["found"] is True
    assert result["all_equal"] is True
    assert result["spread"] == 0


def test_compare_dedups_on_paragon_id():
    # The same paragon under two surfaces (id + alias) collapses → defer.
    result = btd6_data_service.compare_paragon_costs(["apex_plasma_master", "dart"])
    assert result["found"] is False
    assert result["priced"] == 1


def test_compare_needs_two_distinct():
    result = btd6_data_service.compare_paragon_costs(["glaive dominus"])
    assert result["found"] is False
    assert result["priced"] == 1


def test_compare_skips_unknown_names_never_guesses():
    result = btd6_data_service.compare_paragon_costs(["glaive dominus", "not a paragon"])
    assert result["found"] is False
    assert result["priced"] == 1


def test_compare_difficulty_scales_the_base_price():
    result = btd6_data_service.compare_paragon_costs(
        ["glaive dominus", "ascended shadow"],
        difficulty="impoppable",
    )
    assert result["found"] is True
    assert result["difficulty"] == "impoppable"
    # Impoppable is the Medium price × 1.20 (rounded to $5).
    assert result["cheapest"]["base_cost"] == 450_000
    assert result["most_expensive"]["base_cost"] == 600_000


def test_compare_unknown_difficulty_fails_closed():
    result = btd6_data_service.compare_paragon_costs(
        ["glaive dominus", "ascended shadow"],
        difficulty="nightmare",
    )
    assert result["found"] is False


# --- the floor reply (deterministic_paragon_cost_comparison_reply) -------------


def test_reply_fires_and_names_the_cheaper_paragon():
    reply = btd6_context_service.deterministic_paragon_cost_comparison_reply(
        "is the glaive dominus or ascended shadow paragon cheaper?",
    )
    assert reply is not None
    assert "Paragon cost comparison" in reply
    assert "Glaive Dominus" in reply and "Ascended Shadow" in reply
    assert "The **Glaive Dominus** is cheaper by **$125,000**" in reply


def test_reply_three_paragons_uses_spread_format():
    reply = btd6_context_service.deterministic_paragon_cost_comparison_reply(
        "compare the cost of the dart, glaive and goliath doomship paragons",
    )
    assert reply is not None
    assert "Cheapest:" in reply
    assert "Most expensive:" in reply
    assert "Spread:" in reply


def test_reply_difficulty_token_routes_pricing():
    reply = btd6_context_service.deterministic_paragon_cost_comparison_reply(
        "which paragon is cheaper on impoppable, glaive dominus or ascended shadow?",
    )
    assert reply is not None
    assert "Impoppable base price" in reply
    assert "$450,000" in reply


def test_reply_tie_states_same_price():
    reply = btd6_context_service.deterministic_paragon_cost_comparison_reply(
        "do the ascended shadow and navarch paragons cost the same?",
    )
    assert reply is not None
    assert "cost the **same**" in reply


def test_single_paragon_defers():
    assert (
        btd6_context_service.deterministic_paragon_cost_comparison_reply(
            "how much does the glaive dominus paragon cost?",
        )
        is None
    )


def test_no_paragon_token_defers():
    # Two paragon-tower names but no "paragon" word → not routed here (it is a
    # tower question, owned by the tower cost builder).
    assert (
        btd6_context_service.deterministic_paragon_cost_comparison_reply(
            "is the dart monkey or ninja monkey cheaper?",
        )
        is None
    )


def test_no_cost_cue_defers():
    assert (
        btd6_context_service.deterministic_paragon_cost_comparison_reply(
            "what do the glaive dominus and ascended shadow paragons do?",
        )
        is None
    )


def test_strategy_recommendation_defers():
    assert (
        btd6_context_service.deterministic_paragon_cost_comparison_reply(
            "should i build the glaive dominus or ascended shadow paragon?",
        )
        is None
    )


# --- the dispatcher wiring + exclusivity ---------------------------------------


def test_dispatcher_routes_paragon_cost_comparison():
    reply = btd6_context_service.deterministic_btd6_list_reply(
        "is the glaive dominus or ascended shadow paragon cheaper?",
    )
    assert reply is not None
    assert "Paragon cost comparison" in reply


def test_paragon_question_does_not_reach_the_tower_cost_builder():
    # A "dart/ninja paragon" cost question (tower aliases present) must not be
    # priced as the base tower — the tower cost builders defer on the paragon cue.
    phrase = "is the dart or ninja paragon cheaper?"
    firing = [
        builder.__name__
        for builder in btd6_context_service._BTD6_LIST_BUILDERS
        if builder(phrase) is not None
    ]
    assert firing == ["deterministic_paragon_cost_comparison_reply"]
