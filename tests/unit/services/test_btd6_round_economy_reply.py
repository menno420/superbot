"""Deterministic "economy of round N" floor reply — RBE + cash + XP in one answer.

Consolidates the three round-economy stats (otherwise split across the cash
workflow, the XP floor reply, and no RBE reply) into one grounded answer that
mirrors the round embed's Economy field. These cover the reply's grounding,
roundset support, and defer paths; exclusivity with the narrower XP builder is
pinned by test_btd6_floor_builder_exclusivity.py.
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


def test_reply_includes_rbe_cash_and_xp():
    reply = btd6_context_service.deterministic_round_economy_reply(
        "what's the economy of round 63",
    )
    assert reply is not None
    entry = btd6_data_service.get_round(63)
    assert entry is not None
    assert entry.rbe is not None and f"{entry.rbe:,}" in reply
    assert entry.cash is not None and f"${entry.cash:,.0f}" in reply
    base_xp = btd6_data_service.round_base_xp(63)
    assert base_xp is not None and f"{base_xp:,}" in reply
    assert "Round 63" in reply


def test_reply_grounds_on_the_data_not_hardcoded():
    for rnd in (5, 50, 95):
        reply = btd6_context_service.deterministic_round_economy_reply(
            f"round {rnd} economy overview",
        )
        entry = btd6_data_service.get_round(rnd)
        assert reply is not None and entry is not None
        assert entry.rbe is not None and f"{entry.rbe:,}" in reply


def test_various_economy_cues_fire():
    for phrase in (
        "round 40 stats",
        "round 40 rewards",
        "round 40 summary",
        "what is the rbe of round 40",
        "round 40 economy breakdown",
    ):
        assert (
            btd6_context_service.deterministic_round_economy_reply(phrase) is not None
        ), phrase


def test_abr_roundset_is_supported():
    default_reply = btd6_context_service.deterministic_round_economy_reply(
        "economy of round 60",
    )
    abr_reply = btd6_context_service.deterministic_round_economy_reply(
        "economy of round 60 in abr",
    )
    assert default_reply is not None and abr_reply is not None
    assert "ABR" in abr_reply
    # ABR cash differs from the default set, so the two answers are not identical.
    assert abr_reply != default_reply


def test_defers_without_an_economy_cue():
    # No economy/stats/rbe cue → a bare "tell me about round 63" is not ours.
    assert (
        btd6_context_service.deterministic_round_economy_reply("tell me about round 63")
        is None
    )


def test_defers_without_a_round():
    assert (
        btd6_context_service.deterministic_round_economy_reply(
            "what economy relics exist"
        )
        is None
    )


def test_defers_for_out_of_range_round():
    assert (
        btd6_context_service.deterministic_round_economy_reply("economy of round 999")
        is None
    )


def test_dispatcher_routes_the_economy_reply():
    reply = btd6_context_service.deterministic_btd6_list_reply(
        "what's the economy of round 95",
    )
    assert reply is not None
    assert "Round 95" in reply


def test_pure_xp_question_routes_to_the_xp_builder_not_economy():
    # "how much xp does round 63 give" has no economy cue → economy defers and the
    # narrower XP builder owns it, even though economy is registered first.
    assert (
        btd6_context_service.deterministic_round_economy_reply(
            "how much xp does round 63 give",
        )
        is None
    )
