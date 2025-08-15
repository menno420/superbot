"""Async SQLite database service with migrations."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterable, Sequence
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import aiosqlite

from config import get_settings
from .errors import MigrationError
from .logging_service import log_error, log_info


class DBService:
    """Central asynchronous database service."""

    _conn: aiosqlite.Connection | None = None
    _db_path: Path

    @classmethod
    async def init(cls) -> None:
        """Initialize connection and run migrations."""
        settings = get_settings()
        cls._db_path = Path(settings.DB_PATH)
        cls._db_path.parent.mkdir(parents=True, exist_ok=True)
        cls._conn = await aiosqlite.connect(cls._db_path)
        await cls._conn.execute("PRAGMA journal_mode=WAL")
        cls._conn.row_factory = aiosqlite.Row
        await cls._conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)",
        )
        await cls._conn.commit()
        migrations_dir = Path(__file__).resolve().parents[4] / "migrations"
        await cls._run_migrations(migrations_dir)

    @classmethod
    async def close(cls) -> None:
        """Close the database connection."""
        if cls._conn is not None:
            await cls._conn.close()
            cls._conn = None

    @classmethod
    @asynccontextmanager
    async def connection(cls) -> AsyncIterator[aiosqlite.Connection]:
        """Yield an active database connection."""
        if cls._conn is None:
            raise RuntimeError("Database not initialized")
        yield cls._conn

    # Basic helpers -----------------------------------------------------
    @classmethod
    async def fetch_one(
        cls, query: str, params: Sequence[Any] | None = None,
    ) -> aiosqlite.Row | None:
        """Return the first row for a query."""
        params = params or []
        async with cls.connection() as conn, conn.execute(query, params) as cur:
            return await cur.fetchone()

    @classmethod
    async def fetch_all(
        cls, query: str, params: Sequence[Any] | None = None,
    ) -> list[aiosqlite.Row]:
        """Return all rows for a query."""
        params = params or []
        async with cls.connection() as conn, conn.execute(query, params) as cur:
            return await cur.fetchall()

    @classmethod
    async def execute(cls, query: str, params: Sequence[Any] | None = None) -> None:
        """Execute a statement."""
        params = params or []
        async with cls.connection() as conn:
            await conn.execute(query, params)
            await conn.commit()

    @classmethod
    async def executemany(
        cls, query: str, param_seq: Iterable[Sequence[Any]],
    ) -> None:
        """Execute a statement for multiple parameter sets."""
        async with cls.connection() as conn:
            await conn.executemany(query, param_seq)
            await conn.commit()

    # Migrations -------------------------------------------------------
    @classmethod
    async def _get_version(cls) -> int:
        async with cls.connection() as conn, conn.execute(
            "SELECT COALESCE(MAX(version), 0) FROM schema_version",
        ) as cur:
            row = await cur.fetchone()
            return int(row[0]) if row else 0

    @classmethod
    async def _run_migrations(cls, migrations_dir: Path) -> None:
        current = await cls._get_version()
        files = sorted(p for p in migrations_dir.glob("*.sql"))
        for path in files:
            try:
                version = int(path.stem.split("_", 1)[0])
            except ValueError:
                continue
            if version <= current:
                continue
            log_info("Applying migration %s", path.name)
            script = path.read_text(encoding="utf-8")
            async with cls.connection() as conn:
                try:
                    await conn.executescript(script)
                    await conn.execute(
                        "INSERT INTO schema_version(version) VALUES (?)",
                        (version,),
                    )
                    await conn.commit()
                    current = version
                except Exception as exc:  # noqa: BLE001
                    await conn.rollback()
                    log_error("Migration %s failed", path.name, exc_info=exc)
                    raise MigrationError(f"Failed migration {path.name}") from exc
