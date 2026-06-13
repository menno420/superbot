"""Unit tests for the counters subsystem schema (cogs.counters.schemas)."""

from __future__ import annotations

import pytest

from core.runtime import subsystem_schema as schema_mod
from services import counter_config


@pytest.fixture(autouse=True)
def _isolated_state():
    saved = schema_mod.all_schemas()
    schema_mod._reset_for_tests()
    yield
    schema_mod._reset_for_tests()
    for schema in saved.values():
        schema_mod.register(schema)


def test_register_adds_counters_schema():
    from cogs.counters.schemas import register_schemas

    register_schemas()
    assert "counters" in schema_mod.registered_subsystems()
    schema = schema_mod.get_schema("counters")
    assert schema is not None and schema.subsystem == "counters"


def test_register_is_idempotent():
    from cogs.counters.schemas import register_schemas

    register_schemas()
    schema_mod._reset_for_tests()
    register_schemas()
    assert schema_mod.get_schema("counters") is not None


_EXPECTED_DEFAULTS = {
    "enabled": counter_config.DEFAULT_ENABLED,
    "total_channel": counter_config.DEFAULT_CHANNEL,
    "humans_channel": counter_config.DEFAULT_CHANNEL,
    "bots_channel": counter_config.DEFAULT_CHANNEL,
    "total_template": counter_config.DEFAULT_TOTAL_TEMPLATE,
    "humans_template": counter_config.DEFAULT_HUMANS_TEMPLATE,
    "bots_template": counter_config.DEFAULT_BOTS_TEMPLATE,
}


def test_spec_defaults_match_config_defaults():
    from cogs.counters.schemas import COUNTERS_SETTINGS

    by_name = {s.name: s for s in COUNTERS_SETTINGS}
    assert set(by_name) == set(_EXPECTED_DEFAULTS)
    for name, expected in _EXPECTED_DEFAULTS.items():
        assert by_name[name].default == expected


def test_master_flag_defaults_off():
    from cogs.counters.schemas import COUNTERS_SETTINGS

    by_name = {s.name: s for s in COUNTERS_SETTINGS}
    assert by_name["enabled"].default is False


def test_all_specs_require_the_counters_capability():
    from cogs.counters.schemas import COUNTERS_SETTINGS

    for spec in COUNTERS_SETTINGS:
        assert spec.capability_required == "counters.settings.configure"


def test_channel_specs_carry_picker_input_hint():
    from cogs.counters.schemas import COUNTERS_SETTINGS

    by_name = {s.name: s for s in COUNTERS_SETTINGS}
    for name in ("total_channel", "humans_channel", "bots_channel"):
        assert by_name[name].input_hint == "channel"


def test_id_validator_rejects_non_numeric():
    from cogs.counters.schemas import COUNTERS_SETTINGS

    validator = {s.name: s for s in COUNTERS_SETTINGS}["total_channel"].validator
    validator("123")  # ok
    validator("")  # ok — unbound
    with pytest.raises(ValueError):
        validator("nope")


def test_template_validator_rejects_empty_and_overlong():
    from cogs.counters.schemas import COUNTERS_SETTINGS

    validator = {s.name: s for s in COUNTERS_SETTINGS}["total_template"].validator
    validator("Members: {count}")  # ok
    with pytest.raises(ValueError):
        validator("   ")
    with pytest.raises(ValueError):
        validator("x" * (counter_config.MAX_TEMPLATE_LENGTH + 1))
