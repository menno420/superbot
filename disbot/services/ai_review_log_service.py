"""AI answer review log — the reviewable record of what the bot got wrong.

Two kinds of entry, both carrying the redacted question + answer so a human can
actually review them (unlike ``ai_decision_audit``, which stores no text):

* ``unknown``    — the natural-language stage engaged a message but could not
                   answer it properly (provider outage, empty / no-route reply,
                   or a grounding / faithfulness floor). Recorded from the
                   stage's existing audit seams via :func:`record_unknown`.
* ``correction`` — a member 👎-reacted to, or replied-with-a-correction to, one
                   of the bot's AI answers. Recorded by ``cogs/ai_review_cog.py``
                   via :func:`record_correction`.

Both writers redact text through the bot's outbound scrubber, cap its length,
persist a row via ``utils/db/ai_review.py``, and emit ``ai.review_logged`` so the
cog can post it to the configured review channel. **Every public call is
fail-safe** — a logging failure must never disturb the AI reply path or a user's
reaction / reply.

Correction matching uses a bounded in-memory registry (:func:`remember_answer` /
:func:`lookup_answer`): when the stage sends an AI answer it remembers the reply
message id → (question, answer, metadata); when a member reacts / replies to that
message the cog recovers the original Q&A. Process-local + best-effort by design
(ADR-001 no external store, ADR-002 not restart-safe) — a correction to an
answer sent before the last restart is simply not enriched.
"""

from __future__ import annotations

import logging
import time
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger("bot.services.ai_review_log")

EVT_AI_REVIEW_LOGGED = "ai.review_logged"

# Entry kinds (the `kind` column).
KIND_UNKNOWN = "unknown"
KIND_CORRECTION = "correction"

# Correction signals (stored in `reason_code` for kind='correction').
SIGNAL_REACTION = "reaction"
SIGNAL_REPLY = "reply"

# Stored-text cap — generous enough to review, bounded so a pasted wall of text
# can't bloat a row. Discord embed fields cap at 1024; the embed truncates
# further at render time.
_TEXT_CAP = 2000

# Retention horizon written onto each row. Metadata for now (a physical purge
# job is a documented follow-up); guild teardown deletes rows immediately.
_RETENTION_DAYS = 90

# Answer-registry bounds (correction matching).
_REGISTRY_MAX = 1000
_REGISTRY_TTL_SECONDS = 60 * 60  # corrections land soon after the answer


@dataclass(frozen=True)
class AnswerContext:
    """A remembered AI answer, recovered when a user corrects it."""

    guild_id: int
    channel_id: int
    user_id: int
    message_id: int | None  # the original question message
    question: str
    answer: str
    task: str | None
    route: str | None
    provider: str | None
    model: str | None


# reply_message_id -> (monotonic_ts, AnswerContext, flagger_user_ids)
_ANSWER_REGISTRY: OrderedDict[int, tuple[float, AnswerContext, set[int]]] = (
    OrderedDict()
)


# ---------------------------------------------------------------------------
# Text handling
# ---------------------------------------------------------------------------


def _redact(text: str | None) -> str | None:
    """Scrub *text* through the outbound redactor and cap it; None if empty."""
    if not text:
        return None
    try:
        from core.runtime.ai.redaction import redact_text

        scrubbed = redact_text(text).value
    except Exception:  # noqa: BLE001 — redaction must never block logging
        scrubbed = text
    scrubbed = scrubbed.strip()
    if not scrubbed:
        return None
    return scrubbed[:_TEXT_CAP]


def _expires_at() -> datetime:
    return datetime.now(tz=timezone.utc) + timedelta(days=_RETENTION_DAYS)


# ---------------------------------------------------------------------------
# Answer registry (correction matching)
# ---------------------------------------------------------------------------


def _prune_registry() -> None:
    cutoff = time.monotonic() - _REGISTRY_TTL_SECONDS
    stale = [key for key, (ts, _ctx, _f) in _ANSWER_REGISTRY.items() if ts < cutoff]
    for key in stale:
        _ANSWER_REGISTRY.pop(key, None)
    while len(_ANSWER_REGISTRY) > _REGISTRY_MAX:
        _ANSWER_REGISTRY.popitem(last=False)


