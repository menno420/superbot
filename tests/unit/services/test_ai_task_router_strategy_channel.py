"""M4 — task router honours the strategy-intake channel binding."""

from __future__ import annotations

import sys
from pathlib import Path

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from core.runtime.ai.contracts import AITask  # noqa: E402
from services import ai_task_router  # noqa: E402


def test_btd6_text_in_strategy_channel_routes_to_review():
    decision = ai_task_router.classify(
        "Here is my chimps strategy with quad cannon and obyn",
        channel_is_strategy_intake=True,
    )
    assert decision.task is AITask.BTD6_STRATEGY_REVIEW
    assert decision.route == "btd6.strategy_review"


def test_btd6_text_outside_strategy_channel_routes_to_answer():
    decision = ai_task_router.classify(
        "Here is my chimps strategy with quad cannon and obyn",
        channel_is_strategy_intake=False,
    )
    assert decision.task is AITask.BTD6_ANSWER


def test_non_btd6_text_stays_general_even_in_strategy_channel():
    decision = ai_task_router.classify(
        "good morning everyone",
        channel_is_strategy_intake=True,
    )
    assert decision.task is AITask.GENERAL_NL_ANSWER
