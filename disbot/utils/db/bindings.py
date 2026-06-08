"""Subsystem bindings — DB CRUD primitives (Phase 2b).

Owns the read/write surface for ``subsystem_bindings`` and the audit
inserts into ``binding_audit_log``.  Higher-level callers (the
:class:`~services.binding_mutation.BindingMutationPipeline`, the
diagnostics provider, the typed ``get_binding`` accessor) wrap these
primitives; nothing outside this module + the mutation pipeline issues
raw SQL against the binding tables.

Transaction model:
The pipeline calls :func:`upsert_with_audit` / :func:`clear_with_audit`
which open a single asyncpg transaction so the row write + audit row
land atomically.  Read primitives are autocommit.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from utils.db import pool

logger = logging.getLogger("bot.db.bindings")

# ---------------------------------------------------------------------------
# Read primitives
# ---------------------------------------------------------------------------


async def get_one(
    guild_id: int,
    subsystem: str,
    binding_name: str,
) -> dict[str, Any] | None:
    """Return the binding row, or ``None`` when the slot has no row.

    Caller is responsible for converting the dict's ``kind`` / ``status``
    strings into the corresponding enums.
    """
    row = await pool.get().fetchrow(
        """
        SELECT guild_id, subsystem, binding_name, kind, target_id, status,
               last_validated_at, last_updated_at, version
        FROM subsystem_bindings
        WHERE guild_id = $1 AND subsystem = $2 AND binding_name = $3
        """,
        guild_id,
        subsystem,
        binding_name,
    )
    return dict(row) if row else None


async def list_for_guild(
    guild_id: int,
    *,
    subsystem: str | None = None,
) -> list[dict[str, Any]]:
    """Return every binding row for ``guild_id`` (optionally one subsystem)."""
    if subsystem is None:
        rows = await pool.get().fetch(
            """
            SELECT guild_id, subsystem, binding_name, kind, target_id, status,
                   last_validated_at, last_updated_at, version
            FROM subsystem_bindings
            WHERE guild_id = $1
            ORDER BY subsystem, binding_name
            """,
            guild_id,
        )
    else:
        rows = await pool.get().fetch(
            """
            SELECT guild_id, subsystem, binding_name, kind, target_id, status,
                   last_validated_at, last_updated_at, version
            FROM subsystem_bindings
            WHERE guild_id = $1 AND subsystem = $2
            ORDER BY binding_name
            """,
            guild_id,
            subsystem,
        )
    return [dict(r) for r in rows]


async def count_by_status(
    guild_id: int,
    *,
    subsystem: str | None = None,
) -> dict[str, int]:
    """Return a ``status -> count`` histogram for the guild."""
    if subsystem is None:
        rows = await pool.get().fetch(
            """
            SELECT status, COUNT(*)::int AS n
            FROM subsystem_bindings
            WHERE guild_id = $1
            GROUP BY status
            """,
            guild_id,
        )
    else:
        rows = await pool.get().fetch(
            """
            SELECT status, COUNT(*)::int AS n
            FROM subsystem_bindings
            WHERE guild_id = $1 AND subsystem = $2
            GROUP BY status
            """,
            guild_id,
            subsystem,
        )
    return {r["status"]: r["n"] for r in rows}


async def count_by_subsystem(guild_id: int) -> dict[str, int]:
    """Return a ``subsystem -> count`` histogram for the guild."""
    rows = await pool.get().fetch(
        """
        SELECT subsystem, COUNT(*)::int AS n
        FROM subsystem_bindings
        WHERE guild_id = $1
        GROUP BY subsystem
        ORDER BY subsystem
        """,
        guild_id,
    )
    return {r["subsystem"]: r["n"] for r in rows}


# ---------------------------------------------------------------------------
# Mutation primitives — used only by BindingMutationPipeline
# ---------------------------------------------------------------------------


async def upsert_with_audit(
    *,
    guild_id: int,
    subsystem: str,
    binding_name: str,
    kind: str,
    target_id: int | None,
    status: str,
    actor_id: int,
    actor_type: str,
    mutation_id: str,
    old_target_id: int | None,
    old_status: str | None,
) -> None:
    """Atomic write: upsert the binding row + insert one audit row.

    Runs both statements in a single asyncpg transaction.  If either
    fails the entire mutation is rolled back; the caller (the mutation
    pipeline) only invalidates caches and emits events after this
    returns successfully.
    """
    async with pool.get().acquire() as conn, conn.transaction():
        await conn.execute(
            """
                INSERT INTO subsystem_bindings
                    (guild_id, subsystem, binding_name, kind, target_id,
                     status, last_validated_at, last_updated_at, version)
                VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW(), 1)
                ON CONFLICT (guild_id, subsystem, binding_name)
                DO UPDATE SET
                    kind              = EXCLUDED.kind,
                    target_id         = EXCLUDED.target_id,
                    status            = EXCLUDED.status,
                    last_validated_at = NOW(),
                    last_updated_at   = NOW(),
                    version           = subsystem_bindings.version + 1
                """,
            guild_id,
            subsystem,
            binding_name,
            kind,
            target_id,
            status,
        )
        await conn.execute(
            """
                INSERT INTO binding_audit_log
                    (mutation_id, guild_id, subsystem, binding_name,
                     actor_id, actor_type, action,
                     old_target_id, new_target_id,
                     old_status, new_status)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                """,
            mutation_id,
            guild_id,
            subsystem,
            binding_name,
            actor_id,
            actor_type,
            "backfill" if actor_type == "backfill" else "set",
            old_target_id,
            target_id,
            old_status,
            status,
        )


async def clear_with_audit(
    *,
    guild_id: int,
    subsystem: str,
    binding_name: str,
    actor_id: int,
    actor_type: str,
    mutation_id: str,
    old_target_id: int | None,
    old_status: str | None,
) -> None:
    """Atomic clear: set target_id NULL + status='unresolved' + audit row.

    The row is retained (not deleted) so the slot stays declared.
    Phase 4c diagnostics rely on the row to surface "this binding
    exists but is unbound" rather than "this binding was never
    declared".
    """
    async with pool.get().acquire() as conn, conn.transaction():
        await conn.execute(
            """
                UPDATE subsystem_bindings
                SET target_id        = NULL,
                    status           = 'unresolved',
                    last_updated_at  = NOW(),
                    version          = version + 1
                WHERE guild_id = $1
                  AND subsystem = $2
                  AND binding_name = $3
                """,
            guild_id,
            subsystem,
            binding_name,
        )
        await conn.execute(
            """
                INSERT INTO binding_audit_log
                    (mutation_id, guild_id, subsystem, binding_name,
                     actor_id, actor_type, action,
                     old_target_id, new_target_id,
                     old_status, new_status)
                VALUES ($1, $2, $3, $4, $5, $6, 'clear',
                        $7, NULL, $8, 'unresolved')
                """,
            mutation_id,
            guild_id,
            subsystem,
            binding_name,
            actor_id,
            actor_type,
            old_target_id,
            old_status,
        )


# ---------------------------------------------------------------------------
# Maintenance primitives
# ---------------------------------------------------------------------------


def _parse_delete_count(result: str) -> int:
    """Best-effort parse of asyncpg's ``"DELETE N"`` status string."""
    try:
        return int(result.split()[-1])
    except (ValueError, IndexError):
        return 0


