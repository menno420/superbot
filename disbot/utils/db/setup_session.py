"""Setup session — DB primitives (Phase 9e / Track 4 PR 8).

Owns the read/write surface for the ``setup_session`` table created
by migration 031. Higher-level callers (:mod:`services.setup_session`
and the setup-launcher cog in Track 4 PR 9) wrap these primitives;
nothing outside this module + the service issues raw SQL against
``setup_session``.

Status semantics (mirror migration 031 CHECK constraint):

  pending      — guild joined, launcher posted, owner has not started
  in_progress  — owner clicked Start; wizard mid-flow
  complete     — owner finished at least once
  dismissed    — owner deferred / ignored the launcher
"""

from __future__ import annotations

import logging
from typing import Any

from utils.db import pool

logger = logging.getLogger("bot.db.setup_session")

KNOWN_STATUSES: frozenset[str] = frozenset(
    {"pending", "in_progress", "complete", "dismissed"},
)


async def get(guild_id: int) -> dict[str, Any] | None:
    """Return the row for ``guild_id``, or ``None`` when none exists."""
    row = await pool.get().fetchrow(
        """
        SELECT guild_id, guild_name, owner_id, joined_at, setup_status,
               setup_channel_id, setup_message_id, last_readiness_score,
               current_step, delegated_admins, created_at, updated_at
        FROM setup_session
        WHERE guild_id = $1
        """,
        guild_id,
    )
    if row is None:
        return None
    return dict(row)


async def upsert(
    *,
    guild_id: int,
    guild_name: str,
    owner_id: int,
    setup_status: str = "pending",
    setup_channel_id: int | None = None,
    setup_message_id: int | None = None,
) -> None:
    """Insert or update a session row.

    ``joined_at`` is set to NOW() on insert and preserved on update.
    ``setup_status`` only changes via :func:`set_status` /
    :func:`set_step` to keep the lifecycle transitions auditable;
    the upsert path leaves it at its current value when the row
    already exists.
    """
    if setup_status not in KNOWN_STATUSES:
        raise ValueError(
            f"setup_status must be one of {sorted(KNOWN_STATUSES)}, "
            f"got {setup_status!r}",
        )
    await pool.get().execute(
        """
        INSERT INTO setup_session (
            guild_id, guild_name, owner_id, setup_status,
            setup_channel_id, setup_message_id
        )
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (guild_id) DO UPDATE SET
            guild_name       = EXCLUDED.guild_name,
            owner_id         = EXCLUDED.owner_id,
            setup_channel_id = COALESCE(EXCLUDED.setup_channel_id,
                                        setup_session.setup_channel_id),
            setup_message_id = COALESCE(EXCLUDED.setup_message_id,
                                        setup_session.setup_message_id),
            updated_at       = NOW()
        """,
        guild_id,
        guild_name,
        owner_id,
        setup_status,
        setup_channel_id,
        setup_message_id,
    )


async def set_status(guild_id: int, status: str) -> None:
    """Move the row to one of the four documented statuses."""
    if status not in KNOWN_STATUSES:
        raise ValueError(
            f"status must be one of {sorted(KNOWN_STATUSES)}, got {status!r}",
        )
    await pool.get().execute(
        """
        UPDATE setup_session
           SET setup_status = $2,
               updated_at   = NOW()
         WHERE guild_id = $1
        """,
        guild_id,
        status,
    )


async def set_step(guild_id: int, step: str | None) -> None:
    """Update the resume token for the wizard's current step."""
    await pool.get().execute(
        """
        UPDATE setup_session
           SET current_step = $2,
               updated_at   = NOW()
         WHERE guild_id = $1
        """,
        guild_id,
        step,
    )


async def set_readiness_score(guild_id: int, score: int | None) -> None:
    """Cache the latest readiness percentage for drift detection."""
    await pool.get().execute(
        """
        UPDATE setup_session
           SET last_readiness_score = $2,
               updated_at           = NOW()
         WHERE guild_id = $1
        """,
        guild_id,
        score,
    )


async def add_delegated_admin(guild_id: int, user_id: int) -> None:
    """Append ``user_id`` to ``delegated_admins`` (idempotent)."""
    await pool.get().execute(
        """
        UPDATE setup_session
           SET delegated_admins = (
                   SELECT ARRAY(SELECT DISTINCT UNNEST(delegated_admins || $2::BIGINT))
                   FROM setup_session WHERE guild_id = $1
               ),
               updated_at = NOW()
         WHERE guild_id = $1
        """,
        guild_id,
        user_id,
    )


async def remove_delegated_admin(guild_id: int, user_id: int) -> None:
    """Drop ``user_id`` from ``delegated_admins``."""
    await pool.get().execute(
        """
        UPDATE setup_session
           SET delegated_admins = ARRAY_REMOVE(delegated_admins, $2::BIGINT),
               updated_at = NOW()
         WHERE guild_id = $1
        """,
        guild_id,
        user_id,
    )


async def clear(guild_id: int) -> None:
    """Delete the row entirely. Used by ``guild_lifecycle.teardown``."""
    await pool.get().execute(
        "DELETE FROM setup_session WHERE guild_id = $1",
        guild_id,
    )


__all__ = [
    "KNOWN_STATUSES",
    "add_delegated_admin",
    "clear",
    "get",
    "remove_delegated_admin",
    "set_readiness_score",
    "set_status",
    "set_step",
    "upsert",
]