def remember_answer(
    reply_message_id: int,
    *,
    guild_id: int,
    channel_id: int,
    user_id: int,
    message_id: int | None,
    question: str | None,
    answer: str | None,
    task: str | None,
    route: str | None,
    provider: str | None,
    model: str | None,
) -> None:
    """Remember a freshly-sent AI answer so a later correction can recover it.

    Best-effort + fail-safe: never raises into the send path.
    """
    try:
        ctx = AnswerContext(
            guild_id=guild_id,
            channel_id=channel_id,
            user_id=user_id,
            message_id=message_id,
            question=_redact(question) or "",
            answer=_redact(answer) or "",
            task=task,
            route=route,
            provider=provider,
            model=model,
        )
        _ANSWER_REGISTRY[reply_message_id] = (time.monotonic(), ctx, set())
        _ANSWER_REGISTRY.move_to_end(reply_message_id)
        _prune_registry()
    except Exception:  # noqa: BLE001 — remembering must never disturb the reply
        logger.debug(
            "remember_answer failed for msg=%s",
            reply_message_id,
            exc_info=True,
        )


def lookup_answer(reply_message_id: int) -> AnswerContext | None:
    """Recover a remembered AI answer by its Discord message id, or None."""
    entry = _ANSWER_REGISTRY.get(reply_message_id)
    if entry is None:
        return None
    ts, ctx, _flaggers = entry
    if ts < time.monotonic() - _REGISTRY_TTL_SECONDS:
        _ANSWER_REGISTRY.pop(reply_message_id, None)
        return None
    return ctx


def already_flagged(reply_message_id: int, user_id: int) -> bool:
    """True if *user_id* has already corrected this answer (dedup signal)."""
    entry = _ANSWER_REGISTRY.get(reply_message_id)
    return entry is not None and user_id in entry[2]


def _note_flagger(reply_message_id: int, user_id: int) -> None:
    entry = _ANSWER_REGISTRY.get(reply_message_id)
    if entry is not None:
        entry[2].add(user_id)


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------


async def record_unknown(
    *,
    guild_id: int,
    channel_id: int,
    user_id: int,
    message_id: int | None,
    task: str | None,
    route: str | None,
    reason_code: str,
    question: str | None,
    answer: str | None,
    provider: str | None = None,
    model: str | None = None,
) -> int | None:
    """Log a "didn't-know" outcome. Fail-safe — returns the row id or None."""
    return await _record(
        guild_id=guild_id,
        channel_id=channel_id,
        user_id=user_id,
        message_id=message_id,
        reply_message_id=None,
        kind=KIND_UNKNOWN,
        reason_code=reason_code,
        task=task,
        route=route,
        question=question,
        answer=answer,
        correction=None,
        corrected_by=None,
        provider=provider,
        model=model,
    )


async def record_correction(
    *,
    guild_id: int,
    channel_id: int,
    user_id: int,
    message_id: int | None,
    reply_message_id: int | None,
    corrected_by: int,
    signal: str,
    question: str | None,
    answer: str | None,
    correction: str | None,
    task: str | None = None,
    route: str | None = None,
    provider: str | None = None,
    model: str | None = None,
) -> int | None:
    """Log a user correction of an AI answer. Fail-safe — row id or None."""
    entry_id = await _record(
        guild_id=guild_id,
        channel_id=channel_id,
        user_id=user_id,
        message_id=message_id,
        reply_message_id=reply_message_id,
        kind=KIND_CORRECTION,
        reason_code=signal,
        task=task,
        route=route,
        question=question,
        answer=answer,
        correction=correction,
        corrected_by=corrected_by,
        provider=provider,
        model=model,
    )
    if entry_id is not None and reply_message_id is not None:
        _note_flagger(reply_message_id, corrected_by)
    return entry_id


async def _record(**fields: Any) -> int | None:
    try:
        from utils.db import ai_review as ai_review_db

        redacted = dict(fields)
        redacted["question"] = _redact(fields.get("question"))
        redacted["answer"] = _redact(fields.get("answer"))
        redacted["correction"] = _redact(fields.get("correction"))
        entry_id = await ai_review_db.record_review_entry(
            expires_at=_expires_at(),
            **redacted,
        )
    except Exception:  # noqa: BLE001 — logging must never disturb the AI path
        logger.warning(
            "ai_review_log: failed to record %s entry for guild=%s",
            fields.get("kind"),
            fields.get("guild_id"),
            exc_info=True,
        )
        return None
    await _emit(entry_id, redacted)
    return entry_id


async def _emit(entry_id: int, fields: dict[str, Any]) -> None:
    try:
        from core.events import bus

        await bus.emit(
            EVT_AI_REVIEW_LOGGED,
            entry_id=entry_id,
            guild_id=fields["guild_id"],
            channel_id=fields["channel_id"],
            user_id=fields["user_id"],
            kind=fields["kind"],
            reason_code=fields.get("reason_code"),
            task=fields.get("task"),
            route=fields.get("route"),
            question=fields.get("question"),
            answer=fields.get("answer"),
            correction=fields.get("correction"),
            corrected_by=fields.get("corrected_by"),
            provider=fields.get("provider"),
            model=fields.get("model"),
        )
    except Exception:  # noqa: BLE001 — emit is best-effort
        logger.debug(
            "ai.review_logged emit failed for id=%s",
            entry_id,
            exc_info=True,
        )


