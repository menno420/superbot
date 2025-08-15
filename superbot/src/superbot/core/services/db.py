"""SQLite database helper."""

from __future__ import annotations

from pathlib import Path

import aiosqlite

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


async def init_db(path: Path) -> aiosqlite.Connection:
    """Open a database connection and run migrations."""
    conn = await aiosqlite.connect(path)
    await conn.execute("PRAGMA journal_mode=WAL;")
    await _run_migrations(conn)
    await conn.commit()
    return conn


async def _run_migrations(conn: aiosqlite.Connection) -> None:
    """Apply SQL migration files in order."""
    if not MIGRATIONS_DIR.exists():
        return
    for file in sorted(MIGRATIONS_DIR.glob("*.sql")):
        await conn.executescript(file.read_text())
