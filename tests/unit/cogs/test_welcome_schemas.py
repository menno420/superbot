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
    "card_enabled": welcome_config.DEFAULT_CARD_ENABLED,
    "dm_enabled": welcome_config.DEFAULT_DM_ENABLED,
    "dm_message": welcome_config.DEFAULT_DM_MESSAGE,
    "min_account_age_days": welcome_config.DEFAULT_MIN_ACCOUNT_AGE_DAYS,
    "delete_after_seconds": welcome_config.DEFAULT_DELETE_AFTER_SECONDS,
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


def test_message_validator_accepts_multiple_variants():
    from cogs.welcome.schemas import WELCOME_SETTINGS

    validator = {s.name: s for s in WELCOME_SETTINGS}["join_message"].validator
    # Several "---"-separated variants are valid (random-greeting feature).
    validator("Hi {user}\n---\nWelcome {user}\n---\nHey {user}")


def test_message_validator_caps_variant_count():
    from cogs.welcome.schemas import WELCOME_SETTINGS

    validator = {s.name: s for s in WELCOME_SETTINGS}["join_message"].validator
    too_many = "\n---\n".join(
        f"msg {i}" for i in range(welcome_config.MAX_MESSAGE_VARIANTS + 1)
    )
    with pytest.raises(ValueError):
        validator(too_many)


def test_message_validator_caps_each_variant_length():
    from cogs.welcome.schemas import WELCOME_SETTINGS

    validator = {s.name: s for s in WELCOME_SETTINGS}["join_message"].validator
    # The combined value is long, but each variant is within the per-variant
    # cap → accepted (the cap is per variant, since only one renders at a time).
    ok = "\n---\n".join(["x" * welcome_config.MAX_MESSAGE_LENGTH] * 3)
    validator(ok)
    # One over-long variant is still rejected.
    bad = "fine\n---\n" + "x" * (welcome_config.MAX_MESSAGE_LENGTH + 1)
    with pytest.raises(ValueError):
        validator(bad)


def test_bool_validator_guards_non_bool():
    from cogs.welcome.schemas import WELCOME_SETTINGS

    validator = {s.name: s for s in WELCOME_SETTINGS}["enabled"].validator
    with pytest.raises(ValueError):
        validator("yes")


def test_min_account_age_validator_bounds_and_type():
    from cogs.welcome.schemas import WELCOME_SETTINGS

    validator = {s.name: s for s in WELCOME_SETTINGS}["min_account_age_days"].validator
    validator(0)  # disabled
    validator(7)  # in range
    validator(welcome_config.MAX_MIN_ACCOUNT_AGE_DAYS)  # boundary ok
    with pytest.raises(ValueError):
        validator(-1)  # below minimum
    with pytest.raises(ValueError):
        validator(welcome_config.MAX_MIN_ACCOUNT_AGE_DAYS + 1)  # above cap
    with pytest.raises(ValueError):
        validator(True)  # bool is not an int here
    with pytest.raises(ValueError):
        validator("7")  # str rejected


def test_delete_after_validator_bounds_and_type():
    from cogs.welcome.schemas import WELCOME_SETTINGS

    validator = {s.name: s for s in WELCOME_SETTINGS}["delete_after_seconds"].validator
    validator(0)  # keep
    validator(30)  # in range
    validator(welcome_config.MAX_DELETE_AFTER_SECONDS)  # boundary ok
    with pytest.raises(ValueError):
        validator(-1)
    with pytest.raises(ValueError):
        validator(welcome_config.MAX_DELETE_AFTER_SECONDS + 1)
    with pytest.raises(ValueError):
        validator(True)


def test_new_int_specs_carry_numeric_preset_hint():
    from cogs.welcome.schemas import WELCOME_SETTINGS

    by_name = {s.name: s for s in WELCOME_SETTINGS}
    for name in ("min_account_age_days", "delete_after_seconds"):
        assert by_name[name].input_hint == "numeric_presets"
        assert by_name[name].presets and 0 in by_name[name].presets
