"""Governance dependency rule propagation.

Layer: models → events → cache → dependency.
Imports from governance.models only (within governance/).
"""

from __future__ import annotations

from governance.models import PolicySource, ResolutionTrace, SubsystemState
from utils.subsystem_registry import (
    _COMPILED_DEPENDENCY_ORDER,
    SUBSYSTEMS,
)


def _apply_dependency_rules(
    states: dict[str, SubsystemState],
    traces: dict[str, ResolutionTrace],
    resolved_from: dict[str, PolicySource],
) -> None:
    """Propagate hard dependency blocking using topological order.

    Modifies states, traces, and resolved_from in-place.
    Uses _COMPILED_DEPENDENCY_ORDER so deps are always processed before dependents.
    Soft dependencies are not propagated (future: UI hint only).
    """
    for subsystem in _COMPILED_DEPENDENCY_ORDER:
        if subsystem not in states:
            continue
        meta = SUBSYSTEMS.get(subsystem)
        if not meta:
            continue
        blocking_deps = [
            dep
            for dep in meta.get("dependencies", [])
            if states.get(dep)
            in (SubsystemState.DISABLED, SubsystemState.BLOCKED_DEPENDENCY)
        ]
        if blocking_deps and states[subsystem] == SubsystemState.ENABLED:
            states[subsystem] = SubsystemState.BLOCKED_DEPENDENCY
            resolved_from[subsystem] = PolicySource.DEPENDENCY_BLOCK
            if subsystem in traces:
                traces[subsystem].dependency_blocks.extend(blocking_deps)
                traces[subsystem].final_state = SubsystemState.BLOCKED_DEPENDENCY
                traces[subsystem].matched_scope = PolicySource.DEPENDENCY_BLOCK
