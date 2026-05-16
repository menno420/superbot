"""Runtime session + state CRUD + per-guild housekeeping.

Sessions are one row per (user, channel, subsystem) enforced by a
DB-level UNIQUE constraint; state is an unbounded KV bag keyed by
(session_id, key).  The codec module owns the legacy-decode shim
referenced from session-state reads.
"""

from __future__ import annotations

from utils.db import pool
from utils.db.codec import maybe_decode_legacy

# ---------------------------------------------------------------------------
# Session row CRUD
# ---------------------------------------------------------------------------


async def get_or_create_session(
    user_id: int,
    guild_id: int,
    channel_id: int,
    subsystem: str,
) -> dict:
    """Return existing session or create a new one (upsert on unique key).

    Returns the session row as a dict with keys:
    session_id, user_id, guild_id, channel_id, subsystem,
    created_at, last_active_at, metadata.
    """
    row = await pool.get().fetchrow(
        """INSERT INTO runtime_sessions
               (user_id, guild_id, channel_id, subsystem)
           VALUES ($1, $2, $3, $4)
           ON CONFLICT (user_id, channel_id, subsystem) DO UPDATE
               SET last_active_at = NOW()
           RETURNING *""",
        user_id,
        guild_id,
        channel_id,
        subsystem,
    )
    return dict(row)


async def touch_session(session_id: str) -> None:
    """Update last_active_at for an existing session."""
    await pool.get().execute(
        "UPDATE runtime_sessions SET last_active_at = NOW() WHERE session_id = $1",
        session_id,
    )


async def get_session(session_id: str) -> dict | None:
    row = await pool.get().fetchrow(
        "SELECT * FROM runtime_sessions WHERE session_id = $1",
        session_id,
    )
    return dict(row) if row else None


async def delete_session(session_id: str) -> None:
    """Delete a session row; CASCADE drops its state."""
    await pool.get().execute(
        "DELETE FROM runtime_sessions WHERE session_id = $1",
        session_id,
    )


async def delete_sessions_for_subsystem(
    guild_id: int,
    subsystem: str,
) -> list[str]:
    """Delete every session for a subsystem in a guild; return removed IDs."""
    rows = await pool.get().fetch(
        """DELETE FROM runtime_sessions
           WHERE guild_id = $1 AND subsystem = $2
           RETURNING session_id::text""",
        guild_id,
        subsystem,
    )
    return [r["session_id"] for r in rows]


async def delete_sessions_for_scope(
    guild_id: int,
    subsystem: str,
    channel_id: int | None = None,
) -> list[str]:
    """Scope-aware session invalidation.

    A channel-scoped governance change should only invalidate sessions
    in that channel, not guild-wide.  Falls back to guild-wide deletion
    when ``channel_id`` is None.
    """
    if channel_id is not None:
        rows = await pool.get().fetch(
            """DELETE FROM runtime_sessions
               WHERE guild_id = $1 AND subsystem = $2 AND channel_id = $3
               RETURNING session_id::text""",
            guild_id,
            subsystem,
            channel_id,
        )
    else:
        rows = await pool.get().fetch(
            """DELETE FROM runtime_sessions
               WHERE guild_id = $1 AND subsystem = $2
               RETURNING session_id::text""",
            guild_id,
            subsystem,
        )
    return [r["session_id"] for r in rows]


# ---------------------------------------------------------------------------
# runtime_session_state KV
# ---------------------------------------------------------------------------


async def get_session_state(session_id: str, key: str) -> object | None:
    """Read one typed value, returning the Python object or None."""
    row = await pool.get().fetchrow(
        "SELECT value FROM runtime_session_state WHERE session_id = $1 AND key = $2",
        session_id,
        key,
    )
    return maybe_decode_legacy(row["value"]) if row else None


