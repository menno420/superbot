"""M3B — Ninja Kiwi parser registry inventory.

Every captured endpoint (the 18 rows enabled by migration 042) must
have a registered parser. The 5 uncaptured endpoints (CT leaderboards,
/users, /guild) must NOT yet have a parser — their parser scope is
deferred until fixtures are captured and approved.

Per-domain shape assertions live in the dedicated
``tests/unit/services/parsers/test_ninjakiwi_*.py`` modules; this file
covers the registry-level guarantees only.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import btd6_source_parser  # noqa: E402

# 18 source_keys with implemented parsers (all enabled by migration 042).
_REGISTERED = (
    # Maps
    "nk_btd6_maps",
    "nk_btd6_maps_filter",
    "nk_btd6_maps_one",
    # Events
    "nk_btd6_events",
    # Races
    "nk_btd6_races",
    "nk_btd6_races_metadata",
    "nk_btd6_races_leaderboard",
    # Odyssey
    "nk_btd6_odyssey",
    "nk_btd6_odyssey_diff",
    "nk_btd6_odyssey_diff_maps",
    # Challenges
    "nk_btd6_challenges",
    "nk_btd6_challenges_filter",
    "nk_btd6_challenges_one",
    # CT
    "nk_btd6_ct",
    "nk_btd6_ct_tiles",
    # Bosses
    "nk_btd6_bosses",
    "nk_btd6_bosses_metadata",
    "nk_btd6_bosses_leaderboard",
)

# 5 captured-disabled source_keys; no parser approved until scope is
# explicitly opened with captured fixtures.
_UNPARSED = (
    "nk_btd6_ct_lb_player",
    "nk_btd6_ct_lb_team",
    "nk_btd6_ct_lb_group",
    "nk_btd6_users",
    "nk_btd6_guild",
)

# Non-NinjaKiwi parsers registered alongside the captured NK endpoints.
# ``steam_btd6_news`` consumes the public Steam ISteamNews feed (BTD6
# patch notes), not an NK API endpoint, so it is intentionally excluded
# from the NK captured-set pin below.
_NON_NK_PARSERS = frozenset({"steam_btd6_news"})


@pytest.fixture(autouse=True)
def _import_parsers():
    # Importing the package fires every domain module's register() call.
    import services.parsers  # noqa: F401
    yield


@pytest.mark.parametrize("source_key", _REGISTERED)
def test_captured_endpoint_has_a_registered_parser(source_key):
    parser = btd6_source_parser.get(source_key)
    assert parser is not None, (
        f"M3B must register a parser for the captured endpoint {source_key}"
    )
    assert parser.source_key == source_key


@pytest.mark.parametrize("source_key", _UNPARSED)
def test_uncaptured_endpoint_has_no_parser(source_key):
    """The 5 uncaptured endpoints have no parser. They stay disabled
    by migration 042; even if someone enabled the row by hand, the
    fact pipeline would have no way to interpret the response."""
    parser = btd6_source_parser.get(source_key)
    assert parser is None, (
        f"{source_key} should NOT have a parser — its scope has not "
        "been approved yet (no fixture captured)"
    )


def test_registry_count_matches_captured_set():
    known = set(btd6_source_parser.known_keys())
    captured = set(_REGISTERED)
    missing = captured - known
    extra = known - captured - _NON_NK_PARSERS
    assert not missing, f"captured but unregistered: {sorted(missing)}"
    assert not extra, (
        f"registered but not in captured set: {sorted(extra)} — "
        "either remove the registration or add a fixture + entry "
        "to _REGISTERED"
    )


def test_unknown_endpoints_not_in_registry():
    """Out-of-scope endpoints (Battles2, /btd6/save) must not be
    registered as parsers."""
    known = set(btd6_source_parser.known_keys())
    for forbidden in (
        "battles2_anything",
        "btd6_save",
        "nk_btd6_save",
    ):
        assert forbidden not in known


@pytest.mark.parametrize(
    ("source_key", "fixture_name"),
    [
        ("nk_btd6_maps", "btd6_maps.json"),
        ("nk_btd6_events", "btd6_events.json"),
        ("nk_btd6_races", "btd6_races.json"),
        ("nk_btd6_odyssey", "btd6_odyssey.json"),
        ("nk_btd6_challenges", "btd6_challenges.json"),
        ("nk_btd6_ct", "btd6_ct.json"),
        ("nk_btd6_bosses", "btd6_bosses.json"),
    ],
)
def test_registered_index_parser_returns_facts_for_fixture(source_key, fixture_name):
    """Smoke check: each non-parameterised index endpoint, when fed
    its captured fixture through the registry, yields a non-empty
    fact list. Per-fact shape is asserted in the per-domain test
    modules."""
    import json

    fixtures_dir = (
        Path(__file__).parents[2] / "fixtures" / "ninjakiwi"
    )
    payload = json.loads((fixtures_dir / fixture_name).read_text(encoding="utf-8"))
    parser = btd6_source_parser.get(source_key)
    assert parser is not None
    facts = parser.parse(payload, game_version=None)
    assert isinstance(facts, list)
    assert facts, f"{source_key} returned empty facts for {fixture_name}"
