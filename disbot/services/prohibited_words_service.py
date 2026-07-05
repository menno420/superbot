"""Audited writes for the prohibited-word filter + strict-matching toggle.

Single audited seam for the ``prohibited_words`` and ``wordfilter_config``
mutations that the cleanup cog exposes (``!word add/remove``, the add/remove
modals, and the strict-matching toggle). These writes previously went straight
to :mod:`utils.db` from the cog / a view with **zero** ``emit_audit_action``
call (Stage-2 walk bug #6), which also meant a view (``_WordMenuView``) was
writing the DB directly. Routing them through this service satisfies the
mutation-seam + audit contract and removes the view→DB write.

Reads stay in :mod:`utils.db`; the cleanup cog caches the strict flag itself.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from services.audit_events import emit_audit_action
from utils import db


async def add_prohibited_word(
    guild_id: int,
    word: str,
    *,
    actor_id: int | None,
    actor_type: str = "admin",
) -> bool:
    """Add *word* to the guild's prohibited list; audit the add.

    Returns ``True`` if the word was newly added (``False`` if it already
    existed — no audit is emitted for a no-op).
    """
    added = await db.add_prohibited_word(guild_id, word)
    if added:
        await emit_audit_action(
            mutation_id=str(uuid.uuid4()),
            subsystem="cleanup",
            mutation_type="prohibited_word_add",
            target=f"word:{word}",
            scope="guild",
            guild_id=guild_id,
            prev_value=None,
            new_value=word,
            actor_id=actor_id,
            actor_type=actor_type,
            occurred_at=datetime.now(tz=timezone.utc),
        )
    return added


async def remove_prohibited_word(
    guild_id: int,
    word: str,
    *,
    actor_id: int | None,
    actor_type: str = "admin",
) -> bool:
    """Remove *word* from the guild's prohibited list; audit the removal.

    Returns ``True`` if a row was removed (``False`` if the word was not present
    — no audit is emitted for a no-op).
    """
    removed = await db.remove_prohibited_word(guild_id, word)
    if removed:
        await emit_audit_action(
            mutation_id=str(uuid.uuid4()),
            subsystem="cleanup",
            mutation_type="prohibited_word_remove",
            target=f"word:{word}",
            scope="guild",
            guild_id=guild_id,
            prev_value=word,
            new_value=None,
            actor_id=actor_id,
            actor_type=actor_type,
            occurred_at=datetime.now(tz=timezone.utc),
        )
    return removed


async def set_wordfilter_strict(
    guild_id: int,
    strict: bool,
    *,
    actor_id: int | None,
    actor_type: str = "admin",
) -> None:
    """Set the guild's obfuscation-resistant (strict) matching flag; audit it."""
    await db.set_wordfilter_strict(guild_id, strict)
    await emit_audit_action(
        mutation_id=str(uuid.uuid4()),
        subsystem="cleanup",
        mutation_type="wordfilter_strict",
        target=f"guild:{guild_id}",
        scope="guild",
        guild_id=guild_id,
        prev_value=str(not strict),
        new_value=str(strict),
        actor_id=actor_id,
        actor_type=actor_type,
        occurred_at=datetime.now(tz=timezone.utc),
    )
