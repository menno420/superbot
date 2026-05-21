"""Command routing resolver — per-channel cog enable/disable.

Greenfield runtime gate introduced alongside the Setup Wizard's
cog-routing section.  Reads ``command_routing_policy`` via the
:mod:`utils.db.command_routing` primitives and walks the scope chain
``channel → category → guild → default-true`` so absence of any policy
row leaves a cog enabled (the safe default).

This module is the read path.  Writes flow through
:mod:`services.setup_draft` (drafts) and the Final Review dispatcher
(applies); the wizard never writes here directly outside that path.
"""

from __future__ import annotations

import logging
from typing import Any

from utils.db import command_routing as db

logger = logging.getLogger("bot.services.command_routing")


async def is_cog_enabled(
    *,
    guild_id: int,
    cog_name: str,
    channel_id: int | None,
    category_id: int | None,
) -> bool:
    """Return whether ``cog_name`` is enabled in the given scope.

    Walks channel → category → guild → default-true.  The first scope
    that has a policy row wins.  Default-true means a fresh guild
    (no policy rows) gets all cogs enabled; routing only restricts.

    The function reads sequentially because PostgreSQL evaluation of
    three indexed lookups is sub-millisecond and we want the early
    exit on a channel-scope hit.
    """
    if channel_id is not None:
        row = await db.get_one(guild_id, "channel", channel_id, cog_name)
        if row is not None:
            return bool(row["enabled"])
    if category_id is not None:
        row = await db.get_one(guild_id, "category", category_id, cog_name)
        if row is not None:
            return bool(row["enabled"])
    row = await db.get_one(guild_id, "guild", None, cog_name)
    if row is not None:
        return bool(row["enabled"])
    return True


async def set_policy(
    *,
    guild_id: int,
    scope_type: str,
    scope_id: int | None,
    cog_name: str,
    enabled: bool,
    actor_id: int | None,
) -> None:
    """Upsert a routing policy row.  Called by the Final Review
    dispatcher when applying a ``set_cog_routing`` SetupOperation
    (the dispatcher routing arm lands in PR 11; this surface exists
    so the section + tests can pin the contract today).
    """
    await db.set_one(
        guild_id=guild_id,
        scope_type=scope_type,
        scope_id=scope_id,
        cog_name=cog_name,
        enabled=enabled,
        actor_id=actor_id,
    )


async def list_for_guild(guild_id: int) -> list[dict[str, Any]]:
    """Return every routing row for ``guild_id`` ordered by scope."""
    return await db.list_for_guild(guild_id)


__all__ = ["is_cog_enabled", "list_for_guild", "set_policy"]
