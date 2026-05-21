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

__all__ = ["LEVELS", "columns_for_level", "known_level_names"]


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
