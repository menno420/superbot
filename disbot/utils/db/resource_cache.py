"""Resource validation cache — CRUD primitives over migration 020.

Phase 2a introduces ``resource_validation_cache`` as a per-resource
status table.  This module owns reads + writes.  Higher-level services
(Phase 4c diagnostics, Phase 7.5 repair) call into here rather than
issuing raw SQL.

State class (per ``docs/architecture.md`` §"State classification"):

  **authoritative persistent (low-value)** — discord.py guild objects
  remain the source of truth for live resource state.  This table
  caches the validation status enum + timestamp so the diagnostics
  layer and repair flows do not have to re-probe every resource on
  each query.  Rows survive bot restart by design; they're cheap to
  regenerate, but doing so on every request defeats the cache.

Public surface:

* ``get_status(guild_id, kind, resource_id)`` — read a single row.
* ``get_statuses_for_guild(guild_id, *, kind=None)`` — batch read.
* ``upsert_status(guild_id, kind, resource_id, status)`` — write one
  row.
* ``upsert_statuses(rows)`` — batch write.
* ``delete_status(guild_id, kind, resource_id)`` — remove a single row
  (used when a binding is cleared).
* ``count_by_status(guild_id, *, kind=None)`` — Phase 4c histogram.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from datetime import datetime

from utils.db import pool

logger = logging.getLogger("bot.db.resource_cache")


async def get_status(
    guild_id: int,
    kind: str,
    resource_id: int,
) -> tuple[str, datetime] | None:
    """Return ``(status, last_validated_at)`` for the row, or ``None``.

    The caller is responsible for converting the string status into
    :class:`~core.resources.status.ResourceStatus` — keeping the DB
    layer dependency-free of the enum keeps imports cheap.
    """
    row = await pool.get().fetchrow(
        """
        SELECT status, last_validated_at
        FROM resource_validation_cache
        WHERE guild_id = $1 AND kind = $2 AND resource_id = $3
        """,
        guild_id,
        kind,
        resource_id,
    )
    if row is None:
        return None
    return row["status"], row["last_validated_at"]


async def get_statuses_for_guild(
    guild_id: int,
    *,
    kind: str | None = None,
) -> list[dict]:
    """Return every cached row for ``guild_id``, optionally filtered by kind.

    Each row is a dict with keys ``kind``, ``resource_id``, ``status``,
    ``last_validated_at`` — the shape Phase 4c diagnostics consumes.
    """
    if kind is None:
        rows = await pool.get().fetch(
            """
            SELECT kind, resource_id, status, last_validated_at
            FROM resource_validation_cache
            WHERE guild_id = $1
            """,
            guild_id,
        )
    else:
        rows = await pool.get().fetch(
            """
            SELECT kind, resource_id, status, last_validated_at
            FROM resource_validation_cache
            WHERE guild_id = $1 AND kind = $2
            """,
            guild_id,
            kind,
        )
    return [dict(r) for r in rows]


async def upsert_status(
    guild_id: int,
    kind: str,
    resource_id: int,
    status: str,
) -> None:
    """Insert-or-update a single resource's status with NOW() as the
    validation timestamp.
    """
    await pool.get().execute(
        """
        INSERT INTO resource_validation_cache
            (guild_id, kind, resource_id, status, last_validated_at)
        VALUES ($1, $2, $3, $4, NOW())
        ON CONFLICT (guild_id, kind, resource_id)
        DO UPDATE SET
            status = EXCLUDED.status,
            last_validated_at = EXCLUDED.last_validated_at
        """,
        guild_id,
        kind,
        resource_id,
        status,
    )


async def upsert_statuses(rows: Iterable[tuple[int, str, int, str]]) -> int:
    """Batch upsert.  Returns the number of rows written.

    Each tuple is ``(guild_id, kind, resource_id, status)``.  Uses a
    transaction so partial failures roll back; called from validation
    sweeps (Phase 4c).
    """
    materialised = list(rows)
    if not materialised:
        return 0
    async with pool.get().acquire() as conn, conn.transaction():
        await conn.executemany(
            """
                INSERT INTO resource_validation_cache
                    (guild_id, kind, resource_id, status, last_validated_at)
                VALUES ($1, $2, $3, $4, NOW())
                ON CONFLICT (guild_id, kind, resource_id)
                DO UPDATE SET
                    status = EXCLUDED.status,
                    last_validated_at = EXCLUDED.last_validated_at
                """,
            materialised,
        )
    return len(materialised)


async def delete_status(guild_id: int, kind: str, resource_id: int) -> None:
    """Remove the cached row for a single resource."""
    await pool.get().execute(
        """
        DELETE FROM resource_validation_cache
        WHERE guild_id = $1 AND kind = $2 AND resource_id = $3
        """,
        guild_id,
        kind,
        resource_id,
    )


async def delete_for_guild(guild_id: int) -> int:
    """Remove every cached row for ``guild_id``.

    Returns the number of rows deleted (best-effort — parsed from the
    ``"DELETE N"`` status string asyncpg returns; falls back to ``0``
    if the format ever changes).

    Phase 2a hardening introduced this primitive so the wiring change
    that adds it to :mod:`disbot.guild_lifecycle`'s teardown sequence is
    a one-line addition rather than a refactor.  The wiring itself
    lands as a follow-up (the lifecycle module's nine-step cleanup
    sequence has its own ordering rules + tests; mixing them with
    Phase 2a expanded the review surface unnecessarily).
    """
    result = await pool.get().execute(
        "DELETE FROM resource_validation_cache WHERE guild_id = $1",
        guild_id,
    )
    try:
        return int(result.split()[-1])
    except (ValueError, IndexError):
        return 0


async def count_by_status(
    guild_id: int,
    *,
    kind: str | None = None,
) -> dict[str, int]:
    """Return a ``status -> count`` histogram for the guild.

    Used by Phase 4c diagnostics to surface "this guild has 12 missing
    resources" without enumerating every row.
    """
    if kind is None:
        rows = await pool.get().fetch(
            """
            SELECT status, COUNT(*)::int AS n
            FROM resource_validation_cache
            WHERE guild_id = $1
            GROUP BY status
            """,
            guild_id,
        )
    else:
        rows = await pool.get().fetch(
            """
            SELECT status, COUNT(*)::int AS n
            FROM resource_validation_cache
            WHERE guild_id = $1 AND kind = $2
            GROUP BY status
            """,
            guild_id,
            kind,
        )
    return {r["status"]: r["n"] for r in rows}


__all__ = [
    "count_by_status",
    "delete_for_guild",
    "delete_status",
    "get_status",
    "get_statuses_for_guild",
    "upsert_status",
    "upsert_statuses",
]
