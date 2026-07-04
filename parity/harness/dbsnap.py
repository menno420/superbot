"""Database reset + snapshot + delta for golden capture.

Each case starts from the same deterministic database: every public table
(except ``schema_migrations``) is truncated with RESTART IDENTITY, then the
case's fixture rows are applied. The observable "DB out" of a case is the
delta between the post-reset baseline and the post-run dump, with volatile
values (timestamps) normalized.
"""

from __future__ import annotations

import datetime as _dt
import json
from typing import Any

__all__ = ["reset_database", "snapshot", "diff_snapshots", "normalize_value"]

_KEEP_TABLES = {"schema_migrations"}

#: columns whose values are per-run randomness (random hex ids, boot ids) —
#: scrubbed by NAME because shape alone cannot separate them from
#: deterministic content hashes (e.g. policy_snapshot_hash, which stays).
_VOLATILE_COLUMNS = {
    "last_snapshot_id",
    "first_snapshot_id",
    "snapshot_id",
    "boot_id",
    "request_id",
}


async def _tables(pool: Any) -> list[str]:
    rows = await pool.fetchall(
        "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename",
    )
    return [r["tablename"] for r in rows]


async def reset_database(pool: Any) -> None:
    """Truncate every bot table; identities restart so serials are stable."""
    names = [t for t in await _tables(pool) if t not in _KEEP_TABLES]
    if not names:
        return
    joined = ", ".join(f'"{t}"' for t in names)
    await pool.execute(f"TRUNCATE {joined} RESTART IDENTITY CASCADE")


def normalize_value(value: Any) -> Any:
    """Make a cell deterministic + JSON-serializable."""
    import decimal
    import uuid

    if isinstance(value, (_dt.datetime, _dt.date, _dt.time)):
        return "<ts>"
    if isinstance(value, uuid.UUID):
        return "<uuid>"  # boot ids / request ids are per-run randomness
    if isinstance(value, decimal.Decimal):
        return str(value)
    if isinstance(value, _dt.timedelta):
        return f"<td:{value.total_seconds():.0f}s>"
    if isinstance(value, memoryview):
        return f"<bytes:{len(value)}>"
    if isinstance(value, bytes):
        return f"<bytes:{len(value)}>"
    if isinstance(value, dict):
        return {k: normalize_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalize_value(v) for v in value]
    if isinstance(value, str):
        # JSON-typed columns come back as strings via asyncpg's default codec.
        if value and value[0] in "[{":
            try:
                return normalize_value(json.loads(value))
            except (ValueError, TypeError):
                return value
        return value
    return value


async def snapshot(pool: Any) -> dict[str, list[dict[str, Any]]]:
    """Dump every public table as normalized, deterministically ordered rows."""
    out: dict[str, list[dict[str, Any]]] = {}
    for table in await _tables(pool):
        if table in _KEEP_TABLES:
            continue
        rows = await pool.fetchall(f'SELECT * FROM "{table}"')
        normalized = [
            {
                k: ("<hexid>" if k in _VOLATILE_COLUMNS else normalize_value(v))
                for k, v in dict(r).items()
            }
            for r in rows
        ]
        normalized.sort(key=lambda r: json.dumps(r, sort_keys=True, default=str))
        if normalized:
            out[table] = normalized
    return out


def diff_snapshots(
    before: dict[str, list[dict[str, Any]]],
    after: dict[str, list[dict[str, Any]]],
) -> dict[str, dict[str, list[dict[str, Any]]]]:
    """Row-level delta per table: what the case inserted/removed/changed."""
    delta: dict[str, dict[str, list[dict[str, Any]]]] = {}
    tables = sorted(set(before) | set(after))
    for table in tables:
        b_rows = before.get(table, [])
        a_rows = after.get(table, [])
        b_keys = {json.dumps(r, sort_keys=True, default=str) for r in b_rows}
        a_keys = {json.dumps(r, sort_keys=True, default=str) for r in a_rows}
        added = [
            r
            for r in a_rows
            if json.dumps(r, sort_keys=True, default=str) not in b_keys
        ]
        removed = [
            r
            for r in b_rows
            if json.dumps(r, sort_keys=True, default=str) not in a_keys
        ]
        if added or removed:
            entry: dict[str, list[dict[str, Any]]] = {}
            if added:
                entry["added"] = added
            if removed:
                entry["removed"] = removed
            delta[table] = entry
    return delta
