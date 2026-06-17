"""BUG-0009 slice 2 — deterministic "Geraldo items per level".

The model, asked "what does Geraldo unlock at each level", assembles the
level→item grouping itself and mislabels which item unlocks when (every name is
grounded, so the value-only faithfulness guard passes the wrong grouping). These
pin the deterministic grouping + reply that now own the labelled answer, plus
the dispatcher that fronts the BUG-0009 floor.
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


# --- the grouping (btd6_data_service.geraldo_items_by_unlock_level) ------------


def test_grouping_is_ascending_by_level_and_covers_every_item():
    grouped = btd6_data_service.geraldo_items_by_unlock_level()
    levels = [lvl for lvl, _ in grouped]
    assert levels == sorted(levels), "levels must be ascending"
    assert len(set(levels)) == len(levels), "one entry per level (deduped)"
    total = sum(len(rows) for _, rows in grouped)
    assert total == len(btd6_data_service.get_dataset().geraldo_items)


def test_grouping_assigns_each_item_to_its_real_unlock_level():
    grouped = dict(btd6_data_service.geraldo_items_by_unlock_level())
    for level, rows in grouped.items():
        for item in rows:
            assert item.unlock_level == level


def test_starting_items_grouped_under_level_zero():
    """The fresh-Geraldo starting items unlock at level 0 (the bug mislabels
    these as later unlocks)."""
    grouped = dict(btd6_data_service.geraldo_items_by_unlock_level())
    assert 0 in grouped
    assert {i.canonical for i in grouped[0]} >= {"Creepy Idol", "Shooty Turret"}


# --- the reply (deterministic_geraldo_per_level_reply) ------------------------


def test_full_per_level_question_lists_every_level():
    reply = btd6_context_service.deterministic_geraldo_per_level_reply(
        "what items does Geraldo unlock at each level"
    )
    assert reply is not None
    assert "by unlock level" in reply.lower() or "Start (level 0)" in reply
    # A late item must be under its real level, not freelanced earlier.
    assert "Paragon Power Totem" in reply
    assert "Genie Bottle" in reply


def test_list_geraldo_items_question_matches():
    reply = btd6_context_service.deterministic_geraldo_per_level_reply(
        "list Geraldo's items"
    )
    assert reply is not None
    assert "Geraldo" in reply


def test_specific_level_question_returns_only_that_levels_unlocks():
    reply = btd6_context_service.deterministic_geraldo_per_level_reply(
        "what does Geraldo unlock at level 7"
    )
    assert reply is not None
    assert "level 7" in reply.lower()
    assert "Blade Trap" in reply  # the genuine level-7 unlock
    # An item from a different level must not leak into the level-7 answer.
    assert "Paragon Power Totem" not in reply


def test_starting_kit_question_returns_only_level_zero_items():
    """The buffer-slice "starting kit" angle: "what does Geraldo start with" maps
    to his level-0 items (the kit before any level-ups), not the full grouping."""
    for phrase in (
        "what does Geraldo start with?",
        "what are Geraldo's starting items",
        "what does geraldo come with",
    ):
        reply = btd6_context_service.deterministic_geraldo_per_level_reply(phrase)
        assert reply is not None, phrase
        assert reply.startswith("**Geraldo starts with")
        # A level-0 item is present; a later-level one is not.
        assert "Creepy Idol" in reply
        assert "Blade Trap" not in reply  # a level-7 unlock


def test_starting_with_an_explicit_level_uses_that_level():
    """A 'start' cue that also names a level defers to the specific-level branch
    so "what does Geraldo start with at level 5" is the level-5 answer."""
    reply = btd6_context_service.deterministic_geraldo_per_level_reply(
        "what does geraldo start with at level 5"
    )
    assert reply is not None
    assert "level 5" in reply.lower()
    assert "Creepy Idol" not in reply


def test_level_with_no_unlock_says_so_honestly():
    """Level 1 unlocks nothing new — the honest deterministic answer, not an
    invented item."""
    reply = btd6_context_service.deterministic_geraldo_per_level_reply(
        "what does geraldo unlock at level 1"
    )
    assert reply is not None
    assert "no new shop item at level 1" in reply.lower()


def test_single_item_lookup_falls_through_to_model():
    """A specific-item question with no level/list cue is NOT this list family —
    it must return None so the model/tool answers it."""
    assert (
        btd6_context_service.deterministic_geraldo_per_level_reply(
            "what does the Genie Bottle do"
        )
        is None
    )


def test_strategy_question_falls_through():
    assert (
        btd6_context_service.deterministic_geraldo_per_level_reply(
            "what is the best Geraldo item"
        )
        is None
    )


def test_non_geraldo_question_falls_through():
    assert (
        btd6_context_service.deterministic_geraldo_per_level_reply(
            "what items unlock per level"
        )
        is None
    )


# --- the dispatcher (deterministic_btd6_list_reply) ---------------------------


def test_dispatcher_routes_geraldo_per_level():
    reply = btd6_context_service.deterministic_btd6_list_reply(
        "what does Geraldo unlock per level"
    )
    assert reply is not None
    assert "Geraldo" in reply


def test_dispatcher_routes_mk_reference():
    """The slice-1 MK family still flows through the unified dispatcher."""
    reply = btd6_context_service.deterministic_btd6_list_reply(
        "what are all the monkey knowledges related to the farm"
    )
    assert reply is not None
    assert "Banana Farm" in reply


def test_dispatcher_returns_none_for_ordinary_question():
    assert (
        btd6_context_service.deterministic_btd6_list_reply(
            "how much does a dart monkey cost"
        )
        is None
    )
