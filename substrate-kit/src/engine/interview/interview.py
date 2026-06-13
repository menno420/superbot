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


def record_answer(backend: Any, question: dict, answer: str, *, source: str) -> None:
    """Fill ``question``'s slot from an answer.

    ``source="user"`` confirms the slot (``filled``); any other source records a
    ``provisional`` self-answer that must be confirmed before it counts.
    """
    status = "filled" if source == "user" else "provisional"
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


def run_session(
    backend: Any,
    answers: dict[str, str],
    *,
    autonomous: bool = False,
    bank: list[dict] | None = None,
) -> dict[str, Any]:
    """Run one interview session, then attempt graduation.

    ``answers`` maps slot -> user answer. A pending question with a user answer is
    confirmed; otherwise, in ``autonomous`` mode it is self-answered provisionally.
    A session that leaves no blocking question unanswered extends the quiet streak;
    any unanswered blocking question resets it.
    """
    bank = QUESTIONS if bank is None else bank
    pending = pending_questions(backend.data, bank)
    left_blocking = False
    for question in pending:
        slot = question["slot"]
        if slot in answers:
            record_answer(backend, question, answers[slot], source="user")
        elif autonomous:
            record_answer(backend, question, f"ASSUMED: {slot}", source="assumption")
        elif question.get("priority") == "blocking":
            left_blocking = True

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
