"""Unit tests for services.youtube_diagnostics — content-free media counters.

The load-bearing guarantee (P0-2 / Q-0099 follow-up): the diagnostics surface
records only bounded outcome categories + counts + a purge row-count — never any
provider content. These tests pin that contract.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import youtube_diagnostics as diag  # noqa: E402


@pytest.fixture(autouse=True)
def _reset():
    diag._reset_for_tests()
    yield
    diag._reset_for_tests()


def test_outcome_for_reason_maps_known_reasons():
    assert diag.outcome_for_reason("youtube_api_key_missing") == "key_missing"
    assert diag.outcome_for_reason("video_private_or_deleted") == "private_or_deleted"
    assert diag.outcome_for_reason("quota_limited") == "quota_limited"
    assert diag.outcome_for_reason("fetch_error") == "fetch_error"


def test_outcome_for_reason_folds_unknown_into_fetch_error():
    assert diag.outcome_for_reason("some_new_reason_string") == "fetch_error"


def test_record_provider_outcome_increments():
    diag.record_provider_outcome("success")
    diag.record_provider_outcome("success")
    diag.record_provider_outcome("quota_limited")
    counters = diag.provider_outcome_counters()
    assert counters["success"] == 2
    assert counters["quota_limited"] == 1
    # every declared category is present, zero-initialised
    assert set(counters) == set(diag.PROVIDER_OUTCOMES)


def test_record_provider_outcome_folds_unknown_category():
    diag.record_provider_outcome("not_a_category")
    assert diag.provider_outcome_counters()["fetch_error"] == 1


def test_record_purge_tracks_last_outcome():
    assert diag.last_purge_snapshot() is None
    diag.record_purge(5, ok=True)
    snap = diag.last_purge_snapshot()
    assert snap is not None
    assert snap["rows"] == 5
    assert snap["ok"] is True
    assert isinstance(snap["at"], str)  # iso timestamp, not a datetime object


def test_record_purge_failure():
    diag.record_purge(0, ok=False)
    snap = diag.last_purge_snapshot()
    assert snap is not None
    assert snap["ok"] is False


def test_snapshot_is_content_free():
    """The provider snapshot carries only counts + last-purge metadata —
    never any provider content key."""
    diag.record_provider_outcome("success")
    diag.record_purge(2, ok=True)
    snap = diag.snapshot()
    assert set(snap) == {"provider_outcomes", "last_purge"}
    # No content keys anywhere in the serialised snapshot.
    flat = repr(snap)
    for forbidden in ("metadata", "transcript", "description", "title", "video_id"):
        assert forbidden not in flat
