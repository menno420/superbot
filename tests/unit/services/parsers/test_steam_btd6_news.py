"""Steam ISteamNews → BTD6 patch-notes parser tests."""

from __future__ import annotations

import datetime as _dt
import json
import sys
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[4] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import btd6_source_parser  # noqa: E402
from services.parsers.steam_btd6_news import parse_steam_news  # noqa: E402

_FIXTURES = Path(__file__).parents[4] / "tests" / "fixtures" / "steam"


def _load(name: str) -> dict:
    return json.loads((_FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _import_parsers():
    import services.parsers  # noqa: F401


def test_extracts_one_record_per_official_update():
    records = parse_steam_news(_load("btd6_news.json"))
    versions = [r["version"] for r in records]
    # Fixture has updates 54.0, 46.0, 40.0 plus a 54.0 re-share (deduped),
    # two non-update announcements, and one external-press item (skipped).
    assert versions == ["54.0", "46.0", "40.0"]


def test_skips_non_update_announcements():
    records = parse_steam_news(_load("btd6_news.json"))
    titles = [r["title"] for r in records]
    assert "Social Seasons Is Live!" not in titles
    assert "Limited Edition Plushies!" not in titles


def test_skips_external_press_feed():
    # The PC Gamer item has a version in its title but feedname != the
    # official developer feed, so it must not become a patch note.
    records = parse_steam_news(_load("btd6_news.json"))
    assert all("pcgamer" not in (r["url"] or "") for r in records)


def test_dedupes_repeated_version_within_payload():
    records = parse_steam_news(_load("btd6_news.json"))
    assert [r["version"] for r in records].count("54.0") == 1


def test_body_is_bbcode_stripped_and_nonempty():
    records = parse_steam_news(_load("btd6_news.json"))
    for record in records:
        assert record["body"], "patch-note body must be non-empty"
        assert "[" not in record["body"], "BBCode tags must be stripped"
        assert "]" not in record["body"]


def test_body_preserves_inner_text():
    records = parse_steam_news(_load("btd6_news.json"))
    v54 = next(r for r in records if r["version"] == "54.0")
    assert "Sun Avatar damage 50 -> 45" in v54["body"]
    assert "Tower Changes" in v54["body"]


def test_published_at_is_timezone_aware():
    records = parse_steam_news(_load("btd6_news.json"))
    v54 = next(r for r in records if r["version"] == "54.0")
    published = v54["published_at"]
    assert isinstance(published, _dt.datetime)
    assert published.tzinfo is not None
    assert published == _dt.datetime.fromtimestamp(1775770208, tz=_dt.timezone.utc)


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("Bloons TD 6 - Update 54.0", "54.0"),
        ("Bloons TD 6 v46.0 - Update Notes!", "46.0"),
        ("Bloons TD 6 - Update Notes! Version 40.0", "40.0"),
        ("Bloons TD 6 - Version 44.0 Update Notes!", "44.0"),
    ],
)
def test_version_extraction_across_title_styles(title, expected):
    payload = {
        "appnews": {
            "newsitems": [
                {
                    "title": title,
                    "contents": "notes",
                    "date": 1700000000,
                    "feedname": "steam_community_announcements",
                },
            ],
        },
    }
    records = parse_steam_news(payload)
    assert [r["version"] for r in records] == [expected]


def test_missing_or_malformed_date_yields_none_published_at():
    payload = {
        "appnews": {
            "newsitems": [
                {
                    "title": "Bloons TD 6 - Update 99.0",
                    "contents": "notes",
                    "date": "not-a-number",
                    "feedname": "steam_community_announcements",
                },
            ],
        },
    }
    records = parse_steam_news(payload)
    assert records[0]["published_at"] is None


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"appnews": None},
        {"appnews": {"newsitems": None}},
        {"appnews": {"newsitems": []}},
        "not a dict",
        [],
    ],
)
def test_malformed_payloads_return_empty(payload):
    assert parse_steam_news(payload) == []


def test_parser_is_registered_and_callable_via_registry():
    parser = btd6_source_parser.get("steam_btd6_news")
    assert parser is not None
    assert parser.source_key == "steam_btd6_news"
    records = parser.parse(_load("btd6_news.json"), game_version=None)
    assert [r["version"] for r in records] == ["54.0", "46.0", "40.0"]
