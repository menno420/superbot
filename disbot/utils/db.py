from __future__ import annotations
import aiosqlite
import os
import logging

logger = logging.getLogger("bot")

_DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "bot_data.db",
)
DB_PATH = os.environ.get("BOT_DB_PATH", _DEFAULT_DB_PATH)

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
        """CREATE TABLE IF NOT EXISTS economy (
            user_id      INTEGER NOT NULL,
            guild_id     INTEGER NOT NULL,
            last_daily   INTEGER NOT NULL DEFAULT 0,
            daily_streak INTEGER NOT NULL DEFAULT 0,
            daily_count  INTEGER NOT NULL DEFAULT 0,
            last_worked  INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, guild_id)
        )""",
        """CREATE TABLE IF NOT EXISTS job_progress (
            user_id      INTEGER NOT NULL,
            guild_id     INTEGER NOT NULL,
            job_name     TEXT    NOT NULL,
            times_worked INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, guild_id, job_name)
        )""",
        """CREATE TABLE IF NOT EXISTS inventory (
            user_id   INTEGER NOT NULL,
            guild_id  INTEGER NOT NULL,
            item_name TEXT    NOT NULL,
            quantity  INTEGER NOT NULL DEFAULT 1,
            PRIMARY KEY (user_id, guild_id, item_name)
        )""",
        """CREATE TABLE IF NOT EXISTS xp (
            user_id  INTEGER NOT NULL,
            guild_id INTEGER NOT NULL,
            xp       INTEGER NOT NULL DEFAULT 0,
            level    INTEGER NOT NULL DEFAULT 0,
            messages INTEGER NOT NULL DEFAULT 0,
            last_xp  INTEGER NOT NULL DEFAULT 0,
            coins    INTEGER NOT NULL DEFAULT 0,
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
        """CREATE TABLE IF NOT EXISTS reaction_roles (
            guild_id    INTEGER NOT NULL,
            message_id  INTEGER NOT NULL,
            emoji       TEXT    NOT NULL,
            role_id     INTEGER NOT NULL,
            PRIMARY KEY (guild_id, message_id, emoji)
        )""",
        """CREATE TABLE IF NOT EXISTS rps_players (
            user_id INTEGER PRIMARY KEY,
            name    TEXT    NOT NULL,
            wins    INTEGER NOT NULL DEFAULT 0,
            losses  INTEGER NOT NULL DEFAULT 0,
            ties    INTEGER NOT NULL DEFAULT 0
        )""",
        """CREATE TABLE IF NOT EXISTS rps_matches (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            player1_id INTEGER NOT NULL,
            player2_id INTEGER NOT NULL,
            winner_id  INTEGER,
            mode       TEXT    NOT NULL DEFAULT 'classic',
            best_of    INTEGER NOT NULL DEFAULT 3,
            timestamp  TEXT    NOT NULL
        )""",
    ]
    for stmt in statements:
        await conn.execute(stmt)
    await conn.commit()
    # Migration: add coins column to existing xp tables that predate it
    async with conn.execute("PRAGMA table_info(xp)") as cur:
        cols = {row[1] async for row in cur}
    if "coins" not in cols:
        await conn.execute("ALTER TABLE xp ADD COLUMN coins INTEGER NOT NULL DEFAULT 0")
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
        "xp": 0, "level": 0, "messages": 0, "last_xp": 0, "coins": 0,
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


# ---------------------------------------------------------------------------
# Coin helpers
# ---------------------------------------------------------------------------

async def get_coins(user_id: int, guild_id: int) -> int:
    row = await fetchone(
        "SELECT coins FROM xp WHERE user_id=? AND guild_id=?", (user_id, guild_id)
    )
    return row["coins"] if row else 0


async def add_coins(user_id: int, guild_id: int, amount: int) -> int:
    """Add (or subtract if negative) coins; clamps to 0. Returns new balance."""
    # Pass amount twice: once for the INSERT default (clamped for new users),
    # once for the UPDATE so negative values actually subtract from existing balance.
    await execute(
        """INSERT INTO xp (user_id, guild_id, coins) VALUES (?, ?, MAX(0, ?))
           ON CONFLICT(user_id, guild_id) DO UPDATE SET
               coins=MAX(0, coins + ?)""",
        (user_id, guild_id, amount, amount),
    )
    return await get_coins(user_id, guild_id)


async def set_coins(user_id: int, guild_id: int, amount: int) -> None:
    await execute(
        """INSERT INTO xp (user_id, guild_id, coins) VALUES (?, ?, MAX(0, ?))
           ON CONFLICT(user_id, guild_id) DO UPDATE SET coins=MAX(0, excluded.coins)""",
        (user_id, guild_id, amount),
    )


# ---------------------------------------------------------------------------
# Economy / daily helpers
# ---------------------------------------------------------------------------

async def get_economy(user_id: int, guild_id: int) -> dict:
    await execute(
        "INSERT OR IGNORE INTO economy (user_id, guild_id) VALUES (?,?)",
        (user_id, guild_id),
    )
    row = await fetchone(
        "SELECT * FROM economy WHERE user_id=? AND guild_id=?", (user_id, guild_id)
    )
    return dict(row)


async def set_economy(user_id: int, guild_id: int, **kwargs) -> None:
    allowed = {"last_daily", "daily_streak", "daily_count", "last_worked"}
    cols = {k: v for k, v in kwargs.items() if k in allowed}
    if not cols:
        return
    sets = ", ".join(f"{k}=?" for k in cols)
    await execute(
        f"UPDATE economy SET {sets} WHERE user_id=? AND guild_id=?",
        (*cols.values(), user_id, guild_id),
    )


# ---------------------------------------------------------------------------
# Job progress helpers
# ---------------------------------------------------------------------------

async def get_job_times(user_id: int, guild_id: int, job_name: str) -> int:
    row = await fetchone(
        "SELECT times_worked FROM job_progress WHERE user_id=? AND guild_id=? AND job_name=?",
        (user_id, guild_id, job_name),
    )
    return row["times_worked"] if row else 0


async def increment_job(user_id: int, guild_id: int, job_name: str) -> int:
    """Increment times_worked for a job and return the new count."""
    await execute(
        """INSERT INTO job_progress (user_id, guild_id, job_name, times_worked)
           VALUES (?,?,?,1)
           ON CONFLICT(user_id, guild_id, job_name)
           DO UPDATE SET times_worked = times_worked + 1""",
        (user_id, guild_id, job_name),
    )
    return await get_job_times(user_id, guild_id, job_name)


# ---------------------------------------------------------------------------
# Inventory helpers
# ---------------------------------------------------------------------------

async def get_inventory(user_id: int, guild_id: int) -> dict[str, int]:
    rows = await fetchall(
        "SELECT item_name, quantity FROM inventory WHERE user_id=? AND guild_id=?",
        (user_id, guild_id),
    )
    return {r["item_name"]: r["quantity"] for r in rows}


async def add_item(user_id: int, guild_id: int, item_name: str, quantity: int = 1) -> None:
    await execute(
        """INSERT INTO inventory (user_id, guild_id, item_name, quantity)
           VALUES (?,?,?,?)
           ON CONFLICT(user_id, guild_id, item_name)
           DO UPDATE SET quantity = quantity + ?""",
        (user_id, guild_id, item_name, quantity, quantity),
    )


async def has_item(user_id: int, guild_id: int, item_name: str) -> bool:
    row = await fetchone(
        "SELECT quantity FROM inventory WHERE user_id=? AND guild_id=? AND item_name=?",
        (user_id, guild_id, item_name),
    )
    return bool(row and row["quantity"] > 0)


# ---------------------------------------------------------------------------
# Reaction role helpers
# ---------------------------------------------------------------------------

async def add_reaction_role(
    guild_id: int, message_id: int, emoji: str, role_id: int
) -> None:
    await execute(
        """INSERT INTO reaction_roles (guild_id, message_id, emoji, role_id)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(guild_id, message_id, emoji) DO UPDATE SET role_id=excluded.role_id""",
        (guild_id, message_id, emoji, role_id),
    )


async def remove_reaction_role(
    guild_id: int, message_id: int, emoji: str
) -> None:
    await execute(
        "DELETE FROM reaction_roles WHERE guild_id=? AND message_id=? AND emoji=?",
        (guild_id, message_id, emoji),
    )


async def get_reaction_role(
    guild_id: int, message_id: int, emoji: str
) -> int | None:
    row = await fetchone(
        "SELECT role_id FROM reaction_roles WHERE guild_id=? AND message_id=? AND emoji=?",
        (guild_id, message_id, emoji),
    )
    return row["role_id"] if row else None


async def get_all_reaction_roles(guild_id: int) -> list[dict]:
    return await fetchall(
        "SELECT message_id, emoji, role_id FROM reaction_roles WHERE guild_id=?",
        (guild_id,),
    )


# ---------------------------------------------------------------------------
# RPS stats helpers
# ---------------------------------------------------------------------------

async def rps_ensure_player(user_id: int, name: str) -> None:
    await execute(
        "INSERT OR IGNORE INTO rps_players (user_id, name) VALUES (?, ?)",
        (user_id, name),
    )


async def rps_update_stat(user_id: int, result: str) -> None:
    col = {"win": "wins", "loss": "losses", "tie": "ties"}.get(result)
    if col:
        await execute(f"UPDATE rps_players SET {col}={col}+1 WHERE user_id=?", (user_id,))


async def rps_get_leaderboard() -> list[dict]:
    return await fetchall(
        "SELECT name, wins, losses, ties FROM rps_players ORDER BY wins DESC LIMIT 15"
    )
