"""Unit tests for core.runtime.startup_outcome — PR-01b recorder."""

from __future__ import annotations

import datetime

import pytest

from core.runtime import startup_outcome


@pytest.fixture(autouse=True)
def _reset_recorder():
    startup_outcome.reset_for_tests()
    yield
    startup_outcome.reset_for_tests()


def test_record_success_stores_outcome():
    startup_outcome.record_success("command_surface_ledger")
    o = startup_outcome.get("command_surface_ledger")
    assert o is not None
    assert o.success is True
    assert o.error is None
    assert o.name == "command_surface_ledger"
    assert isinstance(o.recorded_at, datetime.datetime)


def test_record_failure_stores_type_and_message():
    try:
        raise ValueError("missing schema")
    except ValueError as exc:
        startup_outcome.record_failure("settings_registry", exc)

    o = startup_outcome.get("settings_registry")
    assert o is not None
    assert o.success is False
    assert o.error == "ValueError: missing schema"


def test_record_failure_truncates_long_messages():
    huge = "x" * 500
    try:
        raise RuntimeError(huge)
    except RuntimeError as exc:
        startup_outcome.record_failure("phase", exc)
    o = startup_outcome.get("phase")
    assert o is not None
    assert len(o.error) <= 200
    assert o.error.endswith("...")


def test_record_success_overwrites_prior_failure():
    """A successful rebuild flips the recorded state back to success."""
    try:
        raise RuntimeError("first try")
    except RuntimeError as exc:
        startup_outcome.record_failure("ledger", exc)
    startup_outcome.record_success("ledger")
    o = startup_outcome.get("ledger")
    assert o is not None
    assert o.success is True
    assert o.error is None


def test_all_outcomes_returns_sorted_tuple():
    startup_outcome.record_success("b")
    startup_outcome.record_success("a")
    startup_outcome.record_success("c")
    names = [o.name for o in startup_outcome.all_outcomes()]
    assert names == ["a", "b", "c"]


def test_get_returns_none_when_never_recorded():
    assert startup_outcome.get("missing_phase") is None


def test_reset_for_tests_clears_state():
    startup_outcome.record_success("phase")
    assert len(startup_outcome.all_outcomes()) == 1
    startup_outcome.reset_for_tests()
    assert startup_outcome.all_outcomes() == ()


def test_known_phases_lists_canonical_names():
    """Adding a new try/except in bot1.py requires extending
    KNOWN_PHASES so the readiness snapshot can distinguish a
    successful run from a never-ran startup."""
    assert "command_surface_ledger" in startup_outcome.KNOWN_PHASES
    assert "settings_registry" in startup_outcome.KNOWN_PHASES
    assert "customization_catalogue" in startup_outcome.KNOWN_PHASES
    assert "resource_provisioning_catalogue" in startup_outcome.KNOWN_PHASES
