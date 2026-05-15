"""Session lifecycle management for the runtime platform.

A session represents one user's active workspace in a specific channel for a
specific subsystem.  The UNIQUE constraint on (user_id, channel_id, subsystem)
is enforced by the DB — concurrent creation attempts resolve to one winner.

Public surface:
    get_or_create(user_id, guild_id, channel_id, subsystem) → Session
    get(session_id)                                          → Session | None
    touch(session_id)                                        → None
    remove(session_id)                                       → None
    invalidate_subsystem_sessions(guild_id, subsystem)       → None
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

from utils import db

logger = logging.getLogger("bot.runtime.sessions")


@dataclass
class Session:
    session_id: str
    user_id: int
    guild_id: int
    channel_id: int
    subsystem: str
    created_at: datetime
    last_active_at: datetime
    metadata: dict

    @classmethod
    def _from_row(cls, row: dict) -> "Session":
        return cls(
            session_id=str(row["session_id"]),
            user_id=row["user_id"],
            guild_id=row["guild_id"],
            channel_id=row["channel_id"],
            subsystem=row["subsystem"],
            created_at=row["created_at"],
            last_active_at=row["last_active_at"],
            metadata=row.get("metadata") or {},
        )


async def get_or_create(
    user_id: int,
    guild_id: int,
    channel_id: int,
    subsystem: str,
) -> Session:
    """Return the existing session or create a new one for this workspace."""
    row = await db.get_or_create_session(user_id, guild_id, channel_id, subsystem)
    session = Session._from_row(row)
    logger.debug(
        "Session %s for user=%d subsystem=%s in channel=%d",
        session.session_id,
        user_id,
        subsystem,
        channel_id,
    )
    return session


async def get(session_id: str) -> Session | None:
    """Fetch a session by UUID. Returns None if not found."""
    row = await db.get_session(session_id)
    return Session._from_row(row) if row else None


async def touch(session_id: str) -> None:
    """Refresh last_active_at to prevent session GC from expiring it."""
    await db.touch_session(session_id)


async def remove(session_id: str) -> None:
    """Delete a session and all its associated state rows."""
    await db.delete_session(session_id)
    logger.debug("Removed session %s", session_id)


async def invalidate_subsystem_sessions(guild_id: int, subsystem: str) -> None:
    """Remove all sessions for a subsystem across a guild.

    Called when EVT_VISIBILITY_CHANGED fires — affected users must re-open
    their panel to get fresh governance context.
    """
    removed_ids = await db.delete_sessions_for_subsystem(guild_id, subsystem)
    if removed_ids:
        logger.info(
            "Invalidated %d session(s) for subsystem=%r in guild=%d",
            len(removed_ids),
            subsystem,
            guild_id,
        )
