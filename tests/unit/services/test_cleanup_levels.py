"""Cleanup-level vocabulary: presets, the columns↔level round-trip, version.

``services.cleanup_levels`` is the single source of truth mapping operator-facing
cleanup levels (Off/Light/Standard/Strict) to ``cleanup_policies`` column values.
PR8 adds the inverse (:func:`level_for_columns`) so the read model / diagnostics
can name a stored policy row back to its level, plus the ``POLICY_VERSION`` marker.
"""

from __future__ import annotations

import pytest

from services.cleanup_levels import (
    LEVELS,
    POLICY_VERSION,
    columns_for_level,
    known_level_names,
    level_for_columns,
)


def test_known_level_names_matches_levels():
    assert known_level_names() == frozenset(LEVELS)


def test_policy_version_is_one():
    """v1 is the only shipped policy shape (no dimensioned policies yet)."""
    assert POLICY_VERSION == 1


def test_preset_column_tuples_are_distinct():
    """level_for_columns relies on each preset having a unique column tuple."""
    tuples = {
        (
            c["delete_invalid_commands"],
            c["delete_failed_commands"],
            c["delete_after_seconds"],
        )
        for c in LEVELS.values()
    }
    assert len(tuples) == len(LEVELS)


@pytest.mark.parametrize("name", list(LEVELS))
def test_round_trip_each_level(name: str):
    """columns_for_level → level_for_columns returns the original level name."""
    assert level_for_columns(**columns_for_level(name)) == name


def test_level_for_columns_returns_none_for_custom():
    """A column combination matching no preset is reported as None (custom)."""
    assert (
        level_for_columns(
            delete_invalid_commands=True,
            delete_failed_commands=False,
            delete_after_seconds=3,  # not any preset's delete_after
        )
        is None
    )
