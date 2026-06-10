"""Help "Help appearance" domain panel (audit Phase 5, PR A).

Pins the Settings-hub entry point: the schema declares the domain panel,
the capability is registered (identity contract), and the hub's §6
inclusion rule discovers Help as a domain-config group.
"""

from __future__ import annotations

import pytest

from cogs.help.schemas import HELP_CONFIG_SCHEMA, register_schemas
from core.runtime import settings_registry
from core.runtime import subsystem_schema as schema_mod


@pytest.fixture(autouse=True)
def _isolated_schema_state():
    saved = schema_mod.all_schemas()
    schema_mod._reset_for_tests()
    settings_registry._reset_for_tests()
    yield
    schema_mod._reset_for_tests()
    for schema in saved.values():
        schema_mod.register(schema)
    settings_registry._reset_for_tests()


def test_schema_declares_the_help_appearance_panel():
    panel = HELP_CONFIG_SCHEMA.domain_panels[0]
    assert panel.name == "Help appearance"
    assert panel.capability_required == "help.settings.configure"
    # Q-0055 — the copy must carry the display-only guarantee.
    assert "display-only" in panel.description


def test_capability_is_declared_in_registry():
    from utils.subsystem_registry import SUBSYSTEMS

    assert "help.settings.configure" in SUBSYSTEMS["help"]["capabilities"]


def test_settings_hub_discovers_help_as_domain_group():
    from services.customization_catalogue import actionable_settings_groups

    register_schemas()
    groups = {g.subsystem: g for g in actionable_settings_groups()}
    assert "help" in groups
    assert groups["help"].has_domain_panel is True


def test_register_schemas_is_idempotent():
    register_schemas()
    register_schemas()
    assert "help" in schema_mod.all_schemas()
