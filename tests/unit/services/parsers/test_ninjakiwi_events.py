"""M3B — Ninja Kiwi /btd6/events parser."""

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
from services.parsers.ninjakiwi_events import parse_events_index  # noqa: E402

_FIXTURES = Path(__file__).parents[4] / "tests" / "fixtures" / "ninjakiwi"


def _load(name: str) -> dict:
    return json.loads((_FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _import_parsers():
    import services.parsers  # noqa: F401


def test_parse_events_index_emits_one_fact_per_event():
    facts = parse_events_index(_load("btd6_events.json"))
    assert len(facts) == 16  # fixture captures 16 events
    for fact in facts:
        assert fact["fact_type"] == "btd6.events_index"
        assert fact["entity_kind"] == "btd6_event"
        body = fact["body_json"]
        assert body["id"] == fact["entity_key"]
        assert isinstance(body["start_ms"], int)
        assert isinstance(body["end_ms"], int)


def test_parse_events_index_preserves_null_urls():
    facts = parse_events_index(_load("btd6_events.json"))
    # bossRush / ct / collectableEvent / socialseason events have url=null
    null_url_types = {"bossRush", "ct", "collectableEvent", "socialseason"}
    null_url_facts = [
        fact for fact in facts if fact["body_json"]["url"] is None
    ]
    assert null_url_facts, "fixture should contain events with url=null"
    for fact in null_url_facts:
        assert fact["body_json"]["type"] in null_url_types


def test_parse_events_index_preserves_typed_urls_unfollowed():
    facts = parse_events_index(_load("btd6_events.json"))
    typed = [fact for fact in facts if fact["body_json"]["url"]]
    assert typed, "fixture should contain events with url set"
    for fact in typed:
        url = fact["body_json"]["url"]
        # bosses / races / odyssey links are kept as plain strings.
        assert url.startswith("https://data.ninjakiwi.com/btd6/")


def test_parse_events_index_raises_envelope_error_on_failure():
    with pytest.raises(EnvelopeError):
        parse_events_index({"success": False, "error": "boom", "body": None})


def test_events_parser_is_registered():
    parser = btd6_source_parser.get("nk_btd6_events")
    assert parser is not None
    assert parser.source_key == "nk_btd6_events"
    facts = parser.parse(_load("btd6_events.json"), game_version=None)
    assert len(facts) == 16
