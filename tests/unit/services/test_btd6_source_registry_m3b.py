"""M3B — migration 042 enables the 18 captured NK endpoints.

Scans ``disbot/migrations/042_btd6_sources_enable_m3b.sql`` (not a
live DB) to confirm:

* every captured endpoint receives ``base_url='https://data.ninjakiwi.com'``
* every captured endpoint is flipped to ``enabled=TRUE``
* the 5 uncaptured endpoints are NOT mentioned in 042 (so they keep
  the M3A defaults: ``base_url=NULL``, ``enabled=FALSE``)
* the static asset host (static-api.nkstatic.com) is never used as a
  registry base_url
* ``updated_by`` is never assigned a string value (BIGINT column)
"""

from __future__ import annotations

from pathlib import Path

_MIGRATION = (
    Path(__file__).resolve().parents[3]
    / "disbot"
    / "migrations"
    / "042_btd6_sources_enable_m3b.sql"
)

_CAPTURED_SOURCE_KEYS = (
    "nk_btd6_maps",
    "nk_btd6_maps_filter",
    "nk_btd6_maps_one",
    "nk_btd6_events",
    "nk_btd6_races",
    "nk_btd6_races_metadata",
    "nk_btd6_races_leaderboard",
    "nk_btd6_odyssey",
    "nk_btd6_odyssey_diff",
    "nk_btd6_odyssey_diff_maps",
    "nk_btd6_challenges",
    "nk_btd6_challenges_filter",
    "nk_btd6_challenges_one",
    "nk_btd6_ct",
    "nk_btd6_ct_tiles",
    "nk_btd6_bosses",
    "nk_btd6_bosses_metadata",
    "nk_btd6_bosses_leaderboard",
)

_UNCAPTURED_SOURCE_KEYS = (
    "nk_btd6_ct_lb_player",
    "nk_btd6_ct_lb_team",
    "nk_btd6_ct_lb_group",
    "nk_btd6_users",
    "nk_btd6_guild",
)


def _strip_comments(sql: str) -> str:
    return "\n".join(line.split("--", 1)[0] for line in sql.splitlines())


def test_migration_042_exists():
    assert (
        _MIGRATION.exists()
    ), "migration 042 must land alongside the captured fixtures"


def test_migration_042_enables_every_captured_endpoint():
    text = _MIGRATION.read_text(encoding="utf-8")
    for source_key in _CAPTURED_SOURCE_KEYS:
        assert (
            f"'{source_key}'" in text
        ), f"migration 042 missing captured source_key {source_key!r}"


def test_migration_042_does_not_enable_uncaptured_endpoints():
    text = _MIGRATION.read_text(encoding="utf-8")
    for source_key in _UNCAPTURED_SOURCE_KEYS:
        assert f"'{source_key}'" not in text, (
            f"migration 042 must not touch uncaptured source {source_key!r} "
            "(its parser scope has not been approved yet)"
        )


def test_migration_042_sets_base_url_to_data_ninjakiwi_com():
    text = _MIGRATION.read_text(encoding="utf-8")
    assert "https://data.ninjakiwi.com" in text


def test_migration_042_does_not_use_static_asset_host_as_base_url():
    """static-api.nkstatic.com appears in response bodies (mapURL,
    bossTypeURL) but must never be a source_registry base_url. Strip
    SQL comments before checking so the documentary comment that names
    the host is not a false positive."""
    code = _strip_comments(_MIGRATION.read_text(encoding="utf-8"))
    assert (
        "static-api.nkstatic.com" not in code
    ), "static asset host must not become a registry base_url"


def test_migration_042_flips_enabled_true():
    text = _MIGRATION.read_text(encoding="utf-8")
    assert "enabled    = TRUE" in text or "enabled = TRUE" in text


def test_migration_042_omits_updated_by_string_assignment():
    """``updated_by`` is BIGINT (Discord user id). A string literal
    assigned to it would fail at runtime; the migration records
    provenance in the notes column instead."""
    text = _MIGRATION.read_text(encoding="utf-8")
    assert "updated_by = '" not in text
    assert "updated_by='" not in text


def test_migration_042_records_provenance_in_notes():
    text = _MIGRATION.read_text(encoding="utf-8")
    assert (
        "[042]" in text
    ), "migration 042 should tag the notes column so re-runs are idempotent"
