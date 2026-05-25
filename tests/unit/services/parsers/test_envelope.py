"""M3B — shared NK envelope helper validates success / error / shape."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[4] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services.parsers._envelope import (  # noqa: E402
    Envelope,
    EnvelopeError,
    ParserAdapter,
    unwrap,
)

_FIXTURES = Path(__file__).parents[4] / "tests" / "fixtures" / "ninjakiwi"


def _load(name: str) -> dict:
    return json.loads((_FIXTURES / name).read_text(encoding="utf-8"))


def test_unwrap_returns_envelope_for_success_payload():
    payload = _load("btd6_maps.json")
    env = unwrap(payload, "nk_btd6_maps")
    assert isinstance(env, Envelope)
    assert env.success is True
    assert env.error is None
    assert env.next is None
    assert env.prev is None


def test_unwrap_keeps_body_as_list_when_upstream_returns_list():
    payload = _load("btd6_events.json")
    env = unwrap(payload, "nk_btd6_events")
    assert isinstance(env.body, list)
    assert all(isinstance(row, dict) for row in env.body)


def test_unwrap_keeps_body_as_dict_when_upstream_returns_dict():
    payload = _load("btd6_maps_map_ZFUERYR.json")
    env = unwrap(payload, "nk_btd6_maps_one")
    assert isinstance(env.body, dict)
    assert env.body["id"] == "ZFUERYR"


def test_unwrap_captures_pagination_metadata():
    payload = _load("btd6_races_Reversed_Loop_mpbd7tcu_leaderboard.json")
    env = unwrap(payload, "nk_btd6_races_leaderboard")
    assert env.next == (
        "https://data.ninjakiwi.com/btd6/races/"
        "Reversed_Loop_mpbd7tcu/leaderboard?page=2"
    )
    assert env.prev is None
    assert env.max_pages == 20


def test_unwrap_rejects_non_dict_payload():
    with pytest.raises(EnvelopeError) as info:
        unwrap([1, 2, 3], "nk_btd6_maps")
    assert info.value.reason == "payload_not_a_dict"
    assert info.value.source_key == "nk_btd6_maps"


def test_unwrap_rejects_success_false():
    with pytest.raises(EnvelopeError) as info:
        unwrap({"success": False, "error": "boom", "body": None}, "nk_btd6_maps")
    assert info.value.reason == "success_not_true"


def test_unwrap_rejects_success_missing():
    with pytest.raises(EnvelopeError) as info:
        unwrap({"error": None, "body": []}, "nk_btd6_maps")
    assert info.value.reason == "success_not_true"


def test_unwrap_rejects_error_field_set_even_when_success_true():
    with pytest.raises(EnvelopeError) as info:
        unwrap(
            {"success": True, "error": "throttled", "body": None},
            "nk_btd6_maps",
        )
    assert info.value.reason == "error_present"


def test_parser_adapter_satisfies_protocol_and_delegates():
    captured: dict = {}

    def _fake_parse(payload, *, game_version=None, path_params=None):
        captured["payload"] = payload
        captured["game_version"] = game_version
        captured["path_params"] = path_params
        return [{"fact_type": "btd6.test", "entity_kind": "x",
                 "entity_key": "y", "body_json": {}}]

    adapter = ParserAdapter("nk_btd6_maps", _fake_parse)
    result = adapter.parse(
        {"success": True, "body": []},
        game_version="54.3",
        path_params={"raceID": "abc"},
    )
    assert adapter.source_key == "nk_btd6_maps"
    assert captured["game_version"] == "54.3"
    assert captured["path_params"] == {"raceID": "abc"}
    assert result[0]["fact_type"] == "btd6.test"
