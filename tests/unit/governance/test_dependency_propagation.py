"""Tests for hard dependency propagation in governance.

inventory and mining both depend on economy (hard dep).
Disabling economy must block both dependents.

Tests operate on _apply_dependency_rules (pure function) and
resolve_visibility (integration, DB-mocked) to cover the full pipeline.
"""

from __future__ import annotations

import pytest

from services.governance_service import (
    PolicySource,
    ResolutionTrace,
    SubsystemState,
    _apply_dependency_rules,
    resolve_visibility,
)

from .conftest import make_ctx, make_visibility_row


# ---------------------------------------------------------------------------
# Pure unit tests — _apply_dependency_rules
# ---------------------------------------------------------------------------


def _make_states_traces(subsystems_states: dict[str, SubsystemState]):
    """Build minimal states, traces, resolved_from dicts for _apply_dependency_rules."""
    states = dict(subsystems_states)
    traces = {
        name: ResolutionTrace(
            subsystem=name,
            checked_scopes=[],
            matched_scope=None,
            dependency_blocks=[],
            final_state=state,
        )
        for name, state in subsystems_states.items()
    }
    resolved_from = {name: PolicySource.REGISTRY_DEFAULT for name in subsystems_states}
    return states, traces, resolved_from


def test_disabled_dep_blocks_direct_dependent():
    """economy DISABLED → inventory BLOCKED_DEPENDENCY."""
    # Build state with economy disabled and inventory enabled.
    # We need all subsystems the registry knows about to avoid KeyErrors in the
    # topological order loop; easiest: start from a full ENABLED dict and override.
    from utils.subsystem_registry import SUBSYSTEMS

    all_enabled = {name: SubsystemState.ENABLED for name in SUBSYSTEMS}
    all_enabled["economy"] = SubsystemState.DISABLED
    states, traces, resolved_from = _make_states_traces(all_enabled)

    _apply_dependency_rules(states, traces, resolved_from)

    assert states["inventory"] is SubsystemState.BLOCKED_DEPENDENCY
    assert resolved_from["inventory"] is PolicySource.DEPENDENCY_BLOCK
    assert "economy" in traces["inventory"].dependency_blocks


def test_disabled_dep_blocks_two_dependents():
    """economy DISABLED → both inventory AND mining BLOCKED."""
    from utils.subsystem_registry import SUBSYSTEMS

    all_enabled = {name: SubsystemState.ENABLED for name in SUBSYSTEMS}
    all_enabled["economy"] = SubsystemState.DISABLED
    states, traces, resolved_from = _make_states_traces(all_enabled)

    _apply_dependency_rules(states, traces, resolved_from)

    assert states["inventory"] is SubsystemState.BLOCKED_DEPENDENCY
    assert states["mining"] is SubsystemState.BLOCKED_DEPENDENCY


def test_enabled_dep_does_not_block_dependent():
    """economy ENABLED → inventory stays ENABLED."""
    from utils.subsystem_registry import SUBSYSTEMS

    all_enabled = {name: SubsystemState.ENABLED for name in SUBSYSTEMS}
    states, traces, resolved_from = _make_states_traces(all_enabled)

    _apply_dependency_rules(states, traces, resolved_from)

    assert states["inventory"] is SubsystemState.ENABLED
    assert states["mining"] is SubsystemState.ENABLED


def test_already_disabled_dependent_stays_disabled():
    """A dependent that is already DISABLED stays DISABLED (not BLOCKED_DEPENDENCY)."""
    from utils.subsystem_registry import SUBSYSTEMS

    all_enabled = {name: SubsystemState.ENABLED for name in SUBSYSTEMS}
    all_enabled["economy"] = SubsystemState.DISABLED
    all_enabled["inventory"] = SubsystemState.DISABLED  # already off
    states, traces, resolved_from = _make_states_traces(all_enabled)

    _apply_dependency_rules(states, traces, resolved_from)

    # The dep-block rule only fires when dependent is ENABLED.
    assert states["inventory"] is SubsystemState.DISABLED


def test_blocked_dep_propagates_to_dependent():
    """If dep is BLOCKED_DEPENDENCY, its dependents are also blocked (chain blocking)."""
    from utils.subsystem_registry import SUBSYSTEMS

    all_enabled = {name: SubsystemState.ENABLED for name in SUBSYSTEMS}
    all_enabled["economy"] = SubsystemState.BLOCKED_DEPENDENCY
    states, traces, resolved_from = _make_states_traces(all_enabled)

    _apply_dependency_rules(states, traces, resolved_from)

    assert states["inventory"] is SubsystemState.BLOCKED_DEPENDENCY
    assert states["mining"] is SubsystemState.BLOCKED_DEPENDENCY


# ---------------------------------------------------------------------------
# Integration tests — resolve_visibility with dependency propagation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_economy_disabled_hides_inventory_and_mining(mock_db):
    """resolve_visibility: economy guild-disabled → inventory + mining not visible."""
    ctx = make_ctx(guild_id=100, channel_id=200, category_id=300)
    mock_db.fetch.return_value = [
        make_visibility_row("guild", 100, "economy", False),
    ]

    result = await resolve_visibility(ctx)

    assert "economy" not in result.visible_subsystems
    assert "inventory" not in result.visible_subsystems
    assert "mining" not in result.visible_subsystems


@pytest.mark.asyncio
async def test_economy_enabled_allows_dependents(mock_db):
    """resolve_visibility: economy not blocked → inventory and mining are visible."""
    ctx = make_ctx()  # no DB overrides
    result = await resolve_visibility(ctx)
    assert "economy" in result.visible_subsystems
    assert "inventory" in result.visible_subsystems
    assert "mining" in result.visible_subsystems


@pytest.mark.asyncio
async def test_dependency_block_recorded_in_trace(mock_db):
    """Trace for a blocked dependent records which dep caused the block."""
    ctx = make_ctx(guild_id=100, channel_id=200, category_id=300)
    mock_db.fetch.return_value = [
        make_visibility_row("guild", 100, "economy", False),
    ]

    result = await resolve_visibility(ctx)

    inv_trace = result.traces["inventory"]
    assert inv_trace.final_state is SubsystemState.BLOCKED_DEPENDENCY
    assert "economy" in inv_trace.dependency_blocks
