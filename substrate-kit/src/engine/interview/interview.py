"""The interview pass — fills content slots from the question bank (plan section 4).

A session asks its pending questions. A user-facing answer fills a slot
(``filled``); when no human is present the agent self-answers, recording a
*provisional* assumption (``provisional``) that never counts toward graduation
until confirmed. This is what lets an autonomous run keep moving without blocking:
it records assumptions, flags them, and moves on.
"""

from __future__ import annotations

from typing import Any

from engine.interview.question_bank import QUESTIONS
from engine.interview.stages import maybe_graduate
from engine.lib.modes import question_quota

_PRIORITY_ORDER = {"blocking": 0, "high": 1, "normal": 2}
_PLACEHOLDER_ANSWERS = frozenset({"todo", "tbd", "...", "n/a", "?"})


def critical_slots(bank: list[dict] | None = None) -> list[str]:
    """Return the slot names the bank marks as critical."""
    bank = QUESTIONS if bank is None else bank
    return [q["slot"] for q in bank if q.get("critical")]


def pending_questions(
    state: dict[str, Any],
    bank: list[dict] | None = None,
) -> list[dict]:
    """Return bank questions whose slot is not yet ``filled``."""
    bank = QUESTIONS if bank is None else bank
    slots = state.get("slots", {})
    return [q for q in bank if slots.get(q["slot"]) != "filled"]


def session_questions(
    state: dict[str, Any],
    bank: list[dict] | None = None,
) -> list[dict]:
    """Return this session's ask list: pending, priority-ordered, quota-capped.

    The cap is the integration mode's question quota (observe asks 1-2, guided a
    few, active unlimited). Blocking questions sort first, so a quota can never
    hide one.
    """
    pending = sorted(
        pending_questions(state, bank),
        key=lambda q: _PRIORITY_ORDER.get(q.get("priority", "normal"), 2),
    )
    quota = question_quota(state)
    return pending if quota is None else pending[:quota]


def answer_is_substantive(question: dict, answer: str) -> bool:
    """True when ``answer`` passes the anti-gaming floor for this slot.

    Completeness counts only non-placeholder content: no leftover ``${slot}``
    marker, not a stock placeholder word, and at least the slot's ``min_len``
    characters — so an autonomous run can't graduate on hollow answers.
    """
    text = answer.strip()
    if not text or "${" in text:
        return False
    if text.lower() in _PLACEHOLDER_ANSWERS:
        return False
    return len(text) >= int(question.get("min_len", 1))


def _clear_open_question(backend: Any, question_id: str) -> None:
    """Drop ``question_id`` from the escalated open-questions list, if present."""
    open_questions = list(backend.get("open_questions", []))
    if question_id in open_questions:
        open_questions.remove(question_id)
        backend.set("open_questions", open_questions)


def record_answer(backend: Any, question: dict, answer: str, *, source: str) -> None:
    """Fill ``question``'s slot from an answer.

    ``source="user"`` confirms the slot (``filled``) when the answer passes the
    anti-gaming floor (``partial`` otherwise); any other source records a
    ``provisional`` self-answer that must be confirmed before it counts. A
    filled answer also resolves the question's escalated open-question entry.
    """
    if source == "user":
        status = "filled" if answer_is_substantive(question, answer) else "partial"
    else:
        status = "provisional"
    slots = dict(backend.get("slots", {}))
    values = dict(backend.get("slot_values", {}))
    slots[question["slot"]] = status
    values[question["slot"]] = {
        "value": answer,
        "source": source,
        "question_id": question["id"],
    }
    with backend.transaction():
        backend.set("slots", slots)
        backend.set("slot_values", values)
    if status == "filled":
        _clear_open_question(backend, question["id"])


def confirm_slot(backend: Any, slot: str, *, source: str) -> bool:
    """Promote a ``provisional`` slot to ``filled`` (the confirmation seam).

    ``source`` records who confirmed (``"user"`` or ``"reviewer:<name>"``).
    Returns False when the slot is not provisional (nothing to confirm).
    """
    slots = dict(backend.get("slots", {}))
    if slots.get(slot) != "provisional":
        return False
    values = dict(backend.get("slot_values", {}))
    entry = dict(values.get(slot, {}))
    entry["source"] = f"confirmed:{source}"
    slots[slot] = "filled"
    values[slot] = entry
    with backend.transaction():
        backend.set("slots", slots)
        backend.set("slot_values", values)
    question_id = entry.get("question_id")
    if question_id:
        _clear_open_question(backend, question_id)
    return True


def run_session(
    backend: Any,
    answers: dict[str, str],
    *,
    autonomous: bool = False,
    bank: list[dict] | None = None,
) -> dict[str, Any]:
    """Run one interview session, then attempt graduation.

    ``answers`` maps slot -> user answer. A pending question with a user answer is
    confirmed; otherwise, in ``autonomous`` mode it is self-answered provisionally
    (within the integration mode's question quota — blocking questions sort first,
    so the quota never starves one). A session that leaves no blocking question
    unanswered extends the quiet streak; any unanswered blocking question resets
    it AND escalates onto ``open_questions``, which holds graduation until the
    question is answered.
    """
    bank = QUESTIONS if bank is None else bank
    pending = sorted(
        pending_questions(backend.data, bank),
        key=lambda q: _PRIORITY_ORDER.get(q.get("priority", "normal"), 2),
    )
    quota = question_quota(backend.data)
    left_blocking = False
    self_answered = 0
    for question in pending:
        slot = question["slot"]
        if slot in answers:
            record_answer(backend, question, answers[slot], source="user")
        elif autonomous and (quota is None or self_answered < quota):
            record_answer(backend, question, f"ASSUMED: {slot}", source="assumption")
            self_answered += 1
        elif question.get("priority") == "blocking":
            left_blocking = True
            open_questions = list(backend.get("open_questions", []))
            if question["id"] not in open_questions:
                open_questions.append(question["id"])
                backend.set("open_questions", open_questions)

    backend.set("session_count", int(backend.get("session_count", 0)) + 1)
    quiet = int(backend.get("quiet_sessions", 0))
    backend.set("quiet_sessions", 0 if left_blocking else quiet + 1)

    graduated = maybe_graduate(backend, critical_slots(bank))
    return {
        "session": backend.get("session_count"),
        "pending_after": len(pending_questions(backend.data, bank)),
        "graduated": graduated,
        "stage": backend.get("stage"),
    }
