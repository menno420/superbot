"""Command routing — per-channel cog enable/disable (read path + mutation owner).

Reads ``command_routing_policy`` via the :mod:`utils.db.command_routing`
primitives and walks the scope chain ``channel → category → guild →
default-true`` so absence of any policy row leaves a cog enabled (the
safe default).

This module is also the **canonical mutation owner** for routing rows:
:func:`set_policy` reads the old row, performs the write, emits the
``audit.action_recorded`` companion with the real previous value, and
returns a typed :class:`RoutingMutationResult`.  Callers (the Final
Review dispatcher's ``set_cog_routing`` arm, any future panel) consume
the result; they must not call :mod:`utils.db.command_routing` writers
directly, and they no longer own mutation IDs or audit emission.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from services.audit_events import emit_audit_action
from utils.db import command_routing as db

logger = logging.getLogger("bot.services.command_routing")


@dataclass(frozen=True)
class RoutingMutationResult:
    """Outcome of a routing-policy write.

    ``old_enabled`` is ``None`` when no policy row existed for the scope
    before this write (the scope was riding the default-true chain).
    ``audit_emitted`` carries :func:`emit_audit_action`'s publish-accepted
    flag (best-effort; the DB write is already committed either way).
    """

    mutation_id: str
    guild_id: int
    scope_type: str
    scope_id: int | None
    cog_name: str
    old_enabled: bool | None
    new_enabled: bool
    audit_emitted: bool


def _enabled_label(enabled: bool | None) -> str | None:
    if enabled is None:
        return None
    return "enabled" if enabled else "disabled"


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
    actor_type: str = "user",
) -> RoutingMutationResult:
    """Upsert a routing policy row — the canonical routing write.

    Owns the full mutation: reads the old row (for a real
    ``prev_value`` in the audit trail), performs the upsert, emits the
    ``audit.action_recorded`` companion (best-effort — emission failure
    is logged inside :func:`emit_audit_action` and surfaced via
    ``audit_emitted``, never raised; the committed write stands), and
    returns the typed result.  Every routing write — the Final Review
    dispatcher today, any future operator panel — goes through here so
    no caller can write silently or lose the previous state.
    """
    old_row = await db.get_one(guild_id, scope_type, scope_id, cog_name)
    old_enabled = bool(old_row["enabled"]) if old_row is not None else None

    await db.set_one(
        guild_id=guild_id,
        scope_type=scope_type,
        scope_id=scope_id,
        cog_name=cog_name,
        enabled=enabled,
        actor_id=actor_id,
    )

    mutation_id = str(uuid.uuid4())
    audit_emitted = await emit_audit_action(
        mutation_id=mutation_id,
        subsystem="cog_routing",
        mutation_type="set_cog_routing",
        target=(
            f"{scope_type}:{scope_id if scope_id is not None else 'guild'}:{cog_name}"
        ),
        scope=scope_type,
        guild_id=guild_id,
        prev_value=_enabled_label(old_enabled),
        new_value=_enabled_label(enabled),
        actor_id=actor_id,
        actor_type=actor_type,
        occurred_at=datetime.now(tz=timezone.utc),
    )
    return RoutingMutationResult(
        mutation_id=mutation_id,
        guild_id=guild_id,
        scope_type=scope_type,
        scope_id=scope_id,
        cog_name=cog_name,
        old_enabled=old_enabled,
        new_enabled=enabled,
        audit_emitted=audit_emitted,
    )


async def list_for_guild(guild_id: int) -> list[dict[str, Any]]:
    """Return every routing row for ``guild_id`` ordered by scope."""
    return await db.list_for_guild(guild_id)


__all__ = [
    "RoutingMutationResult",
    "is_cog_enabled",
    "list_for_guild",
    "set_policy",
]
