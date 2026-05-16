"""asyncpg JSONB codec + legacy decode shim.

Registered at pool creation in :mod:`utils.db.pool` so every connection
round-trips ``jsonb`` columns as plain Python dicts/lists.  The legacy
decode shim is a transparent backward-compat path for rows written
before migration 012 was applied (which double-encoded JSONB strings —
see migration file 012 for the repair).

This module has no side effects at import time.
"""

from __future__ import annotations

import json

import asyncpg


async def init_connection(conn: asyncpg.Connection) -> None:
    """Register the JSONB codec on a new asyncpg connection.

    Called by asyncpg via the ``init`` hook on pool creation.  Ensures
    that ``jsonb`` columns serialise from Python objects via
    ``json.dumps`` and deserialise back via ``json.loads`` — the bot
    code can then treat JSONB columns as native dicts/lists.
    """
    await conn.set_type_codec(
        "jsonb",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )


def maybe_decode_legacy(value: object) -> object:
    """Transparently decode double-encoded legacy session-state values.

    Before migration 012 was applied, ``set_session_state()`` manually
    called ``json.dumps()`` before asyncpg, so JSONB rows contain a
    JSON string wrapping the real payload.  After the migration repairs
    existing rows this shim is a no-op (asyncpg decodes JSONB objects
    directly into Python dicts).  Slated for removal in S6 once
    migration 012 is confirmed applied in production.
    """
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            return value
    return value
