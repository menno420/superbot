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

# A7: ``pool`` is no longer called directly here — every query moved behind
# ``utils.db.games.game_state``. The import is kept so the historical
# test-patch seam ``services.game_state_service.pool.<primitive>`` (used by
# tests/unit/services/test_game_state_service.py) still resolves; those
# patches mutate the shared pool module the db helpers call through.
from utils.db import pool  # noqa: F401
from utils.db.games import game_state as game_state_db

logger = logging.getLogger("bot.game_state")


async def save(
    guild_id: int,
    user_id: int,
    channel_id: int,
    subsystem: str,
    state: dict[str, Any],
    *,
    version: int = 1,
    conn: Any | None = None,
) -> None:
    """Upsert a game-state checkpoint.

    The state dict is JSON-encoded; only JSON-safe primitives (int,
    str, bool, None, list, dict of strings) are supported.

    PR G0: the ``version`` column lets adopting cogs detect schema
    drift across deploys.  On load, an adopting cog should compare
    the stored version to its current schema version and decide
    whether to resume the game or refund + clear.

    P0-1: pass *conn* to compose this write inside a caller-owned
    ``db.transaction()`` — ``services.game_wager_workflow`` escrows a
    wager (coin debit + checkpoint write) in ONE transaction so a
    crash can never leave money moved without a recovery row, or a row
    without the money.  When *conn* is None the write runs on the pool
    (the existing best-effort checkpoint behaviour).
    """
    payload = json.dumps(state)
    await game_state_db.upsert_checkpoint(
        guild_id,
        user_id,
        channel_id,
        subsystem,
        payload,
        version,
        conn=conn,
    )


async def load(
    guild_id: int,
    user_id: int,
    channel_id: int,
    subsystem: str,
) -> dict[str, Any] | None:
    """Return the latest checkpoint for this (user, channel, subsystem) or None."""
    row = await game_state_db.fetch_checkpoint(
        guild_id,
        user_id,
        channel_id,
        subsystem,
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
    *,
    conn: Any | None = None,
) -> None:
    """Delete the checkpoint for a completed game.

    P0-1: pass *conn* to delete inside a caller-owned transaction —
    ``game_wager_workflow`` releases a wager's escrow row in the same
    transaction that pays out the pot, so a settle is all-or-nothing.
    """
    await game_state_db.delete_checkpoint(
        guild_id,
        user_id,
        channel_id,
        subsystem,
        conn=conn,
    )


async def fetch_rows_for_update(
    guild_id: int,
    subsystem: str,
    *,
    conn: Any,
    channel_id: int | None = None,
    user_ids: list[int] | None = None,
) -> list[dict[str, Any]]:
    """Lock and return checkpoint rows for an escrow/payout settlement.

    The P0-1 wager workflow calls this **inside** a ``db.transaction()``
    to take a row-level ``FOR UPDATE`` lock on the escrow rows it is
    about to settle.  The lock serialises concurrent settle/refund
    attempts (a crash-retry or a double-click): the first call holds
    the rows and deletes them; the second blocks, then finds them gone
    and treats the settle as already done (idempotency without a
    dedicated key column).

    *channel_id* scopes a PvP match; *user_ids* narrows to the two
    players.  Omit both to lock every row for the subsystem in the
    guild (a tournament payout).  Each returned dict carries the
    decoded ``state`` plus ``user_id`` / ``channel_id``.
    """
    return await game_state_db.lock_rows_for_settlement(
        guild_id,
        subsystem,
        conn=conn,
        channel_id=channel_id,
        user_ids=user_ids,
    )


async def list_active_for_subsystem(
    subsystem: str,
    *,
    guild_id: int | None = None,
) -> list[dict[str, Any]]:
    """Return every active checkpoint for *subsystem*, optionally guild-scoped.

    Used at cog_load to enumerate games that need restoring.  Each
    row dict contains: guild_id, user_id, channel_id, state (decoded
    dict), version, updated_at.
    """
    return await game_state_db.list_active(subsystem, guild_id=guild_id)


# ---------------------------------------------------------------------------
# GC helpers (PR G0) — used by session_gc to prune stale checkpoints.
# ---------------------------------------------------------------------------

GAME_STATE_TTL_HOURS: int = 24


async def list_stale(cutoff_hours: int = GAME_STATE_TTL_HOURS) -> list[dict[str, Any]]:
    """Return every game_state row older than *cutoff_hours*.

    Used by session_gc to find checkpoints that survived past their
    expected lifetime — usually because the bot crashed mid-game and
    the cog never called ``clear``.  Each returned dict includes the
    synthetic row ``id`` so the GC can issue precise per-row deletes
    via :func:`clear_by_id` (the natural key may have been reused by
    a brand-new game with the same player/channel/subsystem).
    """
    return await game_state_db.list_stale(cutoff_hours)


async def clear_by_id(row_id: int) -> None:
    """Delete a game_state checkpoint by its synthetic ``id``.

    Distinct from :func:`clear` so the GC can target the exact row it
    listed without racing a freshly-restarted game that already
    upserted at the same natural key.
    """
    await game_state_db.delete_checkpoint_by_id(row_id)
