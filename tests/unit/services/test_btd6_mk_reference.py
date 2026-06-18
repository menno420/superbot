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
    return {
        mk.canonical for mk in btd6_data_service.monkey_knowledge_referencing(tower)
    }


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
    """ "Arcane Spike does extra damage" (Arcane Impale) is a Wizard upgrade —
    the weak "spike" alias must not pull it into the Spike Factory list."""
    assert "Arcane Impale" not in _names("spike factory")


def test_class_wide_relation_is_scope_phrased_not_just_unnamed():
    """Class-wide = an explicit class-scope phrase ("all Primary towers",
    "Military Monkeys"), NOT merely "names no tower" — that looser test wrongly
    catches tower-specific points the name index missed and power/economy points."""
    primary = {
        mk.canonical for mk in btd6_data_service.monkey_knowledge_class_wide("primary")
    }
    assert "Come On Everybody!" in primary
    # Primary-tab but tower-specific (Ice Monkey freeze) / global economy — excluded:
    assert "Icy Chill" not in primary
    assert "More Cash" not in primary

    military = {
        mk.canonical for mk in btd6_data_service.monkey_knowledge_class_wide("military")
    }
    assert "Advanced Logistics" in military  # "All Military Monkeys base costs…"
    # Military-tab but tower/power-specific — excluded:
    assert "Charged Chinooks" not in military
    assert "Targeted Pineapples" not in military


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


def test_reply_header_is_grammatical_and_affect_framed():
    reply = btd6_context_service.deterministic_mk_reference_reply(
        "which MK affects the glue gunner",
    )
    assert reply is not None
    # "Monkey Knowledge that affects the Glue Gunner" — grammatical, and framed
    # as "affects" (names + class-wide), not the old ungrammatical
    # "Monkey Knowledge that reference".
    assert "Monkey Knowledge that affects the Glue Gunner" in reply
    assert "Monkey Knowledge that reference " not in reply


def test_reply_includes_class_wide_tab_mk_that_affects_the_tower():
    """The owner ask: "which MK affects the glue gunner" must INCLUDE the
    class-wide Primary point (Come On Everybody!), not just name-matching ones —
    and must not drop into the model-refusal path (2026-06-18)."""
    # Glue Gunner is a Primary tower → Come On Everybody! applies class-wide.
    reply = btd6_context_service.deterministic_mk_reference_reply(
        "which MK affects the glue gunner",
    )
    assert reply is not None
    assert "Come On Everybody" in reply
    assert "Names the Glue Gunner" in reply
    assert "Class-wide Primary" in reply
    # A Military tower lists the Military class-wide points instead.
    sniper = btd6_context_service.deterministic_mk_reference_reply(
        "which MK affects the sniper",
    )
    assert sniper is not None
    assert "Ceramic Shock" in sniper  # names the Sniper
    assert "Advanced Logistics" in sniper  # class-wide Military
    assert "Class-wide Military" in sniper
    # A class-wide point that DOESN'T scope to the whole class must not appear —
    # Icy Chill (Ice Monkey freeze) is Primary-tab but tower-specific.
    assert "Icy Chill" not in reply


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


def test_reply_for_tower_with_no_affecting_mk_is_honest():
    """A tower that no point names AND whose class has no class-wide point gets an
    explicit deterministic "none", never a model-assembled (mislabel-prone) list."""
    # Need a tower with empty named relation AND empty class-wide relation.
    empty_tower = next(
        (
            t
            for t in btd6_data_service.get_dataset().towers
            if not btd6_data_service.monkey_knowledge_referencing(t)
            and not btd6_data_service.monkey_knowledge_class_wide(t.category)
        ),
        None,
    )
    if empty_tower is None:
        pytest.skip("every tower currently has at least one affecting MK")
    reply = btd6_context_service.deterministic_mk_reference_reply(
        f"which monkey knowledges affect the {empty_tower.canonical}",
    )
    assert reply is not None
    assert "No Monkey Knowledge specifically affects" in reply
    assert empty_tower.canonical in reply
