"""Moderation table CRUD: warnings, mod_logs, prohibited_words."""

from __future__ import annotations

from utils.db import pool

# ---------------------------------------------------------------------------
# Warnings
# ---------------------------------------------------------------------------


async def get_warnings(user_id: int, guild_id: int) -> int:
    row = await pool.fetchone(
        "SELECT count FROM warnings WHERE user_id=$1 AND guild_id=$2",
        (user_id, guild_id),
    )
    return row["count"] if row else 0


async def add_warning(user_id: int, guild_id: int) -> int:
    """Atomic increment; returns the new total."""
    row = await pool.get().fetchrow(
        """INSERT INTO warnings (user_id, guild_id, count) VALUES ($1, $2, 1)
           ON CONFLICT (user_id, guild_id) DO UPDATE SET count = warnings.count + 1
           RETURNING count""",
        user_id,
        guild_id,
    )
    return row["count"]


async def clear_warnings(user_id: int, guild_id: int) -> None:
    await pool.execute(
        "DELETE FROM warnings WHERE user_id=$1 AND guild_id=$2",
        (user_id, guild_id),
    )


# ---------------------------------------------------------------------------
# Mod logs (append-only)
# ---------------------------------------------------------------------------


async def log_mod_action(
    guild_id: int,
    action: str,
    target_id: int,
    moderator_id: int,
    reason: str = "No reason provided",
) -> None:
    from datetime import datetime, timezone

    # ``mod_logs.timestamp`` is ``timestamp with time zone``; asyncpg
    # needs a real ``datetime`` for that column.  Passing a strftime
    # string raised ``asyncpg.DataError`` at insert time, which silently
    # broke the mod-action audit log for every action type and crashed
    # the counting stage's auto-delete path.  Bind the tz-aware datetime.
    ts = datetime.now(tz=timezone.utc)
    await pool.execute(
        "INSERT INTO mod_logs (timestamp, guild_id, action, target_id, "
        "moderator_id, reason) VALUES ($1, $2, $3, $4, $5, $6)",
        (ts, guild_id, action, target_id, moderator_id, reason),
    )


async def get_mod_logs(
    target_id: int,
    guild_id: int,
    limit: int = 10,
) -> list[dict]:
    return await pool.fetchall(
        "SELECT action, timestamp, moderator_id, reason FROM mod_logs "
        "WHERE target_id=$1 AND guild_id=$2 ORDER BY id DESC LIMIT $3",
        (target_id, guild_id, limit),
    )


# ---------------------------------------------------------------------------
# Prohibited words (cleanup_cog filter list)
# ---------------------------------------------------------------------------


async def get_prohibited_words(guild_id: int) -> list[str]:
    rows = await pool.fetchall(
        "SELECT word FROM prohibited_words WHERE guild_id=$1",
        (guild_id,),
    )
    return [r["word"] for r in rows]


async def add_prohibited_word(guild_id: int, word: str) -> bool:
    """Returns True if newly added, False if already present."""
    result = await pool.get().execute(
        "INSERT INTO prohibited_words (guild_id, word) VALUES ($1, $2) "
        "ON CONFLICT DO NOTHING",
        guild_id,
        word,
    )
    return result == "INSERT 0 1"


async def remove_prohibited_word(guild_id: int, word: str) -> bool:
    """Returns True if removed, False if not found."""
    result = await pool.get().execute(
        "DELETE FROM prohibited_words WHERE guild_id=$1 AND word=$2",
        guild_id,
        word,
    )
    return result == "DELETE 1"


# ---------------------------------------------------------------------------
# Word-filter mode (cleanup_cog anti-evasion toggle, migration 097)
# ---------------------------------------------------------------------------


async def get_wordfilter_strict(guild_id: int) -> bool:
    """Return True when obfuscation-resistant matching is enabled for the guild.

    Default False (no row) → only the exact whole-word prohibited-words match
    runs, so a guild that never opts in behaves exactly as before.
    """
    row = await pool.fetchone(
        "SELECT strict FROM wordfilter_config WHERE guild_id=$1",
        (guild_id,),
    )
    return bool(row["strict"]) if row else False


async def set_wordfilter_strict(guild_id: int, strict: bool) -> None:
    """Enable/disable obfuscation-resistant prohibited-word matching."""
    await pool.execute(
        """INSERT INTO wordfilter_config (guild_id, strict) VALUES ($1, $2)
           ON CONFLICT (guild_id) DO UPDATE SET strict=EXCLUDED.strict""",
        (guild_id, strict),
    )
