"""AI §7.6 slot-4 reframe — deterministic BTD6 *bloon-modifier* explainer.

Camo / Fortified / Regrow are universal *modifiers* applied to ANY bloon, not
per-type properties — so the night-queue slot-4 "bloon property roster" was
reframed: there is no clean roster (it would wrongly imply only DDT can be camo),
but a grounded *explainer* is the genuinely useful answer the data supports. This
floor OWNS that explanation off the dataset's ``category=="modifier"`` marker
entries, fixing both the wrong-roster and the general-path freelance (BUG-0009).
These pin the ``bloon_modifiers`` primitive + the floor reply / dispatcher wiring,
and the deferral to the capability roster (towers detecting camo) so they never
both fire.
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


# --- the primitive (btd6_data_service.bloon_modifiers) -------------------------


def test_primitive_returns_only_modifier_markers():
    mods = btd6_data_service.bloon_modifiers()
    assert {m.id for m in mods} == {"camo", "fortified", "regrow"}
    for m in mods:
        assert m.category == "modifier"
        assert m.description  # each carries a grounded explanation


# --- the floor reply (deterministic_bloon_modifier_reply) ---------------------


def test_reply_explains_a_named_modifier_and_corrects_the_assumption():
    reply = btd6_context_service.deterministic_bloon_modifier_reply(
        "what does camo do?",
    )
    assert reply is not None
    assert "Camo is a bloon modifier, not a bloon type" in reply
    # carries the grounded description and the universal-modifier correction.
    assert "camo detection" in reply
    assert "no fixed list" in reply


def test_reply_reframes_the_which_bloons_are_camo_roster_attempt():
    # The exact slot-4 trap: a roster would imply only DDT is camo. The explainer
    # corrects it instead.
    reply = btd6_context_service.deterministic_bloon_modifier_reply(
        "which bloons are camo?",
    )
    assert reply is not None
    assert "not a bloon type" in reply


def test_reply_handles_fortified_and_regrow():
    for word, label in (("fortified", "Fortified"), ("regrow", "Regrow")):
        reply = btd6_context_service.deterministic_bloon_modifier_reply(
            f"what is the {word} property",
        )
        assert reply is not None
        assert f"{label} is a bloon modifier" in reply


def test_reply_lists_all_modifiers_on_a_generic_ask():
    reply = btd6_context_service.deterministic_bloon_modifier_reply(
        "what are the bloon modifiers",
    )
    assert reply is not None
    assert "bloon modifiers" in reply
    for label in ("Camo", "Fortified", "Regrow"):
        assert label in reply


def test_tower_capability_question_defers():
    # "does the dartling gunner detect camo" is the capability floor's / model's
    # job — a detection verb + a named tower → defer.
    assert (
        btd6_context_service.deterministic_bloon_modifier_reply(
            "does the dartling gunner detect camo",
        )
        is None
    )


def test_tower_roster_camo_question_defers():
    # "which towers detect camo" belongs to the capability roster.
    assert (
        btd6_context_service.deterministic_bloon_modifier_reply(
            "which towers detect camo",
        )
        is None
    )


def test_strategy_question_defers():
    assert (
        btd6_context_service.deterministic_bloon_modifier_reply(
            "what is the best tower against camo bloons",
        )
        is None
    )


def test_no_modifier_named_defers():
    assert (
        btd6_context_service.deterministic_bloon_modifier_reply(
            "what is a moab",
        )
        is None
    )


# --- the dispatcher wiring + exclusivity --------------------------------------


def test_dispatcher_routes_bloon_modifier_explainer():
    reply = btd6_context_service.deterministic_btd6_list_reply(
        "explain the regrow property",
    )
    assert reply is not None
    assert "Regrow is a bloon modifier" in reply


def test_modifier_question_only_one_builder_fires():
    phrase = "what does the fortified property mean"
    firing = [
        builder.__name__
        for builder in btd6_context_service._BTD6_LIST_BUILDERS
        if builder(phrase) is not None
    ]
    assert firing == ["deterministic_bloon_modifier_reply"]
