"""Starboard / Hall-of-Fame CRUD (idea B1; migration 083).

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
        "SELECT guild_id, channel_id, threshold, emoji, enabled, self_star "
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
    self_star: bool = False,
) -> None:
    """Upsert the guild's starboard config (one row per guild)."""
    await pool.execute(
        """INSERT INTO starboard_settings
               (guild_id, channel_id, threshold, emoji, enabled, self_star)
           VALUES ($1, $2, $3, $4, $5, $6)
           ON CONFLICT (guild_id) DO UPDATE SET
               channel_id = EXCLUDED.channel_id,
               threshold  = EXCLUDED.threshold,
               emoji      = EXCLUDED.emoji,
               enabled    = EXCLUDED.enabled,
               self_star  = EXCLUDED.self_star""",
        (guild_id, channel_id, threshold, emoji, enabled, self_star),
    )


async def set_enabled(guild_id: int, enabled: bool) -> None:
    """Flip the on/off switch without touching channel/threshold/emoji."""
    await pool.execute(
        "UPDATE starboard_settings SET enabled=$2 WHERE guild_id=$1",
        (guild_id, enabled),
    )


async def set_self_star(guild_id: int, self_star: bool) -> None:
    """Toggle whether the author's own ⭐ counts toward the threshold."""
    await pool.execute(
        "UPDATE starboard_settings SET self_star=$2 WHERE guild_id=$1",
        (guild_id, self_star),
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
# Ignore channels (messages here never enter the board)
# ---------------------------------------------------------------------------


async def list_ignore_channels(guild_id: int) -> set[int]:
    """Return the set of channel ids whose messages never enter the board."""
    rows = await pool.fetchall(
        "SELECT channel_id FROM starboard_ignore_channels WHERE guild_id=$1",
        (guild_id,),
    )
    return {int(r["channel_id"]) for r in rows}


async def add_ignore_channel(guild_id: int, channel_id: int) -> None:
    """Add a channel to the guild's ignore list (idempotent by PK)."""
    await pool.execute(
        """INSERT INTO starboard_ignore_channels (guild_id, channel_id)
           VALUES ($1, $2)
           ON CONFLICT (guild_id, channel_id) DO NOTHING""",
        (guild_id, channel_id),
    )


async def remove_ignore_channel(guild_id: int, channel_id: int) -> None:
    """Remove a channel from the guild's ignore list."""
    await pool.execute(
        "DELETE FROM starboard_ignore_channels WHERE guild_id=$1 AND channel_id=$2",
        (guild_id, channel_id),
    )


# ---------------------------------------------------------------------------
# Guild teardown
# ---------------------------------------------------------------------------


async def delete_for_guild(guild_id: int) -> int:
    """Delete all starboard rows (settings + entries + ignores) for a guild.

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
    await pool.execute(
        "DELETE FROM starboard_ignore_channels WHERE guild_id=$1",
        (guild_id,),
    )
    return len(rows)
