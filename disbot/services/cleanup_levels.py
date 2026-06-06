"""Setup-wizard cleanup level vocabulary.

Maps the operator-facing level names that the wizard's Cleanup section
exposes (``Off`` / ``Light`` / ``Standard`` / ``Strict``) to the
``cleanup_policies`` column values that :mod:`governance.writes`
persists.

Single source of truth: both
:mod:`views.setup.sections.cleanup` (the operator picker) and
:mod:`services.setup_operations` (the Final Review dispatcher) read
this table.  Adding a new level here automatically appears in both
places.

Custom-tuned policies remain a separate path — operators who need
non-standard ``delete_after_seconds`` should configure via
``!platform`` or a future ``!settings cleanup`` flow rather than
extending this table.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "LEVELS",
    "POLICY_VERSION",
    "columns_for_level",
    "known_level_names",
    "level_for_columns",
]

# Current cleanup-policy schema version. Stamped on every ``cleanup_policies``
# row via the column DEFAULT (migration 058) and surfaced by the read model /
# diagnostics so a stored policy is self-describing. Bump only when the policy
# shape changes (e.g. a future dimensioned policy), alongside its migration.
POLICY_VERSION = 1


LEVELS: dict[str, dict[str, Any]] = {
    "Off": {
        "delete_invalid_commands": False,
        "delete_failed_commands": False,
        "delete_after_seconds": 0,
    },
    "Light": {
        "delete_invalid_commands": True,
        "delete_failed_commands": False,
        "delete_after_seconds": 10,
    },
    "Standard": {
        "delete_invalid_commands": True,
        "delete_failed_commands": True,
        "delete_after_seconds": 5,
    },
    "Strict": {
        "delete_invalid_commands": True,
        "delete_failed_commands": True,
        "delete_after_seconds": 2,
    },
}


def columns_for_level(name: str) -> dict[str, Any]:
    """Return the cleanup_policies column values for ``name``.

    Raises ``KeyError`` if the level is unknown — the caller is
    responsible for surfacing the error in a way the operator sees.
    """
    return LEVELS[name]


def known_level_names() -> frozenset[str]:
    """Return the set of operator-facing level names."""
    return frozenset(LEVELS)


def level_for_columns(
    *,
    delete_invalid_commands: bool,
    delete_failed_commands: bool,
    delete_after_seconds: int,
) -> str | None:
    """Return the preset level name matching these column values, else ``None``.

    The inverse of :func:`columns_for_level`: given a stored ``cleanup_policies``
    row's three columns, name it back to its operator-facing level
    (``Off`` / ``Light`` / ``Standard`` / ``Strict``).  Returns ``None`` when the
    values match no preset (an operator-tuned policy), so the caller decides how
    to render it (e.g. as ``"Custom"``).  The four presets have distinct column
    tuples, so the match is unambiguous.
    """
    for name, cols in LEVELS.items():
        if (
            cols["delete_invalid_commands"] == delete_invalid_commands
            and cols["delete_failed_commands"] == delete_failed_commands
            and cols["delete_after_seconds"] == delete_after_seconds
        ):
            return name
    return None
