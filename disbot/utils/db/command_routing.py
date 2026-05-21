"""Command routing DB primitives.

Per-guild per-scope per-cog enable/disable overrides for the runtime
cog router.  Reads return None when no row exists; the service layer
resolves the chain (channel → category → guild → default-true).
"""

from __future__ import annotations

import logging
from typing import Any

from utils.db import pool

logger = logging.getLogger("bot.db.command_routing")


_KNOWN_SCOPES: frozenset[str] = frozenset({"guild", "category", "channel"})


async def get_one(
    guild_id: int,
    scope_type: str,
    scope_id: int | None,
    cog_name: str,
) -> dict[str, Any] | None:
    """Return the routing row for ``(guild, scope, cog)``, or ``None``.

    Uses ``COALESCE(scope_id, -1) = COALESCE($3, -1)`` so guild-scope
    lookups (scope_id=NULL) match cleanly against the partial UNIQUE
    index.
    """
    if scope_type not in _KNOWN_SCOPES:
        raise ValueError(
            f"scope_type must be one of {sorted(_KNOWN_SCOPES)}, got {scope_type!r}",
        )
    row = await pool.get().fetchrow(
        """
        SELECT enabled, actor_id, updated_at
          FROM command_routing_policy
         WHERE guild_id = $1
           AND scope_type = $2
           AND COALESCE(scope_id, -1) = COALESCE($3, -1)
           AND cog_name = $4
        """,
        guild_id,
        scope_type,
        scope_id,
        cog_name,
    )
    return dict(row) if row else None


async def set_one(
    guild_id: int,
    scope_type: str,
    scope_id: int | None,
    cog_name: str,
    enabled: bool,
    actor_id: int | None,
) -> None:
    """Upsert the routing row.  Conflict resolution mirrors
    cleanup_policies: replace the existing row's enabled flag and
    actor.
    """
    if scope_type not in _KNOWN_SCOPES:
        raise ValueError(
            f"scope_type must be one of {sorted(_KNOWN_SCOPES)}, got {scope_type!r}",
        )
    await pool.get().execute(
        """
        INSERT INTO command_routing_policy
            (guild_id, scope_type, scope_id, cog_name, enabled, actor_id)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (guild_id, scope_type, COALESCE(scope_id, -1), cog_name)
        DO UPDATE SET
            enabled    = EXCLUDED.enabled,
            actor_id   = EXCLUDED.actor_id,
            updated_at = NOW()
        """,
        guild_id,
        scope_type,
        scope_id,
        cog_name,
        enabled,
        actor_id,
    )


async def list_for_guild(guild_id: int) -> list[dict[str, Any]]:
    """Return every routing row for ``guild_id``."""
    rows = await pool.get().fetch(
        """
        SELECT scope_type, scope_id, cog_name, enabled, actor_id, updated_at
          FROM command_routing_policy
         WHERE guild_id = $1
         ORDER BY scope_type, cog_name, scope_id NULLS FIRST
        """,
        guild_id,
    )
    return [dict(r) for r in rows]


__all__ = ["get_one", "list_for_guild", "set_one"]
