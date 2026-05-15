"""Typed key-value session state store.

State is persisted to runtime_session_state in PostgreSQL and is keyed by
(session_id, key).  Values are any JSON-serialisable Python object.

Public surface:
    get(session_id, key)               → object | None
    set(session_id, key, value)        → None
    delete(session_id, key)            → None
    get_all(session_id)                → dict
    invalidate_guild_state(guild_id)   → None
"""

from __future__ import annotations

import logging

from utils import db

logger = logging.getLogger("bot.runtime.state")


async def get(session_id: str, key: str) -> object | None:
    """Read one state value for a session.  Returns None if the key is absent."""
    return await db.get_session_state(session_id, key)


async def set(session_id: str, key: str, value: object) -> None:  # noqa: A001
    """Write (upsert) one state value for a session."""
    await db.set_session_state(session_id, key, value)


async def delete(session_id: str, key: str) -> None:
    """Remove one state key for a session."""
    await db.delete_session_state(session_id, key)


async def get_all(session_id: str) -> dict:
    """Return all key-value state for a session."""
    return await db.get_all_session_state(session_id)


async def invalidate_guild_state(guild_id: int) -> None:
    """Purge all session state for every session in a guild.

    Called when EVT_CACHE_INVALIDATED fires so that stale governance-derived
    state (e.g., cached capability lists) is dropped before the next access.
    """
    await db.delete_guild_session_state(guild_id)
    logger.info("Purged session state for all sessions in guild=%d", guild_id)
