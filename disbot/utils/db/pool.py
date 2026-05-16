"""asyncpg pool lifecycle + generic CRUD primitives.

Owns the process-wide pool instance.  Submodules under ``utils.db.*``
access the pool via :func:`get` and call the generic helpers
:func:`fetchone`, :func:`fetchall`, :func:`execute` rather than reaching
into the global pool directly — that indirection lets tests monkeypatch
``utils.db.pool.get`` (or any helper) without rewriting every callsite.

Lifecycle:
    - :func:`init` is called once from ``bot1.main()`` before any cog
      loads.  It creates the pool, runs ``_ensure_migrations_table``,
      ``_create_tables``, and ``_run_migrations`` from
      :mod:`utils.db.migrations`.
    - :func:`close` is called on graceful shutdown.
    - :func:`get` raises if init has not run yet — production code
      should never see that error; tests must call init or monkeypatch.
"""

from __future__ import annotations

import logging
import os

import asyncpg

from utils.db.codec import init_connection

logger = logging.getLogger("bot.db.pool")

# Module-level singleton.  Tests may swap this via monkeypatch.
_pool: asyncpg.Pool | None = None


def _get_dsn() -> str:
    if dsn := os.environ.get("DATABASE_URL"):
        return dsn
    raise RuntimeError(
        "DATABASE_URL environment variable is required. "
        "Format: postgres://user:password@host:5432/dbname",
    )


async def init() -> None:
    """Create the pool and run migrations.

    Imports the migration runner lazily to keep this module free of
    cross-module dependencies at module-load time (migrations.py imports
    from this module to use ``get``).
    """
    global _pool
    dsn = _get_dsn()
    _pool = await asyncpg.create_pool(
        dsn,
        min_size=2,
        max_size=10,
        init=init_connection,
    )
    # Lazy import — avoids circular dependency at module load.
    from utils.db import migrations

    await migrations.ensure_migrations_table()
    await migrations.create_tables()
    await migrations.run_migrations()
    logger.info("PostgreSQL pool initialised (%s)", dsn.split("@")[-1])


async def close() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


def get() -> asyncpg.Pool:
    """Return the active pool; raise if init() has not run yet."""
    if _pool is None:
        raise RuntimeError("Database not initialised — call db.init() first.")
    return _pool


# ---------------------------------------------------------------------------
# Generic CRUD primitives — preserved verbatim from the pre-split db.py.
# Submodules call these via `from utils.db import pool` + ``pool.fetchone(...)``
# so test monkeypatches on ``utils.db.pool.X`` propagate to every caller.
# ---------------------------------------------------------------------------


async def fetchone(query: str, params: tuple = ()) -> dict | None:
    row = await get().fetchrow(query, *params)
    return dict(row) if row else None


async def fetchall(query: str, params: tuple = ()) -> list[dict]:
    rows = await get().fetch(query, *params)
    return [dict(r) for r in rows]


async def execute(query: str, params: tuple = ()) -> None:
    await get().execute(query, *params)
