"""Read-only DB probes for the platform-consistency diagnostics service.

A7 (2026-06-19): these probes were lifted out of
``services.platform_consistency`` so its section collectors no longer issue
raw ``pool.*`` calls — the SQL now lives behind the ``utils.db`` seam like
every other table accessor. Queries are byte-for-byte the originals.

Every function here is a pure read used by a *fail-safe* collector: the
collector wraps the call in ``try/except`` and downgrades any raise to a
WARNING/FATAL section, so these helpers deliberately do **not** swallow
exceptions themselves — the caller owns the failure policy.

The probes go through ``pool.get().fetchval`` / ``pool.get().fetch`` (rather
than the ``pool.fetchone``/``pool.fetchall`` dict primitives) to preserve the
exact asyncpg surface the collectors relied on, including the existing test
seam that patches ``utils.db.pool.get`` with a minimal fake pool.
"""

from __future__ import annotations

from typing import Any

from utils.db import pool


async def table_oid(table_name: str) -> Any:
    """Return ``to_regclass(<table>)`` — the table's OID, or ``None`` if absent.

    ``table_name`` is interpolated into the SQL because asyncpg cannot
    parameterise a ``to_regclass`` argument; callers pass only trusted
    hard-coded literals (never user input).
    """
    return await pool.get().fetchval(f"SELECT to_regclass('{table_name}')")


async def feature_flag_audit_count() -> Any:
    """Return ``COUNT(*)`` of the ``feature_flag_audit`` table."""
    return await pool.get().fetchval("SELECT COUNT(*) FROM feature_flag_audit")


async def applied_migration_versions() -> list[int]:
    """Return the sorted set of applied ``schema_migrations`` versions."""
    rows = await pool.get().fetch(
        "SELECT version FROM schema_migrations ORDER BY version",
    )
    return [int(r["version"]) for r in rows]
