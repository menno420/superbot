"""Tests for the interview pass (slot-filling, assumptions, graduation)."""

from engine.interview.interview import (
    critical_slots,
    pending_questions,
    record_answer,
    run_session,
)
from engine.interview.question_bank import QUESTIONS
from engine.lib.state import JsonStateBackend, default_state


def _backend(tmp_path):
    backend = JsonStateBackend(tmp_path / ".substrate" / "state.json")
    for key, value in default_state("pid").items():
        backend.set(key, value)
    return backend


def test_critical_slots_are_a_subset_of_the_bank():
    crit = critical_slots()
    assert crit
    assert set(crit) <= {q["slot"] for q in QUESTIONS}


def test_all_questions_pending_initially(tmp_path):
    backend = _backend(tmp_path)
    assert len(pending_questions(backend.data)) == len(QUESTIONS)


def test_user_answer_fills_slot(tmp_path):
    backend = _backend(tmp_path)
    question = QUESTIONS[0]
    record_answer(backend, question, "active", source="user")
    assert backend.get("slots")[question["slot"]] == "filled"
    assert backend.get("slot_values")[question["slot"]]["source"] == "user"


def test_self_answer_is_only_provisional(tmp_path):
    backend = _backend(tmp_path)
    question = QUESTIONS[0]
    record_answer(backend, question, "a guess", source="assumption")
    assert backend.get("slots")[question["slot"]] == "provisional"


def test_run_session_fills_criticals_and_counts(tmp_path):
    backend = _backend(tmp_path)
    answers = {slot: f"v-{slot}" for slot in critical_slots()}
    result = run_session(backend, answers)
    assert result["session"] == 1
    for slot in critical_slots():
        assert backend.get("slots")[slot] == "filled"


def test_run_session_graduates_after_quiet_streak(tmp_path):
    backend = _backend(tmp_path)
    answers = {slot: f"v-{slot}" for slot in critical_slots()}
    run_session(backend, answers)  # session 1: fill criticals, quiet=1
    run_session(backend, {})  # session 2: quiet=2
    result = run_session(backend, {})  # session 3: quiet=3 -> graduate
    assert result["graduated"] is True
    assert backend.get("stage") == "steady"


def test_autonomous_self_answers_never_graduate(tmp_path):
    backend = _backend(tmp_path)
    # Only self-answers (provisional) -> criticals never reach "filled".
    for _ in range(5):
        run_session(backend, {}, autonomous=True)
    assert backend.get("stage") == "integration"
