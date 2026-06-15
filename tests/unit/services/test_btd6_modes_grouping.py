"""BUG-0009 (mode groupings) — deterministic "list the BTD6 game modes".

The owner reported the model "badly grouped" game modes (calling a difficulty a
mode, etc.) — the same grounded-facts-wrong-assembly class as the MK-related and
Geraldo-per-level families. These pin the deterministic kind-grouping + reply
that now own the labelled answer, and its narrow routing (qualifier mentions of
"mode" must NOT fire).
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


# --- the grouping (btd6_data_service.modes_by_kind) ---------------------------


def test_grouping_orders_difficulty_then_mode_then_modifier():
    grouped = btd6_data_service.modes_by_kind()
    kinds = [kind for kind, _ in grouped]
    # The three known kinds present, in the intended presentation order.
    assert kinds[:3] == ["difficulty", "mode", "modifier"]


def test_grouping_covers_every_mode_exactly_once():
    grouped = btd6_data_service.modes_by_kind()
    total = sum(len(rows) for _, rows in grouped)
    assert total == len(btd6_data_service.get_dataset().modes)
    ids = [m.id for _, rows in grouped for m in rows]
    assert len(set(ids)) == len(ids)


def test_grouping_assigns_each_mode_to_its_real_kind():
    for kind, rows in btd6_data_service.modes_by_kind():
        for mode in rows:
            assert mode.kind == kind


def test_chimps_is_a_mode_not_a_difficulty():
    """The exact mislabel class: CHIMPS is a *mode*, Hard is a *difficulty*."""
    by_kind = dict(btd6_data_service.modes_by_kind())
    mode_names = {m.canonical for m in by_kind.get("mode", ())}
    diff_names = {m.canonical for m in by_kind.get("difficulty", ())}
    assert "CHIMPS" in mode_names
    assert "CHIMPS" not in diff_names
    assert {"Easy", "Medium", "Hard"} <= diff_names


# --- the reply (deterministic_modes_reply) ------------------------------------


def test_list_game_modes_question_groups_by_kind():
    reply = btd6_context_service.deterministic_modes_reply("list all the game modes")
    assert reply is not None
    assert "Difficulties" in reply
    assert "Game modes" in reply
    assert "CHIMPS" in reply
    assert "Easy" in reply


def test_how_many_modes_question_matches():
    reply = btd6_context_service.deterministic_modes_reply(
        "how many game modes are there"
    )
    assert reply is not None
    assert "Modifiers" in reply


def test_what_are_all_the_difficulties_matches():
    reply = btd6_context_service.deterministic_modes_reply(
        "what are all the difficulties"
    )
    assert reply is not None
    assert "Hard" in reply


def test_single_mode_lookup_falls_through_to_model():
    """A specific-mode question (no list intent) is NOT this family."""
    assert (
        btd6_context_service.deterministic_modes_reply("what does CHIMPS mode mean")
        is None
    )


def test_mode_as_qualifier_does_not_fire():
    """The over-route guard: "mode"/"difficulty" used as a qualifier on another
    entity must defer to the model, not dump the whole modes list."""
    assert (
        btd6_context_service.deterministic_modes_reply(
            "which towers work on impoppable mode"
        )
        is None
    )
    assert (
        btd6_context_service.deterministic_modes_reply(
            "list all the heroes for hard difficulty"
        )
        is None
    )


def test_strategy_question_falls_through():
    assert (
        btd6_context_service.deterministic_modes_reply("what is the best game mode")
        is None
    )


def test_non_modes_question_falls_through():
    assert btd6_context_service.deterministic_modes_reply("list all the towers") is None


# --- the dispatcher routes the modes family -----------------------------------


def test_dispatcher_routes_modes():
    reply = btd6_context_service.deterministic_btd6_list_reply(
        "what game modes are there"
    )
    assert reply is not None
    assert "Difficulties" in reply