# ---------------------------------------------------------------------------
# Readers
# ---------------------------------------------------------------------------


async def query(
    guild_id: int,
    *,
    kind: str | None = None,
    reviewed: bool | None = None,
    limit: int = 25,
) -> list[dict[str, Any]]:
    """Recent review entries for ``guild_id``, newest first (read-only)."""
    from utils.db import ai_review as ai_review_db

    return await ai_review_db.query_review_entries(
        guild_id,
        kind=kind,
        reviewed=reviewed,
        limit=max(1, min(100, int(limit))),
    )


async def get_entry(guild_id: int, entry_id: int) -> dict[str, Any] | None:
    """Return one review entry by id (read-only), or None. Fail-safe."""
    try:
        from utils.db import ai_review as ai_review_db

        return await ai_review_db.get_review_entry(guild_id, entry_id)
    except Exception:  # noqa: BLE001
        logger.warning("ai_review_log: get_entry failed", exc_info=True)
        return None


async def export(
    guild_id: int,
    *,
    kind: str | None = None,
    include_reviewed: bool = True,
    limit: int = 1000,
) -> list[dict[str, Any]]:
    """Triage-ready export of a guild's review entries (read-only).

    Returns plain JSON-serializable dicts (``created_at`` as an ISO string) for
    the operator ``!aireview export`` dump → ``scripts/ai_review_triage.py``.
    Text is already redacted at write time, so the export carries no un-scrubbed
    content. Newest handling first happens downstream; rows arrive oldest-first.
    """
    from utils.db import ai_review as ai_review_db

    rows = await ai_review_db.export_review_entries(
        guild_id,
        kind=kind,
        include_reviewed=include_reviewed,
        limit=max(1, min(5000, int(limit))),
    )
    out: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        created = item.get("created_at")
        if isinstance(created, datetime):
            item["created_at"] = created.isoformat()
        out.append(item)
    return out


async def mark_reviewed(guild_id: int, entry_id: int) -> bool:
    """Mark one entry reviewed; True if a row matched. Fail-safe."""
    try:
        from utils.db import ai_review as ai_review_db

        return await ai_review_db.mark_reviewed(guild_id, entry_id)
    except Exception:  # noqa: BLE001
        logger.warning("ai_review_log: mark_reviewed failed", exc_info=True)
        return False


async def count_unreviewed(guild_id: int, *, kind: str | None = None) -> int:
    """Count unreviewed entries (optionally by kind); 0 on any failure."""
    try:
        from utils.db import ai_review as ai_review_db

        return await ai_review_db.count_unreviewed(guild_id, kind=kind)
    except Exception:  # noqa: BLE001
        return 0


# ---------------------------------------------------------------------------
# Channel pointer (the typed owner of AI_REVIEW_CHANNEL)
# ---------------------------------------------------------------------------


async def set_review_channel(guild_id: int, channel_id: int | None) -> None:
    """Set (or clear, when ``channel_id`` is None) the guild's review channel.

    The single writer for ``AI_REVIEW_CHANNEL`` — this service is the typed owner
    of that per-guild pointer (allowlisted in
    ``tests/unit/invariants/test_no_direct_settings_keys_writes.py``), so routing
    the write here keeps the bare-``set_setting`` invariant intact. Cogs call
    this; channel *resolution* for display goes through
    ``core.runtime.guild_resources.resolve_settings_channel``.
    """
    from utils import db
    from utils.settings_keys import ai as ai_keys

    await db.set_setting(
        guild_id,
        ai_keys.AI_REVIEW_CHANNEL,
        str(channel_id) if channel_id is not None else "",
    )


def _reset_for_tests() -> None:
    _ANSWER_REGISTRY.clear()


__all__ = [
    "EVT_AI_REVIEW_LOGGED",
    "KIND_CORRECTION",
    "KIND_UNKNOWN",
    "SIGNAL_REACTION",
    "SIGNAL_REPLY",
    "AnswerContext",
    "already_flagged",
    "count_unreviewed",
    "export",
    "get_entry",
    "lookup_answer",
    "mark_reviewed",
    "query",
    "record_correction",
    "record_unknown",
    "remember_answer",
    "set_review_channel",
]
