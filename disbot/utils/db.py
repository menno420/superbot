from __future__ import annotations
import asyncpg
import json
import os
import logging

logger = logging.getLogger("bot")

_pool: asyncpg.Pool | None = None


def _get_dsn() -> str:
    if dsn := os.environ.get("DATABASE_URL"):
        return dsn
    raise RuntimeError(
        "DATABASE_URL environment variable is required. "
        "Format: postgres://user:password@host:5432/dbname"
    )


async def _init_conn(conn: asyncpg.Connection) -> None:
    """Register codecs so JSONB columns round-trip as Python dicts automatically."""
    await conn.set_type_codec(
        "jsonb",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )


async def init() -> None:
    global _pool
    dsn = _get_dsn()
    _pool = await asyncpg.create_pool(dsn, min_size=2, max_size=10, init=_init_conn)
    await _create_tables()
    logger.info("PostgreSQL pool initialised (%s)", dsn.split("@")[-1])


async def close() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


def get() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database not initialised — call db.init() first.")
    return _pool


async def _create_tables() -> None:
    pool = get()
    statements = [
        # ---- existing tables (kept identical in semantics) ----
        """CREATE TABLE IF NOT EXISTS economy (
            user_id      BIGINT  NOT NULL,
            guild_id     BIGINT  NOT NULL,
            last_daily   BIGINT  NOT NULL DEFAULT 0,
            daily_streak INTEGER NOT NULL DEFAULT 0,
            daily_count  INTEGER NOT NULL DEFAULT 0,
            last_worked  BIGINT  NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, guild_id)
        )""",
        """CREATE TABLE IF NOT EXISTS job_progress (
            user_id      BIGINT  NOT NULL,
            guild_id     BIGINT  NOT NULL,
            job_name     TEXT    NOT NULL,
            times_worked INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, guild_id, job_name)
        )""",
        """CREATE TABLE IF NOT EXISTS inventory (
            user_id   BIGINT  NOT NULL,
            guild_id  BIGINT  NOT NULL,
            item_name TEXT    NOT NULL,
            quantity  INTEGER NOT NULL DEFAULT 1,
            PRIMARY KEY (user_id, guild_id, item_name)
        )""",
        """CREATE TABLE IF NOT EXISTS xp (
            user_id  BIGINT  NOT NULL,
            guild_id BIGINT  NOT NULL,
            xp       BIGINT  NOT NULL DEFAULT 0,
            level    INTEGER NOT NULL DEFAULT 0,
            messages BIGINT  NOT NULL DEFAULT 0,
            last_xp  BIGINT  NOT NULL DEFAULT 0,
            coins    BIGINT  NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, guild_id)
        )""",
        """CREATE TABLE IF NOT EXISTS warnings (
            user_id  BIGINT  NOT NULL,
            guild_id BIGINT  NOT NULL,
            count    INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, guild_id)
        )""",
        """CREATE TABLE IF NOT EXISTS mod_logs (
            id           BIGINT  GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            timestamp    TEXT    NOT NULL,
            guild_id     BIGINT  NOT NULL,
            action       TEXT    NOT NULL,
            target_id    BIGINT  NOT NULL,
            moderator_id BIGINT  NOT NULL,
            reason       TEXT    NOT NULL DEFAULT 'No reason provided'
        )""",
        """CREATE TABLE IF NOT EXISTS role_thresholds (
            guild_id      BIGINT  NOT NULL,
            role_name     TEXT    NOT NULL,
            days_required INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (guild_id, role_name)
        )""",
        """CREATE TABLE IF NOT EXISTS guild_settings (
            guild_id BIGINT NOT NULL,
            key      TEXT   NOT NULL,
            value    TEXT   NOT NULL,
            PRIMARY KEY (guild_id, key)
        )""",
        """CREATE TABLE IF NOT EXISTS logs (
            id        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            timestamp TEXT   NOT NULL,
            level     TEXT   NOT NULL,
            message   TEXT   NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS reaction_roles (
            guild_id   BIGINT NOT NULL,
            message_id BIGINT NOT NULL,
            emoji      TEXT   NOT NULL,
            role_id    BIGINT NOT NULL,
            PRIMARY KEY (guild_id, message_id, emoji)
        )""",
        """CREATE TABLE IF NOT EXISTS rps_players (
            user_id BIGINT PRIMARY KEY,
            name    TEXT    NOT NULL,
            wins    INTEGER NOT NULL DEFAULT 0,
            losses  INTEGER NOT NULL DEFAULT 0,
            ties    INTEGER NOT NULL DEFAULT 0
        )""",
        """CREATE TABLE IF NOT EXISTS rps_matches (
            id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            player1_id BIGINT  NOT NULL,
            player2_id BIGINT  NOT NULL,
            winner_id  BIGINT,
            mode       TEXT    NOT NULL DEFAULT 'classic',
            best_of    INTEGER NOT NULL DEFAULT 3,
            timestamp  TEXT    NOT NULL
        )""",
        # ---- new tables replacing JSON files ----
        """CREATE TABLE IF NOT EXISTS mining_inventory (
            user_id   TEXT    NOT NULL,
            item_name TEXT    NOT NULL,
            quantity  INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, item_name)
        )""",
        """CREATE TABLE IF NOT EXISTS prohibited_words (
            guild_id BIGINT NOT NULL,
            word     TEXT   NOT NULL,
            PRIMARY KEY (guild_id, word)
        )""",
        """CREATE TABLE IF NOT EXISTS deathmatch_stats (
            user_id BIGINT  PRIMARY KEY,
            wins    INTEGER NOT NULL DEFAULT 0,
            losses  INTEGER NOT NULL DEFAULT 0
        )""",
        """CREATE TABLE IF NOT EXISTS chain_channels (
            channel_id BIGINT PRIMARY KEY,
            guild_id   BIGINT NOT NULL,
            word       TEXT   NOT NULL DEFAULT '',
            word_limit INTEGER NOT NULL DEFAULT 0,
            chain_count INTEGER NOT NULL DEFAULT 0
        )""",
        """CREATE TABLE IF NOT EXISTS counting_state (
            guild_id BIGINT PRIMARY KEY,
            state    JSONB  NOT NULL DEFAULT '{}'
        )""",
    ]
    async with pool.acquire() as conn:
        for stmt in statements:
            await conn.execute(stmt)


