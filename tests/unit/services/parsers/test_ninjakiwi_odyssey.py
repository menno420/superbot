"""M3B — Ninja Kiwi /btd6/odyssey parsers."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[4] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import btd6_source_parser  # noqa: E402
from services.parsers._envelope import EnvelopeError  # noqa: E402
from services.parsers.ninjakiwi_odyssey import (  # noqa: E402
    parse_odyssey_index,
    parse_odyssey_maps,
    parse_odyssey_metadata,
)

_FIXTURES = Path(__file__).parents[4] / "tests" / "fixtures" / "ninjakiwi"
_ODYSSEY_ID = "mpbd858c"


def _load(name: str) -> dict:
    return json.loads((_FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _import_parsers():
    import services.parsers  # noqa: F401


# ---------------------------------------------------------------------------
# parse_odyssey_index
# ---------------------------------------------------------------------------


def test_parse_odyssey_index_emits_one_fact_per_odyssey():
    facts = parse_odyssey_index(_load("btd6_odyssey.json"))
    assert len(facts) == 11
    for fact in facts:
        assert fact["fact_type"] == "btd6.odyssey_index"
        assert fact["entity_kind"] == "btd6_odyssey"
        body = fact["body_json"]
        for url_field in (
            "metadata_easy_url",
            "metadata_medium_url",
            "metadata_hard_url",
        ):
            assert body[url_field].startswith("https://data.ninjakiwi.com/btd6/odyssey/")


def test_parse_odyssey_index_preserves_description_field():
    facts = parse_odyssey_index(_load("btd6_odyssey.json"))
    keys = {fact["entity_key"]: fact for fact in facts}
    bottoms_up = keys[_ODYSSEY_ID]
    assert bottoms_up["body_json"]["name"] == "Bottoms Up!"
    assert "Bottom Paths" in bottoms_up["body_json"]["description"]


# ---------------------------------------------------------------------------
# parse_odyssey_metadata
# ---------------------------------------------------------------------------


def test_parse_odyssey_metadata_requires_difficulty_path_param():
    facts = parse_odyssey_metadata(
        _load("btd6_odyssey_mpbd858c_easy.json"),
        path_params={"odysseyID": _ODYSSEY_ID},  # missing difficulty
    )
    assert facts == []


def test_parse_odyssey_metadata_composes_entity_key():
    facts = parse_odyssey_metadata(
        _load("btd6_odyssey_mpbd858c_easy.json"),
        path_params={"odysseyID": _ODYSSEY_ID, "difficulty": "easy"},
    )
    assert len(facts) == 1
    fact = facts[0]
    assert fact["fact_type"] == "btd6.odyssey_metadata"
    assert fact["entity_kind"] == "btd6_odyssey_difficulty"
    assert fact["entity_key"] == f"{_ODYSSEY_ID}_easy"
    body = fact["body_json"]
    assert body["odyssey_id"] == _ODYSSEY_ID
    assert body["difficulty"] == "easy"
    assert body["isExtreme"] is False
    assert body["startingHealth"] == 150
    assert body["maxMonkeySeats"] == 12


def test_parse_odyssey_metadata_preserves_tower_availability_structure():
    facts = parse_odyssey_metadata(
        _load("btd6_odyssey_mpbd858c_easy.json"),
        path_params={"odysseyID": _ODYSSEY_ID, "difficulty": "easy"},
    )
    towers = facts[0]["body_json"]["_availableTowers"]
    heroes = [row for row in towers if row.get("isHero")]
    non_heroes = [row for row in towers if not row.get("isHero")]
    assert heroes, "fixture has hero entries"
    assert non_heroes, "fixture has non-hero entries"
    dart_monkey = next(row for row in non_heroes if row["tower"] == "DartMonkey")
    assert dart_monkey["max"] == 6
    assert dart_monkey["path1NumBlockedTiers"] == 3


def test_parse_odyssey_metadata_preserves_zero_powers():
    facts = parse_odyssey_metadata(
        _load("btd6_odyssey_mpbd858c_easy.json"),
        path_params={"odysseyID": _ODYSSEY_ID, "difficulty": "easy"},
    )
    powers = facts[0]["body_json"]["_availablePowers"]
    moab_mine = next(row for row in powers if row["power"] == "MoabMine")
    # max=0 means unavailable; do not coerce to None or drop.
    assert moab_mine["max"] == 0


# ---------------------------------------------------------------------------
# parse_odyssey_maps
# ---------------------------------------------------------------------------


def test_parse_odyssey_maps_requires_path_params():
    facts = parse_odyssey_maps(
        _load("btd6_odyssey_mpbd858c_easy_maps.json"),
    )
    assert facts == []


def test_parse_odyssey_maps_emits_one_fact_per_stage_with_index():
    facts = parse_odyssey_maps(
        _load("btd6_odyssey_mpbd858c_easy_maps.json"),
        path_params={"odysseyID": _ODYSSEY_ID, "difficulty": "easy"},
    )
    # Fixture: 3 stages (EndOfTheRoad, Skates, AlpineRun).
    assert len(facts) == 3
    keys = [fact["entity_key"] for fact in facts]
    assert keys == [
        f"{_ODYSSEY_ID}_easy_stage_1",
        f"{_ODYSSEY_ID}_easy_stage_2",
        f"{_ODYSSEY_ID}_easy_stage_3",
    ]
    for stage_index, fact in enumerate(facts, start=1):
        assert fact["fact_type"] == "btd6.odyssey_maps"
        assert fact["entity_kind"] == "btd6_odyssey_stage"
        body = fact["body_json"]
        assert body["odyssey_id"] == _ODYSSEY_ID
        assert body["difficulty"] == "easy"
        assert body["stage_index"] == stage_index
        # Body edge cases per the plan.
        assert body["id"] == "n/a"
        assert body["creator"] is None
        assert body["createdAt"] == 0
        assert body["_towers"] is None
        assert body["_powers"] == []


def test_parse_odyssey_maps_preserves_per_stage_round_ranges():
    facts = parse_odyssey_maps(
        _load("btd6_odyssey_mpbd858c_easy_maps.json"),
        path_params={"odysseyID": _ODYSSEY_ID, "difficulty": "easy"},
    )
    bodies = [fact["body_json"] for fact in facts]
    assert bodies[0]["map"] == "EndOfTheRoad"
    assert bodies[0]["startRound"] == 4 and bodies[0]["endRound"] == 40
    assert bodies[2]["map"] == "AlpineRun"
    assert bodies[2]["endRound"] == 50


# ---------------------------------------------------------------------------
# registry + envelope
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "source_key",
    [
        "nk_btd6_odyssey",
        "nk_btd6_odyssey_diff",
        "nk_btd6_odyssey_diff_maps",
    ],
)
def test_odyssey_parsers_are_registered(source_key):
    parser = btd6_source_parser.get(source_key)
    assert parser is not None
    assert parser.source_key == source_key


def test_envelope_failure_propagates_through_odyssey_parsers():
    bad = {"success": False, "error": "boom", "body": None}
    with pytest.raises(EnvelopeError):
        parse_odyssey_index(bad)
    with pytest.raises(EnvelopeError):
        parse_odyssey_metadata(
            bad,
            path_params={"odysseyID": _ODYSSEY_ID, "difficulty": "easy"},
        )
    with pytest.raises(EnvelopeError):
        parse_odyssey_maps(
            bad,
            path_params={"odysseyID": _ODYSSEY_ID, "difficulty": "easy"},
        )
