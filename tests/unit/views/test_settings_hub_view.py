"""Unit tests for the Settings Manager hub view — S5.

The hub is the read-only navigation root: header counters + a
subsystem dropdown + four diagnostic-panel buttons.
"""

from __future__ import annotations

import discord
import pytest

from core.runtime import settings_registry
from core.runtime import subsystem_schema as schema_mod
from core.runtime.subsystem_schema import SettingSpec, SubsystemSchema
from views.settings.hub import SettingsHubView, _candidate_subsystems


@pytest.fixture(autouse=True)
def _isolated_state():
    saved_schemas = schema_mod.all_schemas()
    schema_mod._reset_for_tests()
    settings_registry._reset_for_tests()
    yield
    schema_mod._reset_for_tests()
    for schema in saved_schemas.values():
        schema_mod.register(schema)
    settings_registry._reset_for_tests()


def _author():
    class _M:
        id = 1

    return _M()


def test_hub_embed_has_title_and_inventory_field():
    embed = SettingsHubView.build_embed()
    assert "Settings Manager" in (embed.title or "")
    field_names = [f.name for f in embed.fields]
    assert "Inventory" in field_names
    assert "Customization findings" in field_names


def test_hub_view_contains_subsystem_dropdown_and_four_buttons():
    view = SettingsHubView(_author())
    # 1 Select + 4 Buttons = 5 items.
    assert len(view.children) == 5
    selects = [c for c in view.children if isinstance(c, discord.ui.Select)]
    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    assert len(selects) == 1
    assert len(buttons) == 4


def test_hub_dropdown_lists_registered_subsystems():
    # Register one schema so we know the dropdown sees it; do NOT clear
    # SUBSYSTEMS — _candidate_subsystems shows every subsystem in
    # SUBSYSTEMS, not only ones with schemas.
    schema_mod.register(
        SubsystemSchema(
            subsystem="xp",
            settings=(SettingSpec(name="xp_min", value_type=int, default=1),),
        ),
    )
    candidates = _candidate_subsystems()
    candidate_names = {c[0] for c in candidates}
    assert "xp" in candidate_names
    assert "moderation" in candidate_names  # in SUBSYSTEMS, no schema needed


def test_hub_dropdown_options_capped_to_discord_limit():
    view = SettingsHubView(_author())
    select = next(c for c in view.children if isinstance(c, discord.ui.Select))
    assert len(select.options) <= 25  # Discord's hard cap


def test_button_labels_match_directive():
    """The four sub-panel buttons must match the directive's vocabulary."""
    view = SettingsHubView(_author())
    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    labels = {b.label for b in buttons}
    assert labels == {
        "Needs setup",
        "Invalid settings",
        "Missing bindings",
        "Recent changes",
    }


def test_hub_inventory_reflects_registered_settings():
    schema_mod.register(
        SubsystemSchema(
            subsystem="xp",
            settings=(
                SettingSpec(name="xp_min", value_type=int, default=1),
                SettingSpec(name="xp_max", value_type=int, default=10),
            ),
        ),
    )
    settings_registry.build_registry()
    embed = SettingsHubView.build_embed()
    inventory = next(f.value for f in embed.fields if f.name == "Inventory")
    assert "`settings`: 2" in inventory


def test_hub_inventory_reflects_registered_bindings():
    from core.runtime.subsystem_schema import BindingKind, BindingSpec

    schema_mod.register(
        SubsystemSchema(
            subsystem="moderation",
            bindings=(
                BindingSpec(
                    name="mod_log",
                    kind=BindingKind.CHANNEL,
                    required=True,
                    hint="mod log target",
                    capability_required="moderation.log.view",
                ),
            ),
        ),
    )
    embed = SettingsHubView.build_embed()
    inventory = next(f.value for f in embed.fields if f.name == "Inventory")
    assert "`bindings`: 1" in inventory


def test_hub_handles_no_settings_registry_built():
    """When SettingsRegistry has not been built, settings count is 0."""
    embed = SettingsHubView.build_embed()
    inventory = next(f.value for f in embed.fields if f.name == "Inventory")
    assert "`settings`: 0" in inventory
