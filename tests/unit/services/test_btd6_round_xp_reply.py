"""Deterministic "XP for round N" floor reply + the round-embed Economy field.

The data layer (round_xp.json + round_base_xp/round_xp_earned) is pinned by
test_btd6_round_xp.py. These cover the two *surfaces* built on top: the
pre-emptive natural-language floor reply (btd6_context_service) and the round
detail embed's Economy field (btd6_response_builder via btd6_knowledge_service).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import (  # noqa: E402
    btd6_context_service,
    btd6_data_service,
    btd6_knowledge_service,
    btd6_response_builder,
)


@pytest.fixture(autouse=True)
def _reset_dataset_cache():
    btd6_data_service.reset_cache()
    yield
    btd6_data_service.reset_cache()


# --- the natural-language floor reply ------------------------------------------


def test_reply_answers_a_bare_round_xp_question():
    reply = btd6_context_service.deterministic_round_xp_reply(
        "how much xp does round 63 give",
    )
    assert reply is not None
    # Round 63 base = 90(63-50)+1620 = 2790.
    assert "Round 63" in reply
    assert "2,790 XP" in reply


def test_reply_grounds_on_the_data_helper_not_a_hardcoded_value():
    for rnd in (1, 20, 21, 50, 51, 100):
        reply = btd6_context_service.deterministic_round_xp_reply(f"xp for round {rnd}")
        base = btd6_data_service.round_base_xp(rnd)
        assert base is not None
        assert reply is not None
        assert f"{base:,}" in reply


def test_reply_applies_difficulty():
    reply = btd6_context_service.deterministic_round_xp_reply(
        "xp for round 10 on expert",
    )
    assert reply is not None
    # 220 base * 1.3 = 286.
    assert "Expert" in reply
    assert "286 XP" in reply


def test_reply_applies_freeplay():
    reply = btd6_context_service.deterministic_round_xp_reply(
        "how much xp does round 100 give in freeplay",
    )
    assert reply is not None
    # 6120 * 0.30 = 1836.
    assert "freeplay" in reply.lower()
    assert "1,836 XP" in reply


def test_reply_defers_without_an_xp_cue():
    assert (
        btd6_context_service.deterministic_round_xp_reply("what bloons are on round 63")
        is None
    )


def test_reply_defers_without_a_round():
    assert (
        btd6_context_service.deterministic_round_xp_reply(
            "how much xp to unlock the 2-0-4 super monkey",
        )
        is None
    )


def test_reply_defers_for_out_of_range_round():
    assert btd6_context_service.deterministic_round_xp_reply("xp for round 999") is None


def test_dispatcher_routes_the_round_xp_reply():
    reply = btd6_context_service.deterministic_btd6_list_reply(
        "how much xp does round 5 give",
    )
    assert reply is not None
    assert "Round 5" in reply


# --- the round embed Economy field ---------------------------------------------


def test_round_fact_carries_economy_stats():
    fact = btd6_knowledge_service.round_fact(63)
    assert fact is not None
    assert fact.base_xp == btd6_data_service.round_base_xp(63)
    # RBE / cash flow through from RoundEntry.
    entry = btd6_data_service.get_round(63)
    assert entry is not None
    assert fact.rbe == entry.rbe
    assert fact.cash == entry.cash


def test_for_round_renders_an_economy_field_with_xp():
    fact = btd6_knowledge_service.round_fact(63)
    assert fact is not None
    response = btd6_response_builder.for_round(fact)
    economy = dict(response.fields).get("Economy")
    assert economy is not None
    assert "XP" in economy
    base = btd6_data_service.round_base_xp(63)
    assert base is not None
    assert f"{base:,}" in economy
