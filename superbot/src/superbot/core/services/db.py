"""Asynchronous database manager."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import aiosqlite


class DB:
    """Simple aiosqlite-based database manager."""

    _conn: aiosqlite.Connection | None = None

    @classmethod
    async def init(cls, db_path: str) -> None:
        """Initialize the database connection.

        Args:
            db_path: Path to the SQLite database file.
        """
        if cls._conn is not None:
            return
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        cls._conn = await aiosqlite.connect(path)
        cls._conn.row_factory = aiosqlite.Row
        await cls._conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY)",
        )
        await cls._conn.commit()

    @classmethod
    @asynccontextmanager
    async def acquire(cls) -> AsyncIterator[aiosqlite.Connection]:
        """Acquire the database connection."""
        if cls._conn is None:
            raise RuntimeError("Database not initialized")
        yield cls._conn

    @classmethod
    async def close(cls) -> None:
        """Close the database connection."""
        if cls._conn is not None:
            await cls._conn.close()
            cls._conn = None

    @classmethod
    async def run_migrations(cls) -> None:
        """Run database migrations from numbered SQL files."""
        if cls._conn is None:
            raise RuntimeError("Database not initialized")
        project_root = Path(__file__).resolve().parents[4]
        migrations_dir = project_root / "migrations"
        migrations_dir.mkdir(parents=True, exist_ok=True)

        current_version = await cls._get_version()
        for path in sorted(migrations_dir.glob("*.sql")):
            try:
                version = int(path.stem)
            except ValueError:
                continue
            if version <= current_version:
                continue
            with path.open("r", encoding="utf-8") as f:
                await cls._conn.executescript(f.read())
            await cls._conn.execute(
                "REPLACE INTO schema_version (version) VALUES (?)",
                (version,),
            )
            await cls._conn.commit()
            current_version = version

    @classmethod
    async def _get_version(cls) -> int:
        if cls._conn is None:
            return 0
        async with cls._conn.execute(
            "SELECT version FROM schema_version ORDER BY version DESC LIMIT 1",
        ) as cur:
            row = await cur.fetchone()
            return int(row["version"]) if row else 0
