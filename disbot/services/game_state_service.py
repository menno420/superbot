"""Game-state checkpoint service.

Restart-safe persistence layer for in-flight game state (blackjack
hands, RPS tournament rounds, counting per-channel cache).

Cogs that previously kept game state in module-level dicts or
instance attributes lose it on bot restart — see
``docs/runtime_contracts.md`` §8 "What does NOT survive a restart".
This service is the cure: on each turn, save the minimum state
needed to resume; on cog_load, list_active_for_subsystem() returns
every checkpoint so the cog can re-attach views and bind handlers.

Persistence model
-----------------
- One row per (guild_id, user_id, channel_id, subsystem).  UNIQUE
  enforced at the DB layer (migration 015).
- Payload is a JSONB blob — each subsystem owns its schema.  Use
  small, primitive-typed dicts so re-loading after a code change
  doesn't break.  Version your payload if you change the shape.
- Writes are upsert (INSERT … ON CONFLICT DO UPDATE) so every save
  is atomic and the latest checkpoint wins.

Public API
----------
- ``save(...)``    — upsert a checkpoint.
- ``load(...)``    — return the latest checkpoint or None.
- ``clear(...)``   — delete a checkpoint (called on game completion).
- ``list_active_for_subsystem(subsystem)`` — return every checkpoint
  for a subsystem; used at cog_load.

The service does NOT emit EventBus events — checkpoint frequency
makes that noisy.  Cogs decide when to emit higher-level signals
(game_started / game_completed).
"""

from __future__ import annotations

import json
import logging
from typing import Any

from utils.db import pool

logger = logging.getLogger("bot.game_state")


async def save(
    guild_id: int,
    user_id: int,
    channel_id: int,
    subsystem: str,
    state: dict[str, Any],
) -> None:
    """Upsert a game-state checkpoint.

    The state dict is JSON-encoded; only JSON-safe primitives (int,
    str, bool, None, list, dict of strings) are supported.
    """
    payload = json.dumps(state)
    await pool.execute(
        """INSERT INTO game_state
             (guild_id, user_id, channel_id, subsystem, state)
           VALUES ($1, $2, $3, $4, $5::jsonb)
           ON CONFLICT (guild_id, user_id, channel_id, subsystem)
           DO UPDATE SET
               state      = EXCLUDED.state,
               updated_at = NOW()""",
        (guild_id, user_id, channel_id, subsystem, payload),
    )


async def load(
    guild_id: int,
    user_id: int,
    channel_id: int,
    subsystem: str,
) -> dict[str, Any] | None:
    """Return the latest checkpoint for this (user, channel, subsystem) or None."""
    row = await pool.fetchone(
        """SELECT state FROM game_state
           WHERE guild_id=$1 AND user_id=$2
             AND channel_id=$3 AND subsystem=$4""",
        (guild_id, user_id, channel_id, subsystem),
    )
    if row is None:
        return None
    raw = row["state"]
    if isinstance(raw, str):
        return json.loads(raw)
    return raw  # asyncpg may decode JSONB to dict already


async def clear(
    guild_id: int,
    user_id: int,
    channel_id: int,
    subsystem: str,
) -> None:
    """Delete the checkpoint for a completed game."""
    await pool.execute(
        """DELETE FROM game_state
           WHERE guild_id=$1 AND user_id=$2
             AND channel_id=$3 AND subsystem=$4""",
        (guild_id, user_id, channel_id, subsystem),
    )


async def list_active_for_subsystem(
    subsystem: str,
    *,
    guild_id: int | None = None,
) -> list[dict[str, Any]]:
    """Return every active checkpoint for *subsystem*, optionally guild-scoped.

    Used at cog_load to enumerate games that need restoring.  Each
    row dict contains: guild_id, user_id, channel_id, state (decoded
    dict), updated_at.
    """
    if guild_id is None:
        rows = await pool.get().fetch(
            """SELECT guild_id, user_id, channel_id, state, updated_at
               FROM game_state
               WHERE subsystem=$1""",
            subsystem,
        )
    else:
        rows = await pool.get().fetch(
            """SELECT guild_id, user_id, channel_id, state, updated_at
               FROM game_state
               WHERE subsystem=$1 AND guild_id=$2""",
            subsystem,
            guild_id,
        )
    result: list[dict[str, Any]] = []
    for r in rows:
        raw = r["state"]
        state = json.loads(raw) if isinstance(raw, str) else raw
        result.append(
            {
                "guild_id": r["guild_id"],
                "user_id": r["user_id"],
                "channel_id": r["channel_id"],
                "state": state,
                "updated_at": r["updated_at"],
            },
        )
    return result