# ---------------------------------------------------------------------------
# Generic helpers  (same call signature as the old aiosqlite wrappers)
# ---------------------------------------------------------------------------


async def fetchone(query: str, params: tuple = ()) -> dict | None:
    row = await get().fetchrow(query, *params)
    return dict(row) if row else None


async def fetchall(query: str, params: tuple = ()) -> list[dict]:
    rows = await get().fetch(query, *params)
    return [dict(r) for r in rows]


async def execute(query: str, params: tuple = ()) -> None:
    await get().execute(query, *params)


# ---------------------------------------------------------------------------
# XP helpers
# ---------------------------------------------------------------------------


def xp_for_level(level: int) -> int:
    return 5 * (level**2) + 50 * level + 100


def level_progress(total_xp: int) -> tuple[int, int, int]:
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
        "SELECT * FROM xp WHERE user_id=$1 AND guild_id=$2", (user_id, guild_id)
    )
    return row or {
        "user_id": user_id,
        "guild_id": guild_id,
        "xp": 0,
        "level": 0,
        "messages": 0,
        "last_xp": 0,
        "coins": 0,
    }


async def add_xp(
    user_id: int, guild_id: int, amount: int, now: int
) -> tuple[int, int, bool]:
    row = await get_xp(user_id, guild_id)
    new_xp = row["xp"] + amount
    new_level, _, _ = level_progress(new_xp)
    leveled_up = new_level > row["level"]
    await execute(
        """INSERT INTO xp (user_id, guild_id, xp, level, messages, last_xp)
           VALUES ($1, $2, $3, $4, 1, $5)
           ON CONFLICT (user_id, guild_id) DO UPDATE SET
               xp=EXCLUDED.xp, level=EXCLUDED.level,
               messages=xp.messages+1, last_xp=EXCLUDED.last_xp""",
        (user_id, guild_id, new_xp, new_level, now),
    )
    return new_xp, new_level, leveled_up


