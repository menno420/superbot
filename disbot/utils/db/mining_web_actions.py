"""mining_web_actions CRUD — the mineverse WRITE-contract idempotency ledger.

Migration 105. One row per ``(guild_id, action_id)`` — the contract's
idempotency key (superbot-mineverse ``docs/mining-write-contract.md``
§ "Idempotency"): the body digest plus the complete original response
(HTTP status + envelope) so a byte-identical replay returns the original
answer without re-executing, and key reuse with a different body is
detectable. Keys are TEXT exactly as they appear on the wire (string
snowflake / lowercase UUIDv4).

Retention is age-based and enforced at read time: :func:`get_web_action`
ignores rows older than *max_age_hours* (contract minimum 24h), so an
expired ``action_id`` behaves as new even before the purge sweeps it.
:func:`put_web_action` upserts (a post-window reuse overwrites the stale
row) and the endpoint purges opportunistically via :func:`purge_web_actions`.

The only caller is ``disbot/mining_write_api.py`` (relay infrastructure,
not game state — game mutations stay behind ``services/mining_workflow.py``).
"""

from __future__ import annotations

import json
from typing import Any

from utils.db import pool

#: Contract minimum retention (hours) — the default read/purge horizon.
RETENTION_HOURS = 24


async def get_web_action(
    guild_id: str,
    action_id: str,
    *,
    max_age_hours: int = RETENTION_HOURS,
) -> dict[str, Any] | None:
    """The stored outcome for ``(guild_id, action_id)`` inside the window.

    Returns ``{"body_digest", "http_status", "response"}`` or ``None`` when
    the key was never seen (or its row aged out of *max_age_hours*).
    """
    row = await pool.fetchone(
        """SELECT body_digest, http_status, response
           FROM mining_web_actions
           WHERE guild_id=$1 AND action_id=$2
             AND created_at > NOW() - make_interval(hours => $3)""",
        (guild_id, action_id, max_age_hours),
    )
    if row is None:
        return None
    response = row["response"]
    if isinstance(response, str):  # asyncpg returns JSONB as str by default
        response = json.loads(response)
    return {
        "body_digest": row["body_digest"],
        "http_status": row["http_status"],
        "response": response,
    }


async def put_web_action(
    guild_id: str,
    action_id: str,
    body_digest: str,
    http_status: int,
    response: dict[str, Any],
) -> None:
    """Remember the original outcome for ``(guild_id, action_id)`` (upsert).

    The upsert (rather than DO NOTHING) is deliberate: a key reused *after*
    its row aged past the retention window is contractually a NEW action, so
    the fresh outcome replaces the stale row.
    """
    await pool.execute(
        """INSERT INTO mining_web_actions
               (guild_id, action_id, body_digest, http_status, response)
           VALUES ($1, $2, $3, $4, $5::jsonb)
           ON CONFLICT (guild_id, action_id)
           DO UPDATE SET body_digest=$3, http_status=$4, response=$5::jsonb,
                         created_at=NOW()""",
        (guild_id, action_id, body_digest, http_status, json.dumps(response)),
    )


async def purge_web_actions(*, older_than_hours: int = RETENTION_HOURS) -> None:
    """Delete rows older than *older_than_hours* (opportunistic sweep)."""
    await pool.execute(
        """DELETE FROM mining_web_actions
           WHERE created_at <= NOW() - make_interval(hours => $1)""",
        (older_than_hours,),
    )
