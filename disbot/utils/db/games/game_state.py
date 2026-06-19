"""game_state checkpoint-table CRUD — the restart-safe per-game state store.

Migration 015. One row per (guild_id, user_id, channel_id, subsystem),
``state`` is a JSONB blob each subsystem owns. The policy layer
(``services.game_state_service``) decides *when* to checkpoint and owns
the payload schema/versioning; this module is plain table CRUD only.

A7 (2026-06-19): these helpers were lifted out of
``services.game_state_service`` so the service no longer issues raw
``pool.*`` calls — the SQL now lives behind the ``utils.db`` seam like
every other table. Queries/params are byte-for-byte the originals.

Transaction-aware (the Q-0071 precedent): the write/lock primitives take
an optional ``conn`` so ``services.game_wager_workflow`` can escrow a
wager (coin debit + checkpoint write) inside ONE caller-owned
``db.transaction()``. With ``conn`` given a primitive must never open its
own transaction — the caller owns commit/rollback.
"""

from __future__ import annotations

import json
from typing import Any

from utils.db import pool

_SAVE_SQL = """INSERT INTO game_state
             (guild_id, user_id, channel_id, subsystem, state, version)
           VALUES ($1, $2, $3, $4, $5::jsonb, $6)
           ON CONFLICT (guild_id, user_id, channel_id, subsystem)
           DO UPDATE SET
               state      = EXCLUDED.state,
               version    = EXCLUDED.version,
               updated_at = NOW()"""

_LOAD_SQL = """SELECT state FROM game_state
           WHERE guild_id=$1 AND user_id=$2
             AND channel_id=$3 AND subsystem=$4"""

_CLEAR_SQL = """DELETE FROM game_state
           WHERE guild_id=$1 AND user_id=$2
             AND channel_id=$3 AND subsystem=$4"""

_CLEAR_BY_ID_SQL = "DELETE FROM game_state WHERE id=$1"

_LIST_ACTIVE_SQL = """SELECT guild_id, user_id, channel_id, state, version, updated_at
               FROM game_state
               WHERE subsystem=$1"""

_LIST_ACTIVE_GUILD_SQL = """SELECT guild_id, user_id, channel_id, state, version, updated_at
               FROM game_state
               WHERE subsystem=$1 AND guild_id=$2"""

_LIST_STALE_SQL = """SELECT id, guild_id, user_id, channel_id, subsystem,
                  state, version, updated_at
             FROM game_state
            WHERE updated_at < NOW() - make_interval(hours => $1)"""


def _decode_state(raw: Any) -> Any:
    """Decode a JSONB ``state`` value — asyncpg may hand back str or dict."""
    return json.loads(raw) if isinstance(raw, str) else raw


async def upsert_checkpoint(
    guild_id: int,
    user_id: int,
    channel_id: int,
    subsystem: str,
    payload: str,
    version: int,
    *,
    conn: Any | None = None,
) -> None:
    """Upsert one checkpoint row. ``payload`` is the JSON-encoded state."""
    await pool.execute(
        _SAVE_SQL,
        (guild_id, user_id, channel_id, subsystem, payload, version),
        conn=conn,
    )


async def fetch_checkpoint(
    guild_id: int,
    user_id: int,
    channel_id: int,
    subsystem: str,
) -> dict[str, Any] | None:
    """Return the raw ``{"state": ...}`` row for this key, or ``None``."""
    return await pool.fetchone(
        _LOAD_SQL,
        (guild_id, user_id, channel_id, subsystem),
    )


async def delete_checkpoint(
    guild_id: int,
    user_id: int,
    channel_id: int,
    subsystem: str,
    *,
    conn: Any | None = None,
) -> None:
    """Delete the checkpoint for this natural key."""
    await pool.execute(
        _CLEAR_SQL,
        (guild_id, user_id, channel_id, subsystem),
        conn=conn,
    )


async def delete_checkpoint_by_id(row_id: int) -> None:
    """Delete a checkpoint by its synthetic ``id`` (GC-precise)."""
    await pool.execute(_CLEAR_BY_ID_SQL, (row_id,))


async def lock_rows_for_settlement(
    guild_id: int,
    subsystem: str,
    *,
    conn: Any,
    channel_id: int | None = None,
    user_ids: list[int] | None = None,
) -> list[dict[str, Any]]:
    """Lock (``FOR UPDATE``) + return checkpoint rows for an escrow settle.

    Called **inside** a caller-owned ``db.transaction()``; the dynamic
    WHERE narrows by *channel_id* (a PvP match) and/or *user_ids* (the
    two players), or omits both to lock every row for the subsystem.
    Each returned dict carries the decoded ``state`` plus ``user_id`` /
    ``channel_id`` / ``version``.
    """
    clauses = ["guild_id=$1", "subsystem=$2"]
    params: list[Any] = [guild_id, subsystem]
    if channel_id is not None:
        params.append(channel_id)
        clauses.append(f"channel_id=${len(params)}")
    if user_ids is not None:
        params.append(list(user_ids))
        clauses.append(f"user_id = ANY(${len(params)}::bigint[])")
    sql = (
        "SELECT user_id, channel_id, state, version FROM game_state WHERE "
        + " AND ".join(clauses)
        + " FOR UPDATE"
    )
    rows = await pool.fetchall(sql, tuple(params), conn=conn)
    return [
        {
            "user_id": r["user_id"],
            "channel_id": r["channel_id"],
            "state": _decode_state(r["state"]),
            "version": r["version"],
        }
        for r in rows
    ]


async def list_active(
    subsystem: str,
    *,
    guild_id: int | None = None,
) -> list[dict[str, Any]]:
    """Return every active checkpoint for *subsystem*, optionally guild-scoped.

    Each row dict contains: guild_id, user_id, channel_id, state
    (decoded), version, updated_at.
    """
    if guild_id is None:
        rows = await pool.get().fetch(_LIST_ACTIVE_SQL, subsystem)
    else:
        rows = await pool.get().fetch(_LIST_ACTIVE_GUILD_SQL, subsystem, guild_id)
    return [
        {
            "guild_id": r["guild_id"],
            "user_id": r["user_id"],
            "channel_id": r["channel_id"],
            "state": _decode_state(r["state"]),
            "version": r["version"],
            "updated_at": r["updated_at"],
        }
        for r in rows
    ]


async def list_stale(cutoff_hours: int) -> list[dict[str, Any]]:
    """Return every checkpoint older than *cutoff_hours*, with synthetic ``id``.

    Each row dict includes ``id`` so the GC can issue precise per-row
    deletes via :func:`delete_checkpoint_by_id`.
    """
    rows = await pool.get().fetch(_LIST_STALE_SQL, cutoff_hours)
    return [
        {
            "id": r["id"],
            "guild_id": r["guild_id"],
            "user_id": r["user_id"],
            "channel_id": r["channel_id"],
            "subsystem": r["subsystem"],
            "state": _decode_state(r["state"]),
            "version": r["version"],
            "updated_at": r["updated_at"],
        }
        for r in rows
    ]
