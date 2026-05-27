"""AI prompt-composition for BTD6 live state and source freshness.

Sibling to :mod:`services.bot_knowledge_service`: emits
:class:`BotKnowledgeBlock` objects that the central natural-language
stage layers into the instruction stack as untrusted data. The model
sees these blocks as authoritative reference material but never as
instructions (see ``_TASK_CONTRACT`` in
:mod:`services.ai_instruction_service`).

Ownership split (kept deliberately narrow):

* :mod:`services.btd6_ai_context_service` — the read-only **data
  facade**. No AI / instruction-stack concepts.
* This module — **prompt composition only**. Imports the facade,
  emits :class:`BotKnowledgeBlock`. Does not import
  ``btd6_live_query_service`` / ``btd6_fact_store`` /
  ``btd6_source_registry`` / ``btd6_knowledge_api`` directly.

Heuristics deliberately require a BTD6 anchor term to co-occur with a
generic state / freshness term. Bare "event" / "active" / "right now"
/ "leaderboard" / "stale" / "freshness" do **not** route to BTD6 on
their own — too many non-BTD6 false positives (server events, "is the
bot active", XP leaderboard, "is the database stale", …).
"""

from __future__ import annotations

import logging

from services import btd6_ai_context_service
from services.ai_instruction_service import BotKnowledgeBlock

logger = logging.getLogger("bot.services.btd6_ai_knowledge_block")


# ---------------------------------------------------------------------------
# Heuristic vocabularies
# ---------------------------------------------------------------------------


# BTD6 anchor terms — at least one must appear alongside a state /
# freshness term for the block to fire. Single words use whole-word
# matching; multi-word phrases use plain substring.
_BTD6_ANCHORS: frozenset[str] = frozenset(
    {
        "btd6",
        "bloons",
        "bloon",
        "moab",
        "ddt",
        "bfb",
        "zomg",
        "boss",
        "tower",
        "hero",
        "monkey",
        "ninja kiwi",
        "ninjakiwi",
        "odyssey",
        "race",
        "contested territory",
        "ct",
        "chimps",
        "apopalypse",
        "deflation",
        "halfcash",
        "magicmonkeys",
        "primary only",
        "military only",
        "magic only",
        "support only",
    },
)


_STATE_TERMS: tuple[str, ...] = (
    "current",
    "right now",
    "active",
    "running",
    "is on",
    "on right now",
    "what's on",
    "whats on",
    "what's up",
    "any events",
    "any active",
    "any restrictions",
    "banned",
    "limited",
    "restriction",
    "restrictions",
)


_FRESHNESS_TERMS: tuple[str, ...] = (
    "freshness",
    "fresh",
    "stale",
    "outdated",
    "last fetch",
    "last fetched",
    "data fresh",
    "when did you fetch",
    "when was the last",
    "how old",
    "last update",
    "last updated",
)


# ---------------------------------------------------------------------------
# Bounds (mirror bot_knowledge_service patterns)
# ---------------------------------------------------------------------------


_LIVE_STATE_MAX_LINES = 25
_LIVE_STATE_MAX_CHARS = 4000
_SOURCE_STATUS_MAX_LINES = 20
_SOURCE_STATUS_MAX_CHARS = 2000


# Multi-word anchors — must always be matched as substring.
_MULTIWORD_ANCHORS: frozenset[str] = frozenset(a for a in _BTD6_ANCHORS if " " in a)
_SINGLEWORD_ANCHORS: frozenset[str] = frozenset(
    a for a in _BTD6_ANCHORS if " " not in a
)


def _has_btd6_anchor(text: str) -> bool:
    """True when the text co-occurs with a BTD6 anchor.

    Multi-word anchors match as plain substrings; single-word anchors
    match against the whitespace-split word set so ``"boss"`` doesn't
    fire on ``"bossanova"`` and ``"ct"`` doesn't fire on ``"ctrl"``.
    """
    if not text:
        return False
    lowered = text.lower()
    if any(phrase in lowered for phrase in _MULTIWORD_ANCHORS):
        return True
    words = set(_tokenise(lowered))
    return bool(words & _SINGLEWORD_ANCHORS)


def _tokenise(lowered: str) -> list[str]:
    """Cheap word tokeniser: split on whitespace, strip punctuation.

    Kept inline so the heuristic stays single-source-of-truth here
    rather than depending on the resolver's tokenisation rules.
    """
    out: list[str] = []
    buf: list[str] = []
    for ch in lowered:
        if ch.isalnum() or ch == "_":
            buf.append(ch)
        else:
            if buf:
                out.append("".join(buf))
                buf.clear()
    if buf:
        out.append("".join(buf))
    return out


