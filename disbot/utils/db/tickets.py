"""Support-ticket CRUD — the ``ticket`` subsystem's data primitives.

Migration 098 (``ticket_config`` / ``tickets`` / ``ticket_blacklist``).

Conn-aware (Q-0071 precedent): every write primitive takes an optional
``conn`` so :mod:`services.ticket_mutation` can compose reads + writes in one
transaction.  All access goes through :mod:`utils.db.pool` — this module never
touches the global pool directly.

Function names are ``ticket_*``-prefixed because ``utils.db`` re-exports every
submodule symbol flat, so names must be unique across the package.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from utils.db import pool

if TYPE_CHECKING:
    import asyncpg

# --------------------------------------------------------------------------- #
# Config (one row per guild)
# --------------------------------------------------------------------------- #


async def ticket_get_config(
    guild_id: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> dict[str, Any] | None:
    """Return the guild's ticket config row, or ``None`` if never configured."""
    return await pool.fetchone(
        "SELECT guild_id, enabled, staff_role_id, category_id, log_channel_id, "
        "       panel_channel_id, panel_message_id, max_open_per_user, "
        "       ping_staff_on_open, updated_at "
        "FROM ticket_config WHERE guild_id = $1",
        (guild_id,),
        conn=conn,
    )


async def ticket_upsert_config(
    guild_id: int,
    *,
    enabled: bool | None = None,
    staff_role_id: int | None = None,
    category_id: int | None = None,
    log_channel_id: int | None = None,
    panel_channel_id: int | None = None,
    panel_message_id: int | None = None,
    max_open_per_user: int | None = None,
    ping_staff_on_open: bool | None = None,
    updated_at: int = 0,
    conn: asyncpg.Connection | None = None,
) -> None:
    """Insert or update the guild's ticket config.

    Only the fields passed (non-``None``) are changed; on an existing row the
    rest are preserved via ``COALESCE(EXCLUDED.col, ticket_config.col)``.  A
    brand-new row falls back to the column defaults for unset fields.
    """
    await pool.execute(
        "INSERT INTO ticket_config ("
        "    guild_id, enabled, staff_role_id, category_id, log_channel_id, "
        "    panel_channel_id, panel_message_id, max_open_per_user, "
        "    ping_staff_on_open, updated_at"
        ") VALUES ("
        "    $1, COALESCE($2, TRUE), $3, $4, $5, $6, $7, "
        "    COALESCE($8, 1), COALESCE($9, TRUE), $10"
        ") ON CONFLICT (guild_id) DO UPDATE SET "
        "    enabled = COALESCE($2, ticket_config.enabled), "
        "    staff_role_id = COALESCE($3, ticket_config.staff_role_id), "
        "    category_id = COALESCE($4, ticket_config.category_id), "
        "    log_channel_id = COALESCE($5, ticket_config.log_channel_id), "
        "    panel_channel_id = COALESCE($6, ticket_config.panel_channel_id), "
        "    panel_message_id = COALESCE($7, ticket_config.panel_message_id), "
        "    max_open_per_user = COALESCE($8, ticket_config.max_open_per_user), "
        "    ping_staff_on_open = COALESCE($9, ticket_config.ping_staff_on_open), "
        "    updated_at = $10",
        (
            guild_id,
            enabled,
            staff_role_id,
            category_id,
            log_channel_id,
            panel_channel_id,
            panel_message_id,
            max_open_per_user,
            ping_staff_on_open,
            updated_at,
        ),
        conn=conn,
    )


# --------------------------------------------------------------------------- #
# Tickets
# --------------------------------------------------------------------------- #


async def ticket_create(
    guild_id: int,
    channel_id: int,
    opener_id: int,
    subject: str,
    *,
    source: str = "command",
    created_at: int,
    conn: asyncpg.Connection | None = None,
) -> int:
    """Insert a ticket row; return its generated id (0 on failure)."""
    row = await pool.fetchone(
        "INSERT INTO tickets ("
        "    guild_id, channel_id, opener_id, subject, status, source, created_at"
        ") VALUES ($1, $2, $3, $4, 'open', $5, $6) RETURNING id",
        (guild_id, channel_id, opener_id, subject, source, created_at),
        conn=conn,
    )
    return int(row["id"]) if row else 0


