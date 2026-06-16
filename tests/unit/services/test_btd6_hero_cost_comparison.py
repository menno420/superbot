"""AI §7.5 — deterministic BTD6 *hero* base-cost comparison.

The hero member of the multi-entity comparison floor — the hero-entity sibling
of the tower cost builders (``test_btd6_cost_comparison.py`` ranks tower upgrade
states, ``test_btd6_difficulty_cost_comparison.py`` ranks difficulties,
``test_btd6_round_range_comparison.py`` ranks income, ``test_btd6_paragon_cost_comparison.py``
ranks paragons). "is Quincy or Benjamin cheaper" ranks the **base placement
cost** of **two or more** heroes, so the model can never mis-state which is
cheaper / by how much (the BUG-0009 "grounded values, wrong assembly" class the
value-only faithfulness guard cannot catch). These pin the deterministic
``compare_hero_costs`` primitive + the floor reply / dispatcher wiring, and the
exclusivity with the tower/paragon cost builders.
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


# --- the primitive (btd6_data_service.compare_hero_costs) ----------------------


def test_compare_ranks_ascending_with_spread():
    result = btd6_data_service.compare_hero_costs(["quincy", "benjamin"])
    assert result["found"] is True
    costs = [e["base_cost"] for e in result["entries"]]
    assert costs == sorted(costs)
    assert result["cheapest"]["name"] == "Quincy"
    assert result["most_expensive"]["name"] == "Benjamin"
    assert result["cheapest"]["base_cost"] == 540
    assert result["most_expensive"]["base_cost"] == 1_200
    assert result["spread"] == 660
    assert result["all_equal"] is False
    assert result["difficulty"] == "medium"


def test_compare_resolves_aliases_and_canonicals():
    # "gwen" (alias) + "Striker Jones" (canonical) both resolve to heroes.
    result = btd6_data_service.compare_hero_costs(["gwen", "striker jones"])
    assert result["found"] is True
    ids = {e["hero_id"] for e in result["entries"]}
    assert ids == {"gwendolin", "striker_jones"}


def test_compare_equal_base_costs_is_a_real_tie():
    # Ezili and Sauda share a $600 placement cost — a genuine all-equal.
    result = btd6_data_service.compare_hero_costs(["ezili", "sauda"])
    assert result["found"] is True
    assert result["all_equal"] is True
    assert result["spread"] == 0


def test_compare_dedups_on_hero_id():
    # The same hero under two surfaces (id + alias) collapses → defer.
    result = btd6_data_service.compare_hero_costs(["quincy", "q"])
    assert result["found"] is False
    assert result["priced"] == 1


def test_compare_needs_two_distinct():
    result = btd6_data_service.compare_hero_costs(["quincy"])
    assert result["found"] is False
    assert result["priced"] == 1


def test_compare_skips_unknown_names_never_guesses():
    result = btd6_data_service.compare_hero_costs(["quincy", "not a hero"])
    assert result["found"] is False
    assert result["priced"] == 1


def test_compare_difficulty_scales_the_base_cost():
    result = btd6_data_service.compare_hero_costs(
        ["quincy", "benjamin"],
        difficulty="impoppable",
    )
    assert result["found"] is True
    assert result["difficulty"] == "impoppable"
    # Impoppable is the Medium price × 1.20 (rounded to $5).
    assert result["cheapest"]["base_cost"] == 650
    assert result["most_expensive"]["base_cost"] == 1_440


def test_compare_unknown_difficulty_fails_closed():
    result = btd6_data_service.compare_hero_costs(
        ["quincy", "benjamin"],
        difficulty="nightmare",
    )
    assert result["found"] is False


# --- the floor reply (deterministic_hero_cost_comparison_reply) ----------------


def test_reply_fires_and_names_the_cheaper_hero():
    reply = btd6_context_service.deterministic_hero_cost_comparison_reply(
        "is quincy or benjamin cheaper?",
    )
    assert reply is not None
    assert "Hero cost comparison" in reply
    assert "Quincy" in reply and "Benjamin" in reply
    assert "The **Quincy** is cheaper by **$660**" in reply


def test_reply_three_heroes_uses_spread_format():
    reply = btd6_context_service.deterministic_hero_cost_comparison_reply(
        "cheapest hero out of gwendolin, striker jones and benjamin?",
    )
    assert reply is not None
    assert "Cheapest:" in reply
    assert "Most expensive:" in reply
    assert "Spread:" in reply


def test_reply_difficulty_token_routes_pricing():
    reply = btd6_context_service.deterministic_hero_cost_comparison_reply(
        "which hero is cheaper on impoppable, quincy or benjamin?",
    )
    assert reply is not None
    assert "Impoppable placement cost" in reply
    assert "$650" in reply


def test_reply_tie_states_same_price():
    reply = btd6_context_service.deterministic_hero_cost_comparison_reply(
        "do ezili and sauda cost the same to place?",
    )
    assert reply is not None
    assert "cost the **same**" in reply


def test_single_hero_defers():
    assert (
        btd6_context_service.deterministic_hero_cost_comparison_reply(
            "how much does quincy cost?",
        )
        is None
    )


def test_paragon_cue_defers_to_paragon_builder():
    # A paragon cost comparison is the paragon builder's job, even if a hero
    # name happens to appear — the hero builder must defer on the paragon cue.
    assert (
        btd6_context_service.deterministic_hero_cost_comparison_reply(
            "is the glaive dominus or ascended shadow paragon cheaper?",
        )
        is None
    )


def test_no_cost_cue_defers():
    assert (
        btd6_context_service.deterministic_hero_cost_comparison_reply(
            "what do quincy and benjamin do?",
        )
        is None
    )


def test_strategy_recommendation_defers():
    assert (
        btd6_context_service.deterministic_hero_cost_comparison_reply(
            "should i pick quincy or benjamin?",
        )
        is None
    )


# --- the dispatcher wiring + exclusivity ---------------------------------------


def test_dispatcher_routes_hero_cost_comparison():
    reply = btd6_context_service.deterministic_btd6_list_reply(
        "is quincy or benjamin cheaper?",
    )
    assert reply is not None
    assert "Hero cost comparison" in reply


def test_hero_question_only_the_hero_builder_fires():
    # A two-hero cost question must not reach the tower/difficulty/paragon
    # builders — they need a resolvable (tower, crosspath) or a paragon cue.
    phrase = "is gwendolin or sauda cheaper?"
    firing = [
        builder.__name__
        for builder in btd6_context_service._BTD6_LIST_BUILDERS
        if builder(phrase) is not None
    ]
    assert firing == ["deterministic_hero_cost_comparison_reply"]
