"""M3B — Ninja Kiwi /btd6/maps parsers."""

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
from services.parsers.ninjakiwi_maps import (  # noqa: E402
    parse_map_filters,
    parse_map_list,
    parse_map_metadata,
)

_FIXTURES = Path(__file__).parents[4] / "tests" / "fixtures" / "ninjakiwi"


def _load(name: str) -> dict:
    return json.loads((_FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _import_parsers():
    import services.parsers  # noqa: F401 — triggers registration side effect


# ---------------------------------------------------------------------------
# parse_map_filters — /btd6/maps
# ---------------------------------------------------------------------------


def test_parse_map_filters_emits_one_fact_per_filter_entry():
    facts = parse_map_filters(_load("btd6_maps.json"))
    keys = sorted(fact["entity_key"] for fact in facts)
    assert keys == ["mostLiked", "newest", "trending"]
    for fact in facts:
        assert fact["fact_type"] == "btd6.map_filter_index"
        assert fact["entity_kind"] == "btd6_map_filter"
        body = fact["body_json"]
        assert body["filter_type"] == fact["entity_key"]
        assert body["maps_url"].startswith("https://data.ninjakiwi.com/btd6/maps/filter/")


def test_parse_map_filters_carries_game_version_parameter():
    facts = parse_map_filters(_load("btd6_maps.json"), game_version="54.3")
    assert all(fact["game_version"] == "54.3" for fact in facts)


def test_parse_map_filters_raises_envelope_error_on_success_false():
    with pytest.raises(EnvelopeError):
        parse_map_filters({"success": False, "error": "boom", "body": None})


# ---------------------------------------------------------------------------
# parse_map_list — /btd6/maps/filter/<filter>
# ---------------------------------------------------------------------------


def test_parse_map_list_emits_one_fact_per_map():
    facts = parse_map_list(_load("btd6_maps_filter_newest.json"))
    assert len(facts) == 25  # fixture captures 25 maps on page 1
    for fact in facts:
        assert fact["fact_type"] == "btd6.map_list"
        assert fact["entity_kind"] == "btd6_map"
        assert fact["entity_key"].startswith("ZFUE")  # newest sample IDs
        body = fact["body_json"]
        assert isinstance(body["created_at_ms"], int)
        assert body["metadata_url"].startswith("https://data.ninjakiwi.com/btd6/maps/map/")


def test_parse_map_list_preserves_creator_url_unexpanded():
    facts = parse_map_list(_load("btd6_maps_filter_newest.json"))
    first = facts[0]
    body = first["body_json"]
    assert body["creator_url"].startswith("https://data.ninjakiwi.com/btd6/users/")
    # The parser does not follow the URL or expand creator fields.
    assert "displayName" not in body


def test_parse_map_list_skips_entries_missing_id():
    payload = {
        "success": True,
        "error": None,
        "body": [
            {"name": "ok", "id": "ABC123"},
            {"name": "no-id"},                # missing id
            {"name": "blank-id", "id": ""},   # empty id
            "not-a-dict",                     # malformed entry
        ],
    }
    facts = parse_map_list(payload)
    assert [fact["entity_key"] for fact in facts] == ["ABC123"]


# ---------------------------------------------------------------------------
# parse_map_metadata — /btd6/maps/map/<mapID>
# ---------------------------------------------------------------------------


def test_parse_map_metadata_emits_single_fact_with_full_body():
    facts = parse_map_metadata(_load("btd6_maps_map_ZFUERYR.json"))
    assert len(facts) == 1
    fact = facts[0]
    assert fact["fact_type"] == "btd6.map_metadata"
    assert fact["entity_kind"] == "btd6_map"
    assert fact["entity_key"] == "ZFUERYR"
    body = fact["body_json"]
    assert body["name"] == "dartling monkey"
    assert body["created_at_ms"] == 1779681502129
    assert body["game_version"] == "54.3"
    assert body["map"] == "CustomMap"
    assert body["map_url"].endswith("/preview")
    stats = body["stats"]
    # Fresh map — every counter is zero.
    assert stats["plays"] == 0
    assert stats["wins"] == 0
    assert stats["losses_unique"] == 0


def test_parse_map_metadata_prefers_body_game_version_over_param():
    facts = parse_map_metadata(
        _load("btd6_maps_map_ZFUERYR.json"),
        game_version="ignored",
    )
    assert facts[0]["game_version"] == "54.3"


def test_parse_map_metadata_returns_empty_when_body_lacks_id():
    payload = {"success": True, "error": None, "body": {"name": "no-id"}}
    assert parse_map_metadata(payload) == []


# ---------------------------------------------------------------------------
# registry wiring
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "source_key",
    ["nk_btd6_maps", "nk_btd6_maps_filter", "nk_btd6_maps_one"],
)
def test_maps_parsers_are_registered(source_key):
    parser = btd6_source_parser.get(source_key)
    assert parser is not None
    assert parser.source_key == source_key


def test_registered_maps_filters_parser_returns_facts():
    parser = btd6_source_parser.get("nk_btd6_maps")
    facts = parser.parse(_load("btd6_maps.json"), game_version=None)
    assert len(facts) == 3
