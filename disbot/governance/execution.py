"""Governance execution resolution — independent of visibility (ISSUE-008).

Layer: models → events → cache → dependency → resolver → cleanup → execution.
Imports from governance.models, governance.events, governance.resolver.
"""

from __future__ import annotations

import logging
import time

from governance.events import (
    EVT_EXECUTION_ALLOWED,
    EVT_EXECUTION_DENIED,
    _emit_governance_event,
)
from governance.models import ExecutionResult, ExecutionTrace, GovernanceContext
from governance.resolver import resolve_visibility
from utils import db
from utils.subsystem_registry import CAPABILITY_TO_SUBSYSTEM

logger = logging.getLogger("bot")

# Import metrics lazily to avoid circular issues at module init
try:
    from services import metrics as _metrics
except Exception:
    _metrics = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# In-memory capability execution overrides (ISSUE-008)
# Seeded from DB table `capability_execution_overrides` if it exists.
# Simple dict: (guild_id, capability) → bool
# ---------------------------------------------------------------------------

_capability_execution_overrides: dict[tuple[int, str], bool] = {}
_loaded_guilds: set[int] = set()

# Guild → monotonic timestamp of last successful override load (DEBT-001).
# Used to bound staleness: long-running processes will never serve overrides
# older than _OVERRIDE_TTL without a deterministic refresh from DB.  Cache TTL
# is intentionally coarse because capability_execution_overrides is rarely
# mutated; the goal is bounded drift, not zero drift.
_loaded_guilds_at: dict[int, float] = {}
_OVERRIDE_TTL: float = 600.0  # 10 minutes


async def _load_capability_overrides(guild_id: int) -> None:
    """Load capability overrides from DB for a guild.

    Reloads are deterministic: any prior entries for this guild are cleared
    before the fresh row set is inserted, so stale rows cannot survive a
    refresh.  Fails gracefully if the capability_execution_overrides table
    does not yet exist (legacy deployments).
    """
    # Clear any existing entries so a reload cannot leave stale rows behind.
    stale_keys = [k for k in _capability_execution_overrides if k[0] == guild_id]
    for k in stale_keys:
        _capability_execution_overrides.pop(k, None)

    try:
        rows = await db.get().fetch(
            """SELECT capability, allowed
               FROM capability_execution_overrides
               WHERE guild_id = $1""",
            guild_id,
        )
        for row in rows:
            _capability_execution_overrides[(guild_id, row["capability"])] = row[
                "allowed"
            ]
    except Exception as exc:
        # Table may not exist yet — fail gracefully
        logger.debug("capability_execution_overrides table not available: %s", exc)

    _loaded_guilds_at[guild_id] = time.monotonic()


def _check_capability_override(guild_id: int, capability: str) -> bool | None:
    """Return explicit override (True/False) or None if no override set."""
    return _capability_execution_overrides.get((guild_id, capability))


def _overrides_stale(guild_id: int) -> bool:
    """True if this guild's override cache is older than _OVERRIDE_TTL."""
    loaded_at = _loaded_guilds_at.get(guild_id)
    if loaded_at is None:
        return True
    return (time.monotonic() - loaded_at) > _OVERRIDE_TTL


def forget_guild_capabilities(guild_id: int) -> None:
    """Clear all capability override state for a guild.

    Called from guild_lifecycle.teardown() when the bot leaves a guild so
    that _loaded_guilds and _capability_execution_overrides do not hold stale
    data if the bot later rejoins the same guild.

    This function is intentionally not called from governance.cache.forget_guild()
    to avoid a backward import (cache layer must not import execution layer).
    The guild_lifecycle module coordinates both calls in the correct order.
    """
    _loaded_guilds.discard(guild_id)
    _loaded_guilds_at.pop(guild_id, None)
    stale_keys = [k for k in _capability_execution_overrides if k[0] == guild_id]
    for k in stale_keys:
        _capability_execution_overrides.pop(k, None)
    logger.debug("Cleared capability overrides for guild=%d", guild_id)


async def _audit_internal_bypass(
    ctx: GovernanceContext,
    capability: str,
    subsystem_name: str,
) -> None:
    """Persist a DB audit row for an internal/AI-triggered execution bypass.

    Internal bypasses skip the visibility gate; without a durable audit row the
    only record is the EVT_EXECUTION_ALLOWED event (in-process, non-persistent).
    This function writes a fact row to governance_audit_log so AI/scheduled
    invocations remain reconstructable from the DB alone.

    Best-effort: an audit failure must not prevent the legitimate execution
    from proceeding (the bypass decision is already made).  Errors are logged
    at WARNING and swallowed.
    """
    try:
        await db.write_governance_audit(
            guild_id=ctx.guild_id,
            actor_id=ctx.member.id if ctx.member else 0,
            action="execution_bypass",
            scope_type=None,
            scope_id=None,
            subsystem=subsystem_name,
            old_value=None,
            new_value={
                "capability": capability,
                "subsystem": subsystem_name,
                "reason": "internal_or_ai_invocation",
                "visibility_check_skipped": True,
            },
        )
    except Exception as exc:
        logger.warning(
            "internal bypass audit write failed (capability=%r guild=%d): %s",
            capability,
            ctx.guild_id,
            exc,
        )


# ---------------------------------------------------------------------------
# Public resolve_execution
# ---------------------------------------------------------------------------


