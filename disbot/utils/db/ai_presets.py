"""CRUD primitives for ``ai_answer_presets`` (migration 102).

Operator-authored vetted answers the bot serves with **zero model call** on an
exact normalized-question match. Written exclusively through
``services/ai_preset_service.py`` (the audited chokepoint); the hot-path
:func:`lookup` is called by the natural-language stage short-circuit.

No redaction / normalization happens here — the question key arrives already
normalized (``utils.ai_text_normalize``). Pure SQL.
"""

from __future__ import annotations

from typing import Any

from utils.db import pool


async def lookup(guild_id: int, question_key: str) -> str | None:
    """Return the enabled vetted answer for ``question_key``, or None.

    The runtime hot path — one indexed exact-match read on
    ``(guild_id, question_key)``. Disabled presets never match.
    """
    row = await pool.get().fetchrow(
        "SELECT answer FROM ai_answer_presets "
        "WHERE guild_id = $1 AND question_key = $2 AND enabled = TRUE",
        guild_id,
        question_key,
    )
    return str(row["answer"]) if row is not None else None


async def get_by_key(guild_id: int, question_key: str) -> dict[str, Any] | None:
    """Return the full preset row for a key (any enabled state), or None."""
    row = await pool.get().fetchrow(
        "SELECT id, guild_id, question_key, question, answer, task, source,"
        " enabled, created_by, created_at, updated_at "
        "FROM ai_answer_presets WHERE guild_id = $1 AND question_key = $2",
        guild_id,
        question_key,
    )
    return dict(row) if row is not None else None


async def get_by_id(guild_id: int, preset_id: int) -> dict[str, Any] | None:
    """Return the full preset row by id, or None."""
    row = await pool.get().fetchrow(
        "SELECT id, guild_id, question_key, question, answer, task, source,"
        " enabled, created_by, created_at, updated_at "
        "FROM ai_answer_presets WHERE guild_id = $1 AND id = $2",
        guild_id,
        preset_id,
    )
    return dict(row) if row is not None else None


async def upsert(
    *,
    guild_id: int,
    question_key: str,
    question: str,
    answer: str,
    task: str | None,
    source: str | None,
    created_by: int | None,
) -> int:
    """Insert a preset, or update the answer if the key already exists.

    Re-authoring the same normalized question replaces the stored answer (and
    re-enables it), keeping the original ``created_by`` / ``created_at``. Returns
    the row id.
    """
    row = await pool.get().fetchrow(
        """
        INSERT INTO ai_answer_presets (
            guild_id, question_key, question, answer, task, source, created_by
        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT (guild_id, question_key) DO UPDATE SET
            question   = EXCLUDED.question,
            answer     = EXCLUDED.answer,
            task       = EXCLUDED.task,
            source     = EXCLUDED.source,
            enabled    = TRUE,
            updated_at = NOW()
        RETURNING id
        """,
        guild_id,
        question_key,
        question,
        answer,
        task,
        source,
        created_by,
    )
    return int(row["id"])


async def list_for_guild(
    guild_id: int,
    *,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Return a guild's presets, newest first."""
    rows = await pool.get().fetch(
        "SELECT id, question_key, question, answer, task, source, enabled,"
        " created_by, created_at, updated_at "
        "FROM ai_answer_presets WHERE guild_id = $1 "
        "ORDER BY created_at DESC LIMIT $2",
        guild_id,
        int(limit),
    )
    return [dict(r) for r in rows]


async def delete(guild_id: int, preset_id: int) -> bool:
    """Delete one preset; return whether a row matched."""
    result = await pool.get().execute(
        "DELETE FROM ai_answer_presets WHERE guild_id = $1 AND id = $2",
        guild_id,
        preset_id,
    )
    try:
        return int(str(result).split()[-1]) > 0
    except (ValueError, IndexError):
        return False
