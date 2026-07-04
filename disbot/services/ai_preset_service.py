"""Vetted answer presets — the audited write seam + the runtime lookup.

The "make the bot answer it itself" half of the AI review-log answer loop
(``docs/operations/ai-review-backlog-runbook.md``). An operator stores an exact
vetted answer for a question; the natural-language stage short-circuits to it —
after routing, before the gateway — on an exact normalized-question match,
serving it with **zero model call**.

Two surfaces:

* **Mutations** (``set_preset`` / ``remove_preset``) — the sole writers, audited
  on the canonical ``audit.action_recorded`` seam (a deliberate operator action
  has a real actor). Validate input; raise ``ValueError`` on an empty
  question/answer (defence-in-depth above the operator command).
* **Lookup** (``lookup``) — the runtime hot path. **Fail-safe**: any error
  returns ``None`` so a preset miss/outage can never disturb the AI reply path
  (the model answer simply runs as it would with no preset). Default
  byte-identical when the table is empty.

Keyed on ``utils.ai_text_normalize.normalize_question`` — the same key the triage
script derives — so exact-match only (no fuzzy matching that could mis-serve).
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("bot.services.ai_preset")

# Cap the audit prev/new value snippets — the audit row is metadata, not a
# content store (the full answer lives in ai_answer_presets).
_AUDIT_VALUE_CAP = 200


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _clip(text: str | None) -> str | None:
    if not text:
        return None
    return text[:_AUDIT_VALUE_CAP]


async def lookup(guild_id: int, question: str | None) -> str | None:
    """Return the vetted answer for ``question`` in ``guild_id``, or None.

    Fail-safe — the AI reply path calls this on every answerable message, so any
    error (DB down, bad data) returns None and the normal model path proceeds.
    """
    try:
        from utils.ai_text_normalize import normalize_question
        from utils.db import ai_presets as db

        key = normalize_question(question)
        if not key:
            return None
        return await db.lookup(guild_id, key)
    except Exception:  # noqa: BLE001 — a preset lookup must never break the reply
        logger.debug("ai preset lookup failed for guild=%s", guild_id, exc_info=True)
        return None


async def set_preset(
    guild_id: int,
    question: str,
    answer: str,
    *,
    task: str | None = None,
    source: str | None = None,
    actor_id: int | None,
    actor_type: str = "user",
) -> int:
    """Create or replace the vetted preset for ``question``. Returns the row id.

    The sole preset-write path. Emits ``audit.action_recorded`` (failure-safe;
    the DB write is authoritative regardless of the bus). Raises ``ValueError``
    if ``question`` normalizes to empty or ``answer`` is blank.
    """
    from utils.ai_text_normalize import normalize_question
    from utils.db import ai_presets as db

    key = normalize_question(question)
    clean_answer = (answer or "").strip()
    if not key:
        raise ValueError("question is empty after normalization")
    if not clean_answer:
        raise ValueError("answer is empty")

    prev = await db.get_by_key(guild_id, key)
    preset_id = await db.upsert(
        guild_id=guild_id,
        question_key=key,
        question=question.strip(),
        answer=clean_answer,
        task=task,
        source=source,
        created_by=actor_id,
    )

    from services import audit_events

    await audit_events.emit_audit_action(
        mutation_id=str(uuid.uuid4()),
        subsystem="ai",
        mutation_type="preset_updated" if prev else "preset_created",
        target=f"ai_preset:{key}",
        scope="guild",
        guild_id=guild_id,
        prev_value=_clip(prev["answer"]) if prev else None,
        new_value=_clip(clean_answer),
        actor_id=actor_id,
        actor_type=actor_type,
        occurred_at=_now(),
    )
    return preset_id


async def remove_preset(
    guild_id: int,
    preset_id: int,
    *,
    actor_id: int | None,
    actor_type: str = "user",
) -> bool:
    """Delete one preset. Returns whether a row matched. Audited on a real delete.

    Reversible by design (the Q-0105 "un-promote / delete if unreliable"
    discipline) — un-promoting a wrong preset is one command.
    """
    from utils.db import ai_presets as db

    existing = await db.get_by_id(guild_id, preset_id)
    if existing is None:
        return False
    deleted = await db.delete(guild_id, preset_id)
    if not deleted:
        return False

    from services import audit_events

    await audit_events.emit_audit_action(
        mutation_id=str(uuid.uuid4()),
        subsystem="ai",
        mutation_type="preset_removed",
        target=f"ai_preset:{existing['question_key']}",
        scope="guild",
        guild_id=guild_id,
        prev_value=_clip(existing["answer"]),
        new_value=None,
        actor_id=actor_id,
        actor_type=actor_type,
        occurred_at=_now(),
    )
    return True


async def list_presets(guild_id: int, *, limit: int = 25) -> list[dict[str, Any]]:
    """Recent presets for a guild, newest first (read-only)."""
    from utils.db import ai_presets as db

    return await db.list_for_guild(guild_id, limit=max(1, min(100, int(limit))))


__all__ = ["list_presets", "lookup", "remove_preset", "set_preset"]
