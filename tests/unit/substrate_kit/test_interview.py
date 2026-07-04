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


def test_autonomous_blocking_self_answer_still_escalates(tmp_path):
    """A provisional self-answer never discharges a blocking question.

    Regression (review finding): blocking questions sort first, so autonomous
    mode always consumed them within quota — the slot went provisional, the
    quiet streak grew, and the kit could graduate with its one blocking slot
    only ASSUMED. The assumption must escalate onto open_questions (cleared by
    record_answer/confirm_slot on fill/confirm) and hold the quiet streak.
    """
    backend = _backend(tmp_path)
    # Fill every critical slot EXCEPT the blocking one (integration_mode).
    answers = {s: f"v-{s}" for s in critical_slots() if s != "integration_mode"}
    run_session(backend, answers)
    for _ in range(4):
        run_session(backend, {}, autonomous=True)
    assert backend.get("slots")["integration_mode"] == "provisional"
    assert "Q-001" in backend.get("open_questions")
    assert backend.get("stage") == "integration"
    # Confirming the assumption releases the escalation.
    from engine.interview.interview import confirm_slot

    assert confirm_slot(backend, "integration_mode", source="user")
    assert "Q-001" not in backend.get("open_questions")


def test_anti_gaming_floor_rejects_dressed_and_hollow_answers():
    # The floor must reject punctuation-dressed placeholders (todo. / TBD!) and
    # content-free answers (?? / .... / a single repeated char), not only the
    # exact stock words — or an autonomous run graduates on hollow content.
    from engine.interview.interview import answer_is_substantive

    q = {"min_len": 1}
    for hollow in ("todo", "todo.", "TBD!", "n/a?", "...", "??", "!!", "aaaa", "...."):
        assert not answer_is_substantive(q, hollow), hollow
    assert not answer_is_substantive(q, "   ")  # whitespace-only
    assert not answer_is_substantive(q, "${project_name}")  # leftover marker
    for good in ("observe", "Python 3.10", "ASSUMED: integration_mode"):
        assert answer_is_substantive(q, good), good


def test_min_len_floor_and_q001_carries_one():
    from engine.interview.interview import answer_is_substantive

    assert not answer_is_substantive({"min_len": 20}, "abcdef")  # under floor
    assert answer_is_substantive({"min_len": 3}, "abc")
    # Q-001 — the sole blocking+critical slot — must carry a floor so a single
    # char cannot graduate it (it previously had none).
    q001 = next(q for q in QUESTIONS if q["id"] == "Q-001")
    assert int(q001.get("min_len", 1)) >= 2
    assert not answer_is_substantive(q001, "x")
    assert answer_is_substantive(q001, "active")  # a real mode still passes
