"""AI §7.5 — deterministic BTD6 cost comparison ("which costs more / is cheaper").

A cost comparison is the comparison member of the BUG-0009 "grounded values, wrong
assembly" class: every individual price is grounded, but the model freelances/
mis-ranks the comparison (which is cheaper, by how much) and the value-only
faithfulness guard cannot catch a mis-ranking. These pin the deterministic
``compare_crosspath_costs`` primitive + the floor reply / dispatcher that now own
the labelled comparison.
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


# --- the primitive (btd6_data_service.compare_crosspath_costs) -----------------


def test_compare_ranks_ascending_with_spread():
    result = btd6_data_service.compare_crosspath_costs(
        [("Ninja Monkey", "500"), ("Wizard Monkey", "050")],
    )
    assert result["found"] is True
    assert result["difficulty"] == "medium"
    entries = result["entries"]
    assert [e["unit_cost"] for e in entries] == sorted(e["unit_cost"] for e in entries)
    assert result["cheapest"] is entries[0]
    assert result["most_expensive"] is entries[-1]
    assert (
        result["spread"]
        == result["most_expensive"]["unit_cost"] - result["cheapest"]["unit_cost"]
    )
    # Ninja Grandmaster (5-0-0) is cheaper than Wizard Lord Phoenix (0-5-0).
    assert result["cheapest"]["tower"] == "Ninja Monkey"


def test_compare_honours_difficulty():
    medium = btd6_data_service.compare_crosspath_costs(
        [("Super Monkey", "402"), ("Dart Monkey", "024")],
        difficulty="medium",
    )
    impop = btd6_data_service.compare_crosspath_costs(
        [("Super Monkey", "402"), ("Dart Monkey", "024")],
        difficulty="impoppable",
    )
    # Impoppable pricing is strictly dearer than medium for the same upgrade state.
    assert impop["most_expensive"]["unit_cost"] > medium["most_expensive"]["unit_cost"]
    assert impop["difficulty"] == "impoppable"


def test_compare_needs_two_priceable_candidates():
    # One known + one unknown tower → cannot compare, never guesses.
    result = btd6_data_service.compare_crosspath_costs(
        [("Ninja Monkey", "500"), ("Not A Tower", "000")],
    )
    assert result["found"] is False
    assert result["priced"] == 1


def test_compare_rejects_unknown_difficulty():
    result = btd6_data_service.compare_crosspath_costs(
        [("Ninja Monkey", "500"), ("Wizard Monkey", "050")],
        difficulty="nightmare",
    )
    assert result["found"] is False


def test_compare_all_equal_flagged():
    # The same tower+code twice prices identically → all_equal, zero spread.
    result = btd6_data_service.compare_crosspath_costs(
        [("Dart Monkey", "024"), ("Dart Monkey", "024")],
    )
    assert result["found"] is True
    assert result["all_equal"] is True
    assert result["spread"] == 0


# --- the floor reply (btd6_context_service.deterministic_cost_comparison_reply) -


def test_crosspath_comparison_fires_and_names_the_cheaper():
    reply = btd6_context_service.deterministic_cost_comparison_reply(
        "is a 0-4-1 desperado cheaper than a 2-0-4 sniper monkey",
    )
    assert reply is not None
    assert "Cost comparison" in reply
    assert "Desperado 0-4-1" in reply
    assert "Sniper Monkey 2-0-4" in reply
    # Sniper 2-0-4 ($9,700) is the cheaper of the two.
    assert "Sniper Monkey 2-0-4** is cheaper" in reply


def test_compare_verb_with_cost_noun_fires():
    reply = btd6_context_service.deterministic_cost_comparison_reply(
        "compare the cost of a 5-0-0 ninja monkey and a 0-5-0 wizard monkey",
    )
    assert reply is not None
    assert "Ninja Monkey 5-0-0" in reply
    assert "Wizard Monkey 0-5-0" in reply


def test_base_tower_comparison_fires():
    # No crosspath named → base towers (000) compared; still deterministic + true.
    reply = btd6_context_service.deterministic_cost_comparison_reply(
        "which is cheaper, a dart monkey or a sniper monkey",
    )
    assert reply is not None
    assert "Dart Monkey 0-0-0" in reply
    assert "Sniper Monkey 0-0-0" in reply


def test_difficulty_cue_is_honoured_in_reply():
    reply = btd6_context_service.deterministic_cost_comparison_reply(
        "which is more expensive on impoppable, "
        "a 4-0-2 super monkey or a 0-2-4 dart monkey",
    )
    assert reply is not None
    assert "Impoppable pricing" in reply


def test_single_tower_cost_question_defers():
    # A single-entity cost lookup is the grounding pricing leg's job, not this floor.
    assert (
        btd6_context_service.deterministic_cost_comparison_reply(
            "how much does a 0-4-1 desperado cost",
        )
        is None
    )


def test_comparison_without_cost_cue_defers():
    # "which is better" with no money word may be a stats/strategy question.
    assert (
        btd6_context_service.deterministic_cost_comparison_reply(
            "which is better, a ninja monkey or a sniper monkey",
        )
        is None
    )


def test_strategy_recommendation_defers():
    assert (
        btd6_context_service.deterministic_cost_comparison_reply(
            "should i get a ninja monkey or a sniper monkey for cheaper",
        )
        is None
    )


def test_cost_cue_with_one_tower_defers():
    # Cost cue present but only one resolvable tower → no comparison to make.
    assert (
        btd6_context_service.deterministic_cost_comparison_reply(
            "is the wizard monkey cheaper than i think",
        )
        is None
    )


# --- the dispatcher wiring -----------------------------------------------------


def test_dispatcher_routes_cost_comparison():
    reply = btd6_context_service.deterministic_btd6_list_reply(
        "is a 0-4-1 desperado cheaper than a 2-0-4 sniper monkey",
    )
    assert reply is not None
    assert "Cost comparison" in reply


def test_dispatcher_still_defers_ordinary_question():
    assert (
        btd6_context_service.deterministic_btd6_list_reply(
            "how much does a 0-4-1 desperado cost",
        )
        is None
    )
