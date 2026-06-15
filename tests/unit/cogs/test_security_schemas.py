"""Unit tests for the security subsystem schema (cogs.security.schemas)."""

from __future__ import annotations

import pytest

from core.runtime import subsystem_schema as schema_mod
from services import security_config


@pytest.fixture(autouse=True)
def _isolated_state():
    saved = schema_mod.all_schemas()
    schema_mod._reset_for_tests()
    yield
    schema_mod._reset_for_tests()
    for schema in saved.values():
        schema_mod.register(schema)


def test_register_adds_security_schema():
    from cogs.security.schemas import register_schemas

    register_schemas()
    assert "security" in schema_mod.registered_subsystems()
    schema = schema_mod.get_schema("security")
    assert schema is not None and schema.subsystem == "security"


def test_register_is_idempotent():
    from cogs.security.schemas import register_schemas

    register_schemas()
    schema_mod._reset_for_tests()
    register_schemas()
    assert schema_mod.get_schema("security") is not None


# Each spec default must equal the canonical security_config default (shared
# constant) — pins that they never drift.
_EXPECTED_DEFAULTS = {
    "enabled": security_config.DEFAULT_ENABLED,
    "alert_channel": security_config.DEFAULT_ALERT_CHANNEL,
    "raid_enabled": security_config.DEFAULT_RAID_ENABLED,
    "raid_join_count": security_config.DEFAULT_RAID_JOIN_COUNT,
    "raid_window_seconds": security_config.DEFAULT_RAID_WINDOW_SECONDS,
    "raid_slowmode_channel": security_config.DEFAULT_RAID_SLOWMODE_CHANNEL,
    "raid_slowmode_seconds": security_config.DEFAULT_RAID_SLOWMODE_SECONDS,
    "raid_lockdown_seconds": security_config.DEFAULT_RAID_LOCKDOWN_SECONDS,
    "age_enabled": security_config.DEFAULT_AGE_ENABLED,
    "age_min_days": security_config.DEFAULT_AGE_MIN_DAYS,
    "age_action": security_config.DEFAULT_AGE_ACTION,
}


def test_spec_defaults_match_config_defaults():
    from cogs.security.schemas import SECURITY_SETTINGS

    by_name = {s.name: s for s in SECURITY_SETTINGS}
    assert set(by_name) == set(_EXPECTED_DEFAULTS)
    for name, expected in _EXPECTED_DEFAULTS.items():
        assert by_name[name].default == expected


def test_master_and_tier_flags_default_off():
    """A fresh guild must be unaffected — master + both tier flags default off."""
    from cogs.security.schemas import SECURITY_SETTINGS

    by_name = {s.name: s for s in SECURITY_SETTINGS}
    assert by_name["enabled"].default is False
    assert by_name["raid_enabled"].default is False
    assert by_name["age_enabled"].default is False


def test_all_specs_require_the_security_capability():
    from cogs.security.schemas import SECURITY_SETTINGS

    for spec in SECURITY_SETTINGS:
        assert spec.capability_required == "security.settings.configure"


def test_channel_specs_carry_picker_input_hints():
    from cogs.security.schemas import SECURITY_SETTINGS

    by_name = {s.name: s for s in SECURITY_SETTINGS}
    assert by_name["alert_channel"].input_hint == "channel"
    assert by_name["raid_slowmode_channel"].input_hint == "channel"


def test_action_enum_restricts_allowed_values():
    from cogs.security.schemas import SECURITY_SETTINGS

    spec = {s.name: s for s in SECURITY_SETTINGS}["age_action"]
    assert set(spec.allowed_values) == set(security_config.AGE_ACTIONS)
    spec.validator("alert")  # ok
    spec.validator("kick")  # ok
    with pytest.raises(ValueError):
        spec.validator("nuke")


def test_int_validator_enforces_bounds():
    from cogs.security.schemas import SECURITY_SETTINGS

    validator = {s.name: s for s in SECURITY_SETTINGS}["raid_join_count"].validator
    validator(10)  # ok
    with pytest.raises(ValueError):
        validator(1)  # below MIN_RAID_JOIN_COUNT
    with pytest.raises(ValueError):
        validator(99999)  # above MAX
    with pytest.raises(ValueError):
        validator(True)  # bool is not an int here


def test_bool_validator_guards_non_bool():
    from cogs.security.schemas import SECURITY_SETTINGS

    validator = {s.name: s for s in SECURITY_SETTINGS}["enabled"].validator
    with pytest.raises(ValueError):
        validator("yes")
