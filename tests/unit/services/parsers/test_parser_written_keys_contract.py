"""Pin the parser → dependency-chain contract.

``refresh_with_dependencies`` builds child path_params from each
parent's ``written_entity_keys`` (the tuple of ``entity_key`` values
the parent's facts wrote). If a parser changes which field it stores
as ``entity_key``, the chain silently produces wrong children — every
downstream lookup misses.

These tests assert each chain-parent parser produces ``entity_key``
values in the shape the next-hop spec consumes.
"""

from __future__ import annotations

import json
from pathlib import Path

from services.parsers.ninjakiwi_challenges import parse_challenge_filters
from services.parsers.ninjakiwi_maps import parse_map_filters

_FIXTURES = Path(__file__).resolve().parents[3] / "fixtures" / "ninjakiwi"


def _load(name: str) -> dict:
    with (_FIXTURES / name).open() as f:
        return json.load(f)


def _entity_keys(facts: list[dict]) -> set[str]:
    return {f["entity_key"] for f in facts}


# ---------------------------------------------------------------------------
# Maps: parser produces filter names that the chain wraps as {"mapFilter": k}
# ---------------------------------------------------------------------------


def test_parse_maps_index_emits_filter_names_as_entity_keys():
    facts = parse_map_filters(_load("btd6_maps.json"))
    keys = _entity_keys(facts)
    # nk_btd6_maps_filter expects entity_key to be a filter name (newest,
    # trending, mostLiked). The chain wraps it as {"mapFilter": k}.
    assert keys <= {"newest", "trending", "mostLiked"}
    assert keys, "expected at least one filter name from the maps index"
    for fact in facts:
        assert fact["entity_kind"] == "btd6_map_filter"
        assert isinstance(fact["entity_key"], str)
        assert fact["entity_key"], "filter entity_key must be non-empty"


# ---------------------------------------------------------------------------
# Challenges: same shape as maps (parser → filter type names)
# ---------------------------------------------------------------------------


def test_parse_challenges_index_emits_filter_names_as_entity_keys():
    facts = parse_challenge_filters(_load("btd6_challenges.json"))
    keys = _entity_keys(facts)
    assert keys, "expected at least one filter name from the challenges index"
    for fact in facts:
        assert fact["entity_kind"] == "btd6_challenge_filter"
        assert isinstance(fact["entity_key"], str)
        assert fact["entity_key"], "filter entity_key must be non-empty"


# ---------------------------------------------------------------------------
# Maps_filter parser: writes map IDs that the chain wraps as {"mapID": k}
# ---------------------------------------------------------------------------


def test_parse_map_list_emits_map_ids_as_entity_keys():
    from services.parsers.ninjakiwi_maps import parse_map_list

    facts = parse_map_list(_load("btd6_maps_filter_newest.json"))
    assert facts, "fixture should produce at least one map fact"
    for fact in facts:
        assert fact["entity_kind"] == "btd6_map"
        assert isinstance(fact["entity_key"], str)
        # Map ids are non-empty and don't contain whitespace — they're
        # safe to interpolate into a URL path.
        assert fact["entity_key"], "map entity_key must be non-empty"
        assert " " not in fact["entity_key"]


# ---------------------------------------------------------------------------
# Races / bosses / odyssey: index parsers emit ID-shaped entity_keys
# ---------------------------------------------------------------------------


def test_parse_races_index_emits_string_ids():
    from services.parsers.ninjakiwi_races import parse_races_index

    facts = parse_races_index(_load("btd6_races.json"))
    assert facts, "races index fixture should produce at least one fact"
    for fact in facts:
        assert fact["entity_kind"] == "btd6_race"
        assert isinstance(fact["entity_key"], str) and fact["entity_key"]


def test_parse_bosses_index_emits_string_ids():
    from services.parsers.ninjakiwi_bosses import parse_bosses_index

    facts = parse_bosses_index(_load("btd6_bosses.json"))
    assert facts, "bosses index fixture should produce at least one fact"
    for fact in facts:
        assert fact["entity_kind"] == "btd6_boss"
        assert isinstance(fact["entity_key"], str) and fact["entity_key"]


def test_parse_odyssey_index_emits_string_ids():
    from services.parsers.ninjakiwi_odyssey import parse_odyssey_index

    facts = parse_odyssey_index(_load("btd6_odyssey.json"))
    assert facts, "odyssey index fixture should produce at least one fact"
    for fact in facts:
        assert fact["entity_kind"] == "btd6_odyssey"
        assert isinstance(fact["entity_key"], str) and fact["entity_key"]


def test_parse_ct_index_emits_string_ids():
    from services.parsers.ninjakiwi_ct import parse_ct_index

    facts = parse_ct_index(_load("btd6_ct.json"))
    assert facts, "ct index fixture should produce at least one fact"
    for fact in facts:
        assert fact["entity_kind"] == "btd6_ct"
        assert isinstance(fact["entity_key"], str) and fact["entity_key"]