# ---------------------------------------------------------------------------
# Guild settings helpers
# ---------------------------------------------------------------------------


async def get_setting(guild_id: int, key: str, default: str = "") -> str:
    row = await fetchone(
        "SELECT value FROM guild_settings WHERE guild_id=$1 AND key=$2", (guild_id, key)
    )
    return row["value"] if row else default


async def set_setting(guild_id: int, key: str, value: str) -> None:
    await execute(
        """INSERT INTO guild_settings (guild_id, key, value) VALUES ($1, $2, $3)
           ON CONFLICT (guild_id, key) DO UPDATE SET value=EXCLUDED.value""",
        (guild_id, key, value),
    )


# ---------------------------------------------------------------------------
# Role threshold helpers
# ---------------------------------------------------------------------------


async def get_role_thresholds(guild_id: int) -> list[dict]:
    return await fetchall(
        "SELECT role_name, days_required FROM role_thresholds "
        "WHERE guild_id=$1 ORDER BY days_required",
        (guild_id,),
    )


async def set_role_threshold(guild_id: int, role_name: str, days: int) -> None:
    await execute(
        """INSERT INTO role_thresholds (guild_id, role_name, days_required)
           VALUES ($1, $2, $3)
           ON CONFLICT (guild_id, role_name) DO UPDATE SET days_required=EXCLUDED.days_required""",
        (guild_id, role_name, days),
    )


async def remove_role_threshold(guild_id: int, role_name: str) -> None:
    await execute(
        "DELETE FROM role_thresholds WHERE guild_id=$1 AND role_name=$2",
        (guild_id, role_name),
    )


# ---------------------------------------------------------------------------
# Warning helpers
# ---------------------------------------------------------------------------


async def get_warnings(user_id: int, guild_id: int) -> int:
    row = await fetchone(
        "SELECT count FROM warnings WHERE user_id=$1 AND guild_id=$2",
        (user_id, guild_id),
    )
    return row["count"] if row else 0


async def add_warning(user_id: int, guild_id: int) -> int:
    count = await get_warnings(user_id, guild_id) + 1
    await execute(
        """INSERT INTO warnings (user_id, guild_id, count) VALUES ($1, $2, $3)
           ON CONFLICT (user_id, guild_id) DO UPDATE SET count=EXCLUDED.count""",
        (user_id, guild_id, count),
    )
    return count


async def clear_warnings(user_id: int, guild_id: int) -> None:
    await execute(
        "DELETE FROM warnings WHERE user_id=$1 AND guild_id=$2", (user_id, guild_id)
    )


# ---------------------------------------------------------------------------
# Mod log helpers
# ---------------------------------------------------------------------------


async def log_mod_action(
    guild_id: int,
    action: str,
    target_id: int,
    moderator_id: int,
    reason: str = "No reason provided",
) -> None:
    from datetime import datetime

    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    await execute(
        "INSERT INTO mod_logs (timestamp, guild_id, action, target_id, moderator_id, reason) "
        "VALUES ($1, $2, $3, $4, $5, $6)",
        (ts, guild_id, action, target_id, moderator_id, reason),
    )


# ---------------------------------------------------------------------------
# Coin helpers
# ---------------------------------------------------------------------------


async def get_coins(user_id: int, guild_id: int) -> int:
    row = await fetchone(
        "SELECT coins FROM xp WHERE user_id=$1 AND guild_id=$2", (user_id, guild_id)
    )
    return row["coins"] if row else 0


