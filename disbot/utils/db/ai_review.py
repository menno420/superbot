"""CRUD primitives for ``ai_review_log`` (migration 100).

The reviewable AI answer log: "didn't-know" outcomes and user corrections,
with redacted question / answer text. Written exclusively through
``services/ai_review_log_service.py`` (the chokepoint that redacts + caps text
and emits ``ai.review_logged``); read by that service for the ``!aireview``
command and the review-channel poster.

No redaction happens here — text arrives already scrubbed. Pure SQL.
"""

from __future__ import annotations

from typing import Any

from utils.db import pool


async def record_review_entry(
    *,
    guild_id: int,
    channel_id: int,
    user_id: int,
    message_id: int | None,
    reply_message_id: int | None,
    kind: str,
    reason_code: str | None,
    task: str | None,
    route: str | None,
    question: str | None,
    answer: str | None,
    correction: str | None,
    corrected_by: int | None,
    provider: str | None,
    model: str | None,
    expires_at: Any | None = None,
) -> int:
    """Insert one review-log row; return the new ``id``."""
    row = await pool.get().fetchrow(
        """
        INSERT INTO ai_review_log (
            guild_id, channel_id, user_id, message_id, reply_message_id,
            kind, reason_code, task, route, question, answer, correction,
            corrected_by, provider, model, created_at, expires_at
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15,
            NOW(), $16
        )
        RETURNING id
        """,
        guild_id,
        channel_id,
        user_id,
        message_id,
        reply_message_id,
        kind,
        reason_code,
        task,
        route,
        question,
        answer,
        correction,
        corrected_by,
        provider,
        model,
        expires_at,
    )
    return int(row["id"])


async def query_review_entries(
    guild_id: int,
    *,
    kind: str | None = None,
    reviewed: bool | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Return recent review entries for ``guild_id``, newest first."""
    sql = (
        "SELECT id, guild_id, channel_id, user_id, message_id, reply_message_id,"
        " kind, reason_code, task, route, question, answer, correction,"
        " corrected_by, provider, model, reviewed, created_at "
        "FROM ai_review_log WHERE guild_id = $1"
    )
    args: list[Any] = [guild_id]
    if kind is not None:
        args.append(kind)
        sql += f" AND kind = ${len(args)}"
    if reviewed is not None:
        args.append(reviewed)
        sql += f" AND reviewed = ${len(args)}"
    args.append(int(limit))
    sql += f" ORDER BY created_at DESC LIMIT ${len(args)}"
    rows = await pool.get().fetch(sql, *args)
    return [dict(r) for r in rows]


async def get_review_entry(guild_id: int, entry_id: int) -> dict[str, Any] | None:
    """Return one review entry by id (scoped to ``guild_id``), or None."""
    row = await pool.get().fetchrow(
        "SELECT id, guild_id, kind, reason_code, task, route, question, answer,"
        " correction, reviewed, created_at "
        "FROM ai_review_log WHERE guild_id = $1 AND id = $2",
        guild_id,
        entry_id,
    )
    return dict(row) if row is not None else None


async def export_review_entries(
    guild_id: int,
    *,
    kind: str | None = None,
    include_reviewed: bool = True,
    limit: int = 1000,
) -> list[dict[str, Any]]:
    """Return review entries for ``guild_id`` for an operator export.

    Only the triage-relevant columns (no raw channel/message ids) so the dump
    the operator pastes back is lean and focused on the question/answer text +
    the fields a fix needs (``kind`` / ``reason_code`` / ``task`` / ``route``).
    Ordered oldest-first so the export reads chronologically. ``id`` is included
    so an entry can be ``!aireview resolve``d after it is handled.
    """
    sql = (
        "SELECT id, created_at, kind, reason_code, task, route,"
        " question, answer, correction, provider, model, reviewed "
        "FROM ai_review_log WHERE guild_id = $1"
    )
    args: list[Any] = [guild_id]
    if kind is not None:
        args.append(kind)
        sql += f" AND kind = ${len(args)}"
    if not include_reviewed:
        sql += " AND reviewed = FALSE"
    args.append(int(limit))
    sql += f" ORDER BY created_at ASC LIMIT ${len(args)}"
    rows = await pool.get().fetch(sql, *args)
    return [dict(r) for r in rows]


async def mark_reviewed(guild_id: int, entry_id: int) -> bool:
    """Flip ``reviewed`` true for one entry; return whether a row matched."""
    result = await pool.get().execute(
        "UPDATE ai_review_log SET reviewed = TRUE WHERE guild_id = $1 AND id = $2",
        guild_id,
        entry_id,
    )
    # asyncpg returns the command tag, e.g. "UPDATE 1".
    try:
        return int(str(result).split()[-1]) > 0
    except (ValueError, IndexError):
        return False


async def count_unreviewed(guild_id: int, *, kind: str | None = None) -> int:
    """Count unreviewed entries for ``guild_id`` (optionally filtered by kind)."""
    sql = (
        "SELECT COUNT(*) AS n FROM ai_review_log "
        "WHERE guild_id = $1 AND reviewed = FALSE"
    )
    args: list[Any] = [guild_id]
    if kind is not None:
        args.append(kind)
        sql += f" AND kind = ${len(args)}"
    row = await pool.get().fetchrow(sql, *args)
    return int(row["n"]) if row else 0
