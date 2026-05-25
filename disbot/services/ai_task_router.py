"""Map an inbound message to an :class:`AITask`.

M2 ships two routes:

* ``AITask.BTD6_ANSWER`` — message looks like a BTD6 question.
* ``AITask.GENERAL_NL_ANSWER`` — fallback.

The classifier is deterministic and cheap: a keyword scan, not an
LLM call. Real intent classification can land in M4 once BTD6 has
real facts to ground against.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.runtime.ai.contracts import AITask

# Keep this list short and curated. It biases the router toward BTD6;
# anything not matched falls through to GENERAL_NL_ANSWER.
_BTD6_KEYWORDS = (
    "btd6",
    "bloons",
    "bloon",
    "moab",
    "ddt",
    "bad ",
    "bfb",
    "zomg",
    "tower",
    "hero",
    "obyn",
    "psi",
    "ezili",
    "geraldo",
    "etienne",
    "chimps",
    "halfcash",
    "magicmonkeys",
    "alternate bloons",
    "round ",
    "freeplay",
    "deflation",
    "apopalypse",
    "primary only",
    "military only",
    "magic only",
    "support only",
    "boss bloon",
    "ninja kiwi",
    "monkey",
    "primary monkey",
)


@dataclass(frozen=True)
class RoutedTask:
    task: AITask
    route: str  # short string for the audit row (e.g. "btd6.answer")
    confidence: float  # 0.0 .. 1.0 — informational only in M2


def classify(
    message_text: str,
    *,
    channel_is_strategy_intake: bool = False,
) -> RoutedTask:
    """Return the routed task for ``message_text``.

    BTD6-related questions route to :attr:`AITask.BTD6_ANSWER` so
    M3+ can layer in real fact retrieval. Everything else falls back
    to :attr:`AITask.GENERAL_NL_ANSWER`.

    When ``channel_is_strategy_intake`` is True (M4 — the channel is
    bound to ``btd6.strategy_submission_channel``) and the message
    looks BTD6-related, route to :attr:`AITask.BTD6_STRATEGY_REVIEW`
    so the message flows into the strategy review pipeline.
    """
    lowered = (message_text or "").lower()
    looks_btd6 = any(keyword in lowered for keyword in _BTD6_KEYWORDS)
    if channel_is_strategy_intake and looks_btd6:
        return RoutedTask(
            task=AITask.BTD6_STRATEGY_REVIEW,
            route="btd6.strategy_review",
            confidence=0.7,
        )
    if looks_btd6:
        return RoutedTask(
            task=AITask.BTD6_ANSWER,
            route="btd6.answer",
            confidence=0.6,
        )
    return RoutedTask(
        task=AITask.GENERAL_NL_ANSWER,
        route="general.nl_answer",
        confidence=0.4,
    )


__all__ = ["RoutedTask", "classify"]
