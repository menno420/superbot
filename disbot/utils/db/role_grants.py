"""Temporary role-grant CRUD (reaction-roles overhaul PR 4 — free temp roles).

A ``role_grants`` row (migration 080) records that a member holds a role until
``expires_at``; :mod:`services.role_grants_service` wraps these primitives with
the role mutation + audit, and ``RoleGrantsCog`` sweeps expired rows. Re-granting
the same (guild, member, role) extends the expiry via the unique-key UPSERT.

Co-located with the rest of the role DB layer; accessed as a submodule
(``from utils.db import role_grants``) like ``role_menus``.
"""

from __future__ import annotations

from datetime import datetime

from utils.db import pool


async def grant(
    guild_id: int,
    member_id: int,
    role_id: int,
    expires_at: datetime,
    *,
    granted_by: int | None = None,
) -> None:
    """Record (or extend) a temporary role grant until ``expires_at``."""
    await pool.execute(
        """INSERT INTO role_grants
               (guild_id, member_id, role_id, expires_at, granted_by)
           VALUES ($1, $2, $3, $4, $5)
           ON CONFLICT (guild_id, member_id, role_id)
             DO UPDATE SET expires_at=EXCLUDED.expires_at,
                           granted_by=EXCLUDED.granted_by""",
        (guild_id, member_id, role_id, expires_at, granted_by),
    )


async def list_expired(guild_id: int, now: datetime) -> list[dict]:
    """Expired grants for a guild (the sweep read)."""
    return await pool.fetchall(
        "SELECT grant_id, member_id, role_id FROM role_grants "
        "WHERE guild_id=$1 AND expires_at <= $2",
        (guild_id, now),
    )


async def list_for_member(guild_id: int, member_id: int) -> list[dict]:
    """A member's active temp grants (for a future `!temproles` listing)."""
    return await pool.fetchall(
        "SELECT role_id, expires_at FROM role_grants "
        "WHERE guild_id=$1 AND member_id=$2 ORDER BY expires_at",
        (guild_id, member_id),
    )


async def delete_grant(grant_id: int) -> None:
    """Drop one grant row by id (after the role is removed / is gone)."""
    await pool.execute("DELETE FROM role_grants WHERE grant_id=$1", (grant_id,))


async def remove(guild_id: int, member_id: int, role_id: int) -> None:
    """Cancel a specific member's grant (e.g. role removed manually)."""
    await pool.execute(
        "DELETE FROM role_grants WHERE guild_id=$1 AND member_id=$2 AND role_id=$3",
        (guild_id, member_id, role_id),
    )


async def delete_for_guild(guild_id: int) -> int:
    """Delete every grant for a departed guild (teardown). Returns the count."""
    rows = await pool.fetchall(
        "DELETE FROM role_grants WHERE guild_id=$1 RETURNING grant_id",
        (guild_id,),
    )
    return len(rows)