async def set_session_state(session_id: str, key: str, value: object) -> None:
    """Upsert one typed value."""
    await pool.get().execute(
        """INSERT INTO runtime_session_state (session_id, key, value)
           VALUES ($1, $2, $3)
           ON CONFLICT (session_id, key) DO UPDATE SET value = EXCLUDED.value""",
        session_id,
        key,
        value,  # asyncpg JSONB codec handles encoding via init_connection
    )


async def set_session_state_many(
    session_id: str,
    items: dict[str, object],
) -> None:
    """Upsert several keys atomically for one session.

    Empty ``items`` is a no-op.  The transaction prevents a network
    hiccup mid-batch from leaving the session in a partial state.
    """
    if not items:
        return
    p = pool.get()
    async with p.acquire() as conn, conn.transaction():
        for key, value in items.items():
            await conn.execute(
                """INSERT INTO runtime_session_state (session_id, key, value)
                   VALUES ($1, $2, $3)
                   ON CONFLICT (session_id, key) DO UPDATE
                     SET value = EXCLUDED.value""",
                session_id,
                key,
                value,
            )


async def delete_session_state(session_id: str, key: str) -> None:
    await pool.get().execute(
        "DELETE FROM runtime_session_state WHERE session_id = $1 AND key = $2",
        session_id,
        key,
    )


async def get_all_session_state(session_id: str) -> dict:
    rows = await pool.get().fetch(
        "SELECT key, value FROM runtime_session_state WHERE session_id = $1",
        session_id,
    )
    return {r["key"]: maybe_decode_legacy(r["value"]) for r in rows}


async def delete_guild_session_state(guild_id: int) -> None:
    """Purge every session-state row for a guild (cache invalidation)."""
    await pool.get().execute(
        """DELETE FROM runtime_session_state
           WHERE session_id IN (
               SELECT session_id FROM runtime_sessions WHERE guild_id = $1
           )""",
        guild_id,
    )


# ---------------------------------------------------------------------------
# GC / observability
# ---------------------------------------------------------------------------


async def delete_expired_sessions(cutoff_epoch: float) -> list[str]:
    """Delete expired sessions and return the session_ids that were deleted.

    PR N1: the GC sweep now propagates the removed IDs to per-session
    cleanup hooks (currently ``navigation_stack.forget``) so process-local
    lock dicts cannot grow unbounded.  Callers wanting a count can use
    ``len(...)`` on the return value.
    """
    from datetime import datetime, timezone

    cutoff_dt = datetime.fromtimestamp(cutoff_epoch, tz=timezone.utc)
    rows = await pool.get().fetch(
        """DELETE FROM runtime_sessions
            WHERE last_active_at < $1
           RETURNING session_id::text""",
        cutoff_dt,
    )
    return [r["session_id"] for r in rows]


async def delete_sessions_for_guild(guild_id: int) -> list[str]:
    """Delete every runtime session for a guild; return the IDs.

    Mirrors ``delete_sessions_for_subsystem`` /
    ``delete_sessions_for_scope`` so guild-removal teardown
    (:mod:`guild_lifecycle`) has the same shape as the other
    delete-and-return-ids helpers.  The returned IDs feed
    ``navigation_stack.forget`` so in-process per-session state is
    purged in lockstep with the DB rows.
    """
    rows = await pool.get().fetch(
        """DELETE FROM runtime_sessions
            WHERE guild_id = $1
           RETURNING session_id::text""",
        guild_id,
    )
    return [r["session_id"] for r in rows]


async def count_active_sessions() -> int:
    """Return the current number of runtime sessions in the DB."""
    row = await pool.get().fetchrow("SELECT COUNT(*) AS n FROM runtime_sessions")
    return int(row["n"]) if row else 0


# ---------------------------------------------------------------------------
# Back-compat private alias — older code imported `db._maybe_decode_legacy`
# directly. Re-export so the symbol stays reachable until S6 retires it.
# ---------------------------------------------------------------------------

_maybe_decode_legacy = maybe_decode_legacy
