"""AI §7.5 — deterministic BTD6 *difficulty* cost comparison.

The difficulty member of the multi-entity cost-comparison floor (the sibling of
``test_btd6_cost_comparison.py``, which ranks *different towers* at one
difficulty). "is a 0-4-1 desperado cheaper on easy or impoppable" ranks the
**same** upgrade state across difficulties — a single tower, so the multi-tower
builder defers and the model could otherwise mis-state which difficulty is
cheaper / by how much (the BUG-0009 "grounded values, wrong assembly" class the
value-only faithfulness guard cannot catch). These pin the deterministic
``compare_difficulty_costs`` primitive + the floor reply / dispatcher wiring.
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


# --- the primitive (btd6_data_service.compare_difficulty_costs) ----------------


def test_compare_difficulties_ranks_ascending_with_spread():
    result = btd6_data_service.compare_difficulty_costs(
        "Desperado", "041", ["easy", "medium", "hard", "impoppable"],
    )
    assert result["found"] is True
    assert result["tower"] == "Desperado"
    assert result["code"] == "0-4-1"
    entries = result["entries"]
    assert [e["unit_cost"] for e in entries] == sorted(e["unit_cost"] for e in entries)
    # Easy pricing (×0.85) is the floor, Impoppable (×1.20) the ceiling.
    assert result["cheapest"]["difficulty"] == "easy"
    assert result["most_expensive"]["difficulty"] == "impoppable"
    assert (
        result["spread"]
        == result["most_expensive"]["unit_cost"] - result["cheapest"]["unit_cost"]
    )
    assert result["all_equal"] is False


def test_compare_difficulties_needs_two_distinct_valid():
    # One difficulty named → nothing to compare, never guesses a second.
    result = btd6_data_service.compare_difficulty_costs(
        "Desperado", "041", ["impoppable"],
    )
    assert result["found"] is False
    assert result["priced"] == 1


def test_compare_difficulties_skips_unknown_and_dedups():
    # "nightmare" is dropped (never guessed); duplicate "easy" collapses to one.
    result = btd6_data_service.compare_difficulty_costs(
        "Desperado", "041", ["easy", "nightmare", "easy", "hard"],
    )
    assert result["found"] is True
    assert [e["difficulty"] for e in result["entries"]] == ["easy", "hard"]


def test_compare_difficulties_unpriceable_tower_fails_closed():
    result = btd6_data_service.compare_difficulty_costs(
        "Not A Tower", "000", ["easy", "hard"],
    )
    assert result["found"] is False


def test_compare_difficulties_chimps_alias_dedups_to_hard():
    # CHIMPS prices as Hard — "hard" + "chimps" is one distinct difficulty.
    result = btd6_data_service.compare_difficulty_costs(
        "Desperado", "041", ["hard", "chimps"],
    )
    assert result["found"] is False
    assert result["priced"] == 1


# --- the floor reply (deterministic_difficulty_cost_comparison_reply) ----------


def test_difficulty_comparison_fires_and_names_the_cheaper():
    reply = btd6_context_service.deterministic_difficulty_cost_comparison_reply(
        "is a 0-4-1 desperado cheaper on easy or impoppable",
    )
    assert reply is not None
    assert "by difficulty" in reply
    assert "Desperado 0-4-1" in reply
    assert "Cheaper on **Easy**" in reply


def test_difficulty_comparison_base_tower_fires():
    # No crosspath named → base tower (000) priced across the named difficulties.
    reply = btd6_context_service.deterministic_difficulty_cost_comparison_reply(
        "which is cheaper for a dart monkey, easy or hard",
    )
    assert reply is not None
    assert "Dart Monkey 0-0-0" in reply
    assert "Cheaper on **Easy**" in reply


def test_difficulty_comparison_three_difficulties_uses_spread_format():
    reply = btd6_context_service.deterministic_difficulty_cost_comparison_reply(
        "compare the cost of a 5-0-0 ninja monkey on easy, hard and impoppable",
    )
    assert reply is not None
    assert "Cheapest: **Easy**" in reply
    assert "Most expensive: **Impoppable**" in reply
    assert "Spread:" in reply


def test_single_difficulty_defers():
    # One difficulty → no by-difficulty comparison; the grounding leg owns it.
    assert (
        btd6_context_service.deterministic_difficulty_cost_comparison_reply(
            "is a 0-4-1 desperado cheaper on impoppable",
        )
        is None
    )


def test_two_towers_defer_to_the_multi_tower_builder():
    # Two resolvable towers → this is the multi-tower builder's case, not ours.
    assert (
        btd6_context_service.deterministic_difficulty_cost_comparison_reply(
            "is a 0-4-1 desperado cheaper than a 2-0-4 sniper on easy and impoppable",
        )
        is None
    )


def test_difficulty_comparison_without_cost_cue_defers():
    assert (
        btd6_context_service.deterministic_difficulty_cost_comparison_reply(
            "is a dart monkey better on easy or hard",
        )
        is None
    )


def test_difficulty_comparison_strategy_recommendation_defers():
    assert (
        btd6_context_service.deterministic_difficulty_cost_comparison_reply(
            "should i play a dart monkey on easy or hard for cheaper",
        )
        is None
    )


# --- the dispatcher wiring -----------------------------------------------------


def test_dispatcher_routes_difficulty_comparison():
    reply = btd6_context_service.deterministic_btd6_list_reply(
        "is a 0-4-1 desperado cheaper on easy or impoppable",
    )
    assert reply is not None
    assert "by difficulty" in reply


def test_dispatcher_two_towers_still_routes_the_multi_tower_comparison():
    # The multi-tower builder runs first; a two-tower question never falls through
    # to the difficulty builder.
    reply = btd6_context_service.deterministic_btd6_list_reply(
        "is a 0-4-1 desperado cheaper than a 2-0-4 sniper monkey",
    )
    assert reply is not None
    assert "Cost comparison" in reply
    assert "by difficulty" not in reply
