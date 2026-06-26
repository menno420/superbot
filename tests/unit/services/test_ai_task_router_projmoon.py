"""Router pin: Limbus questions route to PROJMOON_ANSWER (the grounding path).

Project Moon knowledge-domain PR 2 (Slice A item 2,
``docs/planning/project-moon-knowledge-domain-plan-2026-06-21.md``). A message
carrying a distinctive Limbus token must route to ``AITask.PROJMOON_ANSWER`` so
``projmoon_context_service`` facts are injected — but BTD6 keeps priority, and
ordinary chatter stays general (the curation that keeps the route low-noise).
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
        "tell me about Limbus Company",
        "who is Faust in limbus?",
        "what does the ZAYIN grade mean?",
        "list every sinner",
        "explain E.G.O grades",
        "what is a mirror dungeon?",
        "how does Heathcliff work",
        "is Don Quixote good",
    ],
)
def test_limbus_questions_route_to_projmoon(text: str) -> None:
    routed = ai_task_router.classify(text)
    assert routed.task is AITask.PROJMOON_ANSWER
    assert routed.route == "projmoon.answer"


@pytest.mark.parametrize(
    "text",
    [
        # bare ambiguous English / sin words must NOT route to projmoon
        "he is the boss of this server",
        "don't be like that",
        "i sang a song yesterday",
        "what time is it",
        "pride comes before a fall",
    ],
)
def test_ordinary_chatter_does_not_route_to_projmoon(text: str) -> None:
    routed = ai_task_router.classify(text)
    assert routed.task is AITask.GENERAL_NL_ANSWER


def test_btd6_keeps_priority_over_projmoon() -> None:
    # A message that names both a BTD6 entity and a Limbus token routes to BTD6
    # (BTD6 is checked first; the two keyword sets are disjoint in practice).
    routed = ai_task_router.classify("compare the dart monkey to a limbus sinner")
    assert routed.task is AITask.BTD6_ANSWER
