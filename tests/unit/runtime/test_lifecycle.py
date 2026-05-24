"""Tests for ``core.runtime.lifecycle`` — LP-2.

Covers phase transitions, request idempotency (shutdown + restart
coalesce during DRAINING), command-admission semantics, the event ring
buffer, and the grace-seconds math.
"""

from __future__ import annotations

import time

import pytest

from core.runtime import lifecycle


@pytest.fixture(autouse=True)
def _reset_lifecycle_state() -> None:
    lifecycle.reset_for_tests()


def test_initial_state_is_starting_and_accepts_commands() -> None:
    assert lifecycle.get_phase() is lifecycle.Phase.STARTING
    assert lifecycle.can_accept_commands() is True
    assert lifecycle.is_shutting_down() is False
    assert lifecycle.restart_requested() is False
    assert lifecycle.get_pending() is None
    assert lifecycle.get_recent_events() == []


def test_set_phase_records_transition_and_is_no_op_on_same_phase() -> None:
    lifecycle.set_phase(lifecycle.Phase.RUNNING, reason="on_ready")
    lifecycle.set_phase(lifecycle.Phase.RUNNING, reason="on_ready_again")

    events = lifecycle.get_recent_events()
    assert len(events) == 1
    assert events[0].name == "phase:RUNNING"
    assert events[0].reason == "on_ready"
    assert events[0].phase is lifecycle.Phase.RUNNING


def test_running_admits_commands_draining_does_not() -> None:
    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    assert lifecycle.can_accept_commands() is True

    lifecycle.request_shutdown("sigterm")

    assert lifecycle.get_phase() is lifecycle.Phase.DRAINING
    assert lifecycle.can_accept_commands() is False
    assert lifecycle.is_shutting_down() is True


@pytest.mark.parametrize(
    "phase,admits",
    [
        (lifecycle.Phase.STARTING, True),
        (lifecycle.Phase.RUNNING, True),
        (lifecycle.Phase.DRAINING, False),
        (lifecycle.Phase.SHUTTING_DOWN, False),
        (lifecycle.Phase.RESTARTING, False),
        (lifecycle.Phase.STOPPED, False),
        (lifecycle.Phase.FAILED_STARTUP, False),
    ],
)
def test_can_accept_commands_matches_phase(
    phase: lifecycle.Phase, admits: bool
) -> None:
    lifecycle.set_phase(phase)
    assert lifecycle.can_accept_commands() is admits


def test_request_shutdown_returns_true_first_call_false_when_coalesced() -> None:
    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    assert lifecycle.request_shutdown("first") is True
    assert lifecycle.request_shutdown("second") is False
    assert lifecycle.request_shutdown("third") is False

    pending = lifecycle.get_pending()
    assert pending is not None
    assert pending.kind == "shutdown"
    assert pending.reason == "first"


def test_request_restart_returns_true_first_call_false_when_coalesced() -> None:
    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    assert lifecycle.request_restart("first") is True
    assert lifecycle.request_restart("second") is False

    pending = lifecycle.get_pending()
    assert pending is not None
    assert pending.kind == "restart"
    assert pending.reason == "first"
    assert lifecycle.restart_requested() is True


def test_restart_request_does_not_upgrade_existing_shutdown_intent() -> None:
    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    lifecycle.request_shutdown("first")
    # A subsequent restart request must NOT silently upgrade the pending
    # intent — the first request wins so cogs cannot race each other.
    assert lifecycle.request_restart("upgrade-attempt") is False

    pending = lifecycle.get_pending()
    assert pending is not None
    assert pending.kind == "shutdown"
    assert lifecycle.restart_requested() is False


def test_repeated_sigterm_coalesces_into_single_pending_request() -> None:
    """Two SIGTERMs in rapid succession must not duplicate the work."""
    lifecycle.set_phase(lifecycle.Phase.RUNNING)

    def _sigterm() -> bool:
        return lifecycle.request_shutdown("sigterm")

    accepted = [_sigterm() for _ in range(5)]
    assert accepted == [True, False, False, False, False]
    # Phase reaches DRAINING once and stays there.
    assert lifecycle.get_phase() is lifecycle.Phase.DRAINING


def test_event_buffer_captures_request_then_phase_transition() -> None:
    lifecycle.set_phase(lifecycle.Phase.RUNNING, reason="on_ready")
    lifecycle.request_shutdown("sigterm", actor="signal_handler")

    names = [event.name for event in lifecycle.get_recent_events()]
    assert names == [
        "phase:RUNNING",
        "shutdown_requested",
        "phase:DRAINING",
    ]


