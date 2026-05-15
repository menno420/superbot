"""Backward-compatibility re-export. Import from governance package directly for new code."""

from governance import *  # noqa: F401, F403
from governance import _FEEDBACK_COOLDOWN  # noqa: F401
from governance import (  # explicit re-exports for IDE support (public API)
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
    GovernanceSnapshot,
    GovernanceTemplate,
    PolicySource,
    ResolutionTrace,
    SubsystemEffectiveState,
    SubsystemState,
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

# Private internals re-exported for backward compatibility with unit tests.
# These are implementation details; prefer importing from governance.* directly.
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
