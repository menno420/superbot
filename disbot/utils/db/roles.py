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
        "SELECT role_name, days_required, level_required, xp_auto_assign, "
        "role_id, display_name "
        "FROM role_thresholds WHERE guild_id=$1 ORDER BY days_required",
        (guild_id,),
    )


async def set_role_threshold(
    guild_id: int,
    role_name: str,
    days: int,
    *,
    role_id: int | None = None,
    display_name: str | None = None,
) -> None:
    """Upsert the time tier for a role threshold.

    ``role_id`` / ``display_name`` are the PR6 id-groundwork (migration 056):
    when supplied (selector-driven writes) they are stored so readers can resolve
    the role id-first and panels can diagnose stale rows.  On conflict they are
    ``COALESCE``-preserved, so a later name-only or XP-only update never wipes a
    previously-captured id.
    """
    await pool.execute(
        """INSERT INTO role_thresholds
               (guild_id, role_name, days_required, role_id, display_name)
           VALUES ($1, $2, $3, $4, $5)
           ON CONFLICT (guild_id, role_name) DO UPDATE SET
               days_required = EXCLUDED.days_required,
               role_id = COALESCE(EXCLUDED.role_id, role_thresholds.role_id),
               display_name = COALESCE(
                   EXCLUDED.display_name, role_thresholds.display_name
               )""",
        (guild_id, role_name, days, role_id, display_name),
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
        "UPDATE role_thresholds SET days_required=0 WHERE guild_id=$1 AND role_name=$2",
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
        "SELECT role_name, level_required, role_id, display_name "
        "FROM role_thresholds "
        "WHERE guild_id=$1 AND xp_auto_assign=TRUE AND level_required IS NOT NULL "
        "ORDER BY level_required",
        (guild_id,),
    )


async def set_role_xp_threshold(
    guild_id: int,
    role_name: str,
    level_required: int | None,
    auto_assign: bool,
    *,
    role_id: int | None = None,
    display_name: str | None = None,
) -> None:
    """Upsert the XP automation columns for a role threshold row.

    If no row exists for (guild_id, role_name), inserts one with
    days_required=0.  Only updates the XP columns; existing
    days_required is preserved on conflict.  ``role_id`` / ``display_name`` are
    the PR6 id-groundwork (migration 056), ``COALESCE``-preserved on conflict so
    a name-only or time-only update never wipes a previously-captured id.
    """
    await pool.execute(
        """INSERT INTO role_thresholds
               (guild_id, role_name, days_required, level_required, xp_auto_assign,
                role_id, display_name)
           VALUES ($1, $2, 0, $3, $4, $5, $6)
           ON CONFLICT (guild_id, role_name) DO UPDATE SET
               level_required = EXCLUDED.level_required,
               xp_auto_assign = EXCLUDED.xp_auto_assign,
               role_id = COALESCE(EXCLUDED.role_id, role_thresholds.role_id),
               display_name = COALESCE(
                   EXCLUDED.display_name, role_thresholds.display_name
               )""",
        (guild_id, role_name, level_required, auto_assign, role_id, display_name),
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


async def get_reaction_roles_for_message(
    guild_id: int,
    message_id: int,
) -> list[dict]:
    """Every emoji → role binding on one message (the unique-mode sibling read)."""
    return await pool.fetchall(
        "SELECT emoji, role_id FROM reaction_roles WHERE guild_id=$1 AND message_id=$2",
        (guild_id, message_id),
    )


# ---------------------------------------------------------------------------
# Per-message reaction modes (overhaul PR 3 — Carl's `rr <mode> <msg_id>`)
# ---------------------------------------------------------------------------
# Mode is a property of the *message*, not a single emoji binding. No row ⇒
# 'normal', so existing reaction messages behave exactly as before.


async def set_reaction_message_mode(
    guild_id: int,
    message_id: int,
    mode: str,
) -> None:
    """Set (or change) a reaction-role message's mode (normal/unique/verify)."""
    await pool.execute(
        """INSERT INTO reaction_role_message_modes (guild_id, message_id, mode)
           VALUES ($1, $2, $3)
           ON CONFLICT (guild_id, message_id) DO UPDATE SET mode=EXCLUDED.mode""",
        (guild_id, message_id, mode),
    )


async def get_reaction_message_mode(guild_id: int, message_id: int) -> str:
    """Return a message's reaction mode, defaulting to ``'normal'`` (no row)."""
    row = await pool.fetchone(
        "SELECT mode FROM reaction_role_message_modes "
        "WHERE guild_id=$1 AND message_id=$2",
        (guild_id, message_id),
    )
    return row["mode"] if row else "normal"


async def clear_reaction_message_mode(guild_id: int, message_id: int) -> None:
    """Reset a message back to the default ``'normal'`` mode (drop its row)."""
    await pool.execute(
        "DELETE FROM reaction_role_message_modes WHERE guild_id=$1 AND message_id=$2",
        (guild_id, message_id),
    )


async def get_reaction_message_modes(guild_id: int) -> list[dict]:
    """All non-default message modes in a guild (the panel's mode display)."""
    return await pool.fetchall(
        "SELECT message_id, mode FROM reaction_role_message_modes WHERE guild_id=$1",
        (guild_id,),
    )


async def delete_reaction_modes_for_guild(guild_id: int) -> int:
    """Drop every reaction-message mode row for a departed guild (teardown)."""
    rows = await pool.fetchall(
        "DELETE FROM reaction_role_message_modes WHERE guild_id=$1 RETURNING message_id",
        (guild_id,),
    )
    return len(rows)


async def delete_role_thresholds_for_guild(guild_id: int) -> int:
    """Drop every ``role_thresholds`` row for a departed guild (teardown)."""
    rows = await pool.fetchall(
        "DELETE FROM role_thresholds WHERE guild_id=$1 RETURNING role_name",
        (guild_id,),
    )
    return len(rows)


async def delete_role_exemptions_for_guild(guild_id: int) -> int:
    """Drop every ``role_automation_exemptions`` row for a departed guild (teardown)."""
    rows = await pool.fetchall(
        "DELETE FROM role_automation_exemptions WHERE guild_id=$1 RETURNING role_id",
        (guild_id,),
    )
    return len(rows)


async def delete_reaction_roles_for_guild(guild_id: int) -> int:
    """Drop every ``reaction_roles`` row for a departed guild (teardown).

    ``reaction_roles`` is guild-scoped (PK ``guild_id, message_id, emoji``) and
    does NOT self-clean on message delete — no message-delete handler removes its
    rows — so guild-leave needs an explicit purge.
    """
    rows = await pool.fetchall(
        "DELETE FROM reaction_roles WHERE guild_id=$1 RETURNING message_id",
        (guild_id,),
    )
    return len(rows)
