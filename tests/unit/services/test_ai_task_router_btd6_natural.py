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


@pytest.mark.parametrize(
    "text",
    # Distinctive BTD6 terms the entity-alias matcher provably MISSES, so
    # they fell through to GENERAL_NL_ANSWER (no grounding) — the AI PR2
    # grounding-gating regression. Verified against the dataset:
    #   * "obyn"      — hero "Obyn Greenfoot"; bare 4-char alias dropped by
    #                   the matcher's len(al) > 4 filter.
    #   * "desperado" — a real tower; single-word tower names are skipped.
    #   * impoppable / half cash — difficulty / mode.
    [
        "how do I use obyn",
        "is obyn good on chimps",
        "is desperado a sniper upgrade",
        "tell me about desperado",
        "impoppable tips",
        "half cash strategy",
    ],
)
def test_rewidened_btd6_terms_route_to_answer(text):
    """Re-widen #388's over-slim: these route back to BTD6_ANSWER so the
    grounding context is injected even when the model doesn't call the
    btd6_lookup tool.
    """
    decision = ai_task_router.classify(text)
    assert (
        decision.task is AITask.BTD6_ANSWER
    ), f"{text!r} routed to {decision.task!r} instead of BTD6_ANSWER"


@pytest.mark.parametrize(
    "text",
    # The re-widened terms must not over-route nearby general chatter.
    # "paragon" was deliberately left OUT of the keyword set precisely so
    # this legitimate English usage stays general.
    [
        "she is a paragon of virtue",
        "i only have half my cash left",  # not the exact 'half cash' phrase
    ],
)
def test_rewidened_terms_do_not_over_route_general_chat(text):
    decision = ai_task_router.classify(text)
    assert (
        decision.task is AITask.GENERAL_NL_ANSWER
    ), f"{text!r} routed to {decision.task!r} instead of GENERAL_NL_ANSWER"


@pytest.mark.parametrize(
    "text",
    # BUG-0002 + BUG-0003 (live, 2026-06-11): boss-name and shorthand
    # questions fell through to the general path, where the model answered
    # from memory unguarded — "elite lych hp per tier" served the Standard
    # table labeled Elite; "10 041 despos … on impop" hallucinated despos =
    # Plasma Monkey Fan Club. Boss canonicals now come from the dataset;
    # "impop" / "despo" are curated keywords (substring → plurals covered).
    [
        "what is the hp of elite lych per tier",
        "how much health does bloonarius have at tier 3",
        "is dreadbloon immune to lead",
        "what does phayze do",
        "how much do 10 041 despos cost on impop",
        "despo best crosspath",
        "how much does a dart monkey cost on impop",
    ],
)
def test_boss_and_shorthand_questions_route_to_btd6_answer(text):
    decision = ai_task_router.classify(text)
    assert (
        decision.task is AITask.BTD6_ANSWER
    ), f"{text!r} routed to {decision.task!r} instead of BTD6_ANSWER"
