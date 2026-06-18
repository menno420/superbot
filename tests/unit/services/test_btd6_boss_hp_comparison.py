"""AI §7.5 — deterministic BTD6 *boss tier-HP* comparison.

The boss member of the multi-entity comparison floor — the sibling of the tower /
hero / paragon cost comparisons. "which boss has the most health at tier 5", "is
Lych or Vortex tougher at tier 3" ranks bosses by their per-tier health so the
model can never mis-state which is tougher / by how much (every HP figure is
grounded, so the value-only faithfulness guard cannot catch a wrong ranking).
These pin the two reply shapes (named-boss ranking + superlative-over-all), the
required-tier fail-closed behaviour, elite handling, and the exclusivity with the
boss-immunity floor (same entity, different shape) and the other floor builders.
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


# --- the two reply shapes ------------------------------------------------------


def test_superlative_ranks_all_bosses_at_a_tier():
    reply = btd6_context_service.deterministic_boss_hp_comparison_reply(
        "which boss has the most health at tier 5",
    )
    assert reply is not None
    assert "Boss HP at tier 5" in reply
    # All seven bosses are ranked.
    assert reply.count("•") == 7
    assert "has the most health at tier 5" in reply


def test_named_bosses_ranked():
    reply = btd6_context_service.deterministic_boss_hp_comparison_reply(
        "is lych or vortex tougher at tier 3",
    )
    assert reply is not None
    assert "Lych" in reply
    assert "Vortex" in reply
    # Only the two named bosses appear.
    assert reply.count("•") == 2


def test_elite_uses_elite_tiers():
    normal = btd6_context_service.deterministic_boss_hp_comparison_reply(
        "which boss has the most hp at tier 5",
    )
    elite = btd6_context_service.deterministic_boss_hp_comparison_reply(
        "which boss has the most hp at elite tier 5",
    )
    assert normal is not None and elite is not None
    assert "elite tier 5" in elite
    # Elite HP is strictly higher than normal at the same tier, so the rendered
    # numbers differ — proves the elite branch reads elite_tiers.
    assert elite != normal


def test_least_superlative_ranks_ascending():
    reply = btd6_context_service.deterministic_boss_hp_comparison_reply(
        "which boss has the least health at tier 1",
    )
    assert reply is not None
    assert "ranked (least first)" in reply
    assert "has the least health at tier 1" in reply


# --- fail-closed + deferral ----------------------------------------------------


def test_missing_tier_defers_as_ambiguous():
    # No tier → a boss has five HP values, so the comparison is ambiguous.
    assert (
        btd6_context_service.deterministic_boss_hp_comparison_reply(
            "which boss has the most health",
        )
        is None
    )


def test_single_boss_lookup_defers():
    # One boss + a tier is a value lookup, not a ranking — the faithfulness guard
    # already covers a wrong single value.
    assert (
        btd6_context_service.deterministic_boss_hp_comparison_reply(
            "what is the hp of lych at tier 3",
        )
        is None
    )


def test_immunity_cue_defers_to_immunity_floor():
    assert (
        btd6_context_service.deterministic_boss_hp_comparison_reply(
            "which boss is most immune to fire at tier 5",
        )
        is None
    )


def test_strategy_question_defers():
    assert (
        btd6_context_service.deterministic_boss_hp_comparison_reply(
            "how do i beat the toughest boss at tier 5",
        )
        is None
    )


def test_no_hp_cue_defers():
    assert (
        btd6_context_service.deterministic_boss_hp_comparison_reply(
            "which boss is fastest at tier 5",
        )
        is None
    )


# --- the dispatcher wiring + exclusivity ---------------------------------------


def test_dispatcher_routes_boss_hp_comparison():
    reply = btd6_context_service.deterministic_btd6_list_reply(
        "which boss has the most health at tier 5",
    )
    assert reply is not None
    assert "Boss HP at tier 5" in reply


def test_only_the_boss_hp_builder_fires():
    phrase = "is lych or vortex tougher at tier 3"
    firing = [
        builder.__name__
        for builder in btd6_context_service._BTD6_LIST_BUILDERS
        if builder(phrase) is not None
    ]
    assert firing == ["deterministic_boss_hp_comparison_reply"]
