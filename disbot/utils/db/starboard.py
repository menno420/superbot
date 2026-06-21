"""Starboard / Hall-of-Fame CRUD (idea B1; migration 082).

Per-guild config (``starboard_settings``) + the source→starboard message mapping
(``starboard_entries``) that makes edit-in-place recounts + dedupe possible. The
audited write seam is :mod:`services.starboard_service`; this module is typed CRUD
only — ``pool.*`` lives here and nowhere else (the ``utils/db`` boundary).
"""

from __future__ import annotations

from utils.db import pool

# ---------------------------------------------------------------------------
# Per-guild config
# ---------------------------------------------------------------------------


async def get_settings(guild_id: int) -> dict | None:
    """Return the guild's starboard config row, or ``None`` if unconfigured."""
    return await pool.fetchone(
        "SELECT guild_id, channel_id, threshold, emoji, enabled "
        "FROM starboard_settings WHERE guild_id=$1",
        (guild_id,),
    )


async def set_settings(
    guild_id: int,
    channel_id: int,
    *,
    threshold: int = 3,
    emoji: str = "⭐",
    enabled: bool = True,
) -> None:
    """Upsert the guild's starboard config (one row per guild)."""
    await pool.execute(
        """INSERT INTO starboard_settings
               (guild_id, channel_id, threshold, emoji, enabled)
           VALUES ($1, $2, $3, $4, $5)
           ON CONFLICT (guild_id) DO UPDATE SET
               channel_id = EXCLUDED.channel_id,
               threshold  = EXCLUDED.threshold,
               emoji      = EXCLUDED.emoji,
               enabled    = EXCLUDED.enabled""",
        (guild_id, channel_id, threshold, emoji, enabled),
    )


async def set_enabled(guild_id: int, enabled: bool) -> None:
    """Flip the on/off switch without touching channel/threshold/emoji."""
    await pool.execute(
        "UPDATE starboard_settings SET enabled=$2 WHERE guild_id=$1",
        (guild_id, enabled),
    )


# ---------------------------------------------------------------------------
# Per-message entries (source → starboard message mapping)
# ---------------------------------------------------------------------------


async def get_entry(guild_id: int, source_message_id: int) -> dict | None:
    """Return the entry for a source message, or ``None`` if it never entered."""
    return await pool.fetchone(
        "SELECT guild_id, source_message_id, starboard_message_id, star_count "
        "FROM starboard_entries WHERE guild_id=$1 AND source_message_id=$2",
        (guild_id, source_message_id),
    )


async def upsert_entry(
    guild_id: int,
    source_message_id: int,
    *,
    star_count: int,
    starboard_message_id: int | None,
) -> None:
    """Insert/update an entry's count + posted-message id (idempotent by PK)."""
    await pool.execute(
        """INSERT INTO starboard_entries
               (guild_id, source_message_id, starboard_message_id, star_count)
           VALUES ($1, $2, $3, $4)
           ON CONFLICT (guild_id, source_message_id) DO UPDATE SET
               starboard_message_id = EXCLUDED.starboard_message_id,
               star_count           = EXCLUDED.star_count""",
        (guild_id, source_message_id, starboard_message_id, star_count),
    )


async def delete_entry(guild_id: int, source_message_id: int) -> None:
    """Drop an entry (message fell back below threshold / source deleted)."""
    await pool.execute(
        "DELETE FROM starboard_entries WHERE guild_id=$1 AND source_message_id=$2",
        (guild_id, source_message_id),
    )


# ---------------------------------------------------------------------------
# Guild teardown
# ---------------------------------------------------------------------------


async def delete_for_guild(guild_id: int) -> int:
    """Delete all starboard rows (settings + entries) for a departed guild.

    Returns the number of entries removed. Registered in
    ``guild_lifecycle.teardown`` (architecture INV-I).
    """
    rows = await pool.fetchall(
        "DELETE FROM starboard_entries WHERE guild_id=$1 RETURNING source_message_id",
        (guild_id,),
    )
    await pool.execute(
        "DELETE FROM starboard_settings WHERE guild_id=$1",
        (guild_id,),
    )
    return len(rows)
