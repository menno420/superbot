"""Unit tests for the automod subsystem schema (cogs.automod.schemas)."""

from __future__ import annotations

import pytest

from core.runtime import subsystem_schema as schema_mod
from services import automod_config


@pytest.fixture(autouse=True)
def _isolated_state():
    saved = schema_mod.all_schemas()
    schema_mod._reset_for_tests()
    yield
    schema_mod._reset_for_tests()
    for schema in saved.values():
        schema_mod.register(schema)


def test_register_adds_automod_schema():
    from cogs.automod.schemas import register_schemas

    register_schemas()
    assert "automod" in schema_mod.registered_subsystems()
    schema = schema_mod.get_schema("automod")
    assert schema is not None and schema.subsystem == "automod"


def test_register_is_idempotent():
    from cogs.automod.schemas import register_schemas

    register_schemas()
    schema_mod._reset_for_tests()
    register_schemas()
    assert schema_mod.get_schema("automod") is not None


# Each spec's default must equal the canonical automod_config default — they
# share the constant, so this pins that they never drift.
_EXPECTED_DEFAULTS = {
    "enabled": automod_config.DEFAULT_ENABLED,
    "spam_enabled": automod_config.DEFAULT_SPAM_ENABLED,
    "invites_enabled": automod_config.DEFAULT_INVITES_ENABLED,
    "caps_enabled": automod_config.DEFAULT_CAPS_ENABLED,
    "mentions_enabled": automod_config.DEFAULT_MENTIONS_ENABLED,
    "cross_channel_spam_enabled": automod_config.DEFAULT_CROSS_CHANNEL_SPAM_ENABLED,
    "duplicate_enabled": automod_config.DEFAULT_DUPLICATE_ENABLED,
    "spam_count": automod_config.DEFAULT_SPAM_COUNT,
    "spam_window_seconds": automod_config.DEFAULT_SPAM_WINDOW_SECONDS,
    "caps_percent": automod_config.DEFAULT_CAPS_PERCENT,
    "mentions_count": automod_config.DEFAULT_MENTIONS_COUNT,
    "cross_channel_spam_count": automod_config.DEFAULT_CROSS_CHANNEL_SPAM_COUNT,
    "duplicate_count": automod_config.DEFAULT_DUPLICATE_COUNT,
    "exempt_roles": automod_config.DEFAULT_EXEMPT_ROLES,
    "exempt_channels": automod_config.DEFAULT_EXEMPT_CHANNELS,
}


def test_spec_defaults_match_config_defaults():
    from cogs.automod.schemas import AUTOMOD_SETTINGS

    by_name = {s.name: s for s in AUTOMOD_SETTINGS}
    assert set(by_name) == set(_EXPECTED_DEFAULTS)
    for name, expected in _EXPECTED_DEFAULTS.items():
        assert by_name[name].default == expected


def test_every_rule_default_is_off():
    """A fresh guild must be unaffected — every flag defaults False."""
    from cogs.automod.schemas import AUTOMOD_SETTINGS

    for spec in AUTOMOD_SETTINGS:
        if spec.value_type is bool:
            assert spec.default is False, spec.name


def test_all_specs_require_a_configure_capability():
    from cogs.automod.schemas import AUTOMOD_SETTINGS

    for spec in AUTOMOD_SETTINGS:
        assert spec.capability_required == "moderation.settings.configure"


def test_threshold_validators_reject_out_of_range():
    from cogs.automod.schemas import AUTOMOD_SETTINGS

    by_name = {s.name: s for s in AUTOMOD_SETTINGS}
    with pytest.raises(ValueError):
        by_name["spam_count"].validator(1)  # below MIN_SPAM_COUNT
    with pytest.raises(ValueError):
        by_name["caps_percent"].validator(0)
    with pytest.raises(ValueError):
        by_name["enabled"].validator("yes")  # not a bool
    with pytest.raises(ValueError):
        by_name["cross_channel_spam_count"].validator(1)  # below MIN
    with pytest.raises(ValueError):
        by_name["duplicate_count"].validator(1)  # below MIN


def test_exempt_csv_validator():
    from cogs.automod.schemas import AUTOMOD_SETTINGS

    by_name = {s.name: s for s in AUTOMOD_SETTINGS}
    validator = by_name["exempt_roles"].validator
    validator("1, 2, 3")  # ok
    validator("")  # ok — empty means none
    with pytest.raises(ValueError):
        validator("1, notanid, 3")
