"""Governance package — public API.

All public names are re-exported here so callers can import from either:
  - ``governance`` (new code)
  - ``services.governance_service`` (legacy, backward-compatible thin wrapper)

Layer order (no circular imports):
  models → events → cache → dependency → resolver → cleanup → execution
         → snapshot → health → writes
"""

from __future__ import annotations

import time as _time

import discord

# NOTE: ``from core.runtime import resources`` deliberately omitted at
# module scope to avoid a circular import.  ``core/runtime/__init__.py``
# imports Phase 2b's ``bindings`` submodule, which transitively pulls
# in ``governance.permission_tiers`` via ``core.resources.role_service``;
# re-entering this ``governance/__init__.py`` mid-load and reaching back
# into ``core.runtime`` crashes with ``ImportError: cannot import name
# 'resources'``.  The single consumer (``_find_redirect_channel`` below)
# imports the alias locally instead.
from governance.cache import (  # noqa: F401
    GovernanceCacheBackend,
    forget_guild,
    invalidate_guild_cache,
    register_failed_subsystems,
)
from governance.cleanup import resolve_cleanup_policy  # noqa: F401
from governance.events import (  # noqa: F401
    EVT_CACHE_INVALIDATED,
    EVT_CLEANUP_CHANGED,
    EVT_EXECUTION_ALLOWED,
    EVT_EXECUTION_DENIED,
    EVT_VISIBILITY_CHANGED,
)
from governance.execution import resolve_execution  # noqa: F401
from governance.health import run_governance_healthcheck  # noqa: F401
from governance.models import (  # noqa: F401
    SCOPE_PARENT,
    SCOPE_PRIORITY,
    CleanupPolicy,
    CommandPolicy,
    ExecutionResult,
    ExecutionTrace,
    GovernanceContext,
    GovernanceDiff,
    GovernanceHealthReport,
    GovernanceSnapshot,
    PolicySource,
    ResolutionTrace,
    SubsystemEffectiveState,
    SubsystemState,
    VisibilityResult,
)
from governance.resolver import get_visible_subsystems, resolve_visibility  # noqa: F401
from governance.snapshot import (  # noqa: F401
    build_governance_snapshot,
    diff_governance_snapshots,
)
from governance.templates import (  # noqa: F401
    GovernanceTemplate,
    apply_template,
    export_template,
    load_template,
    save_template,
)
from governance.writes import (  # noqa: F401
    GovernanceMutationPipeline,
    check_governance_version,
    set_cleanup_policy_for_scope,
    set_subsystem_visibility,
)
from services.governance_exceptions import (  # noqa: F401
    GovernanceError,
    UnauthorizedGovernanceWriteError,
)
from utils.subsystem_registry import (
    CAPABILITY_TO_SUBSYSTEM,
    SUBSYSTEMS,
    get_subsystem_for_command,
)

# ---------------------------------------------------------------------------
# Composite public functions that span multiple layers
# (kept here rather than in any single submodule to avoid circular imports)
# ---------------------------------------------------------------------------


async def resolve_command_policy(
    ctx: GovernanceContext,
    command_name: str,
) -> CommandPolicy:
    """Full policy resolution for a message command invocation attempt.

    Returns allowed=True for unknown commands (not a governance concern).
    """
    found = get_subsystem_for_command(command_name)
    if found is None:
        # Unknown command — not a governance concern
        return CommandPolicy(
            allowed=True,
            cleanup=CleanupPolicy(
                delete_message=False,
                delete_after_seconds=0,
                send_feedback=False,
                resolved_from=PolicySource.REGISTRY_DEFAULT,
            ),
            feedback=None,
            redirect_channel_mention=None,
        )

    subsystem_name, subsystem_meta = found
    visible = await get_visible_subsystems(ctx)

    if subsystem_name in visible:
        return CommandPolicy(
            allowed=True,
            cleanup=CleanupPolicy(
                delete_message=False,
                delete_after_seconds=0,
                send_feedback=False,
                resolved_from=PolicySource.REGISTRY_DEFAULT,
            ),
            feedback=None,
            redirect_channel_mention=None,
        )

    # Blocked — build cleanup + feedback
    cleanup = await resolve_cleanup_policy(ctx)
    guild = ctx.member.guild if ctx.member else None
    redirect = _find_redirect_channel(guild, subsystem_meta)

    send_fb = cleanup.send_feedback and _should_send_feedback(
        ctx.channel_id or 0,
        subsystem_name,
    )
    feedback = _build_feedback(subsystem_meta, redirect) if send_fb else None

    return CommandPolicy(
        allowed=False,
        cleanup=cleanup,
        feedback=feedback,
        redirect_channel_mention=redirect,
    )


async def resolve_all_subsystem_visibility(
    ctx: GovernanceContext,
) -> dict[str, bool]:
    """All subsystems with resolved enabled state."""
    result = await resolve_visibility(ctx)
    return {name: (name in result.visible_subsystems) for name in SUBSYSTEMS}


