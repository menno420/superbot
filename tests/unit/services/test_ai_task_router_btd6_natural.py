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


@pytest.mark.parametrize(
    "text",
    # Tower/hero names without explicit BTD6 keywords — these were falling
    # through to GENERAL_NL_ANSWER before the entity-alias fallback was added,
    # causing the AI to return no BTD6 facts.
    [
        "tell me about the bomb shooter",
        "what is bomb shooter",
        "how does bomb shooter work",
        "tell me about striker jones",
        "who is striker jones",
        "who is gwendolin",
        "how does dart monkey work",
        "what is the tack shooter",
        "who is sauda",
        "tell me about admiral brickell",
        "how does the heli pilot work",
    ],
)
def test_entity_name_questions_route_to_btd6_answer(text):
    """Tower/hero name mentions route to BTD6_ANSWER even without 'tower'/'hero'."""
    decision = ai_task_router.classify(text)
    assert (
        decision.task is AITask.BTD6_ANSWER
    ), f"{text!r} routed to {decision.task!r} instead of BTD6_ANSWER"


@pytest.mark.parametrize(
    "text",
    # Generic words that happen to overlap with BTD6 aliases must NOT
    # route to BTD6 — false positives degrade general chat.
    [
        "super cool idea",
        "the farm is great",
        "hello how are you",
    ],
)
def test_generic_words_do_not_over_route(text):
    """Common words that share BTD6 aliases must not trigger BTD6 routing."""
    decision = ai_task_router.classify(text)
    assert (
        decision.task is AITask.GENERAL_NL_ANSWER
    ), f"{text!r} routed to {decision.task!r} instead of GENERAL_NL_ANSWER"