async def add_coins(user_id: int, guild_id: int, amount: int) -> int:
    await execute(
        """INSERT INTO xp (user_id, guild_id, coins) VALUES ($1, $2, GREATEST(0, $3))
           ON CONFLICT (user_id, guild_id) DO UPDATE SET
               coins=GREATEST(0, xp.coins + $3)""",
        (user_id, guild_id, amount),
    )
    return await get_coins(user_id, guild_id)


async def set_coins(user_id: int, guild_id: int, amount: int) -> None:
    await execute(
        """INSERT INTO xp (user_id, guild_id, coins) VALUES ($1, $2, GREATEST(0, $3))
           ON CONFLICT (user_id, guild_id) DO UPDATE SET coins=GREATEST(0, EXCLUDED.coins)""",
        (user_id, guild_id, amount),
    )


# ---------------------------------------------------------------------------
# Economy / daily helpers
# ---------------------------------------------------------------------------


async def get_economy(user_id: int, guild_id: int) -> dict:
    await execute(
        "INSERT INTO economy (user_id, guild_id) VALUES ($1, $2) ON CONFLICT DO NOTHING",
        (user_id, guild_id),
    )
    row = await fetchone(
        "SELECT * FROM economy WHERE user_id=$1 AND guild_id=$2", (user_id, guild_id)
    )
    return dict(row)


async def set_economy(user_id: int, guild_id: int, **kwargs) -> None:
    allowed = {"last_daily", "daily_streak", "daily_count", "last_worked"}
    cols = {k: v for k, v in kwargs.items() if k in allowed}
    if not cols:
        return
    keys = list(cols)
    sets = ", ".join(f"{k}=${i + 1}" for i, k in enumerate(keys))
    n = len(keys)
    await execute(
        f"UPDATE economy SET {sets} WHERE user_id=${n + 1} AND guild_id=${n + 2}",
        (*cols.values(), user_id, guild_id),
    )


# ---------------------------------------------------------------------------
# Job progress helpers
# ---------------------------------------------------------------------------


async def get_job_times(user_id: int, guild_id: int, job_name: str) -> int:
    row = await fetchone(
        "SELECT times_worked FROM job_progress WHERE user_id=$1 AND guild_id=$2 AND job_name=$3",
        (user_id, guild_id, job_name),
    )
    return row["times_worked"] if row else 0


async def increment_job(user_id: int, guild_id: int, job_name: str) -> int:
    await execute(
        """INSERT INTO job_progress (user_id, guild_id, job_name, times_worked)
           VALUES ($1, $2, $3, 1)
           ON CONFLICT (user_id, guild_id, job_name)
           DO UPDATE SET times_worked=job_progress.times_worked + 1""",
        (user_id, guild_id, job_name),
    )
    return await get_job_times(user_id, guild_id, job_name)


# ---------------------------------------------------------------------------
# Inventory helpers
# ---------------------------------------------------------------------------


async def get_inventory(user_id: int, guild_id: int) -> dict[str, int]:
    rows = await fetchall(
        "SELECT item_name, quantity FROM inventory WHERE user_id=$1 AND guild_id=$2",
        (user_id, guild_id),
    )
    return {r["item_name"]: r["quantity"] for r in rows}


async def add_item(
    user_id: int, guild_id: int, item_name: str, quantity: int = 1
) -> None:
    await execute(
        """INSERT INTO inventory (user_id, guild_id, item_name, quantity)
           VALUES ($1, $2, $3, $4)
           ON CONFLICT (user_id, guild_id, item_name)
           DO UPDATE SET quantity=inventory.quantity + $4""",
        (user_id, guild_id, item_name, quantity),
    )


