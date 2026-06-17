"""AI §7.6 — deterministic BTD6 *relic* category/effect roster.

The relic member of the BUG-0009 roster floor — the sibling of the capability
roster (``test_btd6_capability_roster.py``) and the bloon roster
(``test_btd6_bloon_roster.py``). "what economy relics are there", "list all
offensive relics" buckets the Contested Territory relics by ``category`` so the
model can never mis-bucket the list (every relic name is grounded, so the
value-only faithfulness guard cannot catch a mis-*grouping*). These pin the
deterministic ``relics_by_category`` primitive + the floor reply / dispatcher
wiring, and the exclusivity with the other floor builders.
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


# --- the primitive (btd6_data_service.relics_by_category) ----------------------


def test_grouping_covers_every_relic_exactly_once():
    grouped = btd6_data_service.relics_by_category()
    total = sum(len(rels) for rels in grouped.values())
    assert total == len(btd6_data_service.list_ct_relics())
    # Every grouped relic actually carries the category it is filed under.
    for category, rels in grouped.items():
        for relic in rels:
            assert relic.category == category


def test_grouping_is_name_sorted_within_a_category():
    grouped = btd6_data_service.relics_by_category()
    for rels in grouped.values():
        names = [relic.canonical for relic in rels]
        assert names == sorted(names)


def test_grouping_uses_the_fixed_category_order():
    grouped = btd6_data_service.relics_by_category()
    assert tuple(grouped.keys()) == ("offense", "economy", "lives", "powerup", "utility")


# --- the floor reply (deterministic_relic_roster_reply) ------------------------


def test_reply_lists_a_named_category_with_effects():
    reply = btd6_context_service.deterministic_relic_roster_reply(
        "what economy relics are there?",
    )
    assert reply is not None
    assert "Economy relics" in reply
    # An economy relic + its effect line is present; an offense one is not.
    assert "El Dorado" in reply
    assert "Broken Heart" not in reply


def test_reply_offensive_keyword_routes_offense_category():
    reply = btd6_context_service.deterministic_relic_roster_reply(
        "list all offensive relics",
    )
    assert reply is not None
    assert "Offense relics" in reply
    assert "Sharpsplosion" in reply


def test_reply_all_relics_groups_by_category():
    reply = btd6_context_service.deterministic_relic_roster_reply(
        "list all the relics",
    )
    assert reply is not None
    assert "relics by category" in reply
    # Every category header appears in the grouped view.
    for label in ("Offense", "Economy", "Lives", "Power-up", "Utility"):
        assert label in reply


def test_single_relic_effect_lookup_defers():
    # Matches the enumeration regex by accident ("what ... relic") but names a
    # specific relic → an effect lookup, not a roster → defer to the model.
    assert (
        btd6_context_service.deterministic_relic_roster_reply(
            "what does the el dorado relic do?",
        )
        is None
    )


def test_no_relic_subject_defers():
    assert (
        btd6_context_service.deterministic_relic_roster_reply(
            "what economy towers are there?",
        )
        is None
    )


def test_strategy_question_defers():
    assert (
        btd6_context_service.deterministic_relic_roster_reply(
            "what is the best economy relic?",
        )
        is None
    )


# --- the dispatcher wiring + exclusivity ---------------------------------------


def test_dispatcher_routes_relic_roster():
    reply = btd6_context_service.deterministic_btd6_list_reply(
        "which relics are utility?",
    )
    assert reply is not None
    assert "Utility relics" in reply


def test_relic_question_only_the_relic_builder_fires():
    phrase = "what offensive relics are there"
    firing = [
        builder.__name__
        for builder in btd6_context_service._BTD6_LIST_BUILDERS
        if builder(phrase) is not None
    ]
    assert firing == ["deterministic_relic_roster_reply"]
