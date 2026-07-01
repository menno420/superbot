"""BTD6 round-range bloon roster — the "list all the bloons from r29 till r63" fix.

Owner-reported miss (2026-07-01): a round RANGE in a bloon-listing question only
grounded the two endpoint round numbers (the NL resolver extracts isolated round
numbers with no range concept), so the answer listed rounds 29 + 63's bloons
instead of the whole span. These pin the deterministic
``round_range_bloon_roster`` primitive, the ``deterministic_round_range_bloons_reply``
floor + its exclusivity with the economy/comparison round builders, and the
Ask-modal path wiring (``answer_question``) that previously bypassed the floor.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import (  # noqa: E402
    btd6_ai_service,
    btd6_context_service,
    btd6_data_service,
)


@pytest.fixture(autouse=True)
def _reset_dataset_cache():
    btd6_data_service.reset_cache()
    yield
    btd6_data_service.reset_cache()


# --- the primitive (btd6_data_service.round_range_bloon_roster) ----------------


def test_roster_enumerates_every_round_in_the_range():
    result = btd6_data_service.round_range_bloon_roster(29, 63)
    assert result["found"] is True
    # The whole inclusive span, not two endpoints (the bug: only 29 + 63 grounded).
    assert result["round_start"] == 29
    assert result["round_end"] == 63
    assert result["rounds_in_range"] == 35
    assert result["roundset_label"] == "standard"


def test_roster_collects_distinct_types_across_the_span():
    result = btd6_data_service.round_range_bloon_roster(29, 63)
    names = [entry["bloon"] for entry in result["roster"]]
    # A range that only sampled its endpoints would miss the mid-range types.
    # Ceramics/MOABs/BFB appear well inside 29-63, never at round 29 alone.
    for expected in ("Ceramic Bloon", "MOAB", "BFB"):
        assert expected in names, f"{expected} missing from the range roster"
    # Distinct — each base type appears exactly once in the roster.
    assert len(names) == len(set(names))


def test_roster_first_last_round_and_counts_are_bounded_to_the_range():
    result = btd6_data_service.round_range_bloon_roster(29, 63)
    for entry in result["roster"]:
        assert 29 <= entry["first_round"] <= entry["last_round"] <= 63
        assert entry["rounds_present"] >= 1
        assert entry["total"] >= entry["rounds_present"]  # >=1 spawned per round


def test_roster_normalises_reversed_endpoints():
    forward = btd6_data_service.round_range_bloon_roster(29, 63)
    reversed_ = btd6_data_service.round_range_bloon_roster(63, 29)
    assert reversed_["round_start"] == 29
    assert reversed_["round_end"] == 63
    assert [e["bloon_id"] for e in reversed_["roster"]] == [
        e["bloon_id"] for e in forward["roster"]
    ]


def test_roster_records_modifiers_seen_across_the_range():
    result = btd6_data_service.round_range_bloon_roster(29, 63)
    # Regrow / Camo / Fortified all appear inside this span; they are gathered as
    # a set of modifiers seen, not split into per-variant roster rows.
    assert set(result["modifiers_seen"]) & {"Regrow", "Camo", "Fortified"}


def test_roster_fails_closed_on_unknown_set_and_empty_range():
    assert btd6_data_service.round_range_bloon_roster(29, 63, "nonsense")["found"] is False
    # Valid rounds are 1-140; a range fully outside has no rounds.
    assert btd6_data_service.round_range_bloon_roster(200, 220)["found"] is False


def test_roster_supports_the_abr_round_set():
    result = btd6_data_service.round_range_bloon_roster(20, 40, "abr")
    assert result["found"] is True
    assert result["roundset"] == "alternate"
    assert "ABR" in result["roundset_label"] or "alternate" in result["roundset_label"]


# --- the floor builder (deterministic_round_range_bloons_reply) ----------------


def test_builder_owns_the_reported_query():
    reply = btd6_context_service.deterministic_round_range_bloons_reply(
        "list all the bloons from r29 till r63",
    )
    assert reply is not None
    assert "rounds 29" in reply and "63" in reply
    assert "Ceramic Bloon" in reply and "MOAB" in reply
    assert len(reply) <= 1900


@pytest.mark.parametrize(
    "phrase",
    [
        "list all the bloons from r29 till r63",
        "what bloons spawn between rounds 40 and 60",
        "which bloons appear in rounds 29-63",
        "what blimps show up from round 80 to 100",
    ],
)
def test_builder_fires_on_range_bloon_phrasings(phrase: str):
    assert btd6_context_service.deterministic_round_range_bloons_reply(phrase) is not None


@pytest.mark.parametrize(
    "phrase",
    [
        # No range — a single round is a single-round question, not this floor.
        "what bloons are on round 63",
        # No bloon cue — an economy range belongs to the economy builder.
        "what's the total rbe from rounds 29 to 63",
        "how much cash do i earn from rounds 20-40",
        # Two ranges — the comparison builder owns that.
        "which has more bloons, rounds 20-40 or 40-60",
        # Not a range question at all.
        "what is a ceramic bloon",
    ],
)
def test_builder_defers_outside_its_shape(phrase: str):
    assert btd6_context_service.deterministic_round_range_bloons_reply(phrase) is None


def test_builder_routes_abr_when_cued():
    reply = btd6_context_service.deterministic_round_range_bloons_reply(
        "list the bloons in rounds 20-40 in abr",
    )
    assert reply is not None
    assert "alternate" in reply.lower() or "ABR" in reply


# --- the Ask-modal path wiring (btd6_ai_service.answer_question) ----------------


@pytest.mark.asyncio
async def test_ask_path_serves_the_range_floor_not_the_endpoint_round():
    # Before the fix, the Ask path answered "Round 29 …" (deterministic_answer
    # took intent.rounds[0]); now the range floor owns the whole-span answer.
    response = await btd6_ai_service.answer_question("list all the bloons from r29 till r63")
    body = response.short_answer
    assert "Bloons across rounds 29" in body
    assert "Ceramic Bloon" in body and "MOAB" in body
    # Not the single-round headline the endpoint-only path produced.
    assert not response.title.startswith("Round 29")


@pytest.mark.asyncio
async def test_ask_path_single_round_still_uses_the_entity_answer():
    # A single round is not a range — the normal deterministic round answer wins.
    response = await btd6_ai_service.answer_question("what happens on round 63")
    assert response.title.startswith("Round 63")
