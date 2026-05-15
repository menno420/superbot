"""ISSUE-042: Validate registry entry_points against the real subsystem manifest.

These tests verify that every entry_point declared in SUBSYSTEMS follows the
naming conventions and structural rules that the bot enforces at runtime.
They do NOT require the bot to be running — they check the static data.

A separate runtime check (ISSUE-042 full implementation) would compare
entry_points against bot.commands after cog load; that belongs in an
integration test that requires a running bot.
"""

from __future__ import annotations

import re

import pytest
from utils.subsystem_registry import SUBSYSTEMS

# ---------------------------------------------------------------------------
# Entry point naming rules
# ---------------------------------------------------------------------------

# Discord command names: lowercase letters, digits, underscores; 1-32 chars.
_VALID_COMMAND_PATTERN = re.compile(r"^[a-z0-9_]{1,32}$")


def _all_entry_points():
    """Yield (subsystem_name, entry_point) tuples from the real registry."""
    for name, meta in SUBSYSTEMS.items():
        for ep in meta.get("entry_points", ()):
            yield name, ep


@pytest.mark.parametrize("subsystem,ep", list(_all_entry_points()))
def test_entry_point_matches_discord_naming_rules(subsystem, ep):
    """Every entry_point must be a valid Discord command name."""
    assert _VALID_COMMAND_PATTERN.match(ep), (
        f"Entry point {ep!r} for subsystem {subsystem!r} "
        "violates Discord command naming rules (lowercase, digits, underscores, 1-32 chars)"
    )


# ---------------------------------------------------------------------------
# Entry point uniqueness
# ---------------------------------------------------------------------------


def test_no_duplicate_entry_points_across_subsystems():
    """validate_registry already checks this; we assert the compiled state reflects it."""
    seen: dict[str, str] = {}  # ep → subsystem
    for name, meta in SUBSYSTEMS.items():
        for ep in meta.get("entry_points", ()):
            assert (
                ep not in seen
            ), f"Entry point {ep!r} claimed by both {seen[ep]!r} and {name!r}"
            seen[ep] = name


# ---------------------------------------------------------------------------
# Every subsystem has at least one entry point (or is internal)
# ---------------------------------------------------------------------------


def test_non_internal_subsystems_have_entry_points():
    """Subsystems with visibility_mode != 'internal' must declare at least one entry_point.

    Internal subsystems may have no entry_points since they are not user-facing.
    A subsystem with no entry_point is invisible to governance command routing.
    """
    for name, meta in SUBSYSTEMS.items():
        mode = meta.get("visibility_mode", "normal")
        if mode == "internal":
            continue
        entry_points = meta.get("entry_points", [])
        assert entry_points, (
            f"Subsystem {name!r} (mode={mode!r}) has no entry_points — "
            "governance command routing cannot map commands to this subsystem"
        )


# ---------------------------------------------------------------------------
# Compiled COMMAND_TO_SUBSYSTEM mapping is populated
# ---------------------------------------------------------------------------


def test_command_to_subsystem_covers_all_entry_points():
    """Every entry_point in the registry must appear in COMMAND_TO_SUBSYSTEM."""
    from utils.subsystem_registry import COMMAND_TO_SUBSYSTEM

    for name, meta in SUBSYSTEMS.items():
        for ep in meta.get("entry_points", ()):
            assert ep in COMMAND_TO_SUBSYSTEM, (
                f"Entry point {ep!r} from subsystem {name!r} is missing "
                "from COMMAND_TO_SUBSYSTEM"
            )
            assert COMMAND_TO_SUBSYSTEM[ep] == name, (
                f"COMMAND_TO_SUBSYSTEM[{ep!r}] = {COMMAND_TO_SUBSYSTEM[ep]!r}, "
                f"expected {name!r}"
            )


# ---------------------------------------------------------------------------
# Compiled capability map is populated
# ---------------------------------------------------------------------------


def test_capability_to_subsystem_covers_all_capabilities():
    """Every capability in the registry must appear in CAPABILITY_TO_SUBSYSTEM."""
    from utils.subsystem_registry import CAPABILITY_TO_SUBSYSTEM

    for name, meta in SUBSYSTEMS.items():
        for cap in meta.get("capabilities", ()):
            assert cap in CAPABILITY_TO_SUBSYSTEM, (
                f"Capability {cap!r} from subsystem {name!r} is missing "
                "from CAPABILITY_TO_SUBSYSTEM"
            )
            assert CAPABILITY_TO_SUBSYSTEM[cap] == name, (
                f"CAPABILITY_TO_SUBSYSTEM[{cap!r}] = {CAPABILITY_TO_SUBSYSTEM[cap]!r}, "
                f"expected {name!r}"
            )
