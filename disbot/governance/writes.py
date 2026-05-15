"""Governance write operations — all cogs must route through here.

Layer: models → ... → health → writes.
Imports from governance.models, governance.events, governance.cache.
"""

from __future__ import annotations

import logging

from governance.cache import invalidate_guild_cache
from governance.events import (
    EVT_CLEANUP_CHANGED,
    EVT_VISIBILITY_CHANGED,
    _emit_governance_event,
)
from governance.models import GovernanceContext
from services.governance_exceptions import GovernanceError
from utils import db, settings_keys
from utils.subsystem_registry import REGISTRY_VERSION

logger = logging.getLogger("bot")

_VALID_SCOPE_TYPES: frozenset[str] = frozenset({"channel", "category", "guild"})


async def set_subsystem_visibility(
    ctx: GovernanceContext,
    scope_type: str,
    scope_id: int,
    subsystem: str,
    enabled: bool | None,
) -> None:
    """Set a subsystem visibility override. enabled=None clears the override (inherit).

    scope_type must be one of 'channel', 'category', 'guild'.
    Role-scoped overrides are not yet resolvable (ISSUE-007) and are explicitly
    rejected here to prevent silent misconfiguration.
    """
    if scope_type not in _VALID_SCOPE_TYPES:
        raise GovernanceError(
            f"Invalid scope_type {scope_type!r}. "
            f"Must be one of: {sorted(_VALID_SCOPE_TYPES)}. "
            "Role-scoped overrides are not yet supported."
        )
    await db.set_subsystem_visibility(
        ctx.guild_id, scope_type, scope_id, subsystem, enabled
    )
    await db.write_governance_audit(
        guild_id=ctx.guild_id,
        actor_id=ctx.member.id if ctx.member else 0,
        action="set_visibility",
        scope_type=scope_type,
        scope_id=scope_id,
        subsystem=subsystem,
        new_value={"enabled": enabled},
    )
    invalidate_guild_cache(ctx.guild_id)
    await _emit_governance_event(
        EVT_VISIBILITY_CHANGED,
        {
            "guild_id": ctx.guild_id,
            "scope_type": scope_type,
            "scope_id": scope_id,
            "subsystem": subsystem,
            "enabled": enabled,
        },
    )


async def set_cleanup_policy_for_scope(
    ctx: GovernanceContext,
    scope_type: str,
    scope_id: int,
    delete_invalid_commands: bool = True,
    delete_failed_commands: bool = True,
    delete_after_seconds: int = 5,
) -> None:
    """Set a cleanup policy override for a scope."""
    await db.set_cleanup_policy(
        ctx.guild_id,
        scope_type,
        scope_id,
        delete_invalid_commands=delete_invalid_commands,
        delete_failed_commands=delete_failed_commands,
        delete_after_seconds=delete_after_seconds,
    )
    await db.write_governance_audit(
        guild_id=ctx.guild_id,
        actor_id=ctx.member.id if ctx.member else 0,
        action="set_cleanup",
        scope_type=scope_type,
        scope_id=scope_id,
        subsystem=None,
        new_value={
            "delete_invalid_commands": delete_invalid_commands,
            "delete_failed_commands": delete_failed_commands,
            "delete_after_seconds": delete_after_seconds,
        },
    )
    invalidate_guild_cache(ctx.guild_id)
    await _emit_governance_event(
        EVT_CLEANUP_CHANGED,
        {
            "guild_id": ctx.guild_id,
            "scope_type": scope_type,
            "scope_id": scope_id,
        },
    )


async def check_governance_version(guild_id: int) -> None:
    """Check and upgrade governance version for a guild if needed."""
    stored = await db.get_setting(
        guild_id, settings_keys.GOVERNANCE_VERSION, default="0"
    )
    if int(stored) < REGISTRY_VERSION:
        await _run_governance_upgrade(guild_id, from_version=int(stored))


async def _run_governance_upgrade(guild_id: int, from_version: int) -> None:
    logger.info(
        "governance upgrade guild=%d from v%d to v%d",
        guild_id,
        from_version,
        REGISTRY_VERSION,
    )
    await db.set_setting(
        guild_id, settings_keys.GOVERNANCE_VERSION, str(REGISTRY_VERSION)
    )
