"""AI §7.6 — deterministic BTD6 *paragon ability* roster.

The per-paragon ability member of the BUG-0009 floor — the paragon sibling of the
hero-ability roster. "what abilities does the Ascended Shadow paragon have", "list
the dart monkey paragon's abilities" lists a paragon's curated activated/passive
abilities (name + kind + cooldown + summary) so the model can never invent /
mislabel one (every ability name is grounded, so the value-only faithfulness guard
cannot catch a wrong assembly). These pin the floor reply / dispatcher wiring, the
exclusivity with the paragon *cost* comparison builder (same entity, different
shape) and the hero-ability roster (a paragon question carries the literal
``paragon`` token; a hero question never does), and the owned empty case.
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


# --- the floor reply (deterministic_paragon_ability_roster_reply) --------------


def test_reply_lists_a_paragons_abilities_by_name():
    reply = btd6_context_service.deterministic_paragon_ability_roster_reply(
        "what abilities does the ascended shadow paragon have?",
    )
    assert reply is not None
    assert "Ascended Shadow — abilities" in reply
    assert "Grand Saboteur" in reply
    # Ascended Shadow's two abilities are both passive.
    assert "passive" in reply


def test_reply_resolves_paragon_by_tower_name():
    # "ninja monkey paragon" / "ninja paragon" resolves via the tower surface.
    reply = btd6_context_service.deterministic_paragon_ability_roster_reply(
        "list the ninja monkey paragon's abilities",
    )
    assert reply is not None
    assert "Ascended Shadow — abilities" in reply


def test_reply_owns_the_no_ability_paragon_case():
    # Apex Plasma Master has no curated activated/passive ability — the floor
    # still OWNS an explicit line so the model can't invent one.
    reply = btd6_context_service.deterministic_paragon_ability_roster_reply(
        "what abilities does the apex plasma master paragon have",
    )
    assert reply is not None
    assert "no special activated or passive ability" in reply


def test_activated_ability_shows_cooldown():
    # The BOMB paragon resolves cleanly via its tower surface ("bomb shooter").
    reply = btd6_context_service.deterministic_paragon_ability_roster_reply(
        "what abilities does the bomb shooter paragon have",
    )
    assert reply is not None
    assert "ISABM" in reply
    assert "cooldown" in reply


def test_cost_cue_defers_to_paragon_cost_builder():
    # "ability" + a cost cue → the paragon COST comparison builder's job, not this.
    assert (
        btd6_context_service.deterministic_paragon_ability_roster_reply(
            "is the ascended shadow paragon's ability cheaper than glaive dominus",
        )
        is None
    )


def test_no_paragon_token_defers_to_hero_builder():
    # No "paragon" token → not this builder's shape (a hero ability ask).
    assert (
        btd6_context_service.deterministic_paragon_ability_roster_reply(
            "what abilities does quincy have",
        )
        is None
    )


def test_no_resolvable_paragon_defers():
    assert (
        btd6_context_service.deterministic_paragon_ability_roster_reply(
            "what abilities do paragons have",
        )
        is None
    )


def test_two_paragons_defers_as_ambiguous():
    assert (
        btd6_context_service.deterministic_paragon_ability_roster_reply(
            "what abilities do the ascended shadow and glaive dominus paragons have",
        )
        is None
    )


def test_no_ability_cue_defers():
    assert (
        btd6_context_service.deterministic_paragon_ability_roster_reply(
            "what is the ascended shadow paragon",
        )
        is None
    )


def test_strategy_question_defers():
    assert (
        btd6_context_service.deterministic_paragon_ability_roster_reply(
            "what is the ascended shadow paragon's best ability",
        )
        is None
    )


# --- the dispatcher wiring + exclusivity ---------------------------------------


def test_dispatcher_routes_paragon_ability_roster():
    reply = btd6_context_service.deterministic_btd6_list_reply(
        "what abilities does the ascended shadow paragon have?",
    )
    assert reply is not None
    assert "Ascended Shadow — abilities" in reply


def test_ability_question_only_the_paragon_ability_builder_fires():
    phrase = "list the ascended shadow paragon's abilities"
    firing = [
        builder.__name__
        for builder in btd6_context_service._BTD6_LIST_BUILDERS
        if builder(phrase) is not None
    ]
    assert firing == ["deterministic_paragon_ability_roster_reply"]
