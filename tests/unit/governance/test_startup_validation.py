"""Tests for the startup registry validation pipeline.

Covers:
- validate_registry() succeeds on the real registry (smoke test)
- CircularDependencyError raised on a cycle
- RegistryValidationError raised for missing required fields
- RegistryValidationError raised for invalid visibility_tier
- CapabilityNamespaceError raised for bad capability format
- CapabilityNamespaceError raised for reserved namespace prefix
- RegistryValidationError raised for duplicate entry_point
- RegistryValidationError raised for unknown dependency reference

Each test that injects a bad registry uses monkeypatch to temporarily replace
the module-level SUBSYSTEMS and _COMPILED_DEPENDENCY_ORDER, then restores them.
validate_registry() raises before modifying compiled tables for all error cases.
"""

from __future__ import annotations

import copy
import importlib

import pytest

import utils.subsystem_registry as reg


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _minimal_good_registry() -> dict:
    """A minimal valid registry with two subsystems and no dependency cycle."""
    return {
        "alpha": {
            "display_name": "Alpha",
            "description": "Alpha subsystem",
            "emoji": "🅰️",
            "color": 0x123456,
            "visibility_tier": "user",
            "visibility_mode": "normal",
            "category": "test",
            "tags": [],
            "entry_points": ["alpha"],
            "default_channels": [],
            "related_subsystems": [],
            "dependencies": [],
            "soft_dependencies": [],
            "supports_dm": False,
            "has_cleanup_rules": False,
            "has_onboarding": False,
            "ui_priority": 50,
            "capabilities": ["alpha.resource.read"],
        },
        "beta": {
            "display_name": "Beta",
            "description": "Beta subsystem",
            "emoji": "🅱️",
            "color": 0xABCDEF,
            "visibility_tier": "user",
            "visibility_mode": "normal",
            "category": "test",
            "tags": [],
            "entry_points": ["beta"],
            "default_channels": [],
            "related_subsystems": [],
            "dependencies": ["alpha"],
            "soft_dependencies": [],
            "supports_dm": False,
            "has_cleanup_rules": False,
            "has_onboarding": False,
            "ui_priority": 51,
            "capabilities": ["beta.resource.read"],
        },
    }


def _run_validation_with(monkeypatch, subsystems: dict) -> None:
    """Patch SUBSYSTEMS and run validate_registry(). Restores originals via monkeypatch."""
    monkeypatch.setattr(reg, "SUBSYSTEMS", subsystems)
    # Also reset computed tables so validate_registry() re-populates them.
    monkeypatch.setattr(reg, "COMMAND_TO_SUBSYSTEM", {})
    monkeypatch.setattr(reg, "CAPABILITY_TO_SUBSYSTEM", {})
    monkeypatch.setattr(reg, "_COMPILED_DEPENDENTS", {})
    monkeypatch.setattr(reg, "_COMPILED_TIERS", {})
    monkeypatch.setattr(reg, "_COMPILED_CAPABILITIES", {})
    monkeypatch.setattr(reg, "_COMPILED_ENTRYPOINTS", {})
    monkeypatch.setattr(reg, "_COMPILED_DEPENDENCY_ORDER", [])
    reg.validate_registry()


# ---------------------------------------------------------------------------
# Smoke test: real registry is valid
# ---------------------------------------------------------------------------


def test_real_registry_passes_validation():
    """The real SUBSYSTEMS registry must pass all integrity checks with no exceptions."""
    # validated_registry session fixture already ran this; we just assert the
    # compiled tables are non-empty as a result.
    assert len(reg.SUBSYSTEMS) > 0
    assert len(reg._COMPILED_TIERS) > 0
    assert len(reg._COMPILED_DEPENDENCY_ORDER) > 0


# ---------------------------------------------------------------------------
# Circular dependency detection
# ---------------------------------------------------------------------------


def test_circular_dependency_raises(monkeypatch):
    from services.governance_exceptions import CircularDependencyError

    bad = _minimal_good_registry()
    bad["alpha"]["dependencies"] = ["beta"]  # alpha→beta + beta→alpha = cycle
    with pytest.raises(CircularDependencyError):
        _run_validation_with(monkeypatch, bad)