async def resolve_execution(
    ctx: GovernanceContext,
    capability: str,
    check_visibility: bool = True,
) -> ExecutionResult:
    """Determine if a capability is executable in this context.

    Parameters
    ----------
    ctx:
        Governance context for the request.
    capability:
        The capability string to check (e.g. "moderation.member.ban").
    check_visibility:
        When True (default, user-facing): gate on visibility resolution.
        When False (internal/AI-triggered): skip the visibility gate.
        An explicit denial in capability_execution_overrides always wins.
    """
    # Deterministic refresh: first access OR cache older than _OVERRIDE_TTL.
    # _load_capability_overrides() clears stale rows before reloading so a
    # refresh cannot leave drift behind.
    if ctx.guild_id not in _loaded_guilds or _overrides_stale(ctx.guild_id):
        await _load_capability_overrides(ctx.guild_id)
        _loaded_guilds.add(ctx.guild_id)

    subsystem_name = CAPABILITY_TO_SUBSYSTEM.get(capability)

    if not subsystem_name:
        # Unknown capabilities fail CLOSED (Phase 1.4 — ARCH-005 fix).
        # A typo in a capability string must never silently grant access.
        logger.warning(
            "resolve_execution: unknown capability %r — denying (fail-closed). "
            "Check CAPABILITY_TO_SUBSYSTEM in subsystem_registry.",
            capability,
        )
        return ExecutionResult(
            allowed=False,
            reason="Unknown capability — denied (fail-closed)",
            trace=ExecutionTrace(
                capability=capability,
                checked_scopes=[],
                matched_scope=None,
                denied_by="unknown_capability",
                final_result=False,
            ),
        )

    # Check explicit overrides first — these always win regardless of check_visibility
    explicit_override = _check_capability_override(ctx.guild_id, capability)
    if explicit_override is not None:
        allowed = explicit_override
        denied_by = "capability_override" if not allowed else None
        if not allowed and _metrics:
            _metrics.governance_denials_total.labels(
                subsystem=subsystem_name, scope="override"
            ).inc()
        evt = EVT_EXECUTION_DENIED if not allowed else EVT_EXECUTION_ALLOWED
        await _emit_governance_event(
            evt,
            {
                "guild_id": ctx.guild_id,
                "capability": capability,
                "subsystem": subsystem_name,
                "denied_by": denied_by,
            },
        )
        return ExecutionResult(
            allowed=allowed,
            reason=denied_by,
            resolved_scope="override",
            matched_capability=capability if allowed else None,
            trace=ExecutionTrace(
                capability=capability,
                checked_scopes=[],
                matched_scope="override",
                denied_by=denied_by,
                final_result=allowed,
            ),
        )

    # When check_visibility=False (internal/AI-triggered): skip visibility gate.
    # The "bypass": True flag in the event payload marks the event stream; the
    # accompanying audit row makes the bypass reconstructable from the DB alone
    # (DEBT-002 — required before AI/plugin expansion).
    if not check_visibility:
        logger.info(
            "resolve_execution: internal bypass for capability=%r subsystem=%r guild=%d",
            capability,
            subsystem_name,
            ctx.guild_id,
        )
        await _audit_internal_bypass(ctx, capability, subsystem_name)
        await _emit_governance_event(
            EVT_EXECUTION_ALLOWED,
            {
                "guild_id": ctx.guild_id,
                "capability": capability,
                "subsystem": subsystem_name,
                "bypass": True,
            },
        )
        return ExecutionResult(
            allowed=True,
            reason="Internal/AI-triggered — visibility gate skipped",
            resolved_scope=None,
            matched_capability=capability,
            trace=ExecutionTrace(
                capability=capability,
                checked_scopes=[],
                matched_scope=None,
                denied_by=None,
                final_result=True,
            ),
        )

    # Default path (check_visibility=True): gate on visibility
    vis = await resolve_visibility(ctx)

    allowed = subsystem_name in vis.visible_subsystems
    trace_obj = vis.traces.get(subsystem_name)
    denied_by = trace_obj.final_state.value if trace_obj and not allowed else None

    if not allowed:
        scope_label = (
            trace_obj.matched_scope.value
            if trace_obj and trace_obj.matched_scope
            else "unknown"
        )
        if _metrics:
            _metrics.governance_denials_total.labels(
                subsystem=subsystem_name, scope=scope_label
            ).inc()
        await _emit_governance_event(
            EVT_EXECUTION_DENIED,
            {
                "guild_id": ctx.guild_id,
                "capability": capability,
                "subsystem": subsystem_name,
                "denied_by": denied_by,
            },
        )
    else:
        await _emit_governance_event(
            EVT_EXECUTION_ALLOWED,
            {
                "guild_id": ctx.guild_id,
                "capability": capability,
                "subsystem": subsystem_name,
            },
        )

    return ExecutionResult(
        allowed=allowed,
        reason=denied_by,
        resolved_scope=(
            trace_obj.matched_scope.value
            if trace_obj and trace_obj.matched_scope
            else None
        ),
        matched_capability=capability if allowed else None,
        trace=ExecutionTrace(
            capability=capability,
            checked_scopes=trace_obj.checked_scopes if trace_obj else [],
            matched_scope=(
                trace_obj.matched_scope.value
                if trace_obj and trace_obj.matched_scope
                else None
            ),
            denied_by=denied_by,
            final_result=allowed,
        ),
    )