def test_event_buffer_records_coalesce_attempts_separately() -> None:
    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    lifecycle.request_shutdown("first")
    lifecycle.request_shutdown("second")

    names = [event.name for event in lifecycle.get_recent_events()]
    assert "shutdown_requested" in names
    assert "shutdown_requested_coalesced" in names
    coalesced = [
        event for event in lifecycle.get_recent_events()
        if event.name == "shutdown_requested_coalesced"
    ]
    assert coalesced[0].reason == "second"


def test_get_recent_events_respects_limit() -> None:
    for i in range(10):
        lifecycle._record_event(f"event_{i}")
    assert len(lifecycle.get_recent_events(limit=3)) == 3
    assert lifecycle.get_recent_events(limit=0) == []
    assert lifecycle.get_recent_events(limit=-1) == []


def test_remaining_shutdown_seconds_returns_none_when_no_pending() -> None:
    assert lifecycle.remaining_shutdown_seconds() is None


def test_remaining_shutdown_seconds_returns_none_when_no_grace_set() -> None:
    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    lifecycle.request_shutdown("sigterm")  # no grace_seconds
    assert lifecycle.remaining_shutdown_seconds() is None


def test_remaining_shutdown_seconds_counts_down_from_grace() -> None:
    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    lifecycle.request_shutdown("sigterm", grace_seconds=10.0)
    remaining = lifecycle.remaining_shutdown_seconds()
    assert remaining is not None
    # No real sleep: just assert the value is within the requested
    # window and non-negative.
    assert 0.0 <= remaining <= 10.0


