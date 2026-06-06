"""Lightweight database reachability probe for health diagnostics.

A trivial ``SELECT 1`` round-trip used by the health snapshot's
``database`` adapter to classify the DB as reachable / unreachable.  The
caller applies the timeout (the aggregator wraps this in
``asyncio.wait_for`` for per-source isolation), so this stays a thin
primitive in the ``utils/db`` layer rather than a service reaching for
the connection pool directly.
"""

from __future__ import annotations

from utils.db import pool


async def ping() -> bool:
    """Return ``True`` if a trivial ``SELECT 1`` round-trips.

    Raises on a genuine connection failure (e.g. ``asyncpg`` /
    ``ConnectionError``) so the calling adapter can classify the database
    as unreachable; the aggregator catches and times this out per-source.
    """
    row = await pool.fetchone("SELECT 1 AS ok")
    return bool(row and row.get("ok") == 1)
