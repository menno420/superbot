"""panel_anchors table CRUD.

Anchors are one row per (user, channel, subsystem); ``is_stale`` is set
when a Discord message has been deleted and the GC sweeps deletes the
row later.  Used by ``core.runtime.message_anchor_manager``.
"""

from __future__ import annotations

from utils.db import pool


async def get_panel_anchor(
    user_id: int,
    channel_id: int,
    subsystem: str,
) -> dict | None:
    """Active anchor for (user, channel, subsystem), or None."""
    row = await pool.get().fetchrow(
        """SELECT * FROM panel_anchors
           WHERE user_id = $1 AND channel_id = $2 AND subsystem = $3
             AND NOT is_stale""",
        user_id,
        channel_id,
        subsystem,
    )
    return dict(row) if row else None


async def upsert_panel_anchor(
    user_id: int,
    guild_id: int,
    channel_id: int,
    subsystem: str,
    message_id: int,
) -> dict:
    """Create or replace the anchor for (user, channel, subsystem).

    Replaces the message_id when the user opens a new panel in the same
    channel (old message was deleted or unreachable).
    """
    row = await pool.get().fetchrow(
        """INSERT INTO panel_anchors
               (user_id, guild_id, channel_id, subsystem, message_id)
           VALUES ($1, $2, $3, $4, $5)
           ON CONFLICT (user_id, channel_id, subsystem) DO UPDATE
               SET message_id      = EXCLUDED.message_id,
                   is_stale        = FALSE,
                   last_updated_at = NOW()
           RETURNING *""",
        user_id,
        guild_id,
        channel_id,
        subsystem,
        message_id,
    )
    return dict(row)


async def count_active_anchors_by_subsystem() -> list[dict]:
    """Active (non-stale) anchor counts per subsystem, busiest first.

    The ``!platform anchors`` diagnostic read model (RS08 — the SQL used
    to live inline in ``cogs/diagnostic/_platform_embeds.py``). Rows are
    ``[{"subsystem", "n"}, ...]``.
    """
    rows = await pool.get().fetch(
        "SELECT subsystem, COUNT(*) AS n FROM panel_anchors "
        "WHERE NOT is_stale GROUP BY subsystem ORDER BY n DESC",
    )
    return [dict(r) for r in rows]


async def get_panel_anchor_by_message(message_id: int) -> dict | None:
    row = await pool.get().fetchrow(
        "SELECT * FROM panel_anchors WHERE message_id = $1 AND NOT is_stale",
        message_id,
    )
    return dict(row) if row else None


async def mark_panel_anchor_stale(anchor_id: str) -> None:
    """Mark an anchor stale after its Discord message was deleted."""
    await pool.get().execute(
        "UPDATE panel_anchors SET is_stale = TRUE WHERE anchor_id = $1",
        anchor_id,
    )


async def mark_anchors_stale_for_subsystem(subsystem: str) -> int:
    """Mark every active anchor for *subsystem* stale; return rows touched.

    Used by the identity-contract self-heal path (PR I1b) to evacuate
    orphan anchor rows whose subsystem string no longer matches the
    SUBSYSTEMS registry — typically because a cog was removed or
    renamed.  The session_gc loop sweeps stale rows on its next pass.
    """
    result = await pool.get().execute(
        """UPDATE panel_anchors
              SET is_stale = TRUE
            WHERE subsystem = $1 AND NOT is_stale""",
        subsystem,
    )
    try:
        return int(result.split()[-1])
    except (IndexError, ValueError):
        return 0


async def get_all_active_panel_anchors() -> list[dict]:
    """All non-stale anchors, ordered by last_updated_at (for restart recovery)."""
    rows = await pool.get().fetch(
        "SELECT * FROM panel_anchors WHERE NOT is_stale ORDER BY last_updated_at DESC",
    )
    return [dict(r) for r in rows]


async def delete_stale_panel_anchors() -> int:
    """Delete anchors marked is_stale=TRUE; return count removed."""
    result = await pool.get().execute(
        "DELETE FROM panel_anchors WHERE is_stale = TRUE",
    )
    try:
        return int(result.split()[-1])
    except (IndexError, ValueError):
        return 0


async def delete_guild_panel_anchors(guild_id: int) -> int:
    """Delete every panel anchor for a guild; return count removed.

    Called from ``guild_lifecycle.teardown()`` so departed guilds leave
    no orphan rows.  Index on (guild_id, subsystem) supports this.
    """
    result = await pool.get().execute(
        "DELETE FROM panel_anchors WHERE guild_id = $1",
        guild_id,
    )
    try:
        return int(result.split()[-1])
    except (IndexError, ValueError):
        return 0


async def get_user_subsystem_anchors(
    user_id: int,
    guild_id: int,
    subsystem: str,
) -> list[dict]:
    """All active panel anchors for a user+guild+subsystem combination."""
    rows = await pool.get().fetch(
        """
        SELECT anchor_id, user_id, guild_id, channel_id, message_id, subsystem
        FROM panel_anchors
        WHERE user_id = $1 AND guild_id = $2 AND subsystem = $3
          AND NOT is_stale
        """,
        user_id,
        guild_id,
        subsystem,
    )
    return [dict(r) for r in rows]