async def has_item(user_id: int, guild_id: int, item_name: str) -> bool:
    row = await fetchone(
        "SELECT quantity FROM inventory WHERE user_id=$1 AND guild_id=$2 AND item_name=$3",
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
           VALUES ($1, $2, $3, $4)
           ON CONFLICT (guild_id, message_id, emoji) DO UPDATE SET role_id=EXCLUDED.role_id""",
        (guild_id, message_id, emoji, role_id),
    )


async def remove_reaction_role(guild_id: int, message_id: int, emoji: str) -> None:
    await execute(
        "DELETE FROM reaction_roles WHERE guild_id=$1 AND message_id=$2 AND emoji=$3",
        (guild_id, message_id, emoji),
    )


async def get_reaction_role(guild_id: int, message_id: int, emoji: str) -> int | None:
    row = await fetchone(
        "SELECT role_id FROM reaction_roles WHERE guild_id=$1 AND message_id=$2 AND emoji=$3",
        (guild_id, message_id, emoji),
    )
    return row["role_id"] if row else None


async def get_all_reaction_roles(guild_id: int) -> list[dict]:
    return await fetchall(
        "SELECT message_id, emoji, role_id FROM reaction_roles WHERE guild_id=$1",
        (guild_id,),
    )


# ---------------------------------------------------------------------------
# RPS stats helpers
# ---------------------------------------------------------------------------


async def rps_ensure_player(user_id: int, name: str) -> None:
    await execute(
        "INSERT INTO rps_players (user_id, name) VALUES ($1, $2) ON CONFLICT DO NOTHING",
        (user_id, name),
    )


async def rps_update_stat(user_id: int, result: str) -> None:
    col = {"win": "wins", "loss": "losses", "tie": "ties"}.get(result)
    if col:
        await execute(
            f"UPDATE rps_players SET {col}={col}+1 WHERE user_id=$1", (user_id,)
        )


async def rps_get_leaderboard() -> list[dict]:
    return await fetchall(
        "SELECT name, wins, losses, ties FROM rps_players ORDER BY wins DESC LIMIT 15"
    )


# ---------------------------------------------------------------------------
# Mining inventory helpers  (replaces mining_data.json)
# ---------------------------------------------------------------------------


async def get_mining_inventory(user_id: str) -> dict[str, int]:
    rows = await fetchall(
        "SELECT item_name, quantity FROM mining_inventory WHERE user_id=$1", (user_id,)
    )
    return {r["item_name"]: r["quantity"] for r in rows}


async def update_mining_item(user_id: str, item_name: str, delta: int) -> None:
    """Add or subtract *delta* of *item_name* for *user_id*. Clamps to 0."""
    await execute(
        """INSERT INTO mining_inventory (user_id, item_name, quantity)
           VALUES ($1, $2, GREATEST(0, $3))
           ON CONFLICT (user_id, item_name)
           DO UPDATE SET quantity=GREATEST(0, mining_inventory.quantity + $3)""",
        (user_id, item_name, delta),
    )


async def set_mining_inventory(user_id: str, inventory: dict[str, int]) -> None:
    """Overwrite the entire inventory for a user (used for admin reset)."""
    pool = get()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM mining_inventory WHERE user_id=$1", user_id)
        if inventory:
            await conn.executemany(
                "INSERT INTO mining_inventory (user_id, item_name, quantity) VALUES ($1, $2, $3)",
                [(user_id, k, v) for k, v in inventory.items() if v > 0],
            )


async def get_all_mining_totals() -> list[tuple[str, int]]:
    """Return [(user_id, total_items)] sorted descending — for leaderboard."""
    rows = await fetchall(
        "SELECT user_id, SUM(quantity) AS total FROM mining_inventory GROUP BY user_id ORDER BY total DESC LIMIT 10"
    )
    return [(r["user_id"], r["total"]) for r in rows]


# ---------------------------------------------------------------------------
# Prohibited word helpers  (replaces prohibited_words.json)
# ---------------------------------------------------------------------------


async def get_prohibited_words(guild_id: int) -> list[str]:
    rows = await fetchall(
        "SELECT word FROM prohibited_words WHERE guild_id=$1", (guild_id,)
    )
    return [r["word"] for r in rows]


async def add_prohibited_word(guild_id: int, word: str) -> bool:
    """Returns True if newly added, False if already present."""
    result = await get().execute(
        "INSERT INTO prohibited_words (guild_id, word) VALUES ($1, $2) ON CONFLICT DO NOTHING",
        guild_id,
        word,
    )
    return result == "INSERT 0 1"


async def remove_prohibited_word(guild_id: int, word: str) -> bool:
    """Returns True if removed, False if not found."""
    result = await get().execute(
        "DELETE FROM prohibited_words WHERE guild_id=$1 AND word=$2", guild_id, word
    )
    return result == "DELETE 1"


# ---------------------------------------------------------------------------
# Deathmatch helpers  (replaces leaderboard.json)
# ---------------------------------------------------------------------------


async def get_deathmatch_stats(user_id: int) -> dict:
    row = await fetchone(
        "SELECT wins, losses FROM deathmatch_stats WHERE user_id=$1", (user_id,)
    )
    return row or {"wins": 0, "losses": 0}


async def update_deathmatch(winner_id: int, loser_id: int) -> None:
    pool = get()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO deathmatch_stats (user_id, wins) VALUES ($1, 1)
               ON CONFLICT (user_id) DO UPDATE SET wins=deathmatch_stats.wins+1""",
            winner_id,
        )
        await conn.execute(
            """INSERT INTO deathmatch_stats (user_id, losses) VALUES ($1, 1)
               ON CONFLICT (user_id) DO UPDATE SET losses=deathmatch_stats.losses+1""",
            loser_id,
        )


