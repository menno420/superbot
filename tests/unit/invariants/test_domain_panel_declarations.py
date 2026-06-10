"""Domain-panel declaration coverage invariant (Settings Phase 2, DT06).

Settings audit §10.2 step 4 / consolidated plan Batch 4: a subsystem whose
real configuration lives in a dedicated canonical panel declares a
``DomainPanelSpec`` on its own ``SubsystemSchema`` (registered in cog_load).
The Settings hub's discovery (``actionable_settings_groups``) consumes those
declarations — the Phase 1 curated ``DOMAIN_CONFIG_SUBSYSTEMS`` frozenset is
retired.

This invariant makes the declaration set a **deliberate, test-visible
contract**:

* the set of declaring subsystems must equal ``_EXPECTED_DOMAIN_PANELS`` —
  a dropped declaration (a domain silently vanishing from Settings) and an
  undeclared addition both redden CI until this pin is consciously updated;
* every declaration must be well-formed and belong to a registered
  subsystem;
* the catalogue must actually consume the declarations (group included,
  ``has_domain_panel=True``);
* the retired frozenset must stay gone.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from core.runtime import subsystem_schema as schema_mod

_REPO_ROOT = Path(__file__).resolve().parents[3]
_COGS_DIR = _REPO_ROOT / "disbot" / "cogs"

# The deliberate contract: subsystems whose Settings group is a domain-config
# destination. Audit §4 verified cleanup as the one real domain-panel group
# (governance cleanup-policy tables + dedicated panel; empty scalar page).
# help joined 2026-06-10 (help audit Phase 5): the "Help appearance" panel —
# the HLP-3 overlay editor behind the audited help_overlay_mutation seam.
# Adding a subsystem here requires a real DomainPanelSpec declaration in its
# cogs/<subsystem>/schemas.py — and vice versa.
_EXPECTED_DOMAIN_PANELS: frozenset[str] = frozenset({"cleanup", "help"})


@pytest.fixture()
def _registered_declared_schemas():
    """Import every ``cogs/*/schemas.py`` and register its declarations
    into an isolated schema registry, mirroring what cog_load does at boot.
    """
    saved = schema_mod.all_schemas()
    schema_mod._reset_for_tests()
    for pkg_dir in sorted(_COGS_DIR.iterdir()):
        if not (pkg_dir / "schemas.py").is_file():
            continue
        module = importlib.import_module(f"cogs.{pkg_dir.name}.schemas")
        register = getattr(module, "register_schemas", None)
        if callable(register):
            register()
    try:
        yield schema_mod.all_schemas()
    finally:
        schema_mod._reset_for_tests()
        for schema in saved.values():
            schema_mod.register(schema)


def test_domain_panel_declaration_set_matches_the_contract(
    _registered_declared_schemas,
):
    declared = {
        name
        for name, schema in _registered_declared_schemas.items()
        if schema.domain_panels
    }
    missing = _EXPECTED_DOMAIN_PANELS - declared
    assert not missing, (
        "Domain-config subsystem(s) lost their DomainPanelSpec declaration — "
        "their Settings group would silently vanish. Restore the declaration "
        f"in cogs/<subsystem>/schemas.py or update the pin: {sorted(missing)}"
    )
    undeclared = declared - _EXPECTED_DOMAIN_PANELS
    assert not undeclared, (
        "New domain-panel declaration(s) — adding a domain-config Settings "
        "group is deliberate: update _EXPECTED_DOMAIN_PANELS in this test "
        f"(and the settings audit taxonomy) for: {sorted(undeclared)}"
    )


def test_domain_panel_declarations_are_well_formed(_registered_declared_schemas):
    from utils.subsystem_registry import SUBSYSTEMS

    for name, schema in _registered_declared_schemas.items():
        for spec in schema.domain_panels:
            assert name in SUBSYSTEMS, (
                f"{name!r} declares a domain panel but is not a registered " "subsystem"
            )
            assert (
                spec.name.strip()
            ), f"{name!r} domain panel needs an operator-facing name"
            assert (
                spec.description.strip()
            ), f"{name!r} domain panel needs a one-line description"


def test_catalogue_consumes_the_declarations(_registered_declared_schemas):
    """The Settings hub's discovery includes every declaring subsystem as a
    group with the panel surface — the seam really is the declaration, not
    a curated list."""
    from services.customization_catalogue import actionable_settings_groups

    groups = {g.subsystem: g for g in actionable_settings_groups()}
    for name in _EXPECTED_DOMAIN_PANELS:
        assert name in groups, f"{name!r} missing from actionable groups"
        assert groups[name].has_domain_panel is True
        assert "panel" in groups[name].surfaces


def test_the_phase1_curated_frozenset_is_retired():
    """Regression pin: the curated table must not quietly come back."""
    from services import customization_catalogue

    assert not hasattr(customization_catalogue, "DOMAIN_CONFIG_SUBSYSTEMS"), (
        "DOMAIN_CONFIG_SUBSYSTEMS returned — domain-config inclusion is "
        "declared per-schema (DomainPanelSpec) since Settings Phase 2"
    )
