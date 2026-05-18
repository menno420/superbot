"""Phase 2a unit tests — ResourceStatus enum + tier classification."""

from __future__ import annotations

import pytest

from core.resources.status import STATUS_TIER, ResourceStatus, is_actionable


def test_resource_status_members():
    """Every documented status value is present."""
    expected = {"bound", "unresolved", "missing", "invalid"}
    actual = {s.value for s in ResourceStatus}
    assert actual == expected


def test_status_tier_covers_every_status():
    """Tier table is dense — every enum member has a tier."""
    for status in ResourceStatus:
        assert status in STATUS_TIER, f"missing tier for {status}"


@pytest.mark.parametrize(
    ("status", "expected_actionable"),
    [
        (ResourceStatus.BOUND, False),
        (ResourceStatus.UNRESOLVED, False),
        (ResourceStatus.MISSING, True),
        (ResourceStatus.INVALID, True),
    ],
)
def test_is_actionable(status, expected_actionable):
    """Only missing/invalid are repair-eligible; unresolved waits on probe."""
    assert is_actionable(status) is expected_actionable
