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
import re
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import asyncpg

from core.runtime import slow_path_log as _slow
from services import metrics as _metrics
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
#
# Phase S3.1 / O-2: each primitive observes ``db_query_seconds`` so the
# !platform metrics surface + Prometheus can highlight slow queries by
# (op, table) without retrofitting timing into every CRUD module.
# Phase S3.2: also records slow paths via core.runtime.slow_path_log.
# ---------------------------------------------------------------------------

# Low-cardinality query label.  Matches the first table name after the
# operation keyword in SELECT/INSERT/UPDATE/DELETE statements; falls back
# to "unknown" so a malformed query produces a single label, not a unique
# one per call (which would explode Prometheus cardinality).
_TABLE_RE = re.compile(
    r"\b(?:FROM|INTO|UPDATE|DELETE\s+FROM)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
    re.IGNORECASE,
)


def _query_label(query: str) -> str:
    """Extract a `<op>:<table>` label from a SQL query for histogram observation."""
    stripped = query.lstrip()
    op = stripped.split(None, 1)[0].lower() if stripped else "unknown"
    match = _TABLE_RE.search(query)
    table = match.group(1).lower() if match else "unknown"
    return f"{op}:{table}"


async def fetchone(
    query: str,
    params: tuple = (),
    *,
    conn: asyncpg.Connection | None = None,
) -> dict | None:
    start = time.monotonic()
    try:
        target = conn if conn is not None else get()
        row = await target.fetchrow(query, *params)
        return dict(row) if row else None
    finally:
        elapsed = time.monotonic() - start
        label = _query_label(query)
        _metrics.db_query_seconds.labels(query_name=label).observe(elapsed)
        _slow.maybe_record("db_query", label, elapsed * 1000)


async def fetchall(
    query: str,
    params: tuple = (),
    *,
    conn: asyncpg.Connection | None = None,
) -> list[dict]:
    start = time.monotonic()
    try:
        target = conn if conn is not None else get()
        rows = await target.fetch(query, *params)
        return [dict(r) for r in rows]
    finally:
        elapsed = time.monotonic() - start
        label = _query_label(query)
        _metrics.db_query_seconds.labels(query_name=label).observe(elapsed)
        _slow.maybe_record("db_query", label, elapsed * 1000)


async def execute(
    query: str,
    params: tuple = (),
    *,
    conn: asyncpg.Connection | None = None,
) -> None:
    start = time.monotonic()
    try:
        target = conn if conn is not None else get()
        await target.execute(query, *params)
    finally:
        elapsed = time.monotonic() - start
        label = _query_label(query)
        _metrics.db_query_seconds.labels(query_name=label).observe(elapsed)
        _slow.maybe_record("db_query", label, elapsed * 1000)


@asynccontextmanager
async def transaction() -> AsyncIterator[asyncpg.Connection]:
    """One connection + one transaction for a cross-domain workflow service.

    Q-0071: a workflow spanning coins + a domain inventory must hold ONE
    DB transaction — pass the yielded connection into the conn-aware CRUD
    primitives so every leg commits or rolls back together.  EventBus
    emission belongs AFTER this context exits (= after commit), never
    inside it (the ``economy_service.transfer`` precedent).
    """
    p = get()
    async with p.acquire() as conn, conn.transaction():
        yield conn
