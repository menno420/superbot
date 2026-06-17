"""AI §7.6 — deterministic BTD6 *Monkey-Knowledge by tab/category* roster.

The Monkey-Knowledge member of the BUG-0009 roster floor — the sibling of the
relic roster (``test_btd6_relic_roster.py``) and the capability roster. "what
Support monkey knowledges are there", "list all Military monkey knowledge"
buckets the catalog's MK by its in-game tab so the model can never mis-bucket the
list (every MK name is grounded, so the value-only faithfulness guard cannot
catch a mis-*grouping* — the exact owner-reported "related to the farm" miss).
These pin the deterministic ``monkey_knowledge_by_category`` primitive + the
floor reply / dispatcher wiring, and the exclusivity with the sibling
``deterministic_mk_reference_reply`` (which owns "MK related to <tower>").
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


# --- the primitive (btd6_data_service.monkey_knowledge_by_category) ------------


def test_grouping_covers_every_knowledge_exactly_once():
    grouped = btd6_data_service.monkey_knowledge_by_category()
    total = sum(len(rows) for rows in grouped.values())
    assert total == len(btd6_data_service.get_dataset().monkey_knowledge)
    # Every grouped point actually carries the tab it is filed under.
    for category, rows in grouped.items():
        for mk in rows:
            assert mk.category == category


def test_grouping_is_name_sorted_within_a_tab():
    grouped = btd6_data_service.monkey_knowledge_by_category()
    for rows in grouped.values():
        names = [mk.canonical.lower() for mk in rows]
        assert names == sorted(names)


def test_grouping_uses_the_in_game_tab_order():
    grouped = btd6_data_service.monkey_knowledge_by_category()
    assert tuple(grouped.keys()) == (
        "Primary",
        "Military",
        "Magic",
        "Support",
        "Heroes",
        "Powers",
    )


# --- the floor reply (deterministic_mk_category_roster_reply) ------------------


def test_reply_lists_a_named_tab():
    reply = btd6_context_service.deterministic_mk_category_roster_reply(
        "what support monkey knowledges are there?",
    )
    assert reply is not None
    assert "Support tab" in reply
    # A real Support point is present; a Primary one is not.
    assert "Bank Deposits" in reply
    assert "4 and 4" not in reply


def test_reply_count_matches_the_grouping():
    reply = btd6_context_service.deterministic_mk_category_roster_reply(
        "list all military monkey knowledge",
    )
    assert reply is not None
    grouped = btd6_data_service.monkey_knowledge_by_category()
    assert f"({len(grouped['Military'])})" in reply
    assert "Military tab" in reply


def test_single_mk_lookup_without_a_tab_defers():
    # No tab keyword → an effect lookup, not a roster → defer to the model.
    assert (
        btd6_context_service.deterministic_mk_category_roster_reply(
            "what does more cash monkey knowledge do?",
        )
        is None
    )


def test_no_mk_cue_defers():
    assert (
        btd6_context_service.deterministic_mk_category_roster_reply(
            "what support towers are there?",
        )
        is None
    )


def test_strategy_question_defers():
    assert (
        btd6_context_service.deterministic_mk_category_roster_reply(
            "what is the best support monkey knowledge?",
        )
        is None
    )


def test_tower_cue_defers_to_the_relation_builder():
    # Names a tower → the "MK related to <tower>" builder owns this; the category
    # roster must defer so the two MK builders never both fire.
    phrase = "what military monkey knowledge relate to the dart monkey"
    assert (
        btd6_context_service.deterministic_mk_category_roster_reply(phrase) is None
    )
    # ...and the relation builder is the one that fires.
    assert btd6_context_service.deterministic_mk_reference_reply(phrase) is not None


# --- the dispatcher wiring + exclusivity ---------------------------------------


def test_dispatcher_routes_mk_category_roster():
    reply = btd6_context_service.deterministic_btd6_list_reply(
        "which magic monkey knowledges are there?",
    )
    assert reply is not None
    assert "Magic tab" in reply


def test_mk_category_question_only_one_builder_fires():
    phrase = "list every primary monkey knowledge"
    firing = [
        builder.__name__
        for builder in btd6_context_service._BTD6_LIST_BUILDERS
        if builder(phrase) is not None
    ]
    assert firing == ["deterministic_mk_category_roster_reply"]
