"""Governance execution resolution — independent of visibility (ISSUE-008).

Layer: models → events → cache → dependency → resolver → cleanup → execution.
Imports from governance.models, governance.events, governance.resolver.
"""

from __future__ import annotations

import logging

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


async def _load_capability_overrides(guild_id: int) -> None:
    """Load capability overrides from DB for a guild.

    Fails gracefully if the capability_execution_overrides table does not exist yet.
    """
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


def _check_capability_override(guild_id: int, capability: str) -> bool | None:
    """Return explicit override (True/False) or None if no override set."""
    return _capability_execution_overrides.get((guild_id, capability))


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
    subsystem_name = CAPABILITY_TO_SUBSYSTEM.get(capability)

    if not subsystem_name:
        return ExecutionResult(
            allowed=True,
            reason="Unknown capability — no governance restriction",
            trace=ExecutionTrace(
                capability=capability,
                checked_scopes=[],
                matched_scope=None,
                denied_by=None,
                final_result=True,
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

    # When check_visibility=False (internal/AI-triggered): skip visibility gate
    if not check_visibility:
        await _emit_governance_event(
            EVT_EXECUTION_ALLOWED,
            {
                "guild_id": ctx.guild_id,
                "capability": capability,
                "subsystem": subsystem_name,
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
