"""AI §7.5 — deterministic BTD6 *round-range* cash comparison.

The round-range (income) member of the multi-entity comparison floor — the
sibling of the cost builders (``test_btd6_cost_comparison.py`` ranks towers,
``test_btd6_difficulty_cost_comparison.py`` ranks difficulties). "which earns
more cash, rounds 20-40 or 40-60" ranks the total cash of **two or more** round
ranges, so the model can never mis-state which range earns more / by how much
(the BUG-0009 "grounded values, wrong assembly" class the value-only
faithfulness guard cannot catch). A **single** range is the round-cash
workflow's job — they stay non-overlapping on range count. These pin the
deterministic ``compare_round_ranges`` primitive + the floor reply / dispatcher
wiring.
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


# --- the primitive (btd6_data_service.compare_round_ranges) --------------------


def test_compare_ranges_ranks_descending_with_spread():
    result = btd6_data_service.compare_round_ranges([(20, 40), (40, 60)])
    assert result["found"] is True
    entries = result["entries"]
    # Ranked descending — most cash first (the question asks which earns *more*).
    assert [e["earned"] for e in entries] == sorted(
        (e["earned"] for e in entries),
        reverse=True,
    )
    # Later rounds pay far more, so 40-60 is the top earner.
    assert result["highest"]["round_start"] == 40
    assert result["lowest"]["round_start"] == 20
    assert result["spread"] == round(
        result["highest"]["earned"] - result["lowest"]["earned"], 2
    )
    assert result["all_equal"] is False
    assert result["roundset"] == "default"


def test_compare_ranges_needs_two_distinct():
    # One range named → nothing to compare; never guesses a second.
    result = btd6_data_service.compare_round_ranges([(20, 40)])
    assert result["found"] is False
    assert result["priced"] == 1


def test_compare_ranges_dedups_normalized_pairs():
    # (40, 20) normalises to (20, 40) → identical to the first → one entry → defer.
    result = btd6_data_service.compare_round_ranges([(20, 40), (40, 20)])
    assert result["found"] is False
    assert result["priced"] == 1


def test_compare_ranges_normalises_reversed_endpoints():
    result = btd6_data_service.compare_round_ranges([(40, 20), (60, 40)])
    assert result["found"] is True
    spans = {(e["round_start"], e["round_end"]) for e in result["entries"]}
    assert spans == {(20, 40), (40, 60)}


def test_compare_ranges_skips_out_of_range_fails_closed():
    # Rounds 200-250 do not exist (set is 1-140) → skipped, never summed partial.
    result = btd6_data_service.compare_round_ranges([(20, 40), (200, 250)])
    assert result["found"] is False
    assert result["priced"] == 1


def test_compare_ranges_single_round_segments():
    # lo == hi contributes that round's own cash (the primitive's single_round leg).
    result = btd6_data_service.compare_round_ranges([(50, 50), (80, 80)])
    assert result["found"] is True
    assert all(e["single_round"] for e in result["entries"])


def test_compare_ranges_abr_roundset_labelled():
    result = btd6_data_service.compare_round_ranges(
        [(10, 30), (30, 50)],
        roundset="alternate",
    )
    assert result["found"] is True
    assert result["roundset"] == "alternate"
    assert result["set_label"] == "alternate (ABR)"


# --- the floor reply (deterministic_round_range_comparison_reply) --------------


def test_reply_fires_and_names_the_bigger_earner():
    reply = btd6_context_service.deterministic_round_range_comparison_reply(
        "which earns more cash, rounds 20-40 or rounds 40-60?",
    )
    assert reply is not None
    assert "Cash comparison" in reply
    assert "Rounds 40–60 earn more" in reply
    # Whole-dollar amount renders without a trailing ``.0``.
    assert ".0" not in reply.split("earn more by")[0]


def test_reply_three_ranges_uses_spread_format():
    reply = btd6_context_service.deterministic_round_range_comparison_reply(
        "do i get more money from rounds 1-30, rounds 30-60 or rounds 60-80?",
    )
    assert reply is not None
    assert "Most:" in reply
    assert "Least:" in reply
    assert "Spread:" in reply


def test_reply_between_and_versus_form():
    reply = btd6_context_service.deterministic_round_range_comparison_reply(
        "compare the cash between rounds 10 and 20 versus rounds 30 to 40",
    )
    assert reply is not None
    assert "Rounds 30–40 earn more" in reply


def test_reply_abr_cue_routes_alternate_set():
    reply = btd6_context_service.deterministic_round_range_comparison_reply(
        "which earns more cash in abr, rounds 10-30 or rounds 30-50?",
    )
    assert reply is not None
    assert "alternate (ABR) round set" in reply


def test_single_range_defers_to_the_workflow():
    # One range → the round-cash workflow's job, not this comparison floor.
    assert (
        btd6_context_service.deterministic_round_range_comparison_reply(
            "how much cash do i earn from rounds 20-40?",
        )
        is None
    )


def test_no_cash_noun_defers():
    # Two ranges but no money word → not an income comparison.
    assert (
        btd6_context_service.deterministic_round_range_comparison_reply(
            "which is harder, rounds 20-40 or rounds 40-60?",
        )
        is None
    )


def test_no_comparison_signal_defers():
    # Cash noun + two ranges but no compare word ("and", not "or"/"vs"/"more").
    assert (
        btd6_context_service.deterministic_round_range_comparison_reply(
            "how much cash in rounds 20-40 and rounds 40-60",
        )
        is None
    )


def test_strategy_recommendation_defers():
    assert (
        btd6_context_service.deterministic_round_range_comparison_reply(
            "should i farm cash in rounds 20-40 or rounds 40-60",
        )
        is None
    )


def test_crosspath_codes_are_not_parsed_as_round_ranges():
    # "5-0-0 ninja … 0-5-0 wizard" must never be read as round ranges — a round
    # token is required before each range's first anchor.
    assert (
        btd6_context_service.deterministic_round_range_comparison_reply(
            "does a 5-0-0 ninja or a 0-5-0 wizard earn more cash",
        )
        is None
    )


# --- the dispatcher wiring -----------------------------------------------------


def test_dispatcher_routes_round_range_comparison():
    reply = btd6_context_service.deterministic_btd6_list_reply(
        "which earns more cash, rounds 20-40 or rounds 40-60?",
    )
    assert reply is not None
    assert "Cash comparison" in reply


def test_dispatcher_ordinary_round_cash_question_falls_through():
    # A single-range cash question is not a comparison — the dispatcher returns
    # None so the question reaches the round-cash workflow / model untouched.
    assert (
        btd6_context_service.deterministic_btd6_list_reply(
            "how much cash do i earn from rounds 20-40?",
        )
        is None
    )
