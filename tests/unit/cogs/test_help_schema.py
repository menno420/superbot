"""Help subsystem schema — the "Help appearance" domain panel (editor PR A).

Mirrors ``test_proof_channel_schema.py``: the declaration's shape, registry
capability, idempotent registration, and Settings-hub discovery (the §6
inclusion rule picks up a declared domain panel).
"""

from __future__ import annotations

from cogs.help.schemas import HELP_CONFIG_SCHEMA, register_schemas
from core.runtime import subsystem_schema as schema_mod


def test_schema_declares_the_help_appearance_domain_panel():
    assert HELP_CONFIG_SCHEMA.subsystem == "help"
    assert len(HELP_CONFIG_SCHEMA.domain_panels) == 1
    panel = HELP_CONFIG_SCHEMA.domain_panels[0]
    assert panel.name == "Help appearance"
    # The destination + the verify surface are named for the operator.
    assert "Help editor" in panel.description
    assert "Help Preview" in panel.description
    # Q-0055 — the description must say display-only.
    assert "display-only" in panel.description
    assert panel.capability_required == "help.settings.configure"


def test_register_schemas_is_idempotent():
    register_schemas()
    register_schemas()
    assert "help" in schema_mod.all_schemas()


def test_capability_is_declared_in_registry():
    """The identity contract warns on schema capabilities missing from the
    SUBSYSTEMS registry — pin that ours is declared."""
    from utils.subsystem_registry import SUBSYSTEMS

    cap = HELP_CONFIG_SCHEMA.domain_panels[0].capability_required
    assert cap in SUBSYSTEMS["help"]["capabilities"]


def test_help_becomes_actionable_settings_group():
    """With the domain panel declared, the Settings hub's §6 inclusion rule
    picks help up (it was excluded as schema-less before this slice)."""
    from services.customization_catalogue import actionable_settings_groups

    register_schemas()
    groups = {g.subsystem: g for g in actionable_settings_groups()}
    assert "help" in groups
    assert groups["help"].has_domain_panel
