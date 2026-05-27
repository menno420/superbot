"""Router pin: natural-language BTD6 question phrasings route to BTD6_ANSWER.

The user verified in production (PR #362 follow-up) that
``"what is the current boss?"`` was falling through to
``GENERAL_NL_ANSWER`` because the keyword list only had ``"boss bloon"``
and ``"boss event"`` — neither matched. This file pins the small set
of multi-word natural-question patterns that must route to BTD6 so
the AI block gatherer in ``btd6_ai_knowledge_block_service`` actually
fires for those messages.

Patterns deliberately stay multi-word so bare ``"boss"`` (workplace
boss, "be the boss") does not over-route.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from core.runtime.ai.contracts import AITask  # noqa: E402
from services import ai_task_router  # noqa: E402


@pytest.mark.parametrize(
    "text",
    [
        "what is the current boss?",
        "what is the current race?",
        "what is the current event?",
        "what boss is on right now?",
        "what race is on right now?",
        "what odyssey is happening?",
        "is the active boss hard?",
        "any active race?",
    ],
)
def test_natural_btd6_questions_route_to_answer(text):
    decision = ai_task_router.classify(text)
    assert (
        decision.task is AITask.BTD6_ANSWER
    ), f"{text!r} routed to {decision.task!r} instead of BTD6_ANSWER"


@pytest.mark.parametrize(
    "text",
    # These look BTD6-adjacent but are unambiguous non-BTD6 chatter and
    # must continue to route to the general handler.
    [
        "who is the boss of this server?",
        "what event is on the server right now?",
        "is the bot active?",
        "what's the active warn count?",
    ],
)
def test_non_btd6_lookalikes_still_route_to_general(text):
    decision = ai_task_router.classify(text)
    assert (
        decision.task is AITask.GENERAL_NL_ANSWER
    ), f"{text!r} routed to {decision.task!r} instead of GENERAL_NL_ANSWER"
