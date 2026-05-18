"""Platform migration checkpoints — DB primitives (Phase 2, PR-5).

Owns the read/write surface for ``platform_migration_checkpoints``.
The first consumer is :mod:`services.binding_backfill`; the table is
intentionally generic so future logical migrations (e.g. PR-9
participation backfills) can reuse it without a new schema.

Public surface:

* :func:`get_checkpoint` — single-row read keyed by (name, guild_id).
* :func:`list_checkpoints` — bulk read for diagnostics, optionally
  filtered by name prefix and/or guild.
* :func:`upsert_checkpoint` — insert or update by (name, guild_id);
  idempotent.
* :func:`delete_for_guild` — purge per-guild rows for one guild;
  global rows (``guild_id IS NULL``) are preserved.

Status semantics (mirror migration 026 CHECK constraint):

  pending             — work registered but not started
  dry_run_complete    — dry-run finished without writing target table
  in_progress         — write phase running
  complete            — all work finished successfully
  failed              — write phase aborted; ``summary_json`` carries
                        the error context
  rolled_back         — a previous ``complete`` row was reverted; the
                        same (name, guild_id) is updated in place
"""

from __future__ import annotations

import json
import logging
from typing import Any

from utils.db import pool

logger = logging.getLogger("bot.db.platform_migration_checkpoints")

# Recognized statuses (mirrors migration 026 CHECK).  An alignment test
# pins this set to the SQL literals.
KNOWN_STATUSES: frozenset[str] = frozenset(
    {
        "pending",
        "dry_run_complete",
        "in_progress",
        "complete",
        "failed",
        "rolled_back",
    },
)


def _serialise(summary_json: Any | None) -> str | None:
    """JSON-encode ``summary_json`` for asyncpg.

    asyncpg requires JSONB columns to be passed as ``json.dumps`` text
    (it does not auto-encode Python dicts).  ``None`` passes through as
    SQL NULL.
    """
    if summary_json is None:
        return None
    if isinstance(summary_json, str):
        # Caller already serialised; trust them.
        return summary_json
    return json.dumps(summary_json, default=str)


def _deserialise(raw: Any | None) -> Any | None:
    """Decode the JSONB column for callers.

    asyncpg can return either ``str`` (when the connection has no
    JSONB codec installed) or a Python dict (when it does).  Handle
    both shapes so callers always see a Python value.
    """
    if raw is None:
        return None
    if isinstance(raw, (dict, list)):
        return raw
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        logger.warning(
            "platform_migration_checkpoints: failed to JSON-decode summary; "
            "returning raw value",
        )
        return raw


# ---------------------------------------------------------------------------
# Reads
# ---------------------------------------------------------------------------


async def get_checkpoint(
    name: str,
    guild_id: int | None = None,
) -> dict[str, Any] | None:
    """Return the checkpoint row for ``(name, guild_id)``, or ``None``.

    Uses ``IS NULL`` rather than ``= NULL`` so the global-checkpoint
    row (where ``guild_id`` is null) is correctly resolved.
    """
    if guild_id is None:
        row = await pool.get().fetchrow(
            """
            SELECT id, name, guild_id, status, version,
                   started_at, completed_at, summary_json
            FROM platform_migration_checkpoints
            WHERE name = $1 AND guild_id IS NULL
            """,
            name,
        )
    else:
        row = await pool.get().fetchrow(
            """
            SELECT id, name, guild_id, status, version,
                   started_at, completed_at, summary_json
            FROM platform_migration_checkpoints
            WHERE name = $1 AND guild_id = $2
            """,
            name,
            guild_id,
        )
    if row is None:
        return None
    out = dict(row)
    out["summary_json"] = _deserialise(out.get("summary_json"))
    return out


async def list_checkpoints(
    *,
    name_prefix: str | None = None,
    guild_id: int | None = None,
) -> list[dict[str, Any]]:
    """Return checkpoint rows for diagnostics.

    Filters:

    * ``name_prefix`` — match rows whose ``name`` starts with this
      literal.  ``None`` returns every row.
    * ``guild_id`` — restrict to one guild.  ``None`` returns rows
      for every guild AND the global rows.
    """
    clauses: list[str] = []
    args: list[Any] = []
    if name_prefix is not None:
        args.append(f"{name_prefix}%")
        clauses.append(f"name LIKE ${len(args)}")
    if guild_id is not None:
        args.append(guild_id)
        clauses.append(f"guild_id = ${len(args)}")
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = (
        "SELECT id, name, guild_id, status, version, "
        "started_at, completed_at, summary_json "
        f"FROM platform_migration_checkpoints {where} "
        "ORDER BY name, started_at DESC"
    )
    rows = await pool.get().fetch(sql, *args)
    out: list[dict[str, Any]] = []
    for r in rows:
        d = dict(r)
        d["summary_json"] = _deserialise(d.get("summary_json"))
        out.append(d)
    return out