async def ticket_get(
    ticket_id: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> dict[str, Any] | None:
    """Fetch a single ticket by id."""
    return await pool.fetchone(
        "SELECT * FROM tickets WHERE id = $1",
        (ticket_id,),
        conn=conn,
    )


async def ticket_get_by_channel(
    channel_id: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> dict[str, Any] | None:
    """Fetch the ticket bound to ``channel_id`` (the most recent if reused)."""
    return await pool.fetchone(
        "SELECT * FROM tickets WHERE channel_id = $1 ORDER BY id DESC LIMIT 1",
        (channel_id,),
        conn=conn,
    )


async def ticket_count_open_for_user(
    guild_id: int,
    opener_id: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> int:
    """Number of currently-open tickets ``opener_id`` holds in the guild."""
    row = await pool.fetchone(
        "SELECT COUNT(*) AS n FROM tickets "
        "WHERE guild_id = $1 AND opener_id = $2 AND status = 'open'",
        (guild_id, opener_id),
        conn=conn,
    )
    return int(row["n"]) if row else 0


async def ticket_list_for_user(
    guild_id: int,
    opener_id: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> list[dict[str, Any]]:
    """A member's open tickets in the guild, newest first."""
    return await pool.fetchall(
        "SELECT * FROM tickets "
        "WHERE guild_id = $1 AND opener_id = $2 AND status = 'open' "
        "ORDER BY created_at DESC",
        (guild_id, opener_id),
        conn=conn,
    )


async def ticket_list_open(
    guild_id: int,
    *,
    limit: int = 25,
    conn: asyncpg.Connection | None = None,
) -> list[dict[str, Any]]:
    """All open tickets in the guild, newest first (staff listing)."""
    return await pool.fetchall(
        "SELECT * FROM tickets WHERE guild_id = $1 AND status = 'open' "
        "ORDER BY created_at DESC LIMIT $2",
        (guild_id, limit),
        conn=conn,
    )


async def ticket_set_claim(
    ticket_id: int,
    claimed_by: int | None,
    *,
    conn: asyncpg.Connection | None = None,
) -> None:
    """Set (or clear, with ``None``) the staff member who claimed a ticket."""
    await pool.execute(
        "UPDATE tickets SET claimed_by = $1 WHERE id = $2",
        (claimed_by, ticket_id),
        conn=conn,
    )


async def ticket_close(
    ticket_id: int,
    *,
    closed_by: int,
    close_reason: str | None,
    closed_at: int,
    conn: asyncpg.Connection | None = None,
) -> None:
    """Mark a ticket closed with its closer / reason / timestamp."""
    await pool.execute(
        "UPDATE tickets SET status = 'closed', closed_by = $1, "
        "close_reason = $2, closed_at = $3 WHERE id = $4",
        (closed_by, close_reason, closed_at, ticket_id),
        conn=conn,
    )


# --------------------------------------------------------------------------- #
# Blacklist
# --------------------------------------------------------------------------- #


async def ticket_is_blacklisted(
    guild_id: int,
    user_id: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> bool:
    """True if ``user_id`` is barred from opening tickets in the guild."""
    row = await pool.fetchone(
        "SELECT 1 FROM ticket_blacklist WHERE guild_id = $1 AND user_id = $2",
        (guild_id, user_id),
        conn=conn,
    )
    return row is not None


async def ticket_add_blacklist(
    guild_id: int,
    user_id: int,
    *,
    added_by: int,
    reason: str | None,
    added_at: int,
    conn: asyncpg.Connection | None = None,
) -> None:
    """Add (or refresh) a blacklist entry."""
    await pool.execute(
        "INSERT INTO ticket_blacklist (guild_id, user_id, added_by, reason, added_at) "
        "VALUES ($1, $2, $3, $4, $5) "
        "ON CONFLICT (guild_id, user_id) DO UPDATE SET "
        "    added_by = $3, reason = $4, added_at = $5",
        (guild_id, user_id, added_by, reason, added_at),
        conn=conn,
    )


async def ticket_remove_blacklist(
    guild_id: int,
    user_id: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> None:
    """Remove a blacklist entry (no-op if absent)."""
    await pool.execute(
        "DELETE FROM ticket_blacklist WHERE guild_id = $1 AND user_id = $2",
        (guild_id, user_id),
        conn=conn,
    )
