"""Tests for the BTD6 coverage registry (utils/btd6/coverage.py).

The registry is the single source of truth for "what data do we actually
have, and what are its limits" — consumed by command builders, panel
views, and AI grounding. These tests pin its completeness and the
read-only accessor contract.
"""

from __future__ import annotations

import pytest

from utils.btd6 import coverage
from utils.btd6.coverage import (
    AREA_BOSS,
    AREA_CAPABILITIES,
    AREA_ECONOMY,
    AREA_HERO_STATS,
    AREA_LEADERBOARDS,
    AREA_ODYSSEY,
    AREA_RACES,
    COVERAGE,
    CoverageArea,
    get_coverage,
)

_ALL_AREA_CONSTANTS = [
    AREA_LEADERBOARDS,
    AREA_BOSS,
    AREA_ODYSSEY,
    AREA_RACES,
    AREA_CAPABILITIES,
    AREA_HERO_STATS,
    AREA_ECONOMY,
]


def test_every_area_constant_is_registered() -> None:
    """Every exported AREA_* constant resolves to a registry entry."""
    for area in _ALL_AREA_CONSTANTS:
        entry = get_coverage(area)
        assert isinstance(entry, CoverageArea)
        # The entry's own `area` field round-trips the key.
        assert entry.area == area


def test_registry_has_no_unexpected_keys() -> None:
    assert set(COVERAGE) == set(_ALL_AREA_CONSTANTS)


@pytest.mark.parametrize("area", _ALL_AREA_CONSTANTS)
def test_labels_are_non_empty(area: str) -> None:
    entry = get_coverage(area)
    assert entry.limitation.strip()
    assert entry.user_label.strip()
    assert entry.staff_label.strip()
    assert entry.completeness in ("full", "partial", "none")


def test_economy_is_unsupported() -> None:
    entry = get_coverage(AREA_ECONOMY)
    assert entry.supported is False
    assert entry.completeness == "none"


def test_partial_areas_are_supported() -> None:
    # Everything except economy is at least partially modeled today.
    for area in _ALL_AREA_CONSTANTS:
        entry = get_coverage(area)
        if area == AREA_ECONOMY:
            continue
        assert entry.supported is True
        assert entry.completeness in ("full", "partial")


def test_get_coverage_unknown_area_raises() -> None:
    with pytest.raises(KeyError):
        get_coverage("nonexistent_area")


def test_coverage_mapping_is_read_only() -> None:
    # MappingProxyType is not subscriptable for assignment.
    with pytest.raises(TypeError):
        COVERAGE["leaderboards"] = coverage.CoverageArea(  # type: ignore[index]
            area="x",
            supported=False,
            completeness="none",
            limitation="x",
            user_label="x",
            staff_label="x",
        )


def test_coverage_area_is_frozen() -> None:
    entry = get_coverage(AREA_BOSS)
    with pytest.raises((AttributeError, TypeError)):
        entry.supported = False  # type: ignore[misc]