async def count_by_status(
    *,
    name_prefix: str | None = None,
) -> dict[str, int]:
    """Return a ``status → count`` histogram for diagnostics."""
    if name_prefix is None:
        rows = await pool.get().fetch(
            """
            SELECT status, COUNT(*)::int AS n
            FROM platform_migration_checkpoints
            GROUP BY status
            """,
        )
    else:
        rows = await pool.get().fetch(
            """
            SELECT status, COUNT(*)::int AS n
            FROM platform_migration_checkpoints
            WHERE name LIKE $1
            GROUP BY status
            """,
            f"{name_prefix}%",
        )
    return {r["status"]: r["n"] for r in rows}


# ---------------------------------------------------------------------------
# Writes
# ---------------------------------------------------------------------------


async def upsert_checkpoint(
    *,
    name: str,
    guild_id: int | None,
    status: str,
    version: int = 1,
    summary_json: Any | None = None,
    mark_completed: bool = False,
) -> None:
    """Insert or update the checkpoint for ``(name, guild_id)``.

    Idempotent: re-running with the same ``(name, guild_id)`` updates
    the existing row in place (status, version, summary, optionally
    ``completed_at``).  ``started_at`` is preserved on update so the
    original run timestamp survives.

    Args:
        name: migration identifier (e.g. ``"binding_backfill"``).
        guild_id: per-guild scope, or ``None`` for the global row.
        status: must be in :data:`KNOWN_STATUSES`.
        version: schema/version counter for the migration; bump when
            the ``summary_json`` shape changes.
        summary_json: arbitrary JSON-serialisable payload.  ``None``
            passes through as SQL NULL.
        mark_completed: if ``True``, set ``completed_at = NOW()`` on
            this write.  Used by terminal statuses
            (``complete``/``failed``/``rolled_back``).

    Raises:
        ValueError: if ``status`` is not in :data:`KNOWN_STATUSES`.
    """
    if status not in KNOWN_STATUSES:
        msg = f"unknown status {status!r}; expected one of {sorted(KNOWN_STATUSES)}"
        raise ValueError(msg)

    completed_clause = "NOW()" if mark_completed else "completed_at"
    serialised = _serialise(summary_json)

    if guild_id is None:
        sql = f"""
            INSERT INTO platform_migration_checkpoints
                (name, guild_id, status, version, summary_json)
            VALUES ($1, NULL, $2, $3, $4)
            ON CONFLICT (name) WHERE guild_id IS NULL DO UPDATE SET
                status = EXCLUDED.status,
                version = EXCLUDED.version,
                summary_json = EXCLUDED.summary_json,
                completed_at = {completed_clause}
        """
        await pool.get().execute(sql, name, status, version, serialised)
    else:
        sql = f"""
            INSERT INTO platform_migration_checkpoints
                (name, guild_id, status, version, summary_json)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (name, guild_id) WHERE guild_id IS NOT NULL
            DO UPDATE SET
                status = EXCLUDED.status,
                version = EXCLUDED.version,
                summary_json = EXCLUDED.summary_json,
                completed_at = {completed_clause}
        """
        await pool.get().execute(
            sql,
            name,
            guild_id,
            status,
            version,
            serialised,
        )


async def delete_for_guild(guild_id: int) -> int:
    """Delete per-guild checkpoint rows for ``guild_id``.

    Global checkpoint rows (``guild_id IS NULL``) are preserved.
    Wired into ``guild_lifecycle.teardown`` so a re-invited guild
    starts with a clean checkpoint history while the global migration
    overview survives.

    Returns the deleted-row count parsed from asyncpg's ``"DELETE N"``
    status string; ``0`` on any parse failure.
    """
    result = await pool.get().execute(
        "DELETE FROM platform_migration_checkpoints WHERE guild_id = $1",
        guild_id,
    )
    try:
        return int(result.split()[-1])
    except (ValueError, IndexError):
        return 0


__all__ = [
    "KNOWN_STATUSES",
    "count_by_status",
    "delete_for_guild",
    "get_checkpoint",
    "list_checkpoints",
    "upsert_checkpoint",
]