async def resolve_all_capabilities(ctx: GovernanceContext) -> dict[str, bool]:
    """All capabilities with resolved allowed state."""
    visible = await get_visible_subsystems(ctx)
    return {
        cap: (subsystem in visible)
        for cap, subsystem in CAPABILITY_TO_SUBSYSTEM.items()
    }


async def resolve_subsystem_state(
    ctx: GovernanceContext,
    subsystem_name: str,
) -> SubsystemEffectiveState:
    """Complete resolved state for one subsystem. Powers /why, admin diagnostics."""
    vis = await resolve_visibility(ctx)
    cleanup = await resolve_cleanup_policy(ctx)

    state = (
        SubsystemState.ENABLED
        if subsystem_name in vis.visible_subsystems
        else SubsystemState.DISABLED
    )
    trace = vis.traces.get(
        subsystem_name,
        ResolutionTrace(
            subsystem=subsystem_name,
            checked_scopes=[],
            matched_scope=None,
            dependency_blocks=[],
            final_state=state,
        ),
    )
    source = vis.resolved_from.get(subsystem_name, PolicySource.REGISTRY_DEFAULT)

    return SubsystemEffectiveState(
        name=subsystem_name,
        state=trace.final_state,
        visibility_source=source,
        execution_allowed=subsystem_name in vis.visible_subsystems,
        execution_source=source,
        dependency_blocks=trace.dependency_blocks,
        cleanup_policy=cleanup,
        trace=trace,
    )


# ---------------------------------------------------------------------------
# Internal helpers (re-used by resolve_command_policy)
# ---------------------------------------------------------------------------

_FEEDBACK_COOLDOWN: dict[tuple[int, str], float] = {}
_FEEDBACK_COOLDOWN_SECS = 10


def _should_send_feedback(channel_id: int, subsystem: str) -> bool:
    key = (channel_id, subsystem)
    now = _time.monotonic()
    if now - _FEEDBACK_COOLDOWN.get(key, 0.0) > _FEEDBACK_COOLDOWN_SECS:
        _FEEDBACK_COOLDOWN[key] = now
        if len(_FEEDBACK_COOLDOWN) > 500:
            expired = [
                k
                for k, ts in _FEEDBACK_COOLDOWN.items()
                if now - ts > _FEEDBACK_COOLDOWN_SECS
            ]
            for k in expired:
                del _FEEDBACK_COOLDOWN[k]
        return True
    return False


def _find_redirect_channel(
    guild: discord.Guild | None,
    subsystem_meta: dict,
) -> str | None:
    from core.runtime import guild_resources

    if guild is None:
        return None
    for ch_name in subsystem_meta.get("default_channels", []):
        ch = guild_resources.resolve_channel(guild, name=ch_name)
        if ch:
            return ch.mention
    return None


def _build_feedback(subsystem_meta: dict, redirect: str | None) -> str:
    name = subsystem_meta.get("display_name", "This")
    emoji = subsystem_meta.get("emoji", "❌")
    if redirect:
        return f"{emoji} **{name}** commands are disabled here. Use {redirect} instead."
    return f"{emoji} **{name}** commands are disabled in this channel."


__all__ = [
    # models
    "SCOPE_PARENT",
    "SCOPE_PRIORITY",
    "CleanupPolicy",
    "CommandPolicy",
    "ExecutionResult",
    "ExecutionTrace",
    "GovernanceContext",
    "GovernanceDiff",
    "GovernanceError",
    "GovernanceHealthReport",
    "GovernanceSnapshot",
    "PolicySource",
    "ResolutionTrace",
    "SubsystemEffectiveState",
    "SubsystemState",
    "VisibilityResult",
    # events
    "EVT_CACHE_INVALIDATED",
    "EVT_CLEANUP_CHANGED",
    "EVT_EXECUTION_ALLOWED",
    "EVT_EXECUTION_DENIED",
    "EVT_VISIBILITY_CHANGED",
    # cache
    "GovernanceCacheBackend",
    "forget_guild",
    "invalidate_guild_cache",
    "register_failed_subsystems",
    # resolver
    "get_visible_subsystems",
    "resolve_visibility",
    # cleanup
    "resolve_cleanup_policy",
    # execution
    "resolve_execution",
    # snapshot
    "build_governance_snapshot",
    "diff_governance_snapshots",
    # health
    "run_governance_healthcheck",
    # writes
    "GovernanceMutationPipeline",
    "UnauthorizedGovernanceWriteError",
    "check_governance_version",
    "set_cleanup_policy_for_scope",
    "set_subsystem_visibility",
    # templates
    "GovernanceTemplate",
    "apply_template",
    "export_template",
    "load_template",
    "save_template",
    # composite
    "resolve_all_capabilities",
    "resolve_all_subsystem_visibility",
    "resolve_command_policy",
    "resolve_subsystem_state",
]
