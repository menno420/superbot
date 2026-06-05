"""Schema bootstrap and migration runner.

Runs at startup from :func:`utils.db.pool.init`.  Three steps:

  1. ``ensure_migrations_table``  — creates ``schema_migrations`` if absent
  2. ``create_tables``            — idempotent CREATE TABLE IF NOT EXISTS
  3. ``run_migrations``           — applies every .sql file in
     ``disbot/migrations/`` that has not been recorded yet, under a
     Postgres advisory lock so concurrent bot instances cannot race.

The migration ordering MUST remain forward-only and additive.  Existing
migrations are never edited; new schema changes ship as new files.
"""

from __future__ import annotations

import logging
import os
import re
import time
from collections.abc import Iterable

from utils.db import pool

logger = logging.getLogger("bot.db.migrations")

_MIGRATIONS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "migrations",
)

# Stable 64-bit key for pg_advisory_lock — "superbot" interpreted as int.
_MIGRATION_ADVISORY_LOCK = 0x73757065_72626F74

# NNN_<snake_name>.sql — the contract pinned by
# tests/unit/db/test_migrations_structure.py.  group(1)=version, group(2)=name.
_MIGRATION_NAME_RE = re.compile(r"^(\d{3})_([a-z][a-z0-9_]*)\.sql$")


class MigrationError(RuntimeError):
    """The migrations directory is structurally invalid.

    Raised at startup *before* any migration runs, so a malformed set fails fast
    instead of silently skipping a file (RC-6).  Historically the runner
    ``int(filename.split("_")[0])``-parsed names and *skipped* anything it could
    not parse, and a duplicate leading version meant the second file was silently
    never applied once the first was recorded.
    """


def _ordered_migration_versions(filenames: Iterable[str]) -> list[tuple[int, str]]:
    """Validate ``*.sql`` migration filenames; return ``(version, filename)``
    pairs sorted by filename.

    Raises :class:`MigrationError` when a ``.sql`` file does not match
    ``NNN_<snake_name>.sql`` or when two files share a leading version (the second
    would never apply once the first is recorded — RC-6).  Non-``.sql`` files are
    ignored.
    """
    seen: dict[int, str] = {}
    ordered: list[tuple[int, str]] = []
    for filename in sorted(filenames):
        if not filename.endswith(".sql"):
            continue
        match = _MIGRATION_NAME_RE.match(filename)
        if match is None:
            raise MigrationError(
                f"Migration file does not match NNN_<snake_name>.sql: {filename!r}",
            )
        version = int(match.group(1))
        if version in seen:
            raise MigrationError(
                f"Duplicate migration version {version:03d}: "
                f"{seen[version]!r} and {filename!r} — the second would never "
                "apply (forward-only; rename, do not duplicate).",
            )
        seen[version] = filename
        ordered.append((version, filename))
    return ordered


def migration_versions_on_disk() -> set[int]:
    """Return the set of migration versions present as ``NNN_*.sql`` files.

    Used by the diagnostic schema check to report "migrations applied N/N"
    against the migration chain (the authoritative schema source) instead of a
    hand-maintained expected-table list that silently goes stale as migrations
    add tables.
    """
    if not os.path.isdir(_MIGRATIONS_DIR):
        return set()
    return {
        version
        for version, _ in _ordered_migration_versions(os.listdir(_MIGRATIONS_DIR))
    }


async def ensure_migrations_table() -> None:
    await pool.get().execute(
        """CREATE TABLE IF NOT EXISTS schema_migrations (
            version     INTEGER PRIMARY KEY,
            applied_at  BIGINT  NOT NULL,
            description TEXT    NOT NULL
        )""",
    )


async def run_migrations() -> None:
    """Apply pending migrations under a PostgreSQL advisory lock.

    The session-scoped advisory lock ensures concurrent bot instances
    starting simultaneously (blue-green deploy, horizontal scaling) do
    not race to apply the same migration.  Only one process holds the
    lock; others wait until it's released before checking applied
    versions.
    """
    if not os.path.isdir(_MIGRATIONS_DIR):
        return

    async with pool.get().acquire() as conn:
        await conn.execute("SELECT pg_advisory_lock($1)", _MIGRATION_ADVISORY_LOCK)
        try:
            applied = {
                r["version"]
                for r in await conn.fetch(
                    "SELECT version FROM schema_migrations ORDER BY version",
                )
            }
            for version, filename in _ordered_migration_versions(
                os.listdir(_MIGRATIONS_DIR),
            ):
                if version in applied:
                    continue
                path = os.path.join(_MIGRATIONS_DIR, filename)
                with open(path, encoding="utf-8") as f:
                    sql = f.read()
                # Strip the validated "NNN_" prefix + ".sql" suffix for a human
                # description (the old slice mishandled the zero-padded version
                # and emitted e.g. "1 initial schema").
                description = filename[4:].removesuffix(".sql").replace("_", " ")
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
                        "Migration %03d failed: %s",
                        version,
                        exc,
                        exc_info=True,
                    )
                    raise
        finally:
            await conn.execute(
                "SELECT pg_advisory_unlock($1)",
                _MIGRATION_ADVISORY_LOCK,
            )


async def create_tables() -> None:
    """Idempotent CREATE TABLE IF NOT EXISTS pass for the pre-migration schema.

    The original schema (everything before migration 001) is reproduced
    here so a fresh database can be initialised without manually
    running migrations.  Existing migrations are layered on top.
    """
    p = pool.get()
    statements = [
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
        # PR C1 — ``rps_matches`` removed.  It was created here for an
        # unshipped match-history feature and had zero CRUD callers.
        # Migration 019 drops the table on existing deploys; fresh
        # installs never create it.
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
    async with p.acquire() as conn:
        for stmt in statements:
            await conn.execute(stmt)
