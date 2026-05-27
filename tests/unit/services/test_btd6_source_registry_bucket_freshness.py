"""Tests for the public ``bucket_freshness`` helper.

Source-health (per source_key) and the fact-summary panel (per
entity_kind) both depend on this — single source of truth for the
fresh/aging/stale/never buckets.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from services import btd6_source_registry


def test_bucket_freshness_is_exported():
    """Pin against accidental privatisation."""
    assert "bucket_freshness" in btd6_source_registry.__all__
    assert callable(btd6_source_registry.bucket_freshness)


def test_none_maps_to_never():
    assert btd6_source_registry.bucket_freshness(None) == "never"


def test_fresh_under_six_hours():
    now = datetime.now(tz=timezone.utc)
    assert btd6_source_registry.bucket_freshness(now) == "fresh"
    # Use 5h59m to stay safely under the 6h threshold despite the
    # microseconds of drift between the timestamp construction and
    # the bucket_freshness call.
    assert (
        btd6_source_registry.bucket_freshness(now - timedelta(hours=5, minutes=59))
        == "fresh"
    )


def test_aging_between_six_hours_and_two_days():
    now = datetime.now(tz=timezone.utc)
    assert btd6_source_registry.bucket_freshness(now - timedelta(hours=7)) == "aging"
    assert btd6_source_registry.bucket_freshness(now - timedelta(days=1)) == "aging"


def test_stale_beyond_two_days():
    now = datetime.now(tz=timezone.utc)
    assert (
        btd6_source_registry.bucket_freshness(now - timedelta(days=2, hours=1))
        == "stale"
    )
    assert btd6_source_registry.bucket_freshness(now - timedelta(days=10)) == "stale"


def test_naive_datetime_treated_as_utc():
    """Naive datetimes are interpreted as UTC, not local time."""
    now_utc_naive = datetime.utcnow()
    # Should bucket exactly the same as a tz-aware UTC now.
    assert btd6_source_registry.bucket_freshness(now_utc_naive) == "fresh"


def test_bucket_for_alias_still_works():
    """``_bucket_for`` is kept as an alias for in-module readers."""
    assert btd6_source_registry._bucket_for is btd6_source_registry.bucket_freshness