async def delete_active_bindings_for_guild(guild_id: int) -> int:
    """Remove ``subsystem_bindings`` rows for ``guild_id``; preserve audit.

    Phase 2 retention policy (see ``docs/health/platform-consistency-ledger.md``
    §3) is to **preserve** ``binding_audit_log`` rows on guild leave so
    the historical trail survives re-invitation.  This primitive is the
    one ``guild_lifecycle.teardown`` calls; the audit purge is a
    deliberately separate primitive (``purge_binding_audit_for_guild``)
    that teardown never invokes.

    Returns the number of active rows deleted.
    """
    result = await pool.get().execute(
        "DELETE FROM subsystem_bindings WHERE guild_id = $1",
        guild_id,
    )
    return _parse_delete_count(result)


async def purge_binding_audit_for_guild(guild_id: int) -> int:
    """Forensic primitive: delete ``binding_audit_log`` rows for a guild.

    NOT called from ``guild_lifecycle.teardown`` — audit retention on
    guild leave is by-design (see ``delete_active_bindings_for_guild``).
    Reserved for explicit operator-driven cleanup (GDPR-style erasure,
    test fixtures, manual archival).  Returns the number of audit rows
    deleted.
    """
    result = await pool.get().execute(
        "DELETE FROM binding_audit_log WHERE guild_id = $1",
        guild_id,
    )
    return _parse_delete_count(result)


async def get_audit_count(guild_id: int) -> int:
    """Return the number of audit rows for ``guild_id``."""
    row = await pool.get().fetchrow(
        "SELECT COUNT(*)::int AS n FROM binding_audit_log WHERE guild_id = $1",
        guild_id,
    )
    return int(row["n"]) if row else 0


# ---------------------------------------------------------------------------
# Convenience converter used by typed accessors
# ---------------------------------------------------------------------------


def row_to_summary(row: dict[str, Any]) -> dict[str, Any]:
    """Normalize a DB row into the shape callers want.

    Coerces ``last_validated_at`` / ``last_updated_at`` to UTC-aware
    :class:`datetime` (asyncpg returns tz-aware values already; this
    function is here so callers can override timezone handling without
    touching SQL).
    """
    out = dict(row)
    for field in ("last_validated_at", "last_updated_at"):
        value = out.get(field)
        if isinstance(value, datetime) and value.tzinfo is None:
            out[field] = value
    return out


__all__ = [
    "clear_with_audit",
    "count_by_status",
    "count_by_subsystem",
    "delete_active_bindings_for_guild",
    "get_audit_count",
    "get_one",
    "list_for_guild",
    "purge_binding_audit_for_guild",
    "row_to_summary",
    "upsert_with_audit",
]
