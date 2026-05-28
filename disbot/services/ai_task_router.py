"""Map an inbound message to an :class:`AITask`.

M2 ships two routes:

* ``AITask.BTD6_ANSWER`` — message looks like a BTD6 question.
* ``AITask.GENERAL_NL_ANSWER`` — fallback.

The classifier is deterministic and cheap: a keyword scan, not an
LLM call. Real intent classification can land in M4 once BTD6 has
real facts to ground against.
"""

from __future__ import annotations

import re
import threading
from dataclasses import dataclass

from core.runtime.ai.contracts import AITask

_YOUTUBE_URL_RE = re.compile(
    r"(?:https?://)?(?:www\.)?(?:youtube\.com/(?:watch\?v=|shorts/)|youtu\.be/)([A-Za-z0-9_-]{11})",
)
_VIDEO_QUESTION_WORDS = frozenset(
    {"what", "explain", "how", "why", "summarize", "describe", "tell"},
)


def _count_youtube_urls(text: str) -> int:
    return len(_YOUTUBE_URL_RE.findall(text))


def _has_question_intent(text: str) -> bool:
    words = frozenset(text.lower().split())
    return bool(words & _VIDEO_QUESTION_WORDS)


# Keep this list short and curated. It biases the router toward BTD6;
# anything not matched falls through to GENERAL_NL_ANSWER. Every entry
# must be a BTD6 anchor on its own — bare "event" / "active" / "right
# now" / "leaderboard" / "stale" / "freshness" do NOT belong here: they
# would over-route non-BTD6 questions (server events, "is the bot
# active", XP leaderboard, "is the database stale"). The
# anchor + state-term heuristic for live-state questions lives in
# services.btd6_ai_knowledge_block_service.
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
    "boss event",
    "current boss",
    "current race",
    "current event",
    "what boss",
    "what race",
    "what odyssey",
    "active boss",
    "active race",
    "ninja kiwi",
    "ninjakiwi",
    "monkey",
    "primary monkey",
    "odyssey",
    "contested territory",
    "race ",
    "banned hero",
    "banned tower",
)


# ---------------------------------------------------------------------------
# Entity-alias cache — lazy, thread-safe, dataset-backed
# ---------------------------------------------------------------------------

_entity_aliases_lock = threading.Lock()
_entity_aliases: tuple[frozenset[str], frozenset[str]] | None = None  # (multi, single)


def _get_entity_aliases() -> tuple[frozenset[str], frozenset[str]]:
    """Return (multi_word_phrases, single_word_tokens) from the BTD6 dataset.

    Built once from the fixture JSON on first call and cached for the
    process lifetime. Falls back to empty sets if the dataset is
    unavailable, keeping the router lightweight and fault-tolerant.

    Multi-word phrases are matched as substrings; single-word tokens are
    matched against the whitespace-tokenised word set so generic words
    like 'ice' or 'bomb' are not treated as BTD6 anchors — only
    unambiguous hero names (Gwendolin, Sauda, Corvus, …) are included
    in the single-word set.
    """
    global _entity_aliases
    if _entity_aliases is not None:
        return _entity_aliases
    with _entity_aliases_lock:
        if _entity_aliases is not None:
            return _entity_aliases
        try:
            from services import btd6_data_service

            ds = btd6_data_service.get_dataset()
        except Exception:
            _entity_aliases = (frozenset(), frozenset())
            return _entity_aliases

        multi: set[str] = set()
        single: set[str] = set()

        for tower in ds.towers:
            name = tower.canonical.lower()
            if " " in name:
                multi.add(name)
            # Single-word tower aliases are too generic (bomb, ice, glue…) —
            # skip them to avoid false positives on non-BTD6 messages.

        for hero in ds.heroes:
            name = hero.canonical.lower()
            if " " in name:
                multi.add(name)
            else:
                # Hero canonical names are distinctive enough for whole-word
                # matching (gwendolin, sauda, corvus, quincy, etienne, …).
                single.add(name)
            # Include unambiguous aliases too (e.g. "brickell", "fusty").
            for alias in hero.aliases:
                al = alias.lower()
                if " " in al:
                    multi.add(al)
                elif len(al) > 4:  # skip ultra-short aliases (q, eti, ado…)
                    single.add(al)

        _entity_aliases = (frozenset(multi), frozenset(single))
        return _entity_aliases


def _looks_like_btd6_entity(lowered: str) -> bool:
    """True when the text references a BTD6 tower or hero by name/alias."""
    multi, single = _get_entity_aliases()
    if any(phrase in lowered for phrase in multi):
        return True
    if not single:
        return False
    tokens = frozenset(re.findall(r"[a-z0-9]+", lowered))
    return bool(tokens & single)


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
    if not looks_btd6:
        looks_btd6 = _looks_like_btd6_entity(lowered)
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
    url_count = _count_youtube_urls(message_text or "")
    if url_count >= 2:
        return RoutedTask(
            task=AITask.VIDEO_COMPARE,
            route="video.compare",
            confidence=0.90,
        )
    if url_count == 1 and _has_question_intent(message_text or ""):
        return RoutedTask(task=AITask.VIDEO_QA, route="video.qa", confidence=0.80)
    if url_count == 1:
        return RoutedTask(
            task=AITask.VIDEO_DESCRIBE,
            route="video.describe",
            confidence=0.85,
        )
    return RoutedTask(
        task=AITask.GENERAL_NL_ANSWER,
        route="general.nl_answer",
        confidence=0.4,
    )


__all__ = ["RoutedTask", "classify"]