def test_self_referential_dependency_raises(monkeypatch):
    from services.governance_exceptions import CircularDependencyError

    bad = _minimal_good_registry()
    bad["alpha"]["dependencies"] = ["alpha"]
    with pytest.raises(CircularDependencyError):
        _run_validation_with(monkeypatch, bad)


# ---------------------------------------------------------------------------
# Missing required field
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field",
    ["display_name", "description", "emoji", "visibility_tier", "visibility_mode"],
)
def test_missing_required_field_raises(monkeypatch, field):
    from services.governance_exceptions import RegistryValidationError

    bad = _minimal_good_registry()
    del bad["alpha"][field]
    with pytest.raises(RegistryValidationError):
        _run_validation_with(monkeypatch, bad)


# ---------------------------------------------------------------------------
# Invalid tier / mode
# ---------------------------------------------------------------------------


def test_invalid_visibility_tier_raises(monkeypatch):
    from services.governance_exceptions import RegistryValidationError

    bad = _minimal_good_registry()
    bad["alpha"]["visibility_tier"] = "superadmin"  # not a valid tier
    with pytest.raises(RegistryValidationError):
        _run_validation_with(monkeypatch, bad)


def test_invalid_visibility_mode_raises(monkeypatch):
    from services.governance_exceptions import RegistryValidationError

    bad = _minimal_good_registry()
    bad["alpha"]["visibility_mode"] = "turbo"  # not a valid mode
    with pytest.raises(RegistryValidationError):
        _run_validation_with(monkeypatch, bad)


# ---------------------------------------------------------------------------
# Capability namespace violations
# ---------------------------------------------------------------------------


def test_capability_wrong_part_count_raises(monkeypatch):
    from services.governance_exceptions import CapabilityNamespaceError

    bad = _minimal_good_registry()
    bad["alpha"]["capabilities"] = ["alpha.read"]  # only 2 parts, needs 3
    with pytest.raises(CapabilityNamespaceError):
        _run_validation_with(monkeypatch, bad)


def test_capability_reserved_prefix_raises(monkeypatch):
    from services.governance_exceptions import CapabilityNamespaceError

    bad = _minimal_good_registry()
    bad["alpha"]["capabilities"] = ["_internal.resource.action"]
    with pytest.raises(CapabilityNamespaceError):
        _run_validation_with(monkeypatch, bad)


def test_duplicate_capability_across_subsystems_raises(monkeypatch):
    from services.governance_exceptions import RegistryValidationError

    bad = _minimal_good_registry()
    bad["beta"]["capabilities"] = ["alpha.resource.read"]  # same as alpha's cap
    with pytest.raises(RegistryValidationError):
        _run_validation_with(monkeypatch, bad)


# ---------------------------------------------------------------------------
# Entry point and dependency reference validation
# ---------------------------------------------------------------------------


def test_duplicate_entry_point_raises(monkeypatch):
    from services.governance_exceptions import RegistryValidationError

    bad = _minimal_good_registry()
    bad["beta"]["entry_points"] = ["alpha"]  # "alpha" already registered by alpha
    with pytest.raises(RegistryValidationError):
        _run_validation_with(monkeypatch, bad)


def test_unknown_dependency_raises(monkeypatch):
    from services.governance_exceptions import RegistryValidationError

    bad = _minimal_good_registry()
    bad["alpha"]["dependencies"] = ["nonexistent_subsystem"]
    with pytest.raises(RegistryValidationError):
        _run_validation_with(monkeypatch, bad)


def test_unknown_related_subsystem_raises(monkeypatch):
    from services.governance_exceptions import RegistryValidationError

    bad = _minimal_good_registry()
    bad["alpha"]["related_subsystems"] = ["phantom"]
    with pytest.raises(RegistryValidationError):
        _run_validation_with(monkeypatch, bad)


# ---------------------------------------------------------------------------
# Color type validation
# ---------------------------------------------------------------------------


def test_color_must_be_int_not_discord_color(monkeypatch):
    from services.governance_exceptions import RegistryValidationError

    class FakeColor:
        pass

    bad = _minimal_good_registry()
    bad["alpha"]["color"] = FakeColor()
    with pytest.raises(RegistryValidationError):
        _run_validation_with(monkeypatch, bad)