def looks_like_btd6_state_question(text: str) -> bool:
    """True when the message looks like 'what's active in BTD6 right now'.

    Requires (any anchor) AND (any state term). This deliberately
    rejects bare "what event is on the server right now?" — without a
    BTD6 anchor it routes to the general handler.
    """
    if not text:
        return False
    lowered = text.lower()
    if not any(t in lowered for t in _STATE_TERMS):
        return False
    return _has_btd6_anchor(text)


def looks_like_btd6_freshness_question(text: str) -> bool:
    """True when the message asks about BTD6 data staleness / last fetch."""
    if not text:
        return False
    lowered = text.lower()
    if not any(t in lowered for t in _FRESHNESS_TERMS):
        return False
    return _has_btd6_anchor(text)


# ---------------------------------------------------------------------------
# Block composition
# ---------------------------------------------------------------------------


async def _live_state_block() -> BotKnowledgeBlock | None:
    """Compose the ``bot_btd6_live_state`` block.

    Returns ``None`` when both events and restrictions are empty —
    we deliberately do not tell the AI "nothing is active" because a
    failed fetch can present the same way and we'd rather decline to
    enrich than mislead.
    """
    try:
        events = await btd6_ai_context_service.get_current_events()
        restrictions = await btd6_ai_context_service.get_active_restrictions("all")
    except Exception:  # noqa: BLE001 — defensive enrichment
        logger.exception(
            "btd6_ai_knowledge_block_service._live_state_block failed",
            extra={"method": "_live_state_block"},
        )
        return None

    if not events and not restrictions:
        return None

    header = "Currently active in BTD6 (authoritative, from data.ninjakiwi.com):"
    lines: list[str] = [header]
    total_chars = len(header)

    for event in events:
        line = "- " + event.render()
        if (
            len(lines) >= _LIVE_STATE_MAX_LINES
            or total_chars + len(line) + 1 > _LIVE_STATE_MAX_CHARS
        ):
            break
        lines.append(line)
        total_chars += len(line) + 1

    for restriction in restrictions:
        line = "- " + restriction.render()
        if (
            len(lines) >= _LIVE_STATE_MAX_LINES
            or total_chars + len(line) + 1 > _LIVE_STATE_MAX_CHARS
        ):
            break
        lines.append(line)
        total_chars += len(line) + 1

    if len(lines) == 1:  # only the header — no content survived
        return None

    return BotKnowledgeBlock(kind="bot_btd6_live_state", text="\n".join(lines))


async def _source_status_block() -> BotKnowledgeBlock | None:
    """Compose the ``bot_btd6_source_status`` block (public-safe shape)."""
    try:
        statuses = await btd6_ai_context_service.get_source_status(public_safe=True)
    except Exception:  # noqa: BLE001 — defensive enrichment
        logger.exception(
            "btd6_ai_knowledge_block_service._source_status_block failed",
            extra={"method": "_source_status_block"},
        )
        return None
    if not statuses:
        return None

    header = "BTD6 data sources (last fetch / freshness):"
    lines: list[str] = [header]
    total_chars = len(header)
    for status in statuses:
        line = "- " + status.render()
        if (
            len(lines) >= _SOURCE_STATUS_MAX_LINES
            or total_chars + len(line) + 1 > _SOURCE_STATUS_MAX_CHARS
        ):
            break
        lines.append(line)
        total_chars += len(line) + 1

    if len(lines) == 1:
        return None

    return BotKnowledgeBlock(kind="bot_btd6_source_status", text="\n".join(lines))


async def gather_btd6_bot_knowledge_blocks(
    *,
    user_text: str,
) -> tuple[BotKnowledgeBlock, ...]:
    """Emit zero, one, or two BTD6 BotKnowledgeBlocks for ``user_text``.

    Best-effort: any failure logs and returns ``()`` rather than
    propagating into the AI stage.
    """
    blocks: list[BotKnowledgeBlock] = []
    try:
        if looks_like_btd6_state_question(user_text):
            block = await _live_state_block()
            if block is not None:
                blocks.append(block)
        if looks_like_btd6_freshness_question(user_text):
            block = await _source_status_block()
            if block is not None:
                blocks.append(block)
    except Exception:  # noqa: BLE001 — defensive
        logger.exception(
            "gather_btd6_bot_knowledge_blocks failed; returning no blocks",
            extra={"method": "gather_btd6_bot_knowledge_blocks"},
        )
        return ()
    return tuple(blocks)


__all__ = [
    "gather_btd6_bot_knowledge_blocks",
    "looks_like_btd6_freshness_question",
    "looks_like_btd6_state_question",
]
