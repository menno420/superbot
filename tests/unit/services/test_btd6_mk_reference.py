"""BUG-0009 slice 1 — deterministic "Monkey Knowledge related to <tower>".

The model, asked "which monkey knowledges relate to the farm", listed the whole
Support *category* and labelled it farm-related (every name grounded, so the
value-only faithfulness guard passed the wrong grouping). These pin the
deterministic relation + reply that now own the labelled answer.
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


# --- the relation (btd6_data_service.monkey_knowledge_referencing) -------------


def _names(tower_surface: str) -> set[str]:
    tower = btd6_data_service.find_tower(tower_surface)
    assert tower is not None
    return {mk.canonical for mk in btd6_data_service.monkey_knowledge_referencing(tower)}


def test_farm_relation_is_the_genuinely_related_mk_not_the_whole_category():
    """The exact BUG-0009 case: only the MK that name the farm or its upgrades,
    NOT the whole Support tab. Big Traps / One More Spike (Engineer / Spike
    Factory MK, both Support-tab) must be excluded."""
    names = _names("farm")
    # Strong (canonical/upgrade) + the weak "Farm" alias hit, all genuine:
    assert {
        "Farm Subsidy",  # "First Banana Farm each game costs 100 less"
        "More Valuable Bananas",  # Valuable Bananas upgrade
        "Bank Deposits",  # Monkey Banks
        "Bigger Banks",  # Monkey Banks
        "Backroom Deals",  # IMF Loan
        "Healthy Bananas",  # Marketplaces / Central Markets
        "Flat Pack Buildings",  # "Farm and Village …"
    } <= names
    # The owner's reported false positives — other towers' Support-tab MK:
    assert "Big Traps" not in names  # Bloon Trap (Engineer)
    assert "One More Spike" not in names  # Spike Factory
    assert "Vigilant Sentries" not in names  # Sentry Turrets (Engineer)


def test_spike_factory_excludes_road_spikes_power_mk():
    """A weak "spike" alias hit on a Powers-tab MK (the Road Spikes power's
    "Just One More" / "Pre-game Prep") must not attach to the Spike Factory."""
    names = _names("spike factory")
    assert "One More Spike" in names  # canonical "Spike Factory" in description
    assert "Very Shreddy" in names  # MOAB SHREDR upgrade
    assert "Just One More" not in names  # Road Spikes (Powers tab)
    assert "Pre-game Prep" not in names  # Road Spikes (Powers tab)


def test_strong_match_wins_over_a_different_towers_alias():
    """"Arcane Spike does extra damage" (Arcane Impale) is a Wizard upgrade —
    the weak "spike" alias must not pull it into the Spike Factory list."""
    assert "Arcane Impale" not in _names("spike factory")


def test_relation_is_memoized_stable():
    tower = btd6_data_service.find_tower("druid")
    first = btd6_data_service.monkey_knowledge_referencing(tower)
    second = btd6_data_service.monkey_knowledge_referencing(tower)
    assert first == second
    assert len(first) >= 1


# --- the reply (btd6_context_service.deterministic_mk_reference_reply) ---------


def test_reply_for_the_bug_phrasing_lists_only_farm_mk():
    reply = btd6_context_service.deterministic_mk_reference_reply(
        "what are all the monkey knowledges related to the farm",
    )
    assert reply is not None
    assert "Banana Farm" in reply
    assert "Farm Subsidy" in reply
    assert "More Valuable Bananas" in reply
    # The wrong-grouping names the model produced must NOT appear:
    assert "Big Traps" not in reply
    assert "Vigilant Sentries" not in reply


def test_reply_handles_mk_abbreviation_and_relation_cue():
    reply = btd6_context_service.deterministic_mk_reference_reply(
        "list all mk for spike factory",
    )
    assert reply is not None
    assert "Spike Factory" in reply
    assert "Just One More" not in reply


@pytest.mark.parametrize(
    "text",
    [
        "what does Farm Subsidy do",  # single-MK lookup, no list cue
        "which hero is best for the farm",  # strategy/opinion
        "how much does a banana farm cost",  # no MK cue
        "list all the heroes",  # MK + list cue absent (no "mk"/"monkey knowledge")
        "",  # empty
    ],
)
def test_reply_is_conservative_and_returns_none(text):
    assert btd6_context_service.deterministic_mk_reference_reply(text) is None


def test_reply_for_tower_with_no_referenced_mk_is_honest():
    """A tower no MK references gets an explicit deterministic "none", never a
    model-assembled (and therefore mislabel-prone) list."""
    # Find a tower with an empty relation, if any exists in the dataset.
    empty_tower = next(
        (
            t
            for t in btd6_data_service.get_dataset().towers
            if not btd6_data_service.monkey_knowledge_referencing(t)
        ),
        None,
    )
    if empty_tower is None:
        pytest.skip("every tower currently has at least one referencing MK")
    reply = btd6_context_service.deterministic_mk_reference_reply(
        f"which monkey knowledges relate to the {empty_tower.canonical}",
    )
    assert reply is not None
    assert "No Monkey Knowledge specifically references" in reply
    assert empty_tower.canonical in reply
