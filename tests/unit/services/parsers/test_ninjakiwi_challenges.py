"""M3B — Ninja Kiwi /btd6/challenges parsers."""

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
from services.parsers.ninjakiwi_challenges import (  # noqa: E402
    parse_challenge_filters,
    parse_challenge_list,
    parse_challenge_metadata,
)

_FIXTURES = Path(__file__).parents[4] / "tests" / "fixtures" / "ninjakiwi"
_CHALLENGE_ID = "rot284420260525"


def _load(name: str) -> dict:
    return json.loads((_FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _import_parsers():
    import services.parsers  # noqa: F401


# ---------------------------------------------------------------------------
# parse_challenge_filters
# ---------------------------------------------------------------------------


def test_parse_challenge_filters_emits_three_facts():
    facts = parse_challenge_filters(_load("btd6_challenges.json"))
    keys = sorted(fact["entity_key"] for fact in facts)
    assert keys == ["daily", "newest", "trending"]
    for fact in facts:
        assert fact["fact_type"] == "btd6.challenge_filter_index"
        assert fact["entity_kind"] == "btd6_challenge_filter"
        body = fact["body_json"]
        assert body["filter_type"] == fact["entity_key"]
        assert body["challenges_url"].startswith(
            "https://data.ninjakiwi.com/btd6/challenges/filter/",
        )


# ---------------------------------------------------------------------------
# parse_challenge_list
# ---------------------------------------------------------------------------


def test_parse_challenge_list_emits_one_fact_per_entry():
    facts = parse_challenge_list(_load("btd6_challenges_filter_daily.json"))
    # Fixture has 18 daily challenges (Standard/Advanced/coop mix).
    assert len(facts) == 18
    for fact in facts:
        assert fact["fact_type"] == "btd6.challenge_list"
        assert fact["entity_kind"] == "btd6_challenge"
        body = fact["body_json"]
        # All daily fixtures have creator=null — preserved verbatim.
        assert body["creator_url"] is None
        assert isinstance(body["created_at_ms"], int)


def test_parse_challenge_list_groups_by_category_prefix():
    facts = parse_challenge_list(_load("btd6_challenges_filter_daily.json"))
    ids = {fact["entity_key"] for fact in facts}
    assert any(challenge_id.startswith("rot") for challenge_id in ids)  # Standard
    assert any(challenge_id.startswith("adv") for challenge_id in ids)  # Advanced
    assert any(challenge_id.startswith("coop") for challenge_id in ids)  # coop


# ---------------------------------------------------------------------------
# parse_challenge_metadata
# ---------------------------------------------------------------------------


def test_parse_challenge_metadata_uses_body_id_when_present():
    facts = parse_challenge_metadata(
        _load("btd6_challenges_challenge_rot284420260525.json"),
    )
    assert len(facts) == 1
    fact = facts[0]
    assert fact["fact_type"] == "btd6.challenge_metadata"
    assert fact["entity_kind"] == "btd6_challenge"
    assert fact["entity_key"] == _CHALLENGE_ID
    body = fact["body_json"]
    assert body["challenge_id"] == _CHALLENGE_ID
    assert body["id"] == _CHALLENGE_ID  # not "n/a" for daily challenges
    assert body["creator"] is None
    assert body["map"] == "TreeStump"
    assert body["mode"] == "Standard"
    assert body["difficulty"] == "Medium"


def test_parse_challenge_metadata_preserves_tower_restriction_edge_cases():
    facts = parse_challenge_metadata(
        _load("btd6_challenges_challenge_rot284420260525.json"),
    )
    towers = facts[0]["body_json"]["_towers"]
    obyn = next(row for row in towers if row["tower"] == "ObynGreenfoot")
    assert obyn["max"] == 1  # chosen primary hero
    # DartlingGunner has -1 blocked tiers in this fixture (no restriction).
    dartling = next(row for row in towers if row["tower"] == "DartlingGunner")
    assert dartling["max"] == -1
    assert dartling["path1NumBlockedTiers"] == -1


def test_parse_challenge_metadata_falls_back_to_path_params_when_body_id_is_na():
    payload = {
        "success": True,
        "error": None,
        "body": {
            "id": "n/a",
            "name": "synthetic",
            "map": "Logs",
        },
        "model": None,
        "next": None,
        "prev": None,
    }
    facts = parse_challenge_metadata(
        payload,
        path_params={"challengeID": "fallback123"},
    )
    assert len(facts) == 1
    assert facts[0]["entity_key"] == "fallback123"


# ---------------------------------------------------------------------------
# registry + envelope
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "source_key",
    [
        "nk_btd6_challenges",
        "nk_btd6_challenges_filter",
        "nk_btd6_challenges_one",
    ],
)
def test_challenges_parsers_are_registered(source_key):
    parser = btd6_source_parser.get(source_key)
    assert parser is not None
    assert parser.source_key == source_key


def test_envelope_failure_propagates_through_challenges_parsers():
    bad = {"success": False, "error": "boom", "body": None}
    with pytest.raises(EnvelopeError):
        parse_challenge_filters(bad)
    with pytest.raises(EnvelopeError):
        parse_challenge_list(bad)
    with pytest.raises(EnvelopeError):
        parse_challenge_metadata(bad)
