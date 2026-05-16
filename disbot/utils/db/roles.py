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
