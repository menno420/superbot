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


# ---------------------------------------------------------------------------
# LP-7: per-phase timing + metadata + summary_status + record_phase
# ---------------------------------------------------------------------------


def test_legacy_record_success_leaves_timing_fields_unset():
    """Backwards compatibility: legacy callers that omit timing get
    ``started_at=None`` and ``duration_ms=None``; ``metadata`` is the
    empty dict."""
    startup_outcome.record_success("legacy")
    o = startup_outcome.get("legacy")
    assert o is not None
    assert o.started_at is None
    assert o.duration_ms is None
    assert o.metadata == {}


def test_record_success_with_timing_derives_duration_ms():
    import datetime as _dt

    started = _dt.datetime.now(tz=_dt.timezone.utc) - _dt.timedelta(milliseconds=150)
    startup_outcome.record_success(
        "timed",
        started_at=started,
        metadata={"cogs": 24},
    )
    o = startup_outcome.get("timed")
    assert o is not None
    assert o.started_at is started
    assert o.duration_ms is not None
    assert o.duration_ms >= 100.0  # ≥ requested delay
    assert o.duration_ms < 10000.0  # under 10s slack
    assert o.metadata == {"cogs": 24}


def test_record_failure_with_timing_derives_duration_ms():
    import datetime as _dt

    started = _dt.datetime.now(tz=_dt.timezone.utc) - _dt.timedelta(milliseconds=80)
    try:
        raise RuntimeError("boom")
    except RuntimeError as exc:
        startup_outcome.record_failure("failed_phase", exc, started_at=started)
    o = startup_outcome.get("failed_phase")
    assert o is not None
    assert o.success is False
    assert o.error is not None
    assert "boom" in o.error
    assert o.duration_ms is not None
    assert o.duration_ms >= 50.0


def test_record_phase_context_manager_records_success_on_clean_exit():
    with startup_outcome.record_phase("ctx_ok", metadata={"k": "v"}):
        pass
    o = startup_outcome.get("ctx_ok")
    assert o is not None
    assert o.success is True
    assert o.metadata == {"k": "v"}
    assert o.duration_ms is not None
    assert o.duration_ms >= 0.0


def test_record_phase_context_manager_records_failure_and_reraises():
    import pytest as _pytest

    with _pytest.raises(RuntimeError, match="boom"):
        with startup_outcome.record_phase("ctx_fail"):
            raise RuntimeError("boom")
    o = startup_outcome.get("ctx_fail")
    assert o is not None
    assert o.success is False
    assert o.error is not None
    assert "boom" in o.error


def test_summary_status_empty_for_no_outcomes():
    assert startup_outcome.summary_status() is startup_outcome.SummaryStatus.EMPTY


def test_summary_status_ok_when_every_outcome_succeeded():
    startup_outcome.record_success("a")
    startup_outcome.record_success("b")
    assert startup_outcome.summary_status() is startup_outcome.SummaryStatus.OK


def test_summary_status_failed_when_every_outcome_failed():
    try:
        raise RuntimeError("x")
    except RuntimeError as exc:
        startup_outcome.record_failure("a", exc)
        startup_outcome.record_failure("b", exc)
    assert startup_outcome.summary_status() is startup_outcome.SummaryStatus.FAILED


def test_summary_status_degraded_when_mixed():
    startup_outcome.record_success("a")
    try:
        raise RuntimeError("x")
    except RuntimeError as exc:
        startup_outcome.record_failure("b", exc)
    assert startup_outcome.summary_status() is startup_outcome.SummaryStatus.DEGRADED


def test_summary_status_accepts_explicit_outcomes_argument():
    """``summary_status`` can derive from an arbitrary outcomes tuple
    rather than reading the live recorder — useful for unit tests of
    consumers that build outcomes synthetically."""
    import datetime as _dt

    now = _dt.datetime.now(tz=_dt.timezone.utc)
    synthetic = (
        startup_outcome.StartupOutcome(
            name="x",
            success=True,
            error=None,
            recorded_at=now,
        ),
        startup_outcome.StartupOutcome(
            name="y",
            success=False,
            error="X: y",
            recorded_at=now,
        ),
    )
    assert (
        startup_outcome.summary_status(synthetic)
        is startup_outcome.SummaryStatus.DEGRADED
    )
