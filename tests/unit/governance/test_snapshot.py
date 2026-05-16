"""Tests for GovernanceSnapshot serialization.

Covers the behaviour that matters for clients:
- build_governance_snapshot returns a GovernanceSnapshot
- to_dict() output is JSON-safe (no sets / Enums / datetimes leak)
- visible + denied subsystem sets are mutually exclusive and cover
  all subsystems (invariant — drift breaks help rendering)
- capability_map keys mirror the registry
- Disabling economy propagates to dependents (inventory, mining)
- CleanupPolicy.to_dict serializes the Enum to its value

Deletions (P1 PR-5):
  Five shallow shape-only checks dropped because they enforced
  implementation details (key presence, sorted-list ordering,
  primitive types) without protecting behaviour:
  - test_snapshot_to_dict_has_all_required_keys
  - test_member_tier_is_user_when_no_member
  - test_capability_map_values_are_booleans
  - test_to_dict_visible_subsystems_is_sorted_list
  - test_to_dict_scope_provenance_values_are_strings
"""

from __future__ import annotations

import json

import pytest

from services.governance_service import (
    CleanupPolicy,
    GovernanceSnapshot,
    PolicySource,
    SubsystemState,
    build_governance_snapshot,
)
from utils.subsystem_registry import SUBSYSTEMS

from .conftest import make_ctx, make_visibility_row

# ---------------------------------------------------------------------------
# Snapshot construction & JSON safety
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_build_snapshot_returns_governance_snapshot(mock_db):
    ctx = make_ctx()
    snapshot = await build_governance_snapshot(ctx)
    assert isinstance(snapshot, GovernanceSnapshot)


@pytest.mark.asyncio
async def test_snapshot_to_dict_is_json_serializable(mock_db):
    """to_dict() must produce only JSON-safe primitives (no sets, Enums, datetimes)."""
    ctx = make_ctx()
    snapshot = await build_governance_snapshot(ctx)
    d = snapshot.to_dict()
    # This raises TypeError or ValueError if any value is not JSON-serializable.
    json.dumps(d)


# ---------------------------------------------------------------------------
# Visible / denied coverage
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_visible_and_denied_are_mutually_exclusive(mock_db):
    ctx = make_ctx()
    snapshot = await build_governance_snapshot(ctx)
    assert snapshot.visible_subsystems.isdisjoint(snapshot.denied_subsystems)


@pytest.mark.asyncio
async def test_visible_and_denied_cover_all_subsystems(mock_db):
    ctx = make_ctx()
    snapshot = await build_governance_snapshot(ctx)
    all_names = set(SUBSYSTEMS.keys())
    assert snapshot.visible_subsystems | snapshot.denied_subsystems == all_names


# ---------------------------------------------------------------------------
# Capability map
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_capability_map_contains_all_registry_capabilities(mock_db):
    from utils.subsystem_registry import CAPABILITY_TO_SUBSYSTEM

    ctx = make_ctx()
    snapshot = await build_governance_snapshot(ctx)
    assert set(snapshot.capability_map.keys()) == set(CAPABILITY_TO_SUBSYSTEM.keys())


# ---------------------------------------------------------------------------
# Dependency block reflection in snapshot
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_disabled_economy_appears_in_denied_and_blocks_dependents(mock_db):
    ctx = make_ctx(guild_id=100, channel_id=200, category_id=300)
    mock_db.fetch.return_value = [
        make_visibility_row("guild", 100, "economy", False),
    ]
    snapshot = await build_governance_snapshot(ctx)
    assert "economy" in snapshot.denied_subsystems
    assert "inventory" in snapshot.denied_subsystems
    assert "mining" in snapshot.denied_subsystems


@pytest.mark.asyncio
async def test_dependency_blocks_dict_populated_for_blocked_dependents(mock_db):
    ctx = make_ctx(guild_id=100, channel_id=200, category_id=300)
    mock_db.fetch.return_value = [
        make_visibility_row("guild", 100, "economy", False),
    ]
    snapshot = await build_governance_snapshot(ctx)
    assert "inventory" in snapshot.dependency_blocks
    assert "economy" in snapshot.dependency_blocks["inventory"]


# ---------------------------------------------------------------------------
# CleanupPolicy.to_dict
# ---------------------------------------------------------------------------


def test_cleanup_policy_to_dict_structure():
    policy = CleanupPolicy(
        delete_message=True,
        delete_after_seconds=5,
        send_feedback=True,
        resolved_from=PolicySource.FALLBACK_DEFAULT,
    )
    d = policy.to_dict()
    assert d["delete_message"] is True
    assert d["delete_after_seconds"] == 5
    assert d["send_feedback"] is True
    assert d["resolved_from"] == PolicySource.FALLBACK_DEFAULT.value
