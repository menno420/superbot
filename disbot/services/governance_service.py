"""Legacy entry point — explicit re-exports of the governance public API.

Older call sites and unit tests import names through this module:

    from services.governance_service import resolve_visibility, GovernanceContext

New code should import directly from the ``governance`` package:

    from governance import resolve_visibility, GovernanceContext

This file provides explicit re-exports rather than the previous wildcard
(``from governance import *``) so the public surface is visible at a glance
and additions to ``governance.__all__`` no longer silently extend the shim.

Private helpers re-exported below are exclusively for the governance unit
test suite (tests/unit/governance/*).  Do not import them from production
code.
"""

from __future__ import annotations

from governance import (
    _FEEDBACK_COOLDOWN,  # noqa: F401 — legacy test access
    EVT_CACHE_INVALIDATED,
    EVT_CLEANUP_CHANGED,
    EVT_EXECUTION_ALLOWED,
    EVT_EXECUTION_DENIED,
    EVT_VISIBILITY_CHANGED,
    SCOPE_PARENT,
    SCOPE_PRIORITY,
    CleanupPolicy,
    CommandPolicy,
    ExecutionResult,
    ExecutionTrace,
    GovernanceCacheBackend,
    GovernanceContext,
    GovernanceDiff,
    GovernanceError,
    GovernanceHealthReport,
    GovernanceMutationPipeline,
    GovernanceSnapshot,
    GovernanceTemplate,
    PolicySource,
    ResolutionTrace,
    SubsystemEffectiveState,
    SubsystemState,
    UnauthorizedGovernanceWriteError,
    VisibilityResult,
    apply_template,
    build_governance_snapshot,
    check_governance_version,
    diff_governance_snapshots,
    export_template,
    forget_guild,
    get_visible_subsystems,
    invalidate_guild_cache,
    load_template,
    register_failed_subsystems,
    resolve_all_capabilities,
    resolve_all_subsystem_visibility,
    resolve_cleanup_policy,
    resolve_command_policy,
    resolve_execution,
    resolve_subsystem_state,
    resolve_visibility,
    run_governance_healthcheck,
    save_template,
    set_cleanup_policy_for_scope,
    set_subsystem_visibility,
)

# ---------------------------------------------------------------------------
# Private implementation details re-exported strictly for the existing
# governance unit-test suite.  Production code must not depend on these.
# ---------------------------------------------------------------------------
from governance.cache import (  # noqa: F401
    _CACHE,
    _CACHE_TTL,
    _CACHE_VERSION,
    _FAILED_SUBSYSTEMS,
    _cache_get,
    _cache_key,
    _cache_set,
    _guild_has_role_overrides,
)
from governance.dependency import _apply_dependency_rules  # noqa: F401
from governance.resolver import (  # noqa: F401
    _build_scope_chain,
    _resolve_single_subsystem,
)

__all__ = [
    "EVT_CACHE_INVALIDATED",
    "EVT_CLEANUP_CHANGED",
    "EVT_EXECUTION_ALLOWED",
    "EVT_EXECUTION_DENIED",
    "EVT_VISIBILITY_CHANGED",
    "SCOPE_PARENT",
    "SCOPE_PRIORITY",
    "CleanupPolicy",
    "CommandPolicy",
    "ExecutionResult",
    "ExecutionTrace",
    "GovernanceCacheBackend",
    "GovernanceContext",
    "GovernanceDiff",
    "GovernanceError",
    "GovernanceHealthReport",
    "GovernanceMutationPipeline",
    "GovernanceSnapshot",
    "GovernanceTemplate",
    "PolicySource",
    "ResolutionTrace",
    "SubsystemEffectiveState",
    "SubsystemState",
    "UnauthorizedGovernanceWriteError",
    "VisibilityResult",
    "apply_template",
    "build_governance_snapshot",
    "check_governance_version",
    "diff_governance_snapshots",
    "export_template",
    "forget_guild",
    "get_visible_subsystems",
    "invalidate_guild_cache",
    "load_template",
    "register_failed_subsystems",
    "resolve_all_capabilities",
    "resolve_all_subsystem_visibility",
    "resolve_cleanup_policy",
    "resolve_command_policy",
    "resolve_execution",
    "resolve_subsystem_state",
    "resolve_visibility",
    "run_governance_healthcheck",
    "save_template",
    "set_cleanup_policy_for_scope",
    "set_subsystem_visibility",
]
