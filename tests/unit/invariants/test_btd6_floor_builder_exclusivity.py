"""Invariant: the BUG-0009 / §7.5 deterministic floor builders are mutually exclusive.

`btd6_context_service.deterministic_btd6_list_reply` fans out to a growing tuple
of narrow builders (MK · Geraldo · modes · cost-compare · difficulty-compare ·
round-range-compare). Each is meant to OWN exactly one list/comparison shape and
return ``None`` for everything else, so on a real question **exactly one** builder
fires; the dispatcher's order only resolves a *genuine* overlap (a two-tower cost
question reaching the multi-tower builder before the single-tower difficulty one).

Today that non-overlap is argued in prose and pinned only by per-builder tests. As
the floor grows, two builders silently claiming the same phrasing — or a new
builder shadowing an older one by dispatcher order — is a real regression class
the value-only faithfulness guard cannot see. This invariant makes the
mutual-exclusion contract executable: it runs **every** builder (not just the
dispatcher) against a curated corpus and asserts exactly one fires per
should-fire phrase (the expected one) and zero fire on a should-defer phrase.

Promotes the #950 session's Q-0089 idea to shipped code. The builder tuple is
imported live (`_BTD6_LIST_BUILDERS`), so a builder added to the dispatcher
without a corpus entry fails the coverage test below — keeping the contract honest.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import btd6_context_service, btd6_data_service  # noqa: E402

# (phrase, the builder __name__ that should own it). One representative phrase per
# builder shape — extend when a builder is added (the coverage test enforces it).
_SHOULD_FIRE: tuple[tuple[str, str], ...] = (
    (
        "what are all the monkey knowledges related to the farm",
        "deterministic_mk_reference_reply",
    ),
    (
        "what support monkey knowledges are there",
        "deterministic_mk_category_roster_reply",
    ),
    (
        "what does geraldo unlock at each level",
        "deterministic_geraldo_per_level_reply",
    ),
    (
        "what are all the game modes in btd6",
        "deterministic_modes_reply",
    ),
    (
        "is a 0-4-1 desperado cheaper than a 2-0-4 sniper monkey",
        "deterministic_cost_comparison_reply",
    ),
    (
        "is a 0-4-1 desperado cheaper on easy or impoppable",
        "deterministic_difficulty_cost_comparison_reply",
    ),
    (
        "which earns more cash, rounds 20-40 or rounds 40-60?",
        "deterministic_round_range_comparison_reply",
    ),
    (
        "is the glaive dominus or ascended shadow paragon cheaper",
        "deterministic_paragon_cost_comparison_reply",
    ),
    (
        "is quincy or benjamin cheaper to place",
        "deterministic_hero_cost_comparison_reply",
    ),
    (
        "which power is cheaper, cash drop or monkey boost",
        "deterministic_power_cost_comparison_reply",
    ),
    (
        "which towers can pop lead without upgrades",
        "deterministic_capability_roster_reply",
    ),
    (
        "what are all the moab class bloons",
        "deterministic_bloon_roster_reply",
    ),
    (
        "what does the camo property do",
        "deterministic_bloon_modifier_reply",
    ),
    (
        "how much health does a bad have on round 100",
        "deterministic_bloon_health_reply",
    ),
    (
        "what economy relics are there",
        "deterministic_relic_roster_reply",
    ),
    (
        "what abilities does quincy have",
        "deterministic_hero_ability_roster_reply",
    ),
    (
        "what abilities does the ascended shadow paragon have",
        "deterministic_paragon_ability_roster_reply",
    ),
    (
        "what's the elite boss damage multiplier for paragons",
        "deterministic_paragon_elite_reply",
    ),
    (
        "which bosses are immune to fire",
        "deterministic_boss_immunity_reply",
    ),
    (
        "which boss has the most health at tier 5",
        "deterministic_boss_hp_comparison_reply",
    ),
    (
        "how much xp does round 63 give",
        "deterministic_round_xp_reply",
    ),
    (
        "what's the economy of round 95",
        "deterministic_round_economy_reply",
    ),
    (
        "list all the bloons from r29 till r63",
        "deterministic_round_range_bloons_reply",
    ),
    # An economy cue over a range stays with the economy builder — the range-bloon
    # roster defers whenever _ROUND_ECONOMY_CUE_RE matches (locks that boundary).
    (
        "what's the total rbe from rounds 29 to 63",
        "deterministic_round_economy_reply",
    ),
)

# Ordinary BTD6 questions / strategy / single-entity lookups — zero builders fire.
_SHOULD_DEFER: tuple[str, ...] = (
    "how much does a 0-4-1 desperado cost on impoppable",
    "what is the hp of elite lych per tier",
    "what does the genie bottle do",
    "which tower is best against ddts",
    "how much cash do i earn from rounds 20-40",
    "should i play a dart monkey on easy or hard",
    "what is the navarch of the seas paragon",
    "does the dartling gunner detect camo",
    "which tower is best at popping lead",
    "what is a moab",
    "is the lead bloon immune to sharp",
    # XP to *unlock an upgrade* names no round → the round-XP floor must defer.
    "how much xp to unlock the 2-0-4 super monkey",
)


@pytest.fixture(autouse=True)
def _reset_dataset_cache():
    btd6_data_service.reset_cache()
    yield
    btd6_data_service.reset_cache()


def _firing_builders(phrase: str) -> list[str]:
    """The __name__s of every floor builder that returns a reply for ``phrase``."""
    return [
        builder.__name__
        for builder in btd6_context_service._BTD6_LIST_BUILDERS
        if builder(phrase) is not None
    ]


@pytest.mark.parametrize(("phrase", "expected"), _SHOULD_FIRE)
def test_exactly_one_builder_owns_each_should_fire_phrase(phrase: str, expected: str):
    firing = _firing_builders(phrase)
    assert firing == [
        expected
    ], f"{phrase!r}: expected only {expected} to fire, got {firing}"
    # The dispatcher serves that same builder's answer (order never masks it).
    assert btd6_context_service.deterministic_btd6_list_reply(phrase) is not None


@pytest.mark.parametrize("phrase", _SHOULD_DEFER)
def test_no_builder_fires_on_a_should_defer_phrase(phrase: str):
    firing = _firing_builders(phrase)
    assert firing == [], f"{phrase!r}: expected no builder to fire, got {firing}"
    assert btd6_context_service.deterministic_btd6_list_reply(phrase) is None


def test_every_dispatcher_builder_has_a_corpus_entry():
    """A builder added to the dispatcher without a should-fire phrase fails here.

    Keeps the exclusivity contract executable as the floor grows — the whole point
    of importing the live tuple instead of hardcoding the builder list.
    """
    covered = {expected for _phrase, expected in _SHOULD_FIRE}
    live = {builder.__name__ for builder in btd6_context_service._BTD6_LIST_BUILDERS}
    missing = live - covered
    assert not missing, (
        f"floor builders with no exclusivity-corpus phrase: {sorted(missing)} — "
        "add a representative should-fire phrase to _SHOULD_FIRE"
    )
