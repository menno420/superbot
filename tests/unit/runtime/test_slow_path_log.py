"""Tests for core.runtime.slow_path_log — Phase S3.2 / O-3."""

from __future__ import annotations

import pytest

from core.runtime import slow_path_log


@pytest.fixture(autouse=True)
def _reset():
    slow_path_log._reset_for_tests()
    yield
    slow_path_log._reset_for_tests()


# ---------------------------------------------------------------------------
# maybe_record — threshold gating
# ---------------------------------------------------------------------------


def test_below_threshold_is_dropped():
    slow_path_log.configure(threshold_ms=500.0)
    slow_path_log.maybe_record("db_query", "select:xp", 100.0)
    assert slow_path_log.snapshot() == []


def test_above_threshold_is_recorded():
    slow_path_log.configure(threshold_ms=500.0)
    slow_path_log.maybe_record("db_query", "select:xp", 1234.5)
    entries = slow_path_log.snapshot()
    assert len(entries) == 1
    entry = entries[0]
    assert entry.kind == "db_query"
    assert entry.name == "select:xp"
    assert entry.duration_ms == 1234.5


def test_exact_threshold_is_recorded():
    """At-or-above-threshold observations are recorded (`<` gate)."""
    slow_path_log.configure(threshold_ms=500.0)
    slow_path_log.maybe_record("command", "foo", 500.0)
    assert len(slow_path_log.snapshot()) == 1


def test_just_below_threshold_is_dropped():
    slow_path_log.configure(threshold_ms=500.0)
    slow_path_log.maybe_record("command", "foo", 499.9)
    assert slow_path_log.snapshot() == []


def test_extra_kwargs_preserved_on_entry():
    slow_path_log.configure(threshold_ms=10.0)
    slow_path_log.maybe_record(
        "interaction",
        "economy",
        100.0,
        request_id="abc",
        user_id=42,
    )
    entry = slow_path_log.snapshot()[0]
    assert entry.extra == {"request_id": "abc", "user_id": 42}


# ---------------------------------------------------------------------------
# Ring-buffer bound
# ---------------------------------------------------------------------------


def test_capacity_bound_drops_oldest_first():
    slow_path_log.configure(capacity=3, threshold_ms=10.0)
    for i in range(5):
        slow_path_log.maybe_record("db_query", f"q{i}", 100.0)
    entries = slow_path_log.snapshot()
    assert len(entries) == 3
    # Oldest two dropped — names q2, q3, q4 should remain in that order.
    assert [e.name for e in entries] == ["q2", "q3", "q4"]


def test_configure_capacity_shrink_truncates_existing():
    slow_path_log.configure(capacity=5, threshold_ms=10.0)
    for i in range(5):
        slow_path_log.maybe_record("db_query", f"q{i}", 100.0)
    slow_path_log.configure(capacity=2)
    entries = slow_path_log.snapshot()
    assert len(entries) == 2
    # The 2 most-recent should survive.
    assert [e.name for e in entries] == ["q3", "q4"]


def test_threshold_change_takes_effect_immediately():
    slow_path_log.configure(threshold_ms=500.0)
    slow_path_log.maybe_record("db_query", "fast", 100.0)
    slow_path_log.configure(threshold_ms=50.0)
    slow_path_log.maybe_record("db_query", "now_slow_enough", 100.0)
    names = [e.name for e in slow_path_log.snapshot()]
    assert names == ["now_slow_enough"]


# ---------------------------------------------------------------------------
# Public accessors
# ---------------------------------------------------------------------------


def test_threshold_ms_and_capacity_accessors():
    slow_path_log.configure(capacity=42, threshold_ms=99.9)
    assert slow_path_log.threshold_ms() == 99.9
    assert slow_path_log.capacity() == 42


def test_diagnostics_snapshot_registers_with_diagnostics_service():
    from services import diagnostics_service

    # The provider should be registered at module import.
    snap = diagnostics_service.snapshot("slow_path")
    assert snap == {
        "count": 0,
        "threshold_ms": slow_path_log.threshold_ms(),
        "capacity": slow_path_log.capacity(),
    }


def test_diagnostics_snapshot_reflects_recorded_entries():
    from services import diagnostics_service

    slow_path_log.configure(capacity=10, threshold_ms=10.0)
    for i in range(3):
        slow_path_log.maybe_record("db_query", f"q{i}", 100.0)
    snap = diagnostics_service.snapshot("slow_path")
    assert snap["count"] == 3
    assert snap["threshold_ms"] == 10.0
    assert snap["capacity"] == 10
