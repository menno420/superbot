"""M3B — Ninja Kiwi /btd6/ct parsers (CT index + tiles)."""

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
from services.parsers.ninjakiwi_ct import (  # noqa: E402
    _split_tile_type,
    parse_ct_index,
    parse_ct_tiles,
)

_FIXTURES = Path(__file__).parents[4] / "tests" / "fixtures" / "ninjakiwi"
_CT_ID = "mpejg5d0"


def _load(name: str) -> dict:
    return json.loads((_FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _import_parsers():
    import services.parsers  # noqa: F401


# ---------------------------------------------------------------------------
# parse_ct_index
# ---------------------------------------------------------------------------


def test_parse_ct_index_emits_one_fact_per_event():
    facts = parse_ct_index(_load("btd6_ct.json"))
    assert len(facts) == 8
    for fact in facts:
        assert fact["fact_type"] == "btd6.ct_index"
        assert fact["entity_kind"] == "btd6_ct"
        body = fact["body_json"]
        assert body["tiles_url"].startswith("https://data.ninjakiwi.com/btd6/ct/")
        assert body["leaderboard_player_url"].endswith("/leaderboard/player")
        assert body["leaderboard_team_url"].endswith("/leaderboard/team")


def test_parse_ct_index_preserves_zero_total_scores():
    facts = parse_ct_index(_load("btd6_ct.json"))
    keys = {fact["entity_key"]: fact for fact in facts}
    current = keys[_CT_ID]
    # Current CT in capture has 0 / 0 scores (just started).
    assert current["body_json"]["total_scores_player"] == 0
    assert current["body_json"]["total_scores_team"] == 0
    # Older CT (mousgbkh) had real submissions.
    older = keys["mousgbkh"]
    assert older["body_json"]["total_scores_player"] == 14325
    assert older["body_json"]["total_scores_team"] == 5341


# ---------------------------------------------------------------------------
# _split_tile_type (private helper)
# ---------------------------------------------------------------------------


def test_split_tile_type_splits_relic_strings():
    assert _split_tile_type("Relic - Abilitized") == ("Relic", "Abilitized")
    assert _split_tile_type("Relic - HardBaked") == ("Relic", "HardBaked")


def test_split_tile_type_passes_through_non_relic_types():
    assert _split_tile_type("Regular") == ("Regular", None)
    assert _split_tile_type("Banner") == ("Banner", None)
    assert _split_tile_type("TeamStart") == ("TeamStart", None)


def test_split_tile_type_returns_none_for_non_strings():
    assert _split_tile_type(None) == (None, None)
    assert _split_tile_type(42) == (None, None)


# ---------------------------------------------------------------------------
# parse_ct_tiles
# ---------------------------------------------------------------------------


def test_parse_ct_tiles_emits_one_fact_per_tile_using_body_id():
    facts = parse_ct_tiles(_load("btd6_ct_mpejg5d0_tiles.json"))
    # Fixture has many tiles; verify count + composite entity_key format.
    assert len(facts) > 100
    for fact in facts:
        assert fact["fact_type"] == "btd6.ct_tiles"
        assert fact["entity_kind"] == "btd6_ct_tile"
        assert fact["entity_key"].startswith(f"{_CT_ID}_tile_")
        body = fact["body_json"]
        assert body["ct_id"] == _CT_ID


def test_parse_ct_tiles_splits_relic_strings_into_type_and_relic_name():
    facts = parse_ct_tiles(_load("btd6_ct_mpejg5d0_tiles.json"))
    by_tile = {fact["body_json"]["tile_id"]: fact["body_json"] for fact in facts}
    # MRX = "Relic - Abilitized" in fixture.
    assert by_tile["MRX"]["type"] == "Relic"
    assert by_tile["MRX"]["relic_name"] == "Abilitized"
    # DAD = "Relic - BrokenHeart"
    assert by_tile["DAD"]["relic_name"] == "BrokenHeart"


def test_parse_ct_tiles_preserves_non_relic_types_unchanged():
    facts = parse_ct_tiles(_load("btd6_ct_mpejg5d0_tiles.json"))
    by_tile = {fact["body_json"]["tile_id"]: fact["body_json"] for fact in facts}
    # AAA = "TeamStart"
    assert by_tile["AAA"]["type"] == "TeamStart"
    assert by_tile["AAA"]["relic_name"] is None
    assert by_tile["AAA"]["game_type"] == "TeamStart"
    # DAG = "Banner" / Race
    assert by_tile["DAG"]["type"] == "Banner"
    assert by_tile["DAG"]["game_type"] == "Race"


def test_parse_ct_tiles_falls_back_to_path_params_ct_id_if_body_missing():
    payload = {
        "success": True,
        "error": None,
        "body": {
            # body.id intentionally absent
            "tiles": [{"id": "AAA", "type": "Regular", "gameType": "Race"}],
        },
        "model": None,
        "next": None,
        "prev": None,
    }
    facts = parse_ct_tiles(payload, path_params={"ctID": "synthetic_ct"})
    assert len(facts) == 1
    assert facts[0]["entity_key"] == "synthetic_ct_tile_AAA"


# ---------------------------------------------------------------------------
# registry + envelope
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("source_key", ["nk_btd6_ct", "nk_btd6_ct_tiles"])
def test_ct_parsers_are_registered(source_key):
    parser = btd6_source_parser.get(source_key)
    assert parser is not None
    assert parser.source_key == source_key


def test_envelope_failure_propagates_through_ct_parsers():
    bad = {"success": False, "error": "boom", "body": None}
    with pytest.raises(EnvelopeError):
        parse_ct_index(bad)
    with pytest.raises(EnvelopeError):
        parse_ct_tiles(bad)
