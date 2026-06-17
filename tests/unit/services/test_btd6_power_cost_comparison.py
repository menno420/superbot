"""AI §7.5 — deterministic BTD6 *power* (activated-ability) cost comparison.

The power member of the multi-entity comparison floor — the activated-ability
sibling of the tower cost builders (``test_btd6_cost_comparison.py`` ranks tower
upgrade states, ``test_btd6_difficulty_cost_comparison.py`` ranks difficulties,
``test_btd6_round_range_comparison.py`` ranks income,
``test_btd6_paragon_cost_comparison.py`` ranks paragons,
``test_btd6_hero_cost_comparison.py`` ranks heroes). "is Cash Drop or Monkey
Boost cheaper" ranks the **Monkey Money** store price of **two or more** powers,
so the model can never mis-state which is cheaper / by how much (the BUG-0009
"grounded values, wrong assembly" class the value-only faithfulness guard cannot
catch). Powers are bought with a *fixed* Monkey-Money price (no difficulty
scaling), so — unlike the hero builder — this primitive has no difficulty axis.
These pin the deterministic ``compare_power_costs`` primitive + the floor reply /
dispatcher wiring, and the exclusivity with the tower/hero/paragon cost builders.
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


# --- the primitive (btd6_data_service.compare_power_costs) ---------------------


def test_compare_ranks_ascending_with_spread():
    result = btd6_data_service.compare_power_costs(["cash drop", "monkey boost"])
    assert result["found"] is True
    costs = [e["cost"] for e in result["entries"]]
    assert costs == sorted(costs)
    assert result["cheapest"]["name"] == "Monkey Boost"
    assert result["most_expensive"]["name"] == "Cash Drop"
    assert result["cheapest"]["cost"] == 100
    assert result["most_expensive"]["cost"] == 200
    assert result["spread"] == 100
    assert result["all_equal"] is False
    # No difficulty axis — powers are a fixed Monkey-Money store price.
    assert "difficulty" not in result


def test_compare_resolves_ids_and_canonicals():
    # The catalog id and the canonical name both resolve to powers.
    result = btd6_data_service.compare_power_costs(["banana_farmer", "Battle Cat"])
    assert result["found"] is True
    ids = {e["power_id"] for e in result["entries"]}
    assert ids == {"banana_farmer", "battle_cat"}


def test_compare_equal_costs_is_a_real_tie():
    # Banana Farmer and Road Spikes share a 50-MM price — a genuine all-equal.
    result = btd6_data_service.compare_power_costs(["banana farmer", "road spikes"])
    assert result["found"] is True
    assert result["all_equal"] is True
    assert result["spread"] == 0


def test_compare_dedups_on_power_id():
    # The same power under two surfaces (id + canonical) collapses → defer.
    result = btd6_data_service.compare_power_costs(["cash drop", "cash_drop"])
    assert result["found"] is False
    assert result["priced"] == 1


def test_compare_needs_two_distinct():
    result = btd6_data_service.compare_power_costs(["cash drop"])
    assert result["found"] is False
    assert result["priced"] == 1


def test_compare_skips_unknown_names_never_guesses():
    result = btd6_data_service.compare_power_costs(["cash drop", "not a power"])
    assert result["found"] is False
    assert result["priced"] == 1


# --- the floor reply (deterministic_power_cost_comparison_reply) ---------------


def test_reply_fires_and_names_the_cheaper_power():
    reply = btd6_context_service.deterministic_power_cost_comparison_reply(
        "which power is cheaper, cash drop or monkey boost?",
    )
    assert reply is not None
    assert "Power cost comparison" in reply
    assert "Cash Drop" in reply and "Monkey Boost" in reply
    assert "The **Monkey Boost** is cheaper by **100 MM**" in reply


def test_reply_three_powers_uses_spread_format():
    reply = btd6_context_service.deterministic_power_cost_comparison_reply(
        "cheapest power out of monkey boost, cash drop and super monkey beacon?",
    )
    assert reply is not None
    assert "Cheapest:" in reply
    assert "Most expensive:" in reply
    assert "Spread:" in reply
    # Monkey Boost (100) < Cash Drop (200) < Super Monkey Beacon (400).
    assert "Cheapest: **Monkey Boost**" in reply
    assert "Most expensive: **Super Monkey Beacon**" in reply


def test_reply_tie_states_same_price():
    reply = btd6_context_service.deterministic_power_cost_comparison_reply(
        "do banana farmer and road spikes cost the same?",
    )
    assert reply is not None
    assert "cost the **same**" in reply


def test_single_power_defers():
    assert (
        btd6_context_service.deterministic_power_cost_comparison_reply(
            "how much does cash drop cost?",
        )
        is None
    )


def test_paragon_cue_defers_to_paragon_builder():
    # A paragon cost comparison is the paragon builder's job; defer on the cue.
    assert (
        btd6_context_service.deterministic_power_cost_comparison_reply(
            "is the glaive dominus or ascended shadow paragon cheaper?",
        )
        is None
    )


def test_no_cost_cue_defers():
    assert (
        btd6_context_service.deterministic_power_cost_comparison_reply(
            "what do cash drop and monkey boost do?",
        )
        is None
    )


def test_strategy_recommendation_defers():
    assert (
        btd6_context_service.deterministic_power_cost_comparison_reply(
            "should i buy cash drop or monkey boost?",
        )
        is None
    )


# --- the dispatcher wiring + exclusivity ---------------------------------------


def test_dispatcher_routes_power_cost_comparison():
    reply = btd6_context_service.deterministic_btd6_list_reply(
        "which power is cheaper, cash drop or monkey boost?",
    )
    assert reply is not None
    assert "Power cost comparison" in reply


def test_power_question_only_the_power_builder_fires():
    # A two-power cost question must not reach the tower/hero/paragon builders —
    # they need a resolvable (tower, crosspath), hero, or a paragon cue.
    phrase = "is cash drop or super monkey storm more expensive?"
    firing = [
        builder.__name__
        for builder in btd6_context_service._BTD6_LIST_BUILDERS
        if builder(phrase) is not None
    ]
    assert firing == ["deterministic_power_cost_comparison_reply"]