def test_remaining_shutdown_seconds_clamped_to_zero_after_grace_expires(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_now = [1000.0]

    def _fake_monotonic() -> float:
        return fake_now[0]

    monkeypatch.setattr(time, "monotonic", _fake_monotonic)
    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    lifecycle.request_shutdown("sigterm", grace_seconds=5.0)
    fake_now[0] += 12.0  # past the grace window

    assert lifecycle.remaining_shutdown_seconds() == 0.0


def test_reset_for_tests_clears_phase_pending_and_events() -> None:
    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    lifecycle.request_shutdown("sigterm")
    assert lifecycle.get_pending() is not None

    lifecycle.reset_for_tests()

    assert lifecycle.get_phase() is lifecycle.Phase.STARTING
    assert lifecycle.get_pending() is None
    assert lifecycle.get_recent_events() == []


def test_record_close_executing_appends_event_with_kind_metadata() -> None:
    """The close-driver records this event right before bot.close() so
    operators can distinguish "intent recorded" from "executor ran".

    Kind goes into metadata because LifecycleEvent does not surface a
    top-level ``kind`` field — metadata is the documented payload slot.
    """
    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    lifecycle.request_shutdown("sigterm", actor="signal_handler")
    pending = lifecycle.get_pending()
    assert pending is not None

    lifecycle.record_close_executing(pending)

    names = [event.name for event in lifecycle.get_recent_events()]
    assert names[-1] == "close_executing"

    event = lifecycle.get_recent_events()[-1]
    assert event.phase is lifecycle.Phase.DRAINING
    assert event.actor == "signal_handler"
    assert event.reason == "sigterm"
    assert event.metadata == {"kind": "shutdown"}


def test_record_close_executing_carries_restart_kind_for_restart_intent() -> None:
    """Restart intent surfaces with ``kind="restart"`` so the event
    distinguishes restart-driven close from shutdown-driven close."""
    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    lifecycle.request_restart("!restart", actor="operator#0001")
    pending = lifecycle.get_pending()
    assert pending is not None

    lifecycle.record_close_executing(pending)

    event = lifecycle.get_recent_events()[-1]
    assert event.name == "close_executing"
    assert event.metadata == {"kind": "restart"}


def test_close_executing_event_appears_in_diagnostics_snapshot() -> None:
    """The diagnostics snapshot exposes recent events to !platform
    runtime; close_executing must be visible there without any extra
    plumbing."""
    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    lifecycle.request_shutdown("sigterm")
    pending = lifecycle.get_pending()
    assert pending is not None
    lifecycle.record_close_executing(pending)

    snapshot = lifecycle.diagnostics_snapshot()
    event_names = [event["name"] for event in snapshot["recent_events"]]
    assert "close_executing" in event_names


def _read_phase_gauge() -> dict[str, float]:
    """Return ``{phase_value: gauge_value}`` for ``lifecycle_phase``."""
    from services import metrics as _metrics

    samples = next(iter(_metrics.lifecycle_phase.collect())).samples
    return {
        sample.labels["phase"]: sample.value
        for sample in samples
        if sample.name == "lifecycle_phase"
    }


def test_lifecycle_phase_gauge_reflects_current_phase_after_reset() -> None:
    """The autouse reset_for_tests fixture must re-publish the gauge so
    every test sees STARTING=1 and the other phases=0; without this the
    gauge would leak stale values across tests."""
    values = _read_phase_gauge()
    assert values.get("STARTING") == 1.0
    for other in ("RUNNING", "DRAINING", "SHUTTING_DOWN", "RESTARTING", "STOPPED"):
        assert values.get(other) == 0.0


def test_lifecycle_phase_gauge_updates_on_each_transition() -> None:
    """After set_phase, exactly one series is 1.0 (the new phase) and
    the previously-current series resets to 0.0.  This is the canonical
    Prometheus state-machine encoding so Grafana panels using
    ``max by (phase) (lifecycle_phase)`` always render a single point."""
    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    values = _read_phase_gauge()
    assert values["RUNNING"] == 1.0
    assert values["STARTING"] == 0.0

    lifecycle.request_shutdown("sigterm")
    values = _read_phase_gauge()
    assert values["DRAINING"] == 1.0
    assert values["RUNNING"] == 0.0
    assert values["STARTING"] == 0.0


def test_lifecycle_phase_gauge_terminal_state_reflects_stopped() -> None:
    """Terminal phases (STOPPED, RESTARTING) must also surface — the
    bot may stop emitting metrics shortly after but the last scrape
    before exit should show the terminal state."""
    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    lifecycle.request_shutdown("sigterm")
    lifecycle.set_phase(lifecycle.Phase.SHUTTING_DOWN)
    lifecycle.set_phase(lifecycle.Phase.STOPPED)

    values = _read_phase_gauge()
    assert values["STOPPED"] == 1.0
    # Only the terminal phase is 1; all others, including the prior
    # SHUTTING_DOWN, must be 0.
    nonzero = {phase for phase, value in values.items() if value > 0}
    assert nonzero == {"STOPPED"}


def _lifecycle_event_counter(event: str) -> float:
    """Return the current value of ``lifecycle_event_total{event=...}``."""
    from services import metrics as _metrics

    return _metrics.lifecycle_event_total.labels(event=event)._value.get()


def test_lifecycle_event_counter_increments_on_phase_transition() -> None:
    """Every ``set_phase`` to a new phase records a ring-buffer event
    AND increments the Prometheus counter for that event name."""
    before = _lifecycle_event_counter("phase:RUNNING")
    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    assert _lifecycle_event_counter("phase:RUNNING") == before + 1


def test_lifecycle_event_counter_increments_on_shutdown_request() -> None:
    """``request_shutdown`` increments shutdown_requested AND the phase
    transition counter for DRAINING."""
    before_req = _lifecycle_event_counter("shutdown_requested")
    before_drain = _lifecycle_event_counter("phase:DRAINING")
    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    lifecycle.request_shutdown("sigterm")
    assert _lifecycle_event_counter("shutdown_requested") == before_req + 1
    assert _lifecycle_event_counter("phase:DRAINING") == before_drain + 1


def test_lifecycle_event_counter_increments_on_coalesced_shutdown() -> None:
    """The MOST valuable series: multiple SIGTERMs in quick succession
    surface as shutdown_requested_coalesced.  Operators alerting on
    rate(lifecycle_event_total{event="shutdown_requested_coalesced"}[5m])
    catch SIGTERM-storm misconfigurations (e.g. an orchestrator sending
    SIGTERM faster than the bot drains)."""
    before = _lifecycle_event_counter("shutdown_requested_coalesced")
    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    lifecycle.request_shutdown("first")
    # Second and third requests coalesce.
    lifecycle.request_shutdown("second")
    lifecycle.request_shutdown("third")
    assert _lifecycle_event_counter("shutdown_requested_coalesced") == before + 2


# ---------------------------------------------------------------------------
# Startup-duration observation — lifecycle_startup_seconds histogram.
# ---------------------------------------------------------------------------


def _startup_seconds_count() -> float:
    """Read the +Inf count from lifecycle_startup_seconds."""
    from services import metrics as _metrics

    samples = next(iter(_metrics.lifecycle_startup_seconds.collect())).samples
    return next(s.value for s in samples if s.name.endswith("_count"))


def test_startup_seconds_observed_on_first_starting_to_running() -> None:
    """The first STARTING → RUNNING transition observes the histogram
    exactly once.  Anchored at module import time (or
    reset_for_tests), so the observation captures cold-boot health."""
    before = _startup_seconds_count()
    lifecycle.set_phase(lifecycle.Phase.RUNNING, reason="on_ready")
    assert _startup_seconds_count() == before + 1


def test_startup_seconds_not_re_observed_on_reconnect() -> None:
    """A second RUNNING transition (e.g. Discord gateway reconnect-
    driven on_ready) must not re-observe — the histogram tracks
    cold-boot timing, not connection churn."""
    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    after_first = _startup_seconds_count()
    # Simulate a drain + reconnect cycle.
    lifecycle.set_phase(lifecycle.Phase.DRAINING)
    lifecycle.set_phase(lifecycle.Phase.RUNNING, reason="reconnect")
    assert _startup_seconds_count() == after_first


def test_startup_seconds_anchor_resets_in_reset_for_tests() -> None:
    """``reset_for_tests`` re-stamps the module-load anchor and clears
    the one-shot flag so subsequent set_phase(RUNNING) calls observe
    again. Without this every test in the suite would share one
    process-wide one-shot and only the first ordered test would see an
    observation."""
    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    after_first = _startup_seconds_count()
    lifecycle.reset_for_tests()
    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    assert _startup_seconds_count() == after_first + 1


def test_diagnostics_snapshot_exposes_startup_observed_flag() -> None:
    """``startup_duration_observed`` and ``module_load_age_seconds``
    are operator-visible signals: the boolean tells you whether the
    one-shot fired this process, the age tells you how long ago the
    bot imported lifecycle (useful when investigating a late
    on_ready)."""
    snap = lifecycle.diagnostics_snapshot()
    assert snap["startup_duration_observed"] is False
    assert isinstance(snap["module_load_age_seconds"], float)
    assert snap["module_load_age_seconds"] >= 0.0

    lifecycle.set_phase(lifecycle.Phase.RUNNING)

    snap = lifecycle.diagnostics_snapshot()
    assert snap["startup_duration_observed"] is True


# ---------------------------------------------------------------------------
# Close outcome recorders — record_close_completed, record_close_timeout.
# ---------------------------------------------------------------------------


def test_record_close_completed_captures_duration_and_kind() -> None:
    """``close_completed`` is the canonical "clean unwind" signal in
    the ring buffer.  Kind + duration_seconds metadata lets the embed
    render the close cost without re-deriving it from monotonic
    timestamps."""
    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    lifecycle.request_shutdown("sigterm", actor="signal_handler")
    pending = lifecycle.get_pending()
    assert pending is not None

    lifecycle.record_close_completed(pending, duration_seconds=2.5)

    event = lifecycle.get_recent_events()[-1]
    assert event.name == "close_completed"
    assert event.metadata == {
        "kind": "shutdown",
        "duration_seconds": 2.5,
    }


def test_record_close_timeout_captures_timeout_and_kind() -> None:
    """``close_timeout`` is the wedged-close signal.  ``kind`` lets
    operators tell shutdown-wedge from restart-wedge; ``timeout_seconds``
    pins the budget the driver actually used (in case the constant is
    tuned later)."""
    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    lifecycle.request_restart("!restart", actor="op")
    pending = lifecycle.get_pending()
    assert pending is not None

    lifecycle.record_close_timeout(pending, timeout_seconds=20.0)

    event = lifecycle.get_recent_events()[-1]
    assert event.name == "close_timeout"
    assert event.metadata == {
        "kind": "restart",
        "timeout_seconds": 20.0,
    }


def test_diagnostics_snapshot_exposes_event_metadata() -> None:
    """Recent events in the snapshot must carry the ``metadata`` dict
    so embed builders can render kind / duration / timeout without
    re-importing the lifecycle module."""
    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    lifecycle.request_shutdown("sigterm")
    pending = lifecycle.get_pending()
    assert pending is not None
    lifecycle.record_close_executing(pending)
    lifecycle.record_close_completed(pending, duration_seconds=1.0)
    lifecycle.record_close_timeout(pending, timeout_seconds=20.0)

    snap = lifecycle.diagnostics_snapshot()
    metas = {e["name"]: e["metadata"] for e in snap["recent_events"]}
    assert metas["close_executing"] == {"kind": "shutdown"}
    assert metas["close_completed"] == {
        "kind": "shutdown",
        "duration_seconds": 1.0,
    }
    assert metas["close_timeout"] == {
        "kind": "shutdown",
        "timeout_seconds": 20.0,
    }
