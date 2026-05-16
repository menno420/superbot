"""Backward-compatibility re-export. Import from governance package directly for new code."""

from governance import *  # noqa: F401, F403
from governance import _FEEDBACK_COOLDOWN  # noqa: F401

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