async def get_deathmatch_leaderboard() -> list[dict]:
    return await fetchall(
        "SELECT user_id, wins, losses FROM deathmatch_stats ORDER BY wins DESC LIMIT 15"
    )


# ---------------------------------------------------------------------------
# Chain channel helpers  (replaces chain_data.json)
# ---------------------------------------------------------------------------


async def get_chain_channel(channel_id: int) -> dict | None:
    return await fetchone(
        "SELECT word, word_limit, chain_count FROM chain_channels WHERE channel_id=$1",
        (channel_id,),
    )


async def set_chain_channel(
    channel_id: int, guild_id: int, word: str, limit: int = 0
) -> None:
    await execute(
        """INSERT INTO chain_channels (channel_id, guild_id, word, word_limit, chain_count)
           VALUES ($1, $2, $3, $4, 0)
           ON CONFLICT (channel_id) DO UPDATE SET word=EXCLUDED.word, word_limit=EXCLUDED.word_limit""",
        (channel_id, guild_id, word, limit),
    )


async def delete_chain_channel(channel_id: int) -> None:
    await execute("DELETE FROM chain_channels WHERE channel_id=$1", (channel_id,))


async def set_chain_limit(channel_id: int, limit: int) -> None:
    await execute(
        "UPDATE chain_channels SET word_limit=$1 WHERE channel_id=$2",
        (limit, channel_id),
    )


async def increment_chain_count(channel_id: int) -> int:
    row = await fetchone(
        "UPDATE chain_channels SET chain_count=chain_count+1 WHERE channel_id=$1 RETURNING chain_count",
        (channel_id,),
    )
    return row["chain_count"] if row else 0


async def get_all_chain_channels(guild_id: int) -> list[dict]:
    return await fetchall(
        "SELECT channel_id, word, word_limit, chain_count FROM chain_channels WHERE guild_id=$1",
        (guild_id,),
    )


# ---------------------------------------------------------------------------
# Counting state helpers  (replaces count_data.json)
# ---------------------------------------------------------------------------


async def get_counting_state(guild_id: int) -> dict:
    row = await fetchone(
        "SELECT state FROM counting_state WHERE guild_id=$1", (guild_id,)
    )
    return row["state"] if row else {}


async def set_counting_state(guild_id: int, state: dict) -> None:
    await execute(
        """INSERT INTO counting_state (guild_id, state) VALUES ($1, $2::jsonb)
           ON CONFLICT (guild_id) DO UPDATE SET state=EXCLUDED.state""",
        (guild_id, state),
    )
