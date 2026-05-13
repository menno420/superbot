from __future__ import annotations
import aiosqlite
import os
import logging

logger = logging.getLogger("bot")

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "bot_data.db"
)

_db: aiosqlite.Connection | None = None


async def init() -> None:
    global _db
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    _db = await aiosqlite.connect(DB_PATH)
    _db.row_factory = aiosqlite.Row
    await _db.execute("PRAGMA journal_mode=WAL")
    await _create_tables()
    logger.info("Database initialised at %s", DB_PATH)


async def close() -> None:
    global _db
    if _db:
        await _db.close()
        _db = None


def get() -> aiosqlite.Connection:
    if _db is None:
        raise RuntimeError("Database not initialised — call db.init() first.")
    return _db


async def _create_tables() -> None:
    conn = get()
    statements = [
        """CREATE TABLE IF NOT EXISTS xp (
            user_id  INTEGER NOT NULL,
            guild_id INTEGER NOT NULL,
            xp       INTEGER NOT NULL DEFAULT 0,
            level    INTEGER NOT NULL DEFAULT 0,
            messages INTEGER NOT NULL DEFAULT 0,
            last_xp  INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, guild_id)
        )""",
        """CREATE TABLE IF NOT EXISTS warnings (
            user_id  INTEGER NOT NULL,
            guild_id INTEGER NOT NULL,
            count    INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, guild_id)
        )""",
        """CREATE TABLE IF NOT EXISTS mod_logs (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp    TEXT    NOT NULL,
            guild_id     INTEGER NOT NULL,
            action       TEXT    NOT NULL,
            target_id    INTEGER NOT NULL,
            moderator_id INTEGER NOT NULL,
            reason       TEXT    NOT NULL DEFAULT 'No reason provided'
        )""",
        """CREATE TABLE IF NOT EXISTS role_thresholds (
            guild_id      INTEGER NOT NULL,
            role_name     TEXT    NOT NULL,
            days_required INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (guild_id, role_name)
        )""",
        """CREATE TABLE IF NOT EXISTS guild_settings (
            guild_id INTEGER NOT NULL,
            key      TEXT    NOT NULL,
            value    TEXT    NOT NULL,
            PRIMARY KEY (guild_id, key)
        )""",
        """CREATE TABLE IF NOT EXISTS logs (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            level     TEXT NOT NULL,
            message   TEXT NOT NULL
        )""",
    ]
    for stmt in statements:
        await conn.execute(stmt)
    await conn.commit()


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

async def fetchone(query: str, params: tuple = ()) -> dict | None:
    async with get().execute(query, params) as cur:
        row = await cur.fetchone()
        return dict(row) if row else None


async def fetchall(query: str, params: tuple = ()) -> list[dict]:
    async with get().execute(query, params) as cur:
        return [dict(r) for r in await cur.fetchall()]


async def execute(query: str, params: tuple = ()) -> None:
    await get().execute(query, params)
    await get().commit()


# ---------------------------------------------------------------------------
# XP helpers
# ---------------------------------------------------------------------------

def xp_for_level(level: int) -> int:
    """XP required to complete this level (MEE6-style formula)."""
    return 5 * (level ** 2) + 50 * level + 100


def level_progress(total_xp: int) -> tuple[int, int, int]:
    """Return (level, xp_into_level, xp_needed_for_next_level)."""
    level = 0
    remaining = total_xp
    while True:
        needed = xp_for_level(level)
        if remaining < needed:
            return level, remaining, needed
        remaining -= needed
        level += 1


async def get_xp(user_id: int, guild_id: int) -> dict:
    row = await fetchone(
        "SELECT * FROM xp WHERE user_id=? AND guild_id=?", (user_id, guild_id)
    )
    return row or {
        "user_id": user_id, "guild_id": guild_id,
        "xp": 0, "level": 0, "messages": 0, "last_xp": 0,
    }


async def add_xp(user_id: int, guild_id: int, amount: int, now: int) -> tuple[int, int, bool]:
    """Add *amount* XP; return (total_xp, new_level, leveled_up)."""
    row = await get_xp(user_id, guild_id)
    new_xp = row["xp"] + amount
    new_level, _, _ = level_progress(new_xp)
    leveled_up = new_level > row["level"]
    await execute(
        """INSERT INTO xp (user_id, guild_id, xp, level, messages, last_xp)
           VALUES (?, ?, ?, ?, 1, ?)
           ON CONFLICT(user_id, guild_id) DO UPDATE SET
               xp=excluded.xp, level=excluded.level,
               messages=messages+1, last_xp=excluded.last_xp""",
        (user_id, guild_id, new_xp, new_level, now),
    )
    return new_xp, new_level, leveled_up


# ---------------------------------------------------------------------------
# Guild settings helpers
# ---------------------------------------------------------------------------

async def get_setting(guild_id: int, key: str, default: str = "") -> str:
    row = await fetchone(
        "SELECT value FROM guild_settings WHERE guild_id=? AND key=?", (guild_id, key)
    )
    return row["value"] if row else default


async def set_setting(guild_id: int, key: str, value: str) -> None:
    await execute(
        """INSERT INTO guild_settings (guild_id, key, value) VALUES (?, ?, ?)
           ON CONFLICT(guild_id, key) DO UPDATE SET value=excluded.value""",
        (guild_id, key, value),
    )


# ---------------------------------------------------------------------------
# Role threshold helpers
# ---------------------------------------------------------------------------

async def get_role_thresholds(guild_id: int) -> list[dict]:
    return await fetchall(
        "SELECT role_name, days_required FROM role_thresholds "
        "WHERE guild_id=? ORDER BY days_required",
        (guild_id,),
    )


async def set_role_threshold(guild_id: int, role_name: str, days: int) -> None:
    await execute(
        """INSERT INTO role_thresholds (guild_id, role_name, days_required)
           VALUES (?, ?, ?)
           ON CONFLICT(guild_id, role_name) DO UPDATE SET days_required=excluded.days_required""",
        (guild_id, role_name, days),
    )


async def remove_role_threshold(guild_id: int, role_name: str) -> None:
    await execute(
        "DELETE FROM role_thresholds WHERE guild_id=? AND role_name=?",
        (guild_id, role_name),
    )


# ---------------------------------------------------------------------------
# Warning helpers
# ---------------------------------------------------------------------------

async def get_warnings(user_id: int, guild_id: int) -> int:
    row = await fetchone(
        "SELECT count FROM warnings WHERE user_id=? AND guild_id=?", (user_id, guild_id)
    )
    return row["count"] if row else 0


async def add_warning(user_id: int, guild_id: int) -> int:
    count = await get_warnings(user_id, guild_id) + 1
    await execute(
        """INSERT INTO warnings (user_id, guild_id, count) VALUES (?, ?, ?)
           ON CONFLICT(user_id, guild_id) DO UPDATE SET count=excluded.count""",
        (user_id, guild_id, count),
    )
    return count


async def clear_warnings(user_id: int, guild_id: int) -> None:
    await execute(
        "DELETE FROM warnings WHERE user_id=? AND guild_id=?", (user_id, guild_id)
    )


# ---------------------------------------------------------------------------
# Mod log helpers
# ---------------------------------------------------------------------------

async def log_mod_action(
    guild_id: int, action: str, target_id: int,
    moderator_id: int, reason: str = "No reason provided",
) -> None:
    from datetime import datetime
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    await execute(
        "INSERT INTO mod_logs (timestamp, guild_id, action, target_id, moderator_id, reason) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (ts, guild_id, action, target_id, moderator_id, reason),
    )
