"""AI §7.6 — deterministic BTD6 *hero ability* roster.

The per-hero ability member of the BUG-0009 roster floor — the sibling of the
capability / bloon / relic rosters. "what abilities does Quincy have", "list
Adora's abilities" lists a hero's abilities (level + name + summary) so the model
can never mis-level / mislabel one (every ability name is grounded, so the
value-only faithfulness guard cannot catch a wrong level or ordering). These pin
the deterministic ``hero_abilities`` primitive + the floor reply / dispatcher
wiring, and the exclusivity with the hero *cost* comparison builder (same entity,
different shape) and the other floor builders.
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


# --- the primitive (btd6_data_service.hero_abilities) --------------------------


def test_abilities_returned_ascending_by_level():
    abilities = btd6_data_service.hero_abilities("quincy")
    assert abilities is not None
    levels = [ability.level for ability in abilities]
    assert levels == sorted(levels)
    # Quincy's two abilities, level-ordered.
    assert abilities[0].name == "Rapid Shot"
    assert abilities[0].level == 3


def test_resolves_alias_and_id():
    # "gwen" (alias) and the canonical id both resolve.
    by_alias = btd6_data_service.hero_abilities("gwen")
    by_id = btd6_data_service.hero_abilities("gwendolin")
    assert by_alias is not None and by_id is not None
    assert [a.name for a in by_alias] == [a.name for a in by_id]


def test_unknown_hero_returns_none_never_guesses():
    assert btd6_data_service.hero_abilities("not a hero") is None


def test_every_hero_has_resolvable_abilities():
    # Data-completeness guard: the roster floor is only safe because every hero
    # carries abilities — if a future dataset drops them, this fails loudly.
    for hero in btd6_data_service.get_dataset().heroes:
        abilities = btd6_data_service.hero_abilities(hero.id)
        assert abilities, f"{hero.canonical} has no abilities"


# --- the floor reply (deterministic_hero_ability_roster_reply) -----------------


def test_reply_lists_a_heros_abilities_with_levels():
    reply = btd6_context_service.deterministic_hero_ability_roster_reply(
        "what abilities does quincy have?",
    )
    assert reply is not None
    assert "Quincy — abilities" in reply
    assert "Rapid Shot" in reply
    assert "Level 3" in reply


def test_reply_possessive_phrasing():
    reply = btd6_context_service.deterministic_hero_ability_roster_reply(
        "list adora's abilities",
    )
    assert reply is not None
    assert "Adora — abilities" in reply


def test_cost_cue_defers_to_hero_cost_builder():
    # "ability" + a cost cue → the hero COST comparison builder's job, not this.
    assert (
        btd6_context_service.deterministic_hero_ability_roster_reply(
            "is quincy or adora's ability cheaper",
        )
        is None
    )


def test_no_hero_defers():
    assert (
        btd6_context_service.deterministic_hero_ability_roster_reply(
            "what abilities are in btd6",
        )
        is None
    )


def test_two_heroes_defers_as_ambiguous():
    assert (
        btd6_context_service.deterministic_hero_ability_roster_reply(
            "what abilities do quincy and adora have",
        )
        is None
    )


def test_no_ability_cue_defers():
    assert (
        btd6_context_service.deterministic_hero_ability_roster_reply(
            "what does quincy do",
        )
        is None
    )


def test_strategy_question_defers():
    assert (
        btd6_context_service.deterministic_hero_ability_roster_reply(
            "what is quincy's best ability",
        )
        is None
    )


# --- the dispatcher wiring + exclusivity ---------------------------------------


def test_dispatcher_routes_hero_ability_roster():
    reply = btd6_context_service.deterministic_btd6_list_reply(
        "what abilities does quincy have?",
    )
    assert reply is not None
    assert "Quincy — abilities" in reply


def test_ability_question_only_the_ability_builder_fires():
    phrase = "list adora's abilities"
    firing = [
        builder.__name__
        for builder in btd6_context_service._BTD6_LIST_BUILDERS
        if builder(phrase) is not None
    ]
    assert firing == ["deterministic_hero_ability_roster_reply"]
