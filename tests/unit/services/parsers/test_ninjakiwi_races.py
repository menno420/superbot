"""M3B — Ninja Kiwi /btd6/races parsers."""

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
from services.parsers.ninjakiwi_races import (  # noqa: E402
    parse_race_leaderboard,
    parse_race_metadata,
    parse_races_index,
)

_FIXTURES = Path(__file__).parents[4] / "tests" / "fixtures" / "ninjakiwi"
_RACE_ID = "Reversed_Loop_mpbd7tcu"


def _load(name: str) -> dict:
    return json.loads((_FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _import_parsers():
    import services.parsers  # noqa: F401


# ---------------------------------------------------------------------------
# parse_races_index
# ---------------------------------------------------------------------------


def test_parse_races_index_emits_one_fact_per_race():
    facts = parse_races_index(_load("btd6_races.json"))
    assert len(facts) == 11
    for fact in facts:
        assert fact["fact_type"] == "btd6.races_index"
        assert fact["entity_kind"] == "btd6_race"
        body = fact["body_json"]
        assert isinstance(body["start_ms"], int)
        assert body["leaderboard_url"].startswith(
            "https://data.ninjakiwi.com/btd6/races/"
        )


def test_parse_races_index_includes_total_scores_field():
    facts = parse_races_index(_load("btd6_races.json"))
    keys = {fact["entity_key"]: fact for fact in facts}
    reversed_loop = keys[_RACE_ID]
    assert reversed_loop["body_json"]["total_scores"] == 12017
    upstream = keys["Upstream_mm0qqydh"]
    # Older races can have totalScores=0 — preserved verbatim.
    assert upstream["body_json"]["total_scores"] == 0


# ---------------------------------------------------------------------------
# parse_race_metadata
# ---------------------------------------------------------------------------


def test_parse_race_metadata_requires_path_params_race_id():
    facts = parse_race_metadata(
        _load("btd6_races_Reversed_Loop_mpbd7tcu_metadata.json"),
    )
    # Without path_params the parser cannot compose a stable entity_key.
    assert facts == []


def test_parse_race_metadata_emits_single_fact_when_race_id_known():
    facts = parse_race_metadata(
        _load("btd6_races_Reversed_Loop_mpbd7tcu_metadata.json"),
        path_params={"raceID": _RACE_ID},
    )
    assert len(facts) == 1
    fact = facts[0]
    assert fact["fact_type"] == "btd6.race_metadata"
    assert fact["entity_kind"] == "btd6_race"
    assert fact["entity_key"] == _RACE_ID
    body = fact["body_json"]
    # The "race_id" override is appended so downstream queries don't need
    # to lookup the n/a body id; the body's own "id" field is preserved.
    assert body["race_id"] == _RACE_ID
    assert body["id"] == "n/a"
    assert body["name"] == "Reversed Loop"
    assert body["mode"] == "Reverse"
    # _bloonModifiers carries non-default multipliers in this fixture.
    assert body["_bloonModifiers"]["speedMultiplier"] == 1.5
    assert body["_bloonModifiers"]["moabSpeedMultiplier"] == 1.5


def test_parse_race_metadata_preserves_tower_restriction_structure():
    facts = parse_race_metadata(
        _load("btd6_races_Reversed_Loop_mpbd7tcu_metadata.json"),
        path_params={"raceID": _RACE_ID},
    )
    towers = facts[0]["body_json"]["_towers"]
    assert isinstance(towers, list)
    # Some towers are blocked (max=0), some uncapped (max=-1), some capped.
    alchemist = next(row for row in towers if row["tower"] == "Alchemist")
    assert alchemist["max"] == 1
    engineer = next(row for row in towers if row["tower"] == "EngineerMonkey")
    assert engineer["max"] == -1  # uncapped
    assert engineer["path1NumBlockedTiers"] == 3


# ---------------------------------------------------------------------------
# parse_race_leaderboard
# ---------------------------------------------------------------------------


def test_parse_race_leaderboard_requires_path_params_race_id():
    facts = parse_race_leaderboard(
        _load("btd6_races_Reversed_Loop_mpbd7tcu_leaderboard.json"),
    )
    assert facts == []


def test_parse_race_leaderboard_emits_fact_per_row_with_rank():
    facts = parse_race_leaderboard(
        _load("btd6_races_Reversed_Loop_mpbd7tcu_leaderboard.json"),
        path_params={"raceID": _RACE_ID},
    )
    # Fixture captures 50 leaderboard rows (page 1).
    assert len(facts) == 50
    first = facts[0]
    assert first["fact_type"] == "btd6.race_leaderboard"
    assert first["entity_kind"] == "btd6_race_leaderboard_row"
    assert first["entity_key"] == f"{_RACE_ID}_rank_1"
    body = first["body_json"]
    assert body["race_id"] == _RACE_ID
    assert body["rank"] == 1
    assert body["display_name"] == "TheDoctor"
    assert body["score"] == 121833
    # scoreParts preserved as the API returned it.
    assert isinstance(body["score_parts"], list)
    assert body["submission_time_ms"] == -1
    assert body["profile_url"].startswith("https://data.ninjakiwi.com/btd6/users/")


def test_parse_race_leaderboard_ranks_are_unique_and_ordered():
    facts = parse_race_leaderboard(
        _load("btd6_races_Reversed_Loop_mpbd7tcu_leaderboard.json"),
        path_params={"raceID": _RACE_ID},
    )
    ranks = [fact["body_json"]["rank"] for fact in facts]
    assert ranks == list(range(1, 51))


# ---------------------------------------------------------------------------
# registry wiring + envelope rejection
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "source_key",
    ["nk_btd6_races", "nk_btd6_races_metadata", "nk_btd6_races_leaderboard"],
)
def test_races_parsers_are_registered(source_key):
    parser = btd6_source_parser.get(source_key)
    assert parser is not None
    assert parser.source_key == source_key


def test_envelope_failure_propagates_through_race_parsers():
    bad = {"success": False, "error": "boom", "body": None}
    with pytest.raises(EnvelopeError):
        parse_races_index(bad)
    with pytest.raises(EnvelopeError):
        parse_race_metadata(bad, path_params={"raceID": _RACE_ID})
    with pytest.raises(EnvelopeError):
        parse_race_leaderboard(bad, path_params={"raceID": _RACE_ID})
