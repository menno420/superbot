from __future__ import annotations

import json
import logging
import os
import time

import asyncpg

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
    await _ensure_migrations_table()
    await _create_tables()
    await _run_migrations()
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


_MIGRATIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "migrations")


async def _ensure_migrations_table() -> None:
    await get().execute("""CREATE TABLE IF NOT EXISTS schema_migrations (
            version     INTEGER PRIMARY KEY,
            applied_at  BIGINT  NOT NULL,
            description TEXT    NOT NULL
        )""")


_MIGRATION_ADVISORY_LOCK = 0x73757065_72626F74  # "superbot" as 64-bit int


async def _run_migrations() -> None:
    """Run pending migrations under a PostgreSQL advisory lock.

    The advisory lock (session-level) ensures that concurrent bot instances
    starting simultaneously (e.g. blue-green deploy, horizontal scaling) do
    not race to apply the same migration. Only one process holds the lock at a
    time; others wait until the lock is released before checking applied versions.
    """
    if not os.path.isdir(_MIGRATIONS_DIR):
        return

    async with get().acquire() as conn:
        # Acquire session-scoped advisory lock — blocks until available.
        await conn.execute("SELECT pg_advisory_lock($1)", _MIGRATION_ADVISORY_LOCK)
        try:
            applied = {
                r["version"]
                for r in await conn.fetch(
                    "SELECT version FROM schema_migrations ORDER BY version"
                )
            }
            migration_files = sorted(
                f for f in os.listdir(_MIGRATIONS_DIR) if f.endswith(".sql")
            )
            for filename in migration_files:
                try:
                    version = int(filename.split("_")[0])
                except (ValueError, IndexError):
                    logger.warning(
                        "Migration file with unexpected name skipped: %s", filename
                    )
                    continue
                if version in applied:
                    continue
                path = os.path.join(_MIGRATIONS_DIR, filename)
                with open(path, encoding="utf-8") as f:
                    sql = f.read()
                description = (
                    filename[len(str(version)) + 1 :]
                    .replace("_", " ")
                    .removesuffix(".sql")
                )
                try:
                    async with conn.transaction():
                        await conn.execute(sql)
                        await conn.execute(
                            "INSERT INTO schema_migrations "
                            "(version, applied_at, description) VALUES ($1, $2, $3)",
                            version,
                            int(time.time()),
                            description,
                        )
                    logger.info("Applied migration %03d: %s", version, description)
                except Exception as exc:
                    logger.error(
                        "Migration %03d failed: %s", version, exc, exc_info=True
                    )
                    raise
        finally:
            await conn.execute(
                "SELECT pg_advisory_unlock($1)", _MIGRATION_ADVISORY_LOCK
            )


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
    # Atomic increment — avoids read-modify-write race under concurrent messages.
    row = await get().fetchrow(
        """INSERT INTO xp (user_id, guild_id, xp, level, messages, last_xp)
           VALUES ($1, $2, $3, 0, 1, $4)
           ON CONFLICT (user_id, guild_id) DO UPDATE SET
               xp       = xp.xp + $3,
               messages = xp.messages + 1,
               last_xp  = $4
           RETURNING xp, level""",
        user_id,
        guild_id,
        amount,
        now,
    )
    new_xp = row["xp"]
    old_level = row["level"]
    new_level, _, _ = level_progress(new_xp)
    leveled_up = new_level > old_level
    if leveled_up:
        # Monotonic update: only advances level, never regresses.
        await execute(
            "UPDATE xp SET level=$3 WHERE user_id=$1 AND guild_id=$2 AND level < $3",
            (user_id, guild_id, new_level),
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
        "SELECT role_name, days_required, level_required, xp_auto_assign "
        "FROM role_thresholds WHERE guild_id=$1 ORDER BY days_required",
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


async def get_xp_threshold_roles(guild_id: int) -> list[dict]:
    """Return rows with xp_auto_assign=TRUE and a configured level_required."""
    return await fetchall(
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

    If no row exists for (guild_id, role_name), inserts one with days_required=0.
    Only updates the XP columns; existing days_required is preserved on conflict.
    """
    await execute(
        """INSERT INTO role_thresholds
               (guild_id, role_name, days_required, level_required, xp_auto_assign)
           VALUES ($1, $2, 0, $3, $4)
           ON CONFLICT (guild_id, role_name) DO UPDATE SET
               level_required = EXCLUDED.level_required,
               xp_auto_assign = EXCLUDED.xp_auto_assign""",
        (guild_id, role_name, level_required, auto_assign),
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
    # Atomic increment — avoids read-modify-write race under concurrent mod actions.
    row = await get().fetchrow(
        """INSERT INTO warnings (user_id, guild_id, count) VALUES ($1, $2, 1)
           ON CONFLICT (user_id, guild_id) DO UPDATE SET count = warnings.count + 1
           RETURNING count""",
        user_id,
        guild_id,
    )
    return row["count"]


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


async def get_mod_logs(target_id: int, guild_id: int, limit: int = 10) -> list[dict]:
    return await fetchall(
        "SELECT action, timestamp, moderator_id, reason FROM mod_logs "
        "WHERE target_id=$1 AND guild_id=$2 ORDER BY id DESC LIMIT $3",
        (target_id, guild_id, limit),
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


async def claim_daily_if_ready(
    user_id: int, guild_id: int, now: int, cooldown_seconds: int
) -> bool:
    """Atomically claim daily reward.

    Updates last_daily only when the cooldown has elapsed.
    Returns True if the claim succeeded, False if the user is still on cooldown.
    Using a conditional UPDATE eliminates the read-then-write race that allowed
    concurrent !daily invocations to both succeed.
    """
    result = await get().execute(
        """UPDATE economy SET last_daily=$3
           WHERE user_id=$1 AND guild_id=$2
             AND ($3 - last_daily) >= $4""",
        user_id,
        guild_id,
        now,
        cooldown_seconds,
    )
    return result == "UPDATE 1"


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


async def rps_ensure_player(user_id: int, name: str, guild_id: int = 0) -> None:
    await execute(
        "INSERT INTO rps_players (user_id, guild_id, name) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING",
        (user_id, guild_id, name),
    )


async def rps_update_stat(user_id: int, result: str, guild_id: int = 0) -> None:
    col = {"win": "wins", "loss": "losses", "tie": "ties"}.get(result)
    if col:
        await execute(
            f"UPDATE rps_players SET {col}={col}+1 WHERE user_id=$1 AND guild_id=$2",
            (user_id, guild_id),
        )


async def rps_get_leaderboard(guild_id: int = 0) -> list[dict]:
    return await fetchall(
        "SELECT name, wins, losses, ties FROM rps_players WHERE guild_id=$1 ORDER BY wins DESC LIMIT 15",
        (guild_id,),
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


async def get_deathmatch_stats(user_id: int, guild_id: int = 0) -> dict:
    row = await fetchone(
        "SELECT wins, losses FROM deathmatch_stats WHERE user_id=$1 AND guild_id=$2",
        (user_id, guild_id),
    )
    return row or {"wins": 0, "losses": 0}


async def update_deathmatch(winner_id: int, loser_id: int, guild_id: int = 0) -> None:
    # Both statements are wrapped in a single transaction so a failure on the
    # second statement does not leave the winner's record updated without the
    # loser's record being updated.
    pool = get()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                """INSERT INTO deathmatch_stats (user_id, guild_id, wins) VALUES ($1, $2, 1)
                   ON CONFLICT (user_id, guild_id) DO UPDATE SET wins=deathmatch_stats.wins+1""",
                winner_id,
                guild_id,
            )
            await conn.execute(
                """INSERT INTO deathmatch_stats (user_id, guild_id, losses) VALUES ($1, $2, 1)
                   ON CONFLICT (user_id, guild_id) DO UPDATE SET losses=deathmatch_stats.losses+1""",
                loser_id,
                guild_id,
            )


async def get_deathmatch_leaderboard(guild_id: int = 0) -> list[dict]:
    return await fetchall(
        "SELECT user_id, wins, losses FROM deathmatch_stats WHERE guild_id=$1 ORDER BY wins DESC LIMIT 15",
        (guild_id,),
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


# ---------------------------------------------------------------------------
# Governance: subsystem_visibility
# ---------------------------------------------------------------------------


async def get_subsystem_visibility(
    guild_id: int, scope_type: str, scope_id: int
) -> dict[str, bool | None]:
    """Return subsystem→enabled mapping for a scope. Missing rows = not in dict."""
    rows = await get().fetch(
        "SELECT subsystem, enabled FROM subsystem_visibility"
        " WHERE guild_id=$1 AND scope_type=$2 AND scope_id=$3",
        guild_id,
        scope_type,
        scope_id,
    )
    return {r["subsystem"]: r["enabled"] for r in rows}


async def get_all_visibility_for_guild(guild_id: int):
    """Fetch all visibility rows for a guild (all scopes) in one query."""
    return await get().fetch(
        "SELECT scope_type, scope_id, subsystem, enabled"
        " FROM subsystem_visibility WHERE guild_id=$1",
        guild_id,
    )


async def get_visibility_override(
    guild_id: int,
    scope_type: str,
    scope_id: int,
    subsystem: str,
) -> bool | None:
    """Return the current enabled value for a specific visibility override, or None.

    Used by GovernanceMutationPipeline to read the old value before writing,
    so the governance audit log captures both before and after state.
    """
    row = await get().fetchrow(
        """SELECT enabled FROM subsystem_visibility
           WHERE guild_id = $1 AND scope_type = $2
             AND scope_id = $3 AND subsystem = $4""",
        guild_id,
        scope_type,
        scope_id,
        subsystem,
    )
    return bool(row["enabled"]) if row is not None and row["enabled"] is not None else None


async def set_subsystem_visibility(
    guild_id: int,
    scope_type: str,
    scope_id: int,
    subsystem: str,
    enabled: bool | None,
) -> None:
    """Upsert a visibility override. enabled=None clears the override (inherit)."""
    await get().execute(
        """INSERT INTO subsystem_visibility
               (guild_id, scope_type, scope_id, subsystem, enabled)
           VALUES ($1, $2, $3, $4, $5)
           ON CONFLICT (guild_id, scope_type, scope_id, subsystem)
           DO UPDATE SET enabled = EXCLUDED.enabled""",
        guild_id,
        scope_type,
        scope_id,
        subsystem,
        enabled,
    )


# ---------------------------------------------------------------------------
# Governance: cleanup_policies
# ---------------------------------------------------------------------------


async def get_cleanup_policy(
    guild_id: int, scope_type: str, scope_id: int
) -> dict | None:
    """Return cleanup policy for a scope, or None if no row exists."""
    row = await get().fetchrow(
        "SELECT delete_invalid_commands, delete_failed_commands, delete_after_seconds"
        " FROM cleanup_policies WHERE guild_id=$1 AND scope_type=$2 AND scope_id=$3",
        guild_id,
        scope_type,
        scope_id,
    )
    return dict(row) if row else None


async def get_all_cleanup_for_guild(guild_id: int) -> list[dict]:
    """Fetch all cleanup policy rows for a guild (all scopes)."""
    rows = await get().fetch(
        "SELECT scope_type, scope_id, delete_invalid_commands,"
        " delete_failed_commands, delete_after_seconds"
        " FROM cleanup_policies WHERE guild_id=$1",
        guild_id,
    )
    return [dict(r) for r in rows]


async def set_cleanup_policy(
    guild_id: int,
    scope_type: str,
    scope_id: int,
    delete_invalid_commands: bool = True,
    delete_failed_commands: bool = True,
    delete_after_seconds: int = 5,
) -> None:
    await get().execute(
        """INSERT INTO cleanup_policies
               (guild_id, scope_type, scope_id,
                delete_invalid_commands, delete_failed_commands, delete_after_seconds)
           VALUES ($1, $2, $3, $4, $5, $6)
           ON CONFLICT (guild_id, scope_type, scope_id)
           DO UPDATE SET
               delete_invalid_commands = EXCLUDED.delete_invalid_commands,
               delete_failed_commands  = EXCLUDED.delete_failed_commands,
               delete_after_seconds    = EXCLUDED.delete_after_seconds""",
        guild_id,
        scope_type,
        scope_id,
        delete_invalid_commands,
        delete_failed_commands,
        delete_after_seconds,
    )


# ---------------------------------------------------------------------------
# Runtime session helpers
# ---------------------------------------------------------------------------


async def get_or_create_session(
    user_id: int,
    guild_id: int,
    channel_id: int,
    subsystem: str,
) -> dict:
    """Return existing session or create a new one (upsert on unique key).

    Returns the session row as a dict with keys:
    session_id, user_id, guild_id, channel_id, subsystem,
    created_at, last_active_at, metadata.
    """
    row = await get().fetchrow(
        """INSERT INTO runtime_sessions
               (user_id, guild_id, channel_id, subsystem)
           VALUES ($1, $2, $3, $4)
           ON CONFLICT (user_id, channel_id, subsystem) DO UPDATE
               SET last_active_at = NOW()
           RETURNING *""",
        user_id,
        guild_id,
        channel_id,
        subsystem,
    )
    return dict(row)


async def touch_session(session_id: str) -> None:
    """Update last_active_at for an existing session."""
    await get().execute(
        "UPDATE runtime_sessions SET last_active_at = NOW() WHERE session_id = $1",
        session_id,
    )


async def get_session(session_id: str) -> dict | None:
    """Fetch a session by its UUID, or None if it does not exist."""
    row = await get().fetchrow(
        "SELECT * FROM runtime_sessions WHERE session_id = $1", session_id
    )
    return dict(row) if row else None


async def delete_session(session_id: str) -> None:
    """Delete a session and cascade to its state rows."""
    await get().execute(
        "DELETE FROM runtime_sessions WHERE session_id = $1", session_id
    )


async def delete_sessions_for_subsystem(guild_id: int, subsystem: str) -> list[str]:
    """Delete all sessions for a subsystem in a guild.

    Returns the list of deleted session_ids (for downstream cleanup).
    """
    rows = await get().fetch(
        """DELETE FROM runtime_sessions
           WHERE guild_id = $1 AND subsystem = $2
           RETURNING session_id::text""",
        guild_id,
        subsystem,
    )
    return [r["session_id"] for r in rows]


async def delete_sessions_for_scope(
    guild_id: int,
    subsystem: str,
    channel_id: int | None = None,
) -> list[str]:
    """Delete sessions for a subsystem, optionally scoped to a specific channel.

    Used for scope-aware invalidation: a channel-scoped governance change
    should only invalidate sessions in that channel, not guild-wide.
    Falls back to guild-wide deletion when channel_id is None.

    Returns the list of deleted session_ids.
    """
    if channel_id is not None:
        rows = await get().fetch(
            """DELETE FROM runtime_sessions
               WHERE guild_id = $1 AND subsystem = $2 AND channel_id = $3
               RETURNING session_id::text""",
            guild_id,
            subsystem,
            channel_id,
        )
    else:
        rows = await get().fetch(
            """DELETE FROM runtime_sessions
               WHERE guild_id = $1 AND subsystem = $2
               RETURNING session_id::text""",
            guild_id,
            subsystem,
        )
    return [r["session_id"] for r in rows]


def _maybe_decode_legacy(value: object) -> object:
    """Transparently decode double-encoded legacy session state values.

    Before migration 012 was applied, set_session_state() manually called
    json.dumps() before asyncpg, so JSONB rows contain a JSON string wrapping
    the real payload.  After the migration repairs existing rows this shim is
    a no-op (asyncpg decodes JSONB objects directly into Python dicts).
    """
    if isinstance(value, str):
        try:
            import json as _json

            return _json.loads(value)
        except (ValueError, TypeError):
            return value
    return value


async def get_session_state(session_id: str, key: str) -> object | None:
    """Read a single typed value from session state (returns Python object or None)."""
    row = await get().fetchrow(
        "SELECT value FROM runtime_session_state WHERE session_id = $1 AND key = $2",
        session_id,
        key,
    )
    return _maybe_decode_legacy(row["value"]) if row else None


async def set_session_state(session_id: str, key: str, value: object) -> None:
    """Write a single typed value to session state (upsert)."""
    await get().execute(
        """INSERT INTO runtime_session_state (session_id, key, value)
           VALUES ($1, $2, $3)
           ON CONFLICT (session_id, key) DO UPDATE SET value = EXCLUDED.value""",
        session_id,
        key,
        value,  # asyncpg JSONB codec handles encoding via _init_conn
    )


async def delete_session_state(session_id: str, key: str) -> None:
    """Remove a single state key from a session."""
    await get().execute(
        "DELETE FROM runtime_session_state WHERE session_id = $1 AND key = $2",
        session_id,
        key,
    )


async def get_all_session_state(session_id: str) -> dict:
    """Return all key-value state for a session as a plain dict."""
    rows = await get().fetch(
        "SELECT key, value FROM runtime_session_state WHERE session_id = $1",
        session_id,
    )
    return {r["key"]: _maybe_decode_legacy(r["value"]) for r in rows}


async def delete_guild_session_state(guild_id: int) -> None:
    """Purge all session state for every session in a guild (cache invalidation)."""
    await get().execute(
        """DELETE FROM runtime_session_state
           WHERE session_id IN (
               SELECT session_id FROM runtime_sessions WHERE guild_id = $1
           )""",
        guild_id,
    )


async def write_governance_audit(
    guild_id: int,
    actor_id: int,
    action: str,
    scope_type: str | None,
    scope_id: int | None,
    subsystem: str | None,
    new_value: dict | None,
    old_value: dict | None = None,
    mutation_id: str | None = None,
) -> None:
    """Append a row to governance_audit_log (fire-and-forget; non-blocking)."""
    await get().execute(
        """INSERT INTO governance_audit_log
               (guild_id, actor_id, action, scope_type, scope_id,
                subsystem, old_value, new_value)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
        guild_id,
        actor_id,
        action,
        scope_type,
        scope_id,
        subsystem,
        old_value,   # asyncpg JSONB codec handles encoding via _init_conn
        new_value,   # asyncpg JSONB codec handles encoding via _init_conn
    )


# ---------------------------------------------------------------------------
# Panel anchor helpers
# ---------------------------------------------------------------------------


async def get_panel_anchor(
    user_id: int, channel_id: int, subsystem: str
) -> dict | None:
    """Return the active anchor for (user, channel, subsystem), or None."""
    row = await get().fetchrow(
        """SELECT * FROM panel_anchors
           WHERE user_id = $1 AND channel_id = $2 AND subsystem = $3
             AND NOT is_stale""",
        user_id,
        channel_id,
        subsystem,
    )
    return dict(row) if row else None


async def upsert_panel_anchor(
    user_id: int,
    guild_id: int,
    channel_id: int,
    subsystem: str,
    message_id: int,
) -> dict:
    """Create or replace the anchor for (user, channel, subsystem).

    Uses ON CONFLICT to replace the message_id when the user opens a new panel
    in the same channel (old message was deleted or unreachable).
    """
    row = await get().fetchrow(
        """INSERT INTO panel_anchors
               (user_id, guild_id, channel_id, subsystem, message_id)
           VALUES ($1, $2, $3, $4, $5)
           ON CONFLICT (user_id, channel_id, subsystem) DO UPDATE
               SET message_id      = EXCLUDED.message_id,
                   is_stale        = FALSE,
                   last_updated_at = NOW()
           RETURNING *""",
        user_id,
        guild_id,
        channel_id,
        subsystem,
        message_id,
    )
    return dict(row)


async def get_panel_anchor_by_message(message_id: int) -> dict | None:
    """Return the anchor for a specific Discord message_id, or None."""
    row = await get().fetchrow(
        "SELECT * FROM panel_anchors WHERE message_id = $1 AND NOT is_stale",
        message_id,
    )
    return dict(row) if row else None


async def mark_panel_anchor_stale(anchor_id: str) -> None:
    """Mark an anchor as stale (its Discord message was deleted)."""
    await get().execute(
        "UPDATE panel_anchors SET is_stale = TRUE WHERE anchor_id = $1",
        anchor_id,
    )


async def get_all_active_panel_anchors() -> list[dict]:
    """Return all non-stale anchors for restart recovery."""
    rows = await get().fetch(
        "SELECT * FROM panel_anchors WHERE NOT is_stale ORDER BY last_updated_at DESC"
    )
    return [dict(r) for r in rows]


async def delete_stale_panel_anchors() -> int:
    """Delete anchors marked is_stale=TRUE. Returns count removed."""
    result = await get().execute("DELETE FROM panel_anchors WHERE is_stale = TRUE")
    try:
        return int(result.split()[-1])
    except (IndexError, ValueError):
        return 0


async def delete_guild_panel_anchors(guild_id: int) -> int:
    """Delete every panel anchor for a guild. Returns count removed.

    Called from guild_lifecycle.teardown() so departed guilds leave no orphan
    rows in panel_anchors.  Index on (guild_id, subsystem) supports this query.
    """
    result = await get().execute(
        "DELETE FROM panel_anchors WHERE guild_id = $1", guild_id
    )
    try:
        return int(result.split()[-1])
    except (IndexError, ValueError):
        return 0


async def get_user_subsystem_anchors(
    user_id: int, guild_id: int, subsystem: str
) -> list[dict]:
    """Return all active panel anchors for a user+guild+subsystem combination."""
    rows = await get().fetch(
        """
        SELECT anchor_id, user_id, guild_id, channel_id, message_id, subsystem
        FROM panel_anchors
        WHERE user_id = $1 AND guild_id = $2 AND subsystem = $3 AND NOT is_stale
        """,
        user_id,
        guild_id,
        subsystem,
    )
    return [dict(r) for r in rows]


async def delete_expired_sessions(cutoff_epoch: float) -> int:
    """Delete sessions whose last_active_at is older than cutoff. Returns count."""
    from datetime import datetime, timezone

    cutoff_dt = datetime.fromtimestamp(cutoff_epoch, tz=timezone.utc)
    result = await get().execute(
        "DELETE FROM runtime_sessions WHERE last_active_at < $1",
        cutoff_dt,
    )
    try:
        return int(result.split()[-1])
    except (IndexError, ValueError):
        return 0


async def count_active_sessions() -> int:
    """Return the current number of runtime sessions in the DB."""
    row = await get().fetchrow("SELECT COUNT(*) AS n FROM runtime_sessions")
    return int(row["n"]) if row else 0
