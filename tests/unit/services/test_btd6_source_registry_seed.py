"""M3A — every official NK API endpoint is pre-registered.

Scans the migration SQL so the test does not need a live DB. Every
endpoint listed in the refined-direction plan's M3A inventory must
appear with ``source_kind='official_api'``, ``trust_tier=1``,
``enabled=FALSE``, a stable ``source_key``, and a path template.
"""

from __future__ import annotations

import re
from pathlib import Path

_MIGRATION = (
    Path(__file__).resolve().parents[3]
    / "disbot"
    / "migrations"
    / "040_btd6_sources.sql"
)


# (source_key, path_template fragment). Matches the M3A plan inventory.
_EXPECTED = [
    ("nk_btd6_races",             "/btd6/races"),
    ("nk_btd6_races_leaderboard", "/btd6/races/:raceID/leaderboard"),
    ("nk_btd6_races_metadata",    "/btd6/races/:raceID/metadata"),
    ("nk_btd6_bosses",            "/btd6/bosses"),
    ("nk_btd6_bosses_leaderboard",
     "/btd6/bosses/:bossID/leaderboard/:type/:teamSize"),
    ("nk_btd6_bosses_metadata",
     "/btd6/bosses/:bossID/metadata/:difficulty"),
    ("nk_btd6_users",             "/btd6/users/:userID"),
    ("nk_btd6_challenges",        "/btd6/challenges"),
    ("nk_btd6_challenges_filter",
     "/btd6/challenges/filter/:challengeFilter"),
    ("nk_btd6_challenges_one",    "/btd6/challenges/challenge/:challengeID"),
    ("nk_btd6_ct",                "/btd6/ct"),
    ("nk_btd6_ct_tiles",          "/btd6/ct/:ctID/tiles"),
    ("nk_btd6_ct_lb_player",      "/btd6/ct/:ctID/leaderboard/player"),
    ("nk_btd6_ct_lb_team",        "/btd6/ct/:ctID/leaderboard/team"),
    ("nk_btd6_ct_lb_group",
     "/btd6/ct/:ctID/leaderboard/group/:groupID"),
    ("nk_btd6_guild",             "/btd6/guild/:guildID"),
    ("nk_btd6_odyssey",           "/btd6/odyssey"),
    ("nk_btd6_odyssey_diff",      "/btd6/odyssey/:odysseyID/:difficulty"),
    ("nk_btd6_odyssey_diff_maps",
     "/btd6/odyssey/:odysseyID/:difficulty/maps"),
    ("nk_btd6_maps",              "/btd6/maps"),
    ("nk_btd6_maps_filter",       "/btd6/maps/filter/:mapFilter"),
    ("nk_btd6_maps_one",          "/btd6/maps/map/:mapID"),
    ("nk_btd6_events",            "/btd6/events"),
]


def test_seed_inserts_every_planned_endpoint():
    text = _MIGRATION.read_text(encoding="utf-8")
    missing: list[str] = []
    for source_key, path_template in _EXPECTED:
        if f"'{source_key}'" not in text:
            missing.append(source_key)
            continue
        if path_template not in text:
            missing.append(f"{source_key} (path)")
    assert not missing, (
        "Seed inserts in migration 040 are missing endpoints: "
        + ", ".join(missing)
    )


def test_seed_uses_official_api_kind_and_tier_1():
    text = _MIGRATION.read_text(encoding="utf-8")
    # All seed inserts share the same VALUES tuple shape; verify the
    # 'official_api' kind appears for every nk_btd6_* key.
    for source_key, _ in _EXPECTED:
        match = re.search(
            rf"'{re.escape(source_key)}'[^;]*?'official_api'\s*,\s*1",
            text,
            re.DOTALL,
        )
        assert match, (
            f"seed row {source_key!r} does not declare "
            "source_kind='official_api' and trust_tier=1"
        )


def test_seed_keeps_enabled_false_in_m3a():
    """The fetcher refuses any source with enabled=TRUE that lacks a
    confirmed base_url; M3A seeds must not flip enabled until M3B."""
    text = _MIGRATION.read_text(encoding="utf-8")
    for source_key, _ in _EXPECTED:
        # The matched chunk per row ends with the FALSE flag right
        # before the notes column. Find the row and ensure FALSE is
        # the enabled value.
        match = re.search(
            rf"'{re.escape(source_key)}'[^;]*?(FALSE|TRUE)\s*,",
            text,
            re.DOTALL | re.IGNORECASE,
        )
        assert match is not None, f"could not locate seed row for {source_key}"
        assert match.group(1).upper() == "FALSE", (
            f"seed row {source_key!r} flipped enabled=TRUE in M3A — "
            "M3B flips this after base URL + response format confirmed"
        )


def _strip_comments(sql: str) -> str:
    return "\n".join(
        line.split("--", 1)[0]
        for line in sql.splitlines()
    )


def test_save_oak_endpoint_is_deferred():
    code = _strip_comments(_MIGRATION.read_text(encoding="utf-8"))
    assert "btd6/save" not in code, (
        "/btd6/save/:oakID requires an opt-in / OAK-token / redaction "
        "design before any seed row lands"
    )


def test_battles2_endpoints_are_out_of_scope():
    code = _strip_comments(_MIGRATION.read_text(encoding="utf-8"))
    assert "battles2" not in code.lower(), (
        "Battles2 endpoints are out of scope for this initiative"
    )
