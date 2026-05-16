"""Tests for the startup registry validation pipeline.

Covers, via parametrized error-case clusters:
- The real registry validates cleanly (smoke test)
- Required-field absence raises RegistryValidationError
- Invalid tier/mode/color raise RegistryValidationError
- Duplicate entry_point / duplicate capability raise
  RegistryValidationError
- Unknown dependency / related_subsystem references raise
  RegistryValidationError
- Self-referential / circular dependencies raise
  CircularDependencyError
- Bad capability format / reserved prefix raise
  CapabilityNamespaceError

Each negative test injects a mutated registry, runs validation,
and asserts the expected exception class.  Restoration is handled
by monkeypatch.

P1 PR-7 consolidation: 12+ individual error tests were collapsed
into three parametrized clusters keyed by exception class.  The
mutators stay small (one-line registry tweaks), and reading any
single case in the parameter list explains the failure mode.
"""

from __future__ import annotations

from typing import Callable

import pytest

import utils.subsystem_registry as reg
from services.governance_exceptions import (
    CapabilityNamespaceError,
    CircularDependencyError,
    RegistryValidationError,
)


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
    """Patch SUBSYSTEMS and run validate_registry().

    Resets every compiled lookup table so validate_registry() rebuilds
    them from scratch under the new registry.
    """
    monkeypatch.setattr(reg, "SUBSYSTEMS", subsystems)
    monkeypatch.setattr(reg, "COMMAND_TO_SUBSYSTEM", {})
    monkeypatch.setattr(reg, "CAPABILITY_TO_SUBSYSTEM", {})
    monkeypatch.setattr(reg, "_COMPILED_DEPENDENTS", {})
    monkeypatch.setattr(reg, "_COMPILED_TIERS", {})
    monkeypatch.setattr(reg, "_COMPILED_CAPABILITIES", {})
    monkeypatch.setattr(reg, "_COMPILED_ENTRYPOINTS", {})
    monkeypatch.setattr(reg, "_COMPILED_DEPENDENCY_ORDER", [])
    reg.validate_registry()


Mutator = Callable[[dict], None]


def _set_field(name: str, value: object) -> Mutator:
    def mutate(r: dict) -> None:
        r["alpha"][name] = value
    return mutate


def _delete_field(name: str) -> Mutator:
    def mutate(r: dict) -> None:
        del r["alpha"][name]
    return mutate


# ---------------------------------------------------------------------------
# Smoke test: real registry is valid
# ---------------------------------------------------------------------------


def test_real_registry_passes_validation():
    """The real SUBSYSTEMS registry must pass all integrity checks."""
    assert len(reg.SUBSYSTEMS) > 0
    assert len(reg._COMPILED_TIERS) > 0
    assert len(reg._COMPILED_DEPENDENCY_ORDER) > 0


# ---------------------------------------------------------------------------
# Error cases — grouped by raised exception class
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "mutator",
    [
        # Missing required fields (one case per critical field)
        _delete_field("display_name"),
        _delete_field("description"),
        _delete_field("emoji"),
        _delete_field("visibility_tier"),
        _delete_field("visibility_mode"),
        # Invalid enum values
        _set_field("visibility_tier", "superadmin"),
        _set_field("visibility_mode", "turbo"),
        # Color must be int, not an arbitrary object
        _set_field("color", object()),
        # Duplicate entry_point across subsystems
        lambda r: r["beta"].__setitem__("entry_points", ["alpha"]),
        # Duplicate capability across subsystems
        lambda r: r["beta"].__setitem__("capabilities", ["alpha.resource.read"]),
        # Unknown dependency reference
        _set_field("dependencies", ["nonexistent_subsystem"]),
        # Unknown related_subsystem reference
        _set_field("related_subsystems", ["phantom"]),
    ],
    ids=[
        "missing_display_name",
        "missing_description",
        "missing_emoji",
        "missing_visibility_tier",
        "missing_visibility_mode",
        "invalid_tier",
        "invalid_mode",
        "color_not_int",
        "duplicate_entry_point",
        "duplicate_capability",
        "unknown_dependency",
        "unknown_related",
    ],
)
def test_registry_validation_error_cases(monkeypatch, mutator: Mutator):
    bad = _minimal_good_registry()
    mutator(bad)
    with pytest.raises(RegistryValidationError):
        _run_validation_with(monkeypatch, bad)


@pytest.mark.parametrize(
    "mutator",
    [
        # alpha→beta + beta→alpha → cycle
        lambda r: r["alpha"].__setitem__("dependencies", ["beta"]),
        # alpha→alpha → self cycle
        _set_field("dependencies", ["alpha"]),
    ],
    ids=["mutual_cycle", "self_reference"],
)
def test_circular_dependency_cases(monkeypatch, mutator: Mutator):
    bad = _minimal_good_registry()
    mutator(bad)
    with pytest.raises(CircularDependencyError):
        _run_validation_with(monkeypatch, bad)


@pytest.mark.parametrize(
    "mutator",
    [
        # Wrong part count — capabilities must be exactly subsystem.resource.action
        _set_field("capabilities", ["alpha.read"]),
        # Reserved namespace prefix
        _set_field("capabilities", ["_internal.resource.action"]),
    ],
    ids=["wrong_part_count", "reserved_prefix"],
)
def test_capability_namespace_error_cases(monkeypatch, mutator: Mutator):
    bad = _minimal_good_registry()
    mutator(bad)
    with pytest.raises(CapabilityNamespaceError):
        _run_validation_with(monkeypatch, bad)
