"""Governance snapshot building and diff computation.

Layer: models → ... → resolver → cleanup → execution → snapshot.
Imports from governance.models, governance.resolver, governance.cleanup.
"""

from __future__ import annotations

from governance.cleanup import resolve_cleanup_policy
from governance.models import GovernanceContext, GovernanceDiff, GovernanceSnapshot
from governance.resolver import get_visible_subsystems, resolve_visibility
from utils.subsystem_registry import (
    CAPABILITY_TO_SUBSYSTEM,
    REGISTRY_SCHEMA_VERSION,
    REGISTRY_VERSION,
    SUBSYSTEMS,
)


async def _resolve_all_capabilities(ctx: GovernanceContext) -> dict[str, bool]:
    """All capabilities with resolved allowed state."""
    visible = await get_visible_subsystems(ctx)
    return {
        cap: (subsystem in visible)
        for cap, subsystem in CAPABILITY_TO_SUBSYSTEM.items()
    }


async def build_governance_snapshot(ctx: GovernanceContext) -> GovernanceSnapshot:
    """Complete governance state for a context.

    Powers dashboards, /why, AI reasoning, diagnostics.
    """
    vis = await resolve_visibility(ctx)
    cleanup = await resolve_cleanup_policy(ctx)
    cap_map = await _resolve_all_capabilities(ctx)

    all_names = set(SUBSYSTEMS.keys())
    denied = all_names - vis.visible_subsystems
    dep_blocks: dict[str, list[str]] = {}
    for name, trace in vis.traces.items():
        if trace.dependency_blocks:
            dep_blocks[name] = trace.dependency_blocks

    return GovernanceSnapshot(
        visible_subsystems=vis.visible_subsystems,
        denied_subsystems=denied,
        dependency_blocks=dep_blocks,
        cleanup_policy=cleanup,
        member_tier=vis.member_tier,
        scope_provenance=vis.resolved_from,
        capability_map=cap_map,
        registry_version=REGISTRY_VERSION,
        registry_schema_version=REGISTRY_SCHEMA_VERSION,
    )


def diff_governance_snapshots(
    before: GovernanceSnapshot,
    after: GovernanceSnapshot,
) -> GovernanceDiff:
    """Compute the difference between two GovernanceSnapshots.

    Useful for change-review UI, audit log display, and detecting governance
    drift between a baseline and the current state.
    """
    added = after.visible_subsystems - before.visible_subsystems
    removed = before.visible_subsystems - after.visible_subsystems

    changed_sources: dict[str, tuple[str, str]] = {}
    all_subsystems = set(before.scope_provenance) | set(after.scope_provenance)
    for name in all_subsystems:
        old_src = before.scope_provenance.get(name)
        new_src = after.scope_provenance.get(name)
        if old_src != new_src:
            changed_sources[name] = (
                old_src.value if old_src else "none",
                new_src.value if new_src else "none",
            )

    cap_changes: dict[str, tuple[bool, bool]] = {}
    all_caps = set(before.capability_map) | set(after.capability_map)
    for cap in all_caps:
        old_val = before.capability_map.get(cap, False)
        new_val = after.capability_map.get(cap, False)
        if old_val != new_val:
            cap_changes[cap] = (old_val, new_val)

    cleanup_changed = before.cleanup_policy.to_dict() != after.cleanup_policy.to_dict()

    return GovernanceDiff(
        added_visible=added,
        removed_visible=removed,
        changed_sources=changed_sources,
        capability_changes=cap_changes,
        cleanup_changed=cleanup_changed,
    )
