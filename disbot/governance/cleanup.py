"""Cleanup policy resolution for governance contexts.

Layer: models → events → cache → dependency → resolver → cleanup.
Imports from governance.models, governance.resolver (for _build_scope_chain),
and external utils (db, config).
"""

from __future__ import annotations

import config as _config
from governance.models import CleanupPolicy, GovernanceContext, PolicySource
from governance.resolver import _build_scope_chain
from utils import db

# Import metrics lazily to avoid circular issues at module init
try:
    from services import metrics as _metrics
except Exception:
    _metrics = None  # type: ignore[assignment]


async def _resolve_cleanup_overrides(ctx: GovernanceContext) -> CleanupPolicy:
    """Resolve cleanup policy via scope fallback: thread > channel > category > guild.

    Default preserves backwards-compatible behavior (config whitelist logic).
    """
    chain = _build_scope_chain(ctx)
    for scope_type, scope_id in chain:
        if scope_type in ("role", "thread"):
            continue  # cleanup_policies doesn't support role/thread scope
        row = await db.get_cleanup_policy(ctx.guild_id, scope_type, scope_id)
        if row is not None:
            source_map = {
                "channel": PolicySource.CHANNEL_OVERRIDE,
                "category": PolicySource.CATEGORY_OVERRIDE,
                "guild": PolicySource.GUILD_OVERRIDE,
            }
            return CleanupPolicy(
                delete_message=row["delete_invalid_commands"],
                delete_after_seconds=row["delete_after_seconds"],
                send_feedback=True,
                resolved_from=source_map.get(scope_type, PolicySource.GUILD_OVERRIDE),
            )

    # Backwards-compatible default: behave like config.CLEANUP_WHITELIST_CHANNELS
    if ctx.channel_id and ctx.channel_id in _config.CLEANUP_WHITELIST_CHANNELS:
        return CleanupPolicy(
            delete_message=False,
            delete_after_seconds=0,
            send_feedback=False,
            resolved_from=PolicySource.FALLBACK_DEFAULT,
        )
    return CleanupPolicy(
        delete_message=True,
        delete_after_seconds=5,
        send_feedback=True,
        resolved_from=PolicySource.FALLBACK_DEFAULT,
    )


async def resolve_cleanup_policy(ctx: GovernanceContext) -> CleanupPolicy:
    """Resolve cleanup behavior for this context."""
    return await _resolve_cleanup_overrides(ctx)
