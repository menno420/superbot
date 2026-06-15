"""Tests for the stage state machine + adaptive graduation."""

from engine.interview.stages import (
    STAGE_STEADY,
    critical_fill_ratio,
    graduation_ready,
    maybe_graduate,
)
from engine.lib.state import JsonStateBackend, default_state


def _state(**over):
    s = default_state("pid")
    s.update(over)
    return s


def test_critical_fill_ratio():
    assert critical_fill_ratio({}, []) == 1.0
    assert critical_fill_ratio({"a": "filled"}, ["a", "b"]) == 0.5
    assert critical_fill_ratio({"a": "filled", "b": "filled"}, ["a", "b"]) == 1.0
    # a provisional (self-answered) slot does NOT count as filled
    assert critical_fill_ratio({"a": "provisional"}, ["a"]) == 0.0


def test_graduation_blocked_by_unfilled_slots():
    ready, reasons = graduation_ready(_state(slots={}), ["a", "b"])
    assert not ready
    assert any("critical slots" in r for r in reasons)


def test_graduation_blocked_by_open_blocking_question():
    s = _state(slots={"a": "filled"}, open_questions=["Q-1"], quiet_sessions=9)
    ready, reasons = graduation_ready(s, ["a"])
    assert not ready
    assert any("blocking" in r for r in reasons)


def test_graduation_blocked_by_short_quiet_streak():
    ready, reasons = graduation_ready(_state(slots={"a": "filled"}, quiet_sessions=0), ["a"])
    assert not ready
    assert any("quiet streak" in r for r in reasons)


def test_graduation_ready_when_all_criteria_met():
    s = _state(slots={"a": "filled"}, quiet_sessions=3, open_questions=[])
    ready, reasons = graduation_ready(s, ["a"])
    assert ready
    assert reasons == []


def test_maybe_graduate_transitions_once(tmp_path):
    backend = JsonStateBackend(tmp_path / "s.json")
    for key, value in _state(slots={"a": "filled"}, quiet_sessions=3).items():
        backend.set(key, value)
    assert maybe_graduate(backend, ["a"]) is True
    assert backend.get("stage") == STAGE_STEADY
    # already steady -> does not re-graduate
    assert maybe_graduate(backend, ["a"]) is False
