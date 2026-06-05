"""Role-threshold and reaction-role table CRUD.

Time-based role thresholds (``days_required``) and XP-based thresholds
(``level_required`` + ``xp_auto_assign``) both live in the same
``role_thresholds`` table; the helpers below target each column set.
Reaction roles are separate but co-located here because the
role_cog/views/roles/* layer is their only consumer.
"""

from __future__ import annotations

from utils.db import pool

# ---------------------------------------------------------------------------
# Time-based and XP-based role thresholds
# ---------------------------------------------------------------------------


async def get_role_thresholds(guild_id: int) -> list[dict]:
    return await pool.fetchall(
        "SELECT role_name, days_required, level_required, xp_auto_assign "
        "FROM role_thresholds WHERE guild_id=$1 ORDER BY days_required",
        (guild_id,),
    )


async def set_role_threshold(guild_id: int, role_name: str, days: int) -> None:
    await pool.execute(
        """INSERT INTO role_thresholds (guild_id, role_name, days_required)
           VALUES ($1, $2, $3)
           ON CONFLICT (guild_id, role_name)
             DO UPDATE SET days_required=EXCLUDED.days_required""",
        (guild_id, role_name, days),
    )


async def remove_role_threshold(guild_id: int, role_name: str) -> None:
    await pool.execute(
        "DELETE FROM role_thresholds WHERE guild_id=$1 AND role_name=$2",
        (guild_id, role_name),
    )


async def clear_role_time_threshold(guild_id: int, role_name: str) -> None:
    """Remove only the *time* requirement for a role threshold.

    Field-specific counterpart to the destructive full-row
    :func:`remove_role_threshold`: it zeroes ``days_required`` but leaves any
    XP automation (``level_required`` / ``xp_auto_assign``) on the same row
    intact.  The row is deleted **only** when no automation field remains
    (i.e. there is no XP config either), so clearing a role's time tier never
    silently wipes its XP tier.
    """
    await pool.execute(
        "UPDATE role_thresholds SET days_required=0 "
        "WHERE guild_id=$1 AND role_name=$2",
        (guild_id, role_name),
    )
    await pool.execute(
        "DELETE FROM role_thresholds "
        "WHERE guild_id=$1 AND role_name=$2 "
        "AND days_required=0 AND level_required IS NULL",
        (guild_id, role_name),
    )


async def clear_role_xp_threshold(guild_id: int, role_name: str) -> None:
    """Remove only the *XP* automation for a role threshold.

    Mirror of :func:`clear_role_time_threshold`: it clears ``level_required``
    and ``xp_auto_assign`` while preserving any ``days_required`` time tier on
    the same row, and deletes the row only when no time tier remains
    (``days_required = 0``).  Improves on the previous
    ``set_role_xp_threshold(..., None, False)`` removal, which left a stale
    all-empty row behind when the role had no time config.
    """
    await pool.execute(
        "UPDATE role_thresholds SET level_required=NULL, xp_auto_assign=FALSE "
        "WHERE guild_id=$1 AND role_name=$2",
        (guild_id, role_name),
    )
    await pool.execute(
        "DELETE FROM role_thresholds "
        "WHERE guild_id=$1 AND role_name=$2 "
        "AND days_required=0 AND level_required IS NULL",
        (guild_id, role_name),
    )


async def get_xp_threshold_roles(guild_id: int) -> list[dict]:
    """Rows with xp_auto_assign=TRUE and a configured level_required."""
    return await pool.fetchall(
        "SELECT role_name, level_required FROM role_thresholds "
        "WHERE guild_id=$1 AND xp_auto_assign=TRUE AND level_required IS NOT NULL "
        "ORDER BY level_required",
        (guild_id,),
    )


async def set_role_xp_threshold(
    guild_id: int,
    role_name: str,
    level_required: int | None,
    auto_assign: bool,
) -> None:
    """Upsert the XP automation columns for a role threshold row.

    If no row exists for (guild_id, role_name), inserts one with
    days_required=0.  Only updates the XP columns; existing
    days_required is preserved on conflict.
    """
    await pool.execute(
        """INSERT INTO role_thresholds
               (guild_id, role_name, days_required, level_required, xp_auto_assign)
           VALUES ($1, $2, 0, $3, $4)
           ON CONFLICT (guild_id, role_name) DO UPDATE SET
               level_required = EXCLUDED.level_required,
               xp_auto_assign = EXCLUDED.xp_auto_assign""",
        (guild_id, role_name, level_required, auto_assign),
    )


# ---------------------------------------------------------------------------
# Role-automation exemptions (per-role, id-keyed) — migration 052
# ---------------------------------------------------------------------------


async def get_role_exemptions(guild_id: int) -> list[dict]:
    """Return every exemption row for ``guild_id`` (role_id + both flags)."""
    return await pool.fetchall(
        "SELECT role_id, exempt_xp, exempt_time "
        "FROM role_automation_exemptions WHERE guild_id=$1 ORDER BY role_id",
        (guild_id,),
    )


async def set_role_exemption(
    guild_id: int,
    role_id: int,
    *,
    exempt_xp: bool,
    exempt_time: bool,
) -> None:
    """Upsert the exemption flags for a single role."""
    await pool.execute(
        """INSERT INTO role_automation_exemptions
               (guild_id, role_id, exempt_xp, exempt_time)
           VALUES ($1, $2, $3, $4)
           ON CONFLICT (guild_id, role_id) DO UPDATE SET
               exempt_xp = EXCLUDED.exempt_xp,
               exempt_time = EXCLUDED.exempt_time""",
        (guild_id, role_id, exempt_xp, exempt_time),
    )


async def clear_role_exemption(guild_id: int, role_id: int) -> None:
    """Delete the exemption row for a role (used when both flags clear)."""
    await pool.execute(
        "DELETE FROM role_automation_exemptions WHERE guild_id=$1 AND role_id=$2",
        (guild_id, role_id),
    )


# ---------------------------------------------------------------------------
# Reaction roles
# ---------------------------------------------------------------------------


async def add_reaction_role(
    guild_id: int,
    message_id: int,
    emoji: str,
    role_id: int,
) -> None:
    await pool.execute(
        """INSERT INTO reaction_roles (guild_id, message_id, emoji, role_id)
           VALUES ($1, $2, $3, $4)
           ON CONFLICT (guild_id, message_id, emoji)
             DO UPDATE SET role_id=EXCLUDED.role_id""",
        (guild_id, message_id, emoji, role_id),
    )


async def remove_reaction_role(guild_id: int, message_id: int, emoji: str) -> None:
    await pool.execute(
        "DELETE FROM reaction_roles WHERE guild_id=$1 AND message_id=$2 AND emoji=$3",
        (guild_id, message_id, emoji),
    )


async def get_reaction_role(
    guild_id: int,
    message_id: int,
    emoji: str,
) -> int | None:
    row = await pool.fetchone(
        "SELECT role_id FROM reaction_roles "
        "WHERE guild_id=$1 AND message_id=$2 AND emoji=$3",
        (guild_id, message_id, emoji),
    )
    return row["role_id"] if row else None


async def get_all_reaction_roles(guild_id: int) -> list[dict]:
    return await pool.fetchall(
        "SELECT message_id, emoji, role_id FROM reaction_roles WHERE guild_id=$1",
        (guild_id,),
    )
