"""Phase 1 tests for ``utils.subsystem_registry``.

Covers the schema-v2 additions:

* ``REGISTRY_SCHEMA_VERSION`` has been bumped to 2.
* The real registry continues to validate cleanly with the new
  validator in place (smoke test).
* ``parent_hub`` and ``hub_group`` are accepted when valid.
* ``parent_hub`` and ``hub_group`` are rejected when malformed,
  unknown, self-referential, two-hop, or pointing at a non-routable
  parent.
* Deep-freeze still applies after validation when the new fields are
  present.

The negative cases follow the same monkeypatch pattern used by
``tests/unit/governance/test_startup_validation.py``: build a minimal
synthetic registry, mutate it, run the validator, assert the expected
``RegistryValidationError``.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Callable

import pytest

import utils.subsystem_registry as reg
from services.governance_exceptions import RegistryValidationError


# ---------------------------------------------------------------------------
# Synthetic-registry helpers (mirror the governance startup-validation file)
# ---------------------------------------------------------------------------


def _minimal_registry_with_hub() -> dict:
    """Two subsystems: ``hub`` (routable) and ``child`` (no parent yet)."""
    return {
        "hub": {
            "display_name": "Hub",
            "description": "A routable hub",
            "emoji": "🎮",
            "color": 0x123456,
            "visibility_tier": "user",
            "visibility_mode": "normal",
            "category": "test",
            "tags": [],
            "entry_points": ["hub"],
            "default_channels": [],
            "related_subsystems": [],
            "dependencies": [],
            "soft_dependencies": [],
            "supports_dm": False,
            "has_cleanup_rules": False,
            "ui_priority": 50,
            "capabilities": ["hub.view.show"],
        },
        "child": {
            "display_name": "Child",
            "description": "A potential hub member",
            "emoji": "🅰️",
            "color": 0xABCDEF,
            "visibility_tier": "user",
            "visibility_mode": "normal",
            "category": "test",
            "tags": [],
            "entry_points": ["child"],
            "default_channels": [],
            "related_subsystems": [],
            "dependencies": [],
            "soft_dependencies": [],
            "supports_dm": False,
            "has_cleanup_rules": False,
            "ui_priority": 51,
            "capabilities": ["child.resource.read"],
        },
    }


def _run_validation_with(monkeypatch, subsystems: dict) -> None:
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


# ---------------------------------------------------------------------------
# Schema version + real-registry smoke tests
# ---------------------------------------------------------------------------


def test_registry_schema_version_is_v2():
    """Phase 1 bumps the schema version to 2."""
    assert reg.REGISTRY_SCHEMA_VERSION == 2


def test_real_registry_validates_under_schema_v2():
    """The conftest already validated the real registry — this asserts the
    deep-frozen result still contains every existing entry and that the
    new optional fields read as ``None`` for all of them (Phase 1 sets
    none of them).
    """
    assert len(reg.SUBSYSTEMS) >= 22
    for name, meta in reg.SUBSYSTEMS.items():
        assert meta.get("parent_hub") is None, (
            f"subsystem {name!r} unexpectedly has parent_hub set in Phase 1"
        )
        assert meta.get("hub_group") is None, (
            f"subsystem {name!r} unexpectedly has hub_group set in Phase 1"
        )


# ---------------------------------------------------------------------------
# Positive cases
# ---------------------------------------------------------------------------


def test_valid_parent_hub_passes(monkeypatch):
    good = _minimal_registry_with_hub()
    good["child"]["parent_hub"] = "hub"
    _run_validation_with(monkeypatch, good)
    # Validator deep-froze the registry; assert the field round-trips.
    assert reg.SUBSYSTEMS["child"]["parent_hub"] == "hub"


def test_valid_hub_group_passes(monkeypatch):
    good = _minimal_registry_with_hub()
    good["child"]["parent_hub"] = "hub"
    good["child"]["hub_group"] = "competitive"
    _run_validation_with(monkeypatch, good)
    assert reg.SUBSYSTEMS["child"]["hub_group"] == "competitive"


def test_hub_group_allowed_without_parent_hub(monkeypatch):
    """``hub_group`` does not require ``parent_hub`` to be set; the
    rendering layer owns semantic validation of the label.
    """
    good = _minimal_registry_with_hub()
    good["child"]["hub_group"] = "ungrouped"
    _run_validation_with(monkeypatch, good)
    assert reg.SUBSYSTEMS["child"]["hub_group"] == "ungrouped"


def test_deep_freeze_holds_after_validation_with_new_fields(monkeypatch):
    """The new optional fields must not break the deep-freeze invariant."""
    good = _minimal_registry_with_hub()
    good["child"]["parent_hub"] = "hub"
    good["child"]["hub_group"] = "competitive"
    _run_validation_with(monkeypatch, good)
    # SUBSYSTEMS itself is a MappingProxyType after validate_registry.
    assert isinstance(reg.SUBSYSTEMS, MappingProxyType)
    # And every entry is too.
    for meta in reg.SUBSYSTEMS.values():
        assert isinstance(meta, MappingProxyType)
    # Mutation attempt raises.
    with pytest.raises(TypeError):
        reg.SUBSYSTEMS["child"]["parent_hub"] = "other"  # type: ignore[index]


# ---------------------------------------------------------------------------
# Negative cases — parent_hub
# ---------------------------------------------------------------------------


def _set_parent_hub(value: object) -> Mutator:
    def mutate(r: dict) -> None:
        r["child"]["parent_hub"] = value
    return mutate


def _set_hub_group(value: object) -> Mutator:
    def mutate(r: dict) -> None:
        r["child"]["hub_group"] = value
    return mutate


@pytest.mark.parametrize(
    "mutator, expected_fragment",
    [
        (_set_parent_hub(""), "non-empty string"),
        (_set_parent_hub(123), "non-empty string"),
        (_set_parent_hub("child"), "reference self"),
        (_set_parent_hub("missing_subsystem"), "not a registered subsystem"),
    ],
    ids=[
        "parent_hub_empty_string",
        "parent_hub_wrong_type",
        "parent_hub_self_reference",
        "parent_hub_unknown_subsystem",
    ],
)
def test_parent_hub_invalid_cases(monkeypatch, mutator: Mutator, expected_fragment: str):
    bad = _minimal_registry_with_hub()
    mutator(bad)
    with pytest.raises(RegistryValidationError) as excinfo:
        _run_validation_with(monkeypatch, bad)
    assert expected_fragment in str(excinfo.value)


def test_parent_hub_two_hop_rejected(monkeypatch):
    """A parent_hub pointing at a subsystem that itself has parent_hub set
    must be rejected: hubs are flat.
    """
    bad = _minimal_registry_with_hub()
    # Add a third subsystem so we can construct a 3-link chain.
    bad["grandchild"] = {
        **bad["child"],
        "entry_points": ["grandchild"],
        "capabilities": ["grandchild.resource.read"],
    }
    bad["child"]["parent_hub"] = "hub"
    bad["grandchild"]["parent_hub"] = "child"  # child itself has a parent_hub
    with pytest.raises(RegistryValidationError) as excinfo:
        _run_validation_with(monkeypatch, bad)
    assert "two-hop" in str(excinfo.value)


def test_parent_hub_non_routable_parent_rejected(monkeypatch):
    """The referenced parent_hub must have entry_points (be reachable)."""
    bad = _minimal_registry_with_hub()
    bad["hub"]["entry_points"] = []  # hub is no longer routable
    bad["child"]["parent_hub"] = "hub"
    with pytest.raises(RegistryValidationError) as excinfo:
        _run_validation_with(monkeypatch, bad)
    assert "not routable" in str(excinfo.value)


# ---------------------------------------------------------------------------
# Negative cases — hub_group
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "mutator, expected_fragment",
    [
        (_set_hub_group(""), "non-empty string"),
        (_set_hub_group(123), "non-empty string"),
        (_set_hub_group("x" * 33), "≤ 32"),
    ],
    ids=[
        "hub_group_empty_string",
        "hub_group_wrong_type",
        "hub_group_too_long",
    ],
)
def test_hub_group_invalid_cases(monkeypatch, mutator: Mutator, expected_fragment: str):
    bad = _minimal_registry_with_hub()
    mutator(bad)
    with pytest.raises(RegistryValidationError) as excinfo:
        _run_validation_with(monkeypatch, bad)
    assert expected_fragment in str(excinfo.value)


def test_hub_group_max_length_exactly_32_accepted(monkeypatch):
    """The ≤ 32 bound is inclusive."""
    good = _minimal_registry_with_hub()
    good["child"]["hub_group"] = "x" * 32
    _run_validation_with(monkeypatch, good)
    assert reg.SUBSYSTEMS["child"]["hub_group"] == "x" * 32
