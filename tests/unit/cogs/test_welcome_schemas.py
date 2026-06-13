"""Unit tests for the welcome subsystem schema (cogs.welcome.schemas)."""

from __future__ import annotations

import pytest

from core.runtime import subsystem_schema as schema_mod
from services import welcome_config


@pytest.fixture(autouse=True)
def _isolated_state():
    saved = schema_mod.all_schemas()
    schema_mod._reset_for_tests()
    yield
    schema_mod._reset_for_tests()
    for schema in saved.values():
        schema_mod.register(schema)


def test_register_adds_welcome_schema():
    from cogs.welcome.schemas import register_schemas

    register_schemas()
    assert "welcome" in schema_mod.registered_subsystems()
    schema = schema_mod.get_schema("welcome")
    assert schema is not None and schema.subsystem == "welcome"


def test_register_is_idempotent():
    from cogs.welcome.schemas import register_schemas

    register_schemas()
    schema_mod._reset_for_tests()
    register_schemas()
    assert schema_mod.get_schema("welcome") is not None


# Each spec's default must equal the canonical welcome_config default — they
# share the constant, so this pins that they never drift.
_EXPECTED_DEFAULTS = {
    "enabled": welcome_config.DEFAULT_ENABLED,
    "join_enabled": welcome_config.DEFAULT_JOIN_ENABLED,
    "leave_enabled": welcome_config.DEFAULT_LEAVE_ENABLED,
    "channel": welcome_config.DEFAULT_CHANNEL,
    "join_message": welcome_config.DEFAULT_JOIN_MESSAGE,
    "leave_message": welcome_config.DEFAULT_LEAVE_MESSAGE,
    "entry_role": welcome_config.DEFAULT_ENTRY_ROLE,
}


def test_spec_defaults_match_config_defaults():
    from cogs.welcome.schemas import WELCOME_SETTINGS

    by_name = {s.name: s for s in WELCOME_SETTINGS}
    assert set(by_name) == set(_EXPECTED_DEFAULTS)
    for name, expected in _EXPECTED_DEFAULTS.items():
        assert by_name[name].default == expected


def test_master_flag_defaults_off():
    """A fresh guild must be unaffected — the master switch defaults False."""
    from cogs.welcome.schemas import WELCOME_SETTINGS

    by_name = {s.name: s for s in WELCOME_SETTINGS}
    assert by_name["enabled"].default is False


def test_all_specs_require_the_welcome_capability():
    from cogs.welcome.schemas import WELCOME_SETTINGS

    for spec in WELCOME_SETTINGS:
        assert spec.capability_required == "welcome.settings.configure"


def test_channel_and_role_carry_picker_input_hints():
    from cogs.welcome.schemas import WELCOME_SETTINGS

    by_name = {s.name: s for s in WELCOME_SETTINGS}
    assert by_name["channel"].input_hint == "channel"
    assert by_name["entry_role"].input_hint == "role"


def test_id_validator_rejects_non_numeric():
    from cogs.welcome.schemas import WELCOME_SETTINGS

    validator = {s.name: s for s in WELCOME_SETTINGS}["channel"].validator
    validator("123")  # ok
    validator("")  # ok — empty means unset
    with pytest.raises(ValueError):
        validator("not-an-id")


def test_message_validator_rejects_empty_and_overlong():
    from cogs.welcome.schemas import WELCOME_SETTINGS

    validator = {s.name: s for s in WELCOME_SETTINGS}["join_message"].validator
    validator("Welcome {user}!")  # ok
    with pytest.raises(ValueError):
        validator("   ")  # empty after strip
    with pytest.raises(ValueError):
        validator("x" * (welcome_config.MAX_MESSAGE_LENGTH + 1))


def test_bool_validator_guards_non_bool():
    from cogs.welcome.schemas import WELCOME_SETTINGS

    validator = {s.name: s for s in WELCOME_SETTINGS}["enabled"].validator
    with pytest.raises(ValueError):
        validator("yes")
