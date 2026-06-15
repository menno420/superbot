"""M3B — Ninja Kiwi /btd6/bosses parsers."""

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
from services.parsers.ninjakiwi_bosses import (  # noqa: E402
    parse_boss_leaderboard,
    parse_boss_metadata,
    parse_bosses_index,
)

_FIXTURES = Path(__file__).parents[4] / "tests" / "fixtures" / "ninjakiwi"
_BOSS_ID = "Diamondback5_mpfz8mi4"


def _load(name: str) -> dict:
    return json.loads((_FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _import_parsers():
    import services.parsers  # noqa: F401


# ---------------------------------------------------------------------------
# parse_bosses_index
# ---------------------------------------------------------------------------


def test_parse_bosses_index_emits_one_fact_per_boss():
    facts = parse_bosses_index(_load("btd6_bosses.json"))
    assert len(facts) == 12
    for fact in facts:
        assert fact["fact_type"] == "btd6.bosses_index"
        assert fact["entity_kind"] == "btd6_boss"
        body = fact["body_json"]
        assert body["metadata_standard_url"].endswith("/metadata/standard")
        assert body["metadata_elite_url"].endswith("/metadata/elite")


def test_parse_bosses_index_preserves_deprecated_and_modern_scoring_types():
    facts = parse_bosses_index(_load("btd6_bosses.json"))
    by_id = {fact["entity_key"]: fact["body_json"] for fact in facts}
    blasta = by_id["Blastapopoulos17_mp5xojd6"]
    # Capture shows normal=LeastCash, elite=GameTime — they really can differ.
    assert blasta["normal_scoring_type"] == "LeastCash"
    assert blasta["elite_scoring_type"] == "GameTime"
    # The legacy scalar is preserved as the deprecated alias.
    assert blasta["scoring_type_deprecated"] == "LeastCash"


def test_parse_bosses_index_includes_distinct_boss_types():
    facts = parse_bosses_index(_load("btd6_bosses.json"))
    boss_types = {fact["body_json"]["boss_type"] for fact in facts}
    assert boss_types >= {"diamondback", "blastapopoulos", "lych", "phayze"}


# ---------------------------------------------------------------------------
# parse_boss_metadata
# ---------------------------------------------------------------------------


def test_parse_boss_metadata_requires_both_path_params():
    fixture = _load("btd6_bosses_Diamondback5_mpfz8mi4_metadata_standard.json")
    assert parse_boss_metadata(fixture) == []
    assert parse_boss_metadata(fixture, path_params={"bossID": _BOSS_ID}) == []
    assert (
        parse_boss_metadata(
            fixture,
            path_params={"difficulty": "standard"},
        )
        == []
    )


def test_parse_boss_metadata_emits_single_fact_with_composite_key():
    facts = parse_boss_metadata(
        _load("btd6_bosses_Diamondback5_mpfz8mi4_metadata_standard.json"),
        path_params={"bossID": _BOSS_ID, "difficulty": "standard"},
    )
    assert len(facts) == 1
    fact = facts[0]
    assert fact["fact_type"] == "btd6.boss_metadata"
    assert fact["entity_kind"] == "btd6_boss_difficulty"
    assert fact["entity_key"] == f"{_BOSS_ID}_standard"
    body = fact["body_json"]
    assert body["boss_id"] == _BOSS_ID
    assert body["difficulty"] == "standard"
    # Edge cases per the plan: body.id is "n/a" and createdAt is 0.
    assert body["id"] == "n/a"
    assert body["createdAt"] == 0
    assert body["creator"] is None
    assert body["map"] == "Logs"
    assert body["roundSets"] == ["default", "diamondback"]


def test_parse_boss_metadata_preserves_corvus_as_allowed_hero():
    facts = parse_boss_metadata(
        _load("btd6_bosses_Diamondback5_mpfz8mi4_metadata_standard.json"),
        path_params={"bossID": _BOSS_ID, "difficulty": "standard"},
    )
    towers = facts[0]["body_json"]["_towers"]
    corvus = next(row for row in towers if row["tower"] == "Corvus")
    assert corvus["max"] == 99
    assert corvus["isHero"] is True


# ---------------------------------------------------------------------------
# parse_boss_leaderboard
# ---------------------------------------------------------------------------


def test_parse_boss_leaderboard_requires_path_params():
    fixture = _load(
        "btd6_bosses_Diamondback5_mpfz8mi4_leaderboard_standard_1.json",
    )
    assert parse_boss_leaderboard(fixture) == []
    assert (
        parse_boss_leaderboard(
            fixture,
            path_params={"bossID": _BOSS_ID, "type": "standard"},
        )
        == []
    )  # missing teamSize


def test_parse_boss_leaderboard_emits_fact_per_row_with_composite_rank_key():
    facts = parse_boss_leaderboard(
        _load("btd6_bosses_Diamondback5_mpfz8mi4_leaderboard_standard_1.json"),
        path_params={"bossID": _BOSS_ID, "type": "standard", "teamSize": "1"},
    )
    # Fixture has 25 rows on page 1.
    assert len(facts) == 25
    first = facts[0]
    assert first["fact_type"] == "btd6.boss_leaderboard"
    assert first["entity_kind"] == "btd6_boss_leaderboard_row"
    assert first["entity_key"] == f"{_BOSS_ID}_standard_1_rank_1"
    body = first["body_json"]
    assert body["display_name"] == "drop dead"
    assert body["rank"] == 1
    # scoreParts preserves mixed number / time entries.
    parts = body["score_parts"]
    assert {part["type"] for part in parts} == {"number", "time"}
    assert any(
        part["type"] == "number" and part["name"] == "Boss Tier" for part in parts
    )
    assert any(part["type"] == "time" and part["name"] == "Game Time" for part in parts)


# ---------------------------------------------------------------------------
# registry + envelope
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "source_key",
    [
        "nk_btd6_bosses",
        "nk_btd6_bosses_metadata",
        "nk_btd6_bosses_leaderboard",
    ],
)
def test_bosses_parsers_are_registered(source_key):
    parser = btd6_source_parser.get(source_key)
    assert parser is not None
    assert parser.source_key == source_key


def test_envelope_failure_propagates_through_boss_parsers():
    bad = {"success": False, "error": "boom", "body": None}
    with pytest.raises(EnvelopeError):
        parse_bosses_index(bad)
    with pytest.raises(EnvelopeError):
        parse_boss_metadata(
            bad,
            path_params={"bossID": _BOSS_ID, "difficulty": "standard"},
        )
    with pytest.raises(EnvelopeError):
        parse_boss_leaderboard(
            bad,
            path_params={"bossID": _BOSS_ID, "type": "standard", "teamSize": "1"},
        )
